#!/usr/bin/env python3
"""3-scene pilot: per-interval farthest-point-in-time subsampled RR/ERCB.

Each KF interval admits at most `budget` frames (the same updates/event value
already used for the fixed-schedule rr/ercb/kf_rr panel -- since
total_iterations = 1 + (events-1)*budget, budget already IS each interval's
average training capacity), chosen by greedy farthest-point-in-time sampling
within the interval (build_fps_schedules.py). Intervals with <= budget frames
are kept whole. This replaces the dynamic work-credit admission (which had a
bracket-size confound: large dense brackets got starved of admission
entirely) with a static per-interval cap, so total_iterations/arrival
timing/monotonic order/llffhold-8 held-out identity stay byte-identical to
the existing rr/ercb/kf_rr fixed-schedule runs -- only which dense frames are
candidates changes. Uses --eligible_names_file only; no train.py changes.

Isolated manifest (evidence/manifest_fps_pilot.json). rr/ercb/kf_rr results
for these same 3 scenes/budgets are reused directly from manifest.json /
manifest_kfrr.json (no rerun) when comparing.
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
PILOT_SCENES = (("utmm", "square-1"), ("rpng", "table_01"), ("aria", "aria1253"))
BUDGETS = (15, 30, 60)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    main_manifest = json.loads((HERE / "evidence/manifest.json").read_text())
    job_by_key = {
        (j["family"], j["scene"], j["budget"], j["arm"]): j
        for j in main_manifest["jobs"] if j["stride"] == 20
    }
    jobs = []
    for family, scene in PILOT_SCENES:
        dataset = DATA_ROOT / family / scene / "stride20"
        for budget in BUDGETS:
            reference = job_by_key[(family, scene, budget, "rr")]
            total = reference["total_iterations"]
            checkpoints = sorted({max(1, total // 4), max(1, total // 2), total})
            full_schedule = HERE / "evidence/schedules" / family / f"{scene}_stride20_event{budget}.json"
            fps_schedule = HERE / "evidence/schedules_fps" / family / f"{scene}_stride20_event{budget}.json"
            fps_payload = json.loads(fps_schedule.read_text())
            for arm, scheduler in (
                ("fps_rr", "causal_rr"),
                ("fps_ercb", "relative_floor_interval_softmax_rr"),
            ):
                run_training_arm = "ercb" if scheduler == "relative_floor_interval_softmax_rr" else "rr"
                output = RESULT_ROOT / family / scene / "stride20" / f"event{budget}" / f"{arm}_s{SEED}"
                argv = [
                    PYTHON, str(ROOT / "context/experiments/exp77/run_training.py"),
                    "--repo", str(REPO), "--arm", run_training_arm, "--",
                    "-s", str(dataset), "-m", str(output), "-r", "4", "--eval",
                    "--iterations", str(total), "--test_iterations",
                    *[str(value) for value in checkpoints],
                    "--save_iterations", str(total),
                    "--view_schedule", str(full_schedule),
                    "--eligible_names_file", str(fps_schedule),
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
                    "family": family, "scene": scene, "budget": budget, "arm": arm,
                    "seed": SEED, "total_iterations": total,
                    "fps_pool_size": fps_payload["fps_pool_size"],
                    "full_pool_size": fps_payload["full_pool_size"],
                    "dataset": str(dataset), "output": str(output),
                    "argv": argv, "state": "pending",
                })
    manifest = {
        "protocol": "benchmark-B_fps_pilot_per_interval_farthest_point_subsample",
        "state": "PREPARED_NOT_RUN", "device": "NVIDIA GeForce RTX 5070 Ti",
        "note": "3-scene pilot; static per-interval FPS cap via --eligible_names_file, "
                "no train.py runtime changes. Isolated from manifest.json/manifest_kfrr.json.",
        "repo_head": subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True
        ).strip(),
        "implementation_sha256": {
            "train.py": sha256(REPO / "train.py"),
            "runtime/scheduler.py": sha256(REPO / "runtime/scheduler.py"),
            "exp77/run_training.py": sha256(ROOT / "context/experiments/exp77/run_training.py"),
        },
        "contract": {
            "per_interval_cap": "budget (updates/event), same value as the fixed-schedule panel",
            "subsample_rule": "greedy farthest-point-in-time within each KF interval; "
                               "intervals with <= budget frames kept whole",
            "arms": ["fps_rr (causal_rr)", "fps_ercb (relative_floor_interval_softmax_rr)"],
            "budgets": list(BUDGETS), "resolution": 4, "loss": "RGB-only",
            "fixed_topology": True, "heldout": "llffhold-8", "seed": SEED,
        },
        "jobs": jobs,
    }
    destination = HERE / "evidence/manifest_fps_pilot.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{destination}: {len(jobs)} jobs across {len(PILOT_SCENES)} scenes x {len(BUDGETS)} budgets")


if __name__ == "__main__":
    main()
