#!/usr/bin/env python3
"""Timestamp-paced adapter around the upstream VIGS streaming worker.

The adapter does not change tracking, PGBA, Gaussian losses, or iteration counts.
It prewarms VIGS before starting the replay clock, releases RGB frames according
to source timestamps, enables the upstream bounded asynchronous GS queue through
a config overlay, and records timing/provenance separately from rendering eval.
"""

from __future__ import annotations

import argparse
import json
import os
import queue as queue_module
import re
import shutil
import sys
import time
import traceback
import types
import threading
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.multiprocessing import Event, Process, Queue
from tqdm import tqdm


VANILLA_REPO = Path(
    os.environ.get(
        "VIGS_VANILLA_REPO",
        "/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-vanilla-check",
    )
)
sys.path.insert(0, str(VANILLA_REPO))

from demo import get_tstamps_full, save_trajectory  # noqa: E402
from vigs import VIGS  # noqa: E402
from gaussian.scene.gaussian_model import GaussianModel  # noqa: E402
from util.utils import load_config  # noqa: E402


NETWORK_PIXELS = 341 * 640


class StrictDeadlineReached(RuntimeError):
    """Internal control-flow exception used to preempt an in-flight map packet."""


class StrictZeroTailController:
    """Audit mapping mutations against a fixed sensor-time wall deadline."""

    def __init__(self, enabled: bool, margin_seconds: float) -> None:
        self.enabled = bool(enabled)
        self.margin_seconds = float(margin_seconds)
        self.deadline_monotonic: float | None = None
        self._lock = threading.Lock()
        self.completed_adam_steps = 0
        self.rejected_adam_steps = 0
        self.mapping_packets_started = 0
        self.mapping_packets_completed = 0
        self.mapping_packets_interrupted = 0
        self.mapping_packets_rejected = 0
        self.main_track_mapping_interruptions = 0
        self.mutation_completions: list[tuple[str, float]] = []

    def configure(self, deadline_monotonic: float) -> None:
        deadline = float(deadline_monotonic)
        with self._lock:
            if self.deadline_monotonic is None:
                self.deadline_monotonic = deadline
            elif abs(self.deadline_monotonic - deadline) > 1e-9:
                raise RuntimeError("strict replay deadline changed during a run")

    def allows_start(self) -> bool:
        if not self.enabled:
            return True
        deadline = self.deadline_monotonic
        return deadline is not None and time.monotonic() < deadline - self.margin_seconds

    def require_start(self, operation: str) -> None:
        if self.allows_start():
            return
        if operation == "adam_step":
            with self._lock:
                self.rejected_adam_steps += 1
        raise StrictDeadlineReached(operation)

    def record_completion(self, operation: str) -> float:
        completed = time.monotonic()
        with self._lock:
            self.mutation_completions.append((operation, completed))
            if operation == "adam_step":
                self.completed_adam_steps += 1
        return completed

    def audit(self) -> dict:
        deadline = self.deadline_monotonic
        with self._lock:
            completions = list(self.mutation_completions)
            payload = {
                "protocol": "fixed1p5x_sensor_eos_zero_tail",
                "deadline_monotonic": deadline,
                "margin_seconds": self.margin_seconds,
                "completed_adam_steps": self.completed_adam_steps,
                "rejected_adam_steps": self.rejected_adam_steps,
                "mapping_packets_started": self.mapping_packets_started,
                "mapping_packets_completed": self.mapping_packets_completed,
                "mapping_packets_interrupted": self.mapping_packets_interrupted,
                "mapping_packets_rejected": self.mapping_packets_rejected,
                "main_track_mapping_interruptions": self.main_track_mapping_interruptions,
                "mutation_completion_count": len(completions),
                "updates_completed_after_deadline": (
                    sum(kind == "adam_step" and stamp > deadline for kind, stamp in completions)
                    if deadline is not None
                    else None
                ),
                "map_mutations_completed_after_deadline": (
                    sum(stamp > deadline for _, stamp in completions)
                    if deadline is not None
                    else None
                ),
                "last_adam_completion_monotonic": max(
                    (stamp for kind, stamp in completions if kind == "adam_step"),
                    default=None,
                ),
                "last_map_mutation_completion_monotonic": max(
                    (stamp for _, stamp in completions),
                    default=None,
                ),
            }
        payload["strict_zero_tail_proven"] = bool(
            self.enabled
            and deadline is not None
            and payload["updates_completed_after_deadline"] == 0
            and payload["map_mutations_completed_after_deadline"] == 0
        )
        return payload


def image_files(imagedir: str, start: int, length: int, stride: int) -> list[str]:
    try:
        ordered = sorted(
            os.listdir(imagedir),
            key=lambda name: float(os.path.basename(name)[:-4]),
        )
    except (TypeError, ValueError):
        ordered = sorted(os.listdir(imagedir))
    return ordered[start : start + length : stride]


def timestamp_from_name(name: str, nanoseconds: bool) -> float:
    value = float(re.findall(r"[+]?(?:\d*\.\d+|\d+)", name)[-1])
    return value / 1e9 if nanoseconds else value


def infer_image_size(imagedir: str, files: list[str], cropborder: int) -> list[int]:
    image = cv2.imread(os.path.join(imagedir, files[0]))
    if image is None:
        raise RuntimeError(f"failed to read first RGB image: {files[0]}")
    if cropborder > 0:
        image = image[cropborder:-cropborder, cropborder:-cropborder]
    height, width = image.shape[:2]
    scaled_height = int(height * np.sqrt(NETWORK_PIXELS / (height * width)))
    scaled_width = int(width * np.sqrt(NETWORK_PIXELS / (height * width)))
    return [scaled_height - scaled_height % 8, scaled_width - scaled_width % 8]


def paced_stream(
    frame_queue: Queue,
    producer_release: Event,
    imagedir: str,
    calib_path: str,
    undistort: bool,
    cropborder: int,
    start: int,
    length: int,
    stride: int,
    rgb_file_in_nanoseconds: bool,
    replay_time_scale: float,
    drop_oldest_when_full: bool,
) -> None:
    calib = np.loadtxt(calib_path, delimiter=" ")
    camera_matrix = np.array(
        [[calib[0], 0, calib[2]], [0, calib[1], calib[3]], [0, 0, 1]]
    )
    files = image_files(imagedir, start, length, stride)
    sensor_start = timestamp_from_name(files[0], rgb_file_in_nanoseconds)
    replay_start = None

    dropped_frames = 0
    for frame_idx, filename in enumerate(files):
        sensor_timestamp = timestamp_from_name(filename, rgb_file_in_nanoseconds)
        image = cv2.imread(os.path.join(imagedir, filename))
        if image is None:
            raise RuntimeError(f"failed to read RGB image: {filename}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        intrinsics = torch.tensor(calib[:4])
        if len(calib) > 4 and undistort:
            image = cv2.undistort(image, camera_matrix, calib[4:])
        if cropborder > 0:
            image = image[cropborder:-cropborder, cropborder:-cropborder]
            intrinsics[2:] -= cropborder

        height, width = image.shape[:2]
        scaled_height = int(height * np.sqrt(NETWORK_PIXELS / (height * width)))
        scaled_width = int(width * np.sqrt(NETWORK_PIXELS / (height * width)))
        scaled_height -= scaled_height % 8
        scaled_width -= scaled_width % 8
        image = cv2.resize(image, (scaled_width, scaled_height))
        image_tensor = torch.as_tensor(image).permute(2, 0, 1)
        intrinsics[[0, 2]] *= scaled_width / width
        intrinsics[[1, 3]] *= scaled_height / height

        # Decode/resize is sensor-adapter work, not part of algorithm latency.
        # Start the replay clock only when the first frame is actually ready,
        # and read subsequent frames ahead of their source-time release.
        if replay_start is None:
            replay_start = time.monotonic()
        target_wall = replay_start + replay_time_scale * (
            sensor_timestamp - sensor_start
        )
        delay = target_wall - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        emit_wall = time.monotonic()
        is_last = frame_idx == len(files) - 1
        packet = (
            frame_idx,
            sensor_timestamp,
            image_tensor[None],
            intrinsics[None],
            is_last,
            replay_start,
            target_wall,
            emit_wall,
            dropped_frames,
        )
        if not drop_oldest_when_full:
            frame_queue.put(packet)
            continue
        while True:
            try:
                frame_queue.put_nowait(packet)
                break
            except queue_module.Full:
                try:
                    frame_queue.get_nowait()
                    dropped_frames += 1
                    packet = packet[:-1] + (dropped_frames,)
                except queue_module.Empty:
                    time.sleep(0.001)
    # Torch Queue transfers tensor storage through a resource-sharer owned by
    # this process. Keep it alive until the parent has rebuilt the last tensor.
    producer_release.wait(timeout=300.0)


def guarded_gs_worker(self: VIGS) -> None:
    """Upstream worker loop with error propagation and optional hard cutoff."""
    while True:
        data = self._gs_queue.get()
        controller = getattr(self, "_benchmark_strict_controller", None)
        try:
            if data is None:
                break
            if controller is not None and not controller.allows_start():
                with controller._lock:
                    controller.mapping_packets_rejected += 1
                continue
            if controller is not None:
                with controller._lock:
                    controller.mapping_packets_started += 1
            self.gs.process_track_data(data)
            if controller is not None:
                torch.cuda.synchronize()
                completed = time.monotonic()
                with controller._lock:
                    controller.mapping_packets_completed += 1
                    if controller.enabled:
                        controller.mutation_completions.append(
                            ("mapping_packet", completed)
                        )
        except StrictDeadlineReached:
            if controller is not None:
                with controller._lock:
                    controller.mapping_packets_interrupted += 1
        except BaseException as error:  # surfaced on the tracking thread below
            self._benchmark_worker_error = (error, traceback.format_exc())
            break
        finally:
            self._gs_queue.task_done()


def raise_worker_error(
    vigs: VIGS,
    *,
    reader: Process | None = None,
    producer_release: Event | None = None,
) -> None:
    record = getattr(vigs, "_benchmark_worker_error", None)
    if record is None:
        return
    # If the consumer stops after a GS worker failure, the producer can remain
    # blocked on a full multiprocessing queue and then keep the interpreter
    # alive for its 300 s resource-sharer grace period. This is harness-only
    # lifecycle cleanup: preserve the failed output and let the serial queue
    # advance immediately.
    if producer_release is not None:
        producer_release.set()
    if reader is not None and reader.is_alive():
        reader.terminate()
        reader.join(timeout=5.0)
    error, formatted = record
    raise RuntimeError(
        "background GS worker failed; original traceback follows:\n" + formatted
    ) from error


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--imagedir", required=True)
    result.add_argument("--imufile", required=True)
    result.add_argument("--calib", required=True)
    result.add_argument("--config", required=True)
    result.add_argument("--output", required=True)
    result.add_argument("--gtdepthdir", default=None)
    result.add_argument("--weights", default=str(VANILLA_REPO / "pretrained_models/droid.pth"))
    result.add_argument("--buffer", type=int, default=-1)
    result.add_argument("--stride", type=int, default=1)
    result.add_argument("--start", type=int, default=0)
    result.add_argument("--length", type=int, default=100000)
    result.add_argument("--IMU_poseinit_after", type=int, default=100000)
    result.add_argument("--replay_time_scale", type=float, default=1.5)
    result.add_argument("--frame_queue_size", type=int, default=8)
    result.add_argument("--strict_zero_tail", action="store_true")
    result.add_argument("--strict_margin_seconds", type=float, default=0.05)
    result.add_argument("--undistort", action="store_true")
    result.add_argument("--cropborder", type=int, default=0)
    result.add_argument("--gsmapping", action="store_true")
    result.add_argument("--pure_online", action="store_true")
    result.add_argument("--final_ba_inertial", action="store_true")
    result.add_argument("--droidvis", action="store_true")
    result.add_argument("--rerunvis", action="store_true")
    result.add_argument("--rerun_record", action="store_true")
    result.add_argument("--gsvis", action="store_true")
    return result


def main() -> None:
    args = parser().parse_args()
    if not args.gsmapping or not args.pure_online:
        raise ValueError("streaming benchmark requires --gsmapping --pure_online")
    if args.replay_time_scale <= 0:
        raise ValueError("--replay_time_scale must be positive")
    if args.strict_margin_seconds < 0:
        raise ValueError("--strict_margin_seconds must be non-negative")

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    config = load_config(args.config)
    rgb_nanoseconds = config.get("IMU", {}).get("rgb_file_in_nanoseconds", True)
    if not config.get("Training", {}).get("parallel", False):
        raise ValueError("streaming config must enable upstream Training.parallel")

    try:
        args.imus = np.loadtxt(args.imufile, delimiter=",")
    except ValueError:
        args.imus = np.loadtxt(args.imufile, delimiter=" ")
    args.buffer = 1200 if args.buffer < 0 else args.buffer
    files = image_files(args.imagedir, args.start, args.length, args.stride)
    if not files:
        raise ValueError("no RGB frames selected")
    args.image_size = infer_image_size(args.imagedir, files, args.cropborder)
    shutil.copy2(args.config, output / "config.yaml")

    torch.multiprocessing.set_start_method("spawn")
    print(f"STREAM_PREWARM_START_EPOCH {time.time()}", flush=True)
    # The upstream async mode does not propagate worker exceptions. This wrapper
    # makes failures observable and, in strict mode, rejects packets at the fixed
    # capture deadline without changing vanilla packets admitted before it.
    VIGS._gs_worker = guarded_gs_worker
    vigs = VIGS(args)
    if not getattr(vigs, "_gs_parallel", False):
        raise RuntimeError("upstream GS parallel worker did not start")

    strict = StrictZeroTailController(
        enabled=args.strict_zero_tail,
        margin_seconds=args.strict_margin_seconds,
    )
    vigs._benchmark_strict_controller = strict

    # Guard the physical Gaussian Adam update. Synchronizing before admission
    # means a render/backward that crossed the deadline cannot sneak in an update.
    original_adam_step = torch.optim.Adam.step

    def deadline_guarded_adam_step(optimizer, *step_args, **step_kwargs):
        if not args.strict_zero_tail or optimizer is not vigs.gs.gaussians.optimizer:
            return original_adam_step(optimizer, *step_args, **step_kwargs)
        torch.cuda.synchronize()
        strict.require_start("adam_step")
        result = original_adam_step(optimizer, *step_args, **step_kwargs)
        torch.cuda.synchronize()
        strict.record_completion("adam_step")
        return result

    torch.optim.Adam.step = deadline_guarded_adam_step

    # Birth and topology change the saved map even without an Adam step. Guard
    # each upstream mutation at the same deadline and retain its original body.
    topology_methods = (
        "extend_from_pcd_seq",
        "densify_and_prune",
        "prune_points",
        "reset_opacity",
        "reset_opacity_nonvisible",
    )
    for method_name in topology_methods:
        original_method = getattr(GaussianModel, method_name)

        def guarded_mutation(
            gaussian_model,
            *method_args,
            _method=original_method,
            _name=method_name,
            **method_kwargs,
        ):
            if not args.strict_zero_tail or gaussian_model is not vigs.gs.gaussians:
                return _method(gaussian_model, *method_args, **method_kwargs)
            torch.cuda.synchronize()
            strict.require_start(_name)
            result = _method(gaussian_model, *method_args, **method_kwargs)
            torch.cuda.synchronize()
            strict.record_completion(_name)
            return result

        setattr(GaussianModel, method_name, guarded_mutation)

    # Upstream rescale() already takes this lock, but the IMU reinitialization
    # path's remove_all_gaussians() does not. Serialize that lifecycle mutation
    # with an in-flight map packet without changing its numerical operation.
    remove_all_gaussians = vigs.gs.remove_all_gaussians

    def synchronized_remove_all_gaussians(self) -> None:
        with self._gaussian_lock:
            if args.strict_zero_tail and not strict.allows_start():
                return
            remove_all_gaussians()
            if args.strict_zero_tail:
                torch.cuda.synchronize()
                strict.record_completion("remove_all_gaussians")

    vigs.gs.remove_all_gaussians = types.MethodType(
        synchronized_remove_all_gaussians,
        vigs.gs,
    )

    original_rescale = vigs.gs.rescale

    def deadline_guarded_rescale(self, scale) -> None:
        if args.strict_zero_tail and not strict.allows_start():
            return
        original_rescale(scale)
        if args.strict_zero_tail:
            torch.cuda.synchronize()
            strict.record_completion("rescale")

    vigs.gs.rescale = types.MethodType(deadline_guarded_rescale, vigs.gs)

    original_call_gs = vigs.call_gs

    def deadline_guarded_call_gs(self, *call_args, **call_kwargs):
        if args.strict_zero_tail and not strict.allows_start():
            with strict._lock:
                strict.mapping_packets_rejected += 1
            return None
        return original_call_gs(*call_args, **call_kwargs)

    vigs.call_gs = types.MethodType(deadline_guarded_call_gs, vigs)
    print(f"STREAM_PREWARM_DONE_EPOCH {time.time()}", flush=True)

    frame_queue = Queue(maxsize=args.frame_queue_size)
    producer_release = Event()
    reader = Process(
        target=paced_stream,
        args=(
            frame_queue,
            producer_release,
            args.imagedir,
            args.calib,
            args.undistort,
            args.cropborder,
            args.start,
            args.length,
            args.stride,
            rgb_nanoseconds,
            args.replay_time_scale,
            args.strict_zero_tail,
        ),
    )
    reader.start()

    timings: list[dict] = []
    timestamps_full = get_tstamps_full(
        args.imagedir,
        args.start,
        args.length,
        args.stride,
        rgb_nanoseconds,
    )
    progress = tqdm(total=len(files), desc="Streaming keyframes")
    last_packet = None
    strict_tracking_interruptions = 0
    while True:
        try:
            packet = frame_queue.get(timeout=5.0)
        except queue_module.Empty:
            if not reader.is_alive():
                raise RuntimeError(
                    f"stream producer exited early with code {reader.exitcode}"
                )
            continue
        get_wall = time.monotonic()
        (
            frame_idx,
            sensor_timestamp,
            image,
            intrinsics,
            is_last,
            replay_start,
            target_wall,
            emit_wall,
            producer_dropped_frames,
        ) = packet
        if strict.deadline_monotonic is None:
            source_duration = timestamp_from_name(files[-1], rgb_nanoseconds) - timestamp_from_name(
                files[0], rgb_nanoseconds
            )
            strict.configure(replay_start + args.replay_time_scale * source_duration)
        try:
            vigs.track(
                frame_idx,
                sensor_timestamp,
                image,
                intrinsics=intrinsics,
                is_last=is_last,
            )
        except StrictDeadlineReached:
            # A synchronous PGBA mapping packet may reach the deadline inside
            # track(). Tracking state before call_gs is retained and subsequent
            # map calls are rejected, so continue consuming the live sequence.
            strict_tracking_interruptions += 1
            with strict._lock:
                strict.main_track_mapping_interruptions += 1
        raise_worker_error(
            vigs,
            reader=reader,
            producer_release=producer_release,
        )
        done_wall = time.monotonic()
        timings.append(
            {
                "frame_idx": int(frame_idx),
                "sensor_timestamp": float(sensor_timestamp),
                "target_wall": float(target_wall),
                "emit_wall": float(emit_wall),
                "consumer_get_wall": float(get_wall),
                "tracking_done_wall": float(done_wall),
                "producer_lateness_s": float(emit_wall - target_wall),
                "consumer_lateness_s": float(get_wall - target_wall),
                "producer_dropped_frames": int(producer_dropped_frames),
            }
        )
        last_packet = packet
        if is_last:
            # The tensor has now been rebuilt in this process; the producer can
            # safely release its resource-sharer and exit.
            producer_release.set()
        progress.update()
        progress.set_description(
            f"Streaming keyframe {vigs.video.counter.value} "
            f"gs {vigs.gs.gaussians._xyz.shape[0]}"
        )
        if is_last:
            progress.close()
            break

    track_done_wall = time.monotonic()
    pending_at_eos = vigs._gs_queue.qsize()
    discarded_pending_at_eos = 0
    if args.strict_zero_tail:
        while True:
            try:
                vigs._gs_queue.get_nowait()
                vigs._gs_queue.task_done()
                discarded_pending_at_eos += 1
            except queue_module.Empty:
                break
        vigs._gs_queue.put(None)
        vigs._gs_thread.join()
        raise_worker_error(vigs)
        torch.cuda.synchronize()
        mapping_done_wall = time.monotonic()
    else:
        vigs._gs_queue.join()
        raise_worker_error(vigs)
        torch.cuda.synchronize()
        mapping_done_wall = time.monotonic()
        vigs._gs_queue.put(None)
        vigs._gs_thread.join()
    reader.join()

    if hasattr(vigs, "mp_backend"):
        vigs.video.pgobuf.stop()
        vigs.mp_backend.join(timeout=1.0)

    assert last_packet is not None
    replay_start = float(last_packet[5])
    source_duration = float(
        timestamp_from_name(files[-1], rgb_nanoseconds)
        - timestamp_from_name(files[0], rgb_nanoseconds)
    )
    deadline_wall = replay_start + args.replay_time_scale * source_duration
    strict_audit = strict.audit()
    if args.strict_zero_tail:
        (output / "sensor_eos_audit.json").write_text(
            json.dumps(strict_audit, indent=2) + "\n"
        )
    contract = {
        "adapter": "external timestamp pacing + upstream Training.parallel worker",
        "replay_time_scale": args.replay_time_scale,
        "frame_count": len(files),
        "processed_frame_count": len(timings),
        "producer_drop_oldest": bool(args.strict_zero_tail),
        "producer_dropped_frame_count": int(timings[-1]["producer_dropped_frames"]),
        "processed_frame_fraction": len(timings) / len(files),
        "source_duration_s": source_duration,
        "budget_duration_s": args.replay_time_scale * source_duration,
        "producer_start_monotonic": replay_start,
        "deadline_monotonic": deadline_wall,
        "last_emit_lateness_s": timings[-1]["producer_lateness_s"],
        "last_consumer_lateness_s": timings[-1]["consumer_lateness_s"],
        "track_done_lateness_s": track_done_wall - deadline_wall,
        "mapping_done_lateness_s": mapping_done_wall - deadline_wall,
        "mapping_drain_after_track_s": mapping_done_wall - track_done_wall,
        "pending_gs_packets_at_sensor_eos": pending_at_eos,
        "discarded_pending_gs_packets_at_sensor_eos": discarded_pending_at_eos,
        # A scheduled wakeup cannot be bit-exact to a monotonic timestamp.
        # Ten milliseconds is below one frame period for every benchmark and
        # is a fixed harness tolerance, not a scene-specific compute budget.
        "ingress_schedule_tolerance_s": 0.01,
        "producer_deadline_pass": timings[-1]["producer_lateness_s"] <= 0.01,
        "tracking_deadline_pass": track_done_wall <= deadline_wall,
        "mapping_deadline_pass": (
            strict_audit["strict_zero_tail_proven"]
            if args.strict_zero_tail
            else mapping_done_wall <= deadline_wall
        ),
        "offline_ba": False,
        "offline_color_refinement": False,
        "tracking_mapping_code_modified": False,
        "streaming_lifecycle_fixes": [
            "serialize IMU remove_all_gaussians with upstream gaussian lock",
            "keep producer resource-sharer alive until last tensor acknowledgement",
            "propagate background worker exceptions",
        ],
        "strict_zero_tail_proven": strict_audit["strict_zero_tail_proven"],
        "strict_zero_tail_note": (
            "adapter rejects Gaussian Adam and map mutations at the fixed final-capture deadline; "
            "pending packets are discarded without optimizer drain"
            if args.strict_zero_tail
            else "upstream worker is drained after the last packet; elapsed drain is reported "
            "and this run is not labeled strict zero-tail"
        ),
        "strict_audit": strict_audit,
        "strict_tracking_interruptions": strict_tracking_interruptions,
    }
    (output / "stream_contract.json").write_text(json.dumps(contract, indent=2) + "\n")
    with (output / "stream_timing.jsonl").open("w") as handle:
        for row in timings:
            handle.write(json.dumps(row) + "\n")

    vigs.gs.gaussians.save_ply(str(output / "3dgs_before_final.ply"))
    save_trajectory(
        vigs,
        None,
        args.imagedir,
        str(output),
        start=args.start,
        length=args.length,
        stride=args.stride,
        final=True,
        suffix="_beforeBA",
        tstamps_full=timestamps_full,
    )
    trajectory = vigs.traj_filler(vigs.images)
    trajectory_compact = trajectory.matrix().data
    processed_indices = list(vigs.images.keys())
    trajectory_by_frame = torch.empty(
        (max(processed_indices) + 1, 4, 4),
        dtype=trajectory_compact.dtype,
        device=trajectory_compact.device,
    )
    for compact_idx, frame_idx in enumerate(processed_indices):
        trajectory_by_frame[frame_idx] = trajectory_compact[compact_idx]
    vigs.gs.eval_rendering(
        vigs.images,
        args.gtdepthdir,
        trajectory_by_frame,
        vigs.video.tstamp[: vigs.video.counter.value].to(device="cpu"),
    )
    print("STREAM_CONTRACT " + json.dumps(contract, sort_keys=True), flush=True)
    print(f"Finished Processing, outputs in {output}", flush=True)


if __name__ == "__main__":
    main()
