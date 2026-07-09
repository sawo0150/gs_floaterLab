#!/usr/bin/env python3
"""Z-layer XY scatter — OpenMAVIS ORB-SLAM map points, one page per layer.

Same layout as real_sparse_zlayers_v2.py but:
  - source : data/rgb_3dgs_openmavis_batch_301_1253 (7,182 ORB-SLAM pts, 57 keyframes)
  - color  : observation count (nObs) — low = uncertain, high = confident
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import json
import matplotlib
matplotlib.use("Agg")

import matplotlib.font_manager as fm
for _f in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    fm.fontManager.addfont(_f)
matplotlib.rcParams["font.family"] = "Noto Sans CJK JP"
matplotlib.rcParams["axes.unicode_minus"] = False

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

# ── palette ───────────────────────────────────────────────────────────────────
C_SURFACE    = "#F7F9FC"
C_GRID       = "#E2E8F0"
C_INK        = "#1A202C"
C_CONF_LO    = "#DBEAFE"   # low  obs → blue-100
C_CONF_HI    = "#1E3A8A"   # high obs → blue-900
C_LOW_CONF   = "#FCA5A5"   # obs <= 2 → muted red (uncertain)
C_TRAJ       = "#D97706"   # camera trajectory (amber)
C_CAM_MARKER = "#92400E"
C_FILT       = "#15803D"   # filter boundary (green)

# ── paths ─────────────────────────────────────────────────────────────────────
DATA_DIR   = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data")
BATCH_DIR  = DATA_DIR / "rgb_3dgs_openmavis_batch_301_1253"
PTS_TXT    = BATCH_DIR / "sparse/0/points3D.txt"
IMG_TXT    = BATCH_DIR / "sparse/0/images.txt"
MAP_PTS_JSONL = Path(
    "/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/results/runs"
    "/customdata_fisheye624_v2_30000"
    "/aria_0416_data_0416_301_1253_0416_301_1253_stereo_fisheye624_v2"
    "/orb_export/map_points.jsonl"
)

# ── layer descriptions (8 layers) ────────────────────────────────────────────
LAYER_DESC = [
    ("바닥 아래 (하부 공간)",          "씬 하한 부근. ORB-SLAM point 거의 없음.",                          "#EEF2FF"),
    ("바닥면 부근",                     "바닥 슬라브. low-obs 점 다수.",                                    "#EEF2FF"),
    ("바닥 / 하부 벽",                  "바닥 + 하부 벽. 고confidence 점 집중.",                            "#EFF6FF"),
    ("카메라 눈높이 아래",              "가장 잘 관측되는 표면. 고obs 점 최다.",                            "#EFF6FF"),
    ("카메라 눈높이 위",                "카메라 통과 높이 직상. 비슷하게 촘촘.",                            "#F0FDF4"),
    ("상부 벽 / 천장",                  "천장 + 상부 벽. 관측 수 급감 시작.",                              "#F0FDF4"),
    ("천장 위 — sparse 부족",          "ORB-SLAM 삼각화 각도 부족으로 점 급감. Pop 2 시작 구간.",          "#FFF7ED"),
    ("Pop 2 floater 위험 구간",         "ORB-SLAM 고confidence 점 사실상 0개. plateau 앵커 부재.",          "#FFF1F2"),
]


def _qvec2rotmat(qvec):
    w, x, y, z = qvec
    return np.array([
        [1-2*y*y-2*z*z, 2*x*y-2*w*z,   2*x*z+2*w*y],
        [2*x*y+2*w*z,   1-2*x*x-2*z*z, 2*y*z-2*w*x],
        [2*x*z-2*w*y,   2*y*z+2*w*x,   1-2*x*x-2*y*y],
    ])


def load_data():
    # ── map_points.jsonl → confidence dict ────────────────────────────────────
    conf = {}  # map_point_id → observations
    if MAP_PTS_JSONL.exists():
        with open(MAP_PTS_JSONL) as f:
            for line in f:
                d = json.loads(line)
                conf[d["map_point_id"]] = d["observations"]

    # ── points3D.txt → xyz + obs ───────────────────────────────────────────────
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

    # ── images.txt → camera centers ───────────────────────────────────────────
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

    return pts, obs, np.array(cams, dtype=np.float32)


def filter_bounds(cams, expand=1.0):
    lo = cams.min(0) - np.maximum((cams.max(0) - cams.min(0)) * expand, [2., 2., 3.])
    hi = cams.max(0) + np.maximum((cams.max(0) - cams.min(0)) * expand, [2., 2., 3.])
    return lo, hi


def make_conf_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("orb_conf", [C_CONF_LO, C_CONF_HI])


def one_layer_page(pdf, pts_in, obs_in, pts_out, cams,
                   filt_lo, filt_hi,
                   z_lo, z_hi, layer_idx, n_total,
                   xmin, xmax, ymin, ymax,
                   cmap, obs_max):

    label, interp, bg = LAYER_DESC[layer_idx]
    mask  = (pts_in[:, 2] >= z_lo) & (pts_in[:, 2] < z_hi)
    slab  = pts_in[mask]
    slab_obs = obs_in[mask]
    n     = len(slab)
    pct   = 100 * n / n_total if n_total > 0 else 0.0

    n_lo_conf = int((slab_obs <= 2).sum())
    n_hi_conf = int((slab_obs >= 10).sum())

    # ── figure ────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(13, 9.5), facecolor="white")

    # Header
    hax = fig.add_axes([0, 0.88, 1, 0.12])
    hax.set_facecolor(bg); hax.axis("off")
    hax.text(0.5, 0.72,
             f"Layer {layer_idx+1} / 8   —   Z ∈ [{z_lo:.2f}, {z_hi:.2f}) m",
             ha="center", fontsize=15, fontweight="bold", color=C_INK)
    hax.text(0.5, 0.30,
             f"{label}   |   {n:,} pts  (obs≤2: {n_lo_conf}, obs≥10: {n_hi_conf})",
             ha="center", fontsize=11, color="#444")
    hax.text(0.5, 0.08, interp,
             ha="center", fontsize=9.5, color="#666", style="italic")

    # Main axes
    ax = fig.add_axes([0.07, 0.20, 0.88, 0.67])
    ax.set_facecolor(C_SURFACE)
    ax.set_aspect("equal")
    ax.grid(True, color=C_GRID, linewidth=0.6, zorder=0)

    # Out-of-bound points (subsampled) — reuse muted red like v2
    if len(pts_out) > 0:
        sub = pts_out[::max(1, len(pts_out)//500)]
        ax.scatter(sub[:, 0], sub[:, 1],
                   c=C_LOW_CONF, s=4, alpha=0.25,
                   linewidths=0, rasterized=True, zorder=1)

    # In-layer points coloured by observations
    if n > 0:
        norm = Normalize(vmin=1, vmax=obs_max)
        colors = cmap(norm(slab_obs.astype(float)))
        # draw low-conf first, then high-conf on top
        order = np.argsort(slab_obs)
        ax.scatter(slab[order, 0], slab[order, 1],
                   c=colors[order], s=12, alpha=0.9,
                   linewidths=0, rasterized=True, zorder=2)

    # Camera trajectory (57 keyframes — show ALL, mark every 5th)
    ax.plot(cams[:, 0], cams[:, 1],
            color=C_TRAJ, lw=2.0, alpha=0.9, zorder=4)
    ax.scatter(cams[::5, 0], cams[::5, 1],
               c=C_CAM_MARKER, s=45, marker="^",
               linewidths=0, zorder=5)

    # Filter boundary
    rect = mpatches.FancyBboxPatch(
        (filt_lo[0], filt_lo[1]),
        filt_hi[0] - filt_lo[0], filt_hi[1] - filt_lo[1],
        boxstyle="square,pad=0", linewidth=2,
        edgecolor=C_FILT, facecolor="none", zorder=6)
    ax.add_patch(rect)

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("X  (m) — 카메라 이동 방향 (depth axis)", fontsize=10, color=C_INK)
    ax.set_ylabel("Y  (m) — 좌우 방향", fontsize=10, color=C_INK)
    ax.tick_params(colors="#666", labelsize=8)
    for sp in ax.spines.values():
        sp.set_edgecolor(C_GRID)

    # ── callout annotations ───────────────────────────────────────────────────
    mid_idx = len(cams) // 2
    ax.annotate(
        f"카메라 경로\n(57 keyframes  △=5f마다)",
        xy=(cams[mid_idx, 0], cams[mid_idx, 1]),
        xytext=(cams[mid_idx, 0] + 3.0, cams[mid_idx, 1] - 2.0),
        fontsize=7.5, color=C_TRAJ,
        arrowprops=dict(arrowstyle="->", color=C_TRAJ, lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFFBEB",
                  edgecolor="#FDE68A", alpha=0.9))

    ax.annotate(
        "init_pcd_filter 경계\n(이 밖 → 3DGS init 제거)",
        xy=(filt_lo[0], 0.0),
        xytext=(filt_lo[0] + 2.5, -2.0),
        fontsize=7.5, color=C_FILT,
        arrowprops=dict(arrowstyle="->", color=C_FILT, lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#F0FDF4",
                  edgecolor="#BBF7D0", alpha=0.9))

    if n > 0:
        hi_mask = slab_obs >= 10
        if hi_mask.any():
            cx = float(np.median(slab[hi_mask, 0]))
            cy = float(np.median(slab[hi_mask, 1]))
            ax.annotate(
                f"고confidence 점 (obs≥10)\nn={n_hi_conf}개",
                xy=(cx, cy),
                xytext=(cx + 3.5, cy + 2.0),
                fontsize=7.5, color=C_CONF_HI,
                arrowprops=dict(arrowstyle="->", color=C_CONF_HI, lw=1.2),
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#EFF6FF",
                          edgecolor="#BFDBFE", alpha=0.9))
        if n_lo_conf > 0:
            lo_mask = slab_obs <= 2
            lx = float(np.median(slab[lo_mask, 0]))
            ly = float(np.median(slab[lo_mask, 1]))
            ax.annotate(
                f"저confidence 점 (obs≤2)\nn={n_lo_conf}개",
                xy=(lx, ly),
                xytext=(lx - 4.0, ly + 2.0),
                fontsize=7.5, color="#B91C1C",
                arrowprops=dict(arrowstyle="->", color="#B91C1C", lw=1.2),
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#FEF2F2",
                          edgecolor="#FECACA", alpha=0.9))

    # ── colorbar ─────────────────────────────────────────────────────────────
    sm = ScalarMappable(cmap=cmap, norm=Normalize(1, obs_max))
    sm.set_array([])
    cbar_ax = fig.add_axes([0.965, 0.20, 0.012, 0.67])
    cb = fig.colorbar(sm, cax=cbar_ax)
    cb.set_label("관측 횟수 (observations)", fontsize=8, color=C_INK)
    cb.ax.tick_params(labelsize=7, colors="#666")
    ticks = [1, max(2, obs_max // 3), max(3, 2 * obs_max // 3), obs_max]
    cb.ax.yaxis.set_ticks([t for t in ticks if 1 <= t <= obs_max])

    # ── legend panel ─────────────────────────────────────────────────────────
    leg_ax = fig.add_axes([0.07, 0.00, 0.88, 0.18])
    leg_ax.set_facecolor("#F8FAFC"); leg_ax.axis("off")

    defs = [
        (C_CONF_HI, "●",
         "고confidence ORB-SLAM point (obs≥10)",
         "ORB-SLAM이 10개 이상 keyframe에서 관측한 점. 삼각화 정밀도 높음. 진한 파란색."),
        (C_CONF_LO, "●",
         "저confidence ORB-SLAM point (obs=1~2)",
         "소수 keyframe에서만 관측됨. 삼각화 불안정. 연한 파란색. plateau 앵커 부적합."),
        (C_TRAJ, "▶",
         "카메라 이동 경로 (57 keyframes)",
         "OpenMAVIS SLAM이 추출한 keyframe 카메라 위치. MPS 기반 1,311장보다 훨씬 적음."),
        (C_FILT, "□",
         "init_pcd_filter 경계",
         "카메라 extent × expand=1.0. 이 경계 밖 점은 3DGS 초기화 전 제거."),
    ]

    xs = [0.01, 0.26, 0.52, 0.76]
    for i, (color, mark, name, desc) in enumerate(defs):
        x = xs[i]
        leg_ax.text(x, 0.88, f"{mark}  {name}",
                    fontsize=8.5, fontweight="bold", color=color,
                    transform=leg_ax.transAxes, va="top")
        leg_ax.text(x, 0.68, desc,
                    fontsize=7.2, color="#444",
                    transform=leg_ax.transAxes, va="top", wrap=True)

    pdf.savefig(fig, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  layer {layer_idx+1}: Z[{z_lo:.2f},{z_hi:.2f})  "
          f"n={n:,}  hi-conf={n_hi_conf}  lo-conf={n_lo_conf}")


def cover_page(pdf, n_in, n_out, n_cams, filt_lo, filt_hi, obs_arr):
    fig = plt.figure(figsize=(13, 9.5), facecolor="white")
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("white"); ax.axis("off")

    ax.text(0.5, 0.84, "301-1253  OpenMAVIS ORB-SLAM Sparse Points",
            ha="center", fontsize=22, fontweight="bold", color=C_INK)
    ax.text(0.5, 0.76, "Z축 단면 분석  —  XY 평면, confidence (observations) 색상",
            ha="center", fontsize=14, color="#555")

    hi_conf = int((obs_arr >= 10).sum())
    lo_conf = int((obs_arr <= 2).sum())

    stats = [
        ("ORB-SLAM map points 총계",     f"{n_in + n_out:,}"),
        ("In-filter",                    f"{n_in:,}"),
        ("Out-of-filter (제거 대상)",    f"{n_out:,}"),
        ("고confidence (obs≥10)",        f"{hi_conf:,}  ({100*hi_conf/max(n_in,1):.1f}%)"),
        ("저confidence (obs≤2)",         f"{lo_conf:,}  ({100*lo_conf/max(n_in,1):.1f}%)"),
        ("카메라 keyframe 수",           f"{n_cams:,}"),
        ("필터 Z 범위",                  f"[{filt_lo[2]:.2f}, {filt_hi[2]:.2f}] m"),
        ("obs 중앙값 / 최대값",          f"{int(np.median(obs_arr))} / {int(obs_arr.max())}"),
        ("레이어 수",                    "8  (각 ≈ 0.76 m)"),
    ]
    y0 = 0.65
    for label, val in stats:
        ax.text(0.35, y0, label, ha="right", fontsize=11, color="#666")
        ax.text(0.37, y0, val,   ha="left",  fontsize=11, color=C_INK, fontweight="bold")
        y0 -= 0.052

    ax.text(0.5, 0.18,
            "※ MPS semi-dense(626,811 pts, 1,311 frames)와 달리\n"
            "   ORB-SLAM map points는 7,182개, 57 keyframes.\n"
            "   Pop 2 구간(Z=+2~3m)의 고confidence 점은 사실상 0개.",
            ha="center", fontsize=10, color="#B45309",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#FFFBEB",
                      edgecolor="#FDE68A", alpha=0.9))

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def main():
    out_root = Path("results/diagnostic")
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir  = out_root / f"orb_zlayers_v1_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[load] OpenMAVIS ORB-SLAM data …")
    pts3d, obs, cams = load_data()
    print(f"  pts={len(pts3d):,}  cams={len(cams)}")

    filt_lo, filt_hi = filter_bounds(cams, expand=1.0)
    valid = (
        (pts3d[:, 0] >= filt_lo[0]) & (pts3d[:, 0] <= filt_hi[0]) &
        (pts3d[:, 1] >= filt_lo[1]) & (pts3d[:, 1] <= filt_hi[1]) &
        (pts3d[:, 2] >= filt_lo[2]) & (pts3d[:, 2] <= filt_hi[2])
    )
    pts_in, obs_in = pts3d[valid], obs[valid]
    pts_out        = pts3d[~valid]

    z_edges = np.linspace(float(filt_lo[2]), float(filt_hi[2]), 9)
    pad  = 0.8
    xmin = float(pts_in[:, 0].min()) - pad
    xmax = float(pts_in[:, 0].max()) + pad
    ymin = float(pts_in[:, 1].min()) - pad
    ymax = float(pts_in[:, 1].max()) + pad

    obs_max = max(int(np.percentile(obs_in, 98)), 10)
    cmap    = make_conf_cmap()
    pdf_path = out_dir / "orb_zlayer_annotated.pdf"

    print(f"[render] 8 layers → {pdf_path}")
    with PdfPages(pdf_path) as pdf:
        cover_page(pdf, len(pts_in), len(pts_out), len(cams),
                   filt_lo, filt_hi, obs_in)
        for i in range(8):
            one_layer_page(
                pdf, pts_in, obs_in, pts_out, cams,
                filt_lo, filt_hi,
                z_edges[i], z_edges[i+1],
                i, len(pts_in),
                xmin, xmax, ymin, ymax,
                cmap, obs_max,
            )

    print(f"\n[done] → {pdf_path}")


if __name__ == "__main__":
    main()
