#!/usr/bin/env python3
"""Does the anchor's ellipsoidal plateau region overlap with never-ray-visited
space? Rebuilds the same ray-visited voxel grid as check_gaussian_ray_coverage.py,
then for every voxel no ray ever visited, checks whether it falls inside each
anchor-set/tau-config's plateau (D<=1, same ellipsoid formula as
eval/plateau_loss.py). If enlarged tau's plateau reaches into unvisited space,
that explains why it pulls Gaussians into floater habitat (see
check_gaussian_ray_coverage.py's opacity-weighted floater counts).
"""
import numpy as np
from pathlib import Path
from sklearn.neighbors import NearestNeighbors

DATASET = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full")
IMG_TXT = DATASET / "sparse/0/images.txt"
IMG_W, IMG_H = 1024, 1024
FX, FY, CX, CY = 500.0, 500.0, 511.5, 511.5
VOXEL_SIZE = 0.15
PIXEL_STEP = 48
MAX_DEPTH = 15.0
DEPTH_STEP = 0.15

GENERAL_ANCHOR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic/native_anchors_neworb_v4_20260709_204706/anchors_all_depth_pro.npy"
HIGHCONF_ANCHOR = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic/native_anchors_neworb_highconf_20260709_205327/anchors_all_depth_pro.npy"
BASE_TAU = dict(alpha_n=0.4, alpha_t=0.9, tau_min=0.03, tau_n_max=0.30, tau_t_max=0.60)
BIG_TAU  = dict(alpha_n=0.8, alpha_t=1.8, tau_min=0.03, tau_n_max=0.80, tau_t_max=2.00)
KNN_K = 5


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


def compute_ellipsoid(pts, inds, h_j, alpha_n, alpha_t, tau_min, tau_n_max, tau_t_max):
    N = len(pts)
    tau_n = np.clip(alpha_n * h_j, tau_min, tau_n_max).astype(np.float32)
    tau_t = np.clip(alpha_t * h_j, tau_min, tau_t_max).astype(np.float32)
    frames = np.empty((N, 3, 3), dtype=np.float32)
    for i in range(N):
        neigh = pts[inds[i, 1:KNN_K + 1]]
        X = neigh - neigh.mean(0)
        cov = (X.T @ X) / max(KNN_K - 1, 1)
        _, evec = np.linalg.eigh(cov)
        frames[i] = np.stack([evec[:, 1], evec[:, 2], evec[:, 0]], axis=1)
    return tau_n, tau_t, frames


def d_min_to_anchors(x, anchors, frames, tau_n, tau_t, chunk=256):
    Q = x.shape[0]
    M = anchors.shape[0]
    D_min = np.full(Q, np.inf, dtype=np.float32)
    for s in range(0, M, chunk):
        a, fr, tn, tt = anchors[s:s+chunk], frames[s:s+chunk], tau_n[s:s+chunk], tau_t[s:s+chunk]
        delta = x[:, None, :] - a[None, :, :]
        c = np.einsum("cjk,qcj->qck", fr, delta)
        d2 = (c[..., 0]/tt)**2 + (c[..., 1]/tt)**2 + (c[..., 2]/tn)**2
        D_min = np.minimum(D_min, np.sqrt(d2).min(axis=1))
    return D_min


def main():
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
    n_unvisited = int(dims.prod() - n_visited)
    print(f"[done] visited={n_visited:,}  unvisited={n_unvisited:,} ({100*n_unvisited/dims.prod():.1f}%)")

    unv_idx = np.argwhere(~visited)
    unv_centers = lo[None, :] + (unv_idx + 0.5) * VOXEL_SIZE
    print(f"unvisited voxel centers: {len(unv_centers):,}")

    configs = [
        ("general anchor (7,108) / base tau",      GENERAL_ANCHOR,  BASE_TAU),
        ("general anchor (7,108) / enlarged tau",  GENERAL_ANCHOR,  BIG_TAU),
        ("highconf anchor (1,438) / base tau",     HIGHCONF_ANCHOR, BASE_TAU),
        ("highconf anchor (1,438) / enlarged tau", HIGHCONF_ANCHOR, BIG_TAU),
    ]

    _cache = {}
    print(f"\n{'Config':<42} {'unvisited voxels inside plateau':>32} {'%':>8}")
    for label, anchor_path, tau_cfg in configs:
        if anchor_path not in _cache:
            anchors = np.load(anchor_path).astype(np.float32)
            nbrs = NearestNeighbors(n_neighbors=KNN_K + 1, algorithm="ball_tree").fit(anchors)
            dists, inds = nbrs.kneighbors(anchors)
            h_j = dists[:, KNN_K].astype(np.float32)
            _cache[anchor_path] = (anchors, inds, h_j)
        anchors, inds, h_j = _cache[anchor_path]
        tau_n, tau_t, frames = compute_ellipsoid(anchors, inds, h_j, **tau_cfg)
        D = d_min_to_anchors(unv_centers.astype(np.float32), anchors, frames, tau_n, tau_t)
        inside = int((D <= 1.0).sum())
        print(f"{label:<42} {inside:>32,} {100*inside/len(unv_centers):>7.2f}%")


if __name__ == "__main__":
    main()
