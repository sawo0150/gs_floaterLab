#!/usr/bin/env python3
"""K-sweep manifest: keyframe + (K-1) in-between frames per interval.

Same contract as prepare_manifest.py (benchmark-B datasets/schedules/budgets,
causal_rr, seed 0, densification enabled at stock 3DGS proportions of each
run's own budget). Only the candidate pool changes, via --eligible_names_file
pointing at build_k_pools.py output. K=1 and K=all are already covered by
prepare_manifest.py's kf_only / kf_dense arms.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import os as _os
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH_B = HERE.parent / "benchmark-B"
ROOT = HERE.parents[3]
REPO = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom-exp77-budget-5070ti-repro")
PYTHON = "/home/wosas/miniconda3/envs/3dgs/bin/python"
DATA_ROOT = ROOT / "data/benchmarks/ercb_benchmark_B_stride20"
RESULT_ROOT = ROOT / "results/ERCB_ablation/dense_supervision_densify"
SEED = 0
BUDGETS = tuple(int(v) for v in _os.environ.get('K_BUDGETS','15,30,60').split(','))
import os as _os
SCENES = tuple(tuple(x.split("/")) for x in _os.environ["K_SCENES"].split(",")) if _os.environ.get("K_SCENES") \
    else (("aria", "aria1253"), ("utmm", "square-1"), ("rpng", "table_01"))
K_VALUES = (4,)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    bench_manifest = json.loads((BENCH_B / "evidence/manifest.json").read_text())
    totals = {(j["family"], j["scene"], j["budget"]): j["total_iterations"]
              for j in bench_manifest["jobs"] if j["stride"] == 20 and j["arm"] == "rr"}
    pool_sizes = {(r["family"], r["scene"], r["budget"], r["k"]): r["pool_size"]
                  for r in json.loads((HERE / "evidence/k_pools/inventory.json").read_text())}
    jobs = []
    for family, scene in SCENES:
        dataset = DATA_ROOT / family / scene / "stride20"
        for budget in BUDGETS:
            total = totals[(family, scene, budget)]
            schedule = BENCH_B / "evidence/schedules" / family / f"{scene}_stride20_event{budget}.json"
            densify_from = max(100, total // 60)
            densify_until = max(densify_from + 100, total // 2)
            opacity_reset = max(500, total // 10)
            checkpoints = sorted({max(1, int(total * f)) for f in (0.1, 0.25, 0.5, 0.75)} | {total})
            for k in K_VALUES:
                eligible = HERE / "evidence/k_pools" / family / f"{scene}_event{budget}_k{k}.json"
                arm = f"k{k}"
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
                    "--eligible_names_file", str(eligible),
                    "--depth_l1_weight_init", "0", "--depth_l1_weight_final", "0",
                    "--data_device", "cpu", "--quiet", "--disable_viewer",
                ]
                jobs.append({
                    "family": family, "scene": scene, "budget": budget, "arm": arm, "k": k,
                    "seed": SEED, "total_iterations": total, "curve_iterations": checkpoints,
                    "pool_frames": pool_sizes[(family, scene, budget, k)],
                    "updates_per_pool_frame": round(
                        total / pool_sizes[(family, scene, budget, k)], 2),
                    "densify_from_iter": densify_from, "densify_until_iter": densify_until,
                    "opacity_reset_interval": opacity_reset,
                    "dataset": str(dataset), "schedule": str(schedule),
                    "eligible_names_file": str(eligible), "output": str(output),
                    "argv": argv, "state": "pending",
                })
    manifest = {
        "protocol": "ERCB_dense_supervision_per_interval_K_sweep",
        "state": "PREPARED_NOT_RUN", "device": "NVIDIA GeForce RTX 5070 Ti",
        "repo_head": subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip(),
        "implementation_sha256": {
            "train.py": sha256(REPO / "train.py"),
            "runtime/scheduler.py": sha256(REPO / "runtime/scheduler.py"),
            "exp77/run_training.py": sha256(ROOT / "context/experiments/exp77/run_training.py"),
        },
        "contract": {
            "pool": "per interval: the VIGS keyframe plus K-1 in-between frames chosen by "
                    "farthest-point-in-time sampling seeded with the keyframe",
            "k_values": list(K_VALUES),
            "k1_and_kall": "supplied by prepare_manifest.py's kf_only / kf_dense arms",
            "everything_else": "identical to prepare_manifest.py (benchmark-B schedules, "
                               "budgets, selector, seed, densification proportions, held-out)",
        },
        "jobs": jobs,
    }
    destination = HERE / "evidence/manifest_k.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{destination}: {len(jobs)} jobs")


if __name__ == "__main__":
    main()
