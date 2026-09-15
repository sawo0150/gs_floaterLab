#!/usr/bin/env python3
"""Compare exp78 official README TensorRT probes with PyTorch controls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROBES = (
    ("utmm", "fast-straight", 0),
    ("utmm", "ego-drive", 0),
    ("rpng", "table_06", 0),
    # The PyTorch seed0 trajectory is invalid; seed1 is the preregistered valid retry.
    ("rpng", "table_08", 1),
)


def load(run: Path) -> dict:
    runtime = json.loads((run / "native_runtime.json").read_text())
    rendering = json.loads(
        (run / "psnr/prefinal_split_audit/final_result.json").read_text()
    )["official_public"]
    tracking = json.loads((run / "tracking_metrics.json").read_text())
    return {"runtime": runtime, "rendering": rendering, "tracking": tracking}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pytorch-root", type=Path, required=True)
    parser.add_argument("--tensorrt-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for dataset, sequence, pytorch_seed in PROBES:
        pytorch_run = args.pytorch_root / dataset / sequence / f"seed{pytorch_seed}"
        tensorrt_run = args.tensorrt_root / dataset / sequence / "seed0"
        pytorch = load(pytorch_run)
        tensorrt = load(tensorrt_run)
        pr, tr = pytorch["runtime"], tensorrt["runtime"]
        pi, ti = pytorch["rendering"], tensorrt["rendering"]
        pt, tt = pytorch["tracking"], tensorrt["tracking"]
        rows.append(
            {
                "dataset": dataset,
                "sequence": sequence,
                "pytorch_seed": pytorch_seed,
                "tensorrt_seed": 0,
                "pytorch": {
                    "psnr": pi["mean_psnr"],
                    "ssim": pi["mean_ssim"],
                    "lpips": pi["mean_lpips"],
                    "ate_rmse_cm": pt["ate_rmse_cm"],
                    "recall_at_10cm_percent": pt["recall_at_10cm_percent"],
                    "keyframes": pr["keyframes"],
                    "gaussians": pr["gaussians"],
                    "seconds": pr["tracking_plus_mapping_seconds"],
                    "fps": pr["tracking_plus_mapping_fps"],
                    "peak_cuda_allocated_bytes": pr["peak_cuda_allocated_bytes"],
                    "peak_cuda_reserved_bytes": pr["peak_cuda_reserved_bytes"],
                },
                "tensorrt": {
                    "psnr": ti["mean_psnr"],
                    "ssim": ti["mean_ssim"],
                    "lpips": ti["mean_lpips"],
                    "ate_rmse_cm": tt["ate_rmse_cm"],
                    "recall_at_10cm_percent": tt["recall_at_10cm_percent"],
                    "keyframes": tr["keyframes"],
                    "gaussians": tr["gaussians"],
                    "mapping_iterations": tr["mapping_iterations"],
                    "mapping_view_count": tr["mapping_view_count"],
                    "seconds": tr["tracking_plus_mapping_seconds"],
                    "fps": tr["tracking_plus_mapping_fps"],
                    "peak_cuda_allocated_bytes": tr["peak_cuda_allocated_bytes"],
                    "peak_cuda_reserved_bytes": tr["peak_cuda_reserved_bytes"],
                    "pose_consistency": tr[
                        "prefinal_tracking_vs_mapping_pose_consistency"
                    ],
                },
                "delta_tensorrt_minus_pytorch": {
                    "psnr": ti["mean_psnr"] - pi["mean_psnr"],
                    "ssim": ti["mean_ssim"] - pi["mean_ssim"],
                    "lpips": ti["mean_lpips"] - pi["mean_lpips"],
                    "ate_rmse_cm": tt["ate_rmse_cm"] - pt["ate_rmse_cm"],
                    "seconds": tr["tracking_plus_mapping_seconds"]
                    - pr["tracking_plus_mapping_seconds"],
                    "runtime_ratio": tr["tracking_plus_mapping_seconds"]
                    / pr["tracking_plus_mapping_seconds"],
                    "speedup": pr["tracking_plus_mapping_seconds"]
                    / tr["tracking_plus_mapping_seconds"],
                    "peak_cuda_allocated_gib": (
                        tr["peak_cuda_allocated_bytes"]
                        - pr["peak_cuda_allocated_bytes"]
                    )
                    / 2**30,
                    "peak_cuda_reserved_gib": (
                        tr["peak_cuda_reserved_bytes"]
                        - pr["peak_cuda_reserved_bytes"]
                    )
                    / 2**30,
                },
            }
        )
    output = {
        "protocol": "exp78a-official-readme-trt-probes-v1",
        "comparison_note": (
            "table_08 uses the valid PyTorch seed1 retry because PyTorch seed0 "
            "has catastrophic trajectory failure; all other pairs use seed0"
        ),
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
