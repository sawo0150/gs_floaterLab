#!/usr/bin/env python3
"""Create the benchmark-B stride20 RR/ERCB budget manifest."""

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
DATA_ROOT = ROOT / "data/benchmarks/ercb_benchmark_B_stride20"
RESULT_ROOT = ROOT / "results/ERCB_ablation/benchmark-B_5070ti_stride20"
SEED = 0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def transform(source: Path, destination: Path, budget: int) -> int:
    payload = json.loads(source.read_text())
    mapping = payload["arrival_iteration_by_name"]
    if payload.get("iters_per_event") != 60 or payload.get("tail_iters") != 0:
        raise ValueError(f"unexpected source schedule: {source}")
    if not mapping or not all((int(value) - 1) % 60 == 0 for value in mapping.values()):
        raise ValueError(f"not an event60 schedule: {source}")
    converted = {
        name: 1 + ((int(value) - 1) // 60) * budget for name, value in mapping.items()
    }
    total = max(converted.values())
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({
        "arrival_iteration_by_name": converted,
        "total_iterations": total,
        "source_schedule": str(source),
        "source_schedule_sha256": sha256(source),
        "updates_per_event": budget,
        "tail_iters": 0,
    }, indent=2) + "\n")
    return total


def main() -> None:
    inventory = json.loads((HERE / "evidence/dataset_inventory.json").read_text())
    schedules = HERE / "evidence/schedules"
    jobs = []
    for record in inventory["records"]:
        family, scene = record["family"], record["scene"]
        # stride20 is the primary low/mid/high panel.  The same-run stride40
        # event15 bridge is retained so B-vs-A source-run drift cannot masquerade
        # as an initialization-density effect.
        conditions = [(40, 15), (20, 15), (20, 30), (20, 60)]
        for stride, budget in conditions:
            dataset = DATA_ROOT / family / scene / f"stride{stride}"
            schedule = schedules / family / f"{scene}_stride{stride}_event{budget}.json"
            total = transform(dataset / "causal_arrivals.json", schedule, budget)
            checkpoints = sorted({max(1, total // 4), max(1, total // 2), total})
            for arm in ("rr", "ercb"):
                scheduler = "causal_rr" if arm == "rr" else "relative_floor_interval_softmax_rr"
                output = RESULT_ROOT / family / scene / f"stride{stride}" / f"event{budget}" / f"{arm}_s{SEED}"
                argv = [
                    PYTHON, str(ROOT / "context/experiments/exp77/run_training.py"),
                    "--repo", str(REPO), "--arm", arm, "--",
                    "-s", str(dataset), "-m", str(output), "-r", "4", "--eval",
                    "--iterations", str(total), "--test_iterations",
                    *[str(value) for value in checkpoints],
                    "--save_iterations", str(total),
                    "--view_schedule", str(schedule),
                    "--view_scheduler", scheduler,
                    "--scheduler_seed", str(SEED),
                    "--scheduler_beta", str(math.log(3.0)),
                    "--scheduler_block_size", "8",
                    "--position_lr_max_steps", str(total),
                    "--densify_until_iter", "0",
                    "--depth_l1_weight_init", "0", "--depth_l1_weight_final", "0",
                    "--data_device", "cpu", "--fixed_topology_step_before_report",
                    "--quiet", "--disable_viewer",
                ]
                jobs.append({
                    "family": family, "scene": scene, "stride": stride,
                    "budget": budget, "arm": arm, "seed": SEED,
                    "total_iterations": total, "events": record["events"],
                    "train_frames": record["train_frames"],
                    "heldout_frames": record["heldout_frames"],
                    "dataset": str(dataset), "schedule": str(schedule),
                    "output": str(output), "argv": argv, "state": "pending",
                })
    manifest = {
        "protocol": "benchmark-B_stride20_low_mid_high_rr_ercb_with_stride40_low_bridge",
        "state": "PREPARED_NOT_RUN", "device": "NVIDIA GeForce RTX 5070 Ti",
        "repo_head": subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True
        ).strip(),
        "implementation_sha256": {
            "train.py": sha256(REPO / "train.py"),
            "runtime/scheduler.py": sha256(REPO / "runtime/scheduler.py"),
            "exp77/run_training.py": sha256(ROOT / "context/experiments/exp77/run_training.py"),
        },
        "contract": {
            "primary_density": "stride20", "primary_budgets": [15, 30, 60],
            "paired_bridge": "stride40 event15 from the same VIGS source run",
            "seed": SEED, "arms": ["causal_rr", "relative_floor_interval_softmax_rr"],
            "ercb": {"K": 8, "rho": 0.5, "gamma": "log(3)"},
            "resolution": 4, "loss": "RGB-only", "fixed_topology": True,
            "tail_updates": 0, "heldout": "llffhold-8",
        },
        "unavailable": inventory["unavailable"], "jobs": jobs,
    }
    destination = HERE / "evidence/manifest.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{destination}: {len(jobs)} jobs across {len(inventory['records'])} scenes")


if __name__ == "__main__":
    main()
