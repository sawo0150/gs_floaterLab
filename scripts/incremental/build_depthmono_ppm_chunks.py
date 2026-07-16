#!/usr/bin/env python3
"""각 keyframe 청크에 depth-mono(depth-pro) + PPM(Sobel 적응 샘플링) 점을 추가로 생성.

build_hybrid_init_scene.py(exp44d2 챔피언 레시피)의 2단계(Sobel-PPM depth lift)를
incremental 재생에 맞게 이식 — 딱 하나 다른 점: 배치판은 씬 전체 SLAM point(전량)로
depth를 보정하지만, 여기서는 **그 keyframe 시점까지 이미 관측된 SLAM point만** 써서
보정한다(causal order 유지 — Phase 1에서 OpenMAVIS가 실시간으로 이 형식을 낼 때도
그대로 맞는 방식).

이 버전은 청크 내 dense 구간에서 여러 프레임(K장)을 골고루 샘플링하여 
대표 프레임 1장만 쓸 때 발생하는 사각지대(init 구멍) 문제를 완화합니다.

입력: 05_incremental_dense (dense frame 이미지와 포즈)
출력: 05_incremental_dense/chunk_NNN/sparse/0/ppm_points3D.txt (기존 extra_points3D.txt와 별개 파일)

사용: python build_depthmono_ppm_chunks.py --scene 301_1253 --K 3
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
PPM_PTS_PER_FRAME = 4000


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


def load_all_cams_from_images_txt(images_txt: Path) -> list[dict]:
    """COLMAP images.txt를 파싱하여 각 프레임의 R, t, image_name 리스트를 반환"""
    cams = []
    lines = images_txt.read_text(encoding="utf-8").splitlines()
    for line in lines:
        p = line.strip().split()
        if len(p) < 10 or p[0].startswith("#"):
            continue
        try:
            image_id = int(p[0])
            qw, qx, qy, qz = float(p[1]), float(p[2]), float(p[3]), float(p[4])
            tx, ty, tz = float(p[5]), float(p[6]), float(p[7])
            image_name = p[9]
            R = qvec2rotmat([qw, qx, qy, qz]).astype(np.float32)
            t = np.array([tx, ty, tz], dtype=np.float32)
            cams.append({
                "image_id": image_id,
                "R": R,
                "t": t,
                "image_name": image_name
            })
        except Exception as e:
            print(f"Error parsing line: {line}. Error: {e}")
            continue
    return cams


def calib_depth(depth, R, t, slam_pts):
    """SLAM point를 이 프레임에 투영해 depth-pro raw depth와 대응시켜 Huber 회귀로 스케일/오프셋 보정.
    build_hybrid_init_scene.py의 calib_depth()와 동일 로직 — slam_pts만 호출부에서 다르게(누적) 넘김."""
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


def ppm_sample(image_path: Path, depth_cal, R, t, rng):
    im = np.asarray(Image.open(image_path)).astype(np.float32) / 255.0
    gray = cv2.cvtColor((im * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    sob = np.hypot(cv2.Sobel(gray, cv2.CV_32F, 1, 0), cv2.Sobel(gray, cv2.CV_32F, 0, 1))
    p = sob.ravel() + sob.mean() * 0.1 + 1e-6
    p /= p.sum()
    n = min(PPM_PTS_PER_FRAME, (p > 0).sum())
    sel = rng.choice(len(p), n, replace=False, p=p)
    py, px = np.unravel_index(sel, gray.shape)
    zc = depth_cal[py, px]
    keep = (zc > 0.3) & (zc < 12)
    px, py, zc = px[keep], py[keep], zc[keep]
    xc = (px - CX) / FX * zc
    yc = (py - CY) / FY * zc
    Pw = (np.stack([xc, yc, zc], 1) - t) @ R
    rgb = (im[py, px] * 255).astype(np.uint8)
    return Pw.astype(np.float32), rgb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--dense-dir", default="05_incremental_dense")
    ap.add_argument("--K", type=int, default=3, help="Number of dense frames to sample per keyframe chunk")
    args = ap.parse_args()

    scene_dir = LAB / "data/scenes" / args.scene
    orb_export = LAB / "data/02_openmavis_output/orb_export"
    dense_dir = scene_dir / args.dense_dir

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

    # depth-pro 모델 로드 (1회)
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

    rng = np.random.default_rng(0)
    cumulative_slam = []  # 지금까지(현재 keyframe 포함 이전까지) triangulate된 SLAM point만 누적
    n_written, n_skipped = 0, 0

    for chunk_idx, kf in enumerate(keyframes):
        kf_id = int(kf["kf_id"])

        # 이 keyframe 이전에 이미 알려진 SLAM point만 사용 (causal order — 미래 정보 사용 금지)
        # (이 keyframe 자신이 새로 본 점은 아직 "확정"되지 않은 것으로 보고 다음 스텝부터 포함)
        new_pts_this_kf = [mp_xyz[mid] for mid, fk in mp_to_first_kf.items() if fk == kf_id and mid in mp_xyz]

        chunk_dense = dense_dir / f"chunk_{chunk_idx:03d}"
        images_txt = chunk_dense / "sparse" / "0" / "images.txt"

        out_path = chunk_dense / "sparse" / "0" / "ppm_points3D.txt"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if len(cumulative_slam) < 10 or not images_txt.exists():
            out_path.write_text("", encoding="utf-8")
            n_skipped += 1
        else:
            cams = load_all_cams_from_images_txt(images_txt)
            if len(cams) == 0:
                out_path.write_text("", encoding="utf-8")
                n_skipped += 1
            else:
                # K개 프레임 균등 간격으로 샘플링
                M = len(cams)
                if M <= args.K:
                    selected_indices = list(range(M))
                else:
                    selected_indices = [int(round(i)) for i in np.linspace(0, M - 1, args.K)]
                selected_indices = sorted(list(set(selected_indices)))

                all_pts = []
                all_rgb = []
                for idx in selected_indices:
                    cam = cams[idx]
                    R = cam["R"]
                    t = cam["t"]
                    image_name = cam["image_name"]
                    image_path = chunk_dense / "images" / image_name

                    if not image_path.exists():
                        continue

                    raw_rgb = cv2.cvtColor(cv2.imread(str(image_path)), cv2.COLOR_BGR2RGB)
                    with torch.no_grad():
                        pred = model.infer(transform(Image.fromarray(raw_rgb)), f_px=f_px_tensor)
                    raw_depth = pred["depth"].cpu().numpy().astype(np.float32)

                    slam_arr = np.stack(cumulative_slam)
                    depth_cal = calib_depth(raw_depth, R, t, slam_arr)
                    if depth_cal is None:
                        continue

                    pts, rgb = ppm_sample(image_path, depth_cal, R, t, rng)
                    all_pts.append(pts)
                    all_rgb.append(rgb)

                if len(all_pts) == 0:
                    out_path.write_text("", encoding="utf-8")
                    n_skipped += 1
                else:
                    merged_pts = np.concatenate(all_pts, axis=0)
                    merged_rgb = np.concatenate(all_rgb, axis=0)
                    with out_path.open("w", encoding="utf-8") as f:
                        for i, (p, c) in enumerate(zip(merged_pts, merged_rgb)):
                            f.write(f"{i} {p[0]:.6f} {p[1]:.6f} {p[2]:.6f} {c[0]} {c[1]} {c[2]} 0\n")
                    n_written += 1

        # 이번 keyframe이 새로 확정한 점들을 다음 스텝부터 쓸 수 있도록 누적
        cumulative_slam.extend(new_pts_this_kf)

        if (chunk_idx + 1) % 10 == 0 or chunk_idx == len(keyframes) - 1:
            print(f"[{chunk_idx+1}/{len(keyframes)}] written={n_written} skipped={n_skipped} "
                  f"cumulative_slam={len(cumulative_slam)}", flush=True)

    print(f"Done. written={n_written} skipped={n_skipped}")


if __name__ == "__main__":
    main()
