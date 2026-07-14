#!/usr/bin/env python3
"""pixel_frustum_footprint.py — 장면별 '1px가 커버하는 물리 크기' 분포.

동기(사용자): 카메라에서 멀리 있는 floater는 1px여도 frustum이 벌어져 물리적으로 커 보인다.
  1px의 물리 footprint(한 변) = z / f  (f=500px). 깊이 z 분포가 곧 footprint 분포.
방이 크거나 먼 구조가 많은 305/12F는 같은 '1px floater'라도 물리적으로 더 클 수 있음 → Q1~Q3 로깅.

깊이 소스: depth-pro 맵을 프레임별 SLAM 점으로 Huber 보정(미터) → 픽셀 깊이 pool.
출력: context/rounds/round9_pixel_frustum.md
"""
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import HuberRegressor

LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
sys.path.insert(0, str(LAB / "scripts/analysis"))
from build_scene_carve_and_pseudolabel import load_cams, load_pts
from design_floater_loss_candidates import FX, FY, CX, CY, IMG_W, IMG_H

F = FX  # 500
PX_STRIDE = 6

SCENES = {
    "1253": ("data/03_rgb_3dgs_full/sparse/0",
             "results/diagnostic/depth_maps_neworb_301_1253/depth_pro"),
    "305":  ("data/scenes/301_305/03_rgb_3dgs/sparse/0",
             "results/diagnostic/depth_maps_301_305/depth_pro"),
    "12F":  ("data/scenes/301_12F/03_rgb_3dgs/sparse/0",
             "results/diagnostic/depth_maps_301_12F/depth_pro"),
}


def scene_depths(sparse, depth_dir, max_frames=60):
    base = LAB / sparse
    Rs, ts = load_cams(base / "images.txt")
    slam = load_pts(base / "points3D.txt")
    names = [l.split()[9] for l in open(base / "images.txt")
             if len(l.split()) >= 10 and not l.startswith("#")]
    n2c = {Path(n).stem: i for i, n in enumerate(names)}
    gy, gx = np.mgrid[0:IMG_H:PX_STRIDE, 0:IMG_W:PX_STRIDE]
    gy, gx = gy.ravel(), gx.ravel()
    pool = []
    files = sorted((LAB / depth_dir).glob("*.npy"))[:max_frames]
    for df in files:
        ci = n2c.get(df.stem)
        if ci is None:
            continue
        depth = np.load(df).astype(np.float32)
        R, t = Rs[ci], ts[ci]
        pc = slam @ R.T + t
        z = pc[:, 2]
        ok = (z > 0.3) & (z < 20)
        u = pc[:, 0] / np.clip(z, 1e-6, None) * FX + CX
        v = pc[:, 1] / np.clip(z, 1e-6, None) * FY + CY
        ok &= (u >= 1) & (u < IMG_W - 1) & (v >= 1) & (v < IMG_H - 1)
        if ok.sum() < 10:
            continue
        zm = depth[v[ok].astype(int), u[ok].astype(int)]
        g = (zm > 0.1) & (zm < 25)
        if g.sum() < 10:
            continue
        reg = HuberRegressor(epsilon=1.35, max_iter=500).fit(zm[g, None], z[ok][g])
        dc = np.maximum(reg.coef_[0] * depth + reg.intercept_, 0.15)
        zc = dc[gy, gx]
        zc = zc[(zc > 0.2) & (zc < 25)]
        pool.append(zc.astype(np.float32))
    return np.concatenate(pool), len(files)


def main():
    lines = []
    lines.append("# round9 — 장면별 1px frustum footprint (2026-07-14)\n")
    lines.append("**동기(사용자):** 멀리 있는 floater는 1px여도 frustum이 벌어져 물리적으로 커 보인다. "
                 "1px 물리 footprint(한 변) = 깊이 z / f (f=500px). 따라서 깊이 분포가 곧 footprint 분포.\n")
    lines.append("**방법:** depth-pro 맵을 프레임별 SLAM 점으로 Huber 보정(미터) → 6px stride 픽셀 깊이 pool → 분위수.\n")
    lines.append("| 장면 | 깊이 Q1 / 중앙 / Q3 (m) | 1px footprint Q1 / 중앙 / Q3 (mm) | p95 깊이 (m) | p95 footprint (mm) | 프레임·픽셀수 |")
    lines.append("|---|---|---|---|---|---|")
    print(f"{'장면':5} {'z Q1':>6} {'z Q2':>6} {'z Q3':>6} {'fp Q1':>7} {'fp Q2':>7} {'fp Q3':>7} (mm)")
    rows = {}
    for nm, (sp, dd) in SCENES.items():
        try:
            z, nf = scene_depths(sp, dd)
        except Exception as e:
            print(f"[FAIL] {nm}: {e}")
            continue
        q1, q2, q3, p95 = np.percentile(z, [25, 50, 75, 95])
        fp = lambda d: d / F * 1000.0  # mm
        rows[nm] = (q1, q2, q3, p95)
        print(f"{nm:5} {q1:6.2f} {q2:6.2f} {q3:6.2f} {fp(q1):7.1f} {fp(q2):7.1f} {fp(q3):7.1f}")
        lines.append(f"| **{nm}** | {q1:.2f} / {q2:.2f} / {q3:.2f} | "
                     f"{fp(q1):.1f} / {fp(q2):.1f} / {fp(q3):.1f} | {p95:.2f} | {fp(p95):.1f} | "
                     f"{nf}프레임·{len(z):,} |")
    # 상대 비교
    if "1253" in rows and rows:
        base_q3 = rows["1253"][2]
        lines.append("\n**상대 비교 (Q3 footprint, 1253=1.0):** " +
                     " · ".join(f"{k} {rows[k][2]/base_q3:.2f}×" for k in rows))
    lines.append("\n**해석:** footprint가 큰 장면일수록 '1px 먼지'가 물리적으로 커서, "
                 "같은 픽셀 오차라도 3D region 지표에서 더 큰 부피로 잡히고 시각적으로도 더 거슬림. "
                 "305/12F의 먼지 부피가 1253보다 크게 나오는 이유의 일부를 depth 스케일이 설명.")
    out = LAB / "context/rounds/round9_pixel_frustum.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"\n[saved] {out}")


if __name__ == "__main__":
    main()
