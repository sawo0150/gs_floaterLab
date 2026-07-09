#!/usr/bin/env python3
"""Z-layer XY scatter — one page per layer, fully annotated."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

# Korean font setup
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

# ── palette (light-mode, validated for CVD) ───────────────────────────────────
C_SURFACE = "#F7F9FC"   # page / axes background
C_GRID    = "#E2E8F0"   # subtle grid
C_INK     = "#1A202C"   # primary text

C_SPARSE_LO  = "#BFDBFE"  # low-density sparse pt  (blue-100)
C_SPARSE_HI  = "#1D4ED8"  # high-density sparse pt (blue-700)
C_OUTLIER    = "#FCA5A5"  # SLAM outlier (red-300, deemphasized)
C_TRAJ       = "#D97706"  # camera trajectory line (amber-600)
C_CAM_MARKER = "#92400E"  # camera sample markers  (amber-800)
C_FILT       = "#15803D"  # filter boundary (green-700)

# ── interpretations per layer (filled at runtime) ────────────────────────────
LAYER_DESC = [
    ("바닥 아래 (하부 공간)",           "씬 하한 부근. 거의 비어 있음.",                           "#EEF2FF"),
    ("바닥면 부근",                      "바닥 슬라브 / 하부 구조물 시작.",                         "#EEF2FF"),
    ("바닥 / 하부 벽",                   "바닥 + 하부 벽. 밀도 높음 — 씬 핵심 구조.",              "#EFF6FF"),
    ("카메라 눈높이 아래",               "카메라 통과 높이 직하. 가장 잘 보이는 표면.",             "#EFF6FF"),
    ("카메라 눈높이 위",                 "카메라 통과 높이 직상. 동일하게 촘촘.",                   "#F0FDF4"),
    ("상부 벽 / 천장",                   "천장 + 상부 벽. 밀도 여전히 충분.",                      "#F0FDF4"),
    ("천장 위 — sparse support 부족",   "sparse 급감. Pop 2 floater 형성 시작 구간.",              "#FFF7ED"),
    ("Pop 2 floater 위험 구간",          "sparse point 거의 없음. densification floater 생성 위험.", "#FFF1F2"),
]

DATA_ROOT = "/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253"
PLY_PATH  = DATA_ROOT + "/sparse/0/points3D.ply"
IMG_PATH  = DATA_ROOT + "/sparse/0/images.txt"


def _qvec2rotmat(qvec):
    w, x, y, z = qvec
    return np.array([
        [1-2*y*y-2*z*z, 2*x*y-2*w*z,   2*x*z+2*w*y],
        [2*x*y+2*w*z,   1-2*x*x-2*z*z, 2*y*z-2*w*x],
        [2*x*z-2*w*y,   2*y*z+2*w*x,   1-2*x*x-2*y*y],
    ])


def load_data():
    from plyfile import PlyData
    ply  = PlyData.read(PLY_PATH)
    pts  = np.stack([ply["vertex"]["x"], ply["vertex"]["y"], ply["vertex"]["z"]], axis=1).astype(np.float32)
    cams = []
    with open(IMG_PATH) as f:
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
    return pts, np.array(cams, dtype=np.float32)


def filter_bounds(cams, expand=1.0):
    lo = cams.min(0) - np.maximum((cams.max(0) - cams.min(0)) * expand, [2., 2., 3.])
    hi = cams.max(0) + np.maximum((cams.max(0) - cams.min(0)) * expand, [2., 2., 3.])
    return lo, hi


def density_colors(xy, xmin, xmax, ymin, ymax, bins=100):
    """Return per-point density value (normalised 0-1)."""
    H, xe, ye = np.histogram2d(xy[:, 0], xy[:, 1],
                                bins=bins,
                                range=[[xmin, xmax], [ymin, ymax]])
    xi = np.clip(np.searchsorted(xe, xy[:, 0]) - 1, 0, H.shape[0] - 1)
    yi = np.clip(np.searchsorted(ye, xy[:, 1]) - 1, 0, H.shape[1] - 1)
    d  = H[xi, yi].astype(float)
    vmax = np.percentile(d, 97) if d.max() > 0 else 1.
    return np.clip(d / vmax, 0, 1)


def make_layer_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list(
        "sparse_density", [C_SPARSE_LO, C_SPARSE_HI])


def draw_legend(fig, ax_bottom):
    """Draw a 4-item legend below the axes."""
    legend_items = [
        (mpatches.Patch(facecolor=C_SPARSE_HI, edgecolor="none"),
         "SLAM 삼각화 성공 sparse point",
         "밀도 높을수록 진한 파란색 / 낮을수록 연한 파란색"),
        (mpatches.Patch(facecolor=C_OUTLIER, edgecolor="none"),
         "SLAM 삼각화 실패 outlier (제거됨)",
         "Z가 수백~수만m인 이상치 → init_pcd_filter로 제거. XY 투영 시 씬 위에 겹쳐 보임"),
        (mlines.Line2D([], [], color=C_TRAJ, lw=2.5),
         "카메라 이동 경로",
         "1,311장의 카메라가 이 경로를 따라 이동. 삼각형 = 30프레임마다 샘플"),
        (mpatches.FancyBboxPatch((0, 0), 1, 1,
                                  boxstyle="square,pad=0", linewidth=2,
                                  edgecolor=C_FILT, facecolor="none"),
         "init_pcd_filter 경계",
         "카메라 extent × expand=1.0 + 최소 margin(XY 2m, Z 3m). 이 밖의 점은 학습 전 제거."),
    ]

    x_starts = [0.03, 0.28, 0.55, 0.77]
    y_icon, y_title, y_desc = 0.62, 0.46, 0.22

    fig.text(0.5, 0.90, "범례 / Legend",
             transform=ax_bottom.transAxes,
             ha="center", va="top",
             fontsize=10, fontweight="bold", color=C_INK)

    for i, (icon, title, desc) in enumerate(legend_items):
        x = x_starts[i]
        # icon swatch
        icon_ax = fig.add_axes([x, 0.055, 0.018, 0.04])
        if isinstance(icon, mlines.Line2D):
            icon_ax.plot([0, 1], [0.5, 0.5], color=C_TRAJ, lw=3)
            icon_ax.scatter([0.5], [0.5], s=80, marker="^",
                             color=C_CAM_MARKER, zorder=5)
        elif isinstance(icon, mpatches.FancyBboxPatch):
            icon_ax.add_patch(mpatches.FancyBboxPatch(
                (0.1, 0.1), 0.8, 0.8,
                boxstyle="square,pad=0", linewidth=2.5,
                edgecolor=C_FILT, facecolor="none"))
        else:
            icon_ax.add_patch(mpatches.Patch(
                facecolor=icon.get_facecolor(), edgecolor="none"))
        icon_ax.set_xlim(0, 1); icon_ax.set_ylim(0, 1)
        icon_ax.axis("off")

        fig.text(x + 0.025, 0.092, title,
                 fontsize=8.5, fontweight="bold", color=C_INK, va="top")
        fig.text(x + 0.025, 0.074, desc,
                 fontsize=7.5, color="#555", va="top",
                 wrap=True)


def one_layer_page(pdf, pts_in, pts_out, cams, filt_lo, filt_hi,
                   z_lo, z_hi, layer_idx, n_total,
                   xmin, xmax, ymin, ymax, cmap):

    label, interp, bg = LAYER_DESC[layer_idx]
    slab = pts_in[(pts_in[:, 2] >= z_lo) & (pts_in[:, 2] < z_hi)]
    n    = len(slab)
    pct  = 100 * n / n_total

    # ── figure layout ────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(13, 9.5), facecolor="white")

    # Header bar
    header_ax = fig.add_axes([0, 0.88, 1, 0.12])
    header_ax.set_facecolor(bg)
    header_ax.axis("off")
    header_ax.text(0.5, 0.72,
                   f"Layer {layer_idx+1} / 8   —   Z ∈ [{z_lo:.2f}, {z_hi:.2f}) m",
                   ha="center", va="center",
                   fontsize=15, fontweight="bold", color=C_INK)
    header_ax.text(0.5, 0.30,
                   f"{label}   |   {n:,} pts ({pct:.1f}% of in-filter total)",
                   ha="center", va="center",
                   fontsize=11, color="#444")
    header_ax.text(0.5, 0.08, interp,
                   ha="center", va="center",
                   fontsize=9.5, color="#666", style="italic")

    # Main scatter axes
    ax = fig.add_axes([0.07, 0.20, 0.88, 0.67])
    ax.set_facecolor(C_SURFACE)
    ax.set_aspect("equal")
    ax.grid(True, color=C_GRID, linewidth=0.6, zorder=0)

    # ── SLAM outliers (context, sub-sampled 1:15) ────────────────────────────
    sub_out = pts_out[::15]
    ax.scatter(sub_out[:, 0], sub_out[:, 1],
               c=C_OUTLIER, s=3, alpha=0.35,
               linewidths=0, rasterized=True, zorder=1,
               label="SLAM 삼각화 실패 outlier (제거됨)")

    # ── in-layer sparse points coloured by density ───────────────────────────
    if n > 0:
        d = density_colors(slab[:, :2], xmin, xmax, ymin, ymax)
        colors = cmap(d)
        ax.scatter(slab[:, 0], slab[:, 1],
                   c=colors, s=2.5, alpha=0.85,
                   linewidths=0, rasterized=True, zorder=2)

    # ── camera trajectory ────────────────────────────────────────────────────
    ax.plot(cams[:, 0], cams[:, 1],
            color=C_TRAJ, lw=1.6, alpha=0.9, zorder=4)
    ax.scatter(cams[::30, 0], cams[::30, 1],
               c=C_CAM_MARKER, s=28, marker="^",
               linewidths=0, zorder=5)

    # ── filter boundary ──────────────────────────────────────────────────────
    rect = mpatches.FancyBboxPatch(
        (filt_lo[0], filt_lo[1]),
        filt_hi[0] - filt_lo[0], filt_hi[1] - filt_lo[1],
        boxstyle="square,pad=0", linewidth=2,
        edgecolor=C_FILT, facecolor="none", zorder=6)
    ax.add_patch(rect)

    # ── axes labels & limits ─────────────────────────────────────────────────
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("X  (m) — 카메라 이동 방향 (depth axis)", fontsize=10, color=C_INK)
    ax.set_ylabel("Y  (m) — 좌우 방향", fontsize=10, color=C_INK)
    ax.tick_params(colors="#666", labelsize=8)
    for sp in ax.spines.values():
        sp.set_edgecolor(C_GRID)

    # ── inline call-outs ─────────────────────────────────────────────────────
    # Point to the outlier cloud
    ax.annotate(
        "SLAM outlier\n(XY 투영으로 씬 위에 겹쳐 보이지만\n실제 Z는 수백~수만m)",
        xy=(xmin + 1.5, ymax - 1.0),
        xytext=(xmin + 5, ymax - 0.3),
        fontsize=7.5, color="#B91C1C",
        arrowprops=dict(arrowstyle="->", color="#B91C1C", lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FEF2F2",
                  edgecolor="#FECACA", alpha=0.9))

    # Point to the filter boundary
    ax.annotate(
        "init_pcd_filter 경계\n(이 밖 → 제거)",
        xy=(filt_lo[0], 0.0),
        xytext=(filt_lo[0] + 2.5, -2.0),
        fontsize=7.5, color=C_FILT,
        arrowprops=dict(arrowstyle="->", color=C_FILT, lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#F0FDF4",
                  edgecolor="#BBF7D0", alpha=0.9))

    # Point to the trajectory
    mid_idx = len(cams) // 2
    ax.annotate(
        f"카메라 경로\n(1,311 frames  △=30f마다)",
        xy=(cams[mid_idx, 0], cams[mid_idx, 1]),
        xytext=(cams[mid_idx, 0] + 3.0, cams[mid_idx, 1] - 1.8),
        fontsize=7.5, color=C_TRAJ,
        arrowprops=dict(arrowstyle="->", color=C_TRAJ, lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFFBEB",
                  edgecolor="#FDE68A", alpha=0.9))

    # Dense cluster annotation (only if enough points)
    if n > 5000:
        peak_x = float(np.median(slab[:, 0]))
        peak_y = float(np.median(slab[:, 1]))
        ax.annotate(
            f"삼각화 성공 sparse pts\n(진한 파란색 = 밀도 높음)\nn = {n:,}",
            xy=(peak_x, peak_y),
            xytext=(peak_x + 4.0, peak_y + 2.5),
            fontsize=7.5, color=C_SPARSE_HI,
            arrowprops=dict(arrowstyle="->", color=C_SPARSE_HI, lw=1.2),
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#EFF6FF",
                      edgecolor="#BFDBFE", alpha=0.9))

    # ── colorbar for density ─────────────────────────────────────────────────
    from matplotlib.cm import ScalarMappable
    from matplotlib.colors import Normalize
    sm = ScalarMappable(cmap=cmap, norm=Normalize(0, 1))
    sm.set_array([])
    cbar_ax = fig.add_axes([0.965, 0.20, 0.012, 0.67])
    cb = fig.colorbar(sm, cax=cbar_ax)
    cb.set_label("로컬 밀도 (높을수록 진함)", fontsize=8, color=C_INK)
    cb.ax.tick_params(labelsize=7, colors="#666")
    cb.ax.yaxis.set_ticks([0, 0.5, 1])
    cb.ax.yaxis.set_ticklabels(["낮음", "중간", "높음"])

    # ── legend panel ─────────────────────────────────────────────────────────
    legend_ax = fig.add_axes([0.07, 0.00, 0.88, 0.18])
    legend_ax.set_facecolor("#F8FAFC")
    legend_ax.axis("off")

    legend_defs = [
        (C_SPARSE_HI,  "●", "삼각화 성공 sparse point",
         "SLAM이 삼각화에 성공한 3D 특징점. 색이 진할수록 그 XY 위치에 점이 많음 (고밀도)."),
        (C_OUTLIER,    "●", "삼각화 실패 outlier (제거됨)",
         "SLAM 삼각화 실패로 Z가 수백~수만m인 이상치. init_pcd_filter가 학습 전 제거함.\n"
         "XY로 투영하면 씬 위에 겹쳐 보이지만, 실제로는 씬과 무관한 위치에 있음."),
        (C_TRAJ,       "▶", "카메라 이동 경로",
         "1,311장의 연속 프레임 카메라가 이 선을 따라 이동. "
         "삼각형(△)은 30 프레임마다 위치 표시."),
        (C_FILT,       "□", "필터 경계",
         "카메라 trajectory extent × expand_factor=1.0 으로 계산한 3D bounding box.\n"
         "이 경계 밖의 sparse point는 3DGS 초기화 전에 제거됨 (init_pcd_filter=true)."),
    ]

    xs = [0.01, 0.26, 0.52, 0.76]
    for i, (color, mark, name, desc) in enumerate(legend_defs):
        x = xs[i]
        legend_ax.text(x, 0.88, f"{mark}  {name}",
                       fontsize=8.5, fontweight="bold", color=color,
                       transform=legend_ax.transAxes, va="top")
        legend_ax.text(x, 0.68, desc,
                       fontsize=7.2, color="#444",
                       transform=legend_ax.transAxes, va="top",
                       wrap=True)

    pdf.savefig(fig, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  layer {layer_idx+1}: Z[{z_lo:.2f},{z_hi:.2f})  n={n:,} ({pct:.1f}%)")


def cover_page(pdf, n_total, n_outlier, n_cams, filt_lo, filt_hi, z_edges):
    fig = plt.figure(figsize=(13, 9.5), facecolor="white")
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("white"); ax.axis("off")

    # title block
    ax.text(0.5, 0.82, "301-1253 Sparse Point Cloud", ha="center",
            fontsize=24, fontweight="bold", color=C_INK)
    ax.text(0.5, 0.74, "Z축 단면 분석  —  XY 평면, Z별 슬라이드", ha="center",
            fontsize=16, color="#555")

    # stats grid
    stats = [
        ("Sparse points 총계",   f"{n_total + n_outlier:,}"),
        ("In-filter (92.6%)",    f"{n_total:,}"),
        ("SLAM outliers (7.4%)", f"{n_outlier:,}"),
        ("카메라 수",             f"{n_cams:,}"),
        ("필터 Z 범위",           f"[{filt_lo[2]:.2f}, {filt_hi[2]:.2f}] m"),
        ("필터 X 범위",           f"[{filt_lo[0]:.1f}, {filt_hi[0]:.1f}] m"),
        ("레이어 수",             "8  (각 ≈ 0.76 m)"),
    ]
    y0 = 0.62
    for label, val in stats:
        ax.text(0.35, y0, label, ha="right", fontsize=12, color="#666")
        ax.text(0.37, y0, val,   ha="left",  fontsize=12, color=C_INK, fontweight="bold")
        y0 -= 0.055

    # layer table
    ax.text(0.5, 0.21, "레이어 구성", ha="center", fontsize=11,
            fontweight="bold", color=C_INK)
    cols = ["Layer", "Z 범위 (m)", "해석", "n (pts)"]
    col_x = [0.07, 0.17, 0.37, 0.76]
    ax.text(col_x[0], 0.17, cols[0], fontsize=8.5, fontweight="bold", color=C_INK)
    ax.text(col_x[1], 0.17, cols[1], fontsize=8.5, fontweight="bold", color=C_INK)
    ax.text(col_x[2], 0.17, cols[2], fontsize=8.5, fontweight="bold", color=C_INK)
    ax.text(col_x[3], 0.17, cols[3], fontsize=8.5, fontweight="bold", color=C_INK)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root",   default="results/diagnostic")
    parser.add_argument("--n-z-slabs",     type=int,   default=8)
    parser.add_argument("--filter-expand", type=float, default=1.0)
    args = parser.parse_args()

    root    = Path(args.output_root)
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = root / f"real_zlayers_v2_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[load] data …")
    pts3d, cams3d = load_data()
    filt_lo, filt_hi = filter_bounds(cams3d, args.filter_expand)

    valid = (
        (pts3d[:, 0] >= filt_lo[0]) & (pts3d[:, 0] <= filt_hi[0]) &
        (pts3d[:, 1] >= filt_lo[1]) & (pts3d[:, 1] <= filt_hi[1]) &
        (pts3d[:, 2] >= filt_lo[2]) & (pts3d[:, 2] <= filt_hi[2])
    )
    pts_in  = pts3d[valid]
    pts_out = pts3d[~valid]

    z_edges = np.linspace(float(filt_lo[2]), float(filt_hi[2]), args.n_z_slabs + 1)
    pad = 0.8
    xmin = float(pts_in[:, 0].min()) - pad
    xmax = float(pts_in[:, 0].max()) + pad
    ymin = float(pts_in[:, 1].min()) - pad
    ymax = float(pts_in[:, 1].max()) + pad

    cmap = make_layer_cmap()
    pdf_path = out_dir / "zlayer_annotated.pdf"

    print(f"[render] {args.n_z_slabs} layers → {pdf_path}")
    with PdfPages(pdf_path) as pdf:
        cover_page(pdf, len(pts_in), len(pts_out), len(cams3d),
                   filt_lo, filt_hi, z_edges)

        for i in range(args.n_z_slabs):
            one_layer_page(
                pdf, pts_in, pts_out, cams3d,
                filt_lo, filt_hi,
                z_edges[i], z_edges[i + 1],
                i, len(pts_in),
                xmin, xmax, ymin, ymax, cmap,
            )

    print(f"\n[done] → {pdf_path}")


if __name__ == "__main__":
    main()
