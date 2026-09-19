#!/usr/bin/env python3
"""B-track v2.1: fail-closed normalized ERCB versus official vanilla.

Exp90 found ~4.8 dB first-evaluation errors on an unchanged saved PLY.  Both
arms therefore use the same post-map cooldown and two independent evaluations.
Any discrepancy stops the panel; this runner never chooses the better score.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import run_exp88_normalized_metric_v2 as v2


base = v2.base
ROOT = base.WORKSPACE / "results/experiments/exp91_normalized_metric_v2_reliable"
DOCS = (
    base.WORKSPACE / "context/experiments/benchmark_custom"
    / "metric_benchmark_v2_reliable_20260917"
)
COOLDOWN_SECONDS = 15
PSNR_TOLERANCE_DB = 0.01
SSIM_TOLERANCE = 0.001
LPIPS_TOLERANCE = 0.001
SOURCE_PATHS = (
    *v2.SOURCE_PATHS,
    base.PAPER_ROOT / "vigs/gaussian/renderer/__init__.py",
    base.PAPER_ROOT / "vigs/gaussian/utils/camera_utils.py",
    base.PAPER_ROOT / "vigs/gaussian/scene/gaussian_model.py",
    base.BUILT_THIRDPARTY_ROOT / "thirdparty/diff-gaussian-rasterization"
    / "diff_gaussian_rasterization/__init__.py",
    base.BUILT_THIRDPARTY_ROOT / "thirdparty/diff-gaussian-rasterization"
    / "diff_gaussian_rasterization/_C.cpython-311-x86_64-linux-gnu.so",
    Path(__file__),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_source_lock() -> None:
    lock = ROOT / "source_lock.json"
    current = {str(path): sha256(path) for path in SOURCE_PATHS}
    if lock.exists():
        if v2.read_json(lock)["sha256"] != current:
            raise RuntimeError("v2.1 source changed after panel start; do not mix results")
    else:
        v2.write_json(lock, {"protocol": "exp91_metric_v2_reliable", "sha256": current})


def scene_paths(row: dict) -> dict[str, Path]:
    paths = v2.scene_paths(row)
    local = ROOT / row["dataset"] / row["scene"]
    paths.update({
        "candidate": local / "normalized_variance_s0",
        "vanilla": local / "native_vanilla_render_matched_s0",
        "pair": local / "pair_verification.json",
        "gate": local / "quality_gate.json",
    })
    return paths


def input_hashes(run: Path, fixed_manifest: Path) -> dict[str, str]:
    paths = {
        "ply": run / "3dgs_before_final.ply",
        "full_trajectory": run / "traj_full_beforeBA.txt",
        "kf_trajectory": run / "traj_kf_beforeBA.txt",
        "mapped_uids": run / "mapped_uids.json",
        "fixed_manifest": fixed_manifest,
    }
    return {name: sha256(path) for name, path in paths.items()}


def run_evaluation_twice(run: Path, dataset: str, scene: str, fixed_manifest: Path) -> dict:
    report_path = run / "evaluation_consistency.json"
    first = run / "psnr/strict_fixed_manifest/final_result.json"
    second = run / "psnr/strict_fixed_manifest_repeat/final_result.json"
    before = input_hashes(run, fixed_manifest)
    if not first.exists():
        v2.gpu_idle()
        time.sleep(COOLDOWN_SECONDS)
        v2.gpu_idle()
        command = base.evaluation_command(run, dataset, scene)
        v2.run_to_file(command, run / "evaluation.log", custom=True)
    if not second.exists():
        v2.gpu_idle()
        command = base.evaluation_command(run, dataset, scene)
        command[command.index("--result-subdir") + 1] = "strict_fixed_manifest_repeat"
        v2.run_to_file(command, run / "evaluation_repeat.log", custom=True)
    after = input_hashes(run, fixed_manifest)
    one, two = v2.read_json(first), v2.read_json(second)
    rows_one, rows_two = one["per_view"], two["per_view"]
    same_views = (
        len(rows_one) == len(rows_two)
        and all(
            a["frame_index"] == b["frame_index"]
            and a["uid"] == b["uid"]
            and a["predeclared_fixed_manifest_split"] == b["predeclared_fixed_manifest_split"]
            for a, b in zip(rows_one, rows_two)
        )
    )
    max_diff = {
        key: max((abs(a[key] - b[key]) for a, b in zip(rows_one, rows_two)), default=float("inf"))
        for key in ("psnr", "ssim", "lpips")
    }
    fixed_one = one["predeclared_fixed_manifest_posthoc"]
    fixed_two = two["predeclared_fixed_manifest_posthoc"]
    checks = {
        "unchanged_inputs": before == after,
        "same_views": same_views,
        "same_gaussian_count": one["gaussians"] == two["gaussians"],
        "same_fixed_view_count": fixed_one["view_count"] == fixed_two["view_count"],
        "psnr_agrees": max_diff["psnr"] <= PSNR_TOLERANCE_DB,
        "ssim_agrees": max_diff["ssim"] <= SSIM_TOLERANCE,
        "lpips_agrees": max_diff["lpips"] <= LPIPS_TOLERANCE,
    }
    report = {
        "protocol": "saved_map_independent_double_evaluation_v1",
        "cooldown_seconds": COOLDOWN_SECONDS,
        "input_sha256": before,
        "checks": checks,
        "max_abs_per_view_difference": max_diff,
        "fixed_psnr_first": fixed_one["mean_psnr"],
        "fixed_psnr_second": fixed_two["mean_psnr"],
        "pass": all(checks.values()),
    }
    v2.write_json(report_path, report)
    if not report["pass"]:
        raise RuntimeError(f"saved-map evaluation disagreement; stop: {run}")
    return report


def run_mapper(arm: str, dataset: str, scene: str, paths: dict[str, Path]) -> None:
    run = paths[arm]
    if (run / "mapping_replay_runtime.json").exists():
        return
    if run.exists():
        raise FileExistsError(f"incomplete run exists; inspect before retry: {run}")
    v2.gpu_idle()
    command = base.mapping_command(arm, dataset, scene, ROOT)
    command[command.index("--output") + 1] = str(run)
    if arm == "candidate":
        command.extend(("--ercb-selection-potential", "normalized_variance"))
    else:
        command[command.index("--reference-service-runtime") + 1] = str(
            paths["candidate"] / "mapping_replay_runtime.json"
        )
    v2.write_json(run / "mapping_command.json", command)
    v2.run_to_file(command, run / "mapping.log", custom=(arm == "candidate"))


def run_one(row: dict) -> dict:
    paths = scene_paths(row)
    v2.preflight(row, paths)
    check_source_lock()
    dataset, scene = row["dataset"], row["scene"]
    run_mapper("candidate", dataset, scene, paths)
    candidate_eval = run_evaluation_twice(
        paths["candidate"], dataset, scene, paths["fixed_manifest"]
    )
    gate = v2.quality_gate(row, paths)
    print(
        f"{dataset}/{scene}: normalized {gate['normalized_psnr']:.4f}, "
        f"R4 {gate['historical_r4_psnr']:.4f}, "
        f"double-eval={candidate_eval['pass']}, stop={gate['stop']}", flush=True,
    )
    if gate["stop"]:
        raise RuntimeError(f"predeclared R4 quality/fairness gate stopped at {dataset}/{scene}")
    run_mapper("vanilla", dataset, scene, paths)
    vanilla_eval = run_evaluation_twice(
        paths["vanilla"], dataset, scene, paths["fixed_manifest"]
    )
    if not paths["pair"].exists():
        command = [
            str(base.PYTHON_ENV / "bin/python"), str(base.RENDER_VERIFIER),
            "--d1-run", str(paths["candidate"]),
            "--vanilla-run", str(paths["vanilla"]),
            "--output", str(paths["pair"]),
        ]
        subprocess.run(command, cwd=base.WORKSPACE, check=True, stdout=subprocess.DEVNULL)
    pair = v2.read_json(paths["pair"])
    if not pair.get("valid"):
        raise RuntimeError(f"render-matched pair verification failed: {dataset}/{scene}")
    result = {
        "dataset": dataset, "scene": scene,
        "normalized_psnr": pair["result"]["d1"]["psnr"],
        "vanilla_psnr": pair["result"]["vanilla"]["psnr"],
        "delta_psnr": pair["result"]["d1_minus_vanilla"]["psnr"],
        "normalized_renders": pair["result"]["d1"]["renders"],
        "vanilla_renders": pair["result"]["vanilla"]["renders"],
        "normalized_adam": pair["result"]["d1"]["optimizer_steps"],
        "vanilla_adam": pair["result"]["vanilla"]["optimizer_steps"],
        "normalized_gaussians": pair["result"]["d1"]["gaussians"],
        "vanilla_gaussians": pair["result"]["vanilla"]["gaussians"],
        "double_evaluation_pass": candidate_eval["pass"] and vanilla_eval["pass"],
        "fairness_pass": pair["valid"],
    }
    v2.write_json(paths["candidate"].parent / "pair_result.json", result)
    print(f"{dataset}/{scene}: normalized−vanilla {result['delta_psnr']:+.4f} dB", flush=True)
    return result


def write_summary(rows: list[dict]) -> None:
    lines = [
        "# Metric benchmark v2.1 — normalized ERCB vs official vanilla",
        "",
        "Predeclared valid inventory: 17 scenes; UTMM slow-straight-1 tracker-ineligible N/A.",
        "Both arms: same frozen tracker, zero-tail, render-matched B-track, 15 s",
        "post-map cooldown and two independent saved-map evaluations. Any >0.01 dB",
        "per-view PSNR disagreement stops the panel; no score is selected by rank.",
        "",
        "| Dataset | Scene | Normalized PSNR | Vanilla PSNR | ΔPSNR | Renders N/V | Adam N/V | GS N/V | Eval/Fairness |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    completed = []
    for row in rows:
        path = ROOT / row["dataset"] / row["scene"] / "pair_result.json"
        if not path.exists():
            lines.append(f"| {row['dataset']} | {row['scene']} | — | — | — | — | — | — | PENDING |")
            continue
        x = v2.read_json(path)
        completed.append(x)
        lines.append(
            f"| {x['dataset']} | {x['scene']} | {x['normalized_psnr']:.4f} | "
            f"{x['vanilla_psnr']:.4f} | {x['delta_psnr']:+.4f} | "
            f"{x['normalized_renders']}/{x['vanilla_renders']} | "
            f"{x['normalized_adam']}/{x['vanilla_adam']} | "
            f"{x['normalized_gaussians']}/{x['vanilla_gaussians']} | "
            f"{'PASS' if x['double_evaluation_pass'] and x['fairness_pass'] else 'FAIL'} |"
        )
    lines.extend(["", f"Completed formal pairs: **{len(completed)}/17**."])
    if len(completed) == 17:
        mean = sum(x["delta_psnr"] for x in completed) / 17
        wins = sum(x["delta_psnr"] > 0 for x in completed)
        valid = all(x["double_evaluation_pass"] and x["fairness_pass"] for x in completed)
        passed = mean >= 0.5 and wins >= 9 and valid
        lines.extend([
            f"Scene-arithmetic mean ΔPSNR: **{mean:+.4f} dB**; wins **{wins}/17**.",
            f"Predeclared minimum acceptance: **{'PASS' if passed else 'FAIL'}** "
            "(mean ≥+0.5 dB, strict majority positive, all fairness PASS).",
            f"Historical R4 stretch target 17/17 and +1.2609 dB: "
            f"**{'PASS' if wins == 17 and mean >= 1.2609 else 'FAIL'}**.",
        ])
    else:
        lines.append("No all-scene acceptance claim until all 17 pairs complete.")
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    global ROOT, DOCS
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run-one", "run-all"))
    parser.add_argument("--dataset", choices=("rpng", "utmm", "aria"))
    parser.add_argument("--scene")
    parser.add_argument(
        "--root",
        type=Path,
        help=(
            "fresh output root; omit only when intentionally resuming the "
            "runner-defined root"
        ),
    )
    parser.add_argument(
        "--docs",
        type=Path,
        help="summary output directory paired with --root",
    )
    args = parser.parse_args()
    if (args.root is None) != (args.docs is None):
        parser.error("--root and --docs must be provided together")
    if args.root is not None:
        ROOT = args.root.resolve()
    if args.docs is not None:
        DOCS = args.docs.resolve()
    rows = v2.install_inventory()
    if args.action == "preflight":
        for row in rows:
            v2.preflight(row, scene_paths(row))
        check_source_lock()
        print(f"v2.1 preflight PASS: {len(rows)} valid scenes; evaluator double-pass")
        return 0
    if args.action == "run-one":
        rows_to_run = [
            row for row in rows
            if (row["dataset"], row["scene"]) == (args.dataset, args.scene)
        ]
        if len(rows_to_run) != 1:
            raise ValueError("run-one requires one valid --dataset/--scene")
    else:
        rows_to_run = rows
    try:
        for row in rows_to_run:
            run_one(row)
    finally:
        write_summary(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
