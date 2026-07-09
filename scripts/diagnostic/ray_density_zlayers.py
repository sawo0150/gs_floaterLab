#!/usr/bin/env python3
"""Photometric ray density per Z layer — 301-1253 scene.

For each Z slab, traces camera pixel rays (not sparse-point rays) and
accumulates where they intersect the slab in XY.  This shows where
photometric loss actually acts — high density = strong gradient,
low density = floater habitat.

500 cameras × downsampled pixel grid → XY histogram per Z slab.
"""

from __future__ import annotations

import argparse
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

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LogNorm

# ── palette ───────────────────────────────────────────────────────────────────
C_TRAJ    = "#D97706"   # camera trajectory (amber)
C_CAM_PT  = "#92400E"   # camera sample markers
C_FILT    = "#15803D"   # filter boundary
C_INK     = "#1A202C"

# Ray density: warm sequential (white → orange → dark red)
RAY_CMAP  = "YlOrRd"

DATA_ROOT = "/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253"
IMG_PATH  = DATA_ROOT + "/sparse/0/images.txt"

# Camera: PINHOLE 1024×1024, fx=fy=500, cx=cy=511.5
IMG_W, IMG_H = 1024, 1024
FX, FY       = 500.0, 500.0
CX, CY       = 511.5, 511.5

LAYER_DESC = [
    ("바닥 아래",                    "씬 하한. 카메라 ray가 거의 도달하지 않음."),
    ("바닥면 부근",                   "바닥 슬라브. 아래 방향 ray만 통과."),
    ("바닥 / 하부 벽",               "씬 핵심 구조. photometric loss 집중."),
    ("카메라 눈높이 아래",            "가장 많은 ray가 통과. loss gradient 최강."),
    ("카메라 눈높이 위",              "동일하게 ray 밀집. 씬 핵심."),
    ("상부 벽 / 천장",               "위쪽 방향 ray가 통과. 여전히 충분."),
    ("천장 위 — ray 급감 시작",      "ray density 급감. gradient 약해짐."),
    ("Pop 2 floater 위험 구간",      "ray 거의 없음. photometric gradient ~0 → floater 고착 위험."),
]


def _qvec2rotmat(qvec):
    w, x, y, z = qvec
    return np.array([
        [1-2*y*y-2*z*z, 2*x*y-2*w*z,   2*x*z+2*w*y],
        [2*x*y+2*w*z,   1-2*x*x-2*z*z, 2*y*z-2*w*x],
        [2*x*z-2*w*y,   2*y*z+2*w*x,   1-2*x*x-2*y*y],
    ])


def load_cameras(n_sample: int):
    """Load camera poses, subsample to n_sample."""
    centers, rotmats = [], []
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
            R = np.transpose(_qvec2rotmat(q))   # R_cam2world
            C = -R @ t
            centers.append(C)
            rotmats.append(R)

    centers  = np.array(centers,  dtype=np.float32)
    rotmats  = np.array(rotmats,  dtype=np.float32)

    # Regular subsample
    step     = max(1, len(centers) // n_sample)
    idx      = np.arange(0, len(centers), step)[:n_sample]
    return centers[idx], rotmats[idx]


def filter_bounds(cams, expand=1.0):
    lo = cams.min(0) - np.maximum((cams.max(0) - cams.min(0)) * expand, [2., 2., 3.])
    hi = cams.max(0) + np.maximum((cams.max(0) - cams.min(0)) * expand, [2., 2., 3.])
    return lo, hi


def build_ray_directions(px_step: int):
    """Build pixel ray directions in camera space (unit Z=1 plane).
    Returns array of shape [N_rays, 3] in camera coords.
    """
    us = np.arange(px_step // 2, IMG_W, px_step, dtype=np.float32)
    vs = np.arange(px_step // 2, IMG_H, px_step, dtype=np.float32)
    uu, vv = np.meshgrid(us, vs)
    dx = (uu.ravel() - CX) / FX
    dy = (vv.ravel() - CY) / FY
    dz = np.ones_like(dx)
    dirs = np.stack([dx, dy, dz], axis=1)   # [N_rays, 3] in camera space
    norms = np.linalg.norm(dirs, axis=1, keepdims=True)
    return (dirs / norms).astype(np.float32)


def compute_ray_density(centers, rotmats, ray_dirs_cam, z_edges, xmin, xmax, ymin, ymax, bins):
    """For each Z slab, accumulate XY intersections of photometric rays.

    centers:      [N_cam, 3]
    rotmats:      [N_cam, 3, 3]  R_cam2world
    ray_dirs_cam: [N_ray, 3]  in camera space (unit vectors)
    z_edges:      [n_slabs+1]
    Returns list of [bins, bins] histograms.
    """
    n_slabs = len(z_edges) - 1
    hists   = [np.zeros((bins, bins), dtype=np.float64) for _ in range(n_slabs)]

    xe = np.linspace(xmin, xmax, bins + 1)
    ye = np.linspace(ymin, ymax, bins + 1)
    dx_bin = (xmax - xmin) / bins
    dy_bin = (ymax - ymin) / bins

    n_cam, n_ray = len(centers), len(ray_dirs_cam)
    print(f"  {n_cam} cameras × {n_ray} rays/cam = {n_cam*n_ray:,} total rays")

    for ci, (C, R) in enumerate(zip(centers, rotmats)):
        if ci % 50 == 0:
            print(f"  cam {ci}/{n_cam} …")

        # Transform ray directions to world space: [N_ray, 3]
        dirs_world = (R @ ray_dirs_cam.T).T   # [N_ray, 3]

        Cz = float(C[2])
        dz = dirs_world[:, 2]   # [N_ray]

        for s in range(n_slabs):
            z_lo, z_hi = float(z_edges[s]), float(z_edges[s + 1])

            # t where ray hits z_lo and z_hi
            with np.errstate(divide="ignore", invalid="ignore"):
                t_lo = np.where(np.abs(dz) > 1e-9, (z_lo - Cz) / dz, np.where(Cz >= z_lo, 0., np.inf))
                t_hi = np.where(np.abs(dz) > 1e-9, (z_hi - Cz) / dz, np.where(Cz < z_hi, np.inf, -np.inf))

            t_enter = np.minimum(t_lo, t_hi)
            t_exit  = np.maximum(t_lo, t_hi)

            # Only keep rays going forward (t > 0) and into a plausible range
            t_enter = np.maximum(t_enter, 0.)
            t_exit  = np.minimum(t_exit,  50.)   # max 50m from camera

            valid = t_enter < t_exit  # [N_ray] bool

            if not valid.any():
                continue

            # Midpoint of intersection segment
            t_mid  = 0.5 * (t_enter[valid] + t_exit[valid])
            x_mid  = C[0] + t_mid * dirs_world[valid, 0]
            y_mid  = C[1] + t_mid * dirs_world[valid, 1]

            # Bin into 2D histogram
            xi = ((x_mid - xmin) / dx_bin).astype(int)
            yi = ((y_mid - ymin) / dy_bin).astype(int)
            in_bounds = (xi >= 0) & (xi < bins) & (yi >= 0) & (yi < bins)
            np.add.at(hists[s], (yi[in_bounds], xi[in_bounds]), 1)

    return hists


def draw_layer_page(pdf, hist, cams_all, filt_lo, filt_hi,
                    z_lo, z_hi, layer_idx, xmin, xmax, ymin, ymax,
                    vmin_log, vmax_log):

    label, interp = LAYER_DESC[layer_idx]
    total_hits    = int(hist.sum())

    # Background tint by danger level
    bgs = ["#EEF2FF","#EEF2FF","#EFF6FF","#EFF6FF",
           "#F0FDF4","#F0FDF4","#FFF7ED","#FFF1F2"]
    bg  = bgs[layer_idx]

    fig = plt.figure(figsize=(13, 9.5), facecolor="white")

    # Header
    hax = fig.add_axes([0, 0.88, 1, 0.12])
    hax.set_facecolor(bg); hax.axis("off")
    hax.text(0.5, 0.72, f"Ray Density  —  Layer {layer_idx+1} / 8   Z ∈ [{z_lo:.2f}, {z_hi:.2f}) m",
             ha="center", va="center", fontsize=15, fontweight="bold", color=C_INK)
    hax.text(0.5, 0.30, f"{label}   |   총 ray 통과 횟수: {total_hits:,}",
             ha="center", va="center", fontsize=11, color="#444")
    hax.text(0.5, 0.08, interp,
             ha="center", va="center", fontsize=9.5, color="#666", style="italic")

    # Main axes
    ax = fig.add_axes([0.07, 0.20, 0.88, 0.67])
    ax.set_facecolor("#111111")
    ax.set_aspect("equal")

    # Ray density heatmap (log scale handles huge dynamic range)
    hist_plot = np.where(hist > 0, hist, np.nan)
    im = ax.imshow(
        hist_plot,
        origin="lower",
        extent=[xmin, xmax, ymin, ymax],
        cmap=RAY_CMAP,
        norm=LogNorm(vmin=max(1, vmin_log), vmax=vmax_log),
        aspect="auto",
        interpolation="bilinear",
    )

    # Camera trajectory
    ax.plot(cams_all[:, 0], cams_all[:, 1],
            color=C_TRAJ, lw=1.6, alpha=0.9, zorder=4)
    ax.scatter(cams_all[::30, 0], cams_all[::30, 1],
               c=C_CAM_PT, s=28, marker="^", linewidths=0, zorder=5)

    # Filter boundary
    rect = mpatches.FancyBboxPatch(
        (filt_lo[0], filt_lo[1]),
        filt_hi[0]-filt_lo[0], filt_hi[1]-filt_lo[1],
        boxstyle="square,pad=0", linewidth=2,
        edgecolor=C_FILT, facecolor="none", zorder=6)
    ax.add_patch(rect)

    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
    ax.set_xlabel("X  (m) — 카메라 이동 방향 (depth axis)", fontsize=10, color="white")
    ax.set_ylabel("Y  (m) — 좌우 방향",                     fontsize=10, color="white")
    ax.tick_params(colors="#AAA", labelsize=8)
    for sp in ax.spines.values(): sp.set_edgecolor("#333")

    # Callout: low-density zone
    if layer_idx >= 6:
        ax.text(0.5, 0.92,
                "⚠ 이 구간에서 ray 밀도가 낮음 → photometric gradient 약함 → floater 형성 위험",
                transform=ax.transAxes, ha="center", va="top",
                fontsize=9, color="#FCA5A5",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#1A0000", edgecolor="#7F1D1D", alpha=0.9))

    # Colorbar
    cbar_ax = fig.add_axes([0.965, 0.20, 0.012, 0.67])
    cb = fig.colorbar(im, cax=cbar_ax)
    cb.set_label("Ray 통과 횟수 (log scale)", fontsize=8, color=C_INK)
    cb.ax.tick_params(labelsize=7, colors="#444")

    # Legend panel
    leg_ax = fig.add_axes([0.07, 0.00, 0.88, 0.18])
    leg_ax.set_facecolor("#F8FAFC"); leg_ax.axis("off")

    items = [
        ("#D4270C", "■", "Ray 밀도 높음 (진한 적색)",
         "카메라 픽셀 ray가 이 XY 위치의 Z 슬랩을 많이 통과.\n"
         "photometric loss가 강하게 적용 → Gaussian gradient 충분."),
        ("#FFECC8", "■", "Ray 밀도 낮음 (연한 노란색)",
         "소수의 ray만 통과.\n"
         "photometric gradient 약함 → Gaussian이 이 구간에서 부유하기 쉬움."),
        (C_TRAJ,   "▶", "카메라 이동 경로",
         "500장 샘플 카메라의 위치. 실제 ray의 출발점.\n"
         "삼각형(△)은 30 프레임마다 표시."),
        (C_FILT,   "□", "init_pcd_filter 경계",
         "카메라 extent 기반 3D bounding box.\n"
         "이 경계 밖의 sparse point는 학습 전 제거됨."),
    ]
    xs = [0.01, 0.26, 0.52, 0.76]
    for i, (color, mark, name, desc) in enumerate(items):
        x = xs[i]
        leg_ax.text(x, 0.90, f"{mark}  {name}",
                    fontsize=8.5, fontweight="bold", color=color,
                    transform=leg_ax.transAxes, va="top")
        leg_ax.text(x, 0.68, desc,
                    fontsize=7.2, color="#444",
                    transform=leg_ax.transAxes, va="top")

    pdf.savefig(fig, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  layer {layer_idx+1}: Z[{z_lo:.2f},{z_hi:.2f})  hits={total_hits:,}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root",    default="results/diagnostic")
    parser.add_argument("--n-cameras",      type=int, default=500)
    parser.add_argument("--pixel-step",     type=int, default=20,
                        help="Sample 1 ray every px_step pixels (20 → 52×52=2704 rays/cam)")
    parser.add_argument("--n-z-slabs",      type=int, default=8)
    parser.add_argument("--bins",           type=int, default=150)
    parser.add_argument("--filter-expand",  type=float, default=1.0)
    args = parser.parse_args()

    root    = Path(args.output_root)
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = root / f"ray_density_zlayers_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[load] cameras (sample {args.n_cameras}) …")
    centers, rotmats = load_cameras(args.n_cameras)
    filt_lo, filt_hi = filter_bounds(centers)

    # XY bounds (use all cameras for filter, not just subsample)
    centers_all, _ = load_cameras(9999)
    pad = 0.8
    xmin = float(centers_all[:, 0].min()) - pad - 2
    xmax = float(centers_all[:, 0].max()) + pad + 2
    ymin = float(centers_all[:, 1].min()) - pad - 2
    ymax = float(centers_all[:, 1].max()) + pad + 2

    print(f"[rays] building pixel ray grid (step={args.pixel_step}) …")
    ray_dirs = build_ray_directions(args.pixel_step)
    print(f"  {len(ray_dirs)} rays per camera")

    z_edges = np.linspace(float(filt_lo[2]), float(filt_hi[2]), args.n_z_slabs + 1)
    print(f"[compute] {args.n_cameras} cams × {len(ray_dirs)} rays × {args.n_z_slabs} slabs …")

    hists = compute_ray_density(centers, rotmats, ray_dirs,
                                z_edges, xmin, xmax, ymin, ymax, args.bins)

    # Shared log scale across all layers for fair comparison
    all_vals = np.concatenate([h[h > 0].ravel() for h in hists if h.max() > 0])
    vmin_log = float(np.percentile(all_vals, 1))
    vmax_log = float(np.percentile(all_vals, 99.5))
    print(f"[scale] log range: {vmin_log:.0f} ~ {vmax_log:.0f}")

    pdf_path = out_dir / "ray_density_zlayers.pdf"
    print(f"[render] → {pdf_path}")
    with PdfPages(pdf_path) as pdf:
        # Cover
        fig = plt.figure(figsize=(13, 9.5), facecolor="white")
        ax  = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
        ax.text(0.5, 0.80, "Photometric Ray Density — Z Layer Analysis",
                ha="center", fontsize=22, fontweight="bold", color=C_INK)
        ax.text(0.5, 0.72, "각 Z 슬랩에서 photometric loss ray가 통과하는 XY 밀도",
                ha="center", fontsize=14, color="#555")
        stats = [
            ("카메라 수",       f"{args.n_cameras} / 1,311 (서브샘플)"),
            ("픽셀 step",       f"{args.pixel_step}px → {len(ray_dirs):,} rays/cam"),
            ("총 ray 수",       f"{args.n_cameras * len(ray_dirs):,}"),
            ("Z 슬랩 수",       f"{args.n_z_slabs}  (각 ≈ {(filt_hi[2]-filt_lo[2])/args.n_z_slabs:.2f} m)"),
            ("Z 필터 범위",     f"[{filt_lo[2]:.2f}, {filt_hi[2]:.2f}] m"),
            ("컬러 스케일",     "Log scale (공유) — 층간 비교 가능"),
        ]
        y0 = 0.62
        for lbl, val in stats:
            ax.text(0.35, y0, lbl, ha="right", fontsize=12, color="#666")
            ax.text(0.37, y0, val, ha="left",  fontsize=12, color=C_INK, fontweight="bold")
            y0 -= 0.055
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

        for i in range(args.n_z_slabs):
            draw_layer_page(pdf, hists[i], centers_all,
                            filt_lo, filt_hi,
                            z_edges[i], z_edges[i+1], i,
                            xmin, xmax, ymin, ymax,
                            vmin_log, vmax_log)

    print(f"\n[done] → {pdf_path}")


if __name__ == "__main__":
    main()
