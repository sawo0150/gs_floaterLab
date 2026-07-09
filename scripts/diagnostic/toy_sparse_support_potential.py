#!/usr/bin/env python3
"""2D toy visualization for sparse-support plateau potential fields."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from scipy.spatial import cKDTree


def make_sparse_points(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t_dense = np.linspace(-2.7, -0.45, 34)
    t_mid = np.linspace(-0.25, 1.25, 18)
    t_sparse = np.linspace(1.55, 3.0, 9)
    t = np.concatenate([t_dense, t_mid, t_sparse])
    y = 0.55 * np.sin(1.35 * t) + 0.15 * np.cos(3.0 * t)
    pts = np.stack([t, y], axis=1)
    pts += rng.normal(scale=[0.035, 0.035], size=pts.shape)

    # A few sparse-init outliers to make the plateau risk visible.
    outliers = np.array([[2.15, 1.65], [-2.2, 1.25], [0.8, -1.55]])
    return np.concatenate([pts, outliers], axis=0)


def local_spacing(points: np.ndarray, k: int) -> np.ndarray:
    tree = cKDTree(points)
    dists, _ = tree.query(points, k=min(k + 1, len(points)))
    return dists[:, -1]


def make_grid(bounds: tuple[float, float, float, float], n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    xmin, xmax, ymin, ymax = bounds
    xs = np.linspace(xmin, xmax, n)
    ys = np.linspace(ymin, ymax, n)
    xx, yy = np.meshgrid(xs, ys)
    grid = np.stack([xx.ravel(), yy.ravel()], axis=1)
    return xx, yy, grid


def normalized_distance(grid: np.ndarray, points: np.ndarray, tau: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    diff = grid[:, None, :] - points[None, :, :]
    dist = np.linalg.norm(diff, axis=2)
    norm = dist / tau[None, :]
    idx = np.argmin(norm, axis=1)
    d = norm[np.arange(len(grid)), idx]
    vec = diff[np.arange(len(grid)), idx]
    return d, idx, vec


def rho_and_grad(d: np.ndarray, kind: str, huber_delta: float = 0.75, sat_scale: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    u = np.maximum(d - 1.0, 0.0)
    if kind == "quadratic":
        rho = u**2
        drho = 2.0 * u
    elif kind == "huber":
        rho = np.where(u <= huber_delta, 0.5 * u**2, huber_delta * (u - 0.5 * huber_delta))
        drho = np.where(u <= huber_delta, u, huber_delta)
    elif kind == "saturating":
        rho = 1.0 - np.exp(-(u / sat_scale) ** 2)
        drho = 2.0 * u / (sat_scale**2) * np.exp(-(u / sat_scale) ** 2)
    else:
        raise ValueError(f"unknown potential kind: {kind}")
    drho = np.where(d <= 1.0, 0.0, drho)
    return rho, drho


def potential_and_force(
    grid: np.ndarray,
    points: np.ndarray,
    tau: np.ndarray,
    kind: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    d, idx, vec = normalized_distance(grid, points, tau)
    rho, drho = rho_and_grad(d, kind)
    dist = np.linalg.norm(vec, axis=1)
    unit = np.divide(vec, dist[:, None], out=np.zeros_like(vec), where=dist[:, None] > 1e-9)
    grad_d = unit / tau[idx, None]
    grad_phi = drho[:, None] * grad_d
    force = -grad_phi
    return rho, d, force


def ray_segments(points: np.ndarray) -> tuple[np.ndarray, list[tuple[np.ndarray, np.ndarray]]]:
    cams = np.array([[-3.2, -2.2], [-1.55, -2.35], [0.15, -2.15], [1.85, -2.3], [3.2, -2.05]])
    segments: list[tuple[np.ndarray, np.ndarray]] = []
    for ci, cam in enumerate(cams):
        stride = 2 + (ci % 2)
        visible = points[ci::stride]
        # Avoid drawing every ray to keep the diagnostic readable.
        for p in visible[:22]:
            if p[1] > -1.3:
                segments.append((cam, p))
    return cams, segments


def point_segment_distance(grid: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ab = b - a
    denom = float(np.dot(ab, ab))
    if denom < 1e-12:
        return np.linalg.norm(grid - a[None, :], axis=1)
    t = np.clip(((grid - a[None, :]) @ ab) / denom, 0.0, 1.0)
    proj = a[None, :] + t[:, None] * ab[None, :]
    return np.linalg.norm(grid - proj, axis=1)


def ray_coverage(grid: np.ndarray, segments: list[tuple[np.ndarray, np.ndarray]], sigma: float) -> np.ndarray:
    cov = np.zeros(len(grid), dtype=np.float64)
    for a, b in segments:
        dist = point_segment_distance(grid, a, b)
        cov += np.exp(-0.5 * (dist / sigma) ** 2)
    if cov.max() > 0:
        cov /= cov.max()
    return cov


def simulate_dynamics(starts: np.ndarray, points: np.ndarray, tau: np.ndarray, kind: str, steps: int, lr: float) -> list[np.ndarray]:
    trajectories = []
    for start in starts:
        x = start.astype(np.float64).copy()
        traj = [x.copy()]
        for _ in range(steps):
            _, d, force = potential_and_force(x[None, :], points, tau, kind)
            if d[0] <= 1.0:
                traj.append(x.copy())
                continue
            x = x + lr * force[0]
            traj.append(x.copy())
        trajectories.append(np.asarray(traj))
    return trajectories


def draw_points_and_cameras(ax, points: np.ndarray, cams: np.ndarray, segments: list[tuple[np.ndarray, np.ndarray]]) -> None:
    for a, b in segments:
        ax.plot([a[0], b[0]], [a[1], b[1]], color="0.75", lw=0.45, alpha=0.45, zorder=1)
    ax.scatter(points[:, 0], points[:, 1], s=16, c="#1f77b4", edgecolor="white", linewidth=0.35, label="sparse init points", zorder=4)
    ax.scatter(cams[:, 0], cams[:, 1], s=70, marker="^", c="#222222", label="cameras", zorder=5)


def add_plateau_circles(ax, points: np.ndarray, tau: np.ndarray, color: str, alpha: float) -> None:
    for p, r in zip(points, tau):
        circle = plt.Circle(p, r, color=color, fill=False, alpha=alpha, lw=0.8)
        ax.add_patch(circle)


def save_fig(fig, pdf: PdfPages, out_dir: Path, name: str) -> None:
    fig.tight_layout()
    pdf.savefig(fig, dpi=160)
    fig.savefig(out_dir / f"{name}.png", dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="results/diagnostic")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--grid-size", type=int, default=220)
    parser.add_argument("--fixed-tau", type=float, default=0.28)
    parser.add_argument("--adaptive-alpha", type=float, default=0.82)
    parser.add_argument("--knn", type=int, default=4)
    args = parser.parse_args()

    root = Path(args.output_root)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = root / f"toy_sparse_support_potential_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    bounds = (-3.55, 3.55, -2.55, 2.25)
    points = make_sparse_points(args.seed)
    h = local_spacing(points, args.knn)
    tau_fixed = np.full(len(points), args.fixed_tau)
    tau_adaptive = np.clip(args.adaptive_alpha * h, 0.16, 0.58)
    xx, yy, grid = make_grid(bounds, args.grid_size)
    cams, segments = ray_segments(points)

    rho_q, d_adapt, force_q = potential_and_force(grid, points, tau_adaptive, "quadratic")
    rho_h, _, force_h = potential_and_force(grid, points, tau_adaptive, "huber")
    rho_s, _, force_s = potential_and_force(grid, points, tau_adaptive, "saturating")
    d_fixed, _, _ = normalized_distance(grid, points, tau_fixed)
    ray_cov = ray_coverage(grid, segments, sigma=0.055)

    starts = np.array([[-3.0, 0.85], [-1.0, 1.35], [0.15, -1.25], [1.8, 1.05], [2.85, -0.25], [-0.7, 0.0]])
    trajectories = simulate_dynamics(starts, points, tau_adaptive, "huber", steps=38, lr=0.22)

    pdf_path = out_dir / "toy_sparse_support_potential_report.pdf"
    with PdfPages(pdf_path) as pdf:
        fig, ax = plt.subplots(figsize=(10, 6))
        sc = ax.scatter(points[:, 0], points[:, 1], c=h, cmap="viridis", s=42, edgecolor="white", linewidth=0.4)
        ax.set_title("Sparse init map distribution and local spacing h_j")
        ax.set_xlim(bounds[0], bounds[1])
        ax.set_ylim(bounds[2], bounds[3])
        ax.set_aspect("equal")
        fig.colorbar(sc, ax=ax, label=f"{args.knn}-NN spacing")
        save_fig(fig, pdf, out_dir, "01_sparse_points_local_spacing")

        fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharex=True, sharey=True)
        for ax, tau, title, color in [
            (axes[0], tau_fixed, f"Fixed plateau radius tau={args.fixed_tau:.2f}", "#d62728"),
            (axes[1], tau_adaptive, "Adaptive plateau radius tau_j=alpha h_j", "#2ca02c"),
        ]:
            add_plateau_circles(ax, points, tau, color, 0.38)
            ax.scatter(points[:, 0], points[:, 1], s=12, c="#1f77b4")
            ax.set_title(title)
            ax.set_xlim(bounds[0], bounds[1])
            ax.set_ylim(bounds[2], bounds[3])
            ax.set_aspect("equal")
        save_fig(fig, pdf, out_dir, "02_fixed_vs_adaptive_plateau")

        fig, ax = plt.subplots(figsize=(10, 6))
        im = ax.imshow(ray_cov.reshape(xx.shape), extent=bounds, origin="lower", cmap="magma", alpha=0.86, vmin=0, vmax=1)
        draw_points_and_cameras(ax, points, cams, segments)
        ax.set_title("Camera/ray distribution: photometric supervision proxy")
        ax.set_xlim(bounds[0], bounds[1])
        ax.set_ylim(bounds[2], bounds[3])
        ax.set_aspect("equal")
        fig.colorbar(im, ax=ax, label="normalized ray coverage")
        save_fig(fig, pdf, out_dir, "03_ray_coverage")

        fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharex=True, sharey=True)
        for ax, d, title in [
            (axes[0], d_fixed, "D(x), fixed tau"),
            (axes[1], d_adapt, "D(x), adaptive tau_j"),
        ]:
            im = ax.imshow(np.minimum(d.reshape(xx.shape), 3.0), extent=bounds, origin="lower", cmap="cividis", vmin=0, vmax=3)
            ax.contour(xx, yy, d.reshape(xx.shape), levels=[1.0], colors="white", linewidths=1.2)
            ax.scatter(points[:, 0], points[:, 1], s=10, c="#1f77b4")
            ax.set_title(title)
            ax.set_xlim(bounds[0], bounds[1])
            ax.set_ylim(bounds[2], bounds[3])
            ax.set_aspect("equal")
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        save_fig(fig, pdf, out_dir, "04_normalized_distance_plateau")

        fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharex=True, sharey=True)
        for ax, rho, force, title in [
            (axes[0], rho_q, force_q, "quadratic hinge"),
            (axes[1], rho_h, force_h, "Huber-like"),
            (axes[2], rho_s, force_s, "saturating"),
        ]:
            im = ax.imshow(rho.reshape(xx.shape), extent=bounds, origin="lower", cmap="inferno", vmin=0, vmax=np.percentile(rho_q, 98))
            ax.contour(xx, yy, d_adapt.reshape(xx.shape), levels=[1.0], colors="cyan", linewidths=0.9)
            step = 15
            fx = force[:, 0].reshape(xx.shape)
            fy = force[:, 1].reshape(xx.shape)
            ax.quiver(xx[::step, ::step], yy[::step, ::step], fx[::step, ::step], fy[::step, ::step], color="white", alpha=0.72, scale=28, width=0.0024)
            ax.scatter(points[:, 0], points[:, 1], s=8, c="#62b6ff")
            ax.set_title(title)
            ax.set_xlim(bounds[0], bounds[1])
            ax.set_ylim(bounds[2], bounds[3])
            ax.set_aspect("equal")
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        save_fig(fig, pdf, out_dir, "05_potential_shapes_force_fields")

        fig, ax = plt.subplots(figsize=(10, 6))
        im = ax.imshow(rho_h.reshape(xx.shape), extent=bounds, origin="lower", cmap="Greys", alpha=0.62)
        ax.contour(xx, yy, d_adapt.reshape(xx.shape), levels=[1.0], colors="#2ca02c", linewidths=1.4)
        ax.scatter(points[:, 0], points[:, 1], s=12, c="#1f77b4", zorder=4)
        for traj in trajectories:
            ax.plot(traj[:, 0], traj[:, 1], "-o", ms=2.2, lw=1.4, alpha=0.9)
        ax.scatter(starts[:, 0], starts[:, 1], s=60, marker="x", c="black", label="initial Gaussian centers")
        ax.set_title("Gaussian center dynamics under Huber-like potential only")
        ax.set_xlim(bounds[0], bounds[1])
        ax.set_ylim(bounds[2], bounds[3])
        ax.set_aspect("equal")
        ax.legend(loc="upper left")
        fig.colorbar(im, ax=ax, label="Phi")
        save_fig(fig, pdf, out_dir, "06_gaussian_center_dynamics")

        fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharex=True, sharey=True)
        plateau_mask = (d_adapt <= 1.0).astype(float)
        potential_active = (d_adapt > 1.0).astype(float)
        maps = [
            (ray_cov, "ray coverage proxy", "magma"),
            (plateau_mask, "support plateau, D(x)<=1", "Greens"),
            (potential_active * (1.0 - ray_cov), "potential-active / weak-ray area", "coolwarm"),
        ]
        for ax, (values, title, cmap) in zip(axes, maps):
            im = ax.imshow(values.reshape(xx.shape), extent=bounds, origin="lower", cmap=cmap, vmin=0, vmax=max(1.0, values.max()))
            ax.contour(xx, yy, d_adapt.reshape(xx.shape), levels=[1.0], colors="white", linewidths=0.9)
            ax.scatter(points[:, 0], points[:, 1], s=8, c="#1f77b4")
            ax.set_title(title)
            ax.set_xlim(bounds[0], bounds[1])
            ax.set_ylim(bounds[2], bounds[3])
            ax.set_aspect("equal")
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        save_fig(fig, pdf, out_dir, "07_ray_vs_potential_coverage")

    summary = {
        "seed": args.seed,
        "num_sparse_points": int(len(points)),
        "num_ray_segments": int(len(segments)),
        "fixed_tau": args.fixed_tau,
        "adaptive_alpha": args.adaptive_alpha,
        "adaptive_tau_min": float(tau_adaptive.min()),
        "adaptive_tau_median": float(np.median(tau_adaptive)),
        "adaptive_tau_max": float(tau_adaptive.max()),
        "fixed_plateau_area_fraction": float(np.mean(d_fixed <= 1.0)),
        "adaptive_plateau_area_fraction": float(np.mean(d_adapt <= 1.0)),
        "weak_ray_potential_active_fraction": float(np.mean((d_adapt > 1.0) & (ray_cov < 0.15))),
        "pdf": str(pdf_path),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
