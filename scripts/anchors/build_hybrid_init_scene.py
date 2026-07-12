#!/usr/bin/env python3
"""build_hybrid_init_scene.py — exp43 hybrid init 이식 (44d2 챔피언 레시피의 범용판).

1253 전용 build_edgs_roma_init.py + PPM depth-lift + hybrid 병합을 장면 파라미터화:
  1. RoMA dense correspondence → 인접 keyframe 쌍 삼각측량 (기하 검증 reproj<2px)
  2. Sobel-PPM 가중 픽셀 샘플 → 보정 depth lift (frame당 4k)
  3. 병합: 4cm voxel에서 RoMA 우선 → carve/depth-anchor 재필터 → SLAM 점 합류
  4. 출력: data/scenes/<scene>/03_rgb_3dgs_hyb/ (images symlink + sparse/0)

사용: python build_hybrid_init_scene.py --scene 301_1253_rot
GPU 필요 (RoMA). depth 캐시(results/diagnostic/depth_maps_<scene>/depth_pro) 선행 필수.
"""
import argparse
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from scipy.spatial import cKDTree
from scipy.ndimage import uniform_filter
from sklearn.linear_model import HuberRegressor

sys.path.insert(0, str(Path(__file__).parent.parent / "analysis"))
from design_floater_loss_candidates import VOXEL, IMG_W, IMG_H, FX, FY, CX, CY
from build_scene_carve_and_pseudolabel import load_cams, load_pts

LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
N_SAMPLE_PER_PAIR = 6000
CERT_TH = 0.5
REPROJ_TH = 2.0
PPM_PTS_PER_FRAME = 4000


def calib_depth(depth, R, t, slam):
    pc = slam @ R.T + t
    z = pc[:, 2]
    ok = (z > 0.3) & (z < 12)
    u = pc[:, 0] / np.clip(z, 1e-6, None) * FX + CX
    v = pc[:, 1] / np.clip(z, 1e-6, None) * FY + CY
    ok &= (u >= 1) & (u < IMG_W - 1) & (v >= 1) & (v < IMG_H - 1)
    if ok.sum() < 10:
        return None
    zm = depth[v[ok].astype(int), u[ok].astype(int)]
    good = (zm > 0.1) & (zm < 20)
    if good.sum() < 10:
        return None
    reg = HuberRegressor(epsilon=1.35, max_iter=500).fit(zm[good, None], z[ok][good])
    return np.maximum(reg.coef_[0] * depth + reg.intercept_, 0.15)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--field", default="", help="재필터용 npz (기본: depth_anchors.npz → carve_field.npz 순)")
    ap.add_argument("--min-baseline", type=float, default=0.0,
                    help=">0이면 인접쌍 대신 카메라 중심 거리가 이 값 이상인 최근접 후속 keyframe과 쌍 구성 (회전 궤적 대책)")
    args = ap.parse_args()

    scene_dir = LAB / "data/scenes" / args.scene
    base = scene_dir / "03_rgb_3dgs/sparse/0"
    imgdir = scene_dir / "03_rgb_3dgs/images"
    depth_dir = LAB / f"results/diagnostic/depth_maps_{args.scene}/depth_pro"
    Rs, ts = load_cams(base / "images.txt")
    slam = load_pts(base / "points3D.txt")
    names = [l.split()[9] for l in open(base / "images.txt")
             if len(l.split()) >= 10 and not l.startswith("#")]
    name2ci = {Path(n).stem: i for i, n in enumerate(names)}
    kf = sorted((name2ci[f.stem], f) for f in depth_dir.glob("*.npy") if f.stem in name2ci)
    print(f"[{args.scene}] keyframes {len(kf)}")

    # ── 1. RoMA 삼각측량 ──
    from romatch import roma_outdoor
    device = "cuda"
    model = roma_outdoor(device=device, use_custom_corr=False)
    K = np.array([[FX, 0, CX], [0, FY, CY], [0, 0, 1]])
    # 쌍 구성: 기본 인접쌍 / min_baseline>0이면 시차 보장 쌍 (작은 시차 삼각측량 오류 대책)
    centers = np.stack([-R.T @ t for R, t in zip(Rs, ts)])
    if args.min_baseline > 0:
        pairs_idx = []
        for pi in range(len(kf)):
            for pj in range(pi + 1, len(kf)):
                if np.linalg.norm(centers[kf[pj][0]] - centers[kf[pi][0]]) >= args.min_baseline:
                    pairs_idx.append((pi, pj))
                    break
        print(f"[pairs] min_baseline {args.min_baseline}m → {len(pairs_idx)}쌍 "
              f"(시차 p50 {np.median([np.linalg.norm(centers[kf[j][0]]-centers[kf[i][0]]) for i,j in pairs_idx]):.2f}m)")
    else:
        pairs_idx = [(pi, pi + 1) for pi in range(len(kf) - 1)]
    roma_pts, roma_rgb = [], []
    for pi, pj in pairs_idx:
        (ia, fa), (ib, fb) = kf[pi], kf[pj]
        pa, pb = str(imgdir / names[ia]), str(imgdir / names[ib])
        warp, certainty = model.match(pa, pb, device=device)
        matches, cert = model.sample(warp, certainty, num=N_SAMPLE_PER_PAIR)
        kA, kB = model.to_pixel_coordinates(matches, IMG_H, IMG_W, IMG_H, IMG_W)
        kA = kA.cpu().numpy(); kB = kB.cpu().numpy(); cert = cert.cpu().numpy()
        m = cert > CERT_TH
        if m.sum() < 50:
            continue
        kA, kB = kA[m], kB[m]
        PA = K @ np.hstack([Rs[ia], ts[ia][:, None]])
        PB = K @ np.hstack([Rs[ib], ts[ib][:, None]])
        X4 = cv2.triangulatePoints(PA, PB, kA.T.astype(np.float64), kB.T.astype(np.float64))
        X = (X4[:3] / np.clip(X4[3], 1e-9, None)).T

        def rp_ok(Xw, R, t, kp):
            pc = Xw @ R.T + t
            z = pc[:, 2]
            u = pc[:, 0] / np.clip(z, 1e-9, None) * FX + CX
            v = pc[:, 1] / np.clip(z, 1e-9, None) * FY + CY
            return (z > 0.3) & (z < 12) & (np.hypot(u - kp[:, 0], v - kp[:, 1]) < REPROJ_TH)
        ok = rp_ok(X, Rs[ia], ts[ia], kA) & rp_ok(X, Rs[ib], ts[ib], kB)
        if ok.sum() == 0:
            continue
        im = np.asarray(Image.open(pa))
        c = im[np.clip(kA[ok, 1].astype(int), 0, IMG_H - 1), np.clip(kA[ok, 0].astype(int), 0, IMG_W - 1)]
        roma_pts.append(X[ok].astype(np.float32)); roma_rgb.append(c.astype(np.uint8))
        if pi % 10 == 0:
            print(f"  roma pair {pi}/{len(kf)-1}: {ok.sum()}", flush=True)
    roma_pts = np.concatenate(roma_pts); roma_rgb = np.concatenate(roma_rgb)
    print(f"[roma] {len(roma_pts):,}")

    # ── 2. Sobel-PPM depth lift ──
    rng = np.random.default_rng(0)
    ppm_pts, ppm_rgb = [], []
    for ci, df in kf:
        im = np.asarray(Image.open(imgdir / names[ci])).astype(np.float32) / 255.0
        depth_cal = calib_depth(np.load(df).astype(np.float32), Rs[ci], ts[ci], slam)
        if depth_cal is None:
            continue
        gray = cv2.cvtColor((im * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        sob = np.hypot(cv2.Sobel(gray, cv2.CV_32F, 1, 0), cv2.Sobel(gray, cv2.CV_32F, 0, 1))
        p = sob.ravel() + sob.mean() * 0.1 + 1e-6
        p /= p.sum()
        sel = rng.choice(len(p), PPM_PTS_PER_FRAME, replace=False, p=p)
        py, px = np.unravel_index(sel, gray.shape)
        zc = depth_cal[py, px]
        keep = (zc > 0.3) & (zc < 12)
        px, py, zc = px[keep], py[keep], zc[keep]
        xc = (px - CX) / FX * zc
        yc = (py - CY) / FY * zc
        Pw = (np.stack([xc, yc, zc], 1) - ts[ci]) @ Rs[ci]
        ppm_pts.append(Pw.astype(np.float32))
        ppm_rgb.append((im[py, px] * 255).astype(np.uint8))
    ppm_pts = np.concatenate(ppm_pts); ppm_rgb = np.concatenate(ppm_rgb)
    print(f"[ppm] {len(ppm_pts):,}")

    # ── 3. 병합 (4cm voxel, RoMA 우선) + 재필터 ──
    pts = np.concatenate([roma_pts, ppm_pts])
    rgb = np.concatenate([roma_rgb, ppm_rgb])
    key = np.floor(pts / 0.04).astype(np.int64)
    _, uidx = np.unique(key, axis=0, return_index=True)  # 앞쪽(RoMA) 우선
    pts, rgb = pts[uidx], rgb[uidx]
    print(f"[merge] {len(pts):,}")

    fpath = Path(args.field) if args.field else (
        scene_dir / "depth_anchors.npz" if (scene_dir / "depth_anchors.npz").exists()
        else scene_dir / "carve_field.npz")
    z = np.load(fpath)
    ts2 = uniform_filter(z["transit"], 3); es2 = uniform_filter(z["terminal"], 3)
    ratio = ts2 / (ts2 + 3 * es2 + 1e-6); lo = z["lo"]; dims = z["dims"]
    gi = np.floor((pts - lo) / VOXEL).astype(np.int64)
    inb = ((gi >= 0) & (gi < dims[None, :])).all(1)
    rho = np.zeros(len(pts), np.float32)
    rho[inb] = ratio[gi[inb, 0], gi[inb, 1], gi[inb, 2]]
    anch = z["anchors"] if "anchors" in z.files else slam
    d5, _ = cKDTree(anch).query(pts, k=5, workers=-1)
    w = rho * np.clip(d5.mean(1) / 0.25, 0, 1)
    pts, rgb = pts[w <= 0.5], rgb[w <= 0.5]
    print(f"[refilter:{fpath.name}] {len(pts):,}")

    pts = np.concatenate([slam, pts])
    rgb = np.concatenate([np.full((len(slam), 3), 128, np.uint8), rgb])
    dst = scene_dir / "03_rgb_3dgs_hyb"
    (dst / "sparse/0").mkdir(parents=True, exist_ok=True)
    if not (dst / "images").exists():
        (dst / "images").symlink_to(imgdir.resolve())
    for f in ("cameras.txt", "images.txt"):
        shutil.copy(base / f, dst / "sparse/0" / f)
    with open(dst / "sparse/0/points3D.txt", "w") as fo:
        for i, (p, c) in enumerate(zip(pts, rgb)):
            fo.write(f"{i} {p[0]:.6f} {p[1]:.6f} {p[2]:.6f} {c[0]} {c[1]} {c[2]} 0\n")
    print(f"[done] hybrid init {len(pts):,} → {dst}")


if __name__ == "__main__":
    main()
