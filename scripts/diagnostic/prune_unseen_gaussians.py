#!/usr/bin/env python3
"""Explicitly prune Gaussians sitting in never-ray-visited voxels from each
run's final (iteration_30000) point cloud, and save the result so before/
after can be diffed directly.

Reuses the exact ray-marching grid from check_gaussian_ray_coverage.py.
For each run, writes two full-property PLYs (loadable by the standard 3DGS
viewer/renderer, same 62 fields as the original):
  pruned.ply   -- kept Gaussians only (ray-visited voxels)          "after"
  removed.ply  -- pruned-out Gaussians only (zero-ray voxels)       "what got cut"
"""
import json
import numpy as np
from pathlib import Path
from plyfile import PlyData, PlyElement

DATASET = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full")
IMG_TXT = DATASET / "sparse/0/images.txt"
IMG_W, IMG_H = 1024, 1024
FX, FY, CX, CY = 500.0, 500.0, 511.5, 511.5
VOXEL_SIZE = 0.15
PIXEL_STEP = 48
MAX_DEPTH = 15.0
DEPTH_STEP = 0.15

R = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments")
RUNS = [
    "exp30_orbfull_baseline_20260709_210151",
    "exp31_orbfull_anchorinit_20260709_211736",
    "exp32_orbfull_plateau_basetau_20260709_213513",
    "exp33_orbfull_plateau_bigtau_20260709_221147",
    "exp34_orbfull_highconf_anchorinit_20260709_223856",
    "exp35_orbfull_plateau_highconf_basetau_20260709_224841",
    "exp36_orbfull_plateau_highconf_bigtau_20260709_230121",
    "exp37_orbfull_dense_confmono_init_20260709_231355",
]

_TS = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_ROOT = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic") / f"rayprune_{_TS}"
OUT_ROOT.mkdir(parents=True, exist_ok=True)


def qvec2rotmat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2*y*y - 2*z*z, 2*x*y - 2*w*z,     2*x*z + 2*w*y],
        [2*x*y + 2*w*z,     1 - 2*x*x - 2*z*z, 2*y*z - 2*w*x],
        [2*x*z - 2*w*y,     2*y*z + 2*w*x,     1 - 2*x*x - 2*y*y],
    ])


def load_cameras():
    centers, rotmats = [], []
    for line in open(IMG_TXT):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split()
        if len(p) < 9:
            continue
        q = np.array([float(x) for x in p[1:5]])
        t = np.array([float(x) for x in p[5:8]])
        R_wc = qvec2rotmat(q).T
        centers.append(-R_wc @ t)
        rotmats.append(R_wc)
    return np.array(centers, dtype=np.float32), np.array(rotmats, dtype=np.float32)


def build_ray_dirs_cam(step):
    us = np.arange(step // 2, IMG_W, step, dtype=np.float32)
    vs = np.arange(step // 2, IMG_H, step, dtype=np.float32)
    uu, vv = np.meshgrid(us, vs)
    dx = (uu.ravel() - CX) / FX
    dy = (vv.ravel() - CY) / FY
    dz = np.ones_like(dx)
    dirs = np.stack([dx, dy, dz], axis=1)
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    return dirs.astype(np.float32)


def camera_bound(centers):
    lo = centers.min(0) - np.maximum((centers.max(0) - centers.min(0)) * 1.0, [2., 2., 3.])
    hi = centers.max(0) + np.maximum((centers.max(0) - centers.min(0)) * 1.0, [2., 2., 3.])
    return lo, hi


def build_visited_grid():
    print("[load] cameras ...")
    centers, rotmats = load_cameras()
    lo, hi = camera_bound(centers)
    dims = np.ceil((hi - lo) / VOXEL_SIZE).astype(int) + 1
    print(f"  grid dims={tuple(dims)} ({dims.prod():,} voxels)")

    visited = np.zeros(tuple(dims), dtype=bool)
    ray_dirs_cam = build_ray_dirs_cam(PIXEL_STEP)
    depths = np.arange(DEPTH_STEP, MAX_DEPTH + 1e-6, DEPTH_STEP, dtype=np.float32)

    print("[march] tracing rays ...")
    for ci, (C, Rw) in enumerate(zip(centers, rotmats)):
        if ci % 300 == 0:
            print(f"  cam {ci}/{len(centers)}")
        dirs_world = ray_dirs_cam @ Rw.T
        pts = C[None, None, :] + depths[None, :, None] * dirs_world[:, None, :]
        pts = pts.reshape(-1, 3)
        idx = np.floor((pts - lo) / VOXEL_SIZE).astype(np.int64)
        ok = ((idx >= 0) & (idx < dims[None, :])).all(axis=1)
        idx = idx[ok]
        visited[idx[:, 0], idx[:, 1], idx[:, 2]] = True

    n_visited = int(visited.sum())
    print(f"[done] visited={n_visited:,} / {dims.prod():,} ({100*n_visited/dims.prod():.1f}%)")
    return visited, lo, dims


def prune_run(name, visited, lo, dims):
    ply_path = R / name / "point_cloud/iteration_30000/point_cloud.ply"
    ply = PlyData.read(str(ply_path))
    v = ply["vertex"]
    data = v.data  # structured array, all 62 fields

    xyz = np.stack([np.array(data["x"]), np.array(data["y"]), np.array(data["z"])], axis=1).astype(np.float32)
    opacity = 1.0 / (1.0 + np.exp(-np.array(data["opacity"], dtype=np.float64)))

    idx = np.floor((xyz - lo) / VOXEL_SIZE).astype(np.int64)
    inb = ((idx >= 0) & (idx < dims[None, :])).all(axis=1)
    zero_ray = np.zeros(len(xyz), dtype=bool)
    zero_ray[inb] = ~visited[idx[inb, 0], idx[inb, 1], idx[inb, 2]]
    zero_ray[~inb] = True

    keep_mask = ~zero_ray
    kept, removed = data[keep_mask], data[zero_ray]

    out_dir = OUT_ROOT / name
    out_dir.mkdir(parents=True, exist_ok=True)
    PlyData([PlyElement.describe(kept, "vertex")], text=False).write(out_dir / "pruned.ply")
    PlyData([PlyElement.describe(removed, "vertex")], text=False).write(out_dir / "removed.ply")

    op_removed = opacity[zero_ray]
    summary = {
        "run": name,
        "n_total": int(len(data)),
        "n_kept": int(keep_mask.sum()),
        "n_removed": int(zero_ray.sum()),
        "removed_pct": float(100 * zero_ray.sum() / len(data)),
        "removed_opacity_gt_0.1": int((op_removed > 0.1).sum()),
        "removed_opacity_gt_0.5": int((op_removed > 0.5).sum()),
    }
    json.dump(summary, open(out_dir / "summary.json", "w"), indent=2)
    return summary


def main():
    visited, lo, dims = build_visited_grid()
    np.savez(OUT_ROOT / "ray_grid.npz", visited=visited, lo=lo, dims=dims, voxel_size=VOXEL_SIZE)

    print(f"\n{'Run':<55} {'total':>9} {'kept':>9} {'removed':>9} {'removed%':>9} {'op>0.1':>8} {'op>0.5':>7}")
    rows = []
    for name in RUNS:
        s = prune_run(name, visited, lo, dims)
        rows.append(s)
        print(f"{s['run']:<55} {s['n_total']:>9,} {s['n_kept']:>9,} {s['n_removed']:>9,} "
              f"{s['removed_pct']:>8.2f}% {s['removed_opacity_gt_0.1']:>8,} {s['removed_opacity_gt_0.5']:>7,}")

    json.dump(rows, open(OUT_ROOT / "all_summary.json", "w"), indent=2)
    print(f"\nOutput: {OUT_ROOT}")
    print("Each run dir has pruned.ply (kept only) and removed.ply (cut only), full 62-field 3DGS PLY format.")


if __name__ == "__main__":
    main()
