#!/usr/bin/env python3
"""XY top-down view sliced by Z layers — real 301-1253 sparse point cloud.

Generates:
  - Small-multiples grid: one XY panel per Z slab
  - Full PDF bundling all diagnostic figures
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from scipy.spatial import cKDTree

# ── palette ──────────────────────────────────────────────────────────────────
# Sequential single-hue (blue) for in-layer density
# Fixed accent colors for trajectory / filter / outliers
C_TRAJ   = "#FFFFFF"   # camera trajectory
C_FILT   = "#00E5FF"   # filter boundary
C_OUT    = "#FF5252"   # SLAM outliers
C_CAM_PT = "#FFD740"   # camera sample markers
BG       = "#0D1117"   # dark background

DATA_ROOT = "/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253"
PLY_PATH  = DATA_ROOT + "/sparse/0/points3D.ply"
IMG_PATH  = DATA_ROOT + "/sparse/0/images.txt"


# ── loaders ──────────────────────────────────────────────────────────────────

def _qvec2rotmat(qvec):
    w, x, y, z = qvec
    return np.array([
        [1-2*y*y-2*z*z,  2*x*y-2*w*z,    2*x*z+2*w*y],
        [2*x*y+2*w*z,    1-2*x*x-2*z*z,  2*y*z-2*w*x],
        [2*x*z-2*w*y,    2*y*z+2*w*x,    1-2*x*x-2*y*y],
    ])


def load_sparse_points():
    from plyfile import PlyData
    ply = PlyData.read(PLY_PATH)
    pts = np.stack([ply["vertex"]["x"], ply["vertex"]["y"], ply["vertex"]["z"]], axis=1)
    return pts.astype(np.float32)


def load_camera_centers():
    centers = []
    with open(IMG_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 9:
                continue
            try:
                q = np.array([float(parts[i]) for i in range(1, 5)])
                t = np.array([float(parts[i]) for i in range(5, 8)])
            except ValueError:
                continue
            C = -np.transpose(_qvec2rotmat(q)) @ t
            centers.append(C)
    return np.array(centers, dtype=np.float32)


def filter_bounds(cams3d, expand=1.0):
    cam_min, cam_max = cams3d.min(0), cams3d.max(0)
    margin = np.maximum((cam_max - cam_min) * expand, [2.0, 2.0, 3.0])
    return cam_min - margin, cam_max + margin


# ── Z-layer small multiples ───────────────────────────────────────────────────

def draw_xy_zlayers(pts3d, cams3d, filt_lo, filt_hi, pdf, out_dir,
                    z_edges, xy_lim, n_cols=4):
    """One XY scatter panel per Z slab."""
    n_slabs = len(z_edges) - 1
    n_rows  = (n_slabs + n_cols - 1) // n_cols

    # SLAM outlier XY positions (projected — shown in all panels as context)
    valid_mask = (
        (pts3d[:,0] >= filt_lo[0]) & (pts3d[:,0] <= filt_hi[0]) &
        (pts3d[:,1] >= filt_lo[1]) & (pts3d[:,1] <= filt_hi[1]) &
        (pts3d[:,2] >= filt_lo[2]) & (pts3d[:,2] <= filt_hi[2])
    )
    pts_in  = pts3d[valid_mask]
    pts_out = pts3d[~valid_mask]

    xmin, xmax, ymin, ymax = xy_lim

    fig, axes = plt.subplots(n_rows, n_cols,
                             figsize=(n_cols * 4.5, n_rows * 3.2),
                             facecolor=BG)
    fig.suptitle("XY top-down: sparse points sliced by Z layer\n"
                 f"(in-filter: {len(pts_in):,} pts | SLAM outliers: {len(pts_out):,} pts shown as context)",
                 color="white", fontsize=11, y=1.01)

    ax_flat = axes.ravel()

    for i in range(n_slabs):
        z_lo, z_hi = z_edges[i], z_edges[i + 1]
        ax = ax_flat[i]
        ax.set_facecolor(BG)

        # Points in this Z slab
        slab_mask = (pts_in[:,2] >= z_lo) & (pts_in[:,2] < z_hi)
        slab_pts  = pts_in[slab_mask]
        n_slab    = len(slab_pts)

        # Density coloring via 2D histogram → each point gets a density value
        if n_slab > 0:
            H, xe, ye = np.histogram2d(slab_pts[:,0], slab_pts[:,1],
                                       bins=80, range=[[xmin, xmax], [ymin, ymax]])
            # Assign density to each point via nearest bin
            xi = np.clip(np.searchsorted(xe, slab_pts[:,0]) - 1, 0, H.shape[0]-1)
            yi = np.clip(np.searchsorted(ye, slab_pts[:,1]) - 1, 0, H.shape[1]-1)
            density = H[xi, yi]
            vmax = np.percentile(density, 97) if density.max() > 0 else 1.0

            sc = ax.scatter(slab_pts[:,0], slab_pts[:,1],
                            c=density, cmap="Blues", vmin=0, vmax=vmax,
                            s=1.5, alpha=0.85, rasterized=True, linewidths=0)
        else:
            ax.text(0.5, 0.5, "no points", transform=ax.transAxes,
                    ha="center", va="center", color="#888", fontsize=8)

        # SLAM outliers as faint context (XY projection, sub-sampled)
        ax.scatter(pts_out[::8, 0], pts_out[::8, 1],
                   c=C_OUT, s=0.8, alpha=0.12, rasterized=True, linewidths=0)

        # Camera trajectory
        ax.plot(cams3d[:,0], cams3d[:,1], color=C_TRAJ, lw=0.8, alpha=0.7, zorder=4)
        ax.scatter(cams3d[::30, 0], cams3d[::30, 1],
                   c=C_CAM_PT, s=8, marker="^", zorder=5, linewidths=0)

        # Filter boundary rectangle
        rect = mpatches.FancyBboxPatch(
            (filt_lo[0], filt_lo[1]),
            filt_hi[0]-filt_lo[0], filt_hi[1]-filt_lo[1],
            boxstyle="square,pad=0", linewidth=1.2,
            edgecolor=C_FILT, facecolor="none", zorder=6
        )
        ax.add_patch(rect)

        z_mid = 0.5*(z_lo + z_hi)
        ax.set_title(f"Z ∈ [{z_lo:.2f}, {z_hi:.2f}) m   n={n_slab:,}",
                     color="white", fontsize=8.5, pad=3)
        ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
        ax.set_aspect("equal")
        ax.tick_params(colors="#888", labelsize=6)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333")
        if i % n_cols == 0:
            ax.set_ylabel("Y (m)", color="#888", fontsize=7)
        if i >= (n_rows - 1) * n_cols:
            ax.set_xlabel("X (m)", color="#888", fontsize=7)

    # Hide unused panels
    for j in range(n_slabs, len(ax_flat)):
        ax_flat[j].set_visible(False)

    # Legend
    handles = [
        mpatches.Patch(color="#6EA8FF", label="in-filter sparse pts (color = local density)"),
        mpatches.Patch(color=C_OUT,     alpha=0.4, label="SLAM outliers (context, sub-sampled)"),
        plt.Line2D([0],[0], color=C_TRAJ, lw=1.5, label="camera trajectory"),
        mpatches.Patch(facecolor="none", edgecolor=C_FILT, lw=1.2, label="init_pcd_filter boundary"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4,
               facecolor=BG, edgecolor="#333",
               labelcolor="white", fontsize=8,
               bbox_to_anchor=(0.5, -0.03))

    fig.tight_layout(rect=[0, 0.04, 1, 1])

    png_path = out_dir / "xy_zlayers.png"
    fig.savefig(png_path, dpi=160, bbox_inches="tight", facecolor=BG)
    pdf.savefig(fig, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved xy_zlayers.png")
    return str(png_path)


# ── helper: attach existing PNGs to PDF ───────────────────────────────────────

def png_to_pdf_page(pdf, png_path, title=""):
    """Add an existing PNG as a full-page PDF page."""
    from PIL import Image as PILImage
    img = PILImage.open(png_path)
    w, h = img.size
    # A4 landscape in inches
    fig_w, fig_h = 11.69, 8.27
    fig = plt.figure(figsize=(fig_w, fig_h), facecolor=BG)
    ax  = fig.add_axes([0, 0.04, 1, 0.93])
    ax.imshow(np.array(img))
    ax.axis("off")
    ax.set_facecolor(BG)
    if title:
        fig.text(0.5, 0.01, title, ha="center", va="bottom",
                 color="#888", fontsize=9)
    pdf.savefig(fig, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close(fig)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root",   default="results/diagnostic")
    parser.add_argument("--n-z-slabs",     type=int,   default=8)
    parser.add_argument("--filter-expand", type=float, default=1.0)
    parser.add_argument("--prev-run",      default="",
                        help="Path to previous real_sparse_support_XXXXXX dir to include in PDF")
    args = parser.parse_args()

    root   = Path(args.output_root)
    ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = root / f"real_zlayers_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[load] sparse points …")
    pts3d  = load_sparse_points()
    print(f"  {len(pts3d):,} total  Z=[{pts3d[:,2].min():.1f}, {pts3d[:,2].max():.1f}]")

    print("[load] camera centers …")
    cams3d = load_camera_centers()
    filt_lo, filt_hi = filter_bounds(cams3d, args.filter_expand)
    print(f"  {len(cams3d)} cameras  filter Z=[{filt_lo[2]:.2f}, {filt_hi[2]:.2f}]")

    # Z edges: evenly split the in-filter Z range
    z_lo_v = float(filt_lo[2])
    z_hi_v = float(filt_hi[2])
    z_edges = np.linspace(z_lo_v, z_hi_v, args.n_z_slabs + 1)

    # XY display bounds: use in-filter X/Y extent + small margin
    valid = (
        (pts3d[:,0] >= filt_lo[0]) & (pts3d[:,0] <= filt_hi[0]) &
        (pts3d[:,1] >= filt_lo[1]) & (pts3d[:,1] <= filt_hi[1]) &
        (pts3d[:,2] >= filt_lo[2]) & (pts3d[:,2] <= filt_hi[2])
    )
    pts_in = pts3d[valid]
    pad = 1.0
    xy_lim = (pts_in[:,0].min()-pad, pts_in[:,0].max()+pad,
              pts_in[:,1].min()-pad, pts_in[:,1].max()+pad)

    print(f"[zlayers] Z edge list: {np.round(z_edges, 2).tolist()}")

    pdf_path = out_dir / "sparse_point_diagnostic.pdf"

    with PdfPages(pdf_path) as pdf:
        # ── cover page ────────────────────────────────────────────────────
        fig = plt.figure(figsize=(11.69, 8.27), facecolor=BG)
        fig.text(0.5, 0.62, "301-1253 Sparse Point Cloud Diagnostic",
                 ha="center", va="center", color="white", fontsize=20, fontweight="bold")
        fig.text(0.5, 0.52, "SLAM init outlier filtering + Z-layer analysis + potential field",
                 ha="center", va="center", color="#AAA", fontsize=13)
        fig.text(0.5, 0.42, f"Generated: {ts}  |  total pts: {len(pts3d):,}  |  cameras: {len(cams3d)}",
                 ha="center", va="center", color="#666", fontsize=10)

        rows = [
            ("Sparse points total",            f"{len(pts3d):,}"),
            ("In-filter (92.6%)",               f"{valid.sum():,}"),
            ("SLAM outliers removed (7.4%)",    f"{(~valid).sum():,}"),
            ("Camera count",                    f"{len(cams3d)}"),
            ("Filter Z bounds",                 f"[{filt_lo[2]:.2f}, {filt_hi[2]:.2f}] m"),
            ("Filter X bounds",                 f"[{filt_lo[0]:.1f}, {filt_hi[0]:.1f}] m"),
            ("Z slabs",                         f"{args.n_z_slabs}  (Δ={z_hi_v-z_lo_v:.2f}/{args.n_z_slabs:.0f} = {(z_hi_v-z_lo_v)/args.n_z_slabs:.2f} m each)"),
        ]
        y0 = 0.34
        for label, val in rows:
            fig.text(0.32, y0, label, ha="right", color="#888", fontsize=10)
            fig.text(0.34, y0, val,   ha="left",  color="white", fontsize=10)
            y0 -= 0.04

        pdf.savefig(fig, facecolor=BG)
        plt.close(fig)

        # ── Z-layer small multiples ───────────────────────────────────────
        print("[fig] Z-layer small multiples …")
        draw_xy_zlayers(pts3d, cams3d, filt_lo, filt_hi,
                        pdf, out_dir, z_edges, xy_lim, n_cols=4)

        # ── attach previous run figures if provided ───────────────────────
        prev = Path(args.prev_run) if args.prev_run else None
        if prev and prev.exists():
            ordered = [
                ("01_xy_overview.png",        "Fig: XY overview (all-Z collapsed, SLAM outliers highlighted)"),
                ("02_xz_normalized_distance.png", "Fig: XZ cross-section — normalised distance D(x)"),
                ("03_xz_potential_force.png", "Fig: XZ — Huber potential ρ(x) + force vectors"),
                ("04_xz_gaussian_dynamics.png","Fig: XZ — Gaussian center dynamics under potential"),
                ("05_tau_distribution.png",   "Fig: Local spacing h_j and plateau radius tau_j"),
                ("06_xz_ray_vs_potential.png","Fig: XZ — ray coverage vs support plateau vs risk zone"),
            ]
            print(f"[pdf] attaching {len(ordered)} figures from {prev.name} …")
            for fname, title in ordered:
                p = prev / fname
                if p.exists():
                    png_to_pdf_page(pdf, p, title=title)
                    print(f"  + {fname}")

        # ── summary JSON ─────────────────────────────────────────────────
        summary = {
            "output_dir": str(out_dir),
            "pdf": str(pdf_path),
            "data": {
                "sparse_points_total":     int(len(pts3d)),
                "in_filter":               int(valid.sum()),
                "slam_outliers_removed":   int((~valid).sum()),
                "camera_count":            int(len(cams3d)),
            },
            "filter_bounds": {
                "X": [float(filt_lo[0]), float(filt_hi[0])],
                "Y": [float(filt_lo[1]), float(filt_hi[1])],
                "Z": [float(filt_lo[2]), float(filt_hi[2])],
            },
            "z_slabs": {
                "n":     args.n_z_slabs,
                "edges": z_edges.round(3).tolist(),
                "width_m": float((z_hi_v - z_lo_v) / args.n_z_slabs),
            },
        }
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print(f"\n[done] PDF → {pdf_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
