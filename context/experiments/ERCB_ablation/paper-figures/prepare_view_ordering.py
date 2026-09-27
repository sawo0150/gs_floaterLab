#!/usr/bin/env python3
"""View-ordering grid (random reshuffling vs ERCB) with densification enabled.

benchmark-B already has this grid at 15/30/60 updates per keyframe interval,
but under fixed topology (densification off, Gaussian count pinned to the init
point cloud). The supervision-source table runs with densification on, so the
two cannot sit in the same paper without a regime mismatch. This prepares the
same grid in the densify-on regime, at 24 evaluation checkpoints, so Phase 2
can pick whichever regime produces the better map -- by held-out PSNR, not by
which one flatters ERCB.

Everything except the selector is inherited from benchmark-B verbatim:
datasets, init point clouds, causal arrival schedules, per-interval budgets,
seed, resolution, RGB-only loss, llffhold-8 held-out, zero-tail, and the total
optimizer step count per scene and budget. Densification follows the same fixed
fractions of each run's own budget used by the supervision-source runs.

rr@60 already exists as the dense-supervision curve run; it is emitted pointing
at that output so the runner skips it rather than duplicating 19 trainings.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH_B = HERE.parent / "benchmark-B"
DENSE = HERE.parent / "dense-supervision"
ROOT = HERE.parents[3]
REPO = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom-exp77-budget-5070ti-repro")
PYTHON = "/home/wosas/miniconda3/envs/3dgs/bin/python"
DATA_ROOT = ROOT / "data/benchmarks/ercb_benchmark_B_stride20"
RESULT_ROOT = ROOT / "results/ERCB_ablation/view_ordering_densify"
CURVE_ROOT = ROOT / "results/ERCB_ablation/dense_supervision_curve"
SEED = 0
BUDGETS = (15, 30, 60)
FRACTIONS = (0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35,
             0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90,
             0.95, 1.00)
SELECTORS = {
    "rr": ("causal_rr", "rr"),
    "ercb": ("relative_floor_interval_softmax_rr", "ercb"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    inventory = json.loads((BENCH_B / "evidence/dataset_inventory.json").read_text())
    scenes = [(r["family"], r["scene"]) for r in inventory["records"]]
    bench = json.loads((BENCH_B / "evidence/manifest.json").read_text())
    totals = {(j["family"], j["scene"], j["budget"]): j["total_iterations"]
              for j in bench["jobs"] if j["stride"] == 20 and j["arm"] == "rr"}

    jobs = []
    for budget in BUDGETS:
        for arm, (scheduler, run_arm) in SELECTORS.items():
            for family, scene in scenes:
                total = totals[(family, scene, budget)]
                dataset = DATA_ROOT / family / scene / "stride20"
                schedule = (BENCH_B / "evidence/schedules" / family /
                            f"{scene}_stride20_event{budget}.json")
                densify_from = max(100, total // 60)
                densify_until = max(densify_from + 100, total // 2)
                opacity_reset = max(500, total // 10)
                checkpoints = sorted({max(1, int(total * f)) for f in FRACTIONS} | {total})
                reuse = (arm == "rr" and budget == 60)
                output = (CURVE_ROOT / family / scene / "event60/kf_dense_s0" if reuse
                          else RESULT_ROOT / family / scene / f"event{budget}" / f"{arm}_s{SEED}")
                argv = [
                    PYTHON, str(ROOT / "context/experiments/exp77/run_training.py"),
                    "--repo", str(REPO), "--arm", run_arm, "--",
                    "-s", str(dataset), "-m", str(output), "-r", "4", "--eval",
                    "--iterations", str(total),
                    "--test_iterations", *[str(v) for v in checkpoints],
                    "--save_iterations", str(total),
                    "--view_schedule", str(schedule),
                    "--view_scheduler", scheduler,
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
                    "family": family, "scene": scene, "budget": budget, "arm": arm,
                    "seed": SEED, "total_iterations": total, "curve_iterations": checkpoints,
                    "densify_from_iter": densify_from, "densify_until_iter": densify_until,
                    "opacity_reset_interval": opacity_reset,
                    "dataset": str(dataset), "schedule": str(schedule),
                    "reused_from_dense_supervision": reuse,
                    "output": str(output), "argv": argv, "state": "pending",
                })
    manifest = {
        "protocol": "ERCB_view_ordering_rr_vs_ercb_densify_on_15_30_60",
        "state": "PREPARED_NOT_RUN", "device": "NVIDIA GeForce RTX 5070 Ti",
        "repo_head": subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip(),
        "implementation_sha256": {
            "train.py": sha256(REPO / "train.py"),
            "runtime/scheduler.py": sha256(REPO / "runtime/scheduler.py"),
            "exp77/run_training.py": sha256(ROOT / "context/experiments/exp77/run_training.py"),
        },
        "contract": {
            "inherited_from_benchmark_B": [
                "stride20 datasets and init point clouds", "causal arrival schedules",
                "budgets 15/30/60 updates per keyframe interval", "seed 0", "resolution 4",
                "RGB-only loss", "llffhold-8 held-out", "zero-tail",
                "total optimizer steps per scene and budget",
            ],
            "differs_from_benchmark_B": "densification enabled (same fixed fractions of each "
                                        "run's budget as the supervision-source runs); "
                                        "24 evaluation checkpoints instead of 5",
            "arms": ["rr (causal_rr)", "ercb (relative_floor_interval_softmax_rr, K=8, gamma=log 3)"],
            "regime_choice_rule": "Phase 2 picks the regime with the higher held-out PSNR, "
                                  "never the one with the larger ERCB margin",
        },
        "jobs": jobs,
    }
    destination = HERE / "evidence/manifest_view_ordering.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n")
    reused = sum(j["reused_from_dense_supervision"] for j in jobs)
    print(f"{destination}: {len(jobs)} jobs ({reused} reuse existing runs, "
          f"{len(jobs)-reused} to train)")


if __name__ == "__main__":
    main()
