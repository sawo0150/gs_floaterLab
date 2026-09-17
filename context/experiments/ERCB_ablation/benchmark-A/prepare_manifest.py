#!/usr/bin/env python3
"""Create the fixed low/mid/high-budget RR/ERCB benchmark-A manifest."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REPO = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom-exp77-budget-5070ti-repro")
PYTHON = "/home/wosas/miniconda3/envs/3dgs/bin/python"
DATA_ROOT = ROOT / "data/benchmarks/ercb_benchmark_A_replay_v2"
RESULT_ROOT = ROOT / "results/ERCB_ablation/benchmark-A_5070ti_exp03_low_budget"
BUDGETS = (15, 30, 60)
SEED = 0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform_schedule(source: Path, destination: Path, budget: int) -> int:
    payload = json.loads(source.read_text())
    mapping = payload["arrival_iteration_by_name"]
    if payload.get("iters_per_event") != 60 or payload.get("tail_iters") != 0:
        raise ValueError(f"unexpected source schedule: {source}")
    if not mapping or not all((int(value) - 1) % 60 == 0 for value in mapping.values()):
        raise ValueError(f"not an event60 schedule: {source}")
    transformed = {
        name: 1 + ((int(value) - 1) // 60) * budget for name, value in mapping.items()
    }
    total = max(transformed.values())
    output = {
        "arrival_iteration_by_name": transformed,
        "total_iterations": total,
        "source_schedule": str(source),
        "source_schedule_sha256": sha256(source),
        "updates_per_event": budget,
        "tail_iters": 0,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2) + "\n")
    return total


def main() -> None:
    inventory_path = HERE / "evidence/dataset_inventory.json"
    inventory = json.loads(inventory_path.read_text())
    schedules = HERE / "evidence/schedules"
    jobs = []
    for record in inventory["records"]:
        family, scene = record["family"], record["scene"]
        dataset = Path(record["dataset"])
        for budget in BUDGETS:
            schedule = schedules / family / f"{scene}_event{budget}.json"
            total = transform_schedule(dataset / "causal_arrivals.json", schedule, budget)
            checkpoints = sorted({max(1, total // 4), max(1, total // 2), total})
            for arm in ("rr", "window10_rr", "ercb"):
                scheduler = {
                    "rr": "causal_rr",
                    "window10_rr": "recent_interval_window_rr",
                    "ercb": "relative_floor_interval_softmax_rr",
                }[arm]
                scheduler_block_size = 10 if arm == "window10_rr" else 8
                output = RESULT_ROOT / family / scene / f"event{budget}" / f"{arm}_s{SEED}"
                argv = [
                    PYTHON,
                    str(ROOT / "context/experiments/exp77/run_training.py"),
                    "--repo", str(REPO), "--arm", arm, "--",
                    "-s", str(dataset), "-m", str(output), "-r", "4", "--eval",
                    "--iterations", str(total), "--test_iterations",
                    *[str(value) for value in checkpoints],
                    "--save_iterations", str(total),
                    "--view_schedule", str(schedule),
                    "--view_scheduler", scheduler,
                    "--scheduler_seed", str(SEED),
                    "--scheduler_beta", str(math.log(3.0)),
                    "--scheduler_block_size", str(scheduler_block_size),
                    "--position_lr_max_steps", str(total),
                    "--densify_until_iter", "0",
                    "--data_device", "cpu",
                    "--fixed_topology_step_before_report",
                    "--quiet", "--disable_viewer",
                ]
                jobs.append({
                    "family": family, "scene": scene, "budget": budget,
                    "seed": SEED, "arm": arm, "total_iterations": total,
                    "events": record["events"], "train_frames": record["train_frames"],
                    "heldout_frames": record["heldout_frames"],
                    "dataset": str(dataset), "schedule": str(schedule),
                    "output": str(output), "argv": argv, "state": "pending",
                })
    manifest = {
        "protocol": "benchmark-A_exp03_budget_sweep_full_rr_window10_rr_ercb",
        "state": "PREPARED_NOT_RUN",
        "device": "NVIDIA GeForce RTX 5070 Ti",
        "repo_head": subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True
        ).strip(),
        "implementation_sha256": {
            "train.py": sha256(REPO / "train.py"),
            "runtime/scheduler.py": sha256(REPO / "runtime/scheduler.py"),
            "exp77/run_training.py": sha256(ROOT / "context/experiments/exp77/run_training.py"),
        },
        "contract": {
            "updates_per_event": list(BUDGETS),
            "seed": SEED,
            "arms": [
                "causal_rr",
                "recent_interval_window_rr(window=10)",
                "relative_floor_interval_softmax_rr",
            ],
            "ercb": {"K": 8, "rho": 0.5, "gamma": "log(3)"},
            "window10_rr": {
                "window_intervals": 10,
                "active_pool": "union of frames in latest 10 non-empty keyframe intervals",
                "inner_policy": "causal random reshuffling",
            },
            "resolution": 4,
            "loss": "RGB-only",
            "fixed_topology": True,
            "tail_updates": 0,
            "heldout": "llffhold-8",
            "primary_metric": "paired final held-out PSNR (ERCB - RR)",
            "historical_tail_admission_semantics": True,
        },
        "unavailable": inventory["unavailable"],
        "jobs": jobs,
    }
    destination = HERE / "evidence/manifest.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{destination}: {len(jobs)} jobs, {len(jobs)//3} valid scene-budget groups")


if __name__ == "__main__":
    main()
