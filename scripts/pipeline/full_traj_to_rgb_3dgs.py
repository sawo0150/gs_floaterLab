#!/usr/bin/env python3
"""Build a full-frame RGB 3DGS dataset from an OpenMAVIS stereo-inertial run.

Inputs
  --frame-traj   f_<name>.txt   (per-frame body pose T_w(b0)_body, first-KF re-zeroed world)
  --orb-export   orb_export/    (keyframes.jsonl Tcw + map_points.jsonl, raw Atlas world)
  --aria-yaml    Aria.yaml      (IMU.T_b_c1 = Tbc, cam0(slam-left) -> body)
  --vrs          source VRS     (RGB stream + device calibration)

The f-trajectory world is re-zeroed to the first keyframe body frame
(System::SaveTrajectoryEuRoC), while map_points.jsonl lives in the raw Atlas
world. We recover the constant alignment A = T_worldRaw_cam0 @ inv(T_worldB0_cam0)
from timestamp-matched keyframes, verify it is consistent, and move every frame
pose into the raw world so poses and points3D share one frame.

RGB frames get poses by SE3 interpolation (slerp + lerp) between the two
bracketing SLAM frame poses.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image
from projectaria_tools.core import calibration, data_provider


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_tbc_from_aria_yaml(yaml_path: Path) -> np.ndarray:
    text = yaml_path.read_text(encoding="utf-8")
    m = re.search(r"IMU\.T_b_c1.*?data:\s*\[([^\]]+)\]", text, re.DOTALL)
    if not m:
        raise RuntimeError(f"IMU.T_b_c1 not found in {yaml_path}")
    vals = [float(v) for v in re.split(r"[,\s]+", m.group(1).strip()) if v]
    if len(vals) != 16:
        raise RuntimeError(f"IMU.T_b_c1 has {len(vals)} values, expected 16")
    return np.asarray(vals, dtype=np.float64).reshape(4, 4)


def quat_to_rotmat(qx: float, qy: float, qz: float, qw: float) -> np.ndarray:
    q = np.asarray([qw, qx, qy, qz], dtype=np.float64)
    q /= np.linalg.norm(q)
    w, x, y, z = q
    return np.asarray(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
            [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
            [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def rotmat_to_quat_wxyz(R: np.ndarray) -> np.ndarray:
    t = float(np.trace(R))
    if t > 0.0:
        s = math.sqrt(t + 1.0) * 2.0
        q = np.asarray(
            [0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s]
        )
    else:
        i = int(np.argmax(np.diag(R)))
        if i == 0:
            s = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
            q = np.asarray(
                [(R[2, 1] - R[1, 2]) / s, 0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s]
            )
        elif i == 1:
            s = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
            q = np.asarray(
                [(R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s]
            )
        else:
            s = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
            q = np.asarray(
                [(R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s]
            )
    return q / np.linalg.norm(q)


def slerp_wxyz(q0: np.ndarray, q1: np.ndarray, alpha: float) -> np.ndarray:
    dot = float(np.dot(q0, q1))
    if dot < 0.0:
        q1 = -q1
        dot = -dot
    if dot > 0.9995:
        q = q0 + alpha * (q1 - q0)
        return q / np.linalg.norm(q)
    theta = math.acos(max(-1.0, min(1.0, dot)))
    s0 = math.sin((1.0 - alpha) * theta) / math.sin(theta)
    s1 = math.sin(alpha * theta) / math.sin(theta)
    q = s0 * q0 + s1 * q1
    return q / np.linalg.norm(q)


def se3_from_quat_trans(q_wxyz: np.ndarray, t: np.ndarray) -> np.ndarray:
    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = quat_to_rotmat(q_wxyz[1], q_wxyz[2], q_wxyz[3], q_wxyz[0])
    T[:3, 3] = t
    return T


def load_frame_traj(path: Path) -> tuple[np.ndarray, list[np.ndarray]]:
    """Returns (timestamps_s, list of T_w_body 4x4)."""
    ts_list, poses = [], []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            v = [float(x) for x in line.split()]
            if len(v) != 8:
                continue
            ts, tx, ty, tz, qx, qy, qz, qw = v
            T = np.eye(4, dtype=np.float64)
            T[:3, :3] = quat_to_rotmat(qx, qy, qz, qw)
            T[:3, 3] = [tx, ty, tz]
            ts_list.append(ts)
            poses.append(T)
    order = np.argsort(ts_list)
    return np.asarray(ts_list, dtype=np.float64)[order], [poses[i] for i in order]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frame-traj", required=True, type=Path)
    p.add_argument("--orb-export", required=True, type=Path)
    p.add_argument("--aria-yaml", required=True, type=Path)
    p.add_argument("--vrs", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--left-label", default="camera-slam-left")
    p.add_argument("--rgb-label", default="camera-rgb")
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=1024)
    p.add_argument("--focal", type=float, default=500.0)
    p.add_argument("--kf-match-tol-ms", type=float, default=1.0)
    p.add_argument("--max-interp-gap-ms", type=float, default=120.0)
    p.add_argument("--max-extrap-ms", type=float, default=5.0)
    args = p.parse_args()

    Tbc = parse_tbc_from_aria_yaml(args.aria_yaml)  # cam0 -> body

    # --- SLAM frame trajectory (body poses, b0 world) -> cam0 poses ---
    ts_s, T_wb0_body = load_frame_traj(args.frame_traj)
    if len(ts_s) < 2:
        raise RuntimeError(f"frame trajectory too short: {len(ts_s)} poses")
    T_wb0_c0 = [T @ Tbc for T in T_wb0_body]

    # --- Alignment b0 world -> raw Atlas world via keyframes ---
    keyframes = load_jsonl(args.orb_export / "keyframes.jsonl")
    map_points = load_jsonl(args.orb_export / "map_points.jsonl")
    tol_s = args.kf_match_tol_ms * 1e-3
    aligns = []
    for kf in keyframes:
        kf_ts = int(kf["timestamp_ns"]) * 1e-9
        i = int(np.searchsorted(ts_s, kf_ts))
        best = None
        for j in (i - 1, i):
            if 0 <= j < len(ts_s) and abs(ts_s[j] - kf_ts) <= tol_s:
                if best is None or abs(ts_s[j] - kf_ts) < abs(ts_s[best] - kf_ts):
                    best = j
        if best is None:
            continue
        T_wraw_c0 = np.linalg.inv(np.asarray(kf["Tcw"], dtype=np.float64))
        aligns.append(T_wraw_c0 @ np.linalg.inv(T_wb0_c0[best]))
    if not aligns:
        raise RuntimeError("no keyframe matched the frame trajectory; cannot align worlds")

    A = aligns[len(aligns) // 2]
    trans_dev = [float(np.linalg.norm(Ai[:3, 3] - A[:3, 3])) for Ai in aligns]
    rot_dev = [
        float(np.degrees(np.arccos(np.clip((np.trace(Ai[:3, :3].T @ A[:3, :3]) - 1) / 2, -1, 1))))
        for Ai in aligns
    ]
    print(
        f"[align] matched KFs: {len(aligns)}, translation dev max {max(trans_dev)*1000:.2f} mm, "
        f"rotation dev max {max(rot_dev):.4f} deg"
    )
    if max(trans_dev) > 0.05:
        raise RuntimeError(
            f"world alignment inconsistent (max dev {max(trans_dev):.3f} m). "
            "f-trajectory and orb_export likely come from different runs."
        )

    # --- interpolation source: cam0 poses in raw world, split for slerp ---
    quats = [rotmat_to_quat_wxyz((A @ T)[:3, :3]) for T in T_wb0_c0]
    trans = [(A @ T)[:3, 3] for T in T_wb0_c0]

    # --- VRS: calibration + RGB stream ---
    provider = data_provider.create_vrs_data_provider(str(args.vrs))
    rgb_stream_id = provider.get_stream_id_from_label(args.rgb_label)
    device_calib = provider.get_device_calibration()
    left_calib = device_calib.get_camera_calib(args.left_label)
    rgb_calib = device_calib.get_camera_calib(args.rgb_label)
    if left_calib is None or rgb_calib is None:
        raise RuntimeError("missing camera calibration in VRS")
    dst_rgb_calib = calibration.get_linear_camera_calibration(
        args.width, args.height, args.focal, args.rgb_label
    )
    T_device_left = np.asarray(left_calib.get_transform_device_camera().to_matrix(), dtype=np.float64)
    T_device_rgb = np.asarray(rgb_calib.get_transform_device_camera().to_matrix(), dtype=np.float64)
    T_c0_rgb = np.linalg.inv(T_device_left) @ T_device_rgb  # rgb -> cam0 (same chain as keyframe tool)

    images_dir = args.output / "images"
    sparse_dir = args.output / "sparse" / "0"
    images_dir.mkdir(parents=True, exist_ok=True)
    sparse_dir.mkdir(parents=True, exist_ok=True)

    n_rgb = provider.get_num_data(rgb_stream_id)
    images_lines: list[str] = []
    sanity_rows: list[dict] = []
    n_skipped_gap, n_extrap = 0, 0
    image_id = 1
    max_gap_s = args.max_interp_gap_ms * 1e-3
    max_extrap_s = args.max_extrap_ms * 1e-3

    for i in range(n_rgb):
        image_data, record = provider.get_image_data_by_index(rgb_stream_id, i)
        rgb_ts = int(record.capture_timestamp_ns) * 1e-9

        j = int(np.searchsorted(ts_s, rgb_ts))
        if j == 0 or j == len(ts_s):
            # outside trajectory: allow tiny extrapolation by clamping
            k = 0 if j == 0 else len(ts_s) - 1
            if abs(ts_s[k] - rgb_ts) > max_extrap_s:
                n_skipped_gap += 1
                continue
            q, t = quats[k], trans[k]
            dt_ms = (rgb_ts - ts_s[k]) * 1e3
            n_extrap += 1
        else:
            t0, t1 = ts_s[j - 1], ts_s[j]
            if (t1 - t0) > max_gap_s:
                n_skipped_gap += 1
                continue
            alpha = (rgb_ts - t0) / (t1 - t0)
            q = slerp_wxyz(quats[j - 1], quats[j], float(alpha))
            t = (1.0 - alpha) * trans[j - 1] + alpha * trans[j]
            dt_ms = min(rgb_ts - t0, t1 - rgb_ts) * 1e3

        T_wraw_c0_t = se3_from_quat_trans(q, t)
        T_world_rgb = T_wraw_c0_t @ T_c0_rgb
        T_rgb_world = np.linalg.inv(T_world_rgb)

        undistorted = calibration.distort_by_calibration(
            image_data.to_numpy_array(), dst_rgb_calib, rgb_calib
        )
        image_name = f"frame_{image_id:05d}.jpg"
        Image.fromarray(np.ascontiguousarray(undistorted)).save(images_dir / image_name, quality=95)

        qc = rotmat_to_quat_wxyz(T_rgb_world[:3, :3])
        tc = T_rgb_world[:3, 3]
        images_lines.append(
            f"{image_id} {qc[0]} {qc[1]} {qc[2]} {qc[3]} {tc[0]} {tc[1]} {tc[2]} 1 {image_name}\n\n"
        )
        sanity_rows.append(
            {
                "image_id": image_id,
                "rgb_timestamp_ns": int(record.capture_timestamp_ns),
                "nearest_slam_dt_ms": dt_ms,
                "camera_center": T_world_rgb[:3, 3].tolist(),
            }
        )
        image_id += 1

    (sparse_dir / "cameras.txt").write_text(
        f"1 PINHOLE {args.width} {args.height} {args.focal} {args.focal} "
        f"{args.width / 2.0} {args.height / 2.0}\n",
        encoding="utf-8",
    )
    (sparse_dir / "images.txt").write_text("".join(images_lines), encoding="utf-8")
    with (sparse_dir / "points3D.txt").open("w", encoding="utf-8") as f:
        for row in map_points:
            x, y, z = row["xyz"]
            f.write(f"{int(row['map_point_id'])} {x} {y} {z} 128 128 128 0\n")

    summary = {
        "frame_traj": str(args.frame_traj),
        "orb_export": str(args.orb_export),
        "vrs": str(args.vrs),
        "slam_frames": len(ts_s),
        "rgb_frames_total": n_rgb,
        "images_written": image_id - 1,
        "skipped_out_of_traj_or_gap": n_skipped_gap,
        "extrapolated": n_extrap,
        "points": len(map_points),
        "align_matched_kfs": len(aligns),
        "align_trans_dev_max_m": max(trans_dev),
        "align_rot_dev_max_deg": max(rot_dev),
    }
    (args.output / "pose_sanity.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (args.output / "pose_sanity_rows.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in sanity_rows), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
