#!/usr/bin/env python3
"""Audit exp78-A paper-native VIGS reproduction without hiding bad tracking.

The official public rendering split is the only split used for paper-table parity.
The self-non-KF split is retained as a protocol diagnostic because the exact union
of all methods' keyframes used by the paper is not public.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any


PAPER_RENDERING = {
    "rpng": {
        "table_01": (23.41, 0.750, 0.289),
        "table_02": (20.84, 0.654, 0.338),
        "table_03": (20.71, 0.639, 0.353),
        "table_04": (21.97, 0.742, 0.247),
        "table_05": (21.44, 0.684, 0.345),
        "table_06": (23.47, 0.775, 0.304),
        "table_07": (24.81, 0.821, 0.252),
        "table_08": (21.05, 0.720, 0.383),
    },
    "utmm": {
        "ego-centric-1": (20.05, 0.711, 0.394),
        "ego-centric-2": (20.39, 0.716, 0.382),
        "ego-drive": (21.54, 0.696, 0.399),
        "fast-straight": (21.98, 0.685, 0.458),
        "slow-straight-1": (20.66, 0.669, 0.482),
        "slow-straight-2": (21.92, 0.695, 0.484),
        "square-1": (19.98, 0.644, 0.470),
        "square-2": (20.42, 0.668, 0.460),
    },
}

PAPER_DATASET_MEANS = {
    "rpng": (22.21, 0.723, 0.314),
    "utmm": (20.87, 0.687, 0.441),
}

PAPER_ATE_CM = {
    "rpng": {
        "table_01": 1.31,
        "table_02": 1.57,
        "table_03": 1.22,
        "table_04": 1.75,
        "table_05": 1.28,
        "table_06": 1.38,
        "table_07": 1.08,
        "table_08": 3.86,
    },
    "utmm": {
        "ego-centric-1": 1.81,
        "ego-centric-2": 0.93,
        "ego-drive": 1.45,
        "fast-straight": 1.20,
        "slow-straight-1": 0.81,
        "slow-straight-2": 0.93,
        "square-1": 2.17,
        "square-2": 16.61,
    },
}

# These are the VIGS-SLAM row, not the ORB-SLAM3 row, in paper Table 9.
PAPER_RPNG_RUNTIME = {
    "table_01": (250, 9.11, 7.64),
    "table_02": (349, 7.82, 7.88),
    "table_03": (525, 10.73, 8.64),
    "table_04": (427, 11.25, 9.16),
    "table_05": (341, 13.79, 8.94),
    "table_06": (232, 11.04, 8.36),
    "table_07": (223, 20.22, 7.56),
    "table_08": (579, 12.18, 9.88),
}

TOLERANCE = {"psnr": 0.5, "ssim": 0.02, "lpips": 0.03}


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def rounded(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(value, digits)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--seed-override",
        action="append",
        default=[],
        metavar="DATASET/SEQUENCE=SEED",
        help="replace a failed base-seed run for a named sequence",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    seed_overrides: dict[tuple[str, str], int] = {}
    for value in args.seed_override:
        try:
            name, seed_text = value.rsplit("=", 1)
            dataset, sequence = name.split("/", 1)
            selected_seed = int(seed_text)
        except ValueError as error:
            raise ValueError(
                f"invalid --seed-override {value!r}; expected DATASET/SEQUENCE=SEED"
            ) from error
        seed_overrides[(dataset, sequence)] = selected_seed

    rows: list[dict[str, Any]] = []
    for dataset, sequences in PAPER_RENDERING.items():
        for sequence, target in sequences.items():
            selected_seed = seed_overrides.get((dataset, sequence), args.seed)
            run = args.root / dataset / sequence / f"seed{selected_seed}"
            runtime_path = run / "native_runtime.json"
            rendering_path = run / "psnr/prefinal_split_audit/final_result.json"
            tracking_path = run / "tracking_metrics.json"
            if not (runtime_path.exists() and rendering_path.exists() and tracking_path.exists()):
                continue
            runtime = load(runtime_path)
            rendering = load(rendering_path)
            tracking = load(tracking_path)
            public = rendering["official_public"]
            self_non_kf = rendering["paper_compatible_self_non_kf"]
            consistency = runtime.get("prefinal_tracking_vs_mapping_pose_consistency")
            pose_consistent = None if consistency is None else (
                consistency["camera_center_error_mean"] <= 0.05
                and consistency["camera_center_error_max"] <= 0.5
                and consistency["rotation_error_degrees_mean"] <= 0.5
                and consistency["rotation_error_degrees_max"] <= 5.0
            )
            ate = tracking.get("ate_rmse_cm")
            recall = tracking.get("recall_at_10cm_percent")
            paper_ate = PAPER_ATE_CM[dataset][sequence]
            delta = {
                "psnr": public["mean_psnr"] - target[0],
                "ssim": public["mean_ssim"] - target[1],
                "lpips": public["mean_lpips"] - target[2],
            }
            if pose_consistent is None or recall is None:
                tracking_qualification = "unavailable"
            elif pose_consistent and recall >= 90.0:
                tracking_qualification = "pass"
            else:
                tracking_qualification = "fail"
            row: dict[str, Any] = {
                "dataset": dataset,
                "sequence": sequence,
                "seed": selected_seed,
                "frames": runtime["frames"],
                "keyframes": runtime["keyframes"],
                "gaussians": runtime["gaussians"],
                "mapping_unique_views": runtime.get("mapping_view_count"),
                "mapping_iterations": runtime.get("mapping_iterations"),
                "seconds": rounded(runtime["tracking_plus_mapping_seconds"]),
                "fps": rounded(runtime["tracking_plus_mapping_fps"]),
                "peak_cuda_allocated_gib": rounded(runtime["peak_cuda_allocated_bytes"] / 2**30),
                "peak_cuda_reserved_gib": rounded(runtime["peak_cuda_reserved_bytes"] / 2**30),
                "first_gaussian_frame": runtime.get("first_gaussian_frame"),
                "first_imu_initialized_frame": runtime.get("first_imu_initialized_frame"),
                "official_public": {
                    "views": public["view_count"],
                    "mapping_kf_overlap": public["tracking_keyframe_overlap_count"],
                    "psnr": rounded(public["mean_psnr"]),
                    "ssim": rounded(public["mean_ssim"]),
                    "lpips": rounded(public["mean_lpips"]),
                },
                "self_non_kf_best_effort": {
                    "views": self_non_kf["view_count"],
                    "psnr": rounded(self_non_kf["mean_psnr"]),
                    "ssim": rounded(self_non_kf["mean_ssim"]),
                    "lpips": rounded(self_non_kf["mean_lpips"]),
                },
                "paper": {"psnr": target[0], "ssim": target[1], "lpips": target[2]},
                "public_minus_paper": {key: rounded(value) for key, value in delta.items()},
                "within_symmetric_parity_tolerance": {
                    key: abs(delta[key]) <= TOLERANCE[key] for key in TOLERANCE
                },
                "tracking": {
                    "ate_rmse_cm": ate,
                    "paper_ate_rmse_cm": paper_ate,
                    "ate_minus_paper_cm": rounded(ate - paper_ate) if ate is not None else None,
                    "ate_within_1cm_diagnostic": (
                        abs(ate - paper_ate) <= 1.0 if ate is not None else False
                    ),
                    "recall_at_10cm_percent": recall,
                    "recall_at_least_90_percent": recall is not None and recall >= 90.0,
                    "tracking_map_pose_consistent": pose_consistent,
                    "tracking_map_pose_consistency": consistency,
                },
                "rendering_tracking_qualification": tracking_qualification,
            }
            if dataset == "rpng":
                paper_kfs, paper_fps, paper_mem = PAPER_RPNG_RUNTIME[sequence]
                row["paper_runtime"] = {
                    "keyframes": paper_kfs,
                    "mapping_fps": paper_fps,
                    "mapping_gpu_memory_gib": paper_mem,
                    "keyframes_delta": runtime["keyframes"] - paper_kfs,
                    "fps_delta": rounded(runtime["tracking_plus_mapping_fps"] - paper_fps),
                    "peak_allocated_gib_delta": rounded(
                        runtime["peak_cuda_allocated_bytes"] / 2**30 - paper_mem
                    ),
                }
            rows.append(row)

    aggregates: dict[str, Any] = {}
    for dataset in PAPER_RENDERING:
        selected = [row for row in rows if row["dataset"] == dataset]
        qualified = [
            row for row in selected
            if row["rendering_tracking_qualification"] == "pass"
        ]

        def aggregate(group: list[dict[str, Any]]) -> dict[str, Any]:
            if not group:
                return {"sequence_count": 0}
            local = {
                metric: mean(row["official_public"][metric] for row in group)
                for metric in ("psnr", "ssim", "lpips")
            }
            paper_matched = {
                metric: mean(row["paper"][metric] for row in group)
                for metric in ("psnr", "ssim", "lpips")
            }
            return {
                "sequence_count": len(group),
                "sequences": [row["sequence"] for row in group],
                "official_public_mean": {key: rounded(value) for key, value in local.items()},
                "paper_matched_sequence_mean": {
                    key: rounded(value) for key, value in paper_matched.items()
                },
                "delta": {
                    key: rounded(local[key] - paper_matched[key]) for key in local
                },
            }

        all_sequences = aggregate(selected)
        published = dict(zip(("psnr", "ssim", "lpips"), PAPER_DATASET_MEANS[dataset]))
        published_delta = {
            key: all_sequences["official_public_mean"][key] - value
            for key, value in published.items()
        }
        all_sequences["paper_published_mean"] = published
        all_sequences["delta_vs_paper_published_mean"] = {
            key: rounded(value) for key, value in published_delta.items()
        }
        all_sequences["within_symmetric_parity_tolerance"] = {
            key: abs(published_delta[key]) <= TOLERANCE[key] for key in TOLERANCE
        }
        aggregates[dataset] = {
            "all_raw_sequences": all_sequences,
            "tracking_qualified_subset_diagnostic": aggregate(qualified),
            "tracking_failed_sequences": [
                row["sequence"] for row in selected
                if row["rendering_tracking_qualification"] == "fail"
            ],
            "tracking_qualification_unavailable_sequences": [
                row["sequence"] for row in selected
                if row["rendering_tracking_qualification"] == "unavailable"
            ],
        }

    result = {
        "protocol": "exp78a_paper_native_reproduction_audit_v1",
        "evaluation_state": "prefinal_before_global_ba_and_color_refinement",
        "seed": args.seed,
        "seed_overrides": {
            f"{dataset}/{sequence}": seed
            for (dataset, sequence), seed in sorted(seed_overrides.items())
        },
        "parity_tolerance": TOLERANCE,
        "tracking_qualification_note": (
            "Rendering is marked tracking-qualified only when Recall@10cm >= 90% "
            "and cached map poses agree with the pre-final tracker state. The 1cm "
            "ATE flag is diagnostic, not a predeclared acceptance threshold."
        ),
        "paper_split_limitation": (
            "The exact all-method non-keyframe union is unavailable. official_public "
            "matches released evaluator semantics but overlaps VIGS mapping keyframes; "
            "self_non_kf_best_effort excludes only VIGS keyframes."
        ),
        "rows": rows,
        "aggregates": aggregates,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    temporary.replace(args.output)
    print(json.dumps(aggregates, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
