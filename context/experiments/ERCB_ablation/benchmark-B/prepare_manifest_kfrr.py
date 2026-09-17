#!/usr/bin/env python3
"""Add a keyframe-only causal RR arm to benchmark-B, as an isolated manifest.

Uses the SAME full-pool dataset/view_schedule as the rr/ercb arms (so arrival
timing, monotonicity, all_train_cameras and llffhold-8 held-out identity are
byte-identical to those runs) plus the new train.py --eligible_names_file
flag pointing at the keyframe-only name set (evidence/schedules_kfrr/*.json,
built by build_keyframe_only_schedules.py) -- causal_rr then never adds/draws
a camera outside that set, while total_iterations/checkpoints are unchanged.
Written to evidence/manifest_kfrr.json, and jobs land in kf_rr_s0 output
directories alongside the existing rr_s0/ercb_s0 directories, so this never
touches evidence/manifest.json and is safe to build while run_panel.py is
running that manifest (though actually launching run_panel_kfrr.py still
needs the GPU free, same as any other panel run).
"""

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
CONDITIONS = ((40, 15), (20, 15), (20, 30), (20, 60))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    dataset_inventory = json.loads((HERE / "evidence/dataset_inventory.json").read_text())
    pool_inventory = json.loads((HERE / "evidence/keyframe_pool_inventory.json").read_text())
    pool_by_key = {(r["family"], r["scene"]): r for r in pool_inventory["records"]}
    full_schedules = HERE / "evidence/schedules"
    kfrr_schedules = HERE / "evidence/schedules_kfrr"
    jobs = []
    for record in dataset_inventory["records"]:
        family, scene = record["family"], record["scene"]
        pool = pool_by_key[(family, scene)]
        for stride, budget in CONDITIONS:
            dataset = DATA_ROOT / family / scene / f"stride{stride}"
            schedule = full_schedules / family / f"{scene}_stride{stride}_event{budget}.json"
            eligible = kfrr_schedules / family / f"{scene}_stride{stride}_event{budget}.json"
            eligible_payload = json.loads(eligible.read_text())
            total = json.loads(schedule.read_text())["total_iterations"]
            if total != eligible_payload["total_iterations"]:
                raise ValueError(f"total_iterations mismatch: {family}/{scene} stride{stride} event{budget}")
            checkpoints = sorted({max(1, total // 4), max(1, total // 2), total})
            arm = "kf_rr"
            output = RESULT_ROOT / family / scene / f"stride{stride}" / f"event{budget}" / f"{arm}_s{SEED}"
            argv = [
                PYTHON, str(ROOT / "context/experiments/exp77/run_training.py"),
                "--repo", str(REPO), "--arm", "rr", "--",
                "-s", str(dataset), "-m", str(output), "-r", "4", "--eval",
                "--iterations", str(total), "--test_iterations",
                *[str(value) for value in checkpoints],
                "--save_iterations", str(total),
                "--view_schedule", str(schedule),
                "--view_scheduler", "causal_rr",
                "--eligible_names_file", str(eligible),
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
                "keyframe_only_pool_size": eligible_payload["keyframe_only_pool_size"],
                "full_pool_size": eligible_payload["full_pool_size"],
                "populated_events": eligible_payload["populated_events"],
                "dataset": str(dataset), "schedule": str(schedule), "eligible_names_file": str(eligible),
                "output": str(output), "argv": argv, "state": "pending",
            })
    manifest = {
        "protocol": "benchmark-B_stride20_keyframe_only_rr_arm",
        "state": "PREPARED_NOT_RUN", "device": "NVIDIA GeForce RTX 5070 Ti",
        "note": "isolated manifest; adds kf_rr arm alongside the existing rr/ercb manifest.json",
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
            "seed": SEED,
            "arm": "causal_rr over the full-pool schedule/dataset with "
                   "--eligible_names_file restricting admission to the "
                   "keyframe-only pool (train.py addition; arrival timing, "
                   "monotonicity, all_train_cameras and llffhold-8 held-out "
                   "identity are unchanged from the rr/ercb manifest, only "
                   "which arrived cameras enter the RR pool differs)",
            "resolution": 4, "loss": "RGB-only", "fixed_topology": True,
            "tail_updates": 0, "heldout": "llffhold-8",
        },
        "unavailable": dataset_inventory["unavailable"], "jobs": jobs,
    }
    destination = HERE / "evidence/manifest_kfrr.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{destination}: {len(jobs)} jobs across {len(dataset_inventory['records'])} scenes")


if __name__ == "__main__":
    main()
