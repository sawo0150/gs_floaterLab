#!/usr/bin/env python3
"""Diagnose endpoint interpolation and a causal IMU-shaped rotation curve.

The post-EOS trajectory is used only as an evaluation label in this script.  The
candidate pose construction itself uses the two already-arrived keyframe poses,
raw IMU samples no later than the right endpoint, fixed calibration, and source
timestamps.  It is therefore suitable for deciding whether an online mapper
adapter is worth implementing, but this script never emits training poses.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.spatial.transform import Rotation, Slerp
import torch
import yaml


def rotation_angle_deg(matrix: np.ndarray) -> float:
    value = np.clip((np.trace(matrix) - 1.0) * 0.5, -1.0, 1.0)
    return float(np.degrees(np.arccos(value)))


def slerp_identity(target: np.ndarray, fraction: float) -> np.ndarray:
    rotations = Rotation.from_matrix(np.stack((np.eye(3), target)))
    return Slerp([0.0, 1.0], rotations)([float(fraction)]).as_matrix()[0]


def endpoint_slerp(left: np.ndarray, right: np.ndarray, fraction: float) -> np.ndarray:
    rotations = Rotation.from_matrix(np.stack((left, right)))
    return Slerp([0.0, 1.0], rotations)([float(fraction)]).as_matrix()[0]


def summarize(values: Iterable[float]) -> dict[str, float | int | None]:
    array = np.asarray(list(values), dtype=np.float64)
    if not array.size:
        return {"count": 0, "mean": None, "p50": None, "p90": None, "p95": None, "max": None}
    return {
        "count": int(array.size),
        "mean": float(np.mean(array)),
        "p50": float(np.quantile(array, 0.50)),
        "p90": float(np.quantile(array, 0.90)),
        "p95": float(np.quantile(array, 0.95)),
        "max": float(np.max(array)),
    }


def load_imu(path: Path, config: dict) -> np.ndarray:
    try:
        values = np.loadtxt(path, delimiter=",")
    except ValueError:
        values = np.loadtxt(path, delimiter=" ")
    if bool(config["IMU"].get("imu_in_nanoseconds", False)):
        values[:, 0] /= 1.0e9
    values[:, 0] += float(config["IMU"].get("imu_time_offset", 0.0))
    return values


def integrate_gyro_queries(
    imu: np.ndarray,
    start: float,
    end: float,
    queries: list[float],
) -> dict[float, np.ndarray]:
    """Midpoint-integrate gyro and return body-relative rotations at queries."""
    if not start < end:
        raise ValueError(f"non-positive IMU interval: {start} -> {end}")
    available_end = int(np.searchsorted(imu[:, 0], end, side="right"))
    available = imu[:available_end]
    if len(available) < 2:
        raise ValueError(f"insufficient causal IMU samples through {end:.9f}")
    query_values = sorted(set(float(value) for value in queries + [start, end]))
    left = max(0, int(np.searchsorted(available[:, 0], start, side="right")) - 1)
    sample_times = available[left:, 0]
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


def endpoint_preserving_accel_shape(
    imu: np.ndarray,
    start: float,
    end: float,
    queries: list[float],
    r_wb_left: np.ndarray,
) -> dict[float, np.ndarray]:
    """Double-integrate causal IMU acceleration as zero-endpoint curvature.

    Constant acceleration in world coordinates contains gravity and most
    accelerometer bias over a short keyframe interval, so it is removed before
    integration.  A final linear displacement trend is also removed.  The
    resulting residual is exactly zero at both visual keyframe endpoints and
    therefore changes only the within-interval translation shape.
    """
    if imu.shape[1] < 7:
        raise ValueError("IMU rows do not contain accelerometer xyz columns")
    available_end = int(np.searchsorted(imu[:, 0], end, side="right"))
    available = imu[:available_end]
    left = max(0, int(np.searchsorted(available[:, 0], start, side="right")) - 1)
    sample_times = available[left:, 0]
    knots = np.unique(
        np.concatenate(
            (
                np.asarray(queries + [start, end], dtype=np.float64),
                sample_times[(sample_times > start) & (sample_times < end)],
            )
        )
    )
    knots = knots[(knots >= start) & (knots <= end)]
    gyro_curve = integrate_gyro_queries(
        imu, start, end, [float(value) for value in knots]
    )
    accel_body = np.column_stack(
        [np.interp(knots, available[:, 0], available[:, axis]) for axis in range(4, 7)]
    )
    accel_world = np.stack(
        [
            (r_wb_left @ gyro_curve[float(timestamp)]) @ value
            for timestamp, value in zip(knots, accel_body)
        ]
    )
    duration = float(end - start)
    mean_accel = np.trapezoid(accel_world, knots, axis=0) / duration
    accel_world -= mean_accel

    velocity = np.zeros_like(accel_world)
    displacement = np.zeros_like(accel_world)
    for position in range(1, len(knots)):
        dt = float(knots[position] - knots[position - 1])
        velocity[position] = velocity[position - 1] + 0.5 * (
            accel_world[position - 1] + accel_world[position]
        ) * dt
        displacement[position] = displacement[position - 1] + 0.5 * (
            velocity[position - 1] + velocity[position]
        ) * dt
    beta = ((knots - start) / duration)[:, None]
    displacement -= beta * displacement[-1]
    return {
        float(timestamp): displacement[position].copy()
        for position, timestamp in enumerate(knots)
        if float(timestamp) in set(float(value) for value in queries)
    }


def extrapolate_left_rotation(
    pose_a: np.ndarray,
    alpha_a: float,
    pose_b: np.ndarray,
    alpha_b: float,
) -> np.ndarray:
    """Recover the causal left-endpoint rotation from two archived SE3 samples."""
    if not alpha_b > alpha_a:
        raise ValueError("translation diagnostic needs increasing interpolation samples")
    r_a = pose_a[:3, :3]
    r_b = pose_b[:3, :3]
    increment = Rotation.from_matrix(r_b @ r_a.T).as_rotvec() / (
        alpha_b - alpha_a
    )
    return Rotation.from_rotvec(-alpha_a * increment).as_matrix() @ r_a


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    archive = args.archive.resolve()
    manifest = json.loads((archive / "archive_manifest.json").read_text())
    arrivals = [
        json.loads(line)
        for line in (archive / manifest["arrivals"]).read_text().splitlines()
        if line.strip()
    ]
    timestamps = np.asarray(
        [float(record["sensor_timestamp"]) for record in arrivals], dtype=np.float64
    )
    config_path = Path(manifest["input_config"])
    config = yaml.safe_load(config_path.read_text())
    imu_path_value = manifest.get("input_imu")
    if imu_path_value is None:
        image_dir = Path(manifest["input_image_directory"])
        imu_path_value = image_dir.parent / (
            "imu_ours.txt" if manifest["dataset"] == "utmm" else "imu.txt"
        )
    imu_path = Path(imu_path_value)
    imu = load_imu(imu_path, config)
    t_cb = np.asarray(config["IMU"]["Tcb_np"], dtype=np.float64)
    r_cb = t_cb[:3, :3]
    r_bc = r_cb.T

    final_state = torch.load(
        archive / manifest["final_tracker_state"], map_location="cpu", weights_only=False
    )
    evaluation = torch.load(
        archive / manifest["evaluation_only_post_eos_trajectory"],
        map_location="cpu",
        weights_only=False,
    )
    final_uids = [int(value) for value in final_state["keyframe_uids"].tolist()]
    final_pose_by_uid = {}
    for uid, vector in zip(final_uids, final_state["keyframe_poses_w2c"]):
        value = vector.numpy().astype(np.float64)
        matrix = np.eye(4)
        matrix[:3, :3] = Rotation.from_quat(value[3:7]).as_matrix()
        matrix[:3, 3] = value[:3]
        final_pose_by_uid[uid] = matrix
    evaluation_w2c = evaluation["poses_w2c_matrix"].numpy().astype(np.float64)
    heldout = {
        int(record["frame_uid"]) for record in arrivals if bool(record["held_out"])
    }

    rows: list[dict[str, float | int]] = []
    seen_uids: set[int] = set()
    skipped_missing_final_endpoint = 0
    for interval_metadata in manifest["dense_intervals"]:
        interval = torch.load(
            archive / interval_metadata["payload"], map_location="cpu", weights_only=False
        )
        left_uid = int(interval["left_keyframe_uid"])
        right_uid = int(interval["right_keyframe_uid"])
        if left_uid not in final_pose_by_uid or right_uid not in final_pose_by_uid:
            skipped_missing_final_endpoint += int(interval["candidate_uids"].numel())
            continue
        candidates: list[tuple[int, np.ndarray]] = []
        for uid_tensor, pose_tensor in zip(
            interval["candidate_uids"], interval["interpolated_poses_w2c"]
        ):
            uid = int(uid_tensor.item())
            if uid in heldout or uid in seen_uids:
                continue
            seen_uids.add(uid)
            candidates.append((uid, pose_tensor.numpy().astype(np.float64)))
        if not candidates:
            continue

        start = float(timestamps[left_uid])
        end = float(timestamps[right_uid])
        query_times = [float(timestamps[uid]) for uid, _ in candidates]
        gyro_curve = integrate_gyro_queries(imu, start, end, query_times)
        gyro_end = gyro_curve[end]

        accel_shape = None
        if len(candidates) >= 2:
            uid_a, pose_a = candidates[0]
            uid_b, pose_b = candidates[-1]
            alpha_a = float(uid_a - left_uid) / float(right_uid - left_uid)
            alpha_b = float(uid_b - left_uid) / float(right_uid - left_uid)
            causal_left_w2c_rotation = extrapolate_left_rotation(
                pose_a, alpha_a, pose_b, alpha_b
            )
            causal_r_wb_left = causal_left_w2c_rotation.T @ r_cb
            accel_shape = endpoint_preserving_accel_shape(
                imu, start, end, query_times, causal_r_wb_left
            )

        left_w2c = final_pose_by_uid[left_uid]
        right_w2c = final_pose_by_uid[right_uid]
        r_wc_left = left_w2c[:3, :3].T
        r_wc_right = right_w2c[:3, :3].T
        r_wb_left = r_wc_left @ r_cb
        r_wb_right = r_wc_right @ r_cb
        visual_body_endpoint = r_wb_left.T @ r_wb_right
        correction_right = gyro_end.T @ visual_body_endpoint
        correction_left = visual_body_endpoint @ gyro_end.T
        endpoint_rotation_deg = rotation_angle_deg(visual_body_endpoint)
        gyro_endpoint_disagreement_deg = rotation_angle_deg(
            gyro_end.T @ visual_body_endpoint
        )

        for uid, original_w2c in candidates:
            timestamp = float(timestamps[uid])
            beta = (timestamp - start) / (end - start)
            alpha = float(uid - left_uid) / float(right_uid - left_uid)
            gyro_now = gyro_curve[timestamp]
            gyro_linear = slerp_identity(gyro_end, beta)
            gyro_curvature_deg = rotation_angle_deg(gyro_linear.T @ gyro_now)

            visual_body_now = slerp_identity(visual_body_endpoint, beta)
            curvature_right = gyro_linear.T @ gyro_now
            curvature_left = gyro_now @ gyro_linear.T
            body_shape_right = visual_body_now @ curvature_right
            body_shape_left = curvature_left @ visual_body_now

            body_right = gyro_now @ slerp_identity(correction_right, beta)
            body_left = slerp_identity(correction_left, beta) @ gyro_now
            r_wc_imu_right = r_wb_left @ body_right @ r_bc
            r_wc_imu_left = r_wb_left @ body_left @ r_bc
            r_wc_shape_right = r_wb_left @ body_shape_right @ r_bc
            r_wc_shape_left = r_wb_left @ body_shape_left @ r_bc
            r_wc_slerp = endpoint_slerp(r_wc_left, r_wc_right, beta)
            gt_w2c = evaluation_w2c[uid]
            r_wc_gt = gt_w2c[:3, :3].T

            original_rotation_error = rotation_angle_deg(
                original_w2c[:3, :3] @ gt_w2c[:3, :3].T
            )
            slerp_rotation_error = rotation_angle_deg(r_wc_slerp.T @ r_wc_gt)
            imu_right_error = rotation_angle_deg(r_wc_imu_right.T @ r_wc_gt)
            imu_left_error = rotation_angle_deg(r_wc_imu_left.T @ r_wc_gt)
            shape_right_error = rotation_angle_deg(r_wc_shape_right.T @ r_wc_gt)
            shape_left_error = rotation_angle_deg(r_wc_shape_left.T @ r_wc_gt)
            original_center = -original_w2c[:3, :3].T @ original_w2c[:3, 3]
            gt_center = -gt_w2c[:3, :3].T @ gt_w2c[:3, 3]
            final_left_center = (
                -left_w2c[:3, :3].T @ left_w2c[:3, 3]
            )
            final_right_center = (
                -right_w2c[:3, :3].T @ right_w2c[:3, 3]
            )
            final_linear_center = (
                (1.0 - beta) * final_left_center + beta * final_right_center
            )
            acceleration_residual = (
                np.zeros(3)
                if accel_shape is None
                else accel_shape[timestamp]
            )
            rows.append(
                {
                    "uid": uid,
                    "left_uid": left_uid,
                    "right_uid": right_uid,
                    "interval_frames": right_uid - left_uid,
                    "alpha_uid": alpha,
                    "beta_time": beta,
                    "endpoint_fraction": min(alpha, 1.0 - alpha),
                    "endpoint_rotation_deg": endpoint_rotation_deg,
                    "endpoint_rotation_deg_per_second": endpoint_rotation_deg / (end - start),
                    "gyro_endpoint_disagreement_deg": gyro_endpoint_disagreement_deg,
                    "gyro_curvature_deg": gyro_curvature_deg,
                    "original_translation_error_m": float(
                        np.linalg.norm(original_center - gt_center)
                    ),
                    "final_endpoint_linear_translation_error_m": float(
                        np.linalg.norm(final_linear_center - gt_center)
                    ),
                    "causal_accel_shape_norm_m": float(
                        np.linalg.norm(acceleration_residual)
                    ),
                    "causal_accel_plus_025_translation_error_m": float(
                        np.linalg.norm(
                            original_center + 0.25 * acceleration_residual - gt_center
                        )
                    ),
                    "causal_accel_plus_050_translation_error_m": float(
                        np.linalg.norm(
                            original_center + 0.50 * acceleration_residual - gt_center
                        )
                    ),
                    "causal_accel_plus_100_translation_error_m": float(
                        np.linalg.norm(original_center + acceleration_residual - gt_center)
                    ),
                    "causal_accel_minus_100_translation_error_m": float(
                        np.linalg.norm(original_center - acceleration_residual - gt_center)
                    ),
                    "original_rotation_error_deg": original_rotation_error,
                    "final_endpoint_slerp_rotation_error_deg": slerp_rotation_error,
                    "final_endpoint_imu_right_rotation_error_deg": imu_right_error,
                    "final_endpoint_imu_left_rotation_error_deg": imu_left_error,
                    "final_endpoint_imu_shape_right_rotation_error_deg": shape_right_error,
                    "final_endpoint_imu_shape_left_rotation_error_deg": shape_left_error,
                    "imu_right_improvement_deg": slerp_rotation_error - imu_right_error,
                    "imu_left_improvement_deg": slerp_rotation_error - imu_left_error,
                    "imu_shape_right_improvement_deg": slerp_rotation_error
                    - shape_right_error,
                    "imu_shape_left_improvement_deg": slerp_rotation_error
                    - shape_left_error,
                }
            )

    metric_names = (
        "original_translation_error_m",
        "final_endpoint_linear_translation_error_m",
        "causal_accel_shape_norm_m",
        "causal_accel_plus_025_translation_error_m",
        "causal_accel_plus_050_translation_error_m",
        "causal_accel_plus_100_translation_error_m",
        "causal_accel_minus_100_translation_error_m",
        "original_rotation_error_deg",
        "final_endpoint_slerp_rotation_error_deg",
        "final_endpoint_imu_right_rotation_error_deg",
        "final_endpoint_imu_left_rotation_error_deg",
        "final_endpoint_imu_shape_right_rotation_error_deg",
        "final_endpoint_imu_shape_left_rotation_error_deg",
        "imu_right_improvement_deg",
        "imu_left_improvement_deg",
        "imu_shape_right_improvement_deg",
        "imu_shape_left_improvement_deg",
        "gyro_curvature_deg",
        "gyro_endpoint_disagreement_deg",
        "endpoint_rotation_deg_per_second",
    )
    summary = {name: summarize(float(row[name]) for row in rows) for name in metric_names}
    summary["imu_right_fraction_improved"] = (
        float(np.mean([row["imu_right_improvement_deg"] > 0 for row in rows]))
        if rows
        else None
    )
    summary["imu_left_fraction_improved"] = (
        float(np.mean([row["imu_left_improvement_deg"] > 0 for row in rows]))
        if rows
        else None
    )
    summary["imu_shape_right_fraction_improved"] = (
        float(np.mean([row["imu_shape_right_improvement_deg"] > 0 for row in rows]))
        if rows
        else None
    )
    summary["imu_shape_left_fraction_improved"] = (
        float(np.mean([row["imu_shape_left_improvement_deg"] > 0 for row in rows]))
        if rows
        else None
    )
    result = {
        "protocol": "exp78b_dense_imu_pose_diagnostic_v1",
        "archive": str(archive),
        "dataset": manifest["dataset"],
        "sequence": manifest["sequence"],
        "seed": manifest["seed"],
        "causal_candidate_inputs": [
            "raw IMU through right keyframe timestamp",
            "fixed Tcb calibration",
            "left and right tracker keyframe orientations",
            "source RGB timestamps",
        ],
        "evaluation_label_only": manifest["evaluation_only_post_eos_trajectory"],
        "evaluation_trajectory_mapping_supervision_allowed": False,
        "unique_candidates_evaluated": len(rows),
        "candidate_occurrences_skipped_missing_surviving_final_endpoint": skipped_missing_final_endpoint,
        "summary": summary,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ["uid"])
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
