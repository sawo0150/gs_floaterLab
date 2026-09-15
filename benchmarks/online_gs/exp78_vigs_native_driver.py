#!/usr/bin/env python3
"""Run unmodified VIGS modules and stop at the paper's pre-refinement state.

This driver intentionally mirrors the official ``demo.py`` data path.  The only
functional differences are deterministic seed initialization, explicit timing /
memory telemetry, and saving the full interpolated trajectory before invoking
``VIGS.terminate()`` (which would run final BA and color refinement).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random
import re
import resource
import time

import cv2
import lietorch
import numpy as np
import torch
import yaml
from torch.multiprocessing import Event, Process, Queue
from tqdm import tqdm

from vigs import VIGS
from gaussian.utils.eval_utils import eval_rendering, eval_rendering_kf


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def pose_consistency(
    vigs: VIGS, trajectory_world_to_camera: torch.Tensor
) -> dict[str, float | int | None]:
    """Compare tracker poses used for evaluation with cached mapping viewpoints."""
    translation_errors: list[float] = []
    rotation_errors: list[float] = []
    for raw_index, viewpoint in vigs.gs.viewpoints.items():
        index = int(raw_index)
        tracking_pose = trajectory_world_to_camera[index]
        mapping_pose = torch.eye(4, dtype=tracking_pose.dtype, device=tracking_pose.device)
        mapping_pose[:3, :3] = viewpoint.R
        mapping_pose[:3, 3] = viewpoint.T
        tracking_center = torch.linalg.inv(tracking_pose)[:3, 3]
        mapping_center = torch.linalg.inv(mapping_pose)[:3, 3]
        translation_errors.append(
            float(torch.linalg.norm(tracking_center - mapping_center).item())
        )
        relative_rotation = tracking_pose[:3, :3] @ mapping_pose[:3, :3].transpose(0, 1)
        cosine = torch.clamp((torch.trace(relative_rotation) - 1.0) / 2.0, -1.0, 1.0)
        rotation_errors.append(float(torch.rad2deg(torch.acos(cosine)).item()))
    if not translation_errors:
        return {
            "compared_mapping_views": 0,
            "camera_center_error_mean": None,
            "camera_center_error_max": None,
            "rotation_error_degrees_mean": None,
            "rotation_error_degrees_max": None,
        }
    return {
        "compared_mapping_views": len(translation_errors),
        "camera_center_error_mean": float(np.mean(translation_errors)),
        "camera_center_error_max": float(np.max(translation_errors)),
        "rotation_error_degrees_mean": float(np.mean(rotation_errors)),
        "rotation_error_degrees_max": float(np.max(rotation_errors)),
    }


def get_tstamps_full(
    imagedir: str,
    start: int,
    length: int,
    stride: int,
    rgb_file_in_nanoseconds: bool = True,
) -> np.ndarray:
    names = sorted(os.listdir(imagedir))
    values = [float(re.findall(r"[+]?(?:\d*\.\d+|\d+)", name)[-1]) for name in names]
    stamps = np.asarray(values, dtype=np.float64)[..., np.newaxis]
    if rgb_file_in_nanoseconds:
        stamps /= 1e9
    return stamps[start : start + length][::stride]


def mono_stream(
    queue: Queue,
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
    # Exact official demo.py preprocessing target.
    target_pixels = 341 * 640
    calibration = np.loadtxt(calib, delimiter=" ")
    camera_matrix = np.array(
        [
            [calibration[0], 0, calibration[2]],
            [0, calibration[1], calibration[3]],
            [0, 0, 1],
        ]
    )
    try:
        names = sorted(
            os.listdir(imagedir), key=lambda name: float(os.path.basename(name)[:-4])
        )[start : start + length][::stride]
    except ValueError:
        names = sorted(os.listdir(imagedir))[start : start + length][::stride]

    for index, name in enumerate(names):
        timestamp = float(re.findall(r"[+]?(?:\d*\.\d+|\d+)", name)[-1])
        if rgb_file_in_nanoseconds:
            timestamp /= 1e9
        image = cv2.imread(os.path.join(imagedir, name))
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
        queue.put(
            (
                index,
                timestamp,
                image_tensor[None],
                intrinsics[None],
                index == len(names) - 1,
            )
        )

    # Tensor objects are transferred through a resource-sharer owned by this
    # process.  Keep it alive until the consumer has deserialized the last
    # queued frame; otherwise the final queue.get() can race process teardown.
    consumer_finished.wait()


def save_trajectory(
    vigs: VIGS,
    trajectory_full: np.ndarray | None,
    imagedir: str,
    output: Path,
    start: int,
    length: int,
    stride: int,
    timestamps_full: np.ndarray,
    suffix: str,
) -> None:
    keyframe_count = vigs.video.counter.value
    frame_indices = vigs.video.tstamp[:keyframe_count]
    poses_wc = lietorch.SE3(vigs.video.poses[:keyframe_count]).inv().data
    timestamps_kf = timestamps_full[frame_indices.cpu().numpy().astype(int)]
    trajectory_kf = np.concatenate([timestamps_kf, poses_wc.cpu().numpy()], axis=1)
    np.savetxt(output / f"traj_kf{suffix}.txt", trajectory_kf)
    if trajectory_full is not None:
        rows = np.concatenate([timestamps_full[: len(trajectory_full)], trajectory_full], axis=1)
        np.savetxt(output / f"traj_full{suffix}.txt", rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--imagedir", required=True)
    parser.add_argument("--imufile", required=True)
    parser.add_argument("--calib", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--weights", required=True)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--length", type=int, default=100000)
    parser.add_argument("--buffer", type=int, default=700)
    parser.add_argument("--IMU_poseinit_after", type=int, default=20)
    parser.add_argument("--cropborder", type=int, default=0)
    parser.add_argument("--undistort", action="store_true")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--gtdepthdir", default=None)
    parser.add_argument("--droidvis", action="store_false", default=False)
    parser.add_argument("--rerunvis", action="store_false", default=False)
    parser.add_argument("--rerun_record", action="store_false", default=False)
    parser.add_argument("--gsvis", action="store_false", default=False)
    parser.add_argument("--gsmapping", action="store_true", default=True)
    parser.add_argument(
        "--official-prefinal-eval",
        action="store_true",
        help=(
            "diagnostic only: apply the official evaluator directly to the live "
            "pre-final map before serializing it"
        ),
    )
    parser.add_argument(
        "--diagnose-after-ba-before-color",
        action="store_true",
        help=(
            "diagnostic only: additionally reproduce the official source's state "
            "after visual global BA/map pose propagation but before color refinement"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    torch.cuda.reset_peak_memory_stats()

    with open(args.config, encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    rgb_ns = config.get("IMU", {}).get("rgb_file_in_nanoseconds", True)
    try:
        args.imus = np.loadtxt(args.imufile, delimiter=",")
    except ValueError:
        args.imus = np.loadtxt(args.imufile, delimiter=" ")

    resource.setrlimit(
        resource.RLIMIT_NOFILE,
        (100000, resource.getrlimit(resource.RLIMIT_NOFILE)[1]),
    )
    torch.multiprocessing.set_start_method("spawn")
    queue: Queue = Queue(maxsize=8)
    consumer_finished = Event()
    reader = Process(
        target=mono_stream,
        args=(
            queue,
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

    frame_count = min(args.length, len(os.listdir(args.imagedir)) - args.start)
    frame_count = (max(frame_count, 0) + args.stride - 1) // args.stride
    timestamps_full = get_tstamps_full(
        args.imagedir, args.start, args.length, args.stride, rgb_ns
    )
    vigs_instance: VIGS | None = None
    start_monotonic: float | None = None
    first_gaussian_frame: int | None = None
    first_imu_initialized_frame: int | None = None
    try:
        with tqdm(total=frame_count, desc="Paper-native VIGS") as progress:
            while True:
                index, timestamp, image, intrinsics, is_last = queue.get()
                if vigs_instance is None:
                    args.image_size = [image.shape[2], image.shape[3]]
                    vigs_instance = VIGS(args)
                    start_monotonic = time.monotonic()
                vigs_instance.track(
                    index, timestamp, image, intrinsics=intrinsics, is_last=is_last
                )
                if (
                    first_gaussian_frame is None
                    and vigs_instance.gs.gaussians._xyz.shape[0] > 0
                ):
                    first_gaussian_frame = index
                if (
                    first_imu_initialized_frame is None
                    and bool(vigs_instance.video.IMU_initialized)
                ):
                    first_imu_initialized_frame = index
                progress.update(1)
                progress.set_postfix(
                    keyframes=vigs_instance.video.counter.value,
                    gaussians=vigs_instance.gs.gaussians._xyz.shape[0],
                )
                if is_last:
                    break
    finally:
        consumer_finished.set()
        reader.join(timeout=5.0)
        if reader.is_alive():
            reader.terminate()
            reader.join()

    assert vigs_instance is not None and start_monotonic is not None
    track_map_elapsed = time.monotonic() - start_monotonic
    torch.cuda.synchronize()
    track_map_peak_allocated = int(torch.cuda.max_memory_allocated())
    track_map_peak_reserved = int(torch.cuda.max_memory_reserved())
    if hasattr(vigs_instance, "mp_backend"):
        vigs_instance.video.pgobuf.stop()
        vigs_instance.mp_backend.join(timeout=1.0)
    if getattr(vigs_instance, "_gs_parallel", False):
        vigs_instance._gs_queue.join()
        vigs_instance._gs_queue.put(None)
        vigs_instance._gs_thread.join()

    prefinal_gaussians = int(vigs_instance.gs.gaussians._xyz.shape[0])
    prefinal_mapping_iterations = int(vigs_instance.gs.iteration_count)
    prefinal_mapping_frame_indices = sorted(
        int(index) for index in vigs_instance.gs.viewpoints
    )
    vigs_instance.gs.gaussians.save_ply(output / "3dgs_before_final.ply")
    trajectory_full = vigs_instance.traj_filler(vigs_instance.images)
    trajectory_full_wc = trajectory_full.inv().data.cpu().numpy()
    save_trajectory(
        vigs_instance,
        trajectory_full_wc,
        args.imagedir,
        output,
        args.start,
        args.length,
        args.stride,
        timestamps_full,
        suffix="_beforeBA",
    )
    np.save(
        output / "intrinsics.npy",
        vigs_instance.video.intrinsics[0].cpu().numpy() * 8,
    )
    official_prefinal_result = None
    prefinal_pose_consistency = pose_consistency(
        vigs_instance, trajectory_full.matrix().data
    )
    if args.official_prefinal_eval:
        official_prefinal_result = eval_rendering(
            vigs_instance.images,
            args.gtdepthdir,
            trajectory_full.matrix().data,
            vigs_instance.gs.gaussians,
            str(output),
            vigs_instance.gs.background,
            vigs_instance.gs.projection_matrix,
            vigs_instance.gs.K,
            vigs_instance.video.tstamp[: vigs_instance.video.counter.value].to(
                device="cpu"
            ),
            iteration="inprocess_prefinal_official",
        )
        eval_rendering_kf(
            vigs_instance.gs.viewpoints,
            vigs_instance.gs.gaussians,
            str(output),
            vigs_instance.gs.background,
            iteration="inprocess_prefinal_official",
        )
    after_ba_before_color_result = None
    if args.diagnose_after_ba_before_color:
        diagnostic_start = time.monotonic()
        poses_before_ba = vigs_instance.video.poses[
            : vigs_instance.video.counter.value
        ].clone()
        vigs_instance.backend(7, inertial=False)
        vigs_instance.backend(12, inertial=False)
        poses_after_ba = vigs_instance.video.poses[
            : vigs_instance.video.counter.value
        ].clone()
        pose_updates = lietorch.SE3(poses_after_ba) * lietorch.SE3(poses_before_ba).inv()
        scale_updates = torch.ones(vigs_instance.video.counter.value, 1)
        vigs_instance.call_gs(
            torch.arange(0, vigs_instance.video.counter.value, device="cuda"),
            pose_updates,
            scale_updates,
            final=True,
            blocking=True,
        )
        trajectory_after_ba = vigs_instance.traj_filler(vigs_instance.images)
        vigs_instance.gs.gaussians.save_ply(output / "3dgs_afterBA_before_color.ply")
        save_trajectory(
            vigs_instance,
            trajectory_after_ba.inv().data.cpu().numpy(),
            args.imagedir,
            output,
            args.start,
            args.length,
            args.stride,
            timestamps_full,
            suffix="_afterBA_beforeColor",
        )
        rendering_after_ba = eval_rendering(
            vigs_instance.images,
            args.gtdepthdir,
            trajectory_after_ba.matrix().data,
            vigs_instance.gs.gaussians,
            str(output),
            vigs_instance.gs.background,
            vigs_instance.gs.projection_matrix,
            vigs_instance.gs.K,
            vigs_instance.video.tstamp[: vigs_instance.video.counter.value].to(
                device="cpu"
            ),
            iteration="after_ba_before_color_official",
        )
        eval_rendering_kf(
            vigs_instance.gs.viewpoints,
            vigs_instance.gs.gaussians,
            str(output),
            vigs_instance.gs.background,
            iteration="after_ba_before_color_official",
        )
        torch.cuda.synchronize()
        after_ba_before_color_result = {
            "protocol": "diagnostic_after_visual_ba_before_color_v1",
            "seconds_including_evaluation": time.monotonic() - diagnostic_start,
            "rendering": rendering_after_ba,
            "gaussians": int(vigs_instance.gs.gaussians._xyz.shape[0]),
            "mapping_iterations": int(vigs_instance.gs.iteration_count),
            "mapping_view_count": len(vigs_instance.gs.viewpoints),
            "pose_consistency": pose_consistency(
                vigs_instance, trajectory_after_ba.matrix().data
            ),
            "final_ba_performed": True,
            "final_color_refinement_performed": False,
        }
        write_json(
            output / "diagnostic_after_ba_before_color.json",
            after_ba_before_color_result,
        )
    torch.cuda.synchronize()
    result = {
        "protocol": "paper_native_prefinal_v1",
        "seed": args.seed,
        "frames": frame_count,
        "keyframes": int(vigs_instance.video.counter.value),
        "gaussians": prefinal_gaussians,
        "first_gaussian_frame": first_gaussian_frame,
        "first_imu_initialized_frame": first_imu_initialized_frame,
        "mapping_iterations": prefinal_mapping_iterations,
        "mapping_view_count": len(prefinal_mapping_frame_indices),
        "mapping_frame_indices": prefinal_mapping_frame_indices,
        "prefinal_tracking_vs_mapping_pose_consistency": prefinal_pose_consistency,
        "tracking_plus_mapping_seconds": track_map_elapsed,
        "tracking_plus_mapping_fps": frame_count / track_map_elapsed,
        "tracking_plus_mapping_peak_cuda_allocated_bytes": track_map_peak_allocated,
        "tracking_plus_mapping_peak_cuda_reserved_bytes": track_map_peak_reserved,
        "peak_cuda_allocated_bytes": track_map_peak_allocated,
        "peak_cuda_reserved_bytes": track_map_peak_reserved,
        "final_ba_performed": False,
        "final_color_refinement_performed": False,
        "full_trajectory_filling_performed_after_last_frame": True,
        "official_prefinal_inprocess_evaluation": official_prefinal_result,
        "after_ba_before_color_diagnostic": after_ba_before_color_result,
    }
    write_json(output / "native_runtime.json", result)
    print("EXP78_NATIVE_RESULT " + json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
