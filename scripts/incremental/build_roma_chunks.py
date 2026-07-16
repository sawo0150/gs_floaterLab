#!/usr/bin/env python3
"""각 keyframe 청크 간에 RoMA dense correspondence를 계산하여 기하 검증된 3D 점을 생성.

이 버전은 인접 keyframe(chunk_idx-1과 chunk_idx) 쌍을 매칭하여 
causal order(인과 관계)를 만족하면서 기하학적으로 검증된 3D 점을 점진적으로 복원합니다.

입력: 04_incremental (keyframe 대표 프레임 이미지와 포즈)
출력: 05_incremental_dense/chunk_NNN/sparse/0/roma_points3D.txt

사용: python build_roma_chunks.py --scene 301_1253
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
import torch

LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
IMG_W, IMG_H = 1024, 1024
FX, FY, CX, CY = 500.0, 500.0, 511.5, 511.5
N_SAMPLE_PER_PAIR = 6000
CERT_TH = 0.5
REPROJ_TH = 2.0  # px


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def qvec2rotmat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * y * y - 2 * z * z, 2 * x * y - 2 * z * w, 2 * x * z + 2 * y * w],
        [2 * x * y + 2 * z * w, 1 - 2 * x * x - 2 * z * z, 2 * y * z - 2 * x * w],
        [2 * x * z - 2 * y * w, 2 * y * z + 2 * x * w, 1 - 2 * x * x - 2 * y * y],
    ])


def load_single_cam(images_txt: Path):
    for line in images_txt.read_text().splitlines():
        p = line.strip().split()
        if len(p) < 9 or p[0].startswith("#"):
            continue
        R = qvec2rotmat([float(x) for x in p[1:5]])
        t = np.array([float(x) for x in p[5:8]], dtype=np.float32)
        return R.astype(np.float32), t
    raise RuntimeError(f"no camera in {images_txt}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--kf-only-dir", default="04_incremental")
    ap.add_argument("--dense-dir", default="05_incremental_dense")
    args = ap.parse_args()

    scene_dir = LAB / "data/scenes" / args.scene
    orb_export = LAB / "data/02_openmavis_output/orb_export"
    kf_dir = scene_dir / args.kf_only_dir
    dense_dir = scene_dir / args.dense_dir

    keyframes = load_jsonl(orb_export / "keyframes.jsonl")
    keyframes.sort(key=lambda kf: int(kf["kf_id"]))

    # RoMA 모델 로드 (1회)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from romatch import roma_outdoor
    model = roma_outdoor(device=device, use_custom_corr=False)

    K = np.array([[FX, 0, CX], [0, FY, CY], [0, 0, 1]], dtype=np.float64)
    n_written, n_skipped = 0, 0

    for chunk_idx in range(len(keyframes)):
        chunk_dense = dense_dir / f"chunk_{chunk_idx:03d}"
        out_path = chunk_dense / "sparse" / "0" / "roma_points3D.txt"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if chunk_idx == 0:
            # 첫 번째 청크는 이전 프레임과의 매칭이 불가하므로 빈 파일 저장
            out_path.write_text("", encoding="utf-8")
            n_skipped += 1
            continue

        prev_chunk_kf = kf_dir / f"chunk_{chunk_idx-1:03d}"
        curr_chunk_kf = kf_dir / f"chunk_{chunk_idx:03d}"

        imA_p = prev_chunk_kf / "images" / "frame_00001.jpg"
        imB_p = curr_chunk_kf / "images" / "frame_00001.jpg"
        camA_txt = prev_chunk_kf / "sparse" / "0" / "images.txt"
        camB_txt = curr_chunk_kf / "sparse" / "0" / "images.txt"

        if not (imA_p.exists() and imB_p.exists() and camA_txt.exists() and camB_txt.exists()):
            out_path.write_text("", encoding="utf-8")
            n_skipped += 1
            continue

        try:
            RA, tA = load_single_cam(camA_txt)
            RB, tB = load_single_cam(camB_txt)

            # RoMA 매칭
            warp, certainty = model.match(str(imA_p), str(imB_p), device=device)
            matches, cert = model.sample(warp, certainty, num=N_SAMPLE_PER_PAIR)
            kptsA, kptsB = model.to_pixel_coordinates(matches, IMG_H, IMG_W, IMG_H, IMG_W)
            kptsA = kptsA.cpu().numpy()
            kptsB = kptsB.cpu().numpy()
            cert = cert.cpu().numpy()

            m = cert > CERT_TH
            if m.sum() < 10:
                out_path.write_text("", encoding="utf-8")
                n_skipped += 1
                continue

            kptsA, kptsB = kptsA[m], kptsB[m]

            # 삼각측량 (P = K [R|t])
            PA = K @ np.hstack([RA, tA[:, None]])
            PB = K @ np.hstack([RB, tB[:, None]])
            X4 = cv2.triangulatePoints(PA, PB, kptsA.T.astype(np.float64), kptsB.T.astype(np.float64))
            X = (X4[:3] / np.clip(X4[3], 1e-9, None)).T

            # 기하 검증
            def reproj_ok(Xw, R, t, kp):
                pc = Xw @ R.T + t
                z = pc[:, 2]
                u = pc[:, 0] / np.clip(z, 1e-9, None) * FX + CX
                v = pc[:, 1] / np.clip(z, 1e-9, None) * FY + CY
                err = np.hypot(u - kp[:, 0], v - kp[:, 1])
                return (z > 0.3) & (z < 12) & (err < REPROJ_TH)

            ok = reproj_ok(X, RA, tA, kptsA) & reproj_ok(X, RB, tB, kptsB)
            if ok.sum() == 0:
                out_path.write_text("", encoding="utf-8")
                n_skipped += 1
                continue

            X = X[ok]
            imA = np.asarray(Image.open(imA_p))
            c = imA[np.clip(kptsA[ok, 1].astype(int), 0, IMG_H - 1),
                    np.clip(kptsA[ok, 0].astype(int), 0, IMG_W - 1)]

            # voxel deduplication (3cm 격자)
            key = np.floor(X / 0.03).astype(np.int64)
            _, uidx = np.unique(key, axis=0, return_index=True)
            X, c = X[uidx], c[uidx]

            # 파일 출력
            with out_path.open("w", encoding="utf-8") as f:
                for i, (p, rgb) in enumerate(zip(X, c)):
                    f.write(f"{i} {p[0]:.6f} {p[1]:.6f} {p[2]:.6f} {rgb[0]} {rgb[1]} {rgb[2]} 0\n")
            n_written += 1

        except Exception as e:
            print(f"Error at chunk {chunk_idx}: {e}")
            out_path.write_text("", encoding="utf-8")
            n_skipped += 1

        if (chunk_idx + 1) % 10 == 0 or chunk_idx == len(keyframes) - 1:
            print(f"[{chunk_idx+1}/{len(keyframes)}] written={n_written} skipped={n_skipped}", flush=True)

    print(f"Done. written={n_written} skipped={n_skipped}")


if __name__ == "__main__":
    main()
