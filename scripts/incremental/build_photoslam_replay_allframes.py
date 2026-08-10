#!/usr/bin/env python3
"""exp51 사용자 요청: keyframe(57장)만 쓰지 말고 vanilla batch처럼 전체 dense frame(1303장)을
incremental하게(causal order) 다 써서 학습 — Photo-SLAM의 기존 shuffle-cycle 키프레임 샘플러
(useOneRandomSlidingWindowKeyframe, 등록된 전체를 균등 순환)가 이미 "window+shuffle" 역할을 하므로
새 샘플러 없이, 전체 프레임을 causal 순서로 등록되는 replay 청크로만 만들면 된다.

- 원본 57 SLAM keyframe 자리: 기존 06_photoslam_replay_ppm/chunk_NNN을 그대로 재사용
  (SLAM+PPM init point + depth 타깃 포함, depth-pro 재실행 없음).
- 나머지 ~1246개 dense-only 프레임: pose+image만 등록, points3D 비움(가우시안 생성 없음,
  supervision-only), depth 타깃 없음(depth-pro 재실행 생략 — 속도/스코프 절충).
- 전체를 하나의 시간순 flat 시퀀스(g_00000..g_01302)로 합쳐 trainReplay가 그대로 순서대로 재생.

사용: python build_photoslam_replay_allframes.py --scene 301_1253
출력: data/scenes/301_1253/06_photoslam_replay_allframes/g_NNNNN/...
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


def parse_pose_line(line: str):
    p = line.strip().split()
    q = [float(x) for x in p[1:5]]
    t = [float(x) for x in p[5:8]]
    name = p[9]
    return q, t, name


def load_all_lines(images_txt: Path):
    if not images_txt.exists():
        return []
    out = []
    for line in images_txt.read_text().splitlines():
        p = line.strip().split()
        if len(p) >= 10 and not p[0].startswith("#") and p[0].isdigit():
            out.append(line)
    return out


def write_dense_only_chunk(dst: Path, q, t, img_src: Path, image_id):
    (dst / "sparse/0").mkdir(parents=True, exist_ok=True)
    (dst / "images").mkdir(parents=True, exist_ok=True)
    name = "d.jpg"
    link = dst / "images" / name
    if link.exists() or link.is_symlink():
        link.unlink()
    os.symlink(img_src.resolve(), link)

    rec = pycolmap.Reconstruction()
    cam = pycolmap.Camera.create(1, "PINHOLE", FX, IMG_W, IMG_H)
    cam.camera_id = 1
    cam.params = [FX, FY, CX, CY]
    rec.add_camera(cam)

    im = pycolmap.Image(image_id=image_id, name=name, camera_id=1)
    im.cam_from_world = pycolmap.Rigid3d(
        pycolmap.Rotation3d(np.array([q[1], q[2], q[3], q[0]])), np.array(t))
    try:
        im.registered = True
    except Exception:
        pass
    rec.add_image(im)
    # no points3D -> supervision-only, no new gaussians
    rec.write_binary(str(dst / "sparse/0"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--kf-dir", default="04_incremental")
    ap.add_argument("--dense-dir", default="05_incremental_dense")
    ap.add_argument("--kf-replay-dir", default="06_photoslam_replay_ppm",
                     help="이미 만들어진 keyframe replay(SLAM+PPM init+depth 타깃 포함) 재사용")
    ap.add_argument("--out-dir", default="06_photoslam_replay_allframes")
    args = ap.parse_args()

    scene = LAB / "data/scenes" / args.scene
    kf_root = scene / args.kf_dir
    dense_root = scene / args.dense_dir
    kf_replay_root = scene / args.kf_replay_dir
    out_root = scene / args.out_dir
    out_root.mkdir(parents=True, exist_ok=True)

    kf_chunks = sorted(kf_root.glob("chunk_*"))
    manifest = []
    g_idx = 0
    image_id_counter = 1
    n_kf, n_dense = 0, 0

    for chunk_idx, ch in enumerate(kf_chunks):
        # 1) 이 청크의 keyframe 자리 -> 기존 06_photoslam_replay_ppm 재사용 (symlink)
        kf_src = kf_replay_root / ch.name
        if kf_src.exists():
            dst = out_root / f"chunk_{g_idx:05d}_kf"
            if dst.exists() or dst.is_symlink():
                if dst.is_symlink():
                    dst.unlink()
            if not dst.exists():
                os.symlink(kf_src.resolve(), dst)
            manifest.append({"g_idx": g_idx, "type": "kf", "chunk_idx": chunk_idx, "dir": dst.name})
            g_idx += 1
            n_kf += 1

        # 2) 이 청크의 dense-only 프레임들 (keyframe 자신과 동일 시각 근접 프레임 제외 없이 전부 causal 순서로)
        chunk_dense = dense_root / ch.name
        images_txt = chunk_dense / "sparse" / "0" / "images.txt"
        lines = load_all_lines(images_txt)
        for line in lines:
            q, t, name = parse_pose_line(line)
            img_src = chunk_dense / "images" / name
            if not img_src.exists():
                continue
            dst = out_root / f"chunk_{g_idx:05d}_d"
            write_dense_only_chunk(dst, q, t, img_src, image_id_counter)
            manifest.append({"g_idx": g_idx, "type": "dense", "chunk_idx": chunk_idx, "dir": dst.name})
            g_idx += 1
            image_id_counter += 1
            n_dense += 1

        if (chunk_idx + 1) % 10 == 0 or chunk_idx == len(kf_chunks) - 1:
            print(f"[{chunk_idx+1}/{len(kf_chunks)}] g_idx={g_idx} kf={n_kf} dense={n_dense}", flush=True)

    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Done. total sub-chunks={g_idx} (kf={n_kf}, dense-only={n_dense}) -> {out_root}")


if __name__ == "__main__":
    main()
