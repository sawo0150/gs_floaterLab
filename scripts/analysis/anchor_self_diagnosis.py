#!/usr/bin/env python3
"""anchor_self_diagnosis.py — 라벨 없는 앵커 소스 자가진단 (exp43 우선순위 ①).

새 장면에서 carve field의 앵커 소스를 자동 선택하는 2규칙:
  1. SLAM 자기 NN p50 < 0.05m  → SLAM 앵커 (지도가 표면을 촘촘히 덮음)
  2. 아니면 depth 교차프레임 불일치 p50 < 0.04 → depth-pro 앵커
  3. 둘 다 실패 → 문제 클래스 경고 (예: fog/저텍스처 — 12F)

검증(2026-07-13, 4장면): 1253→SLAM(0.976), rot→SLAM(0.972, depth였으면 0.851),
305→depth(0.886, SLAM이면 0.770), 12F→경고(둘 다 0.82-0.84). 4/4 일치.

사용: python anchor_self_diagnosis.py --scene 301_305
     (data/scenes/<scene>/03_rgb_3dgs + results/diagnostic/depth_maps_<scene>/depth_pro 필요.
      depth 캐시 없으면 규칙 1만 판정)
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from sklearn.linear_model import HuberRegressor

sys.path.insert(0, str(Path(__file__).parent))
from build_scene_carve_and_pseudolabel import load_cams, load_pts
from design_floater_loss_candidates import FX, FY, CX, CY, IMG_W, IMG_H

LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
SLAM_NN_TH = 0.05      # m
DEPTH_INCONS_TH = 0.04  # 상대 깊이


def calib(depth, R, t, slam):
    pc = slam @ R.T + t
    z = pc[:, 2]
    ok = (z > 0.3) & (z < 12)
    u = pc[:, 0] / np.clip(z, 1e-6, None) * FX + CX
    v = pc[:, 1] / np.clip(z, 1e-6, None) * FY + CY
    ok &= (u >= 1) & (u < IMG_W - 1) & (v >= 1) & (v < IMG_H - 1)
    if ok.sum() < 10:
        return None
    zm = depth[v[ok].astype(int), u[ok].astype(int)]
    g = (zm > 0.1) & (zm < 20)
    if g.sum() < 10:
        return None
    reg = HuberRegressor(epsilon=1.35, max_iter=500).fit(zm[g, None], z[ok][g])
    return np.maximum(reg.coef_[0] * depth + reg.intercept_, 0.15)


def slam_self_nn(slam):
    return float(np.median(cKDTree(slam).query(slam, k=2, workers=-1)[0][:, 1]))


def depth_cross_inconsistency(scene, Rs, ts, slam, max_pairs=15):
    base = LAB / "data/scenes" / scene / "03_rgb_3dgs/sparse/0"
    names = [l.split()[9] for l in open(base / "images.txt")
             if len(l.split()) >= 10 and not l.startswith("#")]
    n2c = {Path(n).stem: i for i, n in enumerate(names)}
    files = [f for f in sorted((LAB / f"results/diagnostic/depth_maps_{scene}/depth_pro").glob("*.npy"))
             if f.stem in n2c]
    if len(files) < 3:
        return None
    incons = []
    for k in range(0, min(len(files) - 2, max_pairs * 2), 2):
        fa, fb = files[k], files[k + 2]
        ca, cb = n2c[fa.stem], n2c[fb.stem]
        da = calib(np.load(fa).astype(np.float32), Rs[ca], ts[ca], slam)
        db = calib(np.load(fb).astype(np.float32), Rs[cb], ts[cb], slam)
        if da is None or db is None:
            continue
        gy, gx = np.mgrid[8:IMG_H:16, 8:IMG_W:16]
        gy, gx = gy.ravel(), gx.ravel()
        zc = da[gy, gx]
        keep = (zc > 0.3) & (zc < 12)
        xc = (gx[keep] - CX) / FX * zc[keep]
        yc = (gy[keep] - CY) / FY * zc[keep]
        Pw = (np.stack([xc, yc, zc[keep]], 1) - ts[ca]) @ Rs[ca]
        pc = Pw @ Rs[cb].T + ts[cb]
        z2 = pc[:, 2]
        ok = (z2 > 0.3) & (z2 < 12)
        u2 = pc[:, 0] / np.clip(z2, 1e-6, None) * FX + CX
        v2 = pc[:, 1] / np.clip(z2, 1e-6, None) * FY + CY
        ok &= (u2 >= 0) & (u2 < IMG_W) & (v2 >= 0) & (v2 < IMG_H)
        if ok.sum() < 100:
            continue
        zb = db[v2[ok].astype(int), u2[ok].astype(int)]
        incons.append(np.median(np.abs(z2[ok] - zb) / np.clip(zb, 0.3, None)))
    return float(np.median(incons)) if incons else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    args = ap.parse_args()
    base = LAB / "data/scenes" / args.scene / "03_rgb_3dgs/sparse/0"
    Rs, ts = load_cams(base / "images.txt")
    slam = load_pts(base / "points3D.txt")

    nn = slam_self_nn(slam)
    print(f"[규칙1] SLAM 자기 NN p50 = {nn:.3f}m (문턱 {SLAM_NN_TH})")
    if nn < SLAM_NN_TH:
        print("→ 판정: SLAM 앵커 사용")
        return
    inc = depth_cross_inconsistency(args.scene, Rs, ts, slam)
    if inc is None:
        print("→ 판정 보류: depth 캐시 없음 — inference_depthpro_scene.py 먼저 실행")
        return
    print(f"[규칙2] depth 교차프레임 불일치 p50 = {inc:.4f} (문턱 {DEPTH_INCONS_TH})")
    if inc < DEPTH_INCONS_TH:
        print("→ 판정: depth-pro 앵커 사용 (build_depth_anchor_field.py)")
    else:
        print("→ 판정: ⚠ 문제 클래스 — SLAM 희소 + depth 불안정. 두 앵커 모두 신뢰 불가")


if __name__ == "__main__":
    main()
