#!/usr/bin/env python3
"""
plateau_ellipsoid_v2.py

Anisotropic (ellipsoidal) plateau:
  - kNN-5 PCA로 각 앵커의 local surface normal 추정
  - normal 방향: alpha_n=0.4 × h_j (표면에 수직 → 타이트)
  - tangent 방향: alpha_t=0.9 × h_j (표면에 평행 → 여유)

v1 (구형) 대비:
  - 벽면 앵커: tangent가 벽 방향 → XY coverage가 좁고 깊이 방향으로 tight
  - 바닥/천장 앵커: normal이 vertical → XY coverage가 넓고 Z 방향 tight

입력: Stage 3 filtered ORB-SLAM map points (obs≥3 + kNN isolation)
출력: results/diagnostic/plateau_ellipsoid_v2_<ts>/
  ellipsoid_zlayer_stage3.pdf   — Z-layer scatter (Stage 3, 필터 결과 참조용)
  ellipsoid_plateau.pdf         — 타원체 plateau coverage (vs 구형 비교)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.font_manager as fm
for _f in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    fm.fontManager.addfont(_f)
matplotlib.rcParams["font.family"] = "Noto Sans CJK JP"
matplotlib.rcParams["axes.unicode_minus"] = False

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
from sklearn.neighbors import NearestNeighbors

# ── paths ──────────────────────────────────────────────────────────────────────
DATA_DIR  = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data")
BATCH_DIR = DATA_DIR / "rgb_3dgs_openmavis_batch_301_1253"
PTS_TXT   = BATCH_DIR / "sparse/0/points3D.txt"
IMG_TXT   = BATCH_DIR / "sparse/0/images.txt"
MAP_PTS_JSONL = Path(
    "/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/results/runs"
    "/customdata_fisheye624_v2_30000"
    "/aria_0416_data_0416_301_1253_0416_301_1253_stereo_fisheye624_v2"
    "/orb_export/map_points.jsonl"
)
OUT_ROOT = Path(
    "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic"
)

# ── ellipsoid tau parameters ────────────────────────────────────────────────────
KNN_K        = 5     # k-NN for h_j AND normal estimation
ALPHA_N      = 0.4   # normal 방향 반경 (표면 수직, tight)
ALPHA_T      = 0.9   # tangent 방향 반경 (표면 평행, loose)
ALPHA_SPHER  = 0.6   # 구형 비교용

TAU_N_MAX    = 0.30  # m  (normal 방향 최대: ALPHA_N/ALPHA_SPHER × 0.60 ≈ 0.40)
TAU_T_MAX    = 0.60  # m  (tangent 방향 최대)
TAU_MIN      = 0.03  # m  (최소)

KNN_ISO_MULT = 3.0   # Stage 3 kNN isolation multiplier

# ── palette ────────────────────────────────────────────────────────────────────
C_SURFACE = "#F7F9FC"
C_GRID    = "#E2E8F0"
C_INK     = "#1A202C"
C_CONF_LO = "#DBEAFE"
C_CONF_HI = "#1E3A8A"
C_TRAJ    = "#D97706"
C_CAM_MRK = "#92400E"
C_FILT    = "#15803D"

# planarity colormap: red (low planarity / edge) → blue (high planarity / flat surface)
CMAP_PLAN = LinearSegmentedColormap.from_list("planarity", ["#FCA5A5", "#1E40AF"])
# tau_t colormap: light → dark green
CMAP_TAU_T = LinearSegmentedColormap.from_list("tau_t", ["#D1FAE5", "#065F46"])

LAYER_DESC = [
    ("바닥 아래 (하부 공간)",   "씬 하한 부근. ORB-SLAM point 거의 없음.",           "#EEF2FF"),
    ("바닥면 부근",             "바닥 슬라브. low-obs 점 다수.",                      "#EEF2FF"),
    ("바닥 / 하부 벽",          "바닥 + 하부 벽. 고confidence 점 집중.",              "#EFF6FF"),
    ("카메라 눈높이 아래",      "가장 잘 관측되는 표면. 고obs 점 최다.",              "#EFF6FF"),
    ("카메라 눈높이 위",        "카메라 통과 높이 직상. 비슷하게 촘촘.",              "#F0FDF4"),
    ("상부 벽 / 천장",          "천장 + 상부 벽. 관측 수 급감 시작.",                "#F0FDF4"),
    ("천장 위 — sparse 부족",   "삼각화 각도 부족으로 점 급감. Pop 2 시작 구간.",     "#FFF7ED"),
    ("Pop 2 floater 위험 구간", "고confidence 점 사실상 0개. plateau 앵커 부재.",      "#FFF1F2"),
]


# ══════════════════════════════════════════════════════════════════════════════
# Data loading & filtering (Stage 3: Z-bound + obs≥3 + kNN isolation)
# ══════════════════════════════════════════════════════════════════════════════

def _qvec2rotmat(qvec):
    w, x, y, z = qvec
    return np.array([
        [1-2*y*y-2*z*z, 2*x*y-2*w*z,   2*x*z+2*w*y],
        [2*x*y+2*w*z,   1-2*x*x-2*z*z, 2*y*z-2*w*x],
        [2*x*z-2*w*y,   2*y*z+2*w*x,   1-2*x*x-2*y*y],
    ])


def load_stage3():
    """Load points and apply Stage 3 filter (Z-bound + obs≥3 + kNN isolation)."""
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

    cams = []
    with open(IMG_TXT) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split()
            if len(p) < 9:
                continue
            try:
                q = np.array([float(p[i]) for i in range(1, 5)])
                t = np.array([float(p[i]) for i in range(5, 8)])
            except ValueError:
                continue
            cams.append(-np.transpose(_qvec2rotmat(q)) @ t)

    pts = np.array(pts_list, dtype=np.float32)
    obs = np.array(obs_list,  dtype=np.int32)
    cams = np.array(cams,     dtype=np.float32)

    # camera bounds
    lo = cams.min(0) - np.maximum((cams.max(0)-cams.min(0))*1.0, [2., 2., 3.])
    hi = cams.max(0) + np.maximum((cams.max(0)-cams.min(0))*1.0, [2., 2., 3.])

    # Z-bound
    valid = (
        (pts[:,0] >= lo[0]) & (pts[:,0] <= hi[0]) &
        (pts[:,1] >= lo[1]) & (pts[:,1] <= hi[1]) &
        (pts[:,2] >= lo[2]) & (pts[:,2] <= hi[2])
    )
    pts, obs = pts[valid], obs[valid]
    print(f"  after Z-bound: {len(pts):,}")

    # obs≥3
    mask = obs >= 3
    pts, obs = pts[mask], obs[mask]
    print(f"  after obs≥3:   {len(pts):,}")

    # kNN isolation
    nbrs = NearestNeighbors(n_neighbors=KNN_K+1, algorithm="ball_tree").fit(pts)
    dists, _ = nbrs.kneighbors(pts)
    knn_dist = dists[:, KNN_K]
    thresh = KNN_ISO_MULT * np.median(knn_dist)
    mask = knn_dist <= thresh
    pts, obs = pts[mask], obs[mask]
    print(f"  after kNN iso: {len(pts):,}  (removed {(~mask).sum()})")

    return pts, obs, cams, lo, hi


# ══════════════════════════════════════════════════════════════════════════════
# Ellipsoid computation: PCA normal + anisotropic tau
# ══════════════════════════════════════════════════════════════════════════════

def compute_ellipsoid(pts, k=KNN_K):
    """
    Returns:
      frames   : (N,3,3)  columns = [u_t1, u_t2, u_n]  (local ONB)
      h_j      : (N,)     local spacing (k-NN distance)
      planarity: (N,)     (λ2-λ1)/λ3  ∈ [0,1], 1=flat plane, 0=isotropic
      tau_n    : (N,)     clip(ALPHA_N*h_j, TAU_MIN, TAU_N_MAX)
      tau_t    : (N,)     clip(ALPHA_T*h_j, TAU_MIN, TAU_T_MAX)
    """
    N = len(pts)
    nbrs = NearestNeighbors(n_neighbors=k+1, algorithm="ball_tree").fit(pts)
    dists, inds = nbrs.kneighbors(pts)

    h_j      = dists[:, k].astype(np.float32)
    frames   = np.zeros((N, 3, 3), dtype=np.float32)
    planarity = np.zeros(N, dtype=np.float32)

    for i in range(N):
        neigh = pts[inds[i, 1:]]          # (k, 3)  exclude self
        centroid = neigh.mean(0)
        X = neigh - centroid               # (k, 3)
        cov = (X.T @ X) / max(k - 1, 1)   # (3,3)

        eigvals, eigvecs = np.linalg.eigh(cov)  # ascending order
        # eigvecs[:,0] = direction with LEAST variance = surface normal
        u_n  = eigvecs[:, 0]
        u_t1 = eigvecs[:, 1]
        u_t2 = eigvecs[:, 2]

        frames[i] = np.stack([u_t1, u_t2, u_n], axis=1)  # columns

        lam = eigvals.clip(0)
        denom = lam[2] if lam[2] > 1e-9 else 1e-9
        planarity[i] = float((lam[1] - lam[0]) / denom)   # ~1 → planar

    tau_n = np.clip(ALPHA_N * h_j, TAU_MIN, TAU_N_MAX)
    tau_t = np.clip(ALPHA_T * h_j, TAU_MIN, TAU_T_MAX)

    return frames, h_j, planarity, tau_n, tau_t


# ══════════════════════════════════════════════════════════════════════════════
# Coverage heatmap: anisotropic (ellipsoidal) distance
# ══════════════════════════════════════════════════════════════════════════════

def aniso_coverage(anchor_pts, frames, tau_n, tau_t,
                   xmin, xmax, ymin, ymax, z_mid,
                   nx=100, ny=130, chunk=64):
    """
    For XY grid at Z=z_mid, compute which cells are inside ANY anchor's ellipsoid.
    Returns (covered_grid [ny,nx], coverage_fraction)
    """
    if len(anchor_pts) == 0:
        return np.zeros((ny, nx), dtype=bool), 0.0

    xg = np.linspace(xmin, xmax, nx)
    yg = np.linspace(ymin, ymax, ny)
    XX, YY = np.meshgrid(xg, yg)
    Zg  = np.full(XX.size, z_mid, dtype=np.float32)
    grid_3d = np.stack([XX.ravel().astype(np.float32),
                        YY.ravel().astype(np.float32),
                        Zg], axis=1)  # (N_grid, 3)
    N_grid = len(grid_3d)
    M      = len(anchor_pts)

    covered = np.zeros(N_grid, dtype=bool)

    for start in range(0, M, chunk):
        end   = min(start + chunk, M)
        b_pts = anchor_pts[start:end].copy() # (C, 3)
        b_pts[:, 2] = z_mid                  # 앵커 Z를 z_mid로 고정 → Δz=0 (2D XY footprint)
        b_fr  = frames[start:end]            # (C, 3, 3)
        b_tn  = tau_n[start:end]             # (C,)
        b_tt  = tau_t[start:end]             # (C,)

        # delta[c, n, :] = grid_3d[n] - anchor[c]  (Δz≡0 → XY footprint 투영)
        delta = grid_3d[np.newaxis] - b_pts[:, np.newaxis]  # (C, N_grid, 3)

        # project onto local frame: c_coord[c,n,k] = u_k · delta[c,n]
        # frames[:,: ,0]=u_t1  [:,: ,1]=u_t2  [:,: ,2]=u_n
        c_coord = np.einsum('cjk,cnj->cnk', b_fr, delta)   # (C, N_grid, 3)

        # anisotropic distance²
        d2 = ((c_coord[:,:,0] / b_tt[:,np.newaxis])**2 +
              (c_coord[:,:,1] / b_tt[:,np.newaxis])**2 +
              (c_coord[:,:,2] / b_tn[:,np.newaxis])**2)     # (C, N_grid)

        covered |= (d2 <= 1.0).any(axis=0)

    return covered.reshape(ny, nx), float(covered.mean())


def spher_coverage(anchor_pts, h_j, xmin, xmax, ymin, ymax,
                   nx=100, ny=130):
    """Spherical tau reference coverage (alpha=0.6)."""
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


# ══════════════════════════════════════════════════════════════════════════════
# Visualization
# ══════════════════════════════════════════════════════════════════════════════

def conf_cmap():
    return LinearSegmentedColormap.from_list("orb_conf", [C_CONF_LO, C_CONF_HI])


def cover_page(pdf, n_pts, tau_n, tau_t, planarity):
    fig = plt.figure(figsize=(13, 9.5), facecolor="white")
    ax  = fig.add_axes([0, 0, 1, 1]); ax.axis("off")

    ax.text(0.5, 0.89, "Plateau Ellipsoid v2  —  Anisotropic Tau",
            ha="center", fontsize=22, fontweight="bold", color=C_INK)
    ax.text(0.5, 0.82,
            f"normal 방향: α_n={ALPHA_N}  |  tangent 방향: α_t={ALPHA_T}  "
            f"|  kNN k={KNN_K}  |  Stage 3 filtered",
            ha="center", fontsize=13, color="#555")

    rows = [
        ("앵커 점 수 (Stage 3)",     f"{n_pts:,}"),
        ("tau_n  (normal 방향)",     f"median={np.median(tau_n):.3f}m  "
                                     f"max={tau_n.max():.3f}m"),
        ("tau_t  (tangent 방향)",    f"median={np.median(tau_t):.3f}m  "
                                     f"max={tau_t.max():.3f}m"),
        ("tau_n / tau_t 비율",       f"median={np.median(tau_n/tau_t):.2f}  "
                                     f"(설계값={ALPHA_N/ALPHA_T:.2f})"),
        ("planarity 중앙값",         f"{np.median(planarity):.3f}  "
                                     f"(1=평면, 0=등방)"),
        ("고planarity (≥0.7) pts",   f"{(planarity>=0.7).sum():,}  "
                                     f"({100*(planarity>=0.7).mean():.1f}%)"),
        ("저planarity (≤0.3) pts",   f"{(planarity<=0.3).sum():,}  "
                                     f"({100*(planarity<=0.3).mean():.1f}%)"),
    ]
    y0 = 0.70
    for lbl, val in rows:
        ax.text(0.35, y0, lbl, ha="right", fontsize=11, color="#666")
        ax.text(0.37, y0, val, ha="left",  fontsize=11, color=C_INK, fontweight="bold")
        y0 -= 0.058

    ax.text(0.5, 0.19,
            "타원체 plateau 원리\n"
            "d_aniso² = (Δ·u_t1/τ_t)² + (Δ·u_t2/τ_t)² + (Δ·u_n/τ_n)²\n"
            "Δ = x - p_j,  in_plateau if d_aniso ≤ 1\n\n"
            "u_n  : kNN PCA 최소 고유벡터 (표면 법선)\n"
            "u_t1, u_t2 : 표면 접선 방향\n"
            "τ_n < τ_t  →  표면 수직=tight  /  접선=loose\n"
            "heatmap: 앵커 Z를 z_mid로 고정 (XY footprint 2D 투영 비교)",
            ha="center", fontsize=10, color="#1E3A8A",
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#EFF6FF",
                      edgecolor="#93C5FD", alpha=0.9))

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)


def one_layer_page(pdf, pts, obs, frames, tau_n, tau_t, h_j, planarity, cams,
                   filt_lo, filt_hi, z_lo, z_hi, layer_idx,
                   xmin, xmax, ymin, ymax, obs_max):

    label, interp, bg = LAYER_DESC[layer_idx]
    mask      = (pts[:,2] >= z_lo) & (pts[:,2] < z_hi)
    slab      = pts[mask]
    slab_obs  = obs[mask]
    slab_fr   = frames[mask]
    slab_tn   = tau_n[mask]
    slab_tt   = tau_t[mask]
    slab_hj   = h_j[mask]
    slab_plan = planarity[mask]
    n         = len(slab)

    n_hi = int((slab_obs >= 10).sum())
    n_lo = int((slab_obs <= 2).sum())

    z_mid = (z_lo + z_hi) / 2.0

    # coverage: ellipsoidal vs spherical
    e_grid, e_frac = aniso_coverage(slab, slab_fr, slab_tn, slab_tt,
                                     xmin, xmax, ymin, ymax, z_mid)
    s_grid, s_frac = spher_coverage(slab, slab_hj, xmin, xmax, ymin, ymax)

    # ── figure ────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(13, 9.5), facecolor="white")

    hax = fig.add_axes([0, 0.88, 1, 0.12])
    hax.set_facecolor(bg); hax.axis("off")
    hax.text(0.5, 0.72,
             f"[Ellipsoid v2]  Layer {layer_idx+1}/8  —  Z ∈ [{z_lo:.2f}, {z_hi:.2f}) m",
             ha="center", fontsize=14, fontweight="bold", color=C_INK)
    hax.text(0.5, 0.28,
             f"{label}   |   {n:,} anchors   "
             f"ellipsoid coverage {e_frac*100:.1f}%  vs  sphere {s_frac*100:.1f}%  "
             f"(Δ{(e_frac-s_frac)*100:+.1f}%)",
             ha="center", fontsize=11, color="#444")
    hax.text(0.5, 0.06, interp,
             ha="center", fontsize=9.5, color="#666", style="italic")

    # ── main axes ─────────────────────────────────────────────────────────────
    ax = fig.add_axes([0.07, 0.20, 0.88, 0.67])
    ax.set_facecolor(C_SURFACE); ax.set_aspect("equal")
    ax.grid(True, color=C_GRID, linewidth=0.6, zorder=0)

    # Spherical coverage (background, light red)
    xg = np.linspace(xmin, xmax, s_grid.shape[1])
    yg = np.linspace(ymin, ymax, s_grid.shape[0])

    s_rgba = np.zeros((*s_grid.shape, 4))
    s_rgba[s_grid, :] = [0.99, 0.60, 0.60, 0.20]   # muted red for sphere-only
    ax.imshow(s_rgba, origin="lower", extent=[xmin, xmax, ymin, ymax],
              aspect="equal", zorder=1, interpolation="nearest")

    # Ellipsoidal coverage (foreground, blue)
    e_rgba = np.zeros((*e_grid.shape, 4))
    e_rgba[e_grid, :] = [0.231, 0.510, 0.965, 0.30]  # blue
    ax.imshow(e_rgba, origin="lower", extent=[xmin, xmax, ymin, ymax],
              aspect="equal", zorder=2, interpolation="nearest")

    # Anchor scatter: colored by planarity
    if n > 0:
        norm_p = Normalize(vmin=0, vmax=1)
        colors = CMAP_PLAN(norm_p(slab_plan))
        order  = np.argsort(slab_plan)
        ax.scatter(slab[order,0], slab[order,1],
                   c=colors[order], s=10, alpha=0.85,
                   linewidths=0, rasterized=True, zorder=4)

        # Normal direction arrows (XY projection of u_n) — every 15th anchor
        step = max(1, n // 60)
        sub  = np.arange(0, n, step)
        u_n_xy = slab_fr[sub, :2, 2]    # frames[:,: ,2] = u_n; take XY
        norms  = np.linalg.norm(u_n_xy, axis=1, keepdims=True).clip(1e-6)
        u_n_xy = u_n_xy / norms
        scale  = slab_tt[sub] * 0.8     # arrow length ≈ tau_t × 0.8

        ax.quiver(slab[sub,0], slab[sub,1],
                  u_n_xy[:,0]*scale, u_n_xy[:,1]*scale,
                  color="#6D28D9", alpha=0.6, scale=1, scale_units="xy",
                  width=0.004, headwidth=3, headlength=4, zorder=5)

    # Camera trajectory
    ax.plot(cams[:,0], cams[:,1], color=C_TRAJ, lw=2.0, alpha=0.9, zorder=6)
    ax.scatter(cams[::5,0], cams[::5,1], c=C_CAM_MRK, s=45,
               marker="^", linewidths=0, zorder=7)

    # Filter boundary
    rect = mpatches.FancyBboxPatch(
        (filt_lo[0], filt_lo[1]),
        filt_hi[0]-filt_lo[0], filt_hi[1]-filt_lo[1],
        boxstyle="square,pad=0", linewidth=2,
        edgecolor=C_FILT, facecolor="none", zorder=8)
    ax.add_patch(rect)

    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
    ax.set_xlabel("X (m) — 카메라 이동 방향 (depth axis)", fontsize=10, color=C_INK)
    ax.set_ylabel("Y (m) — 좌우 방향",                     fontsize=10, color=C_INK)
    ax.tick_params(colors="#666", labelsize=8)
    for sp in ax.spines.values(): sp.set_edgecolor(C_GRID)

    # Coverage callout
    ax.text(0.02, 0.97,
            f"타원체: {e_frac*100:.1f}%\n"
            f"구형:   {s_frac*100:.1f}%\n"
            f"Δ: {(e_frac-s_frac)*100:+.1f}%\n"
            f"n={n:,}",
            transform=ax.transAxes, fontsize=9, color="#1E40AF", va="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#EFF6FF",
                      edgecolor="#93C5FD", alpha=0.95))

    # Planarity callout
    if n > 0:
        ax.text(0.02, 0.73,
                f"planarity\nmed={np.median(slab_plan):.2f}\n"
                f"τ_n med={np.median(slab_tn):.3f}m\n"
                f"τ_t med={np.median(slab_tt):.3f}m",
                transform=ax.transAxes, fontsize=8.5, color="#6D28D9", va="top",
                bbox=dict(boxstyle="round,pad=0.35", facecolor="#F5F3FF",
                          edgecolor="#C4B5FD", alpha=0.95))

    # Camera annotation
    mid = len(cams)//2
    ax.annotate("카메라 경로 (57 keyframes)",
        xy=(cams[mid,0], cams[mid,1]),
        xytext=(cams[mid,0]+3.0, cams[mid,1]-2.5), fontsize=7.5, color=C_TRAJ,
        arrowprops=dict(arrowstyle="->", color=C_TRAJ, lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFFBEB",
                  edgecolor="#FDE68A", alpha=0.9))

    # Planarity colorbar
    sm_p = ScalarMappable(cmap=CMAP_PLAN, norm=Normalize(0, 1)); sm_p.set_array([])
    cbar_ax = fig.add_axes([0.965, 0.20, 0.012, 0.67])
    cb = fig.colorbar(sm_p, cax=cbar_ax)
    cb.set_label("planarity (1=평면)", fontsize=8, color=C_INK)
    cb.ax.yaxis.set_ticks([0, 0.5, 1.0])
    cb.ax.tick_params(labelsize=7, colors="#666")

    # Legend
    leg = fig.add_axes([0.07, 0.00, 0.88, 0.18])
    leg.set_facecolor("#F8FAFC"); leg.axis("off")
    defs = [
        ("#3B82F6", "■", "Ellipsoid plateau coverage (파란 배경)",
         f"타원체: τ_n={ALPHA_N}×h, τ_t={ALPHA_T}×h. Z=layer 중심에서의 XY 단면 커버리지."),
        ("#F87171", "■", "구형 plateau만 커버 (연한 빨강)",
         f"구형(α={ALPHA_SPHER}×h)에서는 커버되나 타원체에서 추가된 영역."),
        ("#7C3AED", "→", "법선 방향 (XY 투영 화살표)",
         "kNN PCA 최소 고유벡터 u_n의 XY 성분. 수직 표면=화살표 없음(u_n≈Z)."),
        (C_TRAJ,   "▶", "카메라 경로 (57 keyframes)  |  점 색상=planarity",
         "planarity: (λ2-λ1)/λ3.  파랑=평평한 표면, 빨강=모서리/고립점."),
    ]
    xs = [0.01, 0.26, 0.52, 0.76]
    for i, (color, mark, name, desc) in enumerate(defs):
        leg.text(xs[i], 0.88, f"{mark}  {name}",
                 fontsize=8.5, fontweight="bold", color=color,
                 transform=leg.transAxes, va="top")
        leg.text(xs[i], 0.62, desc,
                 fontsize=7.2, color="#444",
                 transform=leg.transAxes, va="top")

    pdf.savefig(fig, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  layer {layer_idx+1}: n={n:,}  "
          f"ellipsoid={e_frac*100:.1f}%  sphere={s_frac*100:.1f}%  "
          f"Δ={( e_frac-s_frac)*100:+.1f}%")


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = OUT_ROOT / f"plateau_ellipsoid_v2_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[output] {out_dir}\n")

    print("[load] Stage 3 filtered points …")
    pts, obs, cams, filt_lo, filt_hi = load_stage3()
    print(f"  final: {len(pts):,} pts\n")

    print("[compute] PCA normals + anisotropic tau …")
    frames, h_j, planarity, tau_n, tau_t = compute_ellipsoid(pts)
    print(f"  tau_n  med={np.median(tau_n):.3f}m  max={tau_n.max():.3f}m")
    print(f"  tau_t  med={np.median(tau_t):.3f}m  max={tau_t.max():.3f}m")
    print(f"  planarity  med={np.median(planarity):.3f}  "
          f"(high≥0.7: {(planarity>=0.7).sum():,} pts)\n")

    z_edges = np.linspace(float(filt_lo[2]), float(filt_hi[2]), 9)
    pad  = 1.0
    xmin = min(float(pts[:,0].min()), float(filt_lo[0])) - pad
    xmax = max(float(pts[:,0].max()), float(filt_hi[0])) + pad
    ymin = min(float(pts[:,1].min()), float(filt_lo[1])) - pad
    ymax = max(float(pts[:,1].max()), float(filt_hi[1])) + pad

    obs_max = max(int(np.percentile(obs, 98)), 10)

    pdf_path = out_dir / "ellipsoid_plateau.pdf"
    print(f"[render] ellipsoid plateau PDF → {pdf_path.name}")
    with PdfPages(pdf_path) as pdf:
        cover_page(pdf, len(pts), tau_n, tau_t, planarity)
        for i in range(8):
            one_layer_page(pdf, pts, obs, frames, tau_n, tau_t, h_j, planarity, cams,
                           filt_lo, filt_hi,
                           z_edges[i], z_edges[i+1],
                           i, xmin, xmax, ymin, ymax, obs_max)

    print(f"\n[done] → {out_dir}")


if __name__ == "__main__":
    main()
