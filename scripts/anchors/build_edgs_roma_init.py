#!/usr/bin/env python3
"""
build_edgs_roma_init.py — exp44c
================================
EDGS 방법론 실전 적용: RoMA dense correspondence를 keyframe 쌍에서 추출,
SLAM pose로 삼각측량해 기하 검증된 dense init을 생성.

- 쌍 선택: depth 캐시가 있는 57개 keyframe을 시간순으로 인접쌍 연결 (+선택적 stride 쌍)
- RoMA(outdoor) 매칭 → certainty 상위 샘플 → cv2 삼각측량 → reprojection 오차 필터
- voxel dedupe + carve 재필터 + 색(매칭 픽셀 색)
- 출력: results/datasets/orb_edgs_roma_scene

GPU 필요 (RoMA 추론). 실행: conda env 3dgs.
"""
import numpy as np
import shutil
import sys
from pathlib import Path

import cv2
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "analysis"))
from design_floater_loss_candidates import (
    BASE, VOXEL, load_slam, load_cameras, FX, FY, CX, CY, IMG_W, IMG_H)
from scipy.spatial import cKDTree
from scipy.ndimage import uniform_filter

IMGDIR = Path("data/03_rgb_3dgs_full/images")
DEPTH_DIR = Path("results/diagnostic/depth_maps_neworb_301_1253/depth_pro")
DST = Path("results/datasets/orb_edgs_roma_scene")
SRC = Path("results/datasets/orb_dense_confmono_init_scene")
N_SAMPLE_PER_PAIR = 6000
CERT_TH = 0.5
REPROJ_TH = 2.0   # px


def main():
    from romatch import roma_outdoor
    device = "cuda"
    model = roma_outdoor(device=device, use_custom_corr=False)  # local_corr CUDA ext 미설치 — torch 폴백

    Rs, ts = load_cameras()
    img_paths = sorted(IMGDIR.glob("*.jpg"))
    name2idx = {p.stem: i for i, p in enumerate(img_paths)}
    kf_ids = sorted(name2idx[f.stem] for f in DEPTH_DIR.glob("*.npy") if f.stem in name2idx)
    pairs = list(zip(kf_ids[:-1], kf_ids[1:]))
    print(f"keyframes {len(kf_ids)}, pairs {len(pairs)}")

    K = np.array([[FX, 0, CX], [0, FY, CY], [0, 0, 1]])
    all_pts, all_rgb = [], []
    for pi, (ia, ib) in enumerate(pairs):
        imA_p, imB_p = str(img_paths[ia]), str(img_paths[ib])
        warp, certainty = model.match(imA_p, imB_p, device=device)
        matches, cert = model.sample(warp, certainty, num=N_SAMPLE_PER_PAIR)
        kptsA, kptsB = model.to_pixel_coordinates(matches, IMG_H, IMG_W, IMG_H, IMG_W)
        kptsA = kptsA.cpu().numpy(); kptsB = kptsB.cpu().numpy()
        cert = cert.cpu().numpy()
        m = cert > CERT_TH
        if m.sum() < 50:
            continue
        kptsA, kptsB = kptsA[m], kptsB[m]
        # 삼각측량 (P = K [R|t], world->cam)
        PA = K @ np.hstack([Rs[ia], ts[ia][:, None]])
        PB = K @ np.hstack([Rs[ib], ts[ib][:, None]])
        X4 = cv2.triangulatePoints(PA, PB, kptsA.T.astype(np.float64), kptsB.T.astype(np.float64))
        X = (X4[:3] / np.clip(X4[3], 1e-9, None)).T
        # 유효성: 양의 깊이 + reprojection 오차
        def reproj_ok(Xw, R, t, kp):
            pc = Xw @ R.T + t
            z = pc[:, 2]
            u = pc[:, 0] / np.clip(z, 1e-9, None) * FX + CX
            v = pc[:, 1] / np.clip(z, 1e-9, None) * FY + CY
            err = np.hypot(u - kp[:, 0], v - kp[:, 1])
            return (z > 0.3) & (z < 12) & (err < REPROJ_TH)
        ok = reproj_ok(X, Rs[ia], ts[ia], kptsA) & reproj_ok(X, Rs[ib], ts[ib], kptsB)
        if ok.sum() == 0:
            continue
        X = X[ok]
        imA = np.asarray(Image.open(imA_p))
        c = imA[np.clip(kptsA[ok, 1].astype(int), 0, IMG_H - 1),
                np.clip(kptsA[ok, 0].astype(int), 0, IMG_W - 1)]
        all_pts.append(X.astype(np.float32))
        all_rgb.append(c.astype(np.uint8))
        if pi % 10 == 0:
            print(f"  pair {pi}/{len(pairs)}: kept {ok.sum()}", flush=True)

    pts = np.concatenate(all_pts); rgb = np.concatenate(all_rgb)
    print(f"raw 삼각측량 점: {len(pts):,}")
    key = np.floor(pts / 0.03).astype(np.int64)
    _, uidx = np.unique(key, axis=0, return_index=True)
    pts, rgb = pts[uidx], rgb[uidx]
    print(f"3cm dedupe 후: {len(pts):,}")

    # carve 재필터
    z0 = np.load(BASE / "carve_fields.npz")
    ts2 = uniform_filter(z0["transit"], 3); es2 = uniform_filter(z0["terminal"], 3)
    ratio = ts2 / (ts2 + 3 * es2 + 1e-6); lo = z0["lo"]; dims = z0["dims"]
    gi = np.floor((pts - lo) / VOXEL).astype(np.int64)
    inb = ((gi >= 0) & (gi < dims[None, :])).all(1)
    rho = np.zeros(len(pts), np.float32); rho[inb] = ratio[gi[inb, 0], gi[inb, 1], gi[inb, 2]]
    slam = load_slam()
    d5, _ = cKDTree(slam).query(pts, k=5, workers=-1)
    w = rho * np.clip(d5.mean(1) / 0.25, 0, 1)
    keep = w <= 0.5
    pts, rgb = pts[keep], rgb[keep]
    print(f"carve 재필터 후: {len(pts):,}")

    slam_rgb = np.full((len(slam), 3), 128, np.uint8)
    pts = np.concatenate([slam, pts]); rgb = np.concatenate([slam_rgb, rgb])
    DST.mkdir(parents=True, exist_ok=True); (DST / "sparse/0").mkdir(parents=True, exist_ok=True)
    if not (DST / "images").exists():
        (DST / "images").symlink_to((SRC / "images").resolve())
    for f in ("cameras.txt", "images.txt"):
        shutil.copy(SRC / f"sparse/0/{f}", DST / f"sparse/0/{f}")
    with open(DST / "sparse/0/points3D.txt", "w") as fo:
        for i, (p, c) in enumerate(zip(pts, rgb)):
            fo.write(f"{i} {p[0]:.6f} {p[1]:.6f} {p[2]:.6f} {c[0]} {c[1]} {c[2]} 0\n")
    print(f"최종 EDGS init {len(pts):,} → {DST}")


if __name__ == "__main__":
    main()
