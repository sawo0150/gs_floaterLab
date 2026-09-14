#!/usr/bin/env python3
"""Prepare the fixed RTX 5070 Ti reproduction manifest; do not train."""

import hashlib
import json
import math
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
EXP = Path(__file__).resolve().parent
REPO = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom-exp77-budget-5070ti-repro")
RESULTS = ROOT / "results/ERCB_ablation/exp03_5070ti_budget_reproduction"
DATASETS = {
    "utmm_square1_full": ROOT / "data/benchmarks/ercb_vigs_replay_v2/utmm_square1_full",
    "rpng_table01_full": ROOT / "data/benchmarks/ercb_vigs_replay_v2/rpng_table01_full",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transformed_schedule(source, budget):
    payload = json.loads(source.read_text())
    mapping = payload["arrival_iteration_by_name"]
    if not all((value - 1) % 60 == 0 for value in mapping.values()):
        raise ValueError(f"source is not an event60 schedule: {source}")
    transformed = {
        name: 1 + ((value - 1) // 60) * budget for name, value in mapping.items()
    }
    total = max(transformed.values())
    return {
        "arrival_iteration_by_name": transformed,
        "total_iterations": total,
        "source_schedule": str(source),
        "source_schedule_sha256": sha256(source),
        "updates_per_event": budget,
        "tail_iters": 0,
    }


def main():
    EXP.mkdir(parents=True, exist_ok=True)
    schedules = EXP / "evidence/schedules"
    schedules.mkdir(parents=True, exist_ok=True)
    jobs = []
    for scene, dataset in DATASETS.items():
        metadata = json.loads((dataset / "vigs_replay_metadata.json").read_text())
        source = dataset / "causal_arrivals.json"
        if metadata["iters_per_event"] != 60 or metadata["tail_iters"] != 0:
            raise ValueError(f"unexpected source schedule metadata: {scene}")
        for budget in (15, 30, 60):
            schedule_payload = transformed_schedule(source, budget)
            schedule = schedules / f"{scene}_event{budget}.json"
            schedule.write_text(json.dumps(schedule_payload, indent=2) + "\n")
            seeds = (0, 1, 2) if budget in (15, 60) else (0,)
            for seed in seeds:
                arm_order = ("ercb", "rr") if seed == 1 else ("rr", "ercb")
                for arm in arm_order:
                    total = schedule_payload["total_iterations"]
                    checkpoints = sorted({max(1, total // 4), max(1, total // 2), total})
                    scheduler = "causal_rr" if arm == "rr" else "relative_floor_interval_softmax_rr"
                    output = RESULTS / scene / f"event{budget}" / f"{arm}_s{seed}"
                    argv = [
                        "/home/wosas/miniconda3/envs/3dgs/bin/python",
                        str(ROOT / "context/experiments/exp77/run_training.py"),
                        "--repo", str(REPO), "--arm", arm, "--",
                        "-s", str(dataset), "-m", str(output), "-r", "4", "--eval",
                        "--iterations", str(total), "--test_iterations",
                        *[str(value) for value in checkpoints],
                        "--save_iterations", str(total),
                        "--view_schedule", str(schedule),
                        "--view_scheduler", scheduler,
                        "--scheduler_seed", str(seed),
                        "--scheduler_beta", str(math.log(3.0)),
                        "--scheduler_block_size", "8",
                        "--position_lr_max_steps", str(total),
                        "--densify_until_iter", "0",
                        "--data_device", "cpu",
                        "--fixed_topology_step_before_report",
                        "--quiet", "--disable_viewer",
                    ]
                    jobs.append({
                        "scene": scene, "budget": budget, "seed": seed, "arm": arm,
                        "total_iterations": total, "dataset": str(dataset),
                        "schedule": str(schedule), "output": str(output), "argv": argv,
                    })
    manifest = {
        "protocol": "exp03_5070ti_exp77_budget_reproduction",
        "state": "PREPARED_NOT_RUN",
        "device": "NVIDIA GeForce RTX 5070 Ti",
        "repo_head": subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True
        ).strip(),
        "repo_patch": str(ROOT / "context/experiments/exp77/local_changes_da1dbda.patch"),
        "repo_files_sha256": {
            "train.py": sha256(REPO / "train.py"),
            "runtime/scheduler.py": sha256(REPO / "runtime/scheduler.py"),
            "runtime/packet_scheduler.py": sha256(REPO / "runtime/packet_scheduler.py"),
        },
        "contract": {
            "budgets_per_event": [15, 30, 60],
            "budget15_seeds": [0, 1, 2],
            "budget30_seeds": [0],
            "budget60_seeds": [0, 1, 2],
            "arms": ["causal_rr", "relative_floor_interval_softmax_rr"],
            "fixed_topology": True,
            "tail_updates": 0,
            "heldout": "llffhold-8",
            "primary_metric": "paired final held-out PSNR",
        },
        "jobs": jobs,
    }
    destination = EXP / "evidence/manifest.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n")
    print(destination)


if __name__ == "__main__":
    main()
