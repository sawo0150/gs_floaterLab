#!/usr/bin/env python3
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

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--orb-export", required=True, type=Path)
    p.add_argument("--vrs", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--left-label", default="camera-slam-left")
    p.add_argument("--rgb-label", default="camera-rgb")
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=1024)
    p.add_argument("--focal", type=float, default=500.0)
    args = p.parse_args()

    # Create output directories
    args.output.mkdir(parents=True, exist_ok=True)

    # 1. Load data from VRS and calibration
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
    
    # T_c0_rgb represents rgb -> cam0 transformation (relative pose)
    T_device_left = np.asarray(left_calib.get_transform_device_camera().to_matrix(), dtype=np.float64)
    T_device_rgb = np.asarray(rgb_calib.get_transform_device_camera().to_matrix(), dtype=np.float64)
    T_c0_rgb = np.linalg.inv(T_device_left) @ T_device_rgb

    # Get all RGB capture timestamps
    n_rgb = provider.get_num_data(rgb_stream_id)
    rgb_ts_ns = []
    for i in range(n_rgb):
        _, record = provider.get_image_data_by_index(rgb_stream_id, i)
        rgb_ts_ns.append(int(record.capture_timestamp_ns))
    rgb_ts_ns = np.asarray(rgb_ts_ns, dtype=np.int64)

    # 2. Load keyframes and observations
    keyframes = load_jsonl(args.orb_export / "keyframes.jsonl")
    map_points = load_jsonl(args.orb_export / "map_points.jsonl")
    observations = load_jsonl(args.orb_export / "observations.jsonl")

    # Map each map_point_id to its first observing kf_id
    mp_to_first_kf = {}
    for obs in observations:
        mp_id = int(obs["map_point_id"])
        kf_id = int(obs["kf_id"])
        if mp_id not in mp_to_first_kf or kf_id < mp_to_first_kf[mp_id]:
            mp_to_first_kf[mp_id] = kf_id

    # Group map points by the kf_id where they are first observed
    kf_to_new_mps = {}
    for mp in map_points:
        mp_id = int(mp["map_point_id"])
        first_kf = mp_to_first_kf.get(mp_id)
        if first_kf is not None:
            kf_to_new_mps.setdefault(first_kf, []).append(mp)

    print(f"Loaded {len(keyframes)} keyframes, {len(map_points)} map points, {len(observations)} observations.")

    manifest = []
    
    # Process keyframes sequentially to build chunks
    for chunk_idx, kf in enumerate(keyframes):
        kf_id = int(kf["kf_id"])
        kf_ts = int(kf["timestamp_ns"])

        # Find closest RGB frame in timestamp
        diff = np.abs(rgb_ts_ns - kf_ts)
        closest_idx = int(np.argmin(diff))
        closest_diff_ms = float(diff[closest_idx]) * 1e-6

        # Extract and undistort the RGB frame
        image_data, _ = provider.get_image_data_by_index(rgb_stream_id, closest_idx)
        undistorted = calibration.distort_by_calibration(
            image_data.to_numpy_array(), dst_rgb_calib, rgb_calib
        )

        # Compute camera pose: T_rgb_worldRaw = inv(inv(Tcw) @ T_c0_rgb) = inv(T_c0_rgb) @ Tcw
        Tcw = np.asarray(kf["Tcw"], dtype=np.float64)
        T_worldRaw_cam0 = np.linalg.inv(Tcw)
        T_worldRaw_rgb = T_worldRaw_cam0 @ T_c0_rgb
        T_rgb_worldRaw = np.linalg.inv(T_worldRaw_rgb)

        qc = rotmat_to_quat_wxyz(T_rgb_worldRaw[:3, :3])
        tc = T_rgb_worldRaw[:3, 3]

        # Create chunk directory
        chunk_dir = args.output / f"chunk_{chunk_idx:03d}"
        images_dir = chunk_dir / "images"
        sparse_dir = chunk_dir / "sparse" / "0"
        images_dir.mkdir(parents=True, exist_ok=True)
        sparse_dir.mkdir(parents=True, exist_ok=True)

        # Save image
        image_name = "frame_00001.jpg"
        Image.fromarray(np.ascontiguousarray(undistorted)).save(images_dir / image_name, quality=95)

        # Write COLMAP files
        (sparse_dir / "cameras.txt").write_text(
            f"1 PINHOLE {args.width} {args.height} {args.focal} {args.focal} "
            f"{args.width / 2.0} {args.height / 2.0}\n",
            encoding="utf-8",
        )
        (sparse_dir / "images.txt").write_text(
            f"1 {qc[0]} {qc[1]} {qc[2]} {qc[3]} {tc[0]} {tc[1]} {tc[2]} 1 {image_name}\n\n",
            encoding="utf-8",
        )

        # Retrieve new map points for this keyframe
        new_mps = kf_to_new_mps.get(kf_id, [])
        if chunk_idx == 0:
            with (sparse_dir / "points3D.txt").open("w", encoding="utf-8") as f:
                for mp in new_mps:
                    x, y, z = mp["xyz"]
                    f.write(f"{int(mp['map_point_id'])} {x} {y} {z} 128 128 128 0\n")
        else:
            # Write 3 dummy points to points3D.txt to make Scene initialization happy and fast
            with (sparse_dir / "points3D.txt").open("w", encoding="utf-8") as f:
                f.write("1 0.0 0.0 0.0 128 128 128 0\n")
                f.write("2 0.01 0.0 0.0 128 128 128 0\n")
                f.write("3 0.0 0.01 0.0 128 128 128 0\n")
            # Write actual new points to extra_points3D.txt
            with (sparse_dir / "extra_points3D.txt").open("w", encoding="utf-8") as f:
                for mp in new_mps:
                    x, y, z = mp["xyz"]
                    f.write(f"{int(mp['map_point_id'])} {x} {y} {z} 128 128 128 0\n")

        # Save chunk info to manifest list
        manifest.append({
            "chunk_idx": chunk_idx,
            "kf_id": kf_id,
            "closest_rgb_idx": closest_idx,
            "timestamp_ns": kf_ts,
            "closest_diff_ms": closest_diff_ms,
            "num_new_map_points": len(new_mps),
            "camera_center": T_worldRaw_rgb[:3, 3].tolist(),
            "chunk_path": str(chunk_dir.relative_to(args.output.parent.parent.parent))
        })
        
        if (chunk_idx + 1) % 10 == 0 or (chunk_idx + 1) == len(keyframes):
            print(f"Processed {chunk_idx + 1}/{len(keyframes)} chunks.")

    # Write manifest file
    with (args.output / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("Done building incremental chunks dataset!")

if __name__ == "__main__":
    main()
