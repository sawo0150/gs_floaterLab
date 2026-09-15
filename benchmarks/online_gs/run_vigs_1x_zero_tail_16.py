#!/usr/bin/env python3
"""Run exp79 fixed-1x optimizer-zero-tail profile on the exp77 datasets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


WORKSPACE = Path(__file__).resolve().parents[2]
VIGS_REPO = (WORKSPACE / "repos/main/VIGS-SLAM").resolve()
RUNNER = VIGS_REPO / "exp72_axes/run_scheduler_ablation.sh"
PYTHON_ENV = Path("/home/colin/miniconda3/envs/vigs-slam-5090")
PROTOCOL = "fixed1x_sensor_eos_zero_tail_v1"
METHOD = "vigs_final_v7_5090_clean"
RUNSET = "exp80_2a3eeeb5_dirty_20260910"
OUTPUT_ROOT = WORKSPACE / "results/benchmarks" / PROTOCOL / METHOD / RUNSET


SEQUENCES = [
    # Short runs first so input/config failures surface early.
    ("utmm", "fast-straight", 332),
    ("utmm", "slow-straight-1", 393),
    ("utmm", "slow-straight-2", 597),
    ("utmm", "square-2", 1219),
    ("utmm", "ego-centric-2", 1298),
    ("utmm", "ego-drive", 1399),
    ("utmm", "ego-centric-1", 1535),
    ("utmm", "square-1", 1614),
    ("rpng", "table_01", 2506),
    ("rpng", "table_06", 2767),
    ("rpng", "table_02", 2914),
    ("rpng", "table_07", 4784),
    ("rpng", "table_04", 6068),
    ("rpng", "table_05", 6164),
    ("rpng", "table_03", 7006),
    ("rpng", "table_08", 8484),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inputs(dataset: str, sequence: str) -> dict[str, Path | int]:
    if dataset == "rpng":
        root = WORKSPACE / "data/benchmarks/rpng/prepared/rpngar" / sequence
        return {
            "root": root,
            "images": root / "rgb",
            "imu": root / "imu.txt",
            "calibration": VIGS_REPO / "calib/rpngar.txt",
            "config": WORKSPACE / "benchmarks/online_gs/config/vigs_final_v7_rpng.yaml",
            "groundtruth": root / "gt.txt",
            "imu_init": 20,
            "buffer": 700,
        }
    root = WORKSPACE / "data/benchmarks/utmm/prepared/UTMM_Dataset" / sequence
    return {
        "root": root,
        "images": root / "rgb_timestamp",
        "imu": root / "imu_ours.txt",
        "calibration": root / "intrinsics_ours.txt",
        "config": WORKSPACE / "benchmarks/online_gs/config/vigs_final_v7_utmm.yaml",
        "groundtruth": root / "groundtruth.txt",
        "imu_init": 15,
        "buffer": -1,
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def check_gpu_idle() -> None:
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name,used_gpu_memory",
            "--format=csv,noheader,nounits",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    if result.stdout.strip():
        raise RuntimeError("another GPU compute process appeared:\n" + result.stdout)


def write_summary() -> None:
    rows = []
    for dataset, sequence, frames in SEQUENCES:
        out = OUTPUT_ROOT / dataset / sequence / "seed0"
        completion = out / "run_complete.json"
        rendering = out / "psnr/online_final/final_result.json"
        if not completion.exists() or not rendering.exists():
            continue
        run = json.loads(completion.read_text())
        render = json.loads(rendering.read_text())
        tracking = run.get("tracking", {})
        rows.append(
            {
                "dataset": dataset,
                "sequence": sequence,
                "frames": frames,
                "elapsed_seconds": run.get("elapsed_seconds"),
                "fixed_eval_views": render.get("fixed_eval_view_count"),
                "heldout_mean_psnr": render.get("fixed_eval_mean_psnr"),
                "heldout_mean_ssim": render.get("fixed_eval_mean_ssim"),
                "heldout_mean_lpips": render.get("fixed_eval_mean_lpips"),
                "ate_rmse_cm_sim3": tracking.get("ate_rmse_cm"),
                "scale_error_percent": tracking.get("scale_error_percent"),
                "recall_at_10cm_percent": tracking.get("recall_at_10cm_percent"),
                "associated_pose_pairs": tracking.get("associated_pose_pairs"),
            }
        )
    fields = [
        "dataset", "sequence", "frames", "elapsed_seconds", "fixed_eval_views",
        "heldout_mean_psnr", "heldout_mean_ssim", "heldout_mean_lpips",
        "ate_rmse_cm_sim3", "scale_error_percent", "recall_at_10cm_percent",
        "associated_pose_pairs",
    ]
    path = OUTPUT_ROOT / "summary.csv"
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def evaluate_tracking(out: Path, gt: Path, env: dict[str, str]) -> dict[str, object]:
    trajectory = out / "traj_kf_beforeBA.txt"
    ape_log = out / "evo_ape_sim3.txt"
    command = [
        str(PYTHON_ENV / "bin/evo_ape"),
        "tum",
        "-vas",
        "--no_warnings",
        "--plot_mode",
        "xy",
        "--save_plot",
        str(out / "ape_sim3.png"),
        "--save_results",
        str(out / "ape_results.zip"),
        str(gt),
        str(trajectory),
    ]
    result = subprocess.run(command, text=True, capture_output=True, env=env)
    ape_log.write_text(result.stdout + result.stderr)
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
        sys.path.insert(0, str(VIGS_REPO))
        from vigs.util.compute_recall import compute_recall_from_file

        _, _, recall = compute_recall_from_file(str(gt), str(trajectory), thresh_cm=10)
        metrics["recall_at_10cm_percent"] = float(recall)
    write_json(out / "tracking_metrics.json", metrics)
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", action="append", default=[], metavar="DATASET/SEQUENCE")
    parser.add_argument("--skip-gpu-idle-check", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()

    selected = SEQUENCES
    if args.only:
        wanted = set(args.only)
        selected = [item for item in SEQUENCES if f"{item[0]}/{item[1]}" in wanted]
        missing = wanted - {f"{item[0]}/{item[1]}" for item in selected}
        if missing:
            parser.error("unknown sequence(s): " + ", ".join(sorted(missing)))

    env = {k: v for k, v in os.environ.items() if not k.startswith(("EXP69_", "EXP70_", "EXP72_", "EXP73_", "VIGS_"))}
    env["PATH"] = str(PYTHON_ENV / "bin") + os.pathsep + env.get("PATH", "")
    env["PYTHONUNBUFFERED"] = "1"
    env["EXP69_REPLAY_TIME_SCALE"] = "1"
    env["VIGS_SENSOR_EOS_ZERO_TAIL"] = "1"
    env["EXP69_SCHEDULER_VERSION"] = "v7"
    env["EXP69_SCHEDULER_MODE_REQUESTED"] = "v7"
    # The available fnet TensorRT engine is static 464x464 (Aria-specific).
    # RPNG/UTMM retain native benchmark resolutions, so use the exact PyTorch
    # fnet while keeping the resolution-independent TRT paths enabled.
    env["VIGS_DISABLE_FNET_TRT"] = "1"
    env["VIGS_DISABLE_UPDATE_TRT"] = "1"

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    state_path = OUTPUT_ROOT / "queue_state.json"
    state: dict[str, object] = {
        "protocol": PROTOCOL,
        "method": METHOD,
        "runset": RUNSET,
        "started_unix": time.time(),
        "runner": str(RUNNER),
        "runner_sha256": sha256(RUNNER),
        "repo_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=VIGS_REPO, text=True
        ).strip(),
        "sequences": {},
    }
    write_json(state_path, state)

    failures = 0
    for dataset, sequence, frames in selected:
        key = f"{dataset}/{sequence}"
        spec = inputs(dataset, sequence)
        out = OUTPUT_ROOT / dataset / sequence / "seed0"
        out.mkdir(parents=True, exist_ok=True)
        completion = out / "run_complete.json"
        if completion.exists():
            print(f"QUEUE_SKIP already complete: {key}", flush=True)
            state["sequences"][key] = json.loads(completion.read_text())  # type: ignore[index]
            write_json(state_path, state)
            write_summary()
            continue
        prior_manifest = out / "run_manifest.json"
        if prior_manifest.exists() and not args.retry_failed:
            prior = json.loads(prior_manifest.read_text())
            if prior.get("status") == "failed":
                print(f"QUEUE_SKIP recorded failure: {key}", flush=True)
                state["sequences"][key] = prior  # type: ignore[index]
                failures += 1
                write_json(state_path, state)
                write_summary()
                continue

        for label in ("images", "imu", "calibration", "config", "groundtruth"):
            path = spec[label]
            if not isinstance(path, Path) or not path.exists():
                raise FileNotFoundError(f"{key}: missing {label}: {path}")
        if not args.skip_gpu_idle_check:
            check_gpu_idle()

        run_env = env.copy()
        run_env.update(
            {
                "EXP69_IMAGE_DIR": str(spec["images"]),
                "EXP69_IMU_FILE": str(spec["imu"]),
                "EXP69_CALIBRATION": str(spec["calibration"]),
                "EXP69_CONFIG_FILE": str(spec["config"]),
                "EXP69_IMU_POSEINIT_AFTER": str(spec["imu_init"]),
                "EXP69_BUFFER_SIZE": str(spec["buffer"]),
            }
        )
        command = ["bash", str(RUNNER), f"benchmark_{dataset}_{sequence}", str(out), "baseline"]
        manifest = {
            "dataset": dataset,
            "sequence": sequence,
            "frames": frames,
            "protocol": PROTOCOL,
            "command": command,
            "inputs": {key: str(value) for key, value in spec.items()},
            "config_sha256": sha256(spec["config"]),  # type: ignore[arg-type]
            "started_unix": time.time(),
            "status": "running",
        }
        manifest["environment_overrides"] = {k: v for k, v in run_env.items() if k.startswith(("EXP69_", "EXP70_", "EXP72_", "EXP73_", "VIGS_"))}
        write_json(out / "run_manifest.json", manifest)
        state["sequences"][key] = manifest
        write_json(state_path, state)
        print(f"QUEUE_START {key} frames={frames} output={out}", flush=True)
        start = time.monotonic()
        result = subprocess.run(command, cwd=VIGS_REPO, env=run_env)
        manifest["elapsed_seconds"] = time.monotonic() - start
        manifest["returncode"] = result.returncode
        manifest["status"] = "complete" if result.returncode == 0 else "failed"
        if result.returncode == 0:
            audit = json.loads((out / "sensor_eos_audit.json").read_text())
            render = json.loads((out / "psnr/online_final/final_result.json").read_text())
            assert audit["updates_completed_after_deadline"] == 0
            assert audit["updates_completed_after_sensor_eos"] == 0
            assert render["fixed_eval_mapping_excluded"]
            manifest["sensor_eos_audit"] = audit
            manifest["tracking"] = evaluate_tracking(
                out, spec["groundtruth"], run_env  # type: ignore[arg-type]
            )
            write_json(completion, manifest)
        else:
            failures += 1
        write_json(out / "run_manifest.json", manifest)
        state["sequences"][key] = manifest  # type: ignore[index]
        write_json(state_path, state)
        write_summary()
        print(
            f"QUEUE_END {key} status={manifest['status']} "
            f"elapsed_seconds={manifest['elapsed_seconds']:.1f}",
            flush=True,
        )

    state["finished_unix"] = time.time()
    state["failures"] = failures
    state["status"] = "complete" if failures == 0 else "complete_with_failures"
    write_json(state_path, state)
    write_summary()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
