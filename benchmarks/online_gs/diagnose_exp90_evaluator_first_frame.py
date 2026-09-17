#!/usr/bin/env python3
"""Probe the saved-map evaluator on one RPNG frame without changing the map."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import lietorch
import numpy as np
import torch
from torchmetrics.image.lpip import LearnedPerceptualImagePatchSimilarity

from exp78_evaluate_vigs_ply import load_gaussians, numeric_names, preprocess_image
from gaussian.renderer import render
from gaussian.utils.camera_utils import Camera
from gaussian.utils.graphics_utils import getProjectionMatrix2
from gaussian.utils.loss_utils import psnr, ssim


def digest(tensor: torch.Tensor) -> str:
    return hashlib.sha256(tensor.detach().contiguous().cpu().numpy().tobytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument("--calib", type=Path, required=True)
    parser.add_argument("--frame-index", type=int, default=0)
    args = parser.parse_args()

    names = numeric_names(args.image_dir)
    trajectory = np.loadtxt(args.run_dir / "traj_full_beforeBA.txt")
    poses = lietorch.SE3(
        torch.as_tensor(trajectory[:, 1:], dtype=torch.float32, device="cuda")
    ).inv().matrix().data
    calibration = np.loadtxt(args.calib, delimiter=" ")
    image, params = preprocess_image(
        args.image_dir / names[args.frame_index], calibration, True
    )
    width, height = int(params[-2]), int(params[-1])
    projection = getProjectionMatrix2(
        znear=0.01, zfar=100.0,
        fx=params[0], fy=params[1], cx=params[2], cy=params[3],
        W=width, H=height,
    ).transpose(0, 1).cuda()
    gaussians = load_gaussians(args.run_dir / "3dgs_before_final.ply")
    # Match evaluator's allocation order before the first render.
    lpips = LearnedPerceptualImagePatchSimilarity(net_type="alex", normalize=True).cuda()
    assert lpips is not None
    frame = Camera.init_from_tracking(
        image.float() / 255.0, None, None,
        poses[args.frame_index], args.frame_index, projection, params,
    )
    gt = frame.original_image.cuda()
    mask = gt > 0
    result = {
        "run_dir": str(args.run_dir), "frame_index": args.frame_index,
        "pose_sha256": digest(poses[args.frame_index]),
        "world_view_sha256": digest(frame.world_view_transform),
        "projection_sha256": digest(frame.full_proj_transform),
        "gaussians": int(gaussians.get_xyz.shape[0]),
        "gt_mean": float(gt.mean().item()),
        "backgrounds": {},
    }
    with torch.no_grad():
        for label, level in (("white", 1.0), ("black", 0.0), ("gray", 0.5)):
            background = torch.full((3,), level, dtype=torch.float32, device="cuda")
            trials = []
            for _ in range(2):
                pred = torch.clamp(render(frame, gaussians, background)["render"], 0, 1)
                torch.cuda.synchronize()
                trials.append({
                    "psnr": float(psnr(pred[mask][None], gt[mask][None]).item()),
                    "ssim": float(ssim(pred[None], gt[None]).item()),
                    "prediction_mean": float(pred.mean().item()),
                    "prediction_sha256": digest(pred),
                })
            result["backgrounds"][label] = trials
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
