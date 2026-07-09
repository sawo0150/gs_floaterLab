"""
Round 1 Diagnostic: Empty Space Floater Detection via Depth Residual

각 Gaussian에 대해 다음을 계산한다:
1. dist_to_nearest_sparse: 3D 공간에서 가장 가까운 sparse point까지의 거리
2. in_front_ratio: 카메라보다 sparse point가 뒤에 있는 카메라 비율 (Gaussian이 앞에 있으면 = floater)
3. depth_residual: 카메라로 project 시 Gaussian depth - 같은 픽셀 방향의 sparse point depth

출력:
- results/diagnostic/round1_depth_residual.npz: per-Gaussian 분석 결과
- results/diagnostic/round1_*.png: 시각화 플롯들
- results/diagnostic/round1_floater_colored.ply: depth_residual로 색칠된 PLY
"""

import numpy as np
import struct
import os
import time
from scipy.spatial import KDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── 경로 설정 ─────────────────────────────────────────────────────────────────

RESULT_DIR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/exp08_openmavis_full_dens_until7000_prune001_beta1_low_20260616_124504"
DATASET_DIR = "/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253"
OUT_DIR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic"

PLY_PATH = os.path.join(RESULT_DIR, "point_cloud/iteration_30000/point_cloud.ply")
CAMERAS_TXT = os.path.join(DATASET_DIR, "sparse/0/cameras.txt")
IMAGES_TXT  = os.path.join(DATASET_DIR, "sparse/0/images.txt")
POINTS3D_TXT = os.path.join(DATASET_DIR, "sparse/0/points3D.txt")

CAMERA_SAMPLE_STEP = 5    # 1311 중 매 5번째 카메라만 사용 (~262개)
DEPTH_RESIDUAL_CAM_LIMIT = 50  # per-Gaussian depth_residual 계산 시 최대 카메라 수


# ── 1. PLY 로딩 ───────────────────────────────────────────────────────────────

def load_gaussian_ply(path):
    print(f"[PLY] Loading {path}")
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
    xyz     = data[:, [idx['x'], idx['y'], idx['z']]]
    raw_op  = data[:, idx['opacity']]
    opacity = 1.0 / (1.0 + np.exp(-raw_op))  # sigmoid
    scale   = np.exp(data[:, [idx['scale_0'], idx['scale_1'], idx['scale_2']]])

    # DC color (SH degree 0) → view-independent color
    dc = data[:, [idx['f_dc_0'], idx['f_dc_1'], idx['f_dc_2']]]
    color_rgb = 0.5 + dc * 0.2820947917738781  # SH C0 coefficient

    # Higher-order SH energy (view-dependent part)
    rest_cols = [i for p, i in idx.items() if p.startswith('f_rest_')]
    sh_rest_energy = np.sqrt((data[:, rest_cols] ** 2).mean(axis=1)) if rest_cols else np.zeros(n)

    print(f"[PLY] Loaded {n} Gaussians | opacity: {opacity.min():.3f}~{opacity.max():.3f}")
    return xyz, opacity, scale, color_rgb, sh_rest_energy, props, data, idx


# ── 2. Camera 로딩 ────────────────────────────────────────────────────────────

def quat_to_rotation(qw, qx, qy, qz):
    """COLMAP quaternion (w,x,y,z) → 3x3 rotation matrix (world-to-camera)."""
    R = np.array([
        [1 - 2*(qy*qy + qz*qz), 2*(qx*qy - qz*qw), 2*(qx*qz + qy*qw)],
        [2*(qx*qy + qz*qw), 1 - 2*(qx*qx + qz*qz), 2*(qy*qz - qx*qw)],
        [2*(qx*qz - qy*qw), 2*(qy*qz + qx*qw), 1 - 2*(qx*qx + qy*qy)],
    ])
    return R


def load_cameras(cameras_txt, images_txt, sample_step=1):
    """Returns list of dicts: {R, t, center, fx, fy, cx, cy, W, H}"""
    # Parse intrinsics
    intrinsics = {}
    with open(cameras_txt) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split()
            cam_id = int(parts[0])
            model = parts[1]
            W, H = int(parts[2]), int(parts[3])
            if model == 'PINHOLE':
                fx, fy, cx, cy = float(parts[4]), float(parts[5]), float(parts[6]), float(parts[7])
            else:
                raise ValueError(f"Unsupported model: {model}")
            intrinsics[cam_id] = dict(W=W, H=H, fx=fx, fy=fy, cx=cx, cy=cy)

    # Parse image poses
    cameras = []
    with open(images_txt) as f:
        lines = [l.strip() for l in f if not l.startswith('#') and l.strip()]

    for i, line in enumerate(lines):
        if i % sample_step != 0:
            continue
        parts = line.split()
        if len(parts) < 9:
            continue
        img_id = int(parts[0])
        qw, qx, qy, qz = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
        tx, ty, tz = float(parts[5]), float(parts[6]), float(parts[7])
        cam_id = int(parts[8])

        R = quat_to_rotation(qw, qx, qy, qz)
        t = np.array([tx, ty, tz])
        center = -R.T @ t  # camera center in world

        cam = dict(R=R, t=t, center=center, img_id=img_id, **intrinsics[cam_id])
        cameras.append(cam)

    print(f"[CAM] Loaded {len(cameras)} cameras (step={sample_step})")
    return cameras


# ── 3. Sparse 3D Points 로딩 ──────────────────────────────────────────────────

def load_sparse_points(points3d_txt):
    print(f"[SPT] Loading {points3d_txt}")
    pts = []
    with open(points3d_txt) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split()
            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
            pts.append([x, y, z])
    pts = np.array(pts, dtype=np.float32)
    print(f"[SPT] Loaded {len(pts)} sparse points")
    return pts


# ── 4. Projection 유틸 ────────────────────────────────────────────────────────

def project_to_camera(xyz_world, cam):
    """xyz_world: [N,3] → returns uvd: [N,3] (u,v,depth), valid: [N] bool"""
    p_cam = (cam['R'] @ xyz_world.T).T + cam['t']
    depth = p_cam[:, 2]
    valid = depth > 0.1
    u = cam['fx'] * p_cam[:, 0] / np.maximum(depth, 1e-6) + cam['cx']
    v = cam['fy'] * p_cam[:, 1] / np.maximum(depth, 1e-6) + cam['cy']
    in_fov = valid & (u >= 0) & (u < cam['W']) & (v >= 0) & (v < cam['H'])
    return u, v, depth, in_fov


# ── 5. 핵심 분석 ──────────────────────────────────────────────────────────────

def compute_metrics(xyz_gauss, opacity, scale, cameras, sparse_pts):
    N = len(xyz_gauss)
    print(f"\n[METRIC] Computing metrics for {N} Gaussians...")

    # (a) 3D nearest sparse point distance
    print("[METRIC] Building KDTree on sparse points...")
    t0 = time.time()
    tree = KDTree(sparse_pts)
    dist_3d, nearest_idx = tree.query(xyz_gauss, k=1, workers=-1)
    nearest_sparse_xyz = sparse_pts[nearest_idx]
    print(f"[METRIC] KDTree query done in {time.time()-t0:.1f}s")

    # (b) In-front ratio: fraction of cameras where Gaussian is closer than sparse point
    print("[METRIC] Computing in-front ratio...")
    t0 = time.time()
    in_front_count = np.zeros(N, dtype=np.int32)
    visible_count  = np.zeros(N, dtype=np.int32)
    cam_centers = np.array([c['center'] for c in cameras])  # [C, 3]

    # Vectorized: for each camera, dist(Gauss, cam) vs dist(Nearest, cam)
    for c in cameras:
        cc = c['center']
        d_gauss   = np.linalg.norm(xyz_gauss - cc, axis=1)        # [N]
        d_sparse  = np.linalg.norm(nearest_sparse_xyz - cc, axis=1)  # [N]
        # Only count cameras where Gaussian is roughly in FOV (rough check via angle)
        ray_dir = xyz_gauss - cc
        fwd = c['R'][2]  # camera forward in world
        cos_angle = np.dot(ray_dir / (np.linalg.norm(ray_dir, axis=1, keepdims=True) + 1e-8), fwd)
        roughly_visible = cos_angle > 0.5  # within ~60 deg
        visible_count  += roughly_visible.astype(np.int32)
        in_front_count += (roughly_visible & (d_gauss < d_sparse)).astype(np.int32)

    in_front_ratio = np.where(visible_count > 0, in_front_count / visible_count, 0.5)
    print(f"[METRIC] In-front ratio done in {time.time()-t0:.1f}s")

    # (c) Depth residual: projection-based (subsample of cameras)
    print(f"[METRIC] Computing depth residual (up to {DEPTH_RESIDUAL_CAM_LIMIT} cameras each)...")
    t0 = time.time()
    depth_residual_sum   = np.zeros(N, dtype=np.float64)
    depth_residual_count = np.zeros(N, dtype=np.int32)

    # For each camera, project all Gaussians + their nearest sparse points
    cam_subset = cameras[:DEPTH_RESIDUAL_CAM_LIMIT]
    for ci, cam in enumerate(cam_subset):
        if ci % 10 == 0:
            print(f"  cam {ci}/{len(cam_subset)}")

        # Project Gaussians
        ug, vg, dg, valid_g = project_to_camera(xyz_gauss, cam)

        # Project corresponding nearest sparse points
        us, vs, ds, valid_s = project_to_camera(nearest_sparse_xyz, cam)

        # Both must be valid AND sparse point must be within ~20 pixels of Gaussian
        pixel_dist = np.sqrt((ug - us)**2 + (vg - vs)**2)
        close_enough = pixel_dist < 40  # pixels

        both_valid = valid_g & valid_s & close_enough & (ds > 0.1)
        residual = dg - ds  # negative = Gaussian is closer than surface = in empty space

        depth_residual_sum   += np.where(both_valid, residual, 0.0)
        depth_residual_count += both_valid.astype(np.int32)

    depth_residual = np.where(
        depth_residual_count > 0,
        depth_residual_sum / depth_residual_count,
        np.nan
    )
    print(f"[METRIC] Depth residual done in {time.time()-t0:.1f}s")
    has_residual = ~np.isnan(depth_residual)
    print(f"  {has_residual.sum()} / {N} Gaussians have depth residual measurement")

    return dist_3d, in_front_ratio, depth_residual, visible_count


# ── 6. 시각화 ─────────────────────────────────────────────────────────────────

def make_plots(opacity, scale, sh_rest_energy, dist_3d, in_front_ratio, depth_residual, out_dir):
    scale_max = scale.max(axis=1)
    valid = ~np.isnan(depth_residual)

    fig, axes = plt.subplots(3, 3, figsize=(18, 14))
    fig.suptitle("Round 1: Empty Space Floater Diagnostics (exp08 iter30000)", fontsize=14)

    # ① opacity histogram
    ax = axes[0, 0]
    ax.hist(opacity, bins=100, color='steelblue', edgecolor='none')
    ax.axvline(0.1, color='red', linestyle='--', label='threshold=0.1')
    ax.set_xlabel("opacity"); ax.set_ylabel("count")
    ax.set_title("(1) Opacity Distribution")
    ax.legend()

    # ② dist_to_nearest_sparse histogram
    ax = axes[0, 1]
    ax.hist(dist_3d[dist_3d < 2.0], bins=100, color='orange', edgecolor='none')
    ax.axvline(0.3, color='red', linestyle='--', label='0.3m')
    ax.set_xlabel("dist to nearest sparse point (m)"); ax.set_ylabel("count")
    ax.set_title("(2) 3D Distance to Nearest Sparse Point")
    ax.legend()

    # ③ depth residual histogram
    ax = axes[0, 2]
    dr_valid = depth_residual[valid]
    ax.hist(dr_valid[np.abs(dr_valid) < 3.0], bins=100, color='salmon', edgecolor='none')
    ax.axvline(0, color='black', linestyle='-', linewidth=1.5)
    ax.axvline(-0.2, color='red', linestyle='--', label='floater threshold (-0.2m)')
    ax.set_xlabel("depth residual (Gaussian - Surface) m"); ax.set_ylabel("count")
    ax.set_title(f"(3) Depth Residual (n={valid.sum()})")
    ax.legend()

    # ④ opacity vs depth_residual scatter
    ax = axes[1, 0]
    s = np.random.choice(np.where(valid)[0], min(5000, valid.sum()), replace=False)
    sc = ax.scatter(opacity[s], depth_residual[s], c=opacity[s], cmap='RdYlGn_r',
                    s=2, alpha=0.5, vmin=0, vmax=0.8)
    ax.axhline(0, color='black', linewidth=1)
    ax.axhline(-0.2, color='red', linestyle='--')
    ax.set_xlabel("opacity"); ax.set_ylabel("depth residual (m)")
    ax.set_title("(4) Opacity vs Depth Residual\n(red=empty space)")
    plt.colorbar(sc, ax=ax)

    # ⑤ opacity vs dist_3d scatter
    ax = axes[1, 1]
    s2 = np.random.choice(len(opacity), min(5000, len(opacity)), replace=False)
    sc2 = ax.scatter(opacity[s2], dist_3d[s2], c=in_front_ratio[s2], cmap='RdYlGn_r',
                     s=2, alpha=0.5, vmin=0, vmax=1)
    ax.set_ylim(0, 3)
    ax.axhline(0.3, color='red', linestyle='--')
    ax.set_xlabel("opacity"); ax.set_ylabel("dist to nearest sparse (m)")
    ax.set_title("(5) Opacity vs 3D Distance\n(color=in_front_ratio)")
    plt.colorbar(sc2, ax=ax, label='in_front_ratio')

    # ⑥ in_front_ratio histogram
    ax = axes[1, 2]
    ax.hist(in_front_ratio, bins=50, color='mediumpurple', edgecolor='none')
    ax.axvline(0.5, color='red', linestyle='--', label='50%')
    ax.axvline(0.7, color='orange', linestyle='--', label='70%')
    ax.set_xlabel("in_front_ratio"); ax.set_ylabel("count")
    ax.set_title("(6) In-Front Ratio Distribution\n(high = floater candidate)")
    ax.legend()

    # ⑦ Cross-check: low-opacity vs depth_residual
    ax = axes[2, 0]
    low_op = opacity < 0.1
    high_op = opacity >= 0.1
    dr_low  = depth_residual[valid & low_op]
    dr_high = depth_residual[valid & high_op]
    ax.hist(dr_low[np.abs(dr_low) < 3], bins=60, alpha=0.6, color='red',
            label=f'opacity<0.1 (n={low_op.sum()})', density=True)
    ax.hist(dr_high[np.abs(dr_high) < 3], bins=60, alpha=0.6, color='steelblue',
            label=f'opacity≥0.1 (n={high_op.sum()})', density=True)
    ax.axvline(0, color='black', linewidth=1.5)
    ax.set_xlabel("depth residual (m)"); ax.set_ylabel("density")
    ax.set_title("(7) Depth Residual by Opacity Group\n(key: does low-opacity = empty space?)")
    ax.legend(fontsize=8)

    # ⑧ scale_max vs depth_residual (P08: Large-scale gradient masking)
    ax = axes[2, 1]
    if valid.sum() > 0:
        sc3 = ax.scatter(np.log10(scale_max[s] + 1e-6), depth_residual[s],
                         c=opacity[s], cmap='viridis', s=2, alpha=0.4, vmin=0, vmax=0.8)
        ax.axhline(-0.2, color='red', linestyle='--')
        ax.axhline(0, color='black', linewidth=1)
        ax.set_xlabel("log10(scale_max)"); ax.set_ylabel("depth residual (m)")
        ax.set_title("(8) Scale vs Depth Residual\n(P08: large-scale masking?)")
        plt.colorbar(sc3, ax=ax, label='opacity')

    # ⑨ SH rest energy vs depth_residual (P05: SH DOF compensation)
    ax = axes[2, 2]
    if valid.sum() > 0:
        sc4 = ax.scatter(sh_rest_energy[s], depth_residual[s],
                         c=opacity[s], cmap='plasma', s=2, alpha=0.4, vmin=0, vmax=0.8)
        ax.axhline(-0.2, color='red', linestyle='--')
        ax.axhline(0, color='black', linewidth=1)
        ax.set_xlabel("SH rest energy (view-dependent)")
        ax.set_ylabel("depth residual (m)")
        ax.set_title("(9) SH DOF vs Depth Residual\n(P05: color compensation?)")
        plt.colorbar(sc4, ax=ax, label='opacity')

    plt.tight_layout()
    out_path = os.path.join(out_dir, "round1_overview.png")
    plt.savefig(out_path, dpi=120, bbox_inches='tight')
    print(f"[PLOT] Saved {out_path}")
    plt.close()


def write_colored_ply(xyz, opacity, depth_residual, out_path, floater_thresh=-0.2):
    """depth_residual로 색칠된 PLY 파일 저장 (CloudCompare/MeshLab에서 열기)"""
    N = len(xyz)
    valid = ~np.isnan(depth_residual)

    # 색상: 빨강=floater(<<0), 초록=표면(≈0), 파랑=뒤쪽(>>0)
    colors = np.zeros((N, 3), dtype=np.uint8)
    colors[:, 1] = 128  # 기본 회색

    if valid.any():
        dr = depth_residual.copy()
        dr[~valid] = 0
        floater_mask = valid & (dr < floater_thresh)
        surface_mask = valid & (np.abs(dr) <= 0.5)
        behind_mask  = valid & (dr > 0.5)

        # 빨강 (floater)
        colors[floater_mask] = [255, 50, 50]
        # 초록 (surface)
        colors[surface_mask] = [50, 200, 50]
        # 파랑 (behind surface)
        colors[behind_mask] = [50, 50, 255]
        # 회색 (no measurement)
        colors[~valid] = [150, 150, 150]

    with open(out_path, 'w') as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {N}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write("property float opacity\nproperty float depth_residual\n")
        f.write("end_header\n")
        for i in range(N):
            dr_val = depth_residual[i] if valid[i] else float('nan')
            f.write(f"{xyz[i,0]:.4f} {xyz[i,1]:.4f} {xyz[i,2]:.4f} "
                    f"{colors[i,0]} {colors[i,1]} {colors[i,2]} "
                    f"{opacity[i]:.4f} {dr_val:.4f}\n")
    print(f"[PLY] Colored PLY saved: {out_path}")


# ── 7. 수치 요약 ──────────────────────────────────────────────────────────────

def print_summary(opacity, dist_3d, in_front_ratio, depth_residual, out_dir):
    valid = ~np.isnan(depth_residual)
    dr = depth_residual[valid]

    low_op = opacity < 0.1
    floater_by_dr = valid & (depth_residual < -0.2)
    floater_by_op = low_op

    # 핵심: low-opacity와 depth_residual floater는 얼마나 겹치는가?
    both     = floater_by_dr & floater_by_op
    dr_only  = floater_by_dr & ~floater_by_op
    op_only  = ~floater_by_dr & floater_by_op

    lines = [
        "=" * 60,
        "Round 1 Summary: exp08 iteration_30000",
        "=" * 60,
        f"Total Gaussians:        {len(opacity):,}",
        f"",
        f"[Opacity-based]",
        f"  low-opacity (<0.1):   {low_op.sum():,}  ({100*low_op.mean():.1f}%)",
        f"",
        f"[3D Distance to Sparse Point]",
        f"  mean:  {dist_3d.mean():.3f}m",
        f"  median:{np.median(dist_3d):.3f}m",
        f"  >0.3m: {(dist_3d>0.3).sum():,}  ({100*(dist_3d>0.3).mean():.1f}%)",
        f"  >1.0m: {(dist_3d>1.0).sum():,}  ({100*(dist_3d>1.0).mean():.1f}%)",
        f"",
        f"[In-Front Ratio]",
        f"  mean: {in_front_ratio.mean():.3f}",
        f"  >0.5 (more often in front): {(in_front_ratio>0.5).sum():,}  ({100*(in_front_ratio>0.5).mean():.1f}%)",
        f"  >0.7 (strongly in front):   {(in_front_ratio>0.7).sum():,}  ({100*(in_front_ratio>0.7).mean():.1f}%)",
        f"",
        f"[Depth Residual] (n={valid.sum()}, {100*valid.mean():.0f}% of Gaussians)",
        f"  mean:   {dr.mean():.3f}m",
        f"  median: {np.median(dr):.3f}m",
        f"  <-0.2m (in empty space):    {floater_by_dr.sum():,}  ({100*floater_by_dr.mean():.1f}%)",
        f"",
        f"[Overlap Analysis: 'opacity<0.1' vs 'depth_residual<-0.2']",
        f"  Both (true floater):         {both.sum():,}  ({100*both.sum()/max(floater_by_op.sum(),1):.1f}% of low-op)",
        f"  depth_residual<-0.2 only:   {dr_only.sum():,}  (moderate-opacity floater! missed by opacity filter)",
        f"  low-opacity only:            {op_only.sum():,}  (low-op but ON surface = not floater)",
        f"",
        f"  → If significant dr_only > 0: opacity-based pruning misses real floaters",
        f"  → If significant op_only > 0: opacity-based pruning over-prunes surface Gaussians",
        "=" * 60,
    ]

    summary = "\n".join(lines)
    print(summary)

    out_path = os.path.join(out_dir, "round1_summary.txt")
    with open(out_path, 'w') as f:
        f.write(summary)
    print(f"\n[OUT] Summary saved: {out_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    t_start = time.time()

    xyz, opacity, scale, color_rgb, sh_rest_energy, props, data, idx = load_gaussian_ply(PLY_PATH)
    cameras = load_cameras(CAMERAS_TXT, IMAGES_TXT, sample_step=CAMERA_SAMPLE_STEP)
    sparse_pts = load_sparse_points(POINTS3D_TXT)

    dist_3d, in_front_ratio, depth_residual, visible_count = compute_metrics(
        xyz, opacity, scale, cameras, sparse_pts
    )

    # 결과 저장
    npz_path = os.path.join(OUT_DIR, "round1_depth_residual.npz")
    np.savez(npz_path,
             xyz=xyz, opacity=opacity, scale=scale,
             sh_rest_energy=sh_rest_energy,
             dist_3d=dist_3d, in_front_ratio=in_front_ratio,
             depth_residual=depth_residual, visible_count=visible_count)
    print(f"[OUT] Data saved: {npz_path}")

    print_summary(opacity, dist_3d, in_front_ratio, depth_residual, OUT_DIR)
    make_plots(opacity, scale, sh_rest_energy, dist_3d, in_front_ratio, depth_residual, OUT_DIR)

    # 색칠된 PLY 저장 (CloudCompare로 열면 3D 확인 가능)
    ply_out = os.path.join(OUT_DIR, "round1_floater_colored.ply")
    write_colored_ply(xyz, opacity, depth_residual, ply_out)

    print(f"\n[DONE] Total time: {(time.time()-t_start)/60:.1f} min")
    print(f"[OUT] All results in: {OUT_DIR}")


if __name__ == "__main__":
    main()
