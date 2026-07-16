#!/usr/bin/env python3
"""exp51 축A: 각 keyframe(06_photoslam_replay/chunk_NNN)의 RGB 이미지에 대해
depth-pro raw depth를 SLAM point로 Huber 보정(calib_depth, causal)한 뒤,
dense inverse-depth map을 저장 — Photo-SLAM trainReplay의 depth loss 타깃.

build_depthmono_ppm_chunks.py와 동일한 causal 누적 SLAM point 로직을 재사용하되,
PPM 샘플링 대신 dense 전체 프레임의 calib된 depth map을 저장한다는 점만 다름.

출력: 06_photoslam_replay/chunk_NNN/depth_target_invdepth.npy (H,W float32, 1/depth, calib 실패 시 파일 없음)

사용: python build_depth_targets.py --scene 301_1253
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from sklearn.linear_model import HuberRegressor

LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
IMG_W, IMG_H = 1024, 1024
FX, FY, CX, CY = 500.0, 500.0, 511.5, 511.5


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


def parse_pose_line(images_txt: Path):
    for line in images_txt.read_text().splitlines():
        p = line.strip().split()
        if len(p) >= 10 and not p[0].startswith("#") and p[0].isdigit():
            qw, qx, qy, qz = float(p[1]), float(p[2]), float(p[3]), float(p[4])
            tx, ty, tz = float(p[5]), float(p[6]), float(p[7])
            name = p[9]
            R = qvec2rotmat([qw, qx, qy, qz]).astype(np.float32)
            t = np.array([tx, ty, tz], dtype=np.float32)
            return R, t, name
    raise RuntimeError(f"no pose in {images_txt}")


def calib_depth(depth, R, t, slam_pts):
    """build_depthmono_ppm_chunks.py의 calib_depth()와 동일 로직 (전체 depth map 반환)."""
    if len(slam_pts) < 10:
        return None
    pc = slam_pts @ R.T + t
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
    ap.add_argument("--kf-dir", default="04_incremental")
    ap.add_argument("--replay-dir", default="06_photoslam_replay")
    args = ap.parse_args()

    scene_dir = LAB / "data/scenes" / args.scene
    orb_export = LAB / "data/02_openmavis_output/orb_export"
    kf_root = scene_dir / args.kf_dir
    replay_root = scene_dir / args.replay_dir

    keyframes = load_jsonl(orb_export / "keyframes.jsonl")
    keyframes.sort(key=lambda kf: int(kf["kf_id"]))
    map_points = load_jsonl(orb_export / "map_points.jsonl")
    observations = load_jsonl(orb_export / "observations.jsonl")

    mp_to_first_kf = {}
    for obs in observations:
        mp_id = int(obs["map_point_id"])
        kf_id = int(obs["kf_id"])
        if mp_id not in mp_to_first_kf or kf_id < mp_to_first_kf[mp_id]:
            mp_to_first_kf[mp_id] = kf_id
    mp_xyz = {int(mp["map_point_id"]): np.array(mp["xyz"], dtype=np.float32) for mp in map_points}

    sys.path.insert(0, str(LAB / "repos/monoDepth/ml-depth-pro/src"))
    import torch
    import depth_pro
    from depth_pro.depth_pro import DepthProConfig

    device = "cuda" if torch.cuda.is_available() else "cpu"
    config = DepthProConfig(
        patch_encoder_preset="dinov2l16_384", image_encoder_preset="dinov2l16_384",
        checkpoint_uri=str(LAB / "repos/monoDepth/ml-depth-pro/checkpoints/depth_pro.pt"),
        decoder_features=256, use_fov_head=True, fov_encoder_preset="dinov2l16_384",
    )
    model, transform = depth_pro.create_model_and_transforms(config=config, device=torch.device(device))
    model = model.eval()
    f_px_tensor = torch.tensor([500.0], device=device)

    cumulative_slam = []
    n_written, n_skipped = 0, 0

    chunks = sorted(kf_root.glob("chunk_*"))
    for chunk_idx, ch in enumerate(chunks):
        kf_id = int(keyframes[chunk_idx]["kf_id"]) if chunk_idx < len(keyframes) else None
        new_pts_this_kf = []
        if kf_id is not None:
            new_pts_this_kf = [mp_xyz[mid] for mid, fk in mp_to_first_kf.items() if fk == kf_id and mid in mp_xyz]

        images_txt = ch / "sparse/0/images.txt"
        replay_chunk = replay_root / ch.name
        out_path = replay_chunk / "depth_target_invdepth.tiff"

        if len(cumulative_slam) < 10 or not images_txt.exists() or not replay_chunk.exists():
            n_skipped += 1
        else:
            R, t, src_name = parse_pose_line(images_txt)
            image_path = ch / "images" / src_name
            if not image_path.exists():
                n_skipped += 1
            else:
                raw_rgb = cv2.cvtColor(cv2.imread(str(image_path)), cv2.COLOR_BGR2RGB)
                with torch.no_grad():
                    pred = model.infer(transform(Image.fromarray(raw_rgb)), f_px=f_px_tensor)
                raw_depth = pred["depth"].cpu().numpy().astype(np.float32)

                slam_arr = np.stack(cumulative_slam)
                depth_cal = calib_depth(raw_depth, R, t, slam_arr)
                if depth_cal is None:
                    n_skipped += 1
                else:
                    invdepth = (1.0 / np.clip(depth_cal, 1e-3, None)).astype(np.float32)
                    cv2.imwrite(str(out_path), invdepth)
                    n_written += 1

        cumulative_slam.extend(new_pts_this_kf)

        if (chunk_idx + 1) % 10 == 0 or chunk_idx == len(chunks) - 1:
            print(f"[{chunk_idx+1}/{len(chunks)}] written={n_written} skipped={n_skipped} "
                  f"cumulative_slam={len(cumulative_slam)}", flush=True)

    print(f"Done. written={n_written} skipped={n_skipped}")


if __name__ == "__main__":
    main()
