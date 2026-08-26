#
# train_incremental_coverage_active.py
# -----------------------------------------------------------------------------
# ACTIVE integration: --view_selector coverage actually REPLACES
# `random.choice(pooled_cams)` with SparseCoverageBuffer-weighted sampling.
# This is the step after train_incremental_coverage_probe.py (observer-only,
# training behavior untouched) -- here the buffer's score genuinely drives
# which view gets trained, so this is a real A/B comparison against
# --view_selector random (byte-identical to the unmodified train_incremental.py).
#
# Visibility for SCORING (not training) is a cheap frustum-only geometric test
# (project Gaussian means through the candidate camera's own full_proj_transform,
# no rasterization) -- matches the design doc's "occlusion ignored" decision.
# The view that actually gets TRAINED still goes through the real renderer as
# always; only the *selection* step uses the cheap frustum proxy.
#
# Diffs from train_incremental_coverage_probe.py are marked "# ACTIVE:".
# -----------------------------------------------------------------------------

import math
import os
import sys
import json
import collections
import random
import argparse
from pathlib import Path
from collections import deque

import torch
import numpy as np

THREEDGS_CUSTOM = "/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom"
sys.path.insert(0, THREEDGS_CUSTOM)
sys.path.insert(0, "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/scripts/incremental")
from coverage_buffer import SparseCoverageBuffer

from arguments import ModelParams, PipelineParams, OptimizationParams
from scene import GaussianModel
from scene.dataset_readers import sceneLoadTypeCallbacks
from utils.camera_utils import cameraList_from_camInfos
from utils.loss_utils import l1_loss, ssim
from utils.general_utils import safe_state
from gaussian_renderer import render
from eval.carve_loss import CarveLoss, CarveLossConfig
from scene.dataset_readers import read_points3D_text
from scene.gaussian_model import BasicPointCloud

try:
    from fused_ssim import fused_ssim
    FUSED_SSIM_AVAILABLE = True
except Exception:
    FUSED_SSIM_AVAILABLE = False


def load_chunk_cameras_and_pcd(chunk_dir: Path, cam_args):
    scene_info = sceneLoadTypeCallbacks["Colmap"](
        str(chunk_dir), "images", "", False, False,
        init_pcd_filter=False, init_pcd_expand_factor=3.0,
    )
    cams = cameraList_from_camInfos(scene_info.train_cameras, 1.0, cam_args, False, False)
    return cams, scene_info.point_cloud, scene_info.nerf_normalization["radius"]


def eval_held_out(gaussians, pipe, background, held_out_cams, dataset):
    if not held_out_cams:
        return None
    total_mse, n = 0.0, 0
    with torch.no_grad():
        for cam in held_out_cams:
            render_pkg = render(cam, gaussians, pipe, background, use_trained_exp=dataset.train_test_exp)
            image = render_pkg["render"]
            gt_image = cam.original_image.cuda()
            total_mse += ((image - gt_image) ** 2).mean().item()
            n += 1
    mse = total_mse / n
    psnr = -10.0 * math.log10(mse) if mse > 0 else 99.0
    return psnr


# ACTIVE: cheap frustum-only visibility for SCORING candidates -- no rasterization.
def frustum_visible_mask(means, camera, margin=1.15):
    ones = torch.ones(means.shape[0], 1, device=means.device, dtype=means.dtype)
    means_h = torch.cat([means, ones], dim=-1)
    clip = means_h @ camera.full_proj_transform
    w = clip[:, 3]
    in_front = w > camera.znear
    ndc_x = clip[:, 0] / w.clamp_min(1e-6)
    ndc_y = clip[:, 1] / w.clamp_min(1e-6)
    return in_front & (ndc_x.abs() <= margin) & (ndc_y.abs() <= margin)


def score_pool(buf, pooled_cams, gaussians_xyz):
    candidates = []
    for cam in pooled_cams:
        vis = frustum_visible_mask(gaussians_xyz, cam)
        candidates.append((gaussians_xyz[vis], cam.camera_center))
    weights = buf.score(candidates)
    return weights


def main():
    parser = argparse.ArgumentParser(description="coverage-buffer ACTIVE integration (replaces random.choice)")
    lp = ModelParams(parser)
    pp = PipelineParams(parser)
    op = OptimizationParams(parser)

    parser.add_argument("--manifest", type=str, required=True)
    parser.add_argument("--dataset_root", type=str, required=True)
    parser.add_argument("--window_size", type=int, default=8)
    parser.add_argument("--iters_per_event", type=int, default=60)
    parser.add_argument("--stable_grad_thresh", type=float, default=5e-4)
    parser.add_argument("--save_every", type=int, default=10)
    parser.add_argument("--max_events", type=int, default=-1)
    parser.add_argument("--carve_loss_config", type=str, default=None)
    parser.add_argument("--constant_lr", action="store_true")
    parser.add_argument("--init_source", type=str, default="slam", choices=["slam", "ppm", "roma", "both", "all", "hybrid"])
    parser.add_argument("--size_threshold_from_iter", type=int, default=3000)
    parser.add_argument("--trace_event", type=int, default=-1)
    parser.add_argument("--cameras_extent_source", type=str, default=None)
    # ACTIVE flags
    parser.add_argument("--view_selector", type=str, default="random", choices=["random", "coverage"],
                         help="random = byte-identical to train_incremental.py. coverage = "
                              "SparseCoverageBuffer-weighted random.choices() instead.")
    parser.add_argument("--coverage_rescore_every", type=int, default=10,
                         help="recompute pool weights every N iterations (K-step batch, per design doc)")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--held_out_interval", type=int, default=5,
                         help="1-in-N frames (by a running global counter across all chunks, NOT reset "
                              "per chunk -- a per-chunk reset would hold out entire single-frame chunks) "
                              "held out from training and used for the held_out_psnr curve")
    parser.add_argument("--held_out_eval_every_events", type=int, default=1,
                         help="run the held-out eval every N events (held-out set only grows, so this "
                              "stays cheap even as it accumulates)")

    args = parser.parse_args()
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    dataset = lp.extract(args)
    pipe = pp.extract(args)
    opt = op.extract(args)

    safe_state(False)

    out_dir = Path(dataset.model_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "point_cloud").mkdir(exist_ok=True)
    from argparse import Namespace as _NS
    with open(out_dir / "cfg_args", "w") as _f:
        _f.write(str(_NS(**vars(dataset))))

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    if args.max_events > 0:
        manifest = manifest[: args.max_events]

    bg_color = [1, 1, 1] if dataset.white_background else [0, 0, 0]
    background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")

    gaussians = GaussianModel(dataset.sh_degree, opt.optimizer_type)

    fixed_cameras_extent = None
    if args.cameras_extent_source:
        _full_info = sceneLoadTypeCallbacks["Colmap"](args.cameras_extent_source, "images", "", False, False)
        fixed_cameras_extent = _full_info.nerf_normalization["radius"]

    carve_loss = CarveLoss(CarveLossConfig.from_yaml(args.carve_loss_config), args.dataset_root) \
        if args.carve_loss_config else CarveLoss(CarveLossConfig(enabled=False), args.dataset_root)

    window = deque(maxlen=args.window_size)
    stable_mask = None
    prev_accum_rgb_grad = None

    draw_counts = collections.Counter()
    global_iter = 0
    event_log = []
    trace_ancestor_ids = None
    event_ranges = {}

    buf = SparseCoverageBuffer(device="cuda")
    pool_weights = None  # ACTIVE: cached [len(pooled_cams)] weights, refreshed every coverage_rescore_every iters

    # held-out split: i%interval==0 WITHIN each chunk, but ONLY for chunks with more
    # than 1 frame. This dataset's early chunks are single-frame (one keyframe = one
    # chunk); a naive i%5==0 with i reset per chunk would hold out i=0 of EVERY such
    # chunk, i.e. 100% of them, starving the training pool at cold start. Dense
    # (multi-frame) chunks always have plenty left over after holding out ~1/interval,
    # so this only ever removes frames where it's safe to. Held-out cameras never
    # enter the training pool; the held-out set only grows as new chunks arrive.
    held_out_cams = []

    for event_idx, chunk in enumerate(manifest):
        chunk_dir = Path(args.dataset_root) / f"chunk_{chunk['chunk_idx']:03d}"
        cams, pcd, radius = load_chunk_cameras_and_pcd(chunk_dir, dataset)

        if len(cams) > 1:
            train_cams = [c for i, c in enumerate(cams) if i % args.held_out_interval != 0]
            held_out_cams.extend(c for i, c in enumerate(cams) if i % args.held_out_interval == 0)
        else:
            train_cams = list(cams)

        n_before = gaussians._xyz.shape[0] if gaussians._xyz.numel() > 0 else 0

        if event_idx == 0:
            cameras_extent = fixed_cameras_extent if fixed_cameras_extent else (radius if radius > 0 else 3.0)

        if event_idx == 0:
            gaussians.create_from_pcd(pcd, cams, cameras_extent)
            gaussians.training_setup(opt)
            event_ranges[0] = (0, gaussians._xyz.shape[0])
            stable_mask = torch.zeros(gaussians._xyz.shape[0], dtype=torch.bool, device="cuda")
            prev_accum_rgb_grad = gaussians.accum_rgb_grad.clone()
        else:
            xyz_parts, rgb_parts = [], []
            if args.init_source in ("slam", "both", "all", "hybrid"):
                p = chunk_dir / "sparse" / "0" / "extra_points3D.txt"
                if p.exists() and p.stat().st_size > 0:
                    xyz, rgb, _ = read_points3D_text(str(p))
                    xyz_parts.append(xyz); rgb_parts.append(rgb)
            if args.init_source in ("ppm", "both", "all", "hybrid"):
                p = chunk_dir / "sparse" / "0" / "ppm_points3D.txt"
                if p.exists() and p.stat().st_size > 0:
                    xyz, rgb, _ = read_points3D_text(str(p))
                    xyz_parts.append(xyz); rgb_parts.append(rgb)
            if args.init_source in ("roma", "all", "hybrid"):
                p = chunk_dir / "sparse" / "0" / "roma_points3D.txt"
                if p.exists() and p.stat().st_size > 0:
                    xyz, rgb, _ = read_points3D_text(str(p))
                    xyz_parts.append(xyz); rgb_parts.append(rgb)
            if xyz_parts:
                xyz = np.concatenate(xyz_parts, axis=0)
                rgb = np.concatenate(rgb_parts, axis=0)
                extra_pcd = BasicPointCloud(points=xyz, colors=rgb / 255.0, normals=np.zeros_like(xyz))
                gaussians.add_extra_points(extra_pcd)
            n_new = gaussians._xyz.shape[0] - n_before
            event_ranges[event_idx] = (n_before, gaussians._xyz.shape[0])
            stable_mask = torch.cat([stable_mask, torch.zeros(n_new, dtype=torch.bool, device="cuda")])
            prev_accum_rgb_grad = torch.cat([prev_accum_rgb_grad, torch.zeros(n_new, device="cuda")])

        if event_idx == args.trace_event:
            trace_ancestor_ids = gaussians.ancestor_idx[n_before:].clone()

        window.append(train_cams)
        pooled_cams = [c for bucket in window for c in bucket]
        pool_weights = None  # force rescore on pool change

        for local_iter in range(args.iters_per_event):
            global_iter += 1
            if not args.constant_lr:
                gaussians.update_learning_rate(global_iter)
            if global_iter % 1000 == 0:
                gaussians.oneupSHdegree()

            # ACTIVE: this is the actual substitution.
            if args.view_selector == "coverage":
                if pool_weights is None or local_iter % args.coverage_rescore_every == 0:
                    with torch.no_grad():
                        pool_weights = score_pool(buf, pooled_cams, gaussians._xyz.detach())
                viewpoint_cam = random.choices(pooled_cams, weights=pool_weights, k=1)[0]
            else:
                viewpoint_cam = random.choice(pooled_cams)  # identical to train_incremental.py
            draw_counts[viewpoint_cam.image_name] += 1

            render_pkg = render(viewpoint_cam, gaussians, pipe, background,
                                 use_trained_exp=dataset.train_test_exp)
            image = render_pkg["render"]
            gt_image = viewpoint_cam.original_image.cuda()

            # buffer bookkeeping: real visible Gaussians from the render that just happened
            visibility_filter = render_pkg["visibility_filter"]
            with torch.no_grad():
                vis_bool_mask = render_pkg["radii"] > 0  # this codebase's visibility_filter is .nonzero(), not bool
                vis_pos = gaussians._xyz[vis_bool_mask].detach()
                cam_pos = viewpoint_cam.camera_center.detach()
                buf.update(vis_pos, cam_pos)

            Ll1 = l1_loss(image, gt_image)
            ssim_value = fused_ssim(image.unsqueeze(0), gt_image.unsqueeze(0)) if FUSED_SSIM_AVAILABLE else ssim(image, gt_image)
            loss = (1.0 - opt.lambda_dssim) * Ll1 + opt.lambda_dssim * (1.0 - ssim_value)

            _psnr_every = int(os.environ.get("PSNR_LOG_EVERY", "0"))
            if _psnr_every > 0 and global_iter % _psnr_every == 0:
                with torch.no_grad():
                    _mse = ((image - gt_image) ** 2).mean().item()
                    _psnr = -10.0 * math.log10(_mse) if _mse > 0 else 99.0
                print(f"[psnr_curve] iter={global_iter} psnr={_psnr:.4f} n_gaussians={gaussians._xyz.shape[0]} "
                      f"selector={args.view_selector}", flush=True)

            loss.backward(retain_graph=carve_loss.cfg.enabled)

            if gaussians._xyz.grad is not None:
                gaussians.accum_rgb_grad += gaussians._xyz.grad.norm(dim=-1)

            if carve_loss.cfg.enabled:
                L_carve, _ = carve_loss.compute_loss(gaussians, global_iter)
                if L_carve is not None:
                    L_carve.backward()

            with torch.no_grad():
                for pname in ("_xyz", "_opacity", "_scaling", "_rotation", "_features_dc", "_features_rest"):
                    g = getattr(gaussians, pname).grad
                    if g is not None:
                        g[stable_mask] = 0

            radii = render_pkg["radii"]
            with torch.no_grad():
                if global_iter < opt.densify_until_iter:
                    gaussians.max_radii2D[visibility_filter] = torch.max(
                        gaussians.max_radii2D[visibility_filter], radii[visibility_filter])
                    gaussians.add_densification_stats(render_pkg["viewspace_points"], visibility_filter)
                    gaussians.accum_visibility[visibility_filter] += 1

                    if global_iter > opt.densify_from_iter and global_iter % opt.densification_interval == 0:
                        size_threshold = 20 if global_iter > args.size_threshold_from_iter else None
                        gaussians.densify_and_prune(
                            opt.densify_grad_threshold, opt.min_opacity_prune_threshold,
                            cameras_extent, size_threshold, radii, iteration=global_iter,
                        )
                        _n = gaussians._xyz.shape[0]
                        if stable_mask.shape[0] != _n:
                            stable_mask = torch.zeros(_n, dtype=torch.bool, device="cuda")
                            prev_accum_rgb_grad = gaussians.accum_rgb_grad.clone()
                        buf.refresh_gaussian_counts(gaussians._xyz.detach())
                        pool_weights = None  # ACTIVE: N changed, force rescore next iter

                    if global_iter % opt.opacity_reset_interval == 0:
                        active_events = range(max(0, event_idx - len(window) + 1), event_idx + 1)
                        active_ancestors = []
                        for e in active_events:
                            if e in event_ranges:
                                start_idx, end_idx = event_ranges[e]
                                active_ancestors.append((start_idx, end_idx))

                        active_mask = torch.zeros(gaussians.get_opacity.shape[0], dtype=torch.bool, device="cuda")
                        for start_idx, end_idx in active_ancestors:
                            active_mask = active_mask | ((gaussians.ancestor_idx >= start_idx) & (gaussians.ancestor_idx < end_idx))

                        opacities = gaussians.get_opacity.clone()
                        opacities_reset = gaussians.inverse_opacity_activation(
                            torch.min(opacities, torch.ones_like(opacities) * 0.01)
                        )

                        current_opacities_raw = gaussians._opacity.clone()
                        current_opacities_raw[active_mask] = opacities_reset[active_mask]

                        optimizable_tensors = gaussians.replace_tensor_to_optimizer(current_opacities_raw, "opacity")
                        gaussians._opacity = optimizable_tensors["opacity"]

            gaussians.optimizer.step()
            gaussians.optimizer.zero_grad(set_to_none=True)

        with torch.no_grad():
            delta = gaussians.accum_rgb_grad - prev_accum_rgb_grad
            newly_stable = (~stable_mask) & (delta < args.stable_grad_thresh)
            stable_mask = stable_mask | newly_stable
            prev_accum_rgb_grad = gaussians.accum_rgb_grad.clone()

        n_total = gaussians._xyz.shape[0]
        n_stable = int(stable_mask.sum().item())
        print(f"[event {event_idx:03d}] kf_id={chunk['kf_id']} window_kfs={len(window)} "
              f"pool={len(pooled_cams)} N={n_total} (+{n_total - n_before}) stable={n_stable} loss={loss.item():.4f} "
              f"selector={args.view_selector} buffer_cells={len(buf)}")
        event_log.append({"event_idx": event_idx, "kf_id": chunk["kf_id"], "N": n_total,
                           "pool_size": len(pooled_cams),
                           "n_stable": n_stable, "global_iter": global_iter, "loss": float(loss.item())})

        if held_out_cams and (event_idx % args.held_out_eval_every_events == 0 or event_idx == len(manifest) - 1):
            held_out_psnr = eval_held_out(gaussians, pipe, background, held_out_cams, dataset)
            print(f"[held_out_psnr] iter={global_iter} psnr={held_out_psnr:.4f} "
                  f"n_held_out={len(held_out_cams)} n_gaussians={n_total} selector={args.view_selector}", flush=True)

        if (event_idx + 1) % args.save_every == 0 or event_idx == len(manifest) - 1:
            ply_dir = out_dir / "point_cloud" / f"iteration_{global_iter}"
            ply_dir.mkdir(parents=True, exist_ok=True)
            gaussians.save_ply(str(ply_dir / "point_cloud.ply"))
            torch.save((gaussians.capture(), global_iter), str(out_dir / f"chkpnt{global_iter}.pth"))
            (out_dir / "event_log.json").write_text(json.dumps(event_log, indent=2), encoding="utf-8")

    (out_dir / "draw_counts.json").write_text(json.dumps(dict(draw_counts), indent=2), encoding="utf-8")
    print(f"\nDone. selector={args.view_selector} {len(manifest)} events, {global_iter} total iterations, "
          f"final N={gaussians._xyz.shape[0]}, stable={int(stable_mask.sum().item())}, buffer_cells={len(buf)}.")


if __name__ == "__main__":
    main()
