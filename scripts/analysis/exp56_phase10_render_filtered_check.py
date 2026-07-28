#!/usr/bin/env python3
"""exp56 Phase 10 -- render_filtered() 검증 (Phase 8b와 동일 수준 요구):
1) keep_mask=all True -> render()와 forward/backward 수치 일치해야 함 (경로 자체의 정확성)
2) keep_mask=partial(frustum) -> kept 원소들의 gradient가 "제거된 애들이
   진짜 안 보였다면" full render()로 계산했을 때와 같아야 함 (invisible을
   지워도 visible의 결과가 안 바뀌는지 -- 이게 핵심 정합성 조건)
"""
import sys, os
sys.path.append("/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM/vigs")
import numpy as np
import torch
from plyfile import PlyData
from scipy.spatial.transform import Rotation as R

from gaussian.utils.camera_utils import Camera
from gaussian.utils.graphics_utils import getProjectionMatrix2
from gaussian.renderer import render, render_filtered, frustum_prefilter
from gaussian.scene.gaussian_model import GaussianModel

PLY = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments/exp56_ax8_camcache/3dgs_before_final.ply"
RUN_DIR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments/exp56_ax8_camcache"


def load_gaussians(ply_path):
    p = PlyData.read(ply_path)
    v = p.elements[0]
    xyz = np.stack([np.asarray(v["x"]), np.asarray(v["y"]), np.asarray(v["z"])], axis=1)
    opacities = np.asarray(v["opacity"])[..., np.newaxis]
    features_dc = np.zeros((xyz.shape[0], 3, 1))
    features_dc[:, 0, 0] = np.asarray(v["f_dc_0"]); features_dc[:, 1, 0] = np.asarray(v["f_dc_1"]); features_dc[:, 2, 0] = np.asarray(v["f_dc_2"])
    scale_names = sorted([pr.name for pr in v.properties if pr.name.startswith("scale_")], key=lambda x: int(x.split("_")[-1]))
    scales = np.stack([np.asarray(v[n]) for n in scale_names], axis=1)
    rot_names = sorted([pr.name for pr in v.properties if pr.name.startswith("rot")], key=lambda x: int(x.split("_")[-1]))
    rots = np.stack([np.asarray(v[n]) for n in rot_names], axis=1)
    class G: pass
    g = G()
    g._xyz = torch.tensor(xyz, dtype=torch.float, device="cuda", requires_grad=True)
    g._features_dc = torch.tensor(features_dc, dtype=torch.float, device="cuda").transpose(1, 2).contiguous().requires_grad_(True)
    g._features_rest = torch.zeros((g._xyz.shape[0], 0, 3), dtype=torch.float, device="cuda")
    g._opacity = torch.tensor(opacities, dtype=torch.float, device="cuda", requires_grad=True)
    g._scaling = torch.tensor(scales, dtype=torch.float, device="cuda", requires_grad=True)
    g._rotation = torch.tensor(rots, dtype=torch.float, device="cuda", requires_grad=True)
    g.max_sh_degree = 0; g.active_sh_degree = 0
    g.scaling_activation = torch.exp; g.opacity_activation = torch.sigmoid; g.rotation_activation = torch.nn.functional.normalize
    type(g).get_xyz = property(lambda self: self._xyz)
    type(g).get_scaling = property(lambda self: self.scaling_activation(self._scaling))
    type(g).get_rotation = property(lambda self: self.rotation_activation(self._rotation))
    type(g).get_opacity = property(lambda self: self.opacity_activation(self._opacity))
    type(g).get_features = property(lambda self: torch.cat((self._features_dc, self._features_rest), dim=1))
    return g


def build_camera(row_idx=None):
    K = np.load(os.path.join(RUN_DIR, "intrinsics.npy"))
    traj = np.loadtxt(os.path.join(RUN_DIR, "traj_kf_beforeBA.txt"))
    row = traj[row_idx if row_idx is not None else len(traj) // 2]
    tx, ty, tz, qx, qy, qz, qw = row[1:8]
    T_c2w = np.eye(4)
    T_c2w[:3, :3] = R.from_quat([qx, qy, qz, qw]).as_matrix()
    T_c2w[:3, 3] = [tx, ty, tz]
    pose = torch.tensor(np.linalg.inv(T_c2w), dtype=torch.float32, device="cuda")
    W, H = 1024, 1024
    fx, fy, cx, cy = float(K[0]), float(K[1]), float(K[2]), float(K[3])
    projection_matrix = getProjectionMatrix2(znear=0.01, zfar=100.0, fx=fx, fy=fy, cx=cx, cy=cy, W=W, H=H).transpose(0, 1).cuda()
    return Camera.init_from_tracking(None, None, None, pose, 0, projection_matrix, [fx, fy, cx, cy, W, H])


def zero_grads(g):
    for t in [g._xyz, g._opacity, g._scaling, g._rotation, g._features_dc]:
        t.grad = None


def run_full(g, cam, bg):
    pkg = render(cam, g, bg)
    loss = pkg["render"].sum() + pkg["depth"].sum()
    loss.backward()
    grads = {
        "xyz": g._xyz.grad.clone(),
        "opacity": g._opacity.grad.clone(),
        "scaling": g._scaling.grad.clone(),
        "rotation": g._rotation.grad.clone(),
        "features_dc": g._features_dc.grad.clone(),
    }
    out = {"render": pkg["render"].detach().clone(), "depth": pkg["depth"].detach().clone(),
           "radii": pkg["radii"].detach().clone(), "vis": pkg["visibility_filter"].detach().clone()}
    zero_grads(g)
    return out, grads


def run_filtered(g, cam, bg, keep_mask):
    pkg = render_filtered(cam, g, bg, keep_mask)
    loss = pkg["render"].sum() + pkg["depth"].sum()
    loss.backward()
    pkg["_scatter_grad_after_backward"]()
    grads = {
        "xyz": g._xyz.grad.clone(),
        "opacity": g._opacity.grad.clone(),
        "scaling": g._scaling.grad.clone(),
        "rotation": g._rotation.grad.clone(),
        "features_dc": g._features_dc.grad.clone(),
    }
    out = {"render": pkg["render"].detach().clone(), "depth": pkg["depth"].detach().clone(),
           "radii": pkg["radii"].detach().clone(), "vis": pkg["visibility_filter"].detach().clone(),
           "vpt_grad": pkg["viewspace_points"].grad.clone()}
    zero_grads(g)
    return out, grads


if __name__ == "__main__":
    g = load_gaussians(PLY)
    N = g._xyz.shape[0]
    cam = build_camera()
    bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")

    print("=== TEST 1: keep_mask=all True vs render() ===")
    out_full, grads_full = run_full(g, cam, bg)
    all_true = torch.ones(N, dtype=torch.bool, device="cuda")
    out_filt, grads_filt = run_filtered(g, cam, bg, all_true)

    print(f"  render forward max abs diff: {(out_full['render']-out_filt['render']).abs().max().item():.3e}")
    print(f"  depth forward max abs diff:  {(out_full['depth']-out_filt['depth']).abs().max().item():.3e}")
    print(f"  radii exact match: {(out_full['radii']==out_filt['radii']).all().item()}")
    for k in grads_full:
        gf, gfilt = grads_full[k], grads_filt[k]
        rel = (gf-gfilt).abs().max().item() / (gf.abs().max().item()+1e-8)
        print(f"  grad[{k}] max abs diff: {(gf-gfilt).abs().max().item():.3e}  rel: {rel:.3e}")

    print("\n=== TEST 2: partial frustum keep_mask -- kept gaussians' grad should match full-render ===")
    keep = frustum_prefilter(g.get_xyz, cam.world_view_transform, np.tan(cam.FoVx*0.5), np.tan(cam.FoVy*0.5), margin=3.0)
    print(f"  keep_frac = {keep.float().mean().item():.4f}")
    out_full2, grads_full2 = run_full(g, cam, bg)
    out_p, grads_p = run_filtered(g, cam, bg, keep)
    print(f"  render forward max abs diff (should be tiny, only from truly-excluded contributions): {(out_full2['render']-out_p['render']).abs().max().item():.3e}")
    # only compare gradients on gaussians that render() itself said were visible AND kept
    true_vis = out_full2["vis"]
    compare_mask = true_vis & keep
    print(f"  #true_vis={true_vis.sum().item()}  #kept={keep.sum().item()}  #compare(true_vis & kept)={compare_mask.sum().item()}  #true_vis_but_excluded={((true_vis) & (~keep)).sum().item()}")
    for k, key_name in [("xyz", "xyz"), ("opacity", "opacity")]:
        gf = grads_full2[key_name][compare_mask]
        gp = grads_p[key_name][compare_mask]
        rel = (gf-gp).abs().max().item() / (gf.abs().max().item()+1e-8)
        print(f"  grad[{key_name}] on (true_vis & kept) max abs diff: {(gf-gp).abs().max().item():.3e}  rel: {rel:.3e}")
    print("  done.")

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "diag":
    g = load_gaussians(PLY)
    N = g._xyz.shape[0]
    cam = build_camera()
    bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")
    all_true = torch.ones(N, dtype=torch.bool, device="cuda")

    out_full, grads_full = run_full(g, cam, bg)
    out_filt, grads_filt = run_filtered(g, cam, bg, all_true)

    diff = (grads_full["xyz"] - grads_filt["xyz"]).abs().sum(dim=1)  # per-gaussian diff magnitude
    vis = out_full["vis"]
    print(f"total gaussians: {N}, visible(radii>0): {vis.sum().item()}")
    print(f"diff concentrated on visible? sum(diff on visible)={diff[vis].sum().item():.3e}  sum(diff on invisible)={diff[~vis].sum().item():.3e}")
    top_idx = torch.argsort(diff, descending=True)[:10]
    print("top-10 worst-diff gaussians:")
    for i in top_idx.tolist():
        print(f"  idx={i} vis={vis[i].item()} radii_full={out_full['radii'][i].item()} grad_full_xyz={grads_full['xyz'][i].cpu().numpy()} grad_filt_xyz={grads_filt['xyz'][i].cpu().numpy()}")
    # check how many visible gaussians have ANY diff at all
    vis_diff = diff[vis]
    print(f"\nvisible gaussians with diff>1e-4: {(vis_diff>1e-4).sum().item()} / {vis.sum().item()}")
    print(f"max diff among visible: {vis_diff.max().item():.3e}, mean diff among visible: {vis_diff.mean().item():.3e}")
    invis_diff = diff[~vis]
    print(f"invisible gaussians with diff>1e-4: {(invis_diff>1e-4).sum().item()} / {(~vis).sum().item()}")
    print(f"max diff among invisible: {invis_diff.max().item():.3e}")

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "order":
    # swap call order: filtered first, then full -- if the "wrong" side flips,
    # it's a stale-memory/allocator-reuse issue, not a structural bug in render_filtered.
    g = load_gaussians(PLY)
    N = g._xyz.shape[0]
    cam = build_camera()
    bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")
    all_true = torch.ones(N, dtype=torch.bool, device="cuda")

    out_filt, grads_filt = run_filtered(g, cam, bg, all_true)
    out_full, grads_full = run_full(g, cam, bg)
    diff = (grads_full["xyz"] - grads_filt["xyz"]).abs().sum(dim=1)
    print(f"[order swapped: filtered first] max diff: {diff.max().item():.3e}  #diff>1e-4: {(diff>1e-4).sum().item()}")

    # also try calling render_filtered TWICE in a row (no render() involved at all)
    out_filt1, grads_filt1 = run_filtered(g, cam, bg, all_true)
    out_filt2, grads_filt2 = run_filtered(g, cam, bg, all_true)
    diff2 = (grads_filt1["xyz"] - grads_filt2["xyz"]).abs().sum(dim=1)
    print(f"[render_filtered vs itself, twice] max diff: {diff2.max().item():.3e}  #diff>1e-4: {(diff2>1e-4).sum().item()}")

    # also try calling render() TWICE in a row
    out_r1, grads_r1 = run_full(g, cam, bg)
    out_r2, grads_r2 = run_full(g, cam, bg)
    diff3 = (grads_r1["xyz"] - grads_r2["xyz"]).abs().sum(dim=1)
    print(f"[render vs itself, twice] max diff: {diff3.max().item():.3e}  #diff>1e-4: {(diff3>1e-4).sum().item()}")

def run_full_realistic(g, cam, bg, gt_image):
    pkg = render(cam, g, bg)
    image = torch.clamp(pkg["render"], 0.0, 1.0)
    loss = torch.abs(image - gt_image).mean() + torch.abs(pkg["depth"]).mean() * 0.01
    loss.backward()
    grads = {k: getattr(g, f"_{k}" if k != "features_dc" else "_features_dc").grad.clone() for k in ["xyz", "opacity", "scaling", "rotation", "features_dc"]}
    out = {"render": image.detach().clone(), "radii": pkg["radii"].detach().clone(), "vis": pkg["visibility_filter"].detach().clone()}
    zero_grads(g)
    return out, grads


def run_filtered_realistic(g, cam, bg, keep_mask, gt_image):
    pkg = render_filtered(cam, g, bg, keep_mask)
    image = torch.clamp(pkg["render"], 0.0, 1.0)
    loss = torch.abs(image - gt_image).mean() + torch.abs(pkg["depth"]).mean() * 0.01
    loss.backward()
    pkg["_scatter_grad_after_backward"]()
    grads = {k: getattr(g, f"_{k}" if k != "features_dc" else "_features_dc").grad.clone() for k in ["xyz", "opacity", "scaling", "rotation", "features_dc"]}
    out = {"render": image.detach().clone(), "radii": pkg["radii"].detach().clone(), "vis": pkg["visibility_filter"].detach().clone()}
    zero_grads(g)
    return out, grads


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "realistic":
    g = load_gaussians(PLY)
    N = g._xyz.shape[0]
    cam = build_camera()
    bg = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")
    torch.manual_seed(0)
    gt_image = torch.rand(3, 1024, 1024, device="cuda")  # random but FIXED "GT" for a bounded, realistic-scale loss
    all_true = torch.ones(N, dtype=torch.bool, device="cuda")

    print("=== render() vs itself (determinism baseline, realistic loss) ===")
    o1, g1 = run_full_realistic(g, cam, bg, gt_image)
    o2, g2 = run_full_realistic(g, cam, bg, gt_image)
    d = (g1["xyz"] - g2["xyz"]).abs().sum(dim=1)
    print(f"  max diff: {d.max().item():.3e}  mean diff: {d.mean().item():.3e}  #diff>1e-6: {(d>1e-6).sum().item()}")

    print("=== render_filtered(all_true) vs render(), realistic loss ===")
    of, gf = run_full_realistic(g, cam, bg, gt_image)
    op, gp = run_filtered_realistic(g, cam, bg, all_true, gt_image)
    print(f"  render forward max abs diff: {(of['render']-op['render']).abs().max().item():.3e}")
    for k in gf:
        diff = (gf[k]-gp[k]).abs()
        rel = diff.max().item() / (gf[k].abs().max().item()+1e-12)
        print(f"  grad[{k}] max abs diff: {diff.max().item():.3e}  rel: {rel:.3e}")

    print("=== render_filtered(partial frustum) vs render(), realistic loss, compare on (true_vis & kept) ===")
    keep = frustum_prefilter(g.get_xyz, cam.world_view_transform, np.tan(cam.FoVx*0.5), np.tan(cam.FoVy*0.5), margin=3.0)
    of2, gf2 = run_full_realistic(g, cam, bg, gt_image)
    op2, gp2 = run_filtered_realistic(g, cam, bg, keep, gt_image)
    compare_mask = of2["vis"] & keep
    print(f"  keep_frac={keep.float().mean().item():.4f}  #compare={compare_mask.sum().item()}")
    for k in ["xyz", "opacity", "scaling", "rotation"]:
        diff = (gf2[k][compare_mask]-gp2[k][compare_mask]).abs()
        rel = diff.max().item() / (gf2[k][compare_mask].abs().max().item()+1e-12)
        print(f"  grad[{k}] on (true_vis & kept) max abs diff: {diff.max().item():.3e}  rel: {rel:.3e}")
