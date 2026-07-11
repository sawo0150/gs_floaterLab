#!/usr/bin/env python3
"""
build_mps_carve_field.py
========================
MPS 트랙(exp08~29 데이터셋)용 carve field 사전 구축.
- ray 타깃: 626,811 semidense를 10cm voxel 다운샘플 (대표점)
- d5 anchor: 전체 626k 유지 (KDTree는 소비자가 로드)
- 출력: results/diagnostic/mps_carve_field.npz (transit, terminal, lo, dims)

카메라 절반(stride 2)만 사용 — free-space 증거는 중복이 많아 손실 미미.
"""
import numpy as np
from pathlib import Path
import sys, time

sys.path.insert(0, str(Path(__file__).parent))
from design_floater_loss_candidates import (
    VOXEL, RAY_STEP, SURF_MARGIN, MIN_T, IMG_W, IMG_H, FX, FY, CX, CY, qvec2rotmat)

MPS = Path("/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253")
OUT = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic/mps_carve_field.npz")
CAM_STRIDE = 2
TARGET_VOXEL = 0.10


def load_cams():
    Rs, ts = [], []
    for line in open(MPS / "sparse/0/images.txt"):
        p = line.strip().split()
        if len(p) < 9 or p[0].startswith("#"):
            continue
        Rs.append(qvec2rotmat(np.array([float(x) for x in p[1:5]])))
        ts.append(np.array([float(x) for x in p[5:8]]))
    return np.array(Rs, np.float32), np.array(ts, np.float32)


def load_pts():
    pts = []
    for line in open(MPS / "sparse/0/points3D.txt"):
        if line.startswith("#") or not line.strip():
            continue
        t = line.split()
        if len(t) >= 7:
            pts.append([float(t[1]), float(t[2]), float(t[3])])
    return np.array(pts, np.float32)


def voxel_downsample(pts, size):
    key = np.floor(pts / size).astype(np.int64)
    _, idx = np.unique(key, axis=0, return_index=True)
    return pts[idx]


def main():
    t0 = time.time()
    Rs, ts = load_cams()
    pts_full = load_pts()
    targets = voxel_downsample(pts_full, TARGET_VOXEL)
    print(f"cams {len(Rs)} (stride {CAM_STRIDE}) | pts {len(pts_full):,} → targets {len(targets):,}")

    centers = np.stack([-R.T @ t for R, t in zip(Rs, ts)]).astype(np.float32)
    lo = centers.min(0) - np.maximum(centers.max(0) - centers.min(0), [2., 2., 3.])
    hi = centers.max(0) + np.maximum(centers.max(0) - centers.min(0), [2., 2., 3.])
    dims = np.ceil((hi - lo) / VOXEL).astype(int) + 1
    n_vox = int(np.prod(dims))
    transit = np.zeros(n_vox, np.float32)
    terminal = np.zeros(n_vox, np.float32)
    max_steps = int(15.0 / RAY_STEP)
    step_d = np.arange(max_steps, dtype=np.float32) * RAY_STEP + MIN_T

    def deposit(p, acc):
        idx = np.floor((p - lo) / VOXEL).astype(np.int64)
        inb = ((idx >= 0) & (idx < dims[None, :])).all(1)
        idx = idx[inb]
        flat = (idx[:, 0] * dims[1] + idx[:, 1]) * dims[2] + idx[:, 2]
        acc += np.bincount(flat, minlength=n_vox).astype(np.float32)

    for ci in range(0, len(Rs), CAM_STRIDE):
        R, t = Rs[ci], ts[ci]
        C = (-R.T @ t).astype(np.float32)
        pc = targets @ R.T + t
        z = pc[:, 2]
        ok = z > 0.2
        u = pc[:, 0] / np.clip(z, 1e-6, None) * FX + CX
        v = pc[:, 1] / np.clip(z, 1e-6, None) * FY + CY
        ok &= (u >= 0) & (u < IMG_W) & (v >= 0) & (v < IMG_H) & (z < 15.0)
        P = targets[ok]
        if len(P) == 0:
            continue
        dvec = P - C
        dist = np.linalg.norm(dvec, axis=1)
        dirs = dvec / dist[:, None]
        valid = step_d[None, :] < (dist - SURF_MARGIN)[:, None]
        p = C[None, None, :] + step_d[None, :, None] * dirs[:, None, :]
        deposit(p[valid], transit)
        off = np.linspace(-SURF_MARGIN, SURF_MARGIN, 5, dtype=np.float32)
        tp = C[None, None, :] + (dist[:, None] + off[None, :])[:, :, None] * dirs[:, None, :]
        deposit(tp.reshape(-1, 3), terminal)
        if ci % 100 == 0:
            print(f"  cam {ci}/{len(Rs)}  ({time.time()-t0:.0f}s)", flush=True)

    np.savez_compressed(OUT, transit=transit.reshape(tuple(dims)),
                        terminal=terminal.reshape(tuple(dims)), lo=lo, dims=dims)
    print(f"[saved] {OUT}  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
