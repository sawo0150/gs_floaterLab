#!/usr/bin/env python3
"""Wrap the unmodified saved-PLY evaluator and capture its first render tensor.

The probe intentionally runs *inside* the evaluator process.  It records
camera/pose/background hashes and the first raw rendered tensor before the
normal evaluator computes PSNR for that image.  The saved map is read-only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import torch
import cv2

import exp78_evaluate_vigs_ply as evaluator


def digest(tensor: torch.Tensor) -> str:
    return hashlib.sha256(tensor.detach().contiguous().cpu().numpy().tobytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--probe-output", type=Path, required=True)
    args, evaluator_argv = parser.parse_known_args()
    if args.probe_output.exists():
        raise FileExistsError(args.probe_output)
    original_render = evaluator.render
    original_preprocess = evaluator.preprocess_image
    seen = False
    preprocess_state = {}

    def probed_preprocess(path, calibration, undistort):
        result = original_preprocess(path, calibration, undistort)
        if not preprocess_state:
            preprocess_state.update({
                "input_image": str(path),
                "input_image_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                "undistort_argument": bool(undistort),
                "calibration_length": int(len(calibration)),
                "calibration_values": calibration.tolist(),
                "preprocessed_uint8_sha256": digest(result[0]),
                "preprocessed_mean": float(result[0].float().mean().item()),
                "opencv_optimized": bool(cv2.useOptimized()),
                "opencv_opencl_enabled": bool(cv2.ocl.useOpenCL()),
            })
        return result

    def probed_render(viewpoint_camera, pc, bg_color, *positional, **kwargs):
        nonlocal seen
        result = original_render(viewpoint_camera, pc, bg_color, *positional, **kwargs)
        if not seen:
            seen = True
            prediction = torch.clamp(result["render"], 0, 1)
            ground_truth = viewpoint_camera.original_image.cuda()
            mask = ground_truth > 0
            torch.cuda.synchronize()
            probe = {
                "timestamp_unix": time.time(),
                "frame_uid": viewpoint_camera.uid,
                "current_cuda_stream": torch.cuda.current_stream().cuda_stream,
                "default_cuda_stream": torch.cuda.default_stream().cuda_stream,
                "gaussians": int(pc.get_xyz.shape[0]),
                "background_sha256": digest(bg_color),
                "background_values": bg_color.detach().cpu().tolist(),
                "camera_R_sha256": digest(viewpoint_camera.R),
                "camera_T_sha256": digest(viewpoint_camera.T),
                "world_view_sha256": digest(viewpoint_camera.world_view_transform),
                "projection_sha256": digest(viewpoint_camera.full_proj_transform),
                "camera_center_sha256": digest(viewpoint_camera.camera_center),
                "prediction_sha256": digest(prediction),
                "prediction_mean": float(prediction.mean().item()),
                "prediction_channel_means": [float(x) for x in prediction.mean((1, 2)).tolist()],
                "prediction_min": float(prediction.min().item()),
                "prediction_max": float(prediction.max().item()),
                "ground_truth_sha256": digest(ground_truth),
                "ground_truth_mean": float(ground_truth.mean().item()),
                "first_frame_psnr": float(
                    evaluator.psnr(prediction[mask][None], ground_truth[mask][None]).item()
                ),
                "torch_version": torch.__version__,
                "tf32_matmul": torch.backends.cuda.matmul.allow_tf32,
                "evaluator_argv": evaluator_argv,
                "preprocess": preprocess_state,
            }
            args.probe_output.parent.mkdir(parents=True, exist_ok=True)
            args.probe_output.write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n")
        return result

    evaluator.preprocess_image = probed_preprocess
    evaluator.render = probed_render
    sys.argv = [str(evaluator.__file__), *evaluator_argv]
    return evaluator.main()


if __name__ == "__main__":
    sys.exit(main())
