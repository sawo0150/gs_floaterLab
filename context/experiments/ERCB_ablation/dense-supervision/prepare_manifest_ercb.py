#!/usr/bin/env python3
"""ERCB arm under the same protocol as the dense-supervision table.

Table A's `kf_dense` arm is already causal RR over the full arrived pool with
densification on. Adding the interval relative-floor ERCB selector over the
same pool, same budget, same seed and same schedule gives an ERCB-vs-random
comparison that shares Table A's seal exactly -- only the draw order differs.
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
BUDGET = 60


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    inventory = json.loads((BENCH_B / "evidence/dataset_inventory.json").read_text())
    bench = json.loads((BENCH_B / "evidence/manifest.json").read_text())
    totals = {(j["family"], j["scene"]): j["total_iterations"] for j in bench["jobs"]
              if j["stride"] == 20 and j["arm"] == "rr" and j["budget"] == BUDGET}
    jobs = []
    for record in inventory["records"]:
        family, scene = record["family"], record["scene"]
        total = totals[(family, scene)]
        dataset = DATA_ROOT / family / scene / "stride20"
        schedule = BENCH_B / "evidence/schedules" / family / f"{scene}_stride20_event{BUDGET}.json"
        densify_from = max(100, total // 60)
        densify_until = max(densify_from + 100, total // 2)
        opacity_reset = max(500, total // 10)
        checkpoints = sorted({max(1, int(total * f)) for f in (0.1, 0.25, 0.5, 0.75)} | {total})
        output = RESULT_ROOT / family / scene / f"event{BUDGET}" / f"ercb_s{SEED}"
        argv = [
            PYTHON, str(ROOT / "context/experiments/exp77/run_training.py"),
            "--repo", str(REPO), "--arm", "ercb", "--",
            "-s", str(dataset), "-m", str(output), "-r", "4", "--eval",
            "--iterations", str(total),
            "--test_iterations", *[str(v) for v in checkpoints],
            "--save_iterations", str(total),
            "--view_schedule", str(schedule),
            "--view_scheduler", "relative_floor_interval_softmax_rr",
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
        jobs.append({
            "family": family, "scene": scene, "budget": BUDGET, "arm": "ercb",
            "seed": SEED, "total_iterations": total, "curve_iterations": checkpoints,
            "densify_from_iter": densify_from, "densify_until_iter": densify_until,
            "opacity_reset_interval": opacity_reset,
            "dataset": str(dataset), "schedule": str(schedule),
            "eligible_names_file": None, "output": str(output),
            "argv": argv, "state": "pending",
        })
    manifest = {
        "protocol": "ERCB_vs_random_over_full_pool_with_densification",
        "state": "PREPARED_NOT_RUN", "device": "NVIDIA GeForce RTX 5070 Ti",
        "repo_head": subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip(),
        "implementation_sha256": {
            "train.py": sha256(REPO / "train.py"),
            "runtime/scheduler.py": sha256(REPO / "runtime/scheduler.py"),
            "exp77/run_training.py": sha256(ROOT / "context/experiments/exp77/run_training.py"),
        },
        "contract": {
            "compared_against": "the kf_dense arm of evidence/manifest.json "
                                "(causal RR over the same full pool)",
            "differs_only_in": "draw order (interval relative-floor ERCB, K=8, gamma=log 3)",
            "budget": f"{BUDGET} optimizer iterations per keyframe interval",
        },
        "jobs": jobs,
    }
    destination = HERE / "evidence/manifest_ercb.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{destination}: {len(jobs)} jobs")


if __name__ == "__main__":
    main()
