#!/usr/bin/env python3
"""Build paired stride40/stride20 causal replay datasets for benchmark-B."""

from __future__ import annotations

import collections
import hashlib
import json
import os
from pathlib import Path

import cv2
import numpy as np
from scipy.spatial.transform import Rotation, Slerp


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE_INVENTORY = HERE / "evidence/source_inventory.json"
OUTPUT_ROOT = ROOT / "data/benchmarks/ercb_benchmark_B_stride20"
IMAGE_CACHE = ROOT / "data/benchmarks/ercb_benchmark_B_image_cache"
A_DATA = ROOT / "data/benchmarks/ercb_benchmark_A_replay_v2"
RPNG_K = (416.85223429743274, 414.92069080087543, 421.02459311003213, 237.76180565241077)
RPNG_DIST = (-0.045761895748285604, 0.03423951132164367,
             -0.00040139057556727315, 0.000431371425853453)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_trajectory(path: Path) -> np.ndarray:
    value = np.loadtxt(path, dtype=np.float64)
    if value.ndim == 1:
        value = value[None, :]
    if value.shape[1] < 8 or len(value) < 2:
        raise ValueError(f"invalid trajectory: {path}")
    value = value[np.argsort(value[:, 0])][:, :8]
    if np.any(np.diff(value[:, 0]) <= 0):
        raise ValueError(f"non-unique trajectory timestamps: {path}")
    return value


def nearest_indices(query: np.ndarray, reference: np.ndarray) -> np.ndarray:
    right = np.clip(np.searchsorted(reference, query), 1, len(reference) - 1)
    left = right - 1
    selected = np.where(
        np.abs(reference[left] - query) <= np.abs(reference[right] - query),
        left, right,
    )
    return np.asarray(sorted(set(map(int, selected))), dtype=np.int64)


def interpolate_poses(query: np.ndarray, trajectory: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    clipped = np.clip(query, trajectory[0, 0], trajectory[-1, 0])
    positions = np.stack([
        np.interp(clipped, trajectory[:, 0], trajectory[:, axis])
        for axis in (1, 2, 3)
    ], axis=1)
    rotations = Slerp(
        trajectory[:, 0], Rotation.from_quat(trajectory[:, 4:8])
    )(clipped).as_matrix()
    return positions, rotations


def qvec(matrix: np.ndarray) -> np.ndarray:
    x, y, z, w = Rotation.from_matrix(matrix).as_quat()
    value = np.asarray([w, x, y, z], dtype=np.float64)
    if value[0] < 0:
        value *= -1
    return value


def inventory(row: dict) -> tuple[list[Path], np.ndarray, tuple[float, ...]]:
    family = row["family"]
    root = Path(row["input"])
    rgb = Path(row["image_dir"])
    images = sorted(
        [path for path in rgb.iterdir() if path.suffix.lower() in (".png", ".jpg", ".jpeg")],
        key=lambda path: int(path.stem),
    )
    if len(images) < 2:
        raise ValueError(f"no timestamped images: {rgb}")
    timestamps = np.asarray([int(path.stem) * 1e-9 for path in images], dtype=np.float64)
    if family == "rpng":
        intrinsics = RPNG_K
    else:
        values = [float(value) for value in Path(row["calib"]).read_text().split()]
        if len(values) < 4:
            raise ValueError(f"invalid calibration: {row['calib']}")
        intrinsics = tuple(values[:4])
    return images, timestamps, intrinsics


def image_target(row: dict, images: list[Path], intrinsics: tuple[float, ...]) -> Path:
    family, scene = row["family"], row["scene"]
    historical = A_DATA / family / scene / "images"
    if historical.is_dir():
        expected = {path.name for path in images}
        observed = {path.name for path in historical.iterdir() if path.is_file() or path.is_symlink()}
        if expected != observed:
            raise RuntimeError(f"benchmark-A image inventory differs: {family}/{scene}")
        return historical.resolve()
    if family != "rpng":
        return Path(row["image_dir"]).resolve()
    cache = IMAGE_CACHE / family / scene
    existing = list(cache.glob("*.png")) if cache.is_dir() else []
    if len(existing) == len(images):
        return cache.resolve()
    if cache.exists():
        raise RuntimeError(f"incomplete undistortion cache preserved: {cache}")
    cache.mkdir(parents=True)
    fx, fy, cx, cy = intrinsics
    camera = np.asarray([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=np.float64)
    distortion = np.asarray(RPNG_DIST, dtype=np.float64)
    for index, source in enumerate(images, 1):
        value = cv2.imread(str(source), cv2.IMREAD_COLOR)
        if value is None:
            raise ValueError(f"could not read {source}")
        destination = cache / source.name
        if not cv2.imwrite(str(destination), cv2.undistort(value, camera, distortion)):
            raise OSError(f"could not write {destination}")
        if index % 1000 == 0:
            print(f"UNDISTORT {family}/{scene} {index}/{len(images)}", flush=True)
    return cache.resolve()


def write_points(source: Path, destination: Path) -> int:
    count = 0
    with source.open() as src, destination.open("x") as dst:
        for point_id, line in enumerate(src):
            fields = line.split()
            if len(fields) < 4:
                raise ValueError(f"invalid point line in {source}: {line!r}")
            xyz = [float(value) for value in fields[1:4]]
            if not np.isfinite(xyz).all():
                raise ValueError(f"nonfinite point in {source}")
            dst.write(f"{point_id} {xyz[0]:.17g} {xyz[1]:.17g} {xyz[2]:.17g} 128 128 128 0\n")
            count += 1
    return count


def valid_dataset(path: Path, stride: int) -> bool:
    required = (
        path / "images", path / "causal_arrivals.json",
        path / "sparse/0/cameras.txt", path / "sparse/0/images.txt",
        path / "sparse/0/points3D.txt", path / "vigs_replay_metadata.json",
    )
    if not all(item.exists() for item in required):
        return False
    metadata = json.loads((path / "vigs_replay_metadata.json").read_text())
    return metadata.get("depth_anchor_stride") == stride


def build_pair(row: dict) -> dict:
    family, scene = row["family"], row["scene"]
    outputs = {stride: OUTPUT_ROOT / family / scene / f"stride{stride}" for stride in (40, 20)}
    if all(valid_dataset(path, stride) for stride, path in outputs.items()):
        control = json.loads((outputs[40] / "vigs_replay_metadata.json").read_text())
        dense = json.loads((outputs[20] / "vigs_replay_metadata.json").read_text())
        return {
            "family": family, "scene": scene, "state": "reused",
            "control_points": control["point_count"],
            "stride20_points": dense["point_count"],
            "density_ratio": dense["point_count"] / control["point_count"],
            "events": dense["events"], "train_frames": dense["train_frames"],
            "heldout_frames": dense["heldout_frames"],
            "pose_source_sha256": dense["pose_source_sha256"],
            "keyframe_source_sha256": dense["keyframe_source_sha256"],
        }
    if any(path.exists() for path in outputs.values()):
        raise RuntimeError(f"incomplete paired dataset preserved: {family}/{scene}")

    source_run = Path(row["output"])
    trajectory_path = source_run / "traj_full_online_eval.txt"
    keyframe_path = source_run / "traj_kf_beforeBA.txt"
    images, timestamps, intrinsics = inventory(row)
    target_images = image_target(row, images, intrinsics)
    trajectory = load_trajectory(trajectory_path)
    keyframes = load_trajectory(keyframe_path)
    positions, rotations_c2w = interpolate_poses(timestamps, trajectory)
    mapped = nearest_indices(keyframes[:, 0], timestamps)
    first_train = next(index for index in range(len(images)) if index % 8 != 0)
    boundaries = mapped[mapped >= first_train]
    if not len(boundaries):
        raise ValueError(f"no usable keyframe boundary: {family}/{scene}")

    sample = cv2.imread(str(images[0]), cv2.IMREAD_COLOR)
    if sample is None:
        raise ValueError(f"could not read sample {images[0]}")
    height, width = sample.shape[:2]
    fx, fy, cx, cy = intrinsics
    image_lines = []
    arrivals = {}
    heldout = []
    for index, (source, position, rotation_c2w) in enumerate(zip(images, positions, rotations_c2w)):
        rotation_w2c = rotation_c2w.T
        translation = -rotation_w2c @ position
        quaternion = qvec(rotation_w2c)
        image_lines.append(
            f"{index + 1} {quaternion[0]:.12g} {quaternion[1]:.12g} "
            f"{quaternion[2]:.12g} {quaternion[3]:.12g} "
            f"{translation[0]:.12g} {translation[1]:.12g} {translation[2]:.12g} "
            f"1 {source.name}\n\n"
        )
        if index % 8 == 0:
            heldout.append(source.name)
        else:
            event = min(int(np.searchsorted(boundaries, index, side="left")), len(boundaries) - 1)
            arrivals[source.name] = 1 + event * 60
    group_sizes = collections.Counter(arrivals.values())
    histogram = collections.Counter(group_sizes.values())
    schedule = {
        "arrival_iteration_by_name": arrivals,
        "total_iterations": max(arrivals.values()), "iters_per_event": 60,
        "tail_iters": 0, "events": len(boundaries), "all_frames": len(images),
        "train_frames": len(arrivals), "heldout_frames": len(heldout),
        "heldout_rule": "sorted COLMAP image index modulo 8 equals zero",
        "interval_definition": "actual VIGS keyframe timestamps mapped to nearest RGB frame",
    }
    common = {
        "kind": family, "scene": scene, "source": row["input"],
        "vigs_run": str(source_run.resolve()),
        "pose_source": "VIGS final online full-frame trajectory",
        "keyframe_source": "VIGS traj_kf_beforeBA keyframe timestamps",
        "pose_source_sha256": sha256(trajectory_path),
        "keyframe_source_sha256": sha256(keyframe_path),
        "raw_vigs_keyframes": len(keyframes),
        "mapped_rgb_keyframe_boundaries": len(mapped),
        "deduplicated_rgb_keyframe_boundaries": len(boundaries),
        "dropped_leading_heldout_only_boundaries": len(mapped) - len(boundaries),
        "max_full_pose_to_rgb_timestamp_error_seconds": float(
            np.max(np.min(np.abs(trajectory[:, 0, None] - timestamps[None, :]), axis=1))
        ),
        "intrinsics": {"fx": fx, "fy": fy, "cx": cx, "cy": cy,
                       "width": width, "height": height},
        "rpng_undistorted": family == "rpng",
        "arrival_group_size_histogram": {
            str(size): count for size, count in sorted(histogram.items())
        },
        "offline_noncausal_fixed_pose_init": True,
        **{key: value for key, value in schedule.items() if key != "arrival_iteration_by_name"},
    }
    counts = {}
    for stride in (40, 20):
        output = outputs[stride]
        sparse = output / "sparse/0"
        sparse.mkdir(parents=True)
        os.symlink(target_images, output / "images", target_is_directory=True)
        (sparse / "cameras.txt").write_text(
            f"1 PINHOLE {width} {height} {fx:.12g} {fy:.12g} {cx:.12g} {cy:.12g}\n"
        )
        (sparse / "images.txt").write_text("".join(image_lines))
        point_source = source_run / ("points3D.txt" if stride == 40 else "points3D_stride20.txt")
        counts[stride] = write_points(point_source, sparse / "points3D.txt")
        (output / "causal_arrivals.json").write_text(json.dumps(schedule, indent=2) + "\n")
        metadata = {
            **common,
            "initialization": f"same-run VIGS BA-refined depth-anchor log, stride{stride}",
            "depth_anchor_stride": stride, "depth_anchor_valid_range_m": [0.01, 20.0],
            "initial_point_color": [128, 128, 128], "point_count": counts[stride],
            "point_source_sha256": sha256(point_source),
            "paired_same_pose_depth_run": True,
        }
        (output / "vigs_replay_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return {
        "family": family, "scene": scene, "state": "built",
        "control_points": counts[40], "stride20_points": counts[20],
        "density_ratio": counts[20] / counts[40],
        "events": len(boundaries), "train_frames": len(arrivals),
        "heldout_frames": len(heldout), "pose_source_sha256": common["pose_source_sha256"],
        "keyframe_source_sha256": common["keyframe_source_sha256"],
    }


def main() -> None:
    source = json.loads(SOURCE_INVENTORY.read_text())
    records = []
    unavailable = {}
    for row in source["records"]:
        label = f"{row['family']}/{row['scene']}"
        if row.get("state") not in ("complete", "reused"):
            unavailable[label] = row.get("reason", "source export failed")
            print(f"UNAVAILABLE {label}", flush=True)
            continue
        record = build_pair(row)
        records.append(record)
        print(f"{record['state'].upper()} {label}", flush=True)
    inventory_path = HERE / "evidence/dataset_inventory.json"
    inventory_path.write_text(json.dumps({
        "protocol": "benchmark-B paired stride40/stride20 fixed replay",
        "records": records, "unavailable": unavailable,
    }, indent=2) + "\n")
    print(inventory_path)


if __name__ == "__main__":
    main()
