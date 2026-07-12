#!/usr/bin/env python3
"""
build_scene_carve_and_pseudolabel.py
====================================
임의 장면(data/scenes/<name>)에 대해:
 1. 그 장면의 카메라+SLAM 포인트로 carve field(transit/terminal) 구축 → carve_field.npz
 2. baseline ply에 champion score + 예산 top-K 추출 → pseudo-label
    (floater_mask.npy, floaters_only.ply, point_cloud_cleaned.ply)

1253 트랙과 동일 설계값 (voxel 0.1, d5_tau 0.25, maxop 5cm, score_min 0.3).

사용:
  python build_scene_carve_and_pseudolabel.py --scene 301_1253_rot \
      --ply <baseline>/point_cloud/iteration_30000/point_cloud.ply [--budget 0.015]
"""
import argparse
import json
from pathlib import Path

import numpy as np
from plyfile import PlyData, PlyElement
from scipy.spatial import cKDTree
from scipy.ndimage import uniform_filter
import sys

sys.path.insert(0, str(Path(__file__).parent))
from design_floater_loss_candidates import (
    VOXEL, RAY_STEP, SURF_MARGIN, MIN_T, IMG_W, IMG_H, FX, FY, CX, CY, qvec2rotmat)

LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
D5_TAU, MAXOP_R, SCORE_MIN = 0.25, 0.05, 0.3


def load_cams(images_txt):
    Rs, ts = [], []
    for line in open(images_txt):
        p = line.strip().split()
        if len(p) < 9 or p[0].startswith("#"):
            continue
        Rs.append(qvec2rotmat(np.array([float(x) for x in p[1:5]])))
        ts.append(np.array([float(x) for x in p[5:8]]))
    return np.array(Rs, np.float32), np.array(ts, np.float32)


def load_pts(points_txt):
    pts = []
    for line in open(points_txt):
        if line.startswith("#") or not line.strip():
            continue
        t = line.split()
        if len(t) >= 7:
            pts.append([float(t[1]), float(t[2]), float(t[3])])
    return np.array(pts, np.float32)


def build_field(Rs, ts, slam, lo, dims):
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

    for R, t in zip(Rs, ts):
        C = (-R.T @ t).astype(np.float32)
        pc = slam @ R.T + t
        z = pc[:, 2]
        ok = z > 0.2
        u = pc[:, 0] / np.clip(z, 1e-6, None) * FX + CX
        v = pc[:, 1] / np.clip(z, 1e-6, None) * FY + CY
        ok &= (u >= 0) & (u < IMG_W) & (v >= 0) & (v < IMG_H) & (z < 15.0)
        P = slam[ok]
        if len(P) == 0:
            continue
        dvec = P - C
        dist = np.linalg.norm(dvec, axis=1)
        dirs = dvec / dist[:, None]
        valid = step_d[None, :] < (dist - SURF_MARGIN)[:, None]
        pts = C[None, None, :] + step_d[None, :, None] * dirs[:, None, :]
        deposit(pts[valid], transit)
        off = np.linspace(-SURF_MARGIN, SURF_MARGIN, 5, dtype=np.float32)
        tp = C[None, None, :] + (dist[:, None] + off[None, :])[:, :, None] * dirs[:, None, :]
        deposit(tp.reshape(-1, 3), terminal)
    return transit.reshape(tuple(dims)), terminal.reshape(tuple(dims))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--ply", required=True)
    ap.add_argument("--budget", type=float, default=0.015)
    args = ap.parse_args()

    base = LAB / "data/scenes" / args.scene / "03_rgb_3dgs/sparse/0"
    field_path = LAB / "data/scenes" / args.scene / "carve_field.npz"

    Rs, ts = load_cams(base / "images.txt")
    slam = load_pts(base / "points3D.txt")

    if field_path.exists():
        z = np.load(field_path)
        transit, terminal, lo, dims = z["transit"], z["terminal"], z["lo"], z["dims"]
        print(f"[field] cached: {field_path}")
    else:
        centers = np.stack([-R.T @ t for R, t in zip(Rs, ts)]).astype(np.float32)
        lo = centers.min(0) - np.maximum(centers.max(0) - centers.min(0), [2., 2., 3.])
        hi = centers.max(0) + np.maximum(centers.max(0) - centers.min(0), [2., 2., 3.])
        dims = np.ceil((hi - lo) / VOXEL).astype(int) + 1
        print(f"[field] building: cams {len(Rs)}, slam {len(slam):,}, grid {tuple(dims)}")
        transit, terminal = build_field(Rs, ts, slam, lo, dims)
        np.savez_compressed(field_path, transit=transit, terminal=terminal, lo=lo, dims=dims)
        print(f"[field] saved → {field_path}")

    ts_ = uniform_filter(transit, 3)
    es_ = uniform_filter(terminal, 3)
    ratio = ts_ / (ts_ + 3.0 * es_ + 1e-6)

    v = PlyData.read(args.ply)["vertex"]
    xyz = np.stack([np.asarray(v[k]) for k in "xyz"], 1).astype(np.float32)
    opac = 1 / (1 + np.exp(-np.asarray(v["opacity"], dtype=np.float64)))
    scales = np.exp(np.stack([np.asarray(v[f"scale_{i}"]) for i in range(3)], 1).astype(np.float64))
    try:
        visn = np.clip(np.asarray(v["accum_visibility"]).astype(np.float64), 1, None)
    except Exception:
        visn = np.ones(len(xyz))
    contrib = opac * np.sort(scales, 1)[:, 1:].prod(1) * visn

    gi = np.floor((xyz - lo) / VOXEL).astype(np.int64)
    inb = ((gi >= 0) & (gi < np.array(dims)[None, :])).all(1)
    rho = np.zeros(len(xyz), np.float32)
    rho[inb] = ratio[gi[inb, 0], gi[inb, 1], gi[inb, 2]]
    d5, _ = cKDTree(slam).query(xyz, k=5, workers=-1)
    w = rho * np.clip(d5.mean(1) / D5_TAU, 0, 1)
    pairs = cKDTree(xyz).query_ball_point(xyz, MAXOP_R, workers=-1, return_sorted=False)
    maxop = np.fromiter((opac[p].max() for p in pairs), dtype=np.float64, count=len(xyz))
    s = w * (1.0 - maxop)

    order = np.argsort(-s)
    eligible = s[order] > SCORE_MIN
    csum = np.cumsum(np.where(eligible, contrib[order], 0)) / contrib.sum()
    k = int((eligible & (csum <= args.budget)).sum())
    mask = np.zeros(len(xyz), bool)
    mask[order[:k]] = True

    out = Path(args.ply).parent / "pseudo_labels"
    out.mkdir(exist_ok=True)
    np.save(out / "floater_mask.npy", mask)
    PlyData([PlyElement.describe(v.data[~mask], "vertex")]).write(str(out / "point_cloud_cleaned.ply"))
    PlyData([PlyElement.describe(v.data[mask], "vertex")]).write(str(out / "floaters_only.ply"))
    rep = {"scene": args.scene, "ply": args.ply, "budget": args.budget,
           "n_total": len(xyz), "n_pseudo_floaters": int(mask.sum()),
           "visible(op>0.3)": int((mask & (opac > 0.3)).sum()),
           "contrib_pct": float(contrib[mask].sum() / contrib.sum() * 100)}
    json.dump(rep, open(out / "report.json", "w"), indent=2, ensure_ascii=False)
    print(f"[pseudo-label] {rep['n_pseudo_floaters']:,}개 (가시 {rep['visible(op>0.3)']:,}, "
          f"기여 {rep['contrib_pct']:.2f}%) → {out}")


if __name__ == "__main__":
    main()
