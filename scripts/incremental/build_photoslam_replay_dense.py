#!/usr/bin/env python3
"""exp51 축C: keyframe 밀도를 원본 57개의 D배로 늘려 Photo-SLAM replay 청크 생성.

각 원본 keyframe 청크(chunk_NNN)의 dense 구간(05_incremental_dense)에서 D개의 균등 간격 프레임을
뽑아 각각을 독립된 gaussian-생성 "keyframe"으로 승격시킨다. 인과 순서 유지:
- sub-frame 0(원본 keyframe 자리)만 그 시점 새로 확정된 SLAM point(extra_points3D.txt)를 받음
  (SLAM map point 확정은 OpenMAVIS keyframe 단위 개념이라 승격 프레임엔 없음).
- sub-frame 0..D-1 전부 자기 자신의 뷰에서 depth-pro+SLAM보정(calib_depth, causal) PPM 점을 받음
  (build_depthmono_ppm_chunks.py 로직 재사용, 프레임마다 별도 샘플이라 공간 커버리지가 늘어남).
- sub-frame 0..D-1 전부 depth_target_invdepth.tiff(축A 재사용)도 자기 뷰 기준으로 생성.
- 출력 디렉토리명 chunk_NNN_Y (Y=0..D-1)로 사전순=시간순 정렬 유지 (trainReplay가 glob+sort로 읽음).
- init 중복방지(축B, EXP51_DEDUP_INIT)는 trainReplay 쪽에서 처리하므로 여기선 그대로 둠.

사용: python build_photoslam_replay_dense.py --scene 301_1253 --density 2
출력: data/scenes/301_1253/06_photoslam_replay_density{D}/chunk_NNN_Y/...
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pycolmap
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
    cams = []
    for line in images_txt.read_text().splitlines():
        p = line.strip().split()
        if len(p) < 10 or p[0].startswith("#") or not p[0].isdigit():
            continue
        qw, qx, qy, qz = float(p[1]), float(p[2]), float(p[3]), float(p[4])
        tx, ty, tz = float(p[5]), float(p[6]), float(p[7])
        R = qvec2rotmat([qw, qx, qy, qz]).astype(np.float32)
        t = np.array([tx, ty, tz], dtype=np.float32)
        cams.append({"q": [qw, qx, qy, qz], "t": [tx, ty, tz], "R": R, "T": t, "image_name": p[9]})
    return cams


def read_points(path: Path):
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


def calib_depth(depth, R, t, slam_pts):
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


def write_chunk(dst: Path, cam, img_src: Path, xyz, rgb, image_id, depth_invdepth=None):
    (dst / "sparse/0").mkdir(parents=True, exist_ok=True)
    (dst / "images").mkdir(parents=True, exist_ok=True)
    name = "kf.jpg"
    link = dst / "images" / name
    if link.exists() or link.is_symlink():
        link.unlink()
    import os
    os.symlink(img_src.resolve(), link)

    rec = pycolmap.Reconstruction()
    pc = pycolmap.Camera.create(1, "PINHOLE", FX, IMG_W, IMG_H)
    pc.camera_id = 1
    pc.params = [FX, FY, CX, CY]
    rec.add_camera(pc)

    q, t = cam["q"], cam["t"]
    im = pycolmap.Image(image_id=image_id, name=name, camera_id=1)
    im.cam_from_world = pycolmap.Rigid3d(
        pycolmap.Rotation3d(np.array([q[1], q[2], q[3], q[0]])), np.array(t))
    try:
        im.registered = True
    except Exception:
        pass
    rec.add_image(im)

    for i in range(len(xyz)):
        rec.add_point3D(xyz[i], pycolmap.Track(), rgb[i])

    rec.write_binary(str(dst / "sparse/0"))

    if depth_invdepth is not None:
        cv2.imwrite(str(dst / "depth_target_invdepth.tiff"), depth_invdepth)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--density", type=int, required=True, choices=[1, 2, 3, 4])
    ap.add_argument("--kf-dir", default="04_incremental")
    ap.add_argument("--dense-dir", default="05_incremental_dense")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()
    D = args.density
    out_dir_name = args.out_dir or f"06_photoslam_replay_density{D}"

    scene = LAB / "data/scenes" / args.scene
    kf_root = scene / args.kf_dir
    dense_root = scene / args.dense_dir
    out_root = scene / out_dir_name
    out_root.mkdir(parents=True, exist_ok=True)

    orb_export = LAB / "data/02_openmavis_output/orb_export"
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

    rng = np.random.default_rng(0)
    cumulative_slam = []
    image_id_counter = 1
    manifest = []
    n_subframes_written = 0

    kf_chunks = sorted(kf_root.glob("chunk_*"))
    for chunk_idx, ch in enumerate(kf_chunks):
        kf_id = int(keyframes[chunk_idx]["kf_id"]) if chunk_idx < len(keyframes) else None
        new_pts_this_kf = []
        if kf_id is not None:
            new_pts_this_kf = [mp_xyz[mid] for mid, fk in mp_to_first_kf.items() if fk == kf_id and mid in mp_xyz]

        chunk_dense = dense_root / ch.name
        images_txt = chunk_dense / "sparse" / "0" / "images.txt"
        cams = load_all_cams_from_images_txt(images_txt) if images_txt.exists() else []

        # sub-frame 0 must be the ORIGINAL keyframe image (04_incremental), matching D1-b exactly
        kf_images_txt = ch / "sparse/0/images.txt"
        kf_line = kf_images_txt.read_text().splitlines()[0].split()
        kf_q = [float(x) for x in kf_line[1:5]]
        kf_t = [float(x) for x in kf_line[5:8]]
        kf_src_name = kf_line[9]
        kf_img_src = ch / "images" / kf_src_name
        subframe_cams = [{"q": kf_q, "t": kf_t, "T": np.array(kf_t, dtype=np.float32),
                           "R": qvec2rotmat(kf_q).astype(np.float32), "image_name": kf_src_name,
                           "img_src": kf_img_src}]

        # additional D-1 promoted dense frames, evenly spaced, excluding endpoints already used
        if D > 1 and len(cams) >= D:
            idxs = [int(round(i)) for i in np.linspace(0, len(cams) - 1, D)][1:]
            idxs = sorted(set(idxs))
            for idx in idxs:
                c = cams[idx]
                subframe_cams.append({**c, "img_src": chunk_dense / "images" / c["image_name"]})

        slam_arr = np.stack(cumulative_slam) if len(cumulative_slam) >= 10 else None

        for y, sc in enumerate(subframe_cams):
            xyz_pts, rgb_pts = (np.zeros((0, 3)), np.zeros((0, 3), dtype=np.uint8))
            if y == 0:
                # sub-frame 0: same SLAM init as D1-b baseline (chunk_000 uses initial points3D.txt)
                pts_path = (ch / "sparse/0/points3D.txt") if chunk_idx == 0 \
                    else (dense_root / ch.name / "sparse/0/extra_points3D.txt")
                xyz_pts, rgb_pts = read_points(pts_path)

            depth_invdepth = None
            if sc["img_src"].exists() and slam_arr is not None:
                raw_rgb = cv2.cvtColor(cv2.imread(str(sc["img_src"])), cv2.COLOR_BGR2RGB)
                with torch.no_grad():
                    pred = model.infer(transform(Image.fromarray(raw_rgb)), f_px=f_px_tensor)
                raw_depth = pred["depth"].cpu().numpy().astype(np.float32)
                depth_cal = calib_depth(raw_depth, sc["R"], sc["T"], slam_arr)
                if depth_cal is not None:
                    depth_invdepth = (1.0 / np.clip(depth_cal, 1e-3, None)).astype(np.float32)
                    ppm_pts, ppm_rgb = ppm_sample(sc["img_src"], depth_cal, sc["R"], sc["T"], rng)
                    if len(ppm_pts):
                        xyz_pts = np.concatenate([xyz_pts, ppm_pts], axis=0)
                        rgb_pts = np.concatenate([rgb_pts, ppm_rgb], axis=0)

            dst = out_root / f"chunk_{chunk_idx:03d}_{y}"
            write_chunk(dst, sc, sc["img_src"], xyz_pts, rgb_pts, image_id_counter, depth_invdepth)
            manifest.append({"chunk_idx": chunk_idx, "sub": y, "dir": dst.name,
                              "num_points": int(len(xyz_pts)), "has_depth": depth_invdepth is not None})
            image_id_counter += 1
            n_subframes_written += 1

        cumulative_slam.extend(new_pts_this_kf)

        if (chunk_idx + 1) % 10 == 0 or chunk_idx == len(kf_chunks) - 1:
            print(f"[{chunk_idx+1}/{len(kf_chunks)}] subframes_written={n_subframes_written} "
                  f"cumulative_slam={len(cumulative_slam)}", flush=True)

    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Done. {n_subframes_written} sub-chunks -> {out_root}")


if __name__ == "__main__":
    main()
