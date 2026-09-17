#!/usr/bin/env python3
"""Binary KF-only vs KF+dense across a widened per-interval update budget.

benchmark-B only ever ran 15/30/60 updates per keyframe interval, all of them
tight enough that each admitted view gets a handful of updates at most. This
extends the same causal replay upward (120/240) with just the two arms the
paper sentence needs, so the claim "using the frames between keyframes as
supervision converges faster under the same number of iterations" can be read
off a single binary table as a function of the budget.

Schedules are generated the same way benchmark-B generates its own: take the
raw event-60 causal arrival file and rescale the per-event budget. Everything
else (datasets, init, selector, seed, held-out, zero-tail, densification
proportions) matches prepare_manifest.py exactly.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH_B = HERE.parent / "benchmark-B"
ROOT = HERE.parents[3]
REPO = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom-exp77-budget-5070ti-repro")
PYTHON = "/home/wosas/miniconda3/envs/3dgs/bin/python"
DATA_ROOT = ROOT / "data/benchmarks/ercb_benchmark_B_stride20"
RESULT_ROOT = ROOT / "results/ERCB_ablation/dense_supervision_densify"
SEED = 0
BUDGETS = tuple(int(v) for v in __import__('os').environ.get('B_BUDGETS','120,240').split(','))
import os as _os
SCENES = tuple(tuple(x.split("/")) for x in _os.environ["B_SCENES"].split(",")) if _os.environ.get("B_SCENES") \
    else (("aria", "aria1253"), ("utmm", "square-1"), ("rpng", "table_01"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_schedule(family: str, scene: str, budget: int) -> tuple[Path, int]:
    causal = DATA_ROOT / family / scene / "stride20/causal_arrivals.json"
    payload = json.loads(causal.read_text())
    if payload.get("iters_per_event") != 60 or payload.get("tail_iters") != 0:
        raise ValueError(f"unexpected causal_arrivals.json: {causal}")
    converted = {name: 1 + ((int(value) - 1) // 60) * budget
                 for name, value in payload["arrival_iteration_by_name"].items()}
    total = max(converted.values())
    destination = HERE / "evidence/schedules_budget" / family / f"{scene}_event{budget}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({
        "arrival_iteration_by_name": converted, "total_iterations": total,
        "updates_per_event": budget, "events": payload["events"], "tail_iters": 0,
        "source_schedule": str(causal), "source_schedule_sha256": sha256(causal),
    }, indent=2) + "\n")
    return destination, total


def main() -> None:
    jobs = []
    for family, scene in SCENES:
        dataset = DATA_ROOT / family / scene / "stride20"
        kf_pool = BENCH_B / "evidence/schedules_kfrr" / family / f"{scene}_stride20_event15.json"
        for budget in BUDGETS:
            schedule, total = make_schedule(family, scene, budget)
            densify_from = max(100, total // 60)
            densify_until = max(densify_from + 100, total // 2)
            opacity_reset = max(500, total // 10)
            checkpoints = sorted({max(1, int(total * f)) for f in (0.1, 0.25, 0.5, 0.75)} | {total})
            for arm, eligible in (("kf_only", kf_pool), ("kf_dense", None)):
                output = RESULT_ROOT / family / scene / f"event{budget}" / f"{arm}_s{SEED}"
                argv = [
                    PYTHON, str(ROOT / "context/experiments/exp77/run_training.py"),
                    "--repo", str(REPO), "--arm", "rr", "--",
                    "-s", str(dataset), "-m", str(output), "-r", "4", "--eval",
                    "--iterations", str(total),
                    "--test_iterations", *[str(v) for v in checkpoints],
                    "--save_iterations", str(total),
                    "--view_schedule", str(schedule),
                    "--view_scheduler", "causal_rr",
                    "--scheduler_seed", str(SEED),
                    "--scheduler_beta", str(math.log(3.0)),
                    "--scheduler_block_size", "8",
                    "--position_lr_max_steps", str(total),
                    "--densify_from_iter", str(densify_from),
                    "--densify_until_iter", str(densify_until),
                    "--opacity_reset_interval", str(opacity_reset),
                    "--depth_l1_weight_init", "0", "--depth_l1_weight_final", "0",
                    "--data_device", "cpu", "--quiet", "--disable_viewer",
                ]
                if eligible:
                    argv += ["--eligible_names_file", str(eligible)]
                jobs.append({
                    "family": family, "scene": scene, "budget": budget, "arm": arm,
                    "seed": SEED, "total_iterations": total, "curve_iterations": checkpoints,
                    "densify_from_iter": densify_from, "densify_until_iter": densify_until,
                    "opacity_reset_interval": opacity_reset,
                    "dataset": str(dataset), "schedule": str(schedule),
                    "eligible_names_file": str(eligible) if eligible else None,
                    "output": str(output), "argv": argv, "state": "pending",
                })
    manifest = {
        "protocol": "ERCB_dense_supervision_budget_extension_120_240",
        "state": "PREPARED_NOT_RUN", "device": "NVIDIA GeForce RTX 5070 Ti",
        "repo_head": subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip(),
        "implementation_sha256": {
            "train.py": sha256(REPO / "train.py"),
            "runtime/scheduler.py": sha256(REPO / "runtime/scheduler.py"),
            "exp77/run_training.py": sha256(ROOT / "context/experiments/exp77/run_training.py"),
        },
        "contract": {
            "arms": ["kf_only", "kf_dense (every arrived frame)"],
            "budgets": list(BUDGETS),
            "everything_else": "identical to prepare_manifest.py / benchmark-B",
        },
        "jobs": jobs,
    }
    destination = HERE / "evidence/manifest_budget.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{destination}: {len(jobs)} jobs")
    for j in jobs:
        if j["arm"] == "kf_only":
            print(f"  {j['family']}/{j['scene']:10s} budget={j['budget']:3d} T={j['total_iterations']}")


if __name__ == "__main__":
    main()
