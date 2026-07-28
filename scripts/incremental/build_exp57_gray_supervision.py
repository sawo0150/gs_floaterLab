#!/usr/bin/env python3
"""Build calibrated Aria SLAM-camera supervision for exp57.

The output images are pinhole rectifications of the raw Fisheye624 streams.
The manifest stores the nearest RGB frame, calibrated intrinsics, and the
RGB-camera -> SLAM-camera transform needed to attach each image to VIGS's RGB
world-to-camera trajectory.

Run this script in the ``aria`` conda environment (projectaria_tools is needed).
"""

import argparse
import bisect
import json
from pathlib import Path

import cv2
import numpy as np
from projectaria_tools.core import calibration, data_provider


SENSORS = {
    "slam_left": ("camera-slam-left", "cam0"),
    "slam_right": ("camera-slam-right", "cam1"),
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vrs", type=Path, required=True)
    parser.add_argument("--rgb-index", type=Path, required=True)
    parser.add_argument("--mav-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stride", type=int, default=5)
    parser.add_argument("--offset", type=int, default=2)
    parser.add_argument("--width", type=int, default=464)
    parser.add_argument("--height", type=int, default=464)
    parser.add_argument("--focal", type=float, default=232.0)
    parser.add_argument("--max-delta-ms", type=float, default=2.0)
    return parser.parse_args()


def load_rgb_index(path):
    records = []
    for line in path.read_text().splitlines():
        timestamp, filename = line.split()
        # VIGS uses zero-based indices; frame_00001 is idx 0.
        frame_idx = int(Path(filename).stem.split("_")[-1]) - 1
        records.append((frame_idx, int(timestamp), filename))
    return records


def nearest_timestamp(sorted_timestamps, target):
    position = bisect.bisect_left(sorted_timestamps, target)
    candidates = sorted_timestamps[max(0, position - 1):position + 1]
    return min(candidates, key=lambda timestamp: abs(timestamp - target))


def main():
    args = parse_args()
    if args.stride <= 0:
        raise ValueError("--stride must be positive")

    provider = data_provider.create_vrs_data_provider(str(args.vrs))
    device_calib = provider.get_device_calibration()
    rgb_calib = device_calib.get_camera_calib("camera-rgb")
    t_device_rgb = rgb_calib.get_transform_device_camera().to_matrix()

    output_records = []
    for sensor_name, (aria_label, mav_name) in SENSORS.items():
        raw_dir = args.mav_root / mav_name / "data"
        timestamps = sorted(int(path.stem) for path in raw_dir.glob("*.png"))
        if not timestamps:
            raise FileNotFoundError(f"no PNG images in {raw_dir}")

        src_calib = device_calib.get_camera_calib(aria_label)
        dst_calib = calibration.get_linear_camera_calibration(
            args.width, args.height, args.focal, aria_label
        )
        t_device_gray = src_calib.get_transform_device_camera().to_matrix()
        # Existing VIGS trajectory is T_rgb_world. Therefore:
        # T_gray_world = (T_gray_device @ T_device_rgb) @ T_rgb_world.
        t_gray_rgb = np.linalg.inv(t_device_gray) @ t_device_rgb

        sensor_output = args.output / sensor_name
        sensor_output.mkdir(parents=True, exist_ok=True)
        for frame_idx, rgb_timestamp, rgb_filename in load_rgb_index(args.rgb_index):
            if frame_idx % args.stride != args.offset % args.stride:
                continue
            gray_timestamp = nearest_timestamp(timestamps, rgb_timestamp)
            delta_ns = gray_timestamp - rgb_timestamp
            if abs(delta_ns) > args.max_delta_ms * 1e6:
                continue

            raw = cv2.imread(
                str(raw_dir / f"{gray_timestamp}.png"), cv2.IMREAD_GRAYSCALE
            )
            if raw is None:
                raise RuntimeError(f"failed to read {gray_timestamp}.png")
            rectified = calibration.distort_by_calibration(raw, dst_calib, src_calib)
            output_name = f"frame_{frame_idx + 1:05d}.png"
            if not cv2.imwrite(str(sensor_output / output_name), rectified):
                raise RuntimeError(f"failed to write {sensor_output / output_name}")

            output_records.append({
                "sensor": sensor_name,
                "aria_label": aria_label,
                "frame_idx": frame_idx,
                "rgb_filename": rgb_filename,
                "rgb_timestamp_ns": rgb_timestamp,
                "gray_timestamp_ns": gray_timestamp,
                "timestamp_delta_ns": delta_ns,
                "image": str(Path(sensor_name) / output_name),
                "K": [
                    args.focal,
                    args.focal,
                    (args.width - 1) / 2.0,
                    (args.height - 1) / 2.0,
                    args.width,
                    args.height,
                ],
                "T_gray_rgb": t_gray_rgb.tolist(),
            })

    args.output.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(json.dumps({
        "schema": "exp57_aria_gray_supervision_v1",
        "rectification": {
            "model": "pinhole",
            "width": args.width,
            "height": args.height,
            "focal": args.focal,
        },
        "stride": args.stride,
        "offset": args.offset,
        "records": output_records,
    }, indent=2))
    deltas = np.asarray([abs(record["timestamp_delta_ns"]) for record in output_records])
    print(
        f"wrote {len(output_records)} images and {manifest_path}; "
        f"|dt| mean={deltas.mean() / 1e6:.3f}ms "
        f"max={deltas.max() / 1e6:.3f}ms"
    )


if __name__ == "__main__":
    main()
