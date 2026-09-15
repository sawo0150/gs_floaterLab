#!/usr/bin/env python3
"""Evaluate a saved official VIGS pre-final map under explicit split variants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import cv2
import lietorch
import numpy as np
from plyfile import PlyData
import torch
from torchmetrics.image.lpip import LearnedPerceptualImagePatchSimilarity
from tqdm import tqdm

from gaussian.renderer import render
from gaussian.scene.gaussian_model import GaussianModel
from gaussian.utils.camera_utils import Camera
from gaussian.utils.graphics_utils import getProjectionMatrix2
from gaussian.utils.loss_utils import psnr, ssim


TARGET_PIXELS = 341 * 640


def numeric_names(image_dir: Path) -> list[str]:
    try:
        return sorted(
            (path.name for path in image_dir.iterdir() if path.is_file()),
            key=lambda name: float(Path(name).stem),
        )
    except ValueError:
        return sorted(path.name for path in image_dir.iterdir() if path.is_file())


def load_gaussians(path: Path) -> GaussianModel:
    vertices = PlyData.read(path)["vertex"]
    names = set(vertices.data.dtype.names or ())

    def fields(prefix: str) -> list[str]:
        return sorted(
            (name for name in names if name.startswith(prefix)),
            key=lambda name: int(name.rsplit("_", 1)[-1]),
        )

    xyz = np.stack([vertices[axis] for axis in ("x", "y", "z")], axis=1)
    opacity = np.asarray(vertices["opacity"])[:, None]
    scaling = np.stack([vertices[name] for name in fields("scale_")], axis=1)
    rotation = np.stack([vertices[name] for name in fields("rot_")], axis=1)
    dc_flat = np.stack([vertices[name] for name in fields("f_dc_")], axis=1)
    rest_names = fields("f_rest_")
    rest_flat = (
        np.stack([vertices[name] for name in rest_names], axis=1)
        if rest_names
        else np.empty((len(vertices), 0), dtype=np.float32)
    )
    if dc_flat.shape[1] != 3 or rest_flat.shape[1] % 3:
        raise ValueError("unexpected spherical-harmonic fields in PLY")
    sh_degree = int(np.sqrt(rest_flat.shape[1] // 3 + 1) - 1)
    model = GaussianModel(sh_degree=sh_degree)
    device = torch.device("cuda")
    model._xyz = torch.as_tensor(xyz, dtype=torch.float32, device=device)
    model._opacity = torch.as_tensor(opacity, dtype=torch.float32, device=device)
    model._scaling = torch.as_tensor(scaling, dtype=torch.float32, device=device)
    model._rotation = torch.as_tensor(rotation, dtype=torch.float32, device=device)
    model._features_dc = torch.as_tensor(
        dc_flat.reshape(len(vertices), 3, 1).transpose(0, 2, 1).copy(),
        dtype=torch.float32,
        device=device,
    )
    model._features_rest = torch.as_tensor(
        rest_flat.reshape(len(vertices), 3, -1).transpose(0, 2, 1).copy(),
        dtype=torch.float32,
        device=device,
    )
    model.active_sh_degree = sh_degree
    return model


def preprocess_image(
    path: Path, calibration: np.ndarray, undistort: bool
) -> tuple[torch.Tensor, list[float | int]]:
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"failed to load image: {path}")
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height0, width0, _ = image.shape
    if len(calibration) > 4 and undistort:
        camera_matrix = np.array(
            [
                [calibration[0], 0, calibration[2]],
                [0, calibration[1], calibration[3]],
                [0, 0, 1],
            ]
        )
        image = cv2.undistort(image, camera_matrix, calibration[4:])
    height1 = int(height0 * np.sqrt(TARGET_PIXELS / (height0 * width0)))
    width1 = int(width0 * np.sqrt(TARGET_PIXELS / (height0 * width0)))
    height1 -= height1 % 8
    width1 -= width1 % 8
    image = cv2.resize(image, (width1, height1))
    intrinsics = calibration[:4].copy()
    intrinsics[[0, 2]] *= width1 / width0
    intrinsics[[1, 3]] *= height1 / height0
    camera = torch.as_tensor(image).permute(2, 0, 1)
    return camera, [*intrinsics.tolist(), width1, height1]


def timestamp_from_name(name: str, nanoseconds: bool) -> float:
    value = float(re.findall(r"[+]?(?:\d*\.\d+|\d+)", name)[-1])
    return value / 1e9 if nanoseconds else value


def aggregate(rows: list[dict[str, object]], key: str) -> dict[str, object]:
    selected = [row for row in rows if bool(row[key])]
    if not selected:
        raise ValueError(f"split {key} selected no frames")
    return {
        "mean_psnr": float(np.mean([float(row["psnr"]) for row in selected])),
        "mean_ssim": float(np.mean([float(row["ssim"]) for row in selected])),
        "mean_lpips": float(np.mean([float(row["lpips"]) for row in selected])),
        "view_count": len(selected),
        "tracking_keyframe_overlap_count": sum(bool(row["is_keyframe"]) for row in selected),
        "mapping_view_overlap_count": sum(
            bool(row["is_mapping_view"]) for row in selected
        ),
        "mapping_disjoint": not any(bool(row["is_mapping_view"]) for row in selected),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument("--calib", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--rgb-file-in-nanoseconds", action="store_true")
    parser.add_argument("--undistort", action="store_true")
    parser.add_argument("--map-file-name", default="3dgs_before_final.ply")
    parser.add_argument("--trajectory-file-name", default="traj_full_beforeBA.txt")
    parser.add_argument("--keyframe-trajectory-file-name", default="traj_kf_beforeBA.txt")
    parser.add_argument("--result-subdir", default="prefinal_split_audit")
    parser.add_argument(
        "--mapped-uids-json",
        type=Path,
        help=(
            "JSON list of actual Gaussian-supervision frame indices. If omitted, "
            "tracking keyframes are conservatively treated as mapping views."
        ),
    )
    parser.add_argument(
        "--evaluation-state",
        default="prefinal_before_global_ba_and_color_refinement",
        help="Explicit map/trajectory state label written into the result metadata.",
    )
    args = parser.parse_args()

    run_dir = args.run_dir.resolve()
    map_path = run_dir / args.map_file_name
    trajectory_path = run_dir / args.trajectory_file_name
    keyframe_trajectory_path = run_dir / args.keyframe_trajectory_file_name
    names = numeric_names(args.image_dir)
    manifest = json.loads(args.manifest.read_text())
    manifest_names = {row["uid"] for row in manifest["views"]}
    name_to_index = {name: index for index, name in enumerate(names)}
    missing_manifest = sorted(manifest_names - set(names))
    if missing_manifest:
        raise ValueError(f"manifest has missing RGB UIDs: {missing_manifest[:5]}")
    manifest_indices = {name_to_index[name] for name in manifest_names}

    trajectory = np.loadtxt(trajectory_path)
    keyframe_trajectory = np.loadtxt(keyframe_trajectory_path)
    if len(trajectory) != len(names):
        raise ValueError(f"trajectory rows {len(trajectory)} != RGB frames {len(names)}")
    image_timestamps = np.asarray(
        [timestamp_from_name(name, args.rgb_file_in_nanoseconds) for name in names]
    )
    max_timestamp_error = float(np.max(np.abs(trajectory[:, 0] - image_timestamps)))
    if max_timestamp_error > 1e-5:
        raise ValueError(f"full trajectory timestamp mismatch: {max_timestamp_error}")
    keyframe_indices: set[int] = set()
    for timestamp in np.atleast_2d(keyframe_trajectory)[:, 0]:
        index = int(np.argmin(np.abs(image_timestamps - timestamp)))
        if abs(image_timestamps[index] - timestamp) > 1e-5:
            raise ValueError(f"unmatched keyframe timestamp: {timestamp}")
        keyframe_indices.add(index)
    mapping_indices = set(keyframe_indices)
    mapping_disjoint_enforced = args.mapped_uids_json is not None
    if args.mapped_uids_json is not None:
        mapping_indices = {
            int(value) for value in json.loads(args.mapped_uids_json.read_text())
        }

    # Saved trajectories are camera-to-world; the renderer consumes world-to-camera.
    poses_world_to_camera = lietorch.SE3(
        torch.as_tensor(trajectory[:, 1:], dtype=torch.float32, device="cuda")
    ).inv().matrix().data
    calibration = np.loadtxt(args.calib, delimiter=" ")
    first_image, camera_params = preprocess_image(
        args.image_dir / names[0], calibration, args.undistort
    )
    width, height = int(camera_params[-2]), int(camera_params[-1])
    projection = getProjectionMatrix2(
        znear=0.01,
        zfar=100.0,
        fx=camera_params[0],
        fy=camera_params[1],
        cx=camera_params[2],
        cy=camera_params[3],
        W=width,
        H=height,
    ).transpose(0, 1).cuda()
    gaussians = load_gaussians(map_path)
    background = torch.tensor([1, 1, 1], dtype=torch.float32, device="cuda")
    lpips = LearnedPerceptualImagePatchSimilarity(
        net_type="alex", normalize=True
    ).cuda()

    public_indices = {
        index
        for index in range(len(names))
        if index % 5 == 0 or index in keyframe_indices or index == len(names) - 1
    }
    paper_self_indices = {
        index
        for index in range(len(names))
        if (index % 5 == 0 or index == len(names) - 1) and index not in keyframe_indices
    }
    render_indices = sorted(public_indices | manifest_indices)
    rows: list[dict[str, object]] = []
    with torch.no_grad():
        for index in tqdm(render_indices, desc="Evaluate pre-final PLY"):
            image_tensor, params = (
                (first_image, camera_params)
                if index == 0
                else preprocess_image(args.image_dir / names[index], calibration, args.undistort)
            )
            if params != camera_params:
                raise ValueError("preprocessed camera shape or intrinsics changed within sequence")
            frame = Camera.init_from_tracking(
                image_tensor.float() / 255.0,
                None,
                None,
                poses_world_to_camera[index],
                index,
                projection,
                camera_params,
            )
            ground_truth = frame.original_image.cuda()
            prediction = torch.clamp(render(frame, gaussians, background)["render"], 0, 1)
            mask = ground_truth > 0
            row = {
                "frame_index": index,
                "uid": names[index],
                "psnr": float(psnr(prediction[mask][None], ground_truth[mask][None]).item()),
                "ssim": float(ssim(prediction[None], ground_truth[None]).item()),
                "lpips": float(lpips(prediction[None], ground_truth[None]).item()),
                "is_keyframe": index in keyframe_indices,
                "is_mapping_view": index in mapping_indices,
                "official_public_split": index in public_indices,
                "paper_compatible_self_non_kf_split": index in paper_self_indices,
                "predeclared_fixed_manifest_split": index in manifest_indices,
            }
            rows.append(row)
            frame.clean()

    result = {
        "protocol": "exp78_split_audit_v2",
        "evaluation_state": args.evaluation_state,
        "map": str(map_path),
        "trajectory": str(trajectory_path),
        "gaussians": int(gaussians.get_xyz.shape[0]),
        "keyframes": len(keyframe_indices),
        "full_trajectory_timestamp_max_abs_error_seconds": max_timestamp_error,
        "official_source_condition": "idx % 5 == 0 OR idx in VIGS keyframes OR final frame",
        "paper_compatible_best_effort_condition": "(idx % 5 == 0 OR final frame) AND idx not in VIGS keyframes; other methods' keyframes unavailable",
        "predeclared_manifest_mapping_note": (
            "Mapping-disjoint filtering was enforced before mapper dispatch; "
            "actual mapped UID overlap is reported."
            if mapping_disjoint_enforced
            else "Native VIGS was not prevented from mapping these views; overlap "
            "is reported and this arm is not a fair strict result."
        ),
        "mapping_disjoint_filter_enforced": mapping_disjoint_enforced,
        "official_public": aggregate(rows, "official_public_split"),
        "paper_compatible_self_non_kf": aggregate(
            rows, "paper_compatible_self_non_kf_split"
        ),
        "predeclared_fixed_manifest_posthoc": aggregate(
            rows, "predeclared_fixed_manifest_split"
        ),
        "per_view": rows,
    }
    output = run_dir / "psnr" / args.result_subdir / "final_result.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    temporary.replace(output)
    print(json.dumps({key: value for key, value in result.items() if key != "per_view"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
