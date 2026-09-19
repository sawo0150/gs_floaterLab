#!/usr/bin/env python3
"""Budget-60 KF-only vs KF+dense, re-run with a dense evaluation grid.

Identical to prepare_manifest.py in every training-relevant respect (same
benchmark-B datasets, causal arrival schedules at 60 optimizer updates per
VIGS keyframe interval, causal_rr, seed 0, -r 4, densification proportions,
llffhold-8 held-out, zero-tail, same total iterations per scene). The only
change is `--test_iterations`: 24 checkpoints instead of 5, so the held-out
curve can be read as a convergence curve rather than a single endpoint.
Evaluation runs under no_grad and does not touch optimizer state, so the
final numbers must reproduce evidence/manifest.json exactly -- which doubles
as a determinism check.

Results go to a separate root so the table runs stay untouched.
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
RESULT_ROOT = ROOT / "results/ERCB_ablation/dense_supervision_curve"
SEED = 0
BUDGET = 60
FRACTIONS = (0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35,
             0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90,
             0.95, 1.00)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    base = json.loads((HERE / "evidence/manifest.json").read_text())
    jobs = []
    for source in base["jobs"]:
        if source["budget"] != BUDGET:
            continue
        family, scene, arm = source["family"], source["scene"], source["arm"]
        total = source["total_iterations"]
        checkpoints = sorted({max(1, int(total * f)) for f in FRACTIONS} | {total})
        output = RESULT_ROOT / family / scene / f"event{BUDGET}" / f"{arm}_s{SEED}"
        argv = list(source["argv"])
        # replace -m and --test_iterations, leave everything else byte-identical
        argv[argv.index("-m") + 1] = str(output)
        start = argv.index("--test_iterations")
        stop = start + 1
        while stop < len(argv) and not argv[stop].startswith("--"):
            stop += 1
        argv[start:stop] = ["--test_iterations"] + [str(v) for v in checkpoints]
        jobs.append({**{k: v for k, v in source.items()
                        if k not in ("state", "returncode", "wall_seconds", "error")},
                     "curve_iterations": checkpoints, "output": str(output),
                     "argv": argv, "state": "pending",
                     "reference_run": source["output"]})
    manifest = {
        "protocol": "ERCB_dense_supervision_budget60_convergence_curve",
        "state": "PREPARED_NOT_RUN", "device": "NVIDIA GeForce RTX 5070 Ti",
        "repo_head": subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip(),
        "implementation_sha256": {
            "train.py": sha256(REPO / "train.py"),
            "runtime/scheduler.py": sha256(REPO / "runtime/scheduler.py"),
            "exp77/run_training.py": sha256(ROOT / "context/experiments/exp77/run_training.py"),
        },
        "contract": {
            "identical_to": "evidence/manifest.json (budget 60, 19 scenes x 2 arms)",
            "single_change": "--test_iterations grid widened from 5 to 24 checkpoints",
            "checkpoint_fractions": list(FRACTIONS),
            "determinism_check": "final-iteration test PSNR must match the reference run",
        },
        "jobs": jobs,
    }
    destination = HERE / "evidence/manifest_curve.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{destination}: {len(jobs)} jobs, {len(FRACTIONS)} checkpoint fractions")


if __name__ == "__main__":
    main()
