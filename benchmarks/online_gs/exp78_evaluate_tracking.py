#!/usr/bin/env python3
"""Evaluate an explicitly named VIGS trajectory state with Sim(3) APE/recall."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


OFFICIAL = Path("/home/intern/VIGS-SLAM-official-exp78")
PYTHON_ENV = Path("/home/colin/miniconda3/envs/vigs-slam-5090")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--groundtruth", type=Path, required=True)
    parser.add_argument("--trajectory", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--recall-threshold-cm", type=float, default=10.0)
    args = parser.parse_args()

    output_json = args.output_json.resolve()
    artifact_stem = output_json.with_suffix("")
    command = [
        str(PYTHON_ENV / "bin/evo_ape"),
        "tum",
        "-vas",
        "--no_warnings",
        "--plot_mode",
        "xy",
        "--save_plot",
        str(artifact_stem.with_name(artifact_stem.name + "_ape_sim3.png")),
        "--save_results",
        str(artifact_stem.with_name(artifact_stem.name + "_ape_results.zip")),
        str(args.groundtruth.resolve()),
        str(args.trajectory.resolve()),
    ]
    result = subprocess.run(command, text=True, capture_output=True)
    log_path = artifact_stem.with_name(artifact_stem.name + "_evo_ape_sim3.txt")
    log_path.write_text(result.stdout + result.stderr)
    metrics: dict[str, object] = {
        "protocol": "exp78_sim3_tracking_state_v1",
        "state": args.state,
        "groundtruth": str(args.groundtruth.resolve()),
        "trajectory": str(args.trajectory.resolve()),
        "command": command,
        "returncode": result.returncode,
    }
    if result.returncode != 0:
        write_json(output_json, metrics)
        return result.returncode

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
        str(args.groundtruth.resolve()),
        str(args.trajectory.resolve()),
        thresh_cm=args.recall_threshold_cm,
    )
    metrics[f"recall_at_{args.recall_threshold_cm:g}cm_percent"] = float(recall)
    write_json(output_json, metrics)
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
