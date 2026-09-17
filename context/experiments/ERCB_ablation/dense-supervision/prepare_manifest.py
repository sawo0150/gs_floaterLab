#!/usr/bin/env python3
"""KF-only vs KF+dense supervision under the ERCB ablation's own streaming budget.

Consistency with the existing ERCB tables is the point: this reuses
benchmark-B's datasets, causal arrival schedules (stride20, event15/30/60 =
15/30/60 optimizer updates per VIGS keyframe interval), keyframe pools,
llffhold-8 held-out split, causal_rr selector, seed and resolution verbatim.

Exactly one thing differs from benchmark-B: densification is enabled, so the
map can grow the capacity that dense views ask for. Its schedule is expressed
as fixed fractions of each run's own budget (stock 3DGS proportions: densify
from 1/60, until 1/2, opacity reset every 1/10), identical for every scene and
both arms -- no scene-specific cutoff.

Arms:
  kf_only   candidate pool = VIGS keyframes only
  kf_dense  candidate pool = every causally arrived train frame (keyframes included)

benchmark-B's own rr (= kf_dense pool) and manifest_kfrr's kf (= kf_only pool)
runs supply the fixed-topology half of the 2x2 table for free.
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
BUDGETS = tuple(int(v) for v in __import__('os').environ.get('DS_BUDGETS','15,30,60').split(','))
PILOT_SCENES = (("aria", "aria1253"), ("utmm", "square-1"), ("rpng", "table_01"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    import sys
    every_scene = "--all" in sys.argv
    inventory = json.loads((BENCH_B / "evidence/dataset_inventory.json").read_text())
    scenes = [(r["family"], r["scene"]) for r in inventory["records"]]
    if not every_scene:
        scenes = [s for s in PILOT_SCENES if s in scenes]
    bench_manifest = json.loads((BENCH_B / "evidence/manifest.json").read_text())
    totals = {(j["family"], j["scene"], j["budget"]): j["total_iterations"]
              for j in bench_manifest["jobs"] if j["stride"] == 20 and j["arm"] == "rr"}

    jobs = []
    for family, scene in scenes:
        dataset = DATA_ROOT / family / scene / "stride20"
        for budget in BUDGETS:
            total = totals[(family, scene, budget)]
            schedule = BENCH_B / "evidence/schedules" / family / f"{scene}_stride20_event{budget}.json"
            kf_pool = BENCH_B / "evidence/schedules_kfrr" / family / f"{scene}_stride20_event{budget}.json"
            # stock 3DGS proportions rescaled to this run's own budget
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
                    "seed": SEED, "total_iterations": total,
                    "curve_iterations": checkpoints,
                    "densify_from_iter": densify_from, "densify_until_iter": densify_until,
                    "opacity_reset_interval": opacity_reset,
                    "dataset": str(dataset), "schedule": str(schedule),
                    "eligible_names_file": str(eligible) if eligible else None,
                    "output": str(output), "argv": argv, "state": "pending",
                })
    manifest = {
        "protocol": "ERCB_dense_supervision_kf_only_vs_kf_plus_dense_with_densification",
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
                "event budgets 15/30/60 updates per keyframe interval",
                "causal_rr selector", "seed 0", "resolution 4", "RGB-only loss",
                "llffhold-8 held-out (never trained by either arm)",
                "zero-tail (no updates after the last frame arrives)",
                "total optimizer updates per scene/budget",
            ],
            "single_change_vs_benchmark_B": "densification enabled; schedule set as fixed "
                                            "fractions of each run's own budget "
                                            "(from 1/60, until 1/2, opacity reset 1/10), "
                                            "identical across scenes and arms",
            "arms": ["kf_only (keyframes)", "kf_dense (keyframes + in-between frames)"],
            "not_claimed": "strict online localization; pose/init replayed from a fixed VIGS run",
        },
        "jobs": jobs,
    }
    destination = HERE / "evidence/manifest.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{destination}: {len(jobs)} jobs ({len(scenes)} scenes x {len(BUDGETS)} budgets x 2 arms)")


if __name__ == "__main__":
    main()
