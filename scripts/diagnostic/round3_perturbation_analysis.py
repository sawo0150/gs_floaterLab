#!/usr/bin/env python3
"""
Round 3: X-axis Depth Flatness Perturbation Analysis (P04 정량화)

목적:
  - 학습된 Gaussian들에 X/Y/Z 방향 perturbation 적용
  - loss landscape의 방향별 민감도 측정
  - Floater vs Surface Gaussian 비교
  - P04 예측: X(depth axis) 방향이 Y/Z보다 loss가 flat함

접근법:
  1. 학습 완료 모델 로드 (exp08, iter 30000)
  2. Forward pass → per-Gaussian gradient 기록 (X/Y/Z 성분별)
  3. Gaussian 분류: Z-outlier(floater), low-opacity, high-opacity surface
  4. 작은 subset에 대해 ±X, ±Y, ±Z perturbation → loss 측정
  5. Figure: loss curve (depth axis vs lateral axis) + gradient breakdown
"""

import sys, os
sys.path.insert(0, '/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/repos/main/3dgs-custom')
sys.path.insert(0, '/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/repos/main/3dgs-custom/submodules/diff-gaussian-rasterization')

import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from tqdm import tqdm

# ============================================================
# Config
# ============================================================
PLY_PATH = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/exp08_openmavis_full_dens_until7000_prune001_beta1_low_20260616_124504/point_cloud/iteration_30000/point_cloud.ply"
DATASET_PATH = "/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253"
OUT_DIR = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic")
OUT_DIR.mkdir(exist_ok=True)

# Camera stride for loss computation (fewer cams = faster)
CAMERA_STRIDE = 30     # ~44 cameras
N_PERTURB_GAUSSIANS = 200  # per group
PERTURB_DELTAS = [-1.0, -0.5, -0.2, -0.1, -0.05, 0.0, 0.05, 0.1, 0.2, 0.5, 1.0]

# ============================================================
# Load model
# ============================================================
from scene.gaussian_model import GaussianModel
from scene import Scene
from arguments import ModelParams, PipelineParams, OptimizationParams
from gaussian_renderer import render
from utils.loss_utils import l1_loss

import argparse

def load_gaussians(ply_path):
    gaussians = GaussianModel(sh_degree=3)
    gaussians.load_ply(ply_path)
    print(f"Loaded {len(gaussians.get_xyz)} Gaussians from {ply_path}")
    return gaussians

def load_cameras(dataset_path, stride=30):
    """Load cameras using the scene loader."""
    from scene.dataset_readers import readColmapSceneInfo
    from utils.camera_utils import cameraList_from_camInfos

    scene_info = readColmapSceneInfo(dataset_path, "images", depths="", eval=False, train_test_exp=False)
    cams_info = scene_info.train_cameras[::stride]
    cam_args = argparse.Namespace(
        data_device="cpu",
        resolution=-1,
        train_test_exp=False,
    )
    cameras = cameraList_from_camInfos(cams_info, resolution_scale=1.0,
                                        args=cam_args,
                                        is_nerf_synthetic=False, is_test_dataset=False)
    print(f"Loaded {len(cameras)} cameras (stride={stride})")
    return cameras

def render_and_loss(gaussians, cameras, pipe_args, bg_color):
    """Compute total L1 photometric loss over cameras."""
    total_loss = torch.tensor(0.0, device="cuda", requires_grad=False)
    n_cams = 0
    for cam in cameras:
        cam_gpu = cam  # already loaded
        render_pkg = render(cam_gpu, gaussians, pipe_args, bg_color)
        img = render_pkg["render"]
        gt = cam_gpu.original_image.cuda()
        loss = l1_loss(img, gt)
        total_loss = total_loss + loss.detach()
        n_cams += 1
    return (total_loss / n_cams).item()

# ============================================================
# Per-Gaussian gradient analysis (1 backward pass)
# ============================================================
def get_per_gaussian_gradients(gaussians, cameras, pipe_args, bg_color):
    """Run one full backward pass and record xyz gradient per-Gaussian."""
    gaussians._xyz.requires_grad_(True)
    if gaussians._xyz.grad is not None:
        gaussians._xyz.grad.zero_()

    total_loss = torch.tensor(0.0, device="cuda")
    for cam in cameras:
        render_pkg = render(cam, gaussians, pipe_args, bg_color)
        img = render_pkg["render"]
        gt = cam.original_image.cuda()
        loss = l1_loss(img, gt)
        total_loss = total_loss + loss

    total_loss = total_loss / len(cameras)
    total_loss.backward()

    grad = gaussians._xyz.grad.detach().cpu().numpy()  # [N, 3]
    xyz = gaussians.get_xyz.detach().cpu().numpy()     # [N, 3]
    opacity = gaussians.get_opacity.detach().squeeze().cpu().numpy()  # [N]
    return grad, xyz, opacity, total_loss.item()

# ============================================================
# Perturbation analysis
# ============================================================
def perturbation_loss_curve(gaussians_orig, cameras, pipe_args, bg_color, gauss_indices, direction_vec, deltas):
    """
    For each delta in deltas, perturb selected Gaussians in direction_vec
    and compute the loss. Returns list of (delta, loss) pairs.
    """
    results = []
    original_xyz = gaussians_orig._xyz.detach().clone()

    with torch.no_grad():
        base_loss = render_and_loss(gaussians_orig, cameras, pipe_args, bg_color)
        results.append((0.0, base_loss))

        dir_tensor = torch.tensor(direction_vec, dtype=torch.float32, device='cuda')

        for delta in deltas:
            if abs(delta) < 1e-9:
                continue
            new_xyz = original_xyz.clone()
            new_xyz[gauss_indices] += delta * dir_tensor
            gaussians_orig._xyz = new_xyz
            loss = render_and_loss(gaussians_orig, cameras, pipe_args, bg_color)
            results.append((delta, loss))

        # Restore
        gaussians_orig._xyz = original_xyz

    results.sort(key=lambda x: x[0])
    return results

# ============================================================
# Main
# ============================================================
def main():
    print("=== Round 3: Perturbation Analysis ===\n")

    # Pipe args
    pipe_args = argparse.Namespace(
        convert_SHs_python=False,
        compute_cov3D_python=False,
        debug=False,
        antialiasing=False,
        beta=5.0
    )
    bg_color = torch.tensor([0, 0, 0], dtype=torch.float32, device="cuda")

    # Load
    gaussians = load_gaussians(PLY_PATH)
    gaussians._xyz = gaussians._xyz.cuda()
    # Move all parameters to GPU
    gaussians._features_dc = gaussians._features_dc.cuda()
    gaussians._features_rest = gaussians._features_rest.cuda()
    gaussians._scaling = gaussians._scaling.cuda()
    gaussians._rotation = gaussians._rotation.cuda()
    gaussians._opacity = gaussians._opacity.cuda()

    cameras = load_cameras(DATASET_PATH, stride=CAMERA_STRIDE)
    # Move camera images to GPU (if not already)
    for cam in cameras:
        if cam.original_image is not None:
            pass  # stays on CPU until needed

    print("\n[Step 1] Per-Gaussian gradient analysis (1 backward pass)...")
    grad, xyz, opacity, loss_val = get_per_gaussian_gradients(gaussians, cameras, pipe_args, bg_color)
    print(f"  Total loss: {loss_val:.6f}")

    grad_norm = np.linalg.norm(grad, axis=1)  # [N]
    grad_x = np.abs(grad[:, 0])
    grad_y = np.abs(grad[:, 1])
    grad_z = np.abs(grad[:, 2])

    # Classify Gaussians
    z_outlier_mask = np.abs(xyz[:, 2]) > 3.0
    low_op_mask = (opacity < 0.1) & ~z_outlier_mask
    high_op_mask = (opacity >= 0.1) & ~z_outlier_mask
    visible_mask = grad_norm > 1e-12  # has some gradient

    print(f"\n  Gaussian groups:")
    print(f"    Z-outlier (|Z|>3m):     {z_outlier_mask.sum():>6d}  | visible: {(z_outlier_mask & visible_mask).sum()}")
    print(f"    Low-opacity surface:    {low_op_mask.sum():>6d}  | visible: {(low_op_mask & visible_mask).sum()}")
    print(f"    High-opacity surface:   {high_op_mask.sum():>6d}  | visible: {(high_op_mask & visible_mask).sum()}")

    # Gradient X/Y/Z ratio per group (visible only)
    groups = {
        'Z-outlier\n(|Z|>3m)': z_outlier_mask & visible_mask,
        'Low-opacity\nsurface': low_op_mask & visible_mask,
        'High-opacity\nsurface': high_op_mask & visible_mask,
    }

    print(f"\n  Gradient X/Y/Z analysis (visible Gaussians):")
    print(f"  {'Group':25s} | {'N':>7s} | {'|grad_x|':>10s} | {'|grad_y|':>10s} | {'|grad_z|':>10s} | {'z/x ratio':>10s}")
    print("  " + "-"*80)
    grad_table = {}
    for name, mask in groups.items():
        if mask.sum() == 0:
            continue
        gx = grad_x[mask].mean()
        gy = grad_y[mask].mean()
        gz = grad_z[mask].mean()
        ratio = gz / (gx + 1e-12)
        print(f"  {name.replace(chr(10),' '):25s} | {mask.sum():>7d} | {gx:10.3e} | {gy:10.3e} | {gz:10.3e} | {ratio:10.4f}")
        grad_table[name] = (gx, gy, gz, mask.sum())

    # ============================================================
    # Perturbation analysis: surface Gaussians (high-opacity)
    # ============================================================
    print(f"\n[Step 2] Perturbation analysis (surface Gaussians, N={N_PERTURB_GAUSSIANS})...")
    surf_visible = np.where(high_op_mask & visible_mask)[0]
    rng = np.random.default_rng(42)
    n_sample = min(N_PERTURB_GAUSSIANS, len(surf_visible))
    surf_idx = rng.choice(surf_visible, n_sample, replace=False)
    surf_idx_torch = torch.from_numpy(surf_idx).long()

    directions = {
        'X (depth axis)': np.array([1.0, 0.0, 0.0]),
        'Y (lateral)':    np.array([0.0, 1.0, 0.0]),
        'Z (vertical)':   np.array([0.0, 0.0, 1.0]),
    }

    perturb_results = {}
    for dir_name, dir_vec in directions.items():
        print(f"  Perturbing in {dir_name}...")
        results = perturbation_loss_curve(
            gaussians, cameras, pipe_args, bg_color,
            surf_idx_torch, dir_vec, PERTURB_DELTAS
        )
        perturb_results[dir_name] = results
        deltas = [r[0] for r in results]
        losses = [r[1] for r in results]
        base = losses[deltas.index(0.0)]
        for d, l in results:
            print(f"    delta={d:+.2f}m: loss={l:.6f}  (Δ={l-base:+.6f})")

    # ============================================================
    # Also perturb Z-outlier floaters
    # ============================================================
    print(f"\n[Step 3] Perturbation analysis (Z-outlier floaters, N=min(50,{z_outlier_mask.sum()}))...")
    floater_visible = np.where(z_outlier_mask)[0]
    n_f = min(50, len(floater_visible))
    floater_idx = rng.choice(floater_visible, n_f, replace=False)
    floater_idx_torch = torch.from_numpy(floater_idx).long()

    floater_perturb = {}
    for dir_name, dir_vec in directions.items():
        print(f"  Perturbing floater in {dir_name}...")
        results = perturbation_loss_curve(
            gaussians, cameras, pipe_args, bg_color,
            floater_idx_torch, dir_vec, PERTURB_DELTAS
        )
        floater_perturb[dir_name] = results

    # ============================================================
    # Figures
    # ============================================================
    print("\n[Step 4] Generating figures...")

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle('Round 3: X-axis Depth Flatness (P04) — Loss Landscape Analysis', fontsize=13, fontweight='bold')

    # Row 1: Surface Gaussians perturbation
    ax = axes[0, 0]
    colors = {'X (depth axis)': 'red', 'Y (lateral)': 'blue', 'Z (vertical)': 'green'}
    for dir_name, results in perturb_results.items():
        deltas = [r[0] for r in results]
        losses = [r[1] for r in results]
        base = losses[deltas.index(0.0)]
        delta_losses = [l - base for l in losses]
        ax.plot(deltas, delta_losses, 'o-', color=colors[dir_name], label=dir_name, linewidth=2)
    ax.axhline(y=0, color='k', linestyle=':', alpha=0.3)
    ax.axvline(x=0, color='k', linestyle=':', alpha=0.3)
    ax.set_xlabel('Perturbation (m)')
    ax.set_ylabel('ΔLoss (vs. base)')
    ax.set_title(f'Surface Gaussian Perturbation\n(N={n_sample} high-opacity)')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Row 1: Z-outlier floater perturbation
    ax = axes[0, 1]
    for dir_name, results in floater_perturb.items():
        deltas = [r[0] for r in results]
        losses = [r[1] for r in results]
        base = losses[deltas.index(0.0)]
        delta_losses = [l - base for l in losses]
        ax.plot(deltas, delta_losses, 'o-', color=colors[dir_name], label=dir_name, linewidth=2)
    ax.axhline(y=0, color='k', linestyle=':', alpha=0.3)
    ax.axvline(x=0, color='k', linestyle=':', alpha=0.3)
    ax.set_xlabel('Perturbation (m)')
    ax.set_ylabel('ΔLoss (vs. base)')
    ax.set_title(f'Z-outlier Floater Perturbation\n(N={n_f})')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Row 1, col 3: Gradient bar chart by group
    ax = axes[0, 2]
    group_names = list(grad_table.keys())
    x = np.arange(len(group_names))
    w = 0.25
    gx_arr = [grad_table[g][0] for g in group_names]
    gy_arr = [grad_table[g][1] for g in group_names]
    gz_arr = [grad_table[g][2] for g in group_names]
    ax.bar(x - w, gx_arr, w, label='|grad_X|', color='red', alpha=0.8)
    ax.bar(x,     gy_arr, w, label='|grad_Y|', color='blue', alpha=0.8)
    ax.bar(x + w, gz_arr, w, label='|grad_Z|', color='green', alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([g.replace('\n', '\n') for g in group_names], fontsize=8)
    ax.set_ylabel('Mean |gradient|')
    ax.set_title('Per-axis Gradient by Gaussian Group\n(1 backward pass)')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    # Row 2: Z-sensitivity analysis at different camera fractions
    ax = axes[1, 0]
    # Show surface perturbation zoomed to ±0.2m
    for dir_name, results in perturb_results.items():
        deltas = [r[0] for r in results if abs(r[0]) <= 0.2]
        losses = [r[1] for r in results if abs(r[0]) <= 0.2]
        base = losses[deltas.index(0.0)]
        delta_losses = [l - base for l in losses]
        ax.plot(deltas, delta_losses, 'o-', color=colors[dir_name], label=dir_name, linewidth=2, markersize=7)
    ax.axhline(y=0, color='k', linestyle=':', alpha=0.3)
    ax.axvline(x=0, color='k', linestyle=':', alpha=0.3)
    ax.set_xlabel('Perturbation (m)')
    ax.set_ylabel('ΔLoss (vs. base)')
    ax.set_title('Surface Gaussian (zoomed: ±0.2m)\nP04: X should be flattest')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Row 2: grad_z/grad_x vs opacity
    ax = axes[1, 1]
    vis = visible_mask & ~z_outlier_mask
    op_bins = np.linspace(0, 1, 21)
    ratio_by_op = []
    op_mids = []
    for i in range(len(op_bins)-1):
        mask = vis & (opacity >= op_bins[i]) & (opacity < op_bins[i+1])
        if mask.sum() > 10:
            rx = grad_x[mask].mean()
            rz = grad_z[mask].mean()
            ratio_by_op.append(rz / (rx + 1e-12))
            op_mids.append((op_bins[i] + op_bins[i+1]) / 2)
    ax.plot(op_mids, ratio_by_op, 'g-o', markersize=4)
    ax.axhline(y=1.0, color='k', linestyle='--', alpha=0.5, label='ratio=1.0')
    ax.set_xlabel('Opacity')
    ax.set_ylabel('grad_Z / grad_X ratio')
    ax.set_title('grad_Z/grad_X Ratio vs Opacity\n(higher opacity = surface Gaussians)')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Row 2: grad_z/grad_x vs |Z| position
    ax = axes[1, 2]
    vis2 = visible_mask
    z_bins = np.percentile(np.abs(xyz[vis2, 2]), np.linspace(0, 99, 20))
    z_mids = []
    ratio_by_z = []
    for i in range(len(z_bins)-1):
        mask = vis2 & (np.abs(xyz[:, 2]) >= z_bins[i]) & (np.abs(xyz[:, 2]) < z_bins[i+1])
        if mask.sum() > 5:
            rx = grad_x[mask].mean()
            rz = grad_z[mask].mean()
            ratio_by_z.append(rz / (rx + 1e-12))
            z_mids.append((z_bins[i] + z_bins[i+1]) / 2)
    ax.plot(z_mids, ratio_by_z, 'b-o', markersize=4)
    ax.axhline(y=1.0, color='k', linestyle='--', alpha=0.5, label='ratio=1.0')
    ax.set_xlabel('|Z| (m)')
    ax.set_ylabel('grad_Z / grad_X ratio')
    ax.set_title('grad_Z/grad_X Ratio vs |Z| Position\n(Z-outliers should have ratio→0)')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = OUT_DIR / 'round3_perturbation_analysis.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"\nSaved: {out_path}")

    # Print summary
    print("\n=== ROUND 3 SUMMARY ===")
    print("\nSurface Gaussian perturbation (loss sensitivity):")
    for dir_name, results in perturb_results.items():
        deltas = [r[0] for r in results]
        losses = [r[1] for r in results]
        base = losses[deltas.index(0.0)]
        # sensitivity = max |ΔLoss| at ±0.1m perturbation
        nearby = [(d, l) for d, l in zip(deltas, losses) if abs(d) == 0.1]
        if nearby:
            sens = np.mean([abs(l - base) for _, l in nearby])
            print(f"  {dir_name:20s}: sensitivity at ±0.1m = {sens:.6f}")

    print("\nFloater Gaussian perturbation (loss sensitivity):")
    for dir_name, results in floater_perturb.items():
        deltas = [r[0] for r in results]
        losses = [r[1] for r in results]
        base = losses[deltas.index(0.0)]
        nearby = [(d, l) for d, l in zip(deltas, losses) if abs(d) == 0.1]
        if nearby:
            sens = np.mean([abs(l - base) for _, l in nearby])
            print(f"  {dir_name:20s}: sensitivity at ±0.1m = {sens:.6f}")

if __name__ == '__main__':
    main()
