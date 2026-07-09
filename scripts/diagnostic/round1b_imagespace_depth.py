"""
Round 1b: Image-Space Ray-Based Depth Residual

Round 1a의 문제: 3D nearest sparse point는 너무 촘촘해서 (median 2.5cm) 방향 정보가 없음.
수정: 각 카메라에서 Gaussian을 projection하고, 같은 픽셀에 project되는 sparse point의 depth와 비교.
이 방식이 "같은 ray 방향에서 Gaussian이 표면보다 앞에 있는가"를 직접 측정한다.

추가 분석:
- 43% 비측정 Gaussian의 공간 분포 (floater 후보?)
- ambiguity map과의 상관관계
- SH energy vs depth position
"""

import numpy as np
import struct
import os
import time
from scipy.spatial import KDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict

RESULT_DIR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/exp08_openmavis_full_dens_until7000_prune001_beta1_low_20260616_124504"
DATASET_DIR = "/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253"
OUT_DIR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic"

PLY_PATH  = os.path.join(RESULT_DIR, "point_cloud/iteration_30000/point_cloud.ply")
CAMERAS_TXT = os.path.join(DATASET_DIR, "sparse/0/cameras.txt")
IMAGES_TXT  = os.path.join(DATASET_DIR, "sparse/0/images.txt")
POINTS3D_TXT = os.path.join(DATASET_DIR, "sparse/0/points3D.txt")

# 카메라는 stride=20으로 줄이고 각 카메라당 image-space grid 방식 사용
CAMERA_STRIDE = 20     # ~66 cameras
PIXEL_RADIUS  = 8      # sparse point를 Gaussian pixel에서 얼마나 멀리까지 허용 (pixels)
DEPTH_IN_FRONT_THRESH = -0.15  # 이것보다 작으면 empty space floater (m)


# ── 유틸 ──────────────────────────────────────────────────────────────────────

def quat_to_rot(qw, qx, qy, qz):
    return np.array([
        [1-2*(qy*qy+qz*qz), 2*(qx*qy-qz*qw), 2*(qx*qz+qy*qw)],
        [2*(qx*qy+qz*qw), 1-2*(qx*qx+qz*qz), 2*(qy*qz-qx*qw)],
        [2*(qx*qz-qy*qw), 2*(qy*qz+qx*qw), 1-2*(qx*qx+qy*qy)],
    ])


def load_gaussian_ply(path):
    with open(path, 'rb') as f:
        header = []
        while True:
            line = f.readline().decode('ascii').strip()
            header.append(line)
            if line == 'end_header':
                break
        props = [h.split()[-1] for h in header if h.startswith('property float')]
        n = next(int(h.split()[-1]) for h in header if h.startswith('element vertex'))
        data = np.frombuffer(f.read(), dtype=np.float32).reshape(n, len(props))
    idx = {p: i for i, p in enumerate(props)}
    xyz    = data[:, [idx['x'], idx['y'], idx['z']]]
    raw_op = data[:, idx['opacity']]
    opacity = 1.0 / (1.0 + np.exp(-raw_op))
    scale   = np.exp(data[:, [idx['scale_0'], idx['scale_1'], idx['scale_2']]])
    dc      = data[:, [idx['f_dc_0'], idx['f_dc_1'], idx['f_dc_2']]]
    rest    = [i for p, i in idx.items() if p.startswith('f_rest_')]
    sh_rest = np.sqrt((data[:, rest]**2).mean(axis=1)) if rest else np.zeros(n)
    print(f"[PLY] {n} Gaussians | opacity {opacity.min():.3f}~{opacity.max():.3f}")
    return xyz, opacity, scale, sh_rest


def load_cameras(cameras_txt, images_txt, stride=1):
    intrinsics = {}
    with open(cameras_txt) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            p = line.split()
            cam_id = int(p[0])
            W, H = int(p[2]), int(p[3])
            fx, fy, cx, cy = float(p[4]), float(p[5]), float(p[6]), float(p[7])
            intrinsics[cam_id] = dict(W=W, H=H, fx=fx, fy=fy, cx=cx, cy=cy)
    cameras = []
    with open(images_txt) as f:
        lines = [l.strip() for l in f if not l.startswith('#') and l.strip()]
    for i, line in enumerate(lines):
        if i % stride != 0:
            continue
        p = line.split()
        if len(p) < 9:
            continue
        qw,qx,qy,qz = float(p[1]),float(p[2]),float(p[3]),float(p[4])
        tx,ty,tz     = float(p[5]),float(p[6]),float(p[7])
        cam_id = int(p[8])
        R = quat_to_rot(qw,qx,qy,qz)
        t = np.array([tx,ty,tz])
        center = -R.T @ t
        cameras.append(dict(R=R, t=t, center=center, **intrinsics[cam_id]))
    print(f"[CAM] {len(cameras)} cameras (stride={stride})")
    return cameras


def load_sparse_points(path):
    pts = []
    with open(path) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            p = line.split()
            pts.append([float(p[1]), float(p[2]), float(p[3])])
    pts = np.array(pts, dtype=np.float32)
    print(f"[SPT] {len(pts)} sparse points | range X:{pts[:,0].min():.1f}~{pts[:,0].max():.1f} Z:{pts[:,2].min():.1f}~{pts[:,2].max():.1f}")
    return pts


def project(xyz, cam):
    """Returns u, v, depth, in_fov for [N,3] world points."""
    p = (cam['R'] @ xyz.T).T + cam['t']
    d = p[:, 2]
    valid = d > 0.05
    u = cam['fx'] * p[:, 0] / np.where(valid, d, 1e-6) + cam['cx']
    v = cam['fy'] * p[:, 1] / np.where(valid, d, 1e-6) + cam['cy']
    in_fov = valid & (u >= 0) & (u < cam['W']) & (v >= 0) & (v < cam['H'])
    return u, v, d, in_fov


# ── 핵심: image-space depth residual ─────────────────────────────────────────

def build_sparse_depth_grid(sparse_pts, cam, cell_size=4):
    """
    Sparse points를 camera image space로 project한 후,
    각 cell의 minimum depth를 저장하는 grid 반환.
    cell_size: 몇 픽셀 단위로 bin 합치는지 (속도 조절)
    """
    W, H = cam['W'], cam['H']
    grid_W = W // cell_size + 1
    grid_H = H // cell_size + 1
    depth_grid = np.full((grid_H, grid_W), np.inf, dtype=np.float32)

    u, v, d, in_fov = project(sparse_pts, cam)
    valid = in_fov
    if valid.sum() == 0:
        return depth_grid, cell_size

    cu = (u[valid] / cell_size).astype(np.int32)
    cv = (v[valid] / cell_size).astype(np.int32)
    cu = np.clip(cu, 0, grid_W - 1)
    cv = np.clip(cv, 0, grid_H - 1)
    dv = d[valid]

    # min depth per cell (loop-free approach via numpy)
    linear_idx = cv * grid_W + cu
    order = np.argsort(linear_idx)
    linear_idx = linear_idx[order]
    dv = dv[order]
    _, first_occ = np.unique(linear_idx, return_index=True)
    min_d = np.minimum.reduceat(dv, first_occ)
    unique_idx = linear_idx[first_occ]
    depth_grid.flat[unique_idx] = np.minimum(depth_grid.flat[unique_idx], min_d)

    return depth_grid, cell_size


def lookup_surface_depth(u_px, v_px, depth_grid, cell_size, radius_cells=2):
    """
    pixel (u, v) 주변 radius_cells 내에서 minimum surface depth lookup.
    Returns NaN if no sparse point nearby.
    """
    grid_H, grid_W = depth_grid.shape
    cu = int(u_px / cell_size)
    cv = int(v_px / cell_size)
    cu0, cu1 = max(0, cu - radius_cells), min(grid_W, cu + radius_cells + 1)
    cv0, cv1 = max(0, cv - radius_cells), min(grid_H, cv + radius_cells + 1)
    patch = depth_grid[cv0:cv1, cu0:cu1]
    min_d = patch.min()
    return min_d if min_d < np.inf else np.nan


def compute_imagespace_depth_residual(xyz_gauss, cameras, sparse_pts):
    """
    Vectorized image-space depth residual.
    Per camera:
      1. sparse points → cell depth grid (min depth per cell)
      2. all Gaussians → project → dilated cell lookup (batch numpy indexing)
    """
    N = len(xyz_gauss)
    residual_sum   = np.zeros(N, dtype=np.float64)
    residual_count = np.zeros(N, dtype=np.int32)
    in_front_sum   = np.zeros(N, dtype=np.int32)
    visible_count  = np.zeros(N, dtype=np.int32)

    cell_size = 4
    radius_cells = PIXEL_RADIUS // cell_size + 1

    # Precompute offset pairs for dilation window (2r+1)^2 patches
    off = np.arange(-radius_cells, radius_cells + 1)
    du_off, dv_off = np.meshgrid(off, off)
    du_off = du_off.ravel()   # (K,)
    dv_off = dv_off.ravel()   # (K,)

    t0 = time.time()
    for ci, cam in enumerate(cameras):
        if ci % 10 == 0:
            elapsed = time.time() - t0
            print(f"  cam {ci}/{len(cameras)} ({elapsed:.0f}s elapsed)")

        W, H = cam['W'], cam['H']
        grid_W = W // cell_size + 1
        grid_H = H // cell_size + 1

        # 1. sparse depth grid
        depth_grid, cs = build_sparse_depth_grid(sparse_pts, cam, cell_size=cell_size)

        # 2. project all Gaussians
        ug, vg, dg, fov_g = project(xyz_gauss, cam)
        vis_idx = np.where(fov_g)[0]
        if len(vis_idx) == 0:
            continue

        visible_count[vis_idx] += 1

        # 3. vectorized dilation lookup: (M, K) cell indices
        cu_v = (ug[vis_idx] / cell_size).astype(np.int32)
        cv_v = (vg[vis_idx] / cell_size).astype(np.int32)
        dg_v = dg[vis_idx]
        M = len(vis_idx)

        cu_all = np.clip(cu_v[:, None] + du_off[None, :], 0, grid_W - 1)   # (M, K)
        cv_all = np.clip(cv_v[:, None] + dv_off[None, :], 0, grid_H - 1)   # (M, K)

        patch_depths = depth_grid[cv_all, cu_all]       # (M, K)
        surface_d = patch_depths.min(axis=1)            # (M,) — inf if no sparse pt nearby

        has_spt = surface_d < np.inf
        if has_spt.sum() == 0:
            continue

        gi_with = vis_idx[has_spt]
        residual = dg_v[has_spt] - surface_d[has_spt]
        np.add.at(residual_sum,   gi_with, residual)
        np.add.at(residual_count, gi_with, 1)
        in_front = residual < DEPTH_IN_FRONT_THRESH
        np.add.at(in_front_sum, gi_with[in_front], 1)

    depth_residual = np.where(
        residual_count > 0,
        residual_sum / residual_count,
        np.nan
    )
    in_front_freq = np.where(
        visible_count > 0,
        in_front_sum / visible_count,
        np.nan
    )

    has_meas = ~np.isnan(depth_residual)
    print(f"\n[METRIC] Measurement coverage: {has_meas.sum():,}/{N:,} ({100*has_meas.mean():.1f}%)")
    print(f"[METRIC] Median visible_count per Gaussian: {np.median(visible_count):.0f}")
    return depth_residual, in_front_freq, visible_count


# ── 분석: 측정 안 된 Gaussian (coverage gap) ─────────────────────────────────

def analyze_coverage_gap(xyz_gauss, opacity, scale, sh_rest, visible_count,
                         depth_residual, cameras, out_dir):
    """
    visible하지만 sparse point reference가 없는 Gaussian 분석.
    이 그룹이 empty space floater의 핵심일 수 있다.
    """
    no_ref = np.isnan(depth_residual) & (visible_count > 0)   # 보이는데 reference 없음
    not_vis = visible_count == 0                                # 아예 안 보임
    has_ref = ~np.isnan(depth_residual)                        # 정상 측정

    print(f"\n[GAP] Coverage Analysis:")
    print(f"  has_reference: {has_ref.sum():,} ({100*has_ref.mean():.1f}%)")
    print(f"  visible_no_ref: {no_ref.sum():,} ({100*no_ref.mean():.1f}%)")
    print(f"  not_visible:   {not_vis.sum():,} ({100*not_vis.mean():.1f}%)")

    # visible_no_ref 그룹의 opacity 분포 vs has_ref 그룹
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle("Round 1b: Coverage Gap Analysis\n(Gaussians visible but without sparse reference)", fontsize=13)

    # ① 세 그룹의 opacity 분포 비교
    ax = axes[0, 0]
    bins = np.linspace(0, 1, 60)
    ax.hist(opacity[has_ref],   bins=bins, alpha=0.5, color='green',  label=f'has_ref (n={has_ref.sum():,})', density=True)
    ax.hist(opacity[no_ref],    bins=bins, alpha=0.5, color='orange', label=f'visible_no_ref (n={no_ref.sum():,})', density=True)
    ax.hist(opacity[not_vis],   bins=bins, alpha=0.5, color='red',    label=f'not_visible (n={not_vis.sum():,})', density=True)
    ax.set_xlabel("opacity"); ax.set_ylabel("density")
    ax.set_title("(1) Opacity by Coverage Group")
    ax.legend(fontsize=8)

    # ② scale_max 분포 비교
    ax = axes[0, 1]
    scale_max = scale.max(axis=1)
    ax.hist(np.log10(scale_max[has_ref]+1e-6),  bins=60, alpha=0.5, color='green',  label='has_ref', density=True)
    ax.hist(np.log10(scale_max[no_ref]+1e-6),   bins=60, alpha=0.5, color='orange', label='visible_no_ref', density=True)
    ax.set_xlabel("log10(scale_max)"); ax.set_ylabel("density")
    ax.set_title("(2) Scale by Coverage Group")
    ax.legend(fontsize=8)

    # ③ SH rest energy 분포 비교
    ax = axes[0, 2]
    ax.hist(sh_rest[has_ref],  bins=60, alpha=0.5, color='green',  label='has_ref', density=True)
    ax.hist(sh_rest[no_ref],   bins=60, alpha=0.5, color='orange', label='visible_no_ref', density=True)
    ax.set_xlabel("SH rest energy"); ax.set_ylabel("density")
    ax.set_title("(3) SH Energy by Coverage Group (P05 check)")
    ax.legend(fontsize=8)

    # ④ XZ 공간 분포: has_ref vs no_ref (top-down view, Z=height in scene)
    ax = axes[1, 0]
    s = np.random.choice(np.where(has_ref)[0], min(3000, has_ref.sum()), replace=False)
    s2 = np.random.choice(np.where(no_ref)[0], min(3000, no_ref.sum()), replace=False)
    ax.scatter(xyz_gauss[s, 0], xyz_gauss[s, 1],   s=1, alpha=0.3, color='green',  label='has_ref')
    ax.scatter(xyz_gauss[s2, 0], xyz_gauss[s2, 1], s=1, alpha=0.3, color='orange', label='visible_no_ref')
    # camera trajectory
    cam_centers = np.array([c['center'] for c in cameras])
    ax.plot(cam_centers[:, 0], cam_centers[:, 1], 'b-', linewidth=1, alpha=0.5, label='trajectory')
    ax.set_xlabel("X (m)"); ax.set_ylabel("Y (m)")
    ax.set_title("(4) Top-down: Coverage Gap Spatial Distribution")
    ax.legend(fontsize=8); ax.set_aspect('equal')

    # ⑤ XZ side view: camera Z is ~0, scene extends in Z
    ax = axes[1, 1]
    ax.scatter(xyz_gauss[s, 0], xyz_gauss[s, 2],   s=1, alpha=0.3, color='green',  label='has_ref')
    ax.scatter(xyz_gauss[s2, 0], xyz_gauss[s2, 2], s=1, alpha=0.3, color='orange', label='visible_no_ref')
    ax.axhline(cam_centers[:, 2].mean(), color='blue', linestyle='--', linewidth=1, label='cam height')
    ax.set_xlabel("X (m)"); ax.set_ylabel("Z (m)")
    ax.set_title("(5) Side view: Coverage Gap Z distribution\n(P01: ray void at certain heights?)")
    ax.legend(fontsize=8)

    # ⑥ visible_count histogram
    ax = axes[1, 2]
    ax.hist(visible_count[has_ref],  bins=50, alpha=0.5, color='green',  label='has_ref', density=True)
    ax.hist(visible_count[no_ref],   bins=50, alpha=0.5, color='orange', label='visible_no_ref', density=True)
    ax.set_xlabel("visible_count (cameras seeing this Gaussian)")
    ax.set_ylabel("density")
    ax.set_title("(6) Camera Visibility Count by Group")
    ax.legend(fontsize=8)

    plt.tight_layout()
    path = os.path.join(out_dir, "round1b_coverage_gap.png")
    plt.savefig(path, dpi=120, bbox_inches='tight')
    print(f"[PLOT] {path}")
    plt.close()

    return no_ref, not_vis


def make_depth_residual_plots(opacity, scale, sh_rest, depth_residual, in_front_freq, out_dir):
    valid = ~np.isnan(depth_residual)
    dr = depth_residual[valid]
    floater_mask = valid & (depth_residual < DEPTH_IN_FRONT_THRESH)
    scale_max = scale.max(axis=1)

    print(f"\n[RESULT] Image-space depth residual summary:")
    print(f"  measured: {valid.sum():,} ({100*valid.mean():.1f}%)")
    print(f"  floater (dr<{DEPTH_IN_FRONT_THRESH}): {floater_mask.sum():,} ({100*floater_mask.mean():.1f}%)")
    print(f"  dr mean: {dr.mean():.3f}m  median: {np.median(dr):.3f}m")

    low_op = opacity < 0.1
    both = floater_mask & low_op
    dr_only = floater_mask & ~low_op
    op_only = ~floater_mask & low_op & valid

    print(f"\n[OVERLAP] floater vs low-opacity:")
    print(f"  dr_only (missed by opacity): {dr_only.sum():,}")
    print(f"  op_only (over-pruned):       {op_only.sum():,}")
    print(f"  both:                        {both.sum():,}")

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle("Round 1b: Image-Space Depth Residual Analysis", fontsize=13)

    ax = axes[0, 0]
    ax.hist(dr[np.abs(dr) < 5], bins=100, color='salmon')
    ax.axvline(0, color='black', linewidth=1.5)
    ax.axvline(DEPTH_IN_FRONT_THRESH, color='red', linestyle='--', label=f'floater thresh')
    ax.set_xlabel("depth residual (m)  [negative = in empty space]")
    ax.set_title(f"(1) Image-Space Depth Residual Histogram (n={valid.sum():,})")
    ax.legend()

    ax = axes[0, 1]
    s = np.random.choice(np.where(valid)[0], min(8000, valid.sum()), replace=False)
    sc = ax.scatter(opacity[s], depth_residual[s], c=depth_residual[s],
                    cmap='RdYlGn', s=2, alpha=0.5, vmin=-2, vmax=2)
    ax.axhline(0, color='black', linewidth=1)
    ax.axhline(DEPTH_IN_FRONT_THRESH, color='red', linestyle='--')
    ax.set_xlabel("opacity"); ax.set_ylabel("depth residual (m)")
    ax.set_title("(2) Opacity vs Depth Residual\n[key: do floaters have low opacity?]")
    plt.colorbar(sc, ax=ax)

    ax = axes[0, 2]
    ax.hist(dr[low_op[valid]], bins=60, alpha=0.6, color='red',
            label=f'opacity<0.1 (n={low_op.sum():,})', density=True)
    ax.hist(dr[~low_op[valid]], bins=60, alpha=0.6, color='steelblue',
            label=f'opacity≥0.1 (n={(~low_op).sum():,})', density=True)
    ax.axvline(0, color='black', linewidth=1.5)
    ax.axvline(DEPTH_IN_FRONT_THRESH, color='red', linestyle='--')
    ax.set_title("(3) Depth Residual: low-op vs high-op\n[KEY: are floaters captured by opacity?]")
    ax.legend(fontsize=8)

    ax = axes[1, 0]
    if valid.sum() > 0 and ~np.isnan(in_front_freq).all():
        valid2 = ~np.isnan(in_front_freq)
        ax.hist(in_front_freq[valid2], bins=50, color='mediumpurple')
        ax.axvline(0.5, color='red', linestyle='--', label='50%')
        ax.set_xlabel("in_front_frequency (fraction of cameras where Gaussian < surface depth)")
        ax.set_title("(4) In-Front Frequency\n(image-space version, per-camera)")
        ax.legend()

    ax = axes[1, 1]
    ax.scatter(np.log10(scale_max[s]+1e-6), depth_residual[s],
               c=opacity[s], cmap='plasma', s=2, alpha=0.4, vmin=0, vmax=1)
    ax.axhline(DEPTH_IN_FRONT_THRESH, color='red', linestyle='--')
    ax.axhline(0, color='black', linewidth=1)
    ax.set_xlabel("log10(scale_max)"); ax.set_ylabel("depth residual (m)")
    ax.set_title("(5) Scale vs Depth Residual (P08: large-scale masking?)")

    ax = axes[1, 2]
    ax.scatter(sh_rest[s], depth_residual[s],
               c=opacity[s], cmap='viridis', s=2, alpha=0.4, vmin=0, vmax=1)
    ax.axhline(DEPTH_IN_FRONT_THRESH, color='red', linestyle='--')
    ax.axhline(0, color='black', linewidth=1)
    ax.set_xlabel("SH rest energy"); ax.set_ylabel("depth residual (m)")
    ax.set_title("(6) SH Energy vs Depth Residual (P05: DOF compensation?)")

    plt.tight_layout()
    path = os.path.join(out_dir, "round1b_depth_residual.png")
    plt.savefig(path, dpi=120, bbox_inches='tight')
    print(f"[PLOT] {path}")
    plt.close()

    return floater_mask


def write_colored_ply(xyz, opacity, depth_residual, in_front_freq, floater_mask,
                      no_ref_mask, out_path):
    N = len(xyz)
    valid = ~np.isnan(depth_residual)
    colors = np.full((N, 3), 150, dtype=np.uint8)
    colors[valid & (depth_residual >= 0)] = [50, 200, 50]    # 초록: 표면 근처
    colors[valid & (depth_residual < 0) & ~floater_mask] = [255, 200, 50]   # 노랑: 살짝 앞
    colors[floater_mask] = [255, 50, 50]                      # 빨강: empty space floater
    colors[no_ref_mask] = [80, 80, 255]                       # 파랑: visible but no reference
    # gray: not visible

    with open(out_path, 'w') as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {N}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write("property float opacity\nproperty float depth_residual\n")
        f.write("end_header\n")
        for i in range(N):
            dr = depth_residual[i] if valid[i] else float('nan')
            f.write(f"{xyz[i,0]:.4f} {xyz[i,1]:.4f} {xyz[i,2]:.4f} "
                    f"{int(colors[i,0])} {int(colors[i,1])} {int(colors[i,2])} "
                    f"{opacity[i]:.4f} {dr:.4f}\n")
    print(f"[PLY] Colored PLY: {out_path}")
    print(f"      RED=floater | BLUE=visible_no_ref | GREEN=surface | GRAY=not_visible")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    t_start = time.time()

    xyz, opacity, scale, sh_rest = load_gaussian_ply(PLY_PATH)
    cameras   = load_cameras(CAMERAS_TXT, IMAGES_TXT, stride=CAMERA_STRIDE)
    sparse_pts = load_sparse_points(POINTS3D_TXT)

    print(f"\n[INFO] Camera height (Z): {np.array([c['center'][2] for c in cameras]).mean():.3f}m "
          f"(±{np.array([c['center'][2] for c in cameras]).std():.3f})")

    print("\n[METRIC] Computing image-space depth residual...")
    depth_residual, in_front_freq, visible_count = compute_imagespace_depth_residual(
        xyz, cameras, sparse_pts
    )

    no_ref_mask, not_vis_mask = analyze_coverage_gap(
        xyz, opacity, scale, sh_rest, visible_count, depth_residual, cameras, OUT_DIR
    )

    floater_mask = make_depth_residual_plots(
        opacity, scale, sh_rest, depth_residual, in_front_freq, OUT_DIR
    )

    ply_out = os.path.join(OUT_DIR, "round1b_floater_colored.ply")
    write_colored_ply(xyz, opacity, depth_residual, in_front_freq,
                      floater_mask, no_ref_mask, ply_out)

    # Save results
    npz_path = os.path.join(OUT_DIR, "round1b_results.npz")
    np.savez(npz_path,
             xyz=xyz, opacity=opacity,
             depth_residual=depth_residual,
             in_front_freq=in_front_freq,
             visible_count=visible_count,
             floater_mask=floater_mask,
             no_ref_mask=no_ref_mask)
    print(f"[OUT] {npz_path}")
    print(f"\n[DONE] {(time.time()-t_start)/60:.1f} min")


if __name__ == "__main__":
    main()
