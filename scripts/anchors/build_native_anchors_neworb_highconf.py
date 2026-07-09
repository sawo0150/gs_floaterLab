#!/usr/bin/env python3
"""High-confidence variant of build_native_anchors_neworb.py.

Difference from the plain native builder:
  - anchor SLAM points are restricted to obs>=10 & found_ratio>=0.5
    (the "고confidence" threshold from context/knowledge/plateau_loss_design.md,
    never actually applied before -- the original v3/v4 scripts and the plain
    native builder both used obs>=3 for anchors AND used ALL visible SLAM
    points per-keyframe for the monodepth scale/shift fit, defended only by
    Huber robust regression).
  - the monodepth calibration fit itself also uses only these high-confidence
    points (previously it used every visible SLAM point regardless of
    confidence).

Reuses the Depth Pro maps already computed by inference_depthpro_neworb.py
(results/diagnostic/depth_maps_neworb_301_1253/depth_pro) -- no new GPU
inference needed, this script is CPU-only.
"""
import json
import os
from pathlib import Path

import numpy as np
from sklearn.linear_model import HuberRegressor
from sklearn.neighbors import NearestNeighbors

DATA = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data")
PTS_TXT = DATA / "03_rgb_3dgs_full/sparse/0/points3D.txt"
IMG_TXT = DATA / "03_rgb_3dgs_full/sparse/0/images.txt"
CAM_TXT = DATA / "03_rgb_3dgs_full/sparse/0/cameras.txt"
MAP_PTS_JSONL = DATA / "02_openmavis_output/orb_export/map_points.jsonl"
DEPTH_DIR = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic/depth_maps_neworb_301_1253/depth_pro")
KF_MAP = Path("/tmp/claude-1000/-home-wosas-Desktop-Incremental-mapping-test-gs-floaterLab/bb6adb02-cf2a-41cb-8c93-b8740eb2e027/scratchpad/kf_frame_map.json")

_TS = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_DIR = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic") / f"native_anchors_neworb_highconf_{_TS}"
OUT_DIR.mkdir(parents=True, exist_ok=True)

KNN_K = 5
KNN_ISO_MULT = 3.0
VOXEL_SIZE = 0.30
STRIDE = 16
MIN_HITS = 2
D_TARGET = 0.50
OBS_MIN = 10
FOUND_RATIO_MIN = 0.5


def qvec2rotmat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2*y*y - 2*z*z, 2*x*y - 2*w*z,     2*x*z + 2*w*y],
        [2*x*y + 2*w*z,     1 - 2*x*x - 2*z*z, 2*y*z - 2*w*x],
        [2*x*z - 2*w*y,     2*y*z + 2*w*x,     1 - 2*x*x - 2*y*y],
    ])


def load_colmap_cameras(path):
    cams = {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split()
        cams[int(p[0])] = {"model": p[1], "width": int(p[2]), "height": int(p[3]),
                            "params": [float(x) for x in p[4:]]}
    return cams


def load_colmap_images(path):
    images = {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split()
        if len(p) < 9:
            continue
        image_id = int(p[0])
        q = np.array([float(x) for x in p[1:5]])
        t = np.array([float(x) for x in p[5:8]])
        images[image_id] = {"qvec": q, "tvec": t, "camera_id": int(p[8]), "name": p[9]}
    return images


def load_and_filter_slam_points_highconf():
    print(f"Loading and filtering SLAM points (high-confidence: obs>={OBS_MIN} & found_ratio>={FOUND_RATIO_MIN})...")
    conf = {}
    for line in open(MAP_PTS_JSONL):
        d = json.loads(line)
        conf[d["map_point_id"]] = (d["observations"], d["found_ratio"])

    pts_list, obs_list = [], []
    for line in open(PTS_TXT):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split()
        pid = int(p[0])
        obs, fr = conf.get(pid, (1, 0.0))
        pts_list.append([float(p[1]), float(p[2]), float(p[3])])
        obs_list.append((obs, fr))
    pts = np.array(pts_list, dtype=np.float64)
    obs_arr = np.array([o for o, _ in obs_list], dtype=np.int32)
    fr_arr = np.array([f for _, f in obs_list], dtype=np.float64)
    print(f"  Stage 0 (raw): {len(pts)}")

    cams = []
    for line in open(IMG_TXT):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split()
        if len(p) < 9:
            continue
        q = np.array([float(x) for x in p[1:5]])
        t = np.array([float(x) for x in p[5:8]])
        cams.append(-qvec2rotmat(q).T @ t)
    cams = np.array(cams, dtype=np.float64)

    lo = cams.min(0) - np.maximum((cams.max(0) - cams.min(0)) * 1.0, [2., 2., 3.])
    hi = cams.max(0) + np.maximum((cams.max(0) - cams.min(0)) * 1.0, [2., 2., 3.])
    valid = ((pts >= lo) & (pts <= hi)).all(axis=1)
    pts, obs_arr, fr_arr = pts[valid], obs_arr[valid], fr_arr[valid]
    print(f"  Stage 1 (camera bound): {len(pts)}")

    valid_conf = (obs_arr >= OBS_MIN) & (fr_arr >= FOUND_RATIO_MIN)
    pts, obs_arr, fr_arr = pts[valid_conf], obs_arr[valid_conf], fr_arr[valid_conf]
    print(f"  Stage 2 (high-confidence obs>={OBS_MIN} & found_ratio>={FOUND_RATIO_MIN}): {len(pts)}")

    if len(pts) > KNN_K + 1:
        nbrs = NearestNeighbors(n_neighbors=KNN_K + 1, algorithm="ball_tree").fit(pts)
        dists, _ = nbrs.kneighbors(pts)
        knn_dist = dists[:, KNN_K]
        threshold = KNN_ISO_MULT * np.median(knn_dist)
        mask = knn_dist <= threshold
        pts, obs_arr = pts[mask], obs_arr[mask]
        print(f"  Stage 3 (kNN isolation, thr={threshold:.3f}m): {len(pts)}")

    return pts, obs_arr, cams, lo, hi


def fit_scale_shift_quadratic_2d(u, v, z_mono, z_slam, W, H):
    N = len(z_slam)
    if N < 15:
        if N < 2:
            return None
        X = np.array(z_mono).reshape(-1, 1)
        y = np.array(z_slam)
        reg = HuberRegressor(epsilon=1.35, max_iter=1000).fit(X, y)
        return np.array([reg.coef_[0], 0, 0, 0, 0, 0, reg.intercept_, 0, 0, 0, 0, 0])
    u_norm = (np.array(u) - W / 2) / (W / 2)
    v_norm = (np.array(v) - H / 2) / (H / 2)
    z_m, z_s = np.array(z_mono), np.array(z_slam)
    M = np.stack([
        z_m, z_m * u_norm, z_m * v_norm, z_m * u_norm**2, z_m * v_norm**2, z_m * u_norm * v_norm,
        np.ones_like(z_m), u_norm, v_norm, u_norm**2, v_norm**2, u_norm * v_norm,
    ], axis=1)
    reg = HuberRegressor(epsilon=1.35, max_iter=1000).fit(M, z_s)
    return reg.coef_


def calibrate_depth_map(depth_map, coeffs, W, H):
    if coeffs is None:
        return depth_map
    uu, vv = np.meshgrid(np.arange(W), np.arange(H))
    u_norm = (uu - W / 2) / (W / 2)
    v_norm = (vv - H / 2) / (H / 2)
    s0, s1, s2, s3, s4, s5, t0, t1, t2, t3, t4, t5 = coeffs
    scale_field = s0 + s1*u_norm + s2*v_norm + s3*u_norm**2 + s4*v_norm**2 + s5*u_norm*v_norm
    shift_field = t0 + t1*u_norm + t2*v_norm + t3*u_norm**2 + t4*v_norm**2 + t5*u_norm*v_norm
    return np.maximum(scale_field * depth_map + shift_field, 0.1)


def check_distance_constraint(pos, G_occ, voxel_size, d_target):
    key = tuple(np.floor(pos / voxel_size).astype(int))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                nk = (key[0] + dx, key[1] + dy, key[2] + dz)
                if nk in G_occ and np.linalg.norm(pos - G_occ[nk]) < d_target:
                    return False
    return True


def _write_ply(path, pts, rgb):
    with open(path, "w") as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {len(pts)}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write("end_header\n")
        for p, c in zip(pts, rgb):
            f.write(f"{p[0]} {p[1]} {p[2]} {int(c[0])} {int(c[1])} {int(c[2])}\n")


def main():
    cameras = load_colmap_cameras(CAM_TXT)
    images = load_colmap_images(IMG_TXT)

    pts_slam, obs_slam, cams_all, filt_lo, filt_hi = load_and_filter_slam_points_highconf()

    kf_mapping = json.load(open(KF_MAP))
    name_to_imgid = {im["name"]: iid for iid, im in images.items()}
    kf_image_ids = sorted({name_to_imgid[m["rgb_frame"]] for m in kf_mapping if m["rgb_frame"] in name_to_imgid})
    print(f"Keyframe RGB images for depth calibration: {len(kf_image_ids)}")

    calibrated = {}
    n_corr_list = []
    for image_id in kf_image_ids:
        img_data = images[image_id]
        stem = os.path.splitext(img_data["name"])[0]
        npy_path = DEPTH_DIR / f"{stem}.npy"
        if not npy_path.exists():
            print(f"  [skip] missing depth for {img_data['name']}")
            continue
        depth_mono = np.load(npy_path)
        cam_info = cameras[img_data["camera_id"]]
        W, H = cam_info["width"], cam_info["height"]
        fx, fy, cx, cy = cam_info["params"][0:4]

        R = qvec2rotmat(img_data["qvec"])
        t = img_data["tvec"]
        xyz_cam = (R @ pts_slam.T).T + t
        z = xyz_cam[:, 2]
        front = z > 0.1
        u = fx * xyz_cam[:, 0] / np.where(front, z, 1) + cx
        v = fy * xyz_cam[:, 1] / np.where(front, z, 1) + cy
        inside = front & (u >= 0) & (u < W) & (v >= 0) & (v < H)

        uu = u[inside].astype(int)
        vv = v[inside].astype(int)
        z_slam = z[inside]
        z_mono = depth_mono[vv, uu]
        ok = z_mono > 0
        n_corr_list.append(int(ok.sum()))
        if ok.sum() < 2:
            print(f"  [skip] {img_data['name']}: only {ok.sum()} high-conf correspondences")
            continue

        coeffs = fit_scale_shift_quadratic_2d(u[inside][ok], v[inside][ok], z_mono[ok], z_slam[ok], W, H)
        calibrated[image_id] = calibrate_depth_map(depth_mono, coeffs, W, H)
        print(f"  {img_data['name']}: {ok.sum()} high-conf correspondences, calibrated")

    print(f"Calibrated {len(calibrated)}/{len(kf_image_ids)} keyframe depth maps")
    if n_corr_list:
        print(f"  correspondences per KF: median={np.median(n_corr_list):.0f} min={min(n_corr_list)} max={max(n_corr_list)}")

    G_occ = {}
    for pt in pts_slam:
        key = tuple(np.floor(pt / VOXEL_SIZE).astype(int))
        G_occ.setdefault(key, pt)

    G_cand = {}
    virtual_points = []
    for image_id, depth_calib in calibrated.items():
        img_data = images[image_id]
        cam_info = cameras[img_data["camera_id"]]
        W, H = cam_info["width"], cam_info["height"]
        fx, fy, cx, cy = cam_info["params"][0:4]
        R = qvec2rotmat(img_data["qvec"])
        t = img_data["tvec"]

        for v in range(0, H, STRIDE):
            for u in range(0, W, STRIDE):
                z = depth_calib[v, u]
                if z <= 0.1 or z > 15.0:
                    continue
                x_cam = np.array([(u - cx) / fx * z, (v - cy) / fy * z, z])
                x_world = R.T @ (x_cam - t)
                if not (filt_lo[0] <= x_world[0] <= filt_hi[0] and
                        filt_lo[1] <= x_world[1] <= filt_hi[1] and
                        filt_lo[2] <= x_world[2] <= filt_hi[2]):
                    continue
                key = tuple(np.floor(x_world / VOXEL_SIZE).astype(int))
                if key in G_occ:
                    continue
                if key not in G_cand:
                    G_cand[key] = {"sum_coords": x_world, "hits": 1, "frames": {image_id}}
                else:
                    if image_id not in G_cand[key]["frames"]:
                        G_cand[key]["sum_coords"] = G_cand[key]["sum_coords"] + x_world
                        G_cand[key]["hits"] += 1
                        G_cand[key]["frames"].add(image_id)
                if G_cand[key]["hits"] >= MIN_HITS:
                    mean_pos = G_cand[key]["sum_coords"] / G_cand[key]["hits"]
                    if check_distance_constraint(mean_pos, G_occ, VOXEL_SIZE, D_TARGET):
                        G_occ[key] = mean_pos
                        virtual_points.append(mean_pos)
                    del G_cand[key]

    pts_virtual = np.array(virtual_points, dtype=np.float32) if virtual_points else np.zeros((0, 3), dtype=np.float32)
    pts_slam32 = pts_slam.astype(np.float32)
    pts_all = np.vstack([pts_slam32, pts_virtual]) if len(pts_virtual) else pts_slam32

    np.save(OUT_DIR / "anchors_slam_depth_pro.npy", pts_slam32)
    np.save(OUT_DIR / "anchors_virtual_depth_pro.npy", pts_virtual)
    np.save(OUT_DIR / "anchors_all_depth_pro.npy", pts_all)

    slam_rgb = np.tile([59, 130, 246], (len(pts_slam32), 1))
    virt_rgb = np.tile([240, 120, 30], (len(pts_virtual), 1))
    all_rgb = np.vstack([slam_rgb, virt_rgb]) if len(pts_virtual) else slam_rgb
    _write_ply(OUT_DIR / "anchors_slam_depth_pro.ply", pts_slam32, slam_rgb)
    _write_ply(OUT_DIR / "anchors_virtual_depth_pro.ply", pts_virtual, virt_rgb)
    _write_ply(OUT_DIR / "anchors_all_depth_pro.ply", pts_all, all_rgb)

    meta = {
        "model": "depth_pro",
        "variant": "high_confidence",
        "obs_min": OBS_MIN,
        "found_ratio_min": FOUND_RATIO_MIN,
        "d_target_m": D_TARGET,
        "voxel_size_m": VOXEL_SIZE,
        "min_hits": MIN_HITS,
        "n_slam": int(len(pts_slam32)),
        "n_virtual": int(len(pts_virtual)),
        "n_total": int(len(pts_all)),
        "source_session": "data/02_openmavis_output + data/03_rgb_3dgs_full (2026-07-07 rebuild)",
        "kf_images_used": len(calibrated),
    }
    json.dump(meta, open(OUT_DIR / "anchors_meta_depth_pro.json", "w"), indent=2)
    print(f"\nDone. SLAM={len(pts_slam32)}, Virtual={len(pts_virtual)}, Total={len(pts_all)}")
    print(f"Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
