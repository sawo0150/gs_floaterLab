#!/usr/bin/env python3
"""make_exp46_materials.py — exp46 축A(경량화)·축3(표면-확신 opacity) 재료 생성.

축A: <scene> hybrid init을 voxel dedupe로 --budget 점까지 경량화 → 03_rgb_3dgs_hyb_budget/
축3: <scene> hybrid init 점의 carve score로 초기 opacity 배정(표면-확신=0.9, 빈공간 의심=0.05)
     → init_attrs_surfconf.npz (CARVE_INIT_ATTRS 용, 점 순서 = points3D.txt 순서)

사용: python make_exp46_materials.py --scene 301_305 --mode budget --budget 150000
      python make_exp46_materials.py --scene 301_12F --mode surfconf
"""
import argparse
import shutil
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import uniform_filter

LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")


def load_pts_rgb(txt):
    P, C = [], []
    for l in open(txt):
        t = l.split()
        if len(t) >= 7 and not l.startswith("#"):
            P.append([float(t[1]), float(t[2]), float(t[3])])
            C.append([int(t[4]), int(t[5]), int(t[6])])
    return np.array(P, np.float32), np.array(C, np.int32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--mode", choices=["budget", "surfconf"], required=True)
    ap.add_argument("--budget", type=int, default=150000)
    args = ap.parse_args()
    sdir = LAB / "data/scenes" / args.scene
    hyb = sdir / "03_rgb_3dgs_hyb/sparse/0/points3D.txt"
    pts, rgb = load_pts_rgb(hyb)
    print(f"[{args.scene}] hybrid init {len(pts):,}점")

    if args.mode == "budget":
        # voxel dedupe 점진적으로 키워 목표 근처로
        vox = 0.02
        while True:
            key = np.floor(pts / vox).astype(np.int64)
            _, uidx = np.unique(key, axis=0, return_index=True)
            if len(uidx) <= args.budget or vox > 0.5:
                break
            vox *= 1.25
        p2, c2 = pts[uidx], rgb[uidx]
        dst = sdir / "03_rgb_3dgs_hyb_budget"
        (dst / "sparse/0").mkdir(parents=True, exist_ok=True)
        if not (dst / "images").exists():
            (dst / "images").symlink_to((sdir / "03_rgb_3dgs/images").resolve())
        for f in ("cameras.txt", "images.txt"):
            shutil.copy(sdir / "03_rgb_3dgs_hyb/sparse/0" / f, dst / "sparse/0" / f)
        with open(dst / "sparse/0/points3D.txt", "w") as fo:
            for i, (p, c) in enumerate(zip(p2, c2)):
                fo.write(f"{i} {p[0]:.6f} {p[1]:.6f} {p[2]:.6f} {c[0]} {c[1]} {c[2]} 0\n")
        print(f"[budget] voxel {vox:.3f} → {len(p2):,}점 → {dst}")

    else:  # surfconf: carve score로 opacity 배정
        z = np.load(sdir / ("depth_anchors.npz" if (sdir / "depth_anchors.npz").exists()
                            else "carve_field.npz"))
        ts = uniform_filter(z["transit"], 3); es = uniform_filter(z["terminal"], 3)
        ratio = ts / (ts + 3 * es + 1e-6); lo = z["lo"]; dims = z["dims"]
        gi = np.floor((pts - lo) / 0.10).astype(np.int64)
        inb = ((gi >= 0) & (gi < dims[None, :])).all(1)
        rho = np.zeros(len(pts), np.float32)
        rho[inb] = ratio[gi[inb, 0], gi[inb, 1], gi[inb, 2]]
        anch = z["anchors"] if "anchors" in z.files else pts
        d5 = cKDTree(anch).query(pts, k=5, workers=-1)[0].mean(1)
        w = rho * np.clip(d5 / 0.25, 0, 1)          # 빈공간 증거 score (높을수록 floater 의심)
        # 표면-확신(w낮음)=opacity 0.9, 빈공간 의심(w높음)=0.05
        opacity = np.clip(0.9 - 0.85 * w, 0.05, 0.9).astype(np.float32)
        out = sdir / "init_attrs_surfconf.npz"
        np.savez_compressed(out, opacity=opacity)
        print(f"[surfconf] opacity p50={np.median(opacity):.2f} "
              f"(표면확신>0.5: {int((opacity>0.5).sum()):,} / 의심<0.2: {int((opacity<0.2).sum()):,}) → {out}")


if __name__ == "__main__":
    main()
