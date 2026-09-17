#!/usr/bin/env python3
"""exp87 manifest: incremental KF-only vs KF+dense supervision at a 30k budget.

Both arms share: dataset, init point cloud, causal arrival schedule, selector
(causal_rr), seed, resolution, loss (RGB-only), densification policy (stock
3DGS defaults), total optimizer updates, and the llffhold-8 held-out set that
neither arm ever trains on. The only difference is the candidate pool:
kf_only draws from VIGS keyframes only, dense_all draws from every causally
arrived train frame.

Unlike benchmark-A/B this run does NOT pass --fixed_topology_step_before_report
/ --densify_until_iter 0, so densification is active -- dense views can create
the Gaussians they need ("equal geometry editing rights", the condition under
which exp66 measured the batch effect). Final Gaussian counts therefore differ
between arms and are reported alongside PSNR.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom-exp77-budget-5070ti-repro")
PYTHON = "/home/wosas/miniconda3/envs/3dgs/bin/python"
DATA_ROOT = ROOT / "data/benchmarks/ercb_benchmark_B_stride20"
RESULT_ROOT = ROOT / "results/exp87_dense_vs_kf_incremental"
SEED = 0
CURVE = (1000, 2000, 3000, 5000, 7000, 10000, 15000, 20000, 25000)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    inventory = json.loads((HERE / "evidence/schedule_inventory.json").read_text())
    jobs = []
    for record in inventory["records"]:
        family, scene = record["family"], record["scene"]
        total = record["total_iterations"]
        dataset = DATA_ROOT / family / scene / f"stride{record['stride']}"
        checkpoints = sorted({i for i in CURVE if i < total} | {total})
        for arm, eligible in (("kf_only", record["eligible_kf"]), ("dense_all", None)):
            output = RESULT_ROOT / family / scene / f"{arm}_s{SEED}"
            argv = [
                PYTHON, str(ROOT / "context/experiments/exp77/run_training.py"),
                "--repo", str(REPO), "--arm", "rr", "--",
                "-s", str(dataset), "-m", str(output), "-r", "4", "--eval",
                "--iterations", str(total),
                "--test_iterations", *[str(v) for v in checkpoints],
                "--save_iterations", str(total),
                "--view_schedule", record["schedule"],
                "--view_scheduler", "causal_rr",
                "--scheduler_seed", str(SEED),
                "--position_lr_max_steps", str(total),
                "--depth_l1_weight_init", "0", "--depth_l1_weight_final", "0",
                "--data_device", "cpu", "--quiet", "--disable_viewer",
            ]
            if eligible:
                argv += ["--eligible_names_file", str(eligible)]
            jobs.append({
                "family": family, "scene": scene, "arm": arm, "seed": SEED,
                "total_iterations": total, "curve_iterations": checkpoints,
                "train_frames": record["train_frames"],
                "keyframe_frames": record["keyframe_frames"],
                "heldout_frames": record["heldout_frames"],
                "pool_frames": record["keyframe_frames"] if eligible else record["train_frames"],
                "updates_per_pool_frame": round(
                    total / (record["keyframe_frames"] if eligible else record["train_frames"]), 2),
                "dataset": str(dataset), "schedule": record["schedule"],
                "eligible_names_file": eligible, "output": str(output),
                "argv": argv, "state": "pending",
            })
    manifest = {
        "protocol": "exp87_incremental_kf_only_vs_kf_plus_dense_supervision",
        "state": "PREPARED_NOT_RUN", "device": "NVIDIA GeForce RTX 5070 Ti",
        "repo_head": subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip(),
        "implementation_sha256": {
            "train.py": sha256(REPO / "train.py"),
            "runtime/scheduler.py": sha256(REPO / "runtime/scheduler.py"),
            "exp77/run_training.py": sha256(ROOT / "context/experiments/exp77/run_training.py"),
        },
        "contract": {
            "question": "does dense (non-keyframe) supervision converge faster than "
                        "keyframe-only supervision under causal/incremental arrival?",
            "arms": ["kf_only (VIGS keyframes only)", "dense_all (every arrived train frame)"],
            "shared": ["dataset", "init point cloud", "causal arrival schedule",
                       "causal_rr selector", "seed", "resolution 4", "RGB-only loss",
                       "stock 3DGS densification (500-15000, interval 100)",
                       "total optimizer updates", "llffhold-8 held-out set"],
            "differs": ["candidate pool only"],
            "known_confound": "densification is active, so final Gaussian count differs "
                              "between arms; counts are reported with every number",
            "not_claimed": "strict online localization; poses/init come from a fixed "
                           "prior VIGS run replayed offline",
        },
        "jobs": jobs,
    }
    destination = HERE / "evidence/manifest.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{destination}: {len(jobs)} jobs")
    for j in jobs:
        print(f"  {j['family']}/{j['scene']:10s} {j['arm']:9s} T={j['total_iterations']} "
              f"pool={j['pool_frames']:5d} upd/frame={j['updates_per_pool_frame']}")


if __name__ == "__main__":
    main()
