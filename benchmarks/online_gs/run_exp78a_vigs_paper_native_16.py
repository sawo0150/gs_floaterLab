#!/usr/bin/env python3
"""Run and evaluate clean paper-native VIGS on all RPNG and UTMM sequences."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


WORKSPACE = Path(__file__).resolve().parents[2]
OFFICIAL = Path("/home/intern/VIGS-SLAM-official-exp78")
PYTHON_ENV = Path("/home/colin/miniconda3/envs/vigs-slam-5090")
RUNNER = WORKSPACE / "benchmarks/online_gs/run_exp78a_vigs_paper_native_sequence.sh"
EVALUATOR = WORKSPACE / "benchmarks/online_gs/exp78_evaluate_vigs_ply.py"
MANIFESTS = WORKSPACE / "context/experiments/exp78/b_strict_fair_comparison/manifests"
OUTPUT_ROOT = Path(
    os.environ.get(
        "EXP78_OUTPUT_ROOT",
        WORKSPACE
        / "results/experiments/exp78/a_paper_reproduction/native_official_22ffe24",
    )
).resolve()

# Short sequences first; table_06 is retained at its paper-gate location and skipped
# automatically when all expected outputs already exist.
SEQUENCES = [
    ("utmm", "fast-straight"),
    ("utmm", "slow-straight-1"),
    ("utmm", "slow-straight-2"),
    ("utmm", "square-2"),
    ("utmm", "ego-centric-2"),
    ("utmm", "ego-drive"),
    ("utmm", "ego-centric-1"),
    ("utmm", "square-1"),
    ("rpng", "table_01"),
    ("rpng", "table_06"),
    ("rpng", "table_02"),
    ("rpng", "table_07"),
    ("rpng", "table_04"),
    ("rpng", "table_05"),
    ("rpng", "table_03"),
    ("rpng", "table_08"),
]
if sequence_filter := os.environ.get("EXP78_SEQUENCE_FILTER"):
    requested = {
        tuple(item.strip().split("/", 1))
        for item in sequence_filter.split(",")
        if item.strip()
    }
    unknown = requested.difference(SEQUENCES)
    if unknown:
        raise ValueError(f"unknown EXP78_SEQUENCE_FILTER entries: {sorted(unknown)}")
    SEQUENCES = [item for item in SEQUENCES if item in requested]

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


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def inputs(dataset: str, sequence: str) -> dict[str, Path | bool]:
    if dataset == "rpng":
        root = WORKSPACE / "data/benchmarks/rpng/prepared/rpngar" / sequence
        return {
            "images": root / "rgb",
            "calibration": OFFICIAL / "calib/rpngar.txt",
            "groundtruth": root / "gt.txt",
            "rgb_nanoseconds": True,
        }
    root = WORKSPACE / "data/benchmarks/utmm/prepared/UTMM_Dataset" / sequence
    return {
        "images": root / "rgb_timestamp",
        "calibration": root / "intrinsics_ours.txt",
        "groundtruth": root / "groundtruth.txt",
        "rgb_nanoseconds": True,
    }


def gpu_processes() -> str:
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name,used_memory",
            "--format=csv,noheader",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def wait_for_gpu() -> None:
    while True:
        processes = gpu_processes()
        if not processes:
            return
        print("EXP78A_GPU_WAIT another compute process is active; not terminating it:")
        print(processes, flush=True)
        time.sleep(30)


def clean_env() -> dict[str, str]:
    env = os.environ.copy()
    paths = [
        OFFICIAL,
        OFFICIAL / "thirdparty/diff-gaussian-rasterization",
        OFFICIAL / "thirdparty/simple-knn",
        OFFICIAL / "thirdparty/lietorch_5090",
        OFFICIAL / "vigs",
    ]
    env["PYTHONPATH"] = os.pathsep.join(map(str, paths))
    libraries = [
        PYTHON_ENV / "lib/python3.11/site-packages/torch/lib",
        PYTHON_ENV / "lib",
    ]
    env["LD_LIBRARY_PATH"] = os.pathsep.join(map(str, libraries))
    env["PYTHONUNBUFFERED"] = "1"
    return env


def evaluate_rendering(dataset: str, sequence: str, output: Path) -> None:
    destination = output / "psnr/prefinal_split_audit/final_result.json"
    if destination.exists():
        print(f"EXP78A_SKIP_RENDER {dataset}/{sequence}", flush=True)
        return
    data = inputs(dataset, sequence)
    command = [
        str(PYTHON_ENV / "bin/python"),
        str(EVALUATOR),
        "--run-dir",
        str(output),
        "--image-dir",
        str(data["images"]),
        "--calib",
        str(data["calibration"]),
        "--manifest",
        str(MANIFESTS / f"{dataset}_{sequence}.json"),
        "--rgb-file-in-nanoseconds",
        "--undistort",
    ]
    wait_for_gpu()
    subprocess.run(command, cwd=WORKSPACE, env=clean_env(), check=True)


def evaluate_tracking(dataset: str, sequence: str, output: Path) -> None:
    destination = output / "tracking_metrics.json"
    if destination.exists():
        print(f"EXP78A_SKIP_TRACKING {dataset}/{sequence}", flush=True)
        return
    data = inputs(dataset, sequence)
    trajectory = output / "traj_kf_beforeBA.txt"
    command = [
        str(PYTHON_ENV / "bin/evo_ape"),
        "tum",
        "-vas",
        "--no_warnings",
        "--plot_mode",
        "xy",
        "--save_plot",
        str(output / "ape_sim3.png"),
        "--save_results",
        str(output / "ape_results.zip"),
        str(data["groundtruth"]),
        str(trajectory),
    ]
    result = subprocess.run(command, text=True, capture_output=True, env=clean_env())
    (output / "evo_ape_sim3.txt").write_text(result.stdout + result.stderr)
    metrics: dict[str, object] = {"command": command, "returncode": result.returncode}
    if result.returncode == 0:
        rmse = re.findall(r"^\s*rmse\s+([0-9.eE+-]+)", result.stdout, re.MULTILINE)
        scale = re.findall(r"Scale correction:\s*([0-9.eE+-]+)", result.stdout)
        pairs = re.findall(r"Compared\s+(\d+)\s+absolute pose pairs", result.stdout)
        if rmse:
            metrics["ate_rmse_m"] = float(rmse[-1])
            metrics["ate_rmse_cm"] = 100.0 * float(rmse[-1])
        if scale:
            metrics["sim3_scale"] = float(scale[-1])
            metrics["scale_error_percent"] = 100.0 * abs(1.0 - float(scale[-1]))
        if pairs:
            metrics["associated_pose_pairs"] = int(pairs[-1])
        sys.path.insert(0, str(OFFICIAL / "vigs"))
        from util.compute_recall import compute_recall_from_file

        _, _, recall = compute_recall_from_file(
            str(data["groundtruth"]), str(trajectory), thresh_cm=10
        )
        metrics["recall_at_10cm_percent"] = float(recall)
    write_json(destination, metrics)


def collect_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for dataset, sequence in SEQUENCES:
        output = OUTPUT_ROOT / dataset / sequence / "seed0"
        runtime_path = output / "native_runtime.json"
        rendering_path = output / "psnr/prefinal_split_audit/final_result.json"
        tracking_path = output / "tracking_metrics.json"
        if not runtime_path.exists() or not rendering_path.exists():
            continue
        runtime = json.loads(runtime_path.read_text())
        rendering = json.loads(rendering_path.read_text())
        tracking = json.loads(tracking_path.read_text()) if tracking_path.exists() else {}
        target = PAPER_RENDERING[dataset][sequence]
        public = rendering["official_public"]
        paper_compatible = rendering["paper_compatible_self_non_kf"]
        rows.append(
            {
                "dataset": dataset,
                "sequence": sequence,
                "frames": runtime["frames"],
                "keyframes": runtime["keyframes"],
                "gaussians": runtime["gaussians"],
                "seconds": runtime["tracking_plus_mapping_seconds"],
                "fps": runtime["tracking_plus_mapping_fps"],
                "peak_cuda_allocated_bytes": runtime["peak_cuda_allocated_bytes"],
                "paper_psnr": target[0],
                "paper_ssim": target[1],
                "paper_lpips": target[2],
                "public_psnr": public["mean_psnr"],
                "public_ssim": public["mean_ssim"],
                "public_lpips": public["mean_lpips"],
                "public_views": public["view_count"],
                "public_kf_overlap": public["tracking_keyframe_overlap_count"],
                "self_non_kf_psnr": paper_compatible["mean_psnr"],
                "self_non_kf_ssim": paper_compatible["mean_ssim"],
                "self_non_kf_lpips": paper_compatible["mean_lpips"],
                "self_non_kf_views": paper_compatible["view_count"],
                "ate_rmse_cm": tracking.get("ate_rmse_cm"),
                "recall_at_10cm_percent": tracking.get("recall_at_10cm_percent"),
            }
        )
    return rows


def write_summary() -> None:
    rows = collect_rows()
    fields = list(rows[0]) if rows else ["dataset", "sequence"]
    csv_path = OUTPUT_ROOT / "summary.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = csv_path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(csv_path)
    aggregates: dict[str, object] = {}
    for dataset in ("rpng", "utmm"):
        selected = [row for row in rows if row["dataset"] == dataset]
        if not selected:
            continue
        aggregates[dataset] = {
            "sequence_count": len(selected),
            "official_public_mean_psnr": sum(float(row["public_psnr"]) for row in selected) / len(selected),
            "official_public_mean_ssim": sum(float(row["public_ssim"]) for row in selected) / len(selected),
            "official_public_mean_lpips": sum(float(row["public_lpips"]) for row in selected) / len(selected),
            "paper_compatible_self_non_kf_mean_psnr": sum(float(row["self_non_kf_psnr"]) for row in selected) / len(selected),
            "paper_compatible_self_non_kf_mean_ssim": sum(float(row["self_non_kf_ssim"]) for row in selected) / len(selected),
            "paper_compatible_self_non_kf_mean_lpips": sum(float(row["self_non_kf_lpips"]) for row in selected) / len(selected),
        }
    write_json(
        OUTPUT_ROOT / "summary.json",
        {
            "protocol": "paper_native_prefinal_v1",
            "rows": rows,
            "aggregates": aggregates,
        },
    )


def main() -> int:
    state_path = OUTPUT_ROOT / "queue_state.json"
    failures: list[dict[str, object]] = []
    position = 0
    current: str | None = None
    try:
        for position, (dataset, sequence) in enumerate(SEQUENCES):
            current = f"{dataset}/{sequence}"
            output = OUTPUT_ROOT / dataset / sequence / "seed0"
            write_json(
                state_path,
                {
                    "status": "running",
                    "position": position,
                    "total": len(SEQUENCES),
                    "current": current,
                    "failures": failures,
                },
            )
            try:
                if (output / "native_runtime.json").exists():
                    print(f"EXP78A_SKIP_NATIVE {dataset}/{sequence}", flush=True)
                else:
                    wait_for_gpu()
                    subprocess.run(
                        ["bash", str(RUNNER), dataset, sequence, "0", str(output)],
                        cwd=WORKSPACE,
                        check=True,
                    )
                evaluate_rendering(dataset, sequence, output)
                evaluate_tracking(dataset, sequence, output)
                write_summary()
            except Exception as error:
                failure = {
                    "dataset": dataset,
                    "sequence": sequence,
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
                failures.append(failure)
                print("EXP78A_FAILURE " + json.dumps(failure, sort_keys=True), flush=True)
    except KeyboardInterrupt:
        write_summary()
        write_json(
            state_path,
            {
                "status": "interrupted",
                "position": position,
                "total": len(SEQUENCES),
                "current": current,
                "failures": failures,
            },
        )
        print(f"EXP78A_INTERRUPTED current={current}", flush=True)
        return 130
    write_summary()
    write_json(
        state_path,
        {
            "status": "complete_with_failures" if failures else "complete",
            "position": len(SEQUENCES),
            "total": len(SEQUENCES),
            "current": None,
            "failures": failures,
        },
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
