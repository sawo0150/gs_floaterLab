#!/usr/bin/env python3
"""Capture a causal, mapper-independent VIGS tracker trace for exp78 Lane B.

The official tracker is run with its Gaussian backend replaced by an archive
sink.  The sink records every packet the tracker would have sent to mapping,
including PGBA pose/scale corrections.  RGB inputs remain tied to the immutable
prepared-dataset file list plus the exact official preprocessing contract;
depth/normal tensors are content-addressed so repeated keyframe packets do not
explode the archive size.

No Gaussian optimization is performed by this program.  A post-EOS full
trajectory is saved only as evaluation-pose metadata and is explicitly marked
non-causal; it must never be consumed as mapping supervision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import queue as thread_queue
import random
import re
import resource
import threading
import time
import types
from typing import Any

import cv2
from lietorch import SE3
import numpy as np
import torch
import yaml
from torch.multiprocessing import Event, Process, Queue
from tqdm import tqdm

from vigs import VIGS


SCHEMA_VERSION = "exp78b_frozen_tracker_v3"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def tensor_digest(*tensors: torch.Tensor) -> str:
    digest = hashlib.sha256()
    for tensor in tensors:
        contiguous = tensor.detach().cpu().contiguous()
        digest.update(str(contiguous.dtype).encode("ascii"))
        digest.update(np.asarray(contiguous.shape, dtype=np.int64).tobytes())
        digest.update(contiguous.numpy().tobytes(order="C"))
    return digest.hexdigest()


def ordered_image_names(imagedir: str, start: int, length: int, stride: int) -> list[str]:
    try:
        names = sorted(
            os.listdir(imagedir),
            key=lambda name: float(os.path.basename(name)[:-4]),
        )
    except ValueError:
        names = sorted(os.listdir(imagedir))
    return names[start : start + length][::stride]


def load_eval_indices(path: Path, names: list[str]) -> tuple[set[int], dict[str, Any]]:
    manifest = json.loads(path.read_text())
    indices = {int(record["frame_index"]) for record in manifest["views"]}
    expected = {index for index in range(len(names)) if index % 5 == 0}
    if names:
        expected.add(len(names) - 1)
    if indices != expected:
        raise ValueError(
            "held-out manifest is not the locked idx%5-or-final contract: "
            f"manifest={len(indices)} expected={len(expected)}"
        )
    if int(manifest["frame_count"]) != len(names):
        raise ValueError(
            f"held-out frame_count={manifest['frame_count']} input={len(names)}"
        )
    return indices, manifest


def mono_stream(
    output_queue: Queue,
    consumer_finished: Event,
    imagedir: str,
    calib: str,
    undistort: bool,
    cropborder: int,
    start: int,
    length: int,
    stride: int,
    rgb_file_in_nanoseconds: bool,
) -> None:
    """Mirror official demo.py preprocessing exactly."""
    target_pixels = 341 * 640
    calibration = np.loadtxt(calib, delimiter=" ")
    camera_matrix = np.array(
        [
            [calibration[0], 0, calibration[2]],
            [0, calibration[1], calibration[3]],
            [0, 0, 1],
        ]
    )
    names = ordered_image_names(imagedir, start, length, stride)
    for index, name in enumerate(names):
        timestamp = float(re.findall(r"[+]?(?:\d*\.\d+|\d+)", name)[-1])
        if rgb_file_in_nanoseconds:
            timestamp /= 1e9
        image = cv2.imread(os.path.join(imagedir, name))
        if image is None:
            raise FileNotFoundError(os.path.join(imagedir, name))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        intrinsics = torch.tensor(calibration[:4])
        if len(calibration) > 4 and undistort:
            image = cv2.undistort(image, camera_matrix, calibration[4:])
        if cropborder > 0:
            image = image[cropborder:-cropborder, cropborder:-cropborder]
            intrinsics[2:] -= cropborder
        height0, width0, _ = image.shape
        height1 = int(height0 * np.sqrt(target_pixels / (height0 * width0)))
        width1 = int(width0 * np.sqrt(target_pixels / (height0 * width0)))
        height1 -= height1 % 8
        width1 -= width1 % 8
        image = cv2.resize(image, (width1, height1))
        image_tensor = torch.as_tensor(image).permute(2, 0, 1)
        intrinsics[[0, 2]] *= width1 / width0
        intrinsics[[1, 3]] *= height1 / height0
        output_queue.put(
            (
                index,
                timestamp,
                name,
                image_tensor[None],
                intrinsics[None],
                index == len(names) - 1,
            )
        )
    consumer_finished.wait()


class TrackerArchiveWriter:
    """Asynchronously persist immutable copies made inside tracker callbacks."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.events_dir = root / "events"
        self.geometry_dir = root / "geometry"
        self.depth_dir = self.geometry_dir / "depth"
        self.normal_dir = self.geometry_dir / "normal"
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.depth_dir.mkdir(parents=True, exist_ok=True)
        self.normal_dir.mkdir(parents=True, exist_ok=True)
        self.work: thread_queue.Queue[dict[str, Any] | None] = thread_queue.Queue(
            maxsize=8
        )
        self.events: list[dict[str, Any]] = []
        self._depth_paths: dict[str, str] = {}
        self._normal_paths: dict[str, str] = {}
        self.error: BaseException | None = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def submit(self, record: dict[str, Any]) -> None:
        if self.error is not None:
            raise RuntimeError("archive writer failed") from self.error
        self.work.put(record)

    def close(self) -> None:
        self.work.put(None)
        self.work.join()
        self.thread.join()
        if self.error is not None:
            raise RuntimeError("archive writer failed") from self.error

    @staticmethod
    def _atomic_torch_save(value: object, path: Path) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        torch.save(value, temporary)
        temporary.replace(path)

    def _run(self) -> None:
        try:
            while True:
                record = self.work.get()
                if record is None:
                    self.work.task_done()
                    break
                self._write_event(record)
                self.work.task_done()
        except BaseException as error:  # surface worker failures to main
            self.error = error
            self.work.task_done()
            while True:
                try:
                    pending = self.work.get_nowait()
                except thread_queue.Empty:
                    break
                self.work.task_done()
                if pending is None:
                    break

    def _write_event(self, record: dict[str, Any]) -> None:
        if record["kind"] in {"metric_rescale", "mapper_reset"}:
            event_id = int(record["event_id"])
            relative_event = f"events/{event_id:06d}.pt"
            destination = self.root / relative_event
            self._atomic_torch_save(record, destination)
            self.events.append(
                {
                    "event_id": event_id,
                    "kind": record["kind"],
                    "emitted_at_frame_uid": int(record["emitted_at_frame_uid"]),
                    "emitted_at_sensor_timestamp": float(
                        record["emitted_at_sensor_timestamp"]
                    ),
                    "frame_count": 0,
                    "frame_uids": [],
                    "payload": relative_event,
                    "payload_sha256": sha256_file(destination),
                    "geometry_refs": [],
                }
            )
            return
        geometry_refs: list[dict[str, str | int]] = []
        for uid, depth, normal in zip(
            record["frame_uids"].tolist(),
            record.pop("depths"),
            record.pop("normals"),
        ):
            depth_digest = tensor_digest(depth)
            normal_digest = tensor_digest(normal)
            combined_digest = tensor_digest(depth, normal)
            depth_relative = self._depth_paths.get(depth_digest)
            if depth_relative is None:
                depth_relative = f"geometry/depth/{int(uid):06d}_{depth_digest}.pt"
                destination = self.root / depth_relative
                if not destination.exists():
                    self._atomic_torch_save(
                        {
                            "schema_version": SCHEMA_VERSION,
                            "tensor_kind": "depth",
                            "frame_uid_at_capture": int(uid),
                            "sha256_tensor_payload": depth_digest,
                            # A view selected from a batched tensor retains the
                            # parent's storage. Clone it before serialization.
                            "tensor": depth.detach().clone(),
                        },
                        destination,
                    )
                self._depth_paths[depth_digest] = depth_relative
            normal_relative = self._normal_paths.get(normal_digest)
            if normal_relative is None:
                normal_relative = f"geometry/normal/{int(uid):06d}_{normal_digest}.pt"
                destination = self.root / normal_relative
                if not destination.exists():
                    self._atomic_torch_save(
                        {
                            "schema_version": SCHEMA_VERSION,
                            "tensor_kind": "normal",
                            "frame_uid_at_capture": int(uid),
                            "sha256_tensor_payload": normal_digest,
                            "tensor": normal.detach().clone(),
                        },
                        destination,
                    )
                self._normal_paths[normal_digest] = normal_relative
            geometry_refs.append(
                {
                    "frame_uid_at_capture": int(uid),
                    "sha256_tensor_payload": combined_digest,
                    "depth": depth_relative,
                    "normal": normal_relative,
                }
            )
        record["geometry_refs"] = geometry_refs
        event_id = int(record["event_id"])
        relative_event = f"events/{event_id:06d}.pt"
        destination = self.root / relative_event
        self._atomic_torch_save(record, destination)
        event_hash = sha256_file(destination)
        self.events.append(
            {
                "event_id": event_id,
                "kind": record["kind"],
                "emitted_at_frame_uid": int(record["emitted_at_frame_uid"]),
                "emitted_at_sensor_timestamp": float(
                    record["emitted_at_sensor_timestamp"]
                ),
                "frame_count": int(record["frame_uids"].numel()),
                "frame_uids": [int(value) for value in record["frame_uids"].tolist()],
                "payload": relative_event,
                "payload_sha256": event_hash,
                "geometry_refs": geometry_refs,
            }
        )


class FrozenTrackerCapture:
    def __init__(
        self,
        writer: TrackerArchiveWriter,
        eval_indices: set[int],
        image_names: list[str],
    ) -> None:
        self.writer = writer
        self.eval_indices = eval_indices
        self.image_names = image_names
        self.current_uid = -1
        self.current_sensor_timestamp = float("nan")
        self.event_count = 0
        self.seen_intervals: set[tuple[int, int]] = set()
        self.dense_intervals: list[dict[str, Any]] = []

    def set_arrival(self, uid: int, sensor_timestamp: float) -> None:
        self.current_uid = int(uid)
        self.current_sensor_timestamp = float(sensor_timestamp)

    def call_gs(
        self,
        vigs: VIGS,
        viz_idx: torch.Tensor,
        dposes: Any = None,
        dscale: torch.Tensor | None = None,
        final: bool = False,
        update_idx: torch.Tensor | None = None,
        blocking: bool = False,
    ) -> None:
        if final:
            raise RuntimeError("frozen tracker capture must stop before final BA")
        viz_cpu = viz_idx.detach().to(device="cpu", dtype=torch.long)
        frame_uids = vigs.video.tstamp[viz_idx].detach().to(device="cpu").long()
        poses = vigs.video.poses[viz_idx].detach().to(device="cpu").clone()
        intrinsics = (
            vigs.video.intrinsics[viz_idx].detach().to(device="cpu").clone() * 8
        )
        depths = (
            1.0 / vigs.video.disps_up[viz_cpu].detach().to(device="cpu")
        ).clone()
        normals = vigs.video.normals[viz_cpu].detach().to(device="cpu").clone()
        pose_update_data = None
        if dposes is not None:
            pose_update_data = dposes.data.detach().to(device="cpu").clone()
        scale_updates = (
            None
            if dscale is None
            else dscale.detach().to(device="cpu").clone()
        )
        update_indices = (
            None
            if update_idx is None
            else update_idx.detach().to(device="cpu").clone()
        )
        record = {
            "schema_version": SCHEMA_VERSION,
            "event_id": self.event_count,
            "kind": "pose_scale_correction" if dposes is not None else "keyframe_update",
            "emitted_at_frame_uid": self.current_uid,
            "emitted_at_sensor_timestamp": self.current_sensor_timestamp,
            "original_viz_idx": viz_cpu.clone(),
            "frame_uids": frame_uids,
            "poses": poses,
            "intrinsics": intrinsics,
            "depths": depths,
            "normals": normals,
            "pose_updates_data": pose_update_data,
            "scale_updates": scale_updates,
            "original_update_idx": update_indices,
            "blocking_requested": bool(blocking),
            "final": False,
        }
        self.writer.submit(record)
        self.event_count += 1

    def metric_rescale(self, scale: float) -> None:
        record = {
            "schema_version": SCHEMA_VERSION,
            "event_id": self.event_count,
            "kind": "metric_rescale",
            "emitted_at_frame_uid": self.current_uid,
            "emitted_at_sensor_timestamp": self.current_sensor_timestamp,
            "scale": float(scale),
            "final": False,
        }
        self.writer.submit(record)
        self.event_count += 1

    def mapper_reset(self) -> None:
        record = {
            "schema_version": SCHEMA_VERSION,
            "event_id": self.event_count,
            "kind": "mapper_reset",
            "emitted_at_frame_uid": self.current_uid,
            "emitted_at_sensor_timestamp": self.current_sensor_timestamp,
            "final": False,
        }
        self.writer.submit(record)
        self.event_count += 1

    def capture_new_dense_intervals(self, vigs: VIGS) -> None:
        """Save causal endpoint-interpolated poses after the right KF arrives."""
        keyframe_count = int(vigs.video.counter.value)
        if keyframe_count < 2:
            return
        keyframe_uids = [
            int(value)
            for value in vigs.video.tstamp[:keyframe_count].detach().cpu().tolist()
        ]
        keyframe_uid_set = set(keyframe_uids)
        for right_position in range(1, keyframe_count):
            left_position = right_position - 1
            left_uid = keyframe_uids[right_position - 1]
            right_uid = keyframe_uids[right_position]
            interval = (left_uid, right_uid)
            if interval in self.seen_intervals or right_uid <= left_uid:
                continue
            self.seen_intervals.add(interval)
            candidate_uids = [
                uid
                for uid in range(left_uid + 1, right_uid)
                if uid not in keyframe_uid_set and uid not in self.eval_indices
            ]
            pose_matrices = torch.empty((0, 4, 4), dtype=torch.float32)
            if candidate_uids:
                pose_left = SE3(
                    vigs.video.poses[left_position : left_position + 1]
                )
                pose_right = SE3(
                    vigs.video.poses[right_position : right_position + 1]
                )
                alpha = torch.as_tensor(
                    [
                        float(uid - left_uid) / float(right_uid - left_uid)
                        for uid in candidate_uids
                    ],
                    dtype=torch.float32,
                    device=vigs.video.poses.device,
                ).unsqueeze(1)
                pose_matrices = (
                    SE3.exp((pose_right * pose_left.inv()).log() * alpha)
                    * pose_left
                ).matrix().data.detach().cpu()
            interval_id = len(self.dense_intervals)
            relative = f"dense_intervals/{interval_id:06d}.pt"
            destination = self.writer.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            TrackerArchiveWriter._atomic_torch_save(
                {
                    "schema_version": SCHEMA_VERSION,
                    "interval_id": interval_id,
                    "available_at_frame_uid": self.current_uid,
                    "available_at_sensor_timestamp": self.current_sensor_timestamp,
                    "left_keyframe_uid": left_uid,
                    "right_keyframe_uid": right_uid,
                    "candidate_uids": torch.as_tensor(candidate_uids, dtype=torch.long),
                    "interpolated_poses_w2c": pose_matrices,
                    "pose_source": "causal_se3_endpoint_interpolation",
                },
                destination,
            )
            self.dense_intervals.append(
                {
                    "interval_id": interval_id,
                    "available_at_frame_uid": self.current_uid,
                    "available_at_sensor_timestamp": self.current_sensor_timestamp,
                    "left_keyframe_uid": left_uid,
                    "right_keyframe_uid": right_uid,
                    "candidate_count": len(candidate_uids),
                    "payload": relative,
                    "payload_sha256": sha256_file(destination),
                }
            )


class MetricRescaleCaptureProxy:
    """DepthVideo's only mapper-side tracker callback besides call_gs."""

    def __init__(self, capture: FrozenTrackerCapture) -> None:
        self.capture = capture

    def rescale(self, scale: float) -> None:
        self.capture.metric_rescale(scale)

    def remove_all_gaussians(self) -> None:
        self.capture.mapper_reset()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--imagedir", required=True)
    parser.add_argument("--imufile", required=True)
    parser.add_argument("--calib", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--weights", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--heldout-manifest", required=True)
    parser.add_argument("--dataset", required=True, choices=("rpng", "utmm"))
    parser.add_argument("--sequence", required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--length", type=int, default=100000)
    parser.add_argument("--buffer", type=int, default=700)
    parser.add_argument("--IMU_poseinit_after", type=int, default=20)
    parser.add_argument("--cropborder", type=int, default=0)
    parser.add_argument("--undistort", action="store_true")
    parser.add_argument("--gtdepthdir", default=None)
    parser.add_argument("--droidvis", action="store_false", default=False)
    parser.add_argument("--rerunvis", action="store_false", default=False)
    parser.add_argument("--rerun_record", action="store_false", default=False)
    parser.add_argument("--gsvis", action="store_false", default=False)
    parser.add_argument("--gsmapping", action="store_true", default=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = Path(args.output).resolve()
    if (output / "archive_manifest.json").exists():
        raise FileExistsError(f"completed archive already exists: {output}")
    output.mkdir(parents=True, exist_ok=True)
    image_names = ordered_image_names(
        args.imagedir, args.start, args.length, args.stride
    )
    eval_indices, heldout_manifest = load_eval_indices(
        Path(args.heldout_manifest), image_names
    )
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    torch.cuda.reset_peak_memory_stats()

    with open(args.config, encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    rgb_ns = bool(config.get("IMU", {}).get("rgb_file_in_nanoseconds", True))
    try:
        args.imus = np.loadtxt(args.imufile, delimiter=",")
    except ValueError:
        args.imus = np.loadtxt(args.imufile, delimiter=" ")

    resource.setrlimit(
        resource.RLIMIT_NOFILE,
        (100000, resource.getrlimit(resource.RLIMIT_NOFILE)[1]),
    )
    torch.multiprocessing.set_start_method("spawn")
    frame_queue: Queue = Queue(maxsize=8)
    consumer_finished = Event()
    reader = Process(
        target=mono_stream,
        args=(
            frame_queue,
            consumer_finished,
            args.imagedir,
            args.calib,
            args.undistort,
            args.cropborder,
            args.start,
            args.length,
            args.stride,
            rgb_ns,
        ),
    )
    reader.start()

    writer = TrackerArchiveWriter(output)
    capture = FrozenTrackerCapture(writer, eval_indices, image_names)
    arrivals: list[dict[str, Any]] = []
    vigs_instance: VIGS | None = None
    tracker_start: float | None = None
    first_imu_initialized_uid: int | None = None
    try:
        with tqdm(total=len(image_names), desc="Frozen VIGS tracker") as progress:
            while True:
                uid, timestamp, source_name, image, intrinsics, is_last = (
                    frame_queue.get()
                )
                arrivals.append(
                    {
                        "frame_uid": int(uid),
                        "sensor_timestamp": float(timestamp),
                        "source_name": source_name,
                        "held_out": int(uid) in eval_indices,
                    }
                )
                if vigs_instance is None:
                    args.image_size = [image.shape[2], image.shape[3]]
                    vigs_instance = VIGS(args)
                    vigs_instance.call_gs = types.MethodType(
                        lambda self, *call_args, **call_kwargs: capture.call_gs(
                            self, *call_args, **call_kwargs
                        ),
                        vigs_instance,
                    )
                    # IMU initialization invokes video.gs.rescale() directly,
                    # outside VIGS.call_gs().  Preserve that causal control
                    # event without running a Gaussian mapper during capture.
                    vigs_instance.video.gs = MetricRescaleCaptureProxy(capture)
                    tracker_start = time.monotonic()
                capture.set_arrival(uid, timestamp)
                vigs_instance.track(
                    uid,
                    timestamp,
                    image,
                    intrinsics=intrinsics,
                    is_last=is_last,
                )
                capture.capture_new_dense_intervals(vigs_instance)
                if (
                    first_imu_initialized_uid is None
                    and bool(vigs_instance.video.IMU_initialized)
                ):
                    first_imu_initialized_uid = int(uid)
                progress.update(1)
                progress.set_postfix(
                    keyframes=vigs_instance.video.counter.value,
                    events=capture.event_count,
                )
                if is_last:
                    break
    finally:
        consumer_finished.set()
        reader.join(timeout=5.0)
        if reader.is_alive():
            reader.terminate()
            reader.join()

    assert vigs_instance is not None and tracker_start is not None
    torch.cuda.synchronize()
    causal_tracker_seconds = time.monotonic() - tracker_start
    if hasattr(vigs_instance, "mp_backend"):
        vigs_instance.video.pgobuf.stop()
        vigs_instance.mp_backend.join(timeout=1.0)
    writer.close()
    writer.events.sort(key=lambda record: int(record["event_id"]))

    keyframe_count = int(vigs_instance.video.counter.value)
    keyframe_uids = (
        vigs_instance.video.tstamp[:keyframe_count].detach().cpu().long()
    )
    keyframe_poses_w2c = (
        vigs_instance.video.poses[:keyframe_count].detach().cpu().clone()
    )
    keyframe_sensor_timestamps = torch.as_tensor(
        [arrivals[int(uid)]["sensor_timestamp"] for uid in keyframe_uids.tolist()],
        dtype=torch.float64,
    )
    final_state_path = output / "final_tracker_state.pt"
    TrackerArchiveWriter._atomic_torch_save(
        {
            "schema_version": SCHEMA_VERSION,
            "keyframe_uids": keyframe_uids,
            "keyframe_poses_w2c": keyframe_poses_w2c,
            "keyframe_intrinsics_full_resolution": (
                vigs_instance.video.intrinsics[:keyframe_count]
                .detach()
                .cpu()
                .clone()
                * 8
            ),
            "keyframe_sensor_timestamps": keyframe_sensor_timestamps,
        },
        final_state_path,
    )

    # Evaluation-only pose filling happens after EOS and is never exposed to
    # either mapper.  Keeping it in a separate file makes accidental use easy
    # to audit.
    eval_pose_start = time.monotonic()
    trajectory_full = vigs_instance.traj_filler(vigs_instance.images)
    torch.cuda.synchronize()
    evaluation_pose_seconds = time.monotonic() - eval_pose_start
    eval_state_path = output / "evaluation_only_post_eos_trajectory.pt"
    TrackerArchiveWriter._atomic_torch_save(
        {
            "schema_version": SCHEMA_VERSION,
            "mapping_supervision_allowed": False,
            "post_eos": True,
            "poses_w2c_matrix": trajectory_full.matrix().data.detach().cpu(),
            "poses_c2w_vector": trajectory_full.inv().data.detach().cpu(),
        },
        eval_state_path,
    )

    arrivals_path = output / "arrivals.jsonl"
    arrivals_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in arrivals)
    )
    event_uids = {
        uid for event in writer.events for uid in event["frame_uids"]
    }
    heldout_packet_overlap = sorted(event_uids.intersection(eval_indices))
    dense_candidate_count = sum(
        int(record["candidate_count"]) for record in capture.dense_intervals
    )
    runtime = {
        "schema_version": SCHEMA_VERSION,
        "dataset": args.dataset,
        "sequence": args.sequence,
        "seed": args.seed,
        "frames": len(arrivals),
        "keyframes": keyframe_count,
        "events": len(writer.events),
        "keyframe_update_events": sum(
            event["kind"] == "keyframe_update" for event in writer.events
        ),
        "pose_scale_correction_events": sum(
            event["kind"] == "pose_scale_correction" for event in writer.events
        ),
        "metric_rescale_events": sum(
            event["kind"] == "metric_rescale" for event in writer.events
        ),
        "mapper_reset_events": sum(
            event["kind"] == "mapper_reset" for event in writer.events
        ),
        "dense_intervals": len(capture.dense_intervals),
        "dense_candidates_mapping_disjoint": dense_candidate_count,
        "first_imu_initialized_frame_uid": first_imu_initialized_uid,
        "causal_tracker_capture_seconds": causal_tracker_seconds,
        "evaluation_only_post_eos_pose_fill_seconds": evaluation_pose_seconds,
        "peak_cuda_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_cuda_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        "gaussian_optimizer_updates": 0,
        "post_eos_gaussian_optimizer_updates": 0,
        "heldout_uids_present_in_raw_tracker_packets": len(heldout_packet_overlap),
        "heldout_packet_overlap_is_expected_and_filtered_at_replay": True,
    }
    write_json(output / "capture_runtime.json", runtime)
    archive_manifest = {
        "schema_version": SCHEMA_VERSION,
        "dataset": args.dataset,
        "sequence": args.sequence,
        "seed": args.seed,
        "official_source_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996",
        "input_image_directory": str(Path(args.imagedir).resolve()),
        "input_imu": str(Path(args.imufile).resolve()),
        "input_calibration": str(Path(args.calib).resolve()),
        "input_config": str(Path(args.config).resolve()),
        "preprocessing": {
            "implementation": "official_demo_equivalent",
            "target_pixels": 341 * 640,
            "resize_multiple": 8,
            "opencv_resize_interpolation": "INTER_LINEAR(default)",
            "undistort": bool(args.undistort),
            "cropborder": int(args.cropborder),
            "start": int(args.start),
            "length": int(args.length),
            "stride": int(args.stride),
            "rgb_file_in_nanoseconds": rgb_ns,
            "output_image_size_hw": list(args.image_size),
        },
        "heldout_manifest": str(Path(args.heldout_manifest).resolve()),
        "heldout_manifest_sha256": sha256_file(Path(args.heldout_manifest)),
        "heldout_eval_indices_sha256": sha256_json(sorted(eval_indices)),
        "heldout_count": len(eval_indices),
        "mapping_filter_contract": (
            "remove held-out UIDs from every keyframe/correction packet before "
            "mapper dispatch; never register held-out dense RGB"
        ),
        "arrivals": "arrivals.jsonl",
        "arrivals_sha256": sha256_file(arrivals_path),
        "events": writer.events,
        "dense_intervals": capture.dense_intervals,
        "final_tracker_state": final_state_path.name,
        "final_tracker_state_sha256": sha256_file(final_state_path),
        "evaluation_only_post_eos_trajectory": eval_state_path.name,
        "evaluation_only_post_eos_trajectory_sha256": sha256_file(
            eval_state_path
        ),
        "evaluation_only_trajectory_mapping_supervision_allowed": False,
        "runtime": runtime,
    }
    write_json(output / "archive_manifest.json", archive_manifest)
    print("EXP78B_FROZEN_TRACKER " + json.dumps(runtime, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
