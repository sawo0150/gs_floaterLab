#!/usr/bin/env python3
"""Dense init variant seeded from the high-confidence ANCHOR set (not raw SLAM core).

Difference from build_dense_init_neworb.py:
  - That script seeds the occupancy grid (G_occ) from the broad "plain" SLAM
    core (obs>=3, 6,543 pts) for maximum real-geometry coverage.
  - THIS script seeds G_occ from the high-confidence ANCHOR set instead --
    the 1,438 pts (646 SLAM + 792 sparse monodepth-virtual) produced by
    build_native_anchors_neworb_highconf.py -- then expands it densely with
    the same fine voxel/stride/no-spacing parameters. The 1,438-pt anchor
    set is exactly what exp34/35/36 use as init/plateau anchors, so this
    dense expansion is directly comparable to (and pluggable alongside) that
    anchor's own plateau field.
  - Depth calibration fit still uses ONLY the high-confidence correspondences
    (obs>=10 & found_ratio>=0.5) -- same as the anchor build.
"""
import argparse
import json
import os
import shutil
from pathlib import Path

import numpy as np
from sklearn.linear_model import HuberRegressor

DATA = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data")
PTS_TXT = DATA / "03_rgb_3dgs_full/sparse/0/points3D.txt"
IMG_TXT = DATA / "03_rgb_3dgs_full/sparse/0/images.txt"
CAM_TXT = DATA / "03_rgb_3dgs_full/sparse/0/cameras.txt"
MAP_PTS_JSONL = DATA / "02_openmavis_output/orb_export/map_points.jsonl"
DEPTH_DIR = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic/depth_maps_neworb_301_1253/depth_pro")
KF_MAP = Path("/tmp/claude-1000/-home-wosas-Desktop-Incremental-mapping-test-gs-floaterLab/bb6adb02-cf2a-41cb-8c93-b8740eb2e027/scratchpad/kf_frame_map.json")
HIGHCONF_ANCHOR = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic/native_anchors_neworb_highconf_20260709_205327/anchors_all_depth_pro.npy")

_ap = argparse.ArgumentParser()
_ap.add_argument("--voxel-size", type=float, default=0.05,
                  help="voxel dedup cell size (m). 0.05 -> ~145k pts (dense). "
                       "0.11 -> ~65k pts (MPS-scale, ~60k target).")
_ap.add_argument("--tag", type=str, default=None,
                  help="output dir/scene name suffix. Defaults to voxel size (e.g. '5cm', '11cm').")
_args = _ap.parse_args()

VOXEL_SIZE = _args.voxel_size
_TAG = _args.tag or f"{int(round(VOXEL_SIZE * 100))}cm"

_TS = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_DIR = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic") / f"dense_confmono_init_highconf_seed_{_TAG}_{_TS}"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SCENE_NAME = f"orb_dense_confmono_init_highconf_seed_{_TAG}_scene"

FIT_OBS_MIN = 10
FIT_FOUND_RATIO_MIN = 0.5

STRIDE = 4
MIN_HITS = 2
D_TARGET = VOXEL_SIZE  # effectively disabled beyond voxel dedup


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


def load_points_with_conf():
    conf = {}
    for line in open(MAP_PTS_JSONL):
        d = json.loads(line)
        conf[d["map_point_id"]] = (d["observations"], d["found_ratio"])
    pts_list, obs_list, fr_list = [], [], []
    for line in open(PTS_TXT):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split()
        pid = int(p[0])
        obs, fr = conf.get(pid, (1, 0.0))
        pts_list.append([float(p[1]), float(p[2]), float(p[3])])
        obs_list.append(obs)
        fr_list.append(fr)
    return (np.array(pts_list, dtype=np.float64),
            np.array(obs_list, dtype=np.int32),
            np.array(fr_list, dtype=np.float64))


def camera_bound(img_txt):
    cams = []
    for line in open(img_txt):
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
    return lo, hi


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
    lo, hi = camera_bound(IMG_TXT)

    seed = np.load(HIGHCONF_ANCHOR).astype(np.float64)
    print(f"High-confidence anchor seed (1,438 expected): {len(seed)}")

    pts_all_raw, obs_arr, fr_arr = load_points_with_conf()
    fit_mask = (obs_arr >= FIT_OBS_MIN) & (fr_arr >= FIT_FOUND_RATIO_MIN)
    valid = ((pts_all_raw >= lo) & (pts_all_raw <= hi)).all(axis=1) & fit_mask
    pts_fit = pts_all_raw[valid]
    print(f"high-confidence fit points (obs>={FIT_OBS_MIN} & found_ratio>={FIT_FOUND_RATIO_MIN}): {len(pts_fit)}")

    kf_mapping = json.load(open(KF_MAP))
    name_to_imgid = {im["name"]: iid for iid, im in images.items()}
    kf_image_ids = sorted({name_to_imgid[m["rgb_frame"]] for m in kf_mapping if m["rgb_frame"] in name_to_imgid})

    calibrated = {}
    for image_id in kf_image_ids:
        img_data = images[image_id]
        stem = os.path.splitext(img_data["name"])[0]
        npy_path = DEPTH_DIR / f"{stem}.npy"
        if not npy_path.exists():
            continue
        depth_mono = np.load(npy_path)
        cam_info = cameras[img_data["camera_id"]]
        W, H = cam_info["width"], cam_info["height"]
        fx, fy, cx, cy = cam_info["params"][0:4]
        R = qvec2rotmat(img_data["qvec"])
        t = img_data["tvec"]

        xyz_cam = (R @ pts_fit.T).T + t
        z = xyz_cam[:, 2]
        front = z > 0.1
        u = fx * xyz_cam[:, 0] / np.where(front, z, 1) + cx
        v = fy * xyz_cam[:, 1] / np.where(front, z, 1) + cy
        inside = front & (u >= 0) & (u < W) & (v >= 0) & (v < H)
        uu, vv = u[inside].astype(int), v[inside].astype(int)
        z_slam = z[inside]
        z_mono = depth_mono[vv, uu]
        ok = z_mono > 0
        if ok.sum() < 2:
            continue
        coeffs = fit_scale_shift_quadratic_2d(u[inside][ok], v[inside][ok], z_mono[ok], z_slam[ok], W, H)
        calibrated[image_id] = calibrate_depth_map(depth_mono, coeffs, W, H)

    print(f"Calibrated {len(calibrated)}/{len(kf_image_ids)} keyframe depth maps (high-conf fit)")

    # Dense voxel seeding, G_occ seeded from the 1,438-pt high-confidence ANCHOR set
    G_occ = {}
    for pt in seed:
        key = tuple(np.floor(pt / VOXEL_SIZE).astype(int))
        G_occ.setdefault(key, pt)
    n_seed_voxels = len(G_occ)

    G_cand = {}
    virtual_points = []
    for image_id, depth_calib in calibrated.items():
        img_data = images[image_id]
        cam_info = cameras[img_data["camera_id"]]
        W, H = cam_info["width"], cam_info["height"]
        fx, fy, cx, cy = cam_info["params"][0:4]
        R = qvec2rotmat(img_data["qvec"])
        t = img_data["tvec"]
        Rt = R.T

        vs = np.arange(0, H, STRIDE)
        us = np.arange(0, W, STRIDE)
        uu_grid, vv_grid = np.meshgrid(us, vs)
        uu_flat, vv_flat = uu_grid.ravel(), vv_grid.ravel()
        z_flat = depth_calib[vv_flat, uu_flat]
        keep = (z_flat > 0.1) & (z_flat <= 15.0)
        uu_flat, vv_flat, z_flat = uu_flat[keep], vv_flat[keep], z_flat[keep]

        x_cam = np.stack([(uu_flat - cx) / fx * z_flat, (vv_flat - cy) / fy * z_flat, z_flat], axis=1)
        x_world = (x_cam - t) @ Rt.T
        bound_ok = ((x_world >= lo) & (x_world <= hi)).all(axis=1)
        x_world = x_world[bound_ok]

        for pos in x_world:
            key = tuple(np.floor(pos / VOXEL_SIZE).astype(int))
            if key in G_occ:
                continue
            if key not in G_cand:
                G_cand[key] = {"sum_coords": pos, "hits": 1, "frames": {image_id}}
            else:
                if image_id not in G_cand[key]["frames"]:
                    G_cand[key]["sum_coords"] = G_cand[key]["sum_coords"] + pos
                    G_cand[key]["hits"] += 1
                    G_cand[key]["frames"].add(image_id)
            if G_cand[key]["hits"] >= MIN_HITS:
                mean_pos = G_cand[key]["sum_coords"] / G_cand[key]["hits"]
                key2 = tuple(np.floor(mean_pos / VOXEL_SIZE).astype(int))
                if key2 not in G_occ:
                    G_occ[key2] = mean_pos
                    virtual_points.append(mean_pos)
                del G_cand[key]

    pts_virtual = np.array(virtual_points, dtype=np.float32) if virtual_points else np.zeros((0, 3), dtype=np.float32)
    seed32 = seed.astype(np.float32)
    pts_all = np.vstack([seed32, pts_virtual]) if len(pts_virtual) else seed32
    print(f"\nSeed (highconf anchor): {len(seed32)} (occupied {n_seed_voxels} voxels)")
    print(f"Dense virtual expansion: {len(pts_virtual)}")
    print(f"Total dense-confidence init: {len(pts_all)}")

    np.save(OUT_DIR / "init_seed_highconf_anchor.npy", seed32)
    np.save(OUT_DIR / "init_virtual_dense.npy", pts_virtual)
    np.save(OUT_DIR / "init_all.npy", pts_all)
    seed_rgb = np.tile([59, 130, 246], (len(seed32), 1))
    virt_rgb = np.tile([240, 120, 30], (len(pts_virtual), 1))
    all_rgb = np.vstack([seed_rgb, virt_rgb]) if len(pts_virtual) else seed_rgb
    _write_ply(OUT_DIR / "init_all.ply", pts_all, all_rgb)

    meta = {
        "model": "depth_pro",
        "purpose": "dense_confmono_init seeded from high-confidence ANCHOR (not raw SLAM core)",
        "seed_path": str(HIGHCONF_ANCHOR),
        "fit_obs_min": FIT_OBS_MIN,
        "fit_found_ratio_min": FIT_FOUND_RATIO_MIN,
        "voxel_size_m": VOXEL_SIZE,
        "stride_px": STRIDE,
        "min_hits": MIN_HITS,
        "d_target_m": D_TARGET,
        "n_seed": int(len(seed32)),
        "n_virtual_dense": int(len(pts_virtual)),
        "n_total": int(len(pts_all)),
        "kf_images_used": len(calibrated),
    }
    json.dump(meta, open(OUT_DIR / "meta.json", "w"), indent=2)

    DATASET = DATA / "03_rgb_3dgs_full"
    SCENE = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/datasets") / SCENE_NAME
    (SCENE / "sparse/0").mkdir(parents=True, exist_ok=True)
    if not (SCENE / "images").exists():
        (SCENE / "images").symlink_to(DATASET / "images")
    for f in ("cameras.txt", "images.txt"):
        shutil.copy(DATASET / "sparse/0" / f, SCENE / "sparse/0" / f)
    with open(SCENE / "sparse/0/points3D.txt", "w") as f:
        f.write("# 3D point list: POINT3D_ID X Y Z R G B ERROR TRACK[]\n")
        f.write(f"# Number of points: {len(pts_all)}, source: dense_confmono_init_highconf_seed "
                f"(highconf anchor seed: {len(seed32)} + dense monodepth virtual "
                f"(fit obs>={FIT_OBS_MIN}&fr>={FIT_FOUND_RATIO_MIN}, voxel={VOXEL_SIZE}m, stride={STRIDE}px): {len(pts_virtual)})\n")
        for i, p in enumerate(pts_all):
            f.write(f"{i+1} {p[0]:.6f} {p[1]:.6f} {p[2]:.6f} 128 128 128 0.0\n")

    print(f"\nOutput dir: {OUT_DIR}")
    print(f"Training scene: {SCENE}")


if __name__ == "__main__":
    main()
