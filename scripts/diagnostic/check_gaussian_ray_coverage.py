#!/usr/bin/env python3
"""For the ORB training trajectory (data/03_rgb_3dgs_full), build a 3D voxel
grid marking which cells any camera pixel ray ever passes through
(0..15m depth). Then, for each experiment's final Gaussians (iter 30000),
check how many fall in voxels that NO ray ever visited -- these have zero
photometric gradient from any view, so their existence is entirely
unconstrained (definite floaters by construction, not just "far from anchor").

Also reports opacity (sigmoid) of those zero-ray-density Gaussians, since a
near-zero-opacity Gaussian sitting in unobserved space is harmless noise,
while a high-opacity one there is an actual visible floater.
"""
import numpy as np
from pathlib import Path
from plyfile import PlyData

DATASET = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full")
IMG_TXT = DATASET / "sparse/0/images.txt"

IMG_W, IMG_H = 1024, 1024
FX, FY, CX, CY = 500.0, 500.0, 511.5, 511.5

VOXEL_SIZE = 0.15
PIXEL_STEP = 48          # -> 21x21 = 441 rays/cam
MAX_DEPTH = 15.0
DEPTH_STEP = 0.15        # matches voxel size

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
        R_wc = qvec2rotmat(q).T   # cam->world rotation
        C = -R_wc @ t
        centers.append(C)
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


def main():
    print("[load] cameras ...")
    centers, rotmats = load_cameras()
    print(f"  {len(centers)} cameras")
    lo, hi = camera_bound(centers)
    dims = np.ceil((hi - lo) / VOXEL_SIZE).astype(int) + 1
    print(f"  bounds lo={lo.round(2)} hi={hi.round(2)}  grid dims={tuple(dims)} ({dims.prod():,} voxels)")

    visited = np.zeros(tuple(dims), dtype=bool)

    ray_dirs_cam = build_ray_dirs_cam(PIXEL_STEP)
    n_ray = len(ray_dirs_cam)
    depths = np.arange(DEPTH_STEP, MAX_DEPTH + 1e-6, DEPTH_STEP, dtype=np.float32)
    n_depth = len(depths)
    print(f"[rays] {n_ray} rays/cam x {n_depth} depth steps -> {len(centers)*n_ray*n_depth:,} samples")

    for ci, (C, Rw) in enumerate(zip(centers, rotmats)):
        if ci % 200 == 0:
            print(f"  cam {ci}/{len(centers)} ...")
        dirs_world = ray_dirs_cam @ Rw.T                      # (n_ray, 3)
        pts = C[None, None, :] + depths[None, :, None] * dirs_world[:, None, :]   # (n_ray, n_depth, 3)
        pts = pts.reshape(-1, 3)
        idx = np.floor((pts - lo) / VOXEL_SIZE).astype(np.int64)
        ok = ((idx >= 0) & (idx < dims[None, :])).all(axis=1)
        idx = idx[ok]
        visited[idx[:, 0], idx[:, 1], idx[:, 2]] = True

    n_visited = int(visited.sum())
    print(f"[done] visited voxels: {n_visited:,} / {dims.prod():,} ({100*n_visited/dims.prod():.1f}%)")

    print(f"\n{'Run':<55} {'Gaussians':>10} {'zero-ray N':>11} {'zero-ray %':>10} {'  op>0.1':>9} {'op>0.5':>8}")
    for name in RUNS:
        ply = R / name / "point_cloud/iteration_30000/point_cloud.ply"
        if not ply.exists():
            print(f"{name:<55} MISSING")
            continue
        v = PlyData.read(str(ply))["vertex"]
        xyz = np.stack([np.array(v["x"]), np.array(v["y"]), np.array(v["z"])], axis=1).astype(np.float32)
        opacity = 1.0 / (1.0 + np.exp(-np.array(v["opacity"], dtype=np.float64)))

        idx = np.floor((xyz - lo) / VOXEL_SIZE).astype(np.int64)
        inb = ((idx >= 0) & (idx < dims[None, :])).all(axis=1)
        zero_ray = np.zeros(len(xyz), dtype=bool)
        zero_ray[inb] = ~visited[idx[inb, 0], idx[inb, 1], idx[inb, 2]]
        zero_ray[~inb] = True   # outside the grid entirely -> definitely never observed

        n = len(xyz)
        nz = int(zero_ray.sum())
        op_zero = opacity[zero_ray]
        n_visible_01 = int((op_zero > 0.1).sum())
        n_visible_05 = int((op_zero > 0.5).sum())
        print(f"{name:<55} {n:>10,} {nz:>11,} {100*nz/n:>9.2f}% {n_visible_01:>9,} {n_visible_05:>8,}")


if __name__ == "__main__":
    main()
