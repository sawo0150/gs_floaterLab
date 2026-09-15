#!/usr/bin/env python3
"""Strict-causal raw-IMU rotation shaping for exp78 dense RGB replay."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation, Slerp
import torch
import yaml


PROTOCOL = "exp78b_dense_imu_rotation_shape_v1"


def _slerp_identity(target: np.ndarray, fraction: float) -> np.ndarray:
    rotations = Rotation.from_matrix(np.stack((np.eye(3), target)))
    return Slerp([0.0, 1.0], rotations)([float(fraction)]).as_matrix()[0]


def load_processed_imu(path: Path, config: dict) -> np.ndarray:
    try:
        values = np.loadtxt(path, delimiter=",")
    except ValueError:
        values = np.loadtxt(path, delimiter=" ")
    if bool(config["IMU"].get("imu_in_nanoseconds", False)):
        values[:, 0] /= 1.0e9
    values[:, 0] += float(config["IMU"].get("imu_time_offset", 0.0))
    if np.any(np.diff(values[:, 0]) <= 0):
        raise ValueError(f"IMU timestamps are not strictly increasing: {path}")
    return values


def integrate_gyro_queries_strict_causal(
    imu: np.ndarray,
    start: float,
    end: float,
    queries: list[float],
) -> dict[float, np.ndarray]:
    """Integrate gyro using no sample whose adjusted timestamp exceeds end."""
    if not start < end:
        raise ValueError(f"non-positive IMU interval: {start} -> {end}")
    available_end = int(np.searchsorted(imu[:, 0], end, side="right"))
    available = imu[:available_end]
    if len(available) < 2:
        raise ValueError(f"insufficient causal IMU samples through {end:.9f}")
    query_values = sorted(set(float(value) for value in queries + [start, end]))
    left = max(0, int(np.searchsorted(available[:, 0], start, side="right")) - 1)
    interval = available[left:]
    sample_times = interval[:, 0]
    knots = np.unique(
        np.concatenate(
            (
                np.asarray(query_values, dtype=np.float64),
                sample_times[(sample_times > start) & (sample_times < end)],
            )
        )
    )
    knots = knots[(knots >= start) & (knots <= end)]
    gyro = np.column_stack(
        [
            np.interp(knots, available[:, 0], available[:, axis])
            for axis in range(1, 4)
        ]
    )
    current = np.eye(3)
    output = {float(knots[0]): current.copy()}
    query_set = set(query_values)
    for position in range(1, len(knots)):
        dt = float(knots[position] - knots[position - 1])
        omega = 0.5 * (gyro[position - 1] + gyro[position])
        current = current @ Rotation.from_rotvec(omega * dt).as_matrix()
        timestamp = float(knots[position])
        if timestamp in query_set:
            output[timestamp] = current.copy()
    missing = [value for value in query_values if value not in output]
    if missing:
        raise RuntimeError(f"failed to integrate query timestamps: {missing[:3]}")
    return output


class CausalImuDensePoseShaper:
    """Add raw-gyro within-keyframe curvature without changing camera centers."""

    def __init__(self, archive) -> None:
        self.archive = archive
        manifest = archive.manifest
        config_path = Path(manifest["input_config"])
        self.config = yaml.safe_load(config_path.read_text())
        imu_value = manifest.get("input_imu")
        if imu_value is None:
            image_dir = Path(manifest["input_image_directory"])
            imu_value = image_dir.parent / (
                "imu_ours.txt" if manifest["dataset"] == "utmm" else "imu.txt"
            )
        self.imu_path = Path(imu_value).resolve()
        self.imu = load_processed_imu(self.imu_path, self.config)
        self.r_cb = np.asarray(self.config["IMU"]["Tcb_np"], dtype=np.float64)[
            :3, :3
        ]
        self.r_bc = self.r_cb.T
        self.timestamps = {
            int(record["frame_uid"]): float(record["sensor_timestamp"])
            for record in archive.arrivals
        }
        self.left_residual_by_uid: dict[int, torch.Tensor] = {}
        self.curvature_by_uid: dict[int, float] = {}
        self.intervals = 0
        self.records = 0
        self.max_imu_timestamp_consumed = -float("inf")
        self.max_right_endpoint_timestamp = -float("inf")
        self.max_future_imu_margin_seconds = -float("inf")
        self.curvature_degrees: list[float] = []

    def shape_records(
        self,
        metadata: dict,
        records: list[tuple],
    ) -> list[tuple]:
        if not records:
            return records
        interval = self.archive.load_dense_interval(metadata)
        left_uid = int(interval["left_keyframe_uid"])
        right_uid = int(interval["right_keyframe_uid"])
        start = self.timestamps[left_uid]
        end = self.timestamps[right_uid]
        query_times = [self.timestamps[int(record[0])] for record in records]
        curve = integrate_gyro_queries_strict_causal(
            self.imu, start, end, query_times
        )
        gyro_end = curve[end]
        maximum_consumed = float(self.imu[self.imu[:, 0] <= end, 0][-1])
        self.max_imu_timestamp_consumed = max(
            self.max_imu_timestamp_consumed, maximum_consumed
        )
        self.max_right_endpoint_timestamp = max(
            self.max_right_endpoint_timestamp, end
        )
        self.max_future_imu_margin_seconds = max(
            self.max_future_imu_margin_seconds, maximum_consumed - end
        )

        shaped = []
        for record in records:
            uid = int(record[0])
            pose = record[2].detach().cpu().clone()
            beta = (self.timestamps[uid] - start) / (end - start)
            gyro_now = curve[self.timestamps[uid]]
            gyro_linear = _slerp_identity(gyro_end, beta)
            curvature_body = gyro_linear.T @ gyro_now
            camera_right_correction = self.r_cb @ curvature_body @ self.r_bc
            w2c_left_correction = camera_right_correction.T
            residual = torch.eye(4, dtype=pose.dtype)
            residual[:3, :3] = torch.as_tensor(
                w2c_left_correction, dtype=pose.dtype
            )
            corrected = residual @ pose
            self.left_residual_by_uid[uid] = residual
            shaped.append((record[0], record[1], corrected, *record[3:]))
            curvature_degrees = float(
                np.degrees(Rotation.from_matrix(curvature_body).magnitude())
            )
            self.curvature_by_uid[uid] = curvature_degrees
            self.curvature_degrees.append(curvature_degrees)
        self.intervals += 1
        self.records += len(shaped)
        return shaped

    def summary(self) -> dict[str, object]:
        values = np.asarray(self.curvature_degrees, dtype=np.float64)
        return {
            "protocol": PROTOCOL,
            "imu_path": str(self.imu_path),
            "imu_sha256": hashlib.sha256(self.imu_path.read_bytes()).hexdigest(),
            "intervals_shaped": self.intervals,
            "records_shaped": self.records,
            "left_residuals_stored": len(self.left_residual_by_uid),
            "curvature_degrees": {
                "mean": float(np.mean(values)) if values.size else None,
                "p50": float(np.quantile(values, 0.50)) if values.size else None,
                "p90": float(np.quantile(values, 0.90)) if values.size else None,
                "p95": float(np.quantile(values, 0.95)) if values.size else None,
                "max": float(np.max(values)) if values.size else None,
            },
            "max_imu_timestamp_consumed": (
                self.max_imu_timestamp_consumed
                if np.isfinite(self.max_imu_timestamp_consumed)
                else None
            ),
            "max_right_endpoint_timestamp": (
                self.max_right_endpoint_timestamp
                if np.isfinite(self.max_right_endpoint_timestamp)
                else None
            ),
            "max_future_imu_margin_seconds": (
                self.max_future_imu_margin_seconds
                if np.isfinite(self.max_future_imu_margin_seconds)
                else None
            ),
            "strict_causal_imu_pass": bool(
                self.max_future_imu_margin_seconds <= 0.0
            ),
            "translation_changed_by_rotation_shape": False,
            "post_eos_trajectory_used": False,
        }
