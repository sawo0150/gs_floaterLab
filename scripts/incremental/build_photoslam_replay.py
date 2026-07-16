#!/usr/bin/env python3
"""Photo-SLAM incremental replay용 per-keyframe 바이너리 COLMAP 청크 생성 (exp49 Phase C).

각 keyframe(=OpenMAVIS가 정한 57개)을 시간 순서대로 하나씩 Photo-SLAM GaussianMapper에
공급하기 위한 데이터. 청크 i = { keyframe i의 RGB 프레임 1장 + RGB-cam pose + 그 keyframe이
새로 확정한 init point }.

재사용:
- 04_incremental/chunk_NNN : RGB keyframe 이미지(최근접 RGB) + RGB-cam pose (build_incremental_chunks.py 산출)
- 05_incremental_dense/chunk_NNN/sparse/0/extra_points3D.txt : keyframe별 새 SLAM point (causal)
- chunk_000은 05에 extra가 없으므로 04의 points3D.txt(초기 점) 사용

출력: data/scenes/301_1253/06_photoslam_replay/chunk_NNN/{sparse/0/{cameras,images,points3D}.bin, images/<name>}
      + manifest.json (청크 순서, 이미지 이름, 새 점 수)

사용: python build_photoslam_replay.py --scene 301_1253
"""
import argparse
import json
import os
from pathlib import Path

import numpy as np
import pycolmap

LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
IMG_W, IMG_H = 1024, 1024
FX, FY, CX, CY = 500.0, 500.0, 512.0, 512.0


def parse_pose_line(images_txt: Path):
    """04_incremental images.txt의 단일 pose 줄 → (qw,qx,qy,qz,tx,ty,tz, name)."""
    for line in images_txt.read_text().splitlines():
        p = line.strip().split()
        if len(p) >= 10 and not p[0].startswith("#") and p[0].isdigit():
            q = [float(x) for x in p[1:5]]   # qw qx qy qz
            t = [float(x) for x in p[5:8]]   # tx ty tz
            name = p[9]
            return q, t, name
    raise RuntimeError(f"no pose in {images_txt}")


def read_points(path: Path):
    """id x y z r g b octave 포맷 → (Nx3 xyz, Nx3 rgb)."""
    xyz, rgb = [], []
    if not path.exists():
        return np.zeros((0, 3)), np.zeros((0, 3), dtype=np.uint8)
    for line in path.read_text().splitlines():
        p = line.strip().split()
        if len(p) < 7 or p[0].startswith("#"):
            continue
        xyz.append([float(p[1]), float(p[2]), float(p[3])])
        rgb.append([int(p[4]), int(p[5]), int(p[6])])
    if not xyz:
        return np.zeros((0, 3)), np.zeros((0, 3), dtype=np.uint8)
    return np.asarray(xyz, dtype=np.float64), np.asarray(rgb, dtype=np.uint8)


def write_chunk(dst: Path, q, t, img_name, img_src: Path, xyz, rgb, image_id):
    (dst / "sparse/0").mkdir(parents=True, exist_ok=True)
    (dst / "images").mkdir(parents=True, exist_ok=True)
    # 이미지 심링크
    link = dst / "images" / img_name
    if link.exists() or link.is_symlink():
        link.unlink()
    os.symlink(img_src.resolve(), link)

    rec = pycolmap.Reconstruction()
    cam = pycolmap.Camera.create(1, "PINHOLE", FX, IMG_W, IMG_H)
    cam.camera_id = 1
    cam.params = [FX, FY, CX, CY]
    rec.add_camera(cam)

    im = pycolmap.Image(image_id=image_id, name=img_name, camera_id=1)
    # COLMAP: qvec(w,x,y,z), tvec — world→cam (Tcw). 04_incremental images.txt가 이미 Tcw.
    im.cam_from_world = pycolmap.Rigid3d(
        pycolmap.Rotation3d(np.array([q[1], q[2], q[3], q[0]])),  # pycolmap quat = (x,y,z,w)
        np.array(t),
    )
    try:
        im.registered = True
    except Exception:
        pass
    rec.add_image(im)

    for i in range(len(xyz)):
        rec.add_point3D(xyz[i], pycolmap.Track(), rgb[i])

    rec.write_binary(str(dst / "sparse/0"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--kf-dir", default="04_incremental")
    ap.add_argument("--dense-dir", default="05_incremental_dense")
    ap.add_argument("--out-dir", default="06_photoslam_replay")
    ap.add_argument("--init-source", default="slam",
                    choices=["slam", "slam+ppm", "slam+ppm+roma"],
                    help="청크별 init 점 소스 (exp49 Phase D). ppm/roma 파일은 "
                         "05_incremental_dense에 exp48이 인과 순서로 생성해 둔 것 사용")
    args = ap.parse_args()

    scene = LAB / "data/scenes" / args.scene
    kf_root = scene / args.kf_dir
    dense_root = scene / args.dense_dir
    out_root = scene / args.out_dir
    out_root.mkdir(parents=True, exist_ok=True)

    chunks = sorted(kf_root.glob("chunk_*"))
    manifest = []
    for idx, ch in enumerate(chunks):
        images_txt = ch / "sparse/0/images.txt"
        q, t, src_name = parse_pose_line(images_txt)
        img_src = ch / "images" / src_name
        name = f"kf_{idx:03d}.jpg"  # 청크 간 이름 충돌 방지 (원본은 전부 frame_00001.jpg)

        # 새 점: chunk 0은 04의 초기 점, 이후는 05의 extra (+옵션에 따라 ppm/roma)
        if idx == 0:
            pts_path = ch / "sparse/0/points3D.txt"
        else:
            pts_path = dense_root / ch.name / "sparse/0/extra_points3D.txt"
        xyz, rgb = read_points(pts_path)

        extra_sources = []
        if "ppm" in args.init_source:
            extra_sources.append(dense_root / ch.name / "sparse/0/ppm_points3D.txt")
        if "roma" in args.init_source:
            extra_sources.append(dense_root / ch.name / "sparse/0/roma_points3D.txt")
        for src in extra_sources:
            exyz, ergb = read_points(src)
            if len(exyz):
                xyz = np.concatenate([xyz, exyz], axis=0)
                rgb = np.concatenate([rgb, ergb], axis=0)

        dst = out_root / ch.name
        write_chunk(dst, q, t, name, img_src, xyz, rgb, image_id=idx + 1)
        manifest.append({"chunk_idx": idx, "chunk": ch.name, "image": name,
                         "num_new_points": int(len(xyz))})
        if (idx + 1) % 10 == 0 or idx == len(chunks) - 1:
            print(f"[{idx+1}/{len(chunks)}] {ch.name} img={name} new_pts={len(xyz)}", flush=True)

    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Done. {len(chunks)} chunks → {out_root}")


if __name__ == "__main__":
    main()
