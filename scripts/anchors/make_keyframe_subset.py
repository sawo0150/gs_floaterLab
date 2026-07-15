#!/usr/bin/env python3
"""make_keyframe_subset.py — 학습 뷰를 N장으로 균등 서브샘플한 데이터셋 생성 (exp47 축 S4).

원본 데이터셋의 images.txt에서 균등 간격 N장만 남긴 <src>_kfN 생성.
points3D(init)·cameras는 그대로, images는 심볼릭. 실시간(keyframe만) 학습 근사.

사용: python make_keyframe_subset.py --scene 301_12F --src 03_rgb_3dgs_hyb --n 300
"""
import argparse
import shutil
from pathlib import Path

LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--src", default="03_rgb_3dgs_hyb")
    ap.add_argument("--n", type=int, default=300)
    args = ap.parse_args()
    sdir = LAB / "data/scenes" / args.scene
    src = sdir / args.src / "sparse/0"
    dst_name = f"{args.src}_kf{args.n}"
    dst = sdir / dst_name / "sparse/0"
    dst.mkdir(parents=True, exist_ok=True)

    # images.txt: COLMAP 형식은 이미지당 2줄(포즈줄 + points2d줄). points2d줄은 보통 빈 줄.
    lines = open(src / "images.txt").read().splitlines()
    header = [l for l in lines if l.startswith("#")]
    body = [l for l in lines if l.strip() and not l.startswith("#")]
    # 포즈줄만 추출(토큰 10개, 이미지명 포함)
    pose_lines = [l for l in body if len(l.split()) >= 10]
    step = max(1, len(pose_lines) // args.n)
    sel = pose_lines[::step][:args.n]
    with open(dst / "images.txt", "w") as f:
        f.write("\n".join(header) + "\n")
        for pl in sel:
            f.write(pl + "\n\n")   # 포즈줄 + 빈 points2d줄
    for fn in ("cameras.txt", "points3D.txt"):
        shutil.copy(src / fn, dst / fn)
    if (src.parent / "points3D.ply").exists():
        shutil.copy(src.parent / "points3D.ply", dst.parent / "points3D.ply")
    if not (dst.parent / "images").exists():
        (dst.parent / "images").symlink_to((sdir / args.src / "images").resolve())
    print(f"[kf] {len(pose_lines)}장 → {len(sel)}장 (step {step}) → {sdir/dst_name}")


if __name__ == "__main__":
    main()
