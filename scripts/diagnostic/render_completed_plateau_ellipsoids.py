#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")

import matplotlib.font_manager as fm
for _f in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    if os.path.exists(_f):
        fm.fontManager.addfont(_f)
matplotlib.rcParams["font.family"] = "Noto Sans CJK JP"
matplotlib.rcParams["axes.unicode_minus"] = False

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import Normalize
from matplotlib.colors import LinearSegmentedColormap
from sklearn.neighbors import NearestNeighbors

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_DIR = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data")
BATCH_DIR = DATA_DIR / "rgb_3dgs_openmavis_keyframes_301_1253"
PTS_TXT = BATCH_DIR / "sparse/0/points3D.txt"
IMG_TXT = BATCH_DIR / "sparse/0/images.txt"
CAM_TXT = BATCH_DIR / "sparse/0/cameras.txt"
MAP_PTS_JSONL = Path(
    "/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/results/runs"
    "/customdata_fisheye624_v2_30000"
    "/aria_0416_data_0416_301_1253_0416_301_1253_stereo_fisheye624_v2"
    "/orb_export/map_points.jsonl"
)
DEPTH_MAPS_DIR = DATA_DIR / "depth_maps"
_RUN_TIMESTAMP = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_DIR = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic") / f"plateau_ellipsoid_v4_{_RUN_TIMESTAMP}"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Hyperparameters ──────────────────────────────────────────────────────────────
KNN_K = 5
ALPHA_N = 0.4
ALPHA_T = 0.9
ALPHA_SPHER = 0.6
TAU_N_MAX = 0.30
TAU_T_MAX = 0.60
TAU_MIN = 0.03
KNN_ISO_MULT = 3.0
VOXEL_SIZE = 0.30  # 30cm voxel size
STRIDE = 16       # 16px scanning stride
MIN_HITS = 2       # multi-view verification hits
D_TARGET = 0.50    # Poisson-disk spacing constraint (50cm)

# ── Palette ────────────────────────────────────────────────────────────────────
C_SURFACE = "#F7F9FC"
C_GRID = "#E2E8F0"
C_INK = "#1A202C"
C_CONF_LO = "#DBEAFE"
C_CONF_HI = "#1E3A8A"
C_TRAJ = "#D97706"
C_CAM_MRK = "#92400E"
C_FILT = "#15803D"

CMAP_PLAN = LinearSegmentedColormap.from_list("planarity", ["#FFC1C1", "#1E40AF"])
CMAP_TAU_T = LinearSegmentedColormap.from_list("tau_t", ["#D1FAE5", "#065F46"])

LAYER_DESC = [
    ("바닥 아래 (하부 공간)",   "씬 하한 부근. 가상 앵커 및 일부 잡음 존재.",         "#EEF2FF"),
    ("바닥면 부근",             "바닥 슬라브. 가상 앵커 대폭 증대.",                    "#EEF2FF"),
    ("바닥 / 하부 벽",          "바닥 + 하부 벽. 고confidence 점 집중.",              "#EFF6FF"),
    ("카메라 눈높이 아래",      "가장 잘 관측되는 표면. 고obs 점 최다.",              "#EFF6FF"),
    ("카메라 눈높이 위",        "카메라 통과 높이 직상. 비슷하게 촘촘.",              "#F0FDF4"),
    ("상부 벽 / 천장",          "천장 + 상부 벽. 관측 수 급감 시작.",                "#F0FDF4"),
    ("천장 위 — sparse 부족",   "삼각화 각도 부족으로 점 급감. 가 가상 앵커로 보완.",   "#FFF7ED"),
    ("Pop 2 floater 위험 구간", "가상 앵커로 완벽 밀폐. plateau 앵커 복원.",            "#FFF1F2"),
]

# ── Rotation conversion ────────────────────────────────────────────────────────
def _qvec2rotmat(qvec):
    w, x, y, z = qvec
    return np.array([
        [1-2*y*y-2*z*z, 2*x*y-2*w*z,   2*x*z+2*w*y],
        [2*x*y+2*w*z,   1-2*x*x-2*z*z, 2*y*z-2*w*x],
        [2*x*z-2*w*y,   2*y*z+2*w*x,   1-2*x*x-2*y*y],
    ])

def check_distance_constraint(pos, G_occ, voxel_size, d_target):
    key = tuple(np.floor(pos / voxel_size).astype(int))
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            for dz in [-1, 0, 1]:
                neighbor_key = (key[0] + dx, key[1] + dy, key[2] + dz)
                if neighbor_key in G_occ:
                    other_pos = G_occ[neighbor_key]
                    dist = np.linalg.norm(pos - other_pos)
                    if dist < d_target:
                        return False
    return True

# ── Colmap Loaders ─────────────────────────────────────────────────────────────
def load_colmap_cameras(cameras_txt_path):
    cameras = {}
    with open(cameras_txt_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            cid = int(parts[0])
            model = parts[1]
            w = int(parts[2])
            h = int(parts[3])
            params = [float(p) for p in parts[4:]]
            cameras[cid] = {
                "model": model,
                "width": w,
                "height": h,
                "params": params
            }
    return cameras

def load_colmap_images(images_txt_path):
    images = {}
    with open(images_txt_path, "r") as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        parts = line.split()
        image_id = int(parts[0])
        qvec = np.array([float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])])
        tvec = np.array([float(parts[5]), float(parts[6]), float(parts[7])])
        camera_id = int(parts[8])
        image_name = parts[9]
        
        line2 = lines[i+1].strip()
        parts2 = line2.split()
        points2d = []
        point3d_ids = []
        for j in range(0, len(parts2), 3):
            u = float(parts2[j])
            v = float(parts2[j+1])
            pid = int(parts2[j+2])
            points2d.append([u, v])
            point3d_ids.append(pid)
            
        images[image_id] = {
            "qvec": qvec,
            "tvec": tvec,
            "camera_id": camera_id,
            "name": image_name,
            "points2d": np.array(points2d, dtype=np.float32).reshape(-1, 2),
            "point3d_ids": np.array(point3d_ids, dtype=np.int32)
        }
        i += 2
    return images

def load_colmap_points3d(points3d_txt_path):
    points = {}
    with open(points3d_txt_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            pid = int(parts[0])
            xyz = np.array([float(parts[1]), float(parts[2]), float(parts[3])])
            points[pid] = xyz
    return points

# ── Load and filter SLAM points (Stage 3) ──────────────────────────────────────────
def load_and_filter_slam_points():
    print("Loading and filtering SLAM points...")
    conf = {}
    if MAP_PTS_JSONL.exists():
        with open(MAP_PTS_JSONL) as f:
            for line in f:
                d = json.loads(line)
                conf[d["map_point_id"]] = d["observations"]

    pts_list, obs_list = [], []
    with open(PTS_TXT) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split()
            pid = int(p[0])
            x, y, z = float(p[1]), float(p[2]), float(p[3])
            pts_list.append([x, y, z])
            obs_list.append(conf.get(pid, 1))

    pts = np.array(pts_list, dtype=np.float32)
    obs = np.array(obs_list, dtype=np.int32)

    cams = []
    with open(IMG_TXT) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split()
            if len(p) < 9: continue
            try:
                q = np.array([float(p[i]) for i in range(1, 5)])
                t = np.array([float(p[i]) for i in range(5, 8)])
            except ValueError: continue
            cams.append(-np.transpose(_qvec2rotmat(q)) @ t)
    cams = np.array(cams, dtype=np.float32)

    lo = cams.min(0) - np.maximum((cams.max(0) - cams.min(0)) * 1.0, [2., 2., 3.])
    hi = cams.max(0) + np.maximum((cams.max(0) - cams.min(0)) * 1.0, [2., 2., 3.])
    valid = (
        (pts[:, 0] >= lo[0]) & (pts[:, 0] <= hi[0]) &
        (pts[:, 1] >= lo[1]) & (pts[:, 1] <= hi[1]) &
        (pts[:, 2] >= lo[2]) & (pts[:, 2] <= hi[2])
    )
    pts, obs = pts[valid], obs[valid]

    valid_obs = obs >= 3
    pts, obs = pts[valid_obs], obs[valid_obs]

    nbrs = NearestNeighbors(n_neighbors=KNN_K + 1, algorithm="ball_tree").fit(pts)
    dists, _ = nbrs.kneighbors(pts)
    knn_dist = dists[:, KNN_K]
    threshold = KNN_ISO_MULT * np.median(knn_dist)
    mask = knn_dist <= threshold
    pts_stage3 = pts[mask]
    obs_stage3 = obs[mask]
    
    return pts_stage3, obs_stage3, cams, lo, hi

# ── Scale-Shift Calibration ────────────────────────────────────────────────────
def fit_scale_shift_quadratic_2d(u, v, z_mono, z_slam, W, H):
    N = len(z_slam)
    if N < 15:
        if N < 2:
            return None
        X = np.array(z_mono).reshape(-1, 1)
        y = np.array(z_slam)
        reg = HuberRegressor(epsilon=1.35, max_iter=1000).fit(X, y)
        s = reg.coef_[0]
        t = reg.intercept_
        return np.array([s, 0, 0, 0, 0, 0, t, 0, 0, 0, 0, 0])
    
    u_norm = (np.array(u) - W/2) / (W/2)
    v_norm = (np.array(v) - H/2) / (H/2)
    z_m = np.array(z_mono)
    z_s = np.array(z_slam)
    
    M = np.stack([
        z_m, z_m * u_norm, z_m * v_norm, z_m * (u_norm**2), z_m * (v_norm**2), z_m * u_norm * v_norm,
        np.ones_like(z_m), u_norm, v_norm, u_norm**2, v_norm**2, u_norm * v_norm
    ], axis=1)
    
    reg = HuberRegressor(epsilon=1.35, max_iter=1000).fit(M, z_s)
    return reg.coef_

def calibrate_depth_map(depth_map, coeffs, W, H):
    if coeffs is None:
        return depth_map
    
    uu, vv = np.meshgrid(np.arange(W), np.arange(H))
    u_norm = (uu - W/2) / (W/2)
    v_norm = (vv - H/2) / (H/2)
    
    s_0, s_1, s_2, s_3, s_4, s_5, t_0, t_1, t_2, t_3, t_4, t_5 = coeffs
    
    scale_field = s_0 + s_1 * u_norm + s_2 * v_norm + s_3 * (u_norm**2) + s_4 * (v_norm**2) + s_5 * u_norm * v_norm
    shift_field = t_0 + t_1 * u_norm + t_2 * v_norm + t_3 * (u_norm**2) + t_4 * (v_norm**2) + t_5 * u_norm * v_norm
    
    calibrated_depth = scale_field * depth_map + shift_field
    return np.maximum(calibrated_depth, 0.1)

# ── Anisotropic Normal Estimation (PCA) ───────────────────────────────────────
def compute_aniso_properties(pts, k=5):
    N = len(pts)
    nbrs = NearestNeighbors(n_neighbors=k+1, algorithm="ball_tree").fit(pts)
    dists, inds = nbrs.kneighbors(pts)

    h_j = dists[:, k].astype(np.float32)
    frames = np.zeros((N, 3, 3), dtype=np.float32)
    planarity = np.zeros(N, dtype=np.float32)

    for i in range(N):
        neigh = pts[inds[i, 1:]]
        centroid = neigh.mean(0)
        X = neigh - centroid
        cov = (X.T @ X) / max(k - 1, 1)

        eigvals, eigvecs = np.linalg.eigh(cov)
        u_n  = eigvecs[:, 0]
        u_t1 = eigvecs[:, 1]
        u_t2 = eigvecs[:, 2]

        frames[i] = np.stack([u_t1, u_t2, u_n], axis=1)

        lam = eigvals.clip(0)
        denom = lam[2] if lam[2] > 1e-9 else 1e-9
        planarity[i] = float((lam[1] - lam[0]) / denom)

    tau_n = np.clip(ALPHA_N * h_j, TAU_MIN, TAU_N_MAX)
    tau_t = np.clip(ALPHA_T * h_j, TAU_MIN, TAU_T_MAX)

    return frames, h_j, planarity, tau_n, tau_t

# ── Anisotropic Coverage ───────────────────────────────────────────────────────
def aniso_coverage(anchor_pts, frames, tau_n, tau_t, xmin, xmax, ymin, ymax, z_mid, nx=100, ny=130, chunk=64):
    if len(anchor_pts) == 0:
        return np.zeros((ny, nx), dtype=bool), 0.0

    xg = np.linspace(xmin, xmax, nx)
    yg = np.linspace(ymin, ymax, ny)
    XX, YY = np.meshgrid(xg, yg)
    Zg = np.full(XX.size, z_mid, dtype=np.float32)
    grid_3d = np.stack([XX.ravel().astype(np.float32), YY.ravel().astype(np.float32), Zg], axis=1)
    N_grid = len(grid_3d)
    M = len(anchor_pts)

    covered = np.zeros(N_grid, dtype=bool)

    for start in range(0, M, chunk):
        end = min(start + chunk, M)
        b_pts = anchor_pts[start:end].copy()
        b_pts[:, 2] = z_mid
        b_fr = frames[start:end]
        b_tn = tau_n[start:end]
        b_tt = tau_t[start:end]

        delta = grid_3d[np.newaxis] - b_pts[:, np.newaxis]  # (C, N_grid, 3)
        c_coord = np.einsum('cjk,cnj->cnk', b_fr, delta)   # (C, N_grid, 3)

        d2 = ((c_coord[:,:,0] / b_tt[:,np.newaxis])**2 +
              (c_coord[:,:,1] / b_tt[:,np.newaxis])**2 +
              (c_coord[:,:,2] / b_tn[:,np.newaxis])**2)     # (C, N_grid)

        covered |= (d2 <= 1.0).any(axis=0)

    return covered.reshape(ny, nx), float(covered.mean())

def spher_coverage(anchor_pts, h_j, xmin, xmax, ymin, ymax, nx=100, ny=130):
    from sklearn.neighbors import BallTree
    if len(anchor_pts) == 0:
        return np.zeros((ny, nx), dtype=bool), 0.0

    tau_s = np.clip(ALPHA_SPHER * h_j, TAU_MIN, TAU_T_MAX)
    xg = np.linspace(xmin, xmax, nx)
    yg = np.linspace(ymin, ymax, ny)
    XX, YY = np.meshgrid(xg, yg)
    grid_2d = np.stack([XX.ravel(), YY.ravel()], axis=1)
    tree = BallTree(anchor_pts[:, :2])
    k_q = min(3, len(anchor_pts))
    dists, inds = tree.query(grid_2d, k=k_q)
    covered = np.any(dists <= tau_s[inds], axis=1)
    return covered.reshape(ny, nx), float(covered.mean())

# ── Render Cover Page ─────────────────────────────────────────────────────────
def cover_page(pdf, n_pts, tau_n, tau_t, planarity, model_label):
    fig = plt.figure(figsize=(13, 9.5), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")

    ax.text(0.5, 0.88, f"Anisotropic (Ellipsoidal) Plateau Coverage  ·  {model_label}",
            ha="center", fontsize=20, fontweight="bold", color=C_INK)
    ax.text(0.5, 0.80, f"Completed Plateau (SLAM + 가상 시딩 앵커)",
            ha="center", fontsize=14, color="#3B82F6", fontweight="bold")
    ax.text(0.5, 0.74, f"tau_n = clip({ALPHA_N} × h_j, {TAU_MIN}m, {TAU_N_MAX}m)  |  tau_t = clip({ALPHA_T} × h_j, {TAU_MIN}m, {TAU_T_MAX}m)",
            ha="center", fontsize=11, color="#555", family="monospace")

    stats = [
        f"총 앵커 포인트 수 (N): {n_pts:,} pts",
        f"로컬 스페이싱 h_j: median = {np.median(tau_t/ALPHA_T):.3f} m",
        f"Normal 반경 tau_n: median = {np.median(tau_n):.3f} m",
        f"Tangent 반경 tau_t: median = {np.median(tau_t):.3f} m",
        f"표면 평탄도 planarity (PCA): median = {np.median(planarity):.3f}"
    ]
    y_pos = 0.55
    for s in stats:
        ax.text(0.35, y_pos, s, fontsize=12, color=C_INK, ha="left")
        y_pos -= 0.05

    pdf.savefig(fig)
    plt.close(fig)

# ── Render Layer Page ──────────────────────────────────────────────────────────
def one_layer_page(pdf, pts, obs, frames, tau_n, tau_t, h_j, planarity, cams,
                   filt_lo, filt_hi, z_lo, z_hi, layer_idx,
                   xmin, xmax, ymin, ymax, obs_max, model_tag):

    label, interp, bg = LAYER_DESC[layer_idx]
    mask = (pts[:,2] >= z_lo) & (pts[:,2] < z_hi)
    slab = pts[mask]
    slab_obs = obs[mask]
    slab_fr = frames[mask]
    slab_tn = tau_n[mask]
    slab_tt = tau_t[mask]
    slab_hj = h_j[mask]
    slab_plan = planarity[mask]
    n = len(slab)

    z_mid = (z_lo + z_hi) / 2.0

    # Calculate coverage footprint
    e_grid, e_frac = aniso_coverage(slab, slab_fr, slab_tn, slab_tt, xmin, xmax, ymin, ymax, z_mid)
    s_grid, s_frac = spher_coverage(slab, slab_hj, xmin, xmax, ymin, ymax)

    fig = plt.figure(figsize=(13, 9.5), facecolor="white")

    # Header
    hax = fig.add_axes([0, 0.88, 1, 0.12])
    hax.set_facecolor(bg); hax.axis("off")
    hax.text(0.5, 0.72,
             f"[{model_tag}]  Layer {layer_idx+1}/8  —  Z ∈ [{z_lo:.2f}, {z_hi:.2f}) m",
             ha="center", fontsize=14, fontweight="bold", color=C_INK)
    hax.text(0.5, 0.28,
             f"{label}   |   {n:,} anchors   "
             f"ellipsoid coverage {e_frac*100:.1f}%  vs  sphere {s_frac*100:.1f}%  "
             f"(Δ{(e_frac-s_frac)*100:+.1f}%)",
             ha="center", fontsize=11, color="#444")
    hax.text(0.5, 0.06, interp,
             ha="center", fontsize=9.5, color="#666", style="italic")

    # Main plot axes
    ax = fig.add_axes([0.07, 0.20, 0.88, 0.67])
    ax.set_facecolor(C_SURFACE); ax.set_aspect("equal")
    ax.grid(True, color=C_GRID, linewidth=0.6, zorder=0)

    # Plot Spherical footprint (background, light red)
    s_rgba = np.zeros((*s_grid.shape, 4))
    s_rgba[s_grid, :] = [0.99, 0.60, 0.60, 0.20]
    ax.imshow(s_rgba, origin="lower", extent=[xmin, xmax, ymin, ymax],
              aspect="equal", zorder=1, interpolation="nearest")

    # Plot Ellipsoidal footprint (foreground, blue)
    e_rgba = np.zeros((*e_grid.shape, 4))
    e_rgba[e_grid, :] = [0.231, 0.510, 0.965, 0.30]
    ax.imshow(e_rgba, origin="lower", extent=[xmin, xmax, ymin, ymax],
              aspect="equal", zorder=2, interpolation="nearest")

    # Plot anchors colored by planarity
    if n > 0:
        norm_p = Normalize(vmin=0, vmax=1)
        colors = CMAP_PLAN(norm_p(slab_plan))
        order = np.argsort(slab_plan)
        ax.scatter(slab[order,0], slab[order,1],
                   c=colors[order], s=10, alpha=0.85,
                   linewidths=0, rasterized=True, zorder=4)

        # Draw local normals
        step = max(1, n // 60)
        sub = np.arange(0, n, step)
        u_n_xy = slab_fr[sub, :2, 2]
        norms = np.linalg.norm(u_n_xy, axis=1, keepdims=True).clip(1e-6)
        u_n_xy = u_n_xy / norms
        scale = slab_tt[sub] * 0.8

        ax.quiver(slab[sub,0], slab[sub,1],
                  u_n_xy[:,0]*scale, u_n_xy[:,1]*scale,
                  color="#6D28D9", alpha=0.6, scale=1, scale_units="xy",
                  width=0.004, headwidth=3, headlength=4, zorder=5)

    # Plot camera trajectories
    ax.plot(cams[:,0], cams[:,1], color=C_TRAJ, lw=2.0, alpha=0.9, zorder=6)
    ax.scatter(cams[::5,0], cams[::5,1], c=C_CAM_MRK, s=45,
               marker="^", linewidths=0, zorder=7)

    # Draw boundary box
    rect = mpatches.FancyBboxPatch(
        (filt_lo[0], filt_lo[1]),
        filt_hi[0]-filt_lo[0], filt_hi[1]-filt_lo[1],
        boxstyle="square,pad=0", linewidth=2,
        edgecolor=C_FILT, facecolor="none", zorder=8)
    ax.add_patch(rect)

    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
    ax.set_xlabel("X (m) — Depth Axis", fontsize=10, color=C_INK)
    ax.set_ylabel("Y (m) — Lateral Axis", fontsize=10, color=C_INK)

    # Legend axis
    leg = fig.add_axes([0.07, 0.05, 0.88, 0.10]); leg.axis("off")
    defs = [
        ("#2563EB", "■", "타원형 Plateau 커버리지", "접선 방향(tangent)은 여유롭게, 법선 방향(normal)은 타이트하게 밀착."),
        ("#FCA5A5", "■", "구형 Plateau (비교용)", "모든 방향 균등 반경 0.6*h_j. 천장/바닥면 통제 불가."),
        ("#6D28D9", "➔", "Local Surface Normal", "PCA 최소 고유벡터의 XY 방향 사영. 천장/바닥 앵커는 화살표 없음(수직)."),
        (C_TRAJ,   "▲", "카메라 경로 (57 keyframes)", "앵커 점들은 planarity(λ2-λ1)/λ3로 매핑 (파랑=평면, 빨강=모서리)."),
    ]
    xs = [0.01, 0.26, 0.52, 0.76]
    for idx_d, (color, mark, name, desc) in enumerate(defs):
        leg.text(xs[idx_d], 0.88, f"{mark}  {name}", fontsize=8.5, fontweight="bold", color=color, transform=leg.transAxes, va="top")
        leg.text(xs[idx_d], 0.62, desc, fontsize=7.2, color="#444", transform=leg.transAxes, va="top")

    pdf.savefig(fig, dpi=150, bbox_inches="tight")
    plt.close(fig)

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("Loading COLMAP inputs...")
    cameras = load_colmap_cameras(CAM_TXT)
    images = load_colmap_images(IMG_TXT)
    points3d = load_colmap_points3d(PTS_TXT)
    
    pts_slam, obs_slam, cams, filt_lo, filt_hi = load_and_filter_slam_points()
    z_edges = np.linspace(float(filt_lo[2]), float(filt_hi[2]), 9)
    
    pad = 1.0
    xmin = min(float(pts_slam[:,0].min()), float(filt_lo[0])) - pad
    xmax = max(float(pts_slam[:,0].max()), float(filt_hi[0])) + pad
    ymin = min(float(pts_slam[:,1].min()), float(filt_lo[1])) - pad
    ymax = max(float(pts_slam[:,1].max()), float(filt_hi[1])) + pad
    obs_max = max(int(np.percentile(obs_slam, 98)), 10)
    
    models = {
        "depth_anything_v2": ("Depth-Anything-V2", "plateau_ellipsoid_completed_depth_anything_v2.pdf"),
        "depth_pro": ("Depth Pro (Apple)", "plateau_ellipsoid_completed_depth_pro.pdf"),
        "metric3d": ("Metric3D (ViT-S)", "plateau_ellipsoid_completed_metric3d.pdf")
    }
    
    for model_name, (model_label, out_pdf_name) in models.items():
        print(f"\n================= Processing completed plateau for {model_label} =================")
        depth_dir = DEPTH_MAPS_DIR / model_name
        
        # 1. Calibrate depth maps
        calibrated_depthmaps = {}
        for image_id, img_data in images.items():
            img_stem = os.path.splitext(img_data["name"])[0]
            npy_path = depth_dir / f"{img_stem}.npy"
            if not npy_path.exists(): continue
                
            depth_mono = np.load(npy_path)
            cam_info = cameras[img_data["camera_id"]]
            W, H = cam_info["width"], cam_info["height"]
            
            R = _qvec2rotmat(img_data["qvec"])
            t = img_data["tvec"]
            
            visible_pts_slam_z = []
            visible_pts_mono_z = []
            visible_pts_u = []
            visible_pts_v = []
            
            for u, v, pid in zip(img_data["points2d"][:, 0], img_data["points2d"][:, 1], img_data["point3d_ids"]):
                if pid == -1 or pid not in points3d: continue
                xyz_world = points3d[pid]
                xyz_cam = R @ xyz_world + t
                z_slam = xyz_cam[2]
                
                u_idx, v_idx = int(np.round(u)), int(np.round(v))
                if 0 <= u_idx < W and 0 <= v_idx < H:
                    z_mono = depth_mono[v_idx, u_idx]
                    if z_mono > 0:
                        visible_pts_slam_z.append(z_slam)
                        visible_pts_mono_z.append(z_mono)
                        visible_pts_u.append(u)
                        visible_pts_v.append(v)
            
            coeffs = fit_scale_shift_quadratic_2d(
                visible_pts_u, visible_pts_v, visible_pts_mono_z, visible_pts_slam_z, W, H
            )
            calibrated_depthmaps[image_id] = calibrate_depth_map(depth_mono, coeffs, W, H)
            
        # 2. Voxel Seeding
        G_occ = {}
        for pt in pts_slam:
            key = tuple(np.floor(pt / VOXEL_SIZE).astype(int))
            if key not in G_occ: G_occ[key] = pt
                
        G_cand = {}
        virtual_points = []
        
        for image_id, img_data in images.items():
            if image_id not in calibrated_depthmaps: continue
            depth_calib = calibrated_depthmaps[image_id]
            cam_info = cameras[img_data["camera_id"]]
            W, H = cam_info["width"], cam_info["height"]
            fx, fy, cx, cy = cam_info["params"][0:4]
            R = _qvec2rotmat(img_data["qvec"])
            t = img_data["tvec"]
            
            for v in range(0, H, STRIDE):
                for u in range(0, W, STRIDE):
                    z = depth_calib[v, u]
                    if z <= 0.1 or z > 15.0: continue
                    x_cam = np.array([(u - cx) / fx * z, (v - cy) / fy * z, z])
                    x_world = np.transpose(R) @ (x_cam - t)
                    
                    if not (filt_lo[0] <= x_world[0] <= filt_hi[0] and
                            filt_lo[1] <= x_world[1] <= filt_hi[1] and
                            filt_lo[2] <= x_world[2] <= filt_hi[2]):
                        continue
                        
                    key = tuple(np.floor(x_world / VOXEL_SIZE).astype(int))
                    if key in G_occ: continue
                        
                    if key not in G_cand:
                        G_cand[key] = {"sum_coords": x_world, "hits": 1, "frames": {image_id}}
                    else:
                        if image_id not in G_cand[key]["frames"]:
                            G_cand[key]["sum_coords"] += x_world
                            G_cand[key]["hits"] += 1
                            G_cand[key]["frames"].add(image_id)
                            
                    if G_cand[key]["hits"] >= MIN_HITS:
                        mean_pos = G_cand[key]["sum_coords"] / G_cand[key]["hits"]
                        if check_distance_constraint(mean_pos, G_occ, VOXEL_SIZE, D_TARGET):
                            G_occ[key] = mean_pos
                            virtual_points.append(mean_pos)
                        del G_cand[key]
                        
        if len(virtual_points) > 0:
            pts_virtual = np.array(virtual_points, dtype=np.float32)
            pts_all = np.vstack([pts_slam, pts_virtual])
        else:
            pts_virtual = np.zeros((0, 3), dtype=np.float32)
            pts_all = pts_slam.copy()
            
        n_all = len(pts_all)
        
        # Fake observations array (assign 1 to virtual points, original obs to SLAM points)
        obs_all = np.ones(n_all, dtype=np.int32)
        obs_all[0:len(pts_slam)] = obs_slam
        
        # 3. Compute anisotropic properties for all points
        print("Computing anisotropic (ellipsoidal) properties...")
        frames, h_j, planarity, tau_n, tau_t = compute_aniso_properties(pts_all, k=KNN_K)
        
        # 4. Render PDF
        pdf_path = OUT_DIR / out_pdf_name
        print(f"Rendering completed plateau ellipsoid PDF -> {pdf_path.name}")
        with PdfPages(pdf_path) as pdf:
            cover_page(pdf, n_all, tau_n, tau_t, planarity, model_label)
            for i in range(8):
                z_lo, z_hi = z_edges[i], z_edges[i+1]
                one_layer_page(pdf, pts_all, obs_all, frames, tau_n, tau_t, h_j, planarity, cams,
                               filt_lo, filt_hi, z_lo, z_hi, i,
                               xmin, xmax, ymin, ymax, obs_max, model_label)
                
        print(f"Finished {model_label} PDF generation.")
        
        # 5. Save anchor files
        safe_name = model_name.replace("-", "_").replace(" ", "_").lower()
        np.save(OUT_DIR / f"anchors_slam_{safe_name}.npy", pts_slam)
        np.save(OUT_DIR / f"anchors_virtual_{safe_name}.npy", pts_virtual)
        np.save(OUT_DIR / f"anchors_all_{safe_name}.npy", pts_all)
        
        # Save PLY (ASCII) for CloudCompare / MeshLab
        def _write_ply(path, pts, rgb=None):
            with open(path, "w") as f:
                f.write("ply\nformat ascii 1.0\n")
                f.write(f"element vertex {len(pts)}\n")
                f.write("property float x\nproperty float y\nproperty float z\n")
                if rgb is not None:
                    f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
                f.write("end_header\n")
                for i, p in enumerate(pts):
                    line = f"{p[0]:.6f} {p[1]:.6f} {p[2]:.6f}"
                    if rgb is not None:
                        r, g, b = rgb[i]
                        line += f" {r} {g} {b}"
                    f.write(line + "\n")
        
        # Color: SLAM=blue(30,100,220), virtual=orange(240,120,30)
        slam_rgb  = np.tile([30,  100, 220], (len(pts_slam),    1))
        virt_rgb  = np.tile([240, 120,  30], (len(pts_virtual), 1))
        all_rgb   = np.vstack([slam_rgb, virt_rgb]) if len(pts_virtual) > 0 else slam_rgb
        
        _write_ply(OUT_DIR / f"anchors_slam_{safe_name}.ply",    pts_slam,    slam_rgb)
        _write_ply(OUT_DIR / f"anchors_virtual_{safe_name}.ply", pts_virtual, virt_rgb)
        _write_ply(OUT_DIR / f"anchors_all_{safe_name}.ply",     pts_all,     all_rgb)
        
        # Save metadata json
        import json as _json
        meta = {
            "model": model_name,
            "d_target_m": D_TARGET,
            "voxel_size_m": VOXEL_SIZE,
            "min_hits": MIN_HITS,
            "n_slam": int(len(pts_slam)),
            "n_virtual": int(len(pts_virtual)),
            "n_total": int(len(pts_all)),
        }
        with open(OUT_DIR / f"anchors_meta_{safe_name}.json", "w") as f:
            _json.dump(meta, f, indent=2)
        
        print(f"  Saved anchors -> {OUT_DIR.name}/ "
              f"[SLAM={len(pts_slam)}, Virtual={len(pts_virtual)}, Total={len(pts_all)}]")
        
    print("\nAll completed plateau ellipsoidal PDF visualizations rendered successfully!")

if __name__ == '__main__':
    main()
