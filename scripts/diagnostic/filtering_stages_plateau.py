#!/usr/bin/env python3
"""
filtering_stages_plateau.py

각 filtering 단계마다 PDF 2개 생성:
  1. Z-layer scatter PDF  — orb_zlayers_v1 스타일, 필터 결과 반영
  2. Plateau coverage PDF — tau_j 크기 + coverage heatmap

Stages:
  0  Raw           — 필터 없음 (전체 7,182 pts)
  1  Z-bound       — init_pcd_filter 경계 (카메라 extent × 1.0)
  2  + obs≥3       — 저confidence (obs≤2) 추가 제거
  3  + kNN isolate — 공간 고립 점 추가 제거 (kNN5 dist > 3× median)

Output: results/diagnostic/filtering_stages_<ts>/
  stage0_raw_zlayer.pdf        stage0_raw_plateau.pdf
  stage1_zbound_zlayer.pdf     stage1_zbound_plateau.pdf
  stage2_obs3_zlayer.pdf       stage2_obs3_plateau.pdf
  stage3_knn_zlayer.pdf        stage3_knn_plateau.pdf
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
from sklearn.neighbors import BallTree, NearestNeighbors

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

# ── tau parameters ──────────────────────────────────────────────────────────────
KNN_K         = 5      # k-NN order for local spacing h_j
ALPHA         = 0.6    # tau_j = alpha × h_j
TAU_MIN       = 0.05   # m  (최소 5cm)
TAU_MAX       = 0.60   # m  (최대 60cm)
KNN_ISO_MULT  = 3.0    # kNN isolation: outlier if kNN5_dist > mult × median

# ── palette ────────────────────────────────────────────────────────────────────
C_SURFACE  = "#F7F9FC"
C_GRID     = "#E2E8F0"
C_INK      = "#1A202C"
C_CONF_LO  = "#DBEAFE"   # obs=low → blue-100
C_CONF_HI  = "#1E3A8A"   # obs=high → blue-900
C_LOW_CONF = "#FCA5A5"   # obs≤2 (background scatter)
C_TRAJ     = "#D97706"
C_CAM_MRK  = "#92400E"
C_FILT     = "#15803D"
C_REMOVED  = "#FCA5A5"   # removed points overlay

# tau colormap: light green (small tau) → dark green (large tau)
CMAP_TAU = LinearSegmentedColormap.from_list("tau_green", ["#D1FAE5", "#065F46"])
# coverage heatmap fill color
C_COVER    = "#3B82F6"   # blue-500

# ── layer metadata ──────────────────────────────────────────────────────────────
LAYER_DESC = [
    ("바닥 아래 (하부 공간)",     "씬 하한 부근. ORB-SLAM point 거의 없음.",             "#EEF2FF"),
    ("바닥면 부근",               "바닥 슬라브. low-obs 점 다수.",                        "#EEF2FF"),
    ("바닥 / 하부 벽",            "바닥 + 하부 벽. 고confidence 점 집중.",                "#EFF6FF"),
    ("카메라 눈높이 아래",        "가장 잘 관측되는 표면. 고obs 점 최다.",                "#EFF6FF"),
    ("카메라 눈높이 위",          "카메라 통과 높이 직상. 비슷하게 촘촘.",                "#F0FDF4"),
    ("상부 벽 / 천장",            "천장 + 상부 벽. 관측 수 급감 시작.",                  "#F0FDF4"),
    ("천장 위 — sparse 부족",     "삼각화 각도 부족으로 점 급감. Pop 2 시작 구간.",       "#FFF7ED"),
    ("Pop 2 floater 위험 구간",   "고confidence 점 사실상 0개. plateau 앵커 부재.",        "#FFF1F2"),
]

STAGES = [
    dict(id=0, tag="raw",    label="Stage 0: Raw (필터 없음)",   obs_min=0, z_filter=False, knn_filter=False),
    dict(id=1, tag="zbound", label="Stage 1: Z-bound filter",    obs_min=0, z_filter=True,  knn_filter=False),
    dict(id=2, tag="obs3",   label="Stage 2: + obs≥3 filter",    obs_min=3, z_filter=True,  knn_filter=False),
    dict(id=3, tag="knn",    label="Stage 3: + kNN isolation",   obs_min=3, z_filter=True,  knn_filter=True),
]


# ══════════════════════════════════════════════════════════════════════════════
# Data loading
# ══════════════════════════════════════════════════════════════════════════════

def _qvec2rotmat(qvec):
    w, x, y, z = qvec
    return np.array([
        [1-2*y*y-2*z*z, 2*x*y-2*w*z,   2*x*z+2*w*y],
        [2*x*y+2*w*z,   1-2*x*x-2*z*z, 2*y*z-2*w*x],
        [2*x*z-2*w*y,   2*y*z+2*w*x,   1-2*x*x-2*y*y],
    ])


def load_raw():
    """Return pts[N,3], obs[N], cams[M,3] — all unfiltered."""
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

    return (
        np.array(pts_list, dtype=np.float32),
        np.array(obs_list,  dtype=np.int32),
        np.array(cams,      dtype=np.float32),
    )


def camera_bounds(cams, expand=1.0):
    lo = cams.min(0) - np.maximum((cams.max(0) - cams.min(0)) * expand, [2., 2., 3.])
    hi = cams.max(0) + np.maximum((cams.max(0) - cams.min(0)) * expand, [2., 2., 3.])
    return lo, hi


# ══════════════════════════════════════════════════════════════════════════════
# Filtering pipeline
# ══════════════════════════════════════════════════════════════════════════════

def apply_knn_isolation(pts, obs, k=KNN_K, mult=KNN_ISO_MULT):
    if len(pts) <= k + 1:
        return pts, obs
    nbrs = NearestNeighbors(n_neighbors=k + 1, algorithm="ball_tree").fit(pts)
    dists, _ = nbrs.kneighbors(pts)
    knn_dist = dists[:, k]          # distance to k-th nearest (exclude self)
    threshold = mult * np.median(knn_dist)
    mask = knn_dist <= threshold
    removed = (~mask).sum()
    print(f"    kNN isolation: removed {removed} pts  (threshold={threshold:.3f}m, "
          f"median kNN={np.median(knn_dist):.3f}m)")
    return pts[mask], obs[mask]


def filter_stage(pts_raw, obs_raw, stage, filt_lo, filt_hi):
    """Apply cumulative filters up to stage['id']. Returns (pts, obs)."""
    pts, obs = pts_raw.copy(), obs_raw.copy()

    if stage["id"] == 0:
        return pts, obs

    # Stage 1: Z-bound (init_pcd_filter equivalent)
    valid = (
        (pts[:, 0] >= filt_lo[0]) & (pts[:, 0] <= filt_hi[0]) &
        (pts[:, 1] >= filt_lo[1]) & (pts[:, 1] <= filt_hi[1]) &
        (pts[:, 2] >= filt_lo[2]) & (pts[:, 2] <= filt_hi[2])
    )
    pts, obs = pts[valid], obs[valid]
    if stage["id"] == 1:
        return pts, obs

    # Stage 2: obs≥3
    mask = obs >= 3
    print(f"    obs≥3: removed {(~mask).sum()} pts (obs≤2)")
    pts, obs = pts[mask], obs[mask]
    if stage["id"] == 2:
        return pts, obs

    # Stage 3: kNN isolation
    pts, obs = apply_knn_isolation(pts, obs)
    return pts, obs


# ══════════════════════════════════════════════════════════════════════════════
# Tau computation
# ══════════════════════════════════════════════════════════════════════════════

def compute_tau(pts, k=KNN_K, alpha=ALPHA, tau_min=TAU_MIN, tau_max=TAU_MAX):
    """tau_j = clip(alpha × kNN_k_dist, tau_min, tau_max) in 3D."""
    if len(pts) <= k + 1:
        return np.full(len(pts), tau_min, dtype=np.float32)
    nbrs = NearestNeighbors(n_neighbors=k + 1, algorithm="ball_tree").fit(pts)
    dists, _ = nbrs.kneighbors(pts)
    h_j = dists[:, k]
    return np.clip(alpha * h_j, tau_min, tau_max).astype(np.float32)


# ══════════════════════════════════════════════════════════════════════════════
# Coverage heatmap helper
# ══════════════════════════════════════════════════════════════════════════════

def coverage_grid(anchor_xy, tau_j, xmin, xmax, ymin, ymax, nx=120, ny=160):
    """2D XY coverage: which grid cells are within tau_j of any anchor."""
    if len(anchor_xy) == 0:
        return np.zeros((ny, nx), dtype=bool), 0.0, 0.0

    xg = np.linspace(xmin, xmax, nx)
    yg = np.linspace(ymin, ymax, ny)
    XX, YY = np.meshgrid(xg, yg)
    grid_pts = np.stack([XX.ravel(), YY.ravel()], axis=1)

    tree = BallTree(anchor_xy)
    k_q  = min(3, len(anchor_xy))
    dists, inds = tree.query(grid_pts, k=k_q)
    # covered if any of the k nearest anchors' tau reaches this cell
    covered = np.any(dists <= tau_j[inds], axis=1)
    return covered.reshape(ny, nx), float(covered.mean()), float(np.median(tau_j))


# ══════════════════════════════════════════════════════════════════════════════
# Z-layer PDF  (orb_zlayers_v1 style + stage header + removed-pts overlay)
# ══════════════════════════════════════════════════════════════════════════════

def _conf_cmap():
    return LinearSegmentedColormap.from_list("orb_conf", [C_CONF_LO, C_CONF_HI])


def zlayer_cover_page(pdf, stage, n_pts, n_removed_total, obs_in, filt_lo, filt_hi, n_cams):
    fig = plt.figure(figsize=(13, 9.5), facecolor="white")
    ax  = fig.add_axes([0, 0, 1, 1]); ax.axis("off")

    ax.text(0.5, 0.88, stage["label"],
            ha="center", fontsize=22, fontweight="bold", color=C_INK)
    ax.text(0.5, 0.80, "Z-layer Scatter  ·  XY 평면  ·  observations 색상",
            ha="center", fontsize=13, color="#555")

    hi = int((obs_in >= 10).sum()) if len(obs_in) else 0
    lo = int((obs_in <= 2).sum())  if len(obs_in) else 0

    rows = [
        ("남은 points",               f"{n_pts:,}"),
        ("이번 단계 제거",             f"{n_removed_total:,}"),
        ("고confidence (obs≥10)",      f"{hi:,}  ({100*hi/max(n_pts,1):.1f}%)" if n_pts else "0"),
        ("저confidence (obs≤2)",       f"{lo:,}  ({100*lo/max(n_pts,1):.1f}%)" if n_pts else "0"),
        ("obs 중앙값 / 최대값",        f"{int(np.median(obs_in))} / {int(obs_in.max())}" if n_pts else "—"),
        ("카메라 keyframes",           f"{n_cams}"),
        ("필터 Z 범위",                f"[{filt_lo[2]:.2f}, {filt_hi[2]:.2f}] m"),
    ]
    y0 = 0.68
    for lbl, val in rows:
        ax.text(0.35, y0, lbl, ha="right", fontsize=11, color="#666")
        ax.text(0.37, y0, val, ha="left",  fontsize=11, color=C_INK, fontweight="bold")
        y0 -= 0.055

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)


def zlayer_one_page(pdf, pts_in, obs_in, pts_prev, cams,
                    filt_lo, filt_hi, z_lo, z_hi,
                    layer_idx, xmin, xmax, ymin, ymax,
                    cmap, obs_max, stage_label):
    label, interp, bg = LAYER_DESC[layer_idx]
    mask     = (pts_in[:, 2] >= z_lo) & (pts_in[:, 2] < z_hi)
    slab     = pts_in[mask];  slab_obs = obs_in[mask];  n = len(slab)
    n_lo     = int((slab_obs <= 2).sum());  n_hi = int((slab_obs >= 10).sum())

    # removed points in this layer (from previous stage)
    if pts_prev is not None:
        mask_prev = (pts_prev[:, 2] >= z_lo) & (pts_prev[:, 2] < z_hi)
        removed_slab = pts_prev[mask_prev]
    else:
        removed_slab = np.empty((0, 3))

    fig = plt.figure(figsize=(13, 9.5), facecolor="white")
    hax = fig.add_axes([0, 0.88, 1, 0.12])
    hax.set_facecolor(bg); hax.axis("off")
    hax.text(0.5, 0.72,
             f"[{stage_label}]  Layer {layer_idx+1}/8  —  Z ∈ [{z_lo:.2f}, {z_hi:.2f}) m",
             ha="center", fontsize=14, fontweight="bold", color=C_INK)
    hax.text(0.5, 0.28,
             f"{label}   |   {n:,} pts  (obs≤2: {n_lo}, obs≥10: {n_hi})",
             ha="center", fontsize=11, color="#444")
    hax.text(0.5, 0.06, interp,
             ha="center", fontsize=9.5, color="#666", style="italic")

    ax = fig.add_axes([0.07, 0.20, 0.88, 0.67])
    ax.set_facecolor(C_SURFACE); ax.set_aspect("equal")
    ax.grid(True, color=C_GRID, linewidth=0.6, zorder=0)

    # Removed points overlay (cross markers, muted red)
    if len(removed_slab) > 0:
        ax.scatter(removed_slab[:, 0], removed_slab[:, 1],
                   c=C_REMOVED, s=18, marker="x", linewidths=0.8,
                   alpha=0.55, zorder=1, label=f"제거됨 ({len(removed_slab)})")

    # In-layer points coloured by obs
    if n > 0:
        norm   = Normalize(vmin=1, vmax=obs_max)
        colors = cmap(norm(slab_obs.astype(float)))
        order  = np.argsort(slab_obs)
        ax.scatter(slab[order, 0], slab[order, 1],
                   c=colors[order], s=12, alpha=0.9,
                   linewidths=0, rasterized=True, zorder=2)

    # Camera trajectory
    ax.plot(cams[:, 0], cams[:, 1], color=C_TRAJ, lw=2.0, alpha=0.9, zorder=4)
    ax.scatter(cams[::5, 0], cams[::5, 1], c=C_CAM_MRK, s=45,
               marker="^", linewidths=0, zorder=5)

    # Filter boundary
    rect = mpatches.FancyBboxPatch(
        (filt_lo[0], filt_lo[1]),
        filt_hi[0]-filt_lo[0], filt_hi[1]-filt_lo[1],
        boxstyle="square,pad=0", linewidth=2,
        edgecolor=C_FILT, facecolor="none", zorder=6)
    ax.add_patch(rect)

    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
    ax.set_xlabel("X (m) — 카메라 이동 방향 (depth axis)", fontsize=10, color=C_INK)
    ax.set_ylabel("Y (m) — 좌우 방향",                     fontsize=10, color=C_INK)
    ax.tick_params(colors="#666", labelsize=8)
    for sp in ax.spines.values(): sp.set_edgecolor(C_GRID)

    # Annotations
    mid = len(cams) // 2
    ax.annotate("카메라 경로\n(57 keyframes △=5f마다)",
        xy=(cams[mid,0], cams[mid,1]),
        xytext=(cams[mid,0]+3.0, cams[mid,1]-2.0), fontsize=7.5, color=C_TRAJ,
        arrowprops=dict(arrowstyle="->", color=C_TRAJ, lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFFBEB", edgecolor="#FDE68A", alpha=0.9))

    ax.annotate("init_pcd_filter 경계",
        xy=(filt_lo[0], 0.0), xytext=(filt_lo[0]+2.5, -2.0),
        fontsize=7.5, color=C_FILT,
        arrowprops=dict(arrowstyle="->", color=C_FILT, lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#F0FDF4", edgecolor="#BBF7D0", alpha=0.9))

    if n > 0 and n_hi > 0:
        hi_m = slab_obs >= 10
        cx, cy = float(np.median(slab[hi_m,0])), float(np.median(slab[hi_m,1]))
        ax.annotate(f"고confidence (obs≥10)\nn={n_hi}개",
            xy=(cx,cy), xytext=(cx+3.5, cy+2.0), fontsize=7.5, color=C_CONF_HI,
            arrowprops=dict(arrowstyle="->", color=C_CONF_HI, lw=1.2),
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#EFF6FF", edgecolor="#BFDBFE", alpha=0.9))

    if n > 0 and n_lo > 0:
        lo_m = slab_obs <= 2
        lx, ly = float(np.median(slab[lo_m,0])), float(np.median(slab[lo_m,1]))
        ax.annotate(f"저confidence (obs≤2)\nn={n_lo}개",
            xy=(lx,ly), xytext=(lx-4.0, ly+2.0), fontsize=7.5, color="#B91C1C",
            arrowprops=dict(arrowstyle="->", color="#B91C1C", lw=1.2),
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FEF2F2", edgecolor="#FECACA", alpha=0.9))

    if len(removed_slab) > 0:
        rx, ry = float(removed_slab[:,0].mean()), float(removed_slab[:,1].mean())
        ax.annotate(f"이번 단계 제거 (×)\nn={len(removed_slab)}개",
            xy=(rx,ry), xytext=(rx-5.0, ry+3.0), fontsize=7.5, color="#9F1239",
            arrowprops=dict(arrowstyle="->", color="#9F1239", lw=1.2),
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF1F2", edgecolor="#FECDD3", alpha=0.9))

    # Colorbar
    sm = ScalarMappable(cmap=cmap, norm=Normalize(1, obs_max)); sm.set_array([])
    cbar_ax = fig.add_axes([0.965, 0.20, 0.012, 0.67])
    cb = fig.colorbar(sm, cax=cbar_ax)
    cb.set_label("observations", fontsize=8, color=C_INK)
    cb.ax.tick_params(labelsize=7, colors="#666")

    # Legend
    leg = fig.add_axes([0.07, 0.00, 0.88, 0.18])
    leg.set_facecolor("#F8FAFC"); leg.axis("off")
    defs = [
        (C_CONF_HI, "●", "고confidence (obs≥10)", "10개+ keyframe에서 관측. plateau 앵커 적합."),
        (C_CONF_LO, "●", "저confidence (obs=1~2)", "소수 keyframe에서만 관측. 앵커 부적합."),
        (C_REMOVED, "×", "이번 단계 제거된 점",   "직전 stage에는 있었으나 현 stage에서 제거됨."),
        (C_FILT,    "□", "init_pcd_filter 경계",   "카메라 extent ×1.0. 이 밖은 3DGS init 제거."),
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


def make_zlayer_pdf(out_path, stage, pts, obs, pts_prev, cams, filt_lo, filt_hi):
    z_edges = np.linspace(float(filt_lo[2]), float(filt_hi[2]), 9)
    n_removed = len(pts_prev) - len(pts) if pts_prev is not None else 0
    pad  = 1.0
    all_pts = pts if len(pts) > 0 else pts_prev
    xmin = min(float(all_pts[:,0].min()), float(filt_lo[0])) - pad
    xmax = max(float(all_pts[:,0].max()), float(filt_hi[0])) + pad
    ymin = min(float(all_pts[:,1].min()), float(filt_lo[1])) - pad
    ymax = max(float(all_pts[:,1].max()), float(filt_hi[1])) + pad
    obs_max = max(int(np.percentile(obs, 98)), 10) if len(obs) else 10
    cmap    = _conf_cmap()

    print(f"  [zlayer] {out_path.name}  n={len(pts):,}  removed={n_removed}")
    with PdfPages(out_path) as pdf:
        zlayer_cover_page(pdf, stage, len(pts), n_removed, obs, filt_lo, filt_hi, len(cams))
        for i in range(8):
            zlayer_one_page(pdf, pts, obs, pts_prev, cams,
                            filt_lo, filt_hi,
                            z_edges[i], z_edges[i+1],
                            i, xmin, xmax, ymin, ymax,
                            cmap, obs_max, stage["tag"])


# ══════════════════════════════════════════════════════════════════════════════
# Plateau PDF
# ══════════════════════════════════════════════════════════════════════════════

def plateau_cover_page(pdf, stage, pts, tau_j, n_cams, filt_lo, filt_hi):
    fig = plt.figure(figsize=(13, 9.5), facecolor="white")
    ax  = fig.add_axes([0, 0, 1, 1]); ax.axis("off")

    ax.text(0.5, 0.88, f"{stage['label']}  ·  Plateau Coverage",
            ha="center", fontsize=21, fontweight="bold", color=C_INK)
    ax.text(0.5, 0.80, f"tau_j = clip({ALPHA} × kNN{KNN_K}_dist,  {TAU_MIN}m,  {TAU_MAX}m)",
            ha="center", fontsize=13, color="#555", family="monospace")

    rows = [
        ("앵커 점 수",              f"{len(pts):,}"),
        ("tau 중앙값",              f"{float(np.median(tau_j)):.3f} m"   if len(tau_j) else "—"),
        ("tau 범위 [min, max]",     f"[{float(tau_j.min()):.3f}, {float(tau_j.max()):.3f}] m" if len(tau_j) else "—"),
        ("tau = TAU_MIN (clip lo)", f"{(tau_j == TAU_MIN).sum():,}  ({100*(tau_j==TAU_MIN).mean():.1f}%)"),
        ("tau = TAU_MAX (clip hi)", f"{(tau_j == TAU_MAX).sum():,}  ({100*(tau_j==TAU_MAX).mean():.1f}%)"),
        ("카메라 keyframes",        f"{n_cams}"),
        ("alpha",                   f"{ALPHA}"),
        ("kNN k",                   f"{KNN_K}"),
    ]
    y0 = 0.68
    for lbl, val in rows:
        ax.text(0.35, y0, lbl, ha="right", fontsize=11, color="#666")
        ax.text(0.37, y0, val, ha="left",  fontsize=11, color=C_INK, fontweight="bold")
        y0 -= 0.055

    ax.text(0.5, 0.18,
            "heatmap = 이 layer의 앵커 점들이 XY 평면에 만드는 plateau 커버리지\n"
            "점 색상 = tau_j 크기 (연초록=작은 tau, 진초록=큰 tau)\n"
            "파란 배경 = plateau 커버된 XY 셀 (120×160 grid)",
            ha="center", fontsize=10, color="#1E40AF",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#EFF6FF",
                      edgecolor="#BFDBFE", alpha=0.9))

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)


def plateau_one_page(pdf, pts, obs, tau_j, cams, filt_lo, filt_hi,
                     z_lo, z_hi, layer_idx, xmin, xmax, ymin, ymax,
                     stage_label):
    label, interp, bg = LAYER_DESC[layer_idx]
    mask     = (pts[:, 2] >= z_lo) & (pts[:, 2] < z_hi)
    slab     = pts[mask];  slab_tau = tau_j[mask];  n = len(slab)
    slab_obs = obs[mask]

    n_hi = int((slab_obs >= 10).sum())
    n_lo = int((slab_obs <= 2).sum())

    # Coverage heatmap (XY only, from this layer's anchors)
    anchor_xy = slab[:, :2] if n > 0 else np.empty((0,2))
    cov_grid, cov_frac, tau_med = coverage_grid(
        anchor_xy, slab_tau, xmin, xmax, ymin, ymax)

    fig = plt.figure(figsize=(13, 9.5), facecolor="white")
    hax = fig.add_axes([0, 0.88, 1, 0.12])
    hax.set_facecolor(bg); hax.axis("off")
    hax.text(0.5, 0.72,
             f"[{stage_label}] Plateau  Layer {layer_idx+1}/8  —  Z ∈ [{z_lo:.2f}, {z_hi:.2f}) m",
             ha="center", fontsize=14, fontweight="bold", color=C_INK)
    hax.text(0.5, 0.28,
             f"{label}   |   {n:,} anchors   coverage {cov_frac*100:.1f}%   "
             f"tau_med={tau_med:.3f}m",
             ha="center", fontsize=11, color="#444")
    hax.text(0.5, 0.06, interp,
             ha="center", fontsize=9.5, color="#666", style="italic")

    ax = fig.add_axes([0.07, 0.20, 0.88, 0.67])
    ax.set_facecolor(C_SURFACE); ax.set_aspect("equal")
    ax.grid(True, color=C_GRID, linewidth=0.6, zorder=0)

    # Coverage heatmap
    xg = np.linspace(xmin, xmax, cov_grid.shape[1])
    yg = np.linspace(ymin, ymax, cov_grid.shape[0])
    cov_rgba = np.zeros((*cov_grid.shape, 4))
    cov_rgba[cov_grid, :] = [0.231, 0.510, 0.965, 0.28]   # blue, alpha 0.28
    ax.imshow(cov_rgba, origin="lower",
              extent=[xmin, xmax, ymin, ymax],
              aspect="equal", zorder=1, interpolation="nearest")

    # Anchor points coloured by tau_j
    if n > 0:
        norm_tau = Normalize(vmin=TAU_MIN, vmax=TAU_MAX)
        colors   = CMAP_TAU(norm_tau(slab_tau))
        order    = np.argsort(slab_tau)
        ax.scatter(slab[order,0], slab[order,1],
                   c=colors[order], s=14, alpha=0.92,
                   linewidths=0, rasterized=True, zorder=3)

    # Camera trajectory
    ax.plot(cams[:,0], cams[:,1], color=C_TRAJ, lw=2.0, alpha=0.9, zorder=5)
    ax.scatter(cams[::5,0], cams[::5,1], c=C_CAM_MRK, s=45,
               marker="^", linewidths=0, zorder=6)

    # Filter boundary
    rect = mpatches.FancyBboxPatch(
        (filt_lo[0], filt_lo[1]),
        filt_hi[0]-filt_lo[0], filt_hi[1]-filt_lo[1],
        boxstyle="square,pad=0", linewidth=2,
        edgecolor=C_FILT, facecolor="none", zorder=7)
    ax.add_patch(rect)

    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
    ax.set_xlabel("X (m) — 카메라 이동 방향 (depth axis)", fontsize=10, color=C_INK)
    ax.set_ylabel("Y (m) — 좌우 방향",                     fontsize=10, color=C_INK)
    ax.tick_params(colors="#666", labelsize=8)
    for sp in ax.spines.values(): sp.set_edgecolor(C_GRID)

    # Coverage callout
    ax.text(0.02, 0.97,
            f"XY coverage: {cov_frac*100:.1f}%\ntau_med: {tau_med:.3f}m\nn={n:,}",
            transform=ax.transAxes, fontsize=9, color="#1E40AF", va="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#EFF6FF",
                      edgecolor="#93C5FD", alpha=0.92))

    # Annotate large/small tau examples
    if n > 0:
        i_max = int(np.argmax(slab_tau))
        ax.annotate(f"큰 tau={slab_tau[i_max]:.2f}m\n(sparse 구간)",
            xy=(slab[i_max,0], slab[i_max,1]),
            xytext=(slab[i_max,0]+2.5, slab[i_max,1]+1.5),
            fontsize=7.5, color="#065F46",
            arrowprops=dict(arrowstyle="->", color="#065F46", lw=1.2),
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#D1FAE5",
                      edgecolor="#6EE7B7", alpha=0.9))

        i_min = int(np.argmin(slab_tau))
        ax.annotate(f"작은 tau={slab_tau[i_min]:.2f}m\n(dense 구간)",
            xy=(slab[i_min,0], slab[i_min,1]),
            xytext=(slab[i_min,0]-5.0, slab[i_min,1]-2.0),
            fontsize=7.5, color="#14532D",
            arrowprops=dict(arrowstyle="->", color="#14532D", lw=1.2),
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#F0FDF4",
                      edgecolor="#BBF7D0", alpha=0.9))

    # Tau colorbar
    sm_tau = ScalarMappable(cmap=CMAP_TAU, norm=Normalize(TAU_MIN, TAU_MAX))
    sm_tau.set_array([])
    cbar_ax = fig.add_axes([0.965, 0.20, 0.012, 0.67])
    cb = fig.colorbar(sm_tau, cax=cbar_ax)
    cb.set_label(f"tau_j (m)", fontsize=8, color=C_INK)
    cb.ax.yaxis.set_ticks([TAU_MIN, (TAU_MIN+TAU_MAX)/2, TAU_MAX])
    cb.ax.tick_params(labelsize=7, colors="#666")

    # Legend
    leg = fig.add_axes([0.07, 0.00, 0.88, 0.18])
    leg.set_facecolor("#F8FAFC"); leg.axis("off")
    defs = [
        ("#3B82F6", "■", "Plateau 커버리지 (파란 배경)",
         f"이 Z layer 앵커들의 XY 투영. tau_j 반경 내 = 커버됨."),
        ("#065F46", "●", f"앵커 점 (진초록 = tau={TAU_MAX}m / 연초록 = tau={TAU_MIN}m)",
         "tau_j = clip(0.6 × kNN5_dist, 0.05m, 0.60m). 밀집=작은 tau, 희소=큰 tau."),
        (C_TRAJ,   "▶", "카메라 이동 경로 (57 keyframes)",
         "OpenMAVIS SLAM keyframe 위치."),
        (C_FILT,   "□", "init_pcd_filter 경계",
         "이 밖 점은 3DGS 초기화 전 제거."),
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


def make_plateau_pdf(out_path, stage, pts, obs, tau_j, cams, filt_lo, filt_hi):
    z_edges = np.linspace(float(filt_lo[2]), float(filt_hi[2]), 9)
    pad  = 1.0
    anchor_pts = pts if len(pts) > 0 else cams
    xmin = min(float(anchor_pts[:,0].min()), float(filt_lo[0])) - pad
    xmax = max(float(anchor_pts[:,0].max()), float(filt_hi[0])) + pad
    ymin = min(float(anchor_pts[:,1].min()), float(filt_lo[1])) - pad
    ymax = max(float(anchor_pts[:,1].max()), float(filt_hi[1])) + pad

    print(f"  [plateau] {out_path.name}  n={len(pts):,}  "
          f"tau_med={np.median(tau_j):.3f}m")
    with PdfPages(out_path) as pdf:
        plateau_cover_page(pdf, stage, pts, tau_j, len(cams), filt_lo, filt_hi)
        for i in range(8):
            plateau_one_page(pdf, pts, obs, tau_j, cams,
                             filt_lo, filt_hi,
                             z_edges[i], z_edges[i+1],
                             i, xmin, xmax, ymin, ymax,
                             stage["tag"])


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = OUT_ROOT / f"filtering_stages_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[output] {out_dir}\n")

    print("[load] raw data …")
    pts_raw, obs_raw, cams = load_raw()
    filt_lo, filt_hi = camera_bounds(cams, expand=1.0)
    print(f"  raw pts={len(pts_raw):,}  cams={len(cams)}")
    print(f"  Z filter [{filt_lo[2]:.2f}, {filt_hi[2]:.2f}] m\n")

    prev_pts = None

    for stage in STAGES:
        print(f"── {stage['label']} ──────────────────────────")
        pts, obs = filter_stage(pts_raw, obs_raw, stage, filt_lo, filt_hi)
        print(f"  pts remaining: {len(pts):,}")

        tau_j = compute_tau(pts)
        print(f"  tau: med={np.median(tau_j):.3f}m  "
              f"min={tau_j.min():.3f}m  max={tau_j.max():.3f}m")

        tag = f"stage{stage['id']}_{stage['tag']}"
        make_zlayer_pdf(
            out_dir / f"{tag}_zlayer.pdf",
            stage, pts, obs, prev_pts, cams, filt_lo, filt_hi)
        make_plateau_pdf(
            out_dir / f"{tag}_plateau.pdf",
            stage, pts, obs, tau_j, cams, filt_lo, filt_hi)

        prev_pts = pts
        print()

    print(f"\n[done] 8 PDFs → {out_dir}")


if __name__ == "__main__":
    main()
