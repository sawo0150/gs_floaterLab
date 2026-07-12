#!/usr/bin/env python3
"""depth-anchor carve — exp43 305 처방.

ORB 지도가 표면을 못 덮는 장면에서 depth-pro 표면 앵커로 carve 재료를 재구성:
  1. depth 프레임별 SLAM 점으로 스케일 보정(Huber) → 픽셀 grid 역투영 = 표면 앵커
  2. 앵커를 ray 목표로 transit/terminal 필드 재구축 (depth 프레임 카메라만 사용)
  3. 출력: data/scenes/<scene>/depth_anchors.npz (+ points3D 포맷 txt, CarveLoss points_txt용)

사용: python build_depth_anchor_field.py --scene 301_305
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from sklearn.linear_model import HuberRegressor

sys.path.insert(0, str(Path(__file__).parent))
from design_floater_loss_candidates import (
    VOXEL, IMG_W, IMG_H, FX, FY, CX, CY)
from build_scene_carve_and_pseudolabel import load_cams, load_pts, build_field

LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
PX_STRIDE = 8           # 앵커용 픽셀 grid (128×128/frame)
FIELD_SUBSAMPLE = 6000  # 필드 ray용 프레임당 앵커 수


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    args = ap.parse_args()

    base = LAB / "data/scenes" / args.scene / "03_rgb_3dgs/sparse/0"
    depth_dir = LAB / f"results/diagnostic/depth_maps_{args.scene}/depth_pro"
    Rs, ts = load_cams(base / "images.txt")
    slam = load_pts(base / "points3D.txt")

    # images.txt 순서 = 이미지 이름 순서 (frame_XXXXX)
    names = []
    for line in open(base / "images.txt"):
        p = line.strip().split()
        if len(p) >= 10 and not p[0].startswith("#"):
            names.append(Path(p[9]).stem)
    name2ci = {n: i for i, n in enumerate(names)}

    gy, gx = np.mgrid[PX_STRIDE // 2:IMG_H:PX_STRIDE, PX_STRIDE // 2:IMG_W:PX_STRIDE]
    gy, gx = gy.ravel(), gx.ravel()

    anchors, field_pts, cam_sel = [], [], []
    for df in sorted(depth_dir.glob("*.npy")):
        ci = name2ci.get(df.stem)
        if ci is None:
            continue
        depth = np.load(df).astype(np.float32)
        R, t = Rs[ci], ts[ci]
        # SLAM 점으로 depth 스케일 보정
        pc = slam @ R.T + t
        z = pc[:, 2]
        ok = (z > 0.3) & (z < 12)
        u = pc[:, 0] / np.clip(z, 1e-6, None) * FX + CX
        v = pc[:, 1] / np.clip(z, 1e-6, None) * FY + CY
        ok &= (u >= 1) & (u < IMG_W - 1) & (v >= 1) & (v < IMG_H - 1)
        if ok.sum() < 10:
            continue
        zm = depth[v[ok].astype(int), u[ok].astype(int)]
        good = (zm > 0.1) & (zm < 20)
        if good.sum() < 10:
            continue
        reg = HuberRegressor(epsilon=1.35, max_iter=500).fit(zm[good, None], z[ok][good])
        depth_cal = np.maximum(reg.coef_[0] * depth + reg.intercept_, 0.15)

        zc = depth_cal[gy, gx]
        keep = (zc > 0.3) & (zc < 12)
        xc = (gx[keep] - CX) / FX * zc[keep]
        yc = (gy[keep] - CY) / FY * zc[keep]
        Pw = (np.stack([xc, yc, zc[keep]], 1) - t) @ R
        anchors.append(Pw.astype(np.float32))
        sub = np.random.default_rng(ci).choice(len(Pw), min(FIELD_SUBSAMPLE, len(Pw)), replace=False)
        field_pts.append(Pw[sub].astype(np.float32))
        cam_sel.append(ci)

    anchors = np.concatenate(anchors)
    key = np.floor(anchors / 0.05).astype(np.int64)
    _, uidx = np.unique(key, axis=0, return_index=True)
    anchors = anchors[uidx]
    print(f"[anchors] {len(anchors):,} (5cm dedupe, frames {len(cam_sel)})")

    # 필드: depth 프레임 카메라 각각이 자기 앵커로 ray (build_field 재사용 위해 union 사용)
    union = np.concatenate(field_pts)
    lo = union.min(0) - 1.0
    hi = union.max(0) + 1.0
    dims = np.ceil((hi - lo) / VOXEL).astype(int) + 1
    print(f"[field] cams {len(cam_sel)}, ray-target {len(union):,}, grid {tuple(dims)}")
    transit, terminal = build_field(Rs[cam_sel], ts[cam_sel], union, lo, dims)

    out = LAB / "data/scenes" / args.scene / "depth_anchors.npz"
    np.savez_compressed(out, anchors=anchors, transit=transit, terminal=terminal, lo=lo, dims=dims)
    with open(out.with_suffix(".points3D.txt"), "w") as fo:
        for i, p in enumerate(anchors):
            fo.write(f"{i} {p[0]:.6f} {p[1]:.6f} {p[2]:.6f} 128 128 128 0\n")
    print(f"[saved] {out}")


if __name__ == "__main__":
    main()
