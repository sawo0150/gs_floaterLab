#!/usr/bin/env python3
"""Sparse-support plateau potential analysis on the real 301-1253 scene.

Visualises how a sparse-support potential field would behave on the actual
COLMAP sparse point cloud and camera trajectory, replacing the synthetic toy
data used in toy_sparse_support_potential.py.

Key cross-sections:
  - XY plane (top-down):  trajectory extent, sparse point density
  - XZ plane (side view): Z-floater formation axis (camera looks in +X, floaters drift in Z)

Usage:
  conda run -n 3dgs python scripts/diagnostic/real_sparse_support_potential.py
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
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from scipy.spatial import cKDTree

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

DATA_ROOT = "/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253"
PLY_PATH  = DATA_ROOT + "/sparse/0/points3D.ply"
IMG_PATH  = DATA_ROOT + "/sparse/0/images.txt"


def _qvec2rotmat(qvec: np.ndarray) -> np.ndarray:
    w, x, y, z = qvec
    return np.array([
        [1 - 2*y*y - 2*z*z,  2*x*y - 2*w*z,       2*x*z + 2*w*y],
        [2*x*y + 2*w*z,       1 - 2*x*x - 2*z*z,   2*y*z - 2*w*x],
        [2*x*z - 2*w*y,       2*y*z + 2*w*x,       1 - 2*x*x - 2*y*y],
    ])


def load_sparse_points() -> np.ndarray:
    from plyfile import PlyData
    ply = PlyData.read(PLY_PATH)
    pts = np.stack([ply["vertex"]["x"], ply["vertex"]["y"], ply["vertex"]["z"]], axis=1)
    return pts.astype(np.float32)


def load_camera_centers() -> np.ndarray:
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
                qw, qx, qy, qz = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                tx, ty, tz      = float(parts[5]), float(parts[6]), float(parts[7])
            except ValueError:
                continue
            R = np.transpose(_qvec2rotmat(np.array([qw, qx, qy, qz])))
            C = -R @ np.array([tx, ty, tz])
            centers.append(C)
    return np.array(centers, dtype=np.float32)


# ---------------------------------------------------------------------------
# Potential field helpers (same as toy, but 2-D slices of 3-D)
# ---------------------------------------------------------------------------

def local_spacing_2d(pts2d: np.ndarray, k: int = 4) -> np.ndarray:
    tree = cKDTree(pts2d)
    dists, _ = tree.query(pts2d, k=min(k + 1, len(pts2d)))
    return dists[:, -1].astype(np.float32)


def normalized_distance_2d(grid: np.ndarray, pts2d: np.ndarray, tau: np.ndarray):
    diff = grid[:, None, :] - pts2d[None, :, :]        # [G, N, 2]
    dist = np.linalg.norm(diff, axis=2)                 # [G, N]
    norm = dist / tau[None, :]                          # [G, N]
    idx  = np.argmin(norm, axis=1)                      # [G]
    d    = norm[np.arange(len(grid)), idx]
    vec  = diff[np.arange(len(grid)), idx]
    return d, idx, vec


def potential_and_force_2d(grid: np.ndarray, pts2d: np.ndarray, tau: np.ndarray, kind: str = "huber"):
    d, idx, vec = normalized_distance_2d(grid, pts2d, tau)
    u = np.maximum(d - 1.0, 0.0)
    if kind == "quadratic":
        rho  = u ** 2
        drho = 2.0 * u
    elif kind == "huber":
        delta = 0.75
        rho  = np.where(u <= delta, 0.5 * u**2, delta * (u - 0.5 * delta))
        drho = np.where(u <= delta, u, delta)
    elif kind == "saturating":
        rho  = 1.0 - np.exp(-(u / 1.0) ** 2)
        drho = 2.0 * u * np.exp(-(u / 1.0) ** 2)
    else:
        raise ValueError(kind)
    drho = np.where(d <= 1.0, 0.0, drho)
    dist_raw = np.linalg.norm(vec, axis=1)
    unit = np.divide(vec, dist_raw[:, None], out=np.zeros_like(vec), where=dist_raw[:, None] > 1e-9)
    force = -drho[:, None] * unit / tau[idx, None]
    return rho, d, force


def make_grid_2d(xmin, xmax, ymin, ymax, n: int):
    xs = np.linspace(xmin, xmax, n)
    ys = np.linspace(ymin, ymax, n)
    xx, yy = np.meshgrid(xs, ys)
    grid = np.stack([xx.ravel(), yy.ravel()], axis=1).astype(np.float32)
    return xx, yy, grid


def ray_coverage_2d(grid: np.ndarray, cam2d: np.ndarray, sigma: float) -> np.ndarray:
    """Proxy: sum of Gaussian weights from each (sub-sampled) camera center to grid points."""
    # Use every 5th camera for speed; [M, 2] → broadcast over grid [G, 2]
    cams_sub = cam2d[::5]  # [M, 2]
    # dist[g, m] = ||grid[g] - cam[m]||
    diff = grid[:, None, :] - cams_sub[None, :, :]  # [G, M, 2]
    dist = np.linalg.norm(diff, axis=2)              # [G, M]
    cov  = np.exp(-0.5 * (dist / sigma) ** 2).sum(axis=1)  # [G]
    if cov.max() > 0:
        cov /= cov.max()
    return cov.astype(np.float32)


def simulate_dynamics_2d(starts: np.ndarray, pts2d: np.ndarray, tau: np.ndarray,
                          kind: str = "huber", steps: int = 60, lr: float = 0.08):
    trajs = []
    for s in starts:
        x = s.astype(np.float64).copy()
        traj = [x.copy()]
        for _ in range(steps):
            _, d, force = potential_and_force_2d(x[None, :], pts2d, tau, kind)
            if d[0] <= 1.0:
                traj.append(x.copy())
                continue
            x = x + lr * force[0]
            traj.append(x.copy())
        trajs.append(np.array(traj))
    return trajs


def save_fig(fig, pdf, out_dir: Path, name: str) -> None:
    fig.tight_layout()
    if pdf is not None:
        pdf.savefig(fig, dpi=150)
    fig.savefig(out_dir / f"{name}.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="results/diagnostic")
    parser.add_argument("--knn",             type=int,   default=4)
    parser.add_argument("--adaptive-alpha",  type=float, default=0.82)
    parser.add_argument("--grid-size",       type=int,   default=200)
    parser.add_argument("--filter-expand",   type=float, default=1.0,
                        help="expand_factor used by init_pcd_filter (to draw boundary)")
    args = parser.parse_args()

    root = Path(args.output_root)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = root / f"real_sparse_support_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[load] sparse points …")
    pts3d = load_sparse_points()
    print(f"  total: {len(pts3d):,}  Z range: {pts3d[:,2].min():.1f} ~ {pts3d[:,2].max():.1f}")

    print("[load] camera centers …")
    cams3d = load_camera_centers()
    print(f"  total: {len(cams3d)}  Z range: {cams3d[:,2].min():.3f} ~ {cams3d[:,2].max():.3f}")

    # Filter boundary (same as init_pcd_filter with expand_factor=args.filter_expand)
    cam_min = cams3d.min(axis=0)
    cam_max = cams3d.max(axis=0)
    cam_span = cam_max - cam_min
    min_margin = np.array([2.0, 2.0, 3.0])
    margin = np.maximum(cam_span * args.filter_expand, min_margin)
    filt_lo = cam_min - margin
    filt_hi = cam_max + margin

    # In-filter sparse points (used as potential anchors)
    valid = (
        (pts3d[:,0] >= filt_lo[0]) & (pts3d[:,0] <= filt_hi[0]) &
        (pts3d[:,1] >= filt_lo[1]) & (pts3d[:,1] <= filt_hi[1]) &
        (pts3d[:,2] >= filt_lo[2]) & (pts3d[:,2] <= filt_hi[2])
    )
    pts_in  = pts3d[valid]
    pts_out = pts3d[~valid]
    print(f"  in-filter:  {len(pts_in):,} ({100*len(pts_in)/len(pts3d):.1f}%)")
    print(f"  out-filter: {len(pts_out):,} ({100*len(pts_out)/len(pts3d):.1f}%)")

    # ----------------------------------------------------------------
    # Fig 1: Overview — XY top-down  (all points, coloured by |Z|)
    # ----------------------------------------------------------------
    print("[fig1] XY overview …")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    # In-filter points coloured by |Z|
    sc = ax.scatter(pts_in[::4, 0], pts_in[::4, 1],
                    c=np.abs(pts_in[::4, 2]), cmap="viridis", s=1, alpha=0.4,
                    vmin=0, vmax=3.5, rasterized=True)
    ax.scatter(pts_out[:, 0], pts_out[:, 1],
               c="red", s=4, alpha=0.6, label=f"SLAM outliers (removed, N={len(pts_out):,})")
    ax.plot(cams3d[:, 0], cams3d[:, 1], "w-", lw=0.8, alpha=0.8, label="camera trajectory")
    ax.scatter(cams3d[::20, 0], cams3d[::20, 1], c="white", s=15, marker="^", zorder=5)
    rect = mpatches.Rectangle(
        (filt_lo[0], filt_lo[1]), filt_hi[0]-filt_lo[0], filt_hi[1]-filt_lo[1],
        linewidth=1.5, edgecolor="cyan", facecolor="none", label="init_pcd_filter boundary"
    )
    ax.add_patch(rect)
    ax.set_xlim(-22, 20); ax.set_ylim(-10, 8)
    ax.set_xlabel("X (m)"); ax.set_ylabel("Y (m)")
    ax.set_title("XY top-down: sparse points coloured by |Z|")
    ax.set_facecolor("#111111")
    ax.legend(fontsize=7, loc="upper right")
    fig.colorbar(sc, ax=ax, label="|Z| (m)")

    ax = axes[1]
    # Histogram of |Z| for in-filter vs out-filter
    ax.hist(np.abs(pts_in[:, 2]), bins=80, range=(0, 8), color="#2196F3", alpha=0.8, label=f"in-filter ({len(pts_in):,})", density=True)
    ax.axvline(3.0, color="cyan", lw=1.5, linestyle="--", label="Z filter bound ±3.03m")
    ax.set_xlabel("|Z| (m)"); ax.set_ylabel("density")
    ax.set_title("In-filter |Z| distribution")
    ax.legend(fontsize=8)
    ax.text(0.97, 0.8, f"SLAM outliers\n(|Z|>filt bound)\nN={len(pts_out):,}", transform=ax.transAxes,
            ha="right", va="top", color="red", fontsize=8)

    save_fig(fig, None, out_dir, "01_xy_overview")

    # ----------------------------------------------------------------
    # Fig 2: XZ cross-section (the floater axis)
    # using Y sliced near median camera Y
    # ----------------------------------------------------------------
    print("[fig2] XZ cross-section …")
    y_median = float(np.median(cams3d[:, 1]))
    y_half   = 0.4   # ±0.4m slab
    slab_mask = np.abs(pts_in[:, 1] - y_median) < y_half
    pts_xz    = pts_in[slab_mask][:, [0, 2]]   # [N, 2] in X,Z
    cams_xz   = cams3d[:, [0, 2]]               # [M, 2]
    filt_xz   = np.array([[filt_lo[0], filt_lo[2]],
                           [filt_hi[0], filt_hi[2]]])

    # Subsample for speed
    rng = np.random.default_rng(42)
    if len(pts_xz) > 4000:
        idx = rng.choice(len(pts_xz), 4000, replace=False)
        pts_xz_sub = pts_xz[idx]
    else:
        pts_xz_sub = pts_xz

    h     = local_spacing_2d(pts_xz_sub, k=args.knn)
    tau_a = np.clip(args.adaptive_alpha * h, 0.05, 0.5)
    tau_f = np.full(len(pts_xz_sub), 0.28, dtype=np.float32)

    xmin_g, xmax_g = filt_lo[0] - 1.0, filt_hi[0] + 1.0
    zmin_g, zmax_g = filt_lo[2] - 0.5, filt_hi[2] + 0.5
    xx, zz, grid = make_grid_2d(xmin_g, xmax_g, zmin_g, zmax_g, args.grid_size)
    bounds_xz = (xmin_g, xmax_g, zmin_g, zmax_g)

    print("  computing potential (XZ slab) …")
    rho_h, d_adapt, force_h = potential_and_force_2d(grid, pts_xz_sub, tau_a, "huber")
    _, d_fixed, _           = normalized_distance_2d(grid, pts_xz_sub, tau_f)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharex=True, sharey=True)
    for ax, d, tau, title, color in [
        (axes[0], d_fixed, tau_f, f"Fixed tau={0.28:.2f}", "#d62728"),
        (axes[1], d_adapt, tau_a, "Adaptive tau = α · h_j", "#2ca02c"),
    ]:
        im = ax.imshow(np.minimum(d, 4.0).reshape(xx.shape),
                       extent=bounds_xz, origin="lower", cmap="cividis", vmin=0, vmax=4)
        ax.contour(xx, zz, d.reshape(xx.shape), levels=[1.0], colors="white", linewidths=1.2)
        ax.scatter(pts_xz_sub[:, 0], pts_xz_sub[:, 1], s=3, c="#62b6ff", alpha=0.7)
        ax.plot(cams_xz[:, 0], cams_xz[:, 1], "r-", lw=0.8, alpha=0.8, label="cam trajectory")
        # filter boundary lines
        ax.axhline(filt_lo[2], color="cyan", lw=1.2, linestyle="--", label="filter Z bound")
        ax.axhline(filt_hi[2], color="cyan", lw=1.2, linestyle="--")
        ax.set_xlabel("X (m)"); ax.set_ylabel("Z (m)")
        ax.set_title(f"Normalised distance D(x) — {title}")
        ax.legend(fontsize=7)
        fig.colorbar(im, ax=ax, label="D(x) [white contour = plateau edge]")
    save_fig(fig, None, out_dir, "02_xz_normalized_distance")

    # ----------------------------------------------------------------
    # Fig 3: Potential field + force vectors (Huber, adaptive tau)
    # ----------------------------------------------------------------
    print("[fig3] potential + force vectors …")
    fig, ax = plt.subplots(figsize=(12, 6))
    vmax_rho = float(np.percentile(rho_h, 97))
    im = ax.imshow(rho_h.reshape(xx.shape), extent=bounds_xz, origin="lower",
                   cmap="inferno", vmin=0, vmax=vmax_rho)
    ax.contour(xx, zz, d_adapt.reshape(xx.shape), levels=[1.0], colors="cyan", linewidths=1.0)
    step = 14
    fx = force_h[:, 0].reshape(xx.shape)
    fz = force_h[:, 1].reshape(xx.shape)
    ax.quiver(xx[::step, ::step], zz[::step, ::step],
              fx[::step, ::step], fz[::step, ::step],
              color="white", alpha=0.65, scale=18, width=0.003)
    ax.scatter(pts_xz_sub[:, 0], pts_xz_sub[:, 1], s=4, c="#62b6ff", alpha=0.8, label="sparse pts (XZ slab)")
    ax.plot(cams_xz[:, 0], cams_xz[:, 1], "r-", lw=1.0, label="cam trajectory")
    ax.axhline(filt_lo[2], color="cyan", lw=1.2, linestyle="--", label=f"filter bound Z={filt_lo[2]:.2f}m")
    ax.axhline(filt_hi[2], color="cyan", lw=1.2, linestyle="--", label=f"filter bound Z=+{filt_hi[2]:.2f}m")
    ax.set_xlabel("X (m)"); ax.set_ylabel("Z (m)")
    ax.set_title("XZ plane: Huber potential ρ(x) + force field (adaptive tau)\n"
                 "cyan contour = plateau edge  |  arrows = force direction toward nearest sparse pt")
    ax.legend(fontsize=7, loc="upper right")
    fig.colorbar(im, ax=ax, label="ρ(x) potential energy")
    save_fig(fig, None, out_dir, "03_xz_potential_force")

    # ----------------------------------------------------------------
    # Fig 4: Gaussian dynamics — Pop 2 floater scenario
    # Start positions just outside filter boundary (where densification creates floaters)
    # ----------------------------------------------------------------
    print("[fig4] Gaussian dynamics (Pop 2 scenario) …")
    starts = np.array([
        [filt_lo[0] + 1.0,  filt_lo[2] + 0.3],   # bottom-left corner, just inside
        [0.0,                filt_lo[2] + 0.3],   # centre X, just inside Z-
        [filt_hi[0] - 1.0,  filt_lo[2] + 0.3],
        [filt_lo[0] + 1.0,  filt_hi[2] - 0.3],   # top boundary
        [0.0,                filt_hi[2] - 0.3],
        [filt_hi[0] - 1.0,  filt_hi[2] - 0.3],
        # further outside (densification drifted past boundary)
        [0.0,                filt_lo[2] - 0.5],
        [0.0,                filt_hi[2] + 0.5],
    ], dtype=np.float32)

    trajs = simulate_dynamics_2d(starts, pts_xz_sub, tau_a, "huber", steps=80, lr=0.12)

    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(rho_h.reshape(xx.shape), extent=bounds_xz, origin="lower",
                   cmap="Greys", alpha=0.55, vmin=0, vmax=vmax_rho)
    ax.contour(xx, zz, d_adapt.reshape(xx.shape), levels=[1.0], colors="#2ca02c", linewidths=1.2)
    ax.scatter(pts_xz_sub[:, 0], pts_xz_sub[:, 1], s=3, c="#1f77b4", alpha=0.6)
    ax.plot(cams_xz[:, 0], cams_xz[:, 1], "r-", lw=0.8, alpha=0.7)
    ax.axhline(filt_lo[2], color="cyan", lw=1.2, linestyle="--")
    ax.axhline(filt_hi[2], color="cyan", lw=1.2, linestyle="--")
    colors = plt.cm.tab10(np.linspace(0, 0.7, len(trajs)))
    for traj, c in zip(trajs, colors):
        ax.plot(traj[:, 0], traj[:, 1], "-o", ms=1.8, lw=1.4, color=c, alpha=0.9)
        ax.scatter(traj[0, 0], traj[0, 1], s=50, marker="x", color=c, zorder=6, linewidths=1.5)
        ax.scatter(traj[-1, 0], traj[-1, 1], s=30, marker="o", color=c, zorder=6)
    ax.set_xlabel("X (m)"); ax.set_ylabel("Z (m)")
    ax.set_title("XZ plane: Gaussian dynamics under sparse-support potential\n"
                 "× = start (boundary region, Pop 2 floater scenario)  ● = end\n"
                 "cyan dashes = filter boundary  |  green contour = plateau edge")
    ax.set_xlim(bounds_xz[0], bounds_xz[1])
    ax.set_ylim(bounds_xz[2], bounds_xz[3])
    save_fig(fig, None, out_dir, "04_xz_gaussian_dynamics")

    # ----------------------------------------------------------------
    # Fig 5: Local spacing h_j histogram + tau_adaptive distribution
    # ----------------------------------------------------------------
    print("[fig5] tau distribution …")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].hist(h, bins=60, color="#2196F3", alpha=0.8)
    axes[0].axvline(float(np.median(h)), color="orange", lw=1.5, linestyle="--", label=f"median h = {np.median(h):.3f}m")
    axes[0].set_xlabel("h_j: 4-NN spacing (m)"); axes[0].set_ylabel("count")
    axes[0].set_title("Local sparse point spacing in XZ slab")
    axes[0].legend()

    axes[1].hist(tau_a, bins=60, color="#4CAF50", alpha=0.8, label="adaptive tau")
    axes[1].axvline(0.28, color="red", lw=1.5, linestyle="--", label="fixed tau=0.28")
    axes[1].set_xlabel("tau_j (m)"); axes[1].set_ylabel("count")
    axes[1].set_title("Adaptive vs fixed plateau radius tau_j = α · h_j")
    axes[1].legend()
    save_fig(fig, None, out_dir, "05_tau_distribution")

    # ----------------------------------------------------------------
    # Fig 6: Ray coverage proxy (XZ plane)
    # ----------------------------------------------------------------
    print("[fig6] ray coverage (XZ) …")
    ray_cov = ray_coverage_2d(grid, cams_xz, sigma=0.12)
    plateau_mask     = (d_adapt <= 1.0).astype(float)
    potential_active = (d_adapt  > 1.0).astype(float)
    weak_ray_pot     = potential_active * (ray_cov < 0.15)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharex=True, sharey=True)
    for ax, vals, title, cmap in [
        (axes[0], ray_cov,       "Ray coverage proxy",                 "magma"),
        (axes[1], plateau_mask,  "Support plateau (D(x) ≤ 1)",         "Greens"),
        (axes[2], weak_ray_pot,  "Potential-active & weak-ray\n(floater risk zone)", "coolwarm"),
    ]:
        im = ax.imshow(vals.reshape(xx.shape), extent=bounds_xz, origin="lower",
                       cmap=cmap, vmin=0, vmax=1)
        ax.contour(xx, zz, d_adapt.reshape(xx.shape), levels=[1.0], colors="white", linewidths=0.9)
        ax.scatter(pts_xz_sub[:, 0], pts_xz_sub[:, 1], s=2, c="#62b6ff", alpha=0.5)
        ax.plot(cams_xz[:, 0], cams_xz[:, 1], "r-", lw=0.8, alpha=0.7)
        ax.axhline(filt_lo[2], color="cyan", lw=1.0, linestyle="--")
        ax.axhline(filt_hi[2], color="cyan", lw=1.0, linestyle="--")
        ax.set_xlabel("X (m)"); ax.set_ylabel("Z (m)")
        ax.set_title(title)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    save_fig(fig, None, out_dir, "06_xz_ray_vs_potential")

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    weak_ray_pot_frac = float(np.mean(weak_ray_pot > 0))
    summary = {
        "data": {
            "sparse_points_total":    int(len(pts3d)),
            "sparse_points_in_filter": int(len(pts_in)),
            "sparse_points_out_filter": int(len(pts_out)),
            "camera_count":           int(len(cams3d)),
        },
        "filter_bounds": {
            "X": [float(filt_lo[0]), float(filt_hi[0])],
            "Y": [float(filt_lo[1]), float(filt_hi[1])],
            "Z": [float(filt_lo[2]), float(filt_hi[2])],
        },
        "xz_slab": {
            "y_median_m": float(y_median),
            "y_half_m":   float(y_half),
            "pts_in_slab": int(len(pts_xz)),
            "pts_used_for_potential": int(len(pts_xz_sub)),
        },
        "tau": {
            "adaptive_alpha":  args.adaptive_alpha,
            "adaptive_min_m":  float(tau_a.min()),
            "adaptive_median_m": float(np.median(tau_a)),
            "adaptive_max_m":  float(tau_a.max()),
            "fixed_m":         0.28,
        },
        "potential": {
            "plateau_area_fraction_adaptive": float(np.mean(d_adapt <= 1.0)),
            "plateau_area_fraction_fixed":    float(np.mean(d_fixed <= 1.0)),
            "weak_ray_potential_active_fraction": weak_ray_pot_frac,
        },
        "output_dir": str(out_dir),
    }

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print()
    print(json.dumps(summary, indent=2))
    print(f"\n[done] figures → {out_dir}")


if __name__ == "__main__":
    main()
