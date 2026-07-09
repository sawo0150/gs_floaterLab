#!/usr/bin/env python3
"""Read PSNR from TFEvents for all plateau experiments."""
import glob, sys
from pathlib import Path

try:
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
except ImportError:
    print("Run with: conda run -n 3dgs python scripts/read_psnr.py")
    sys.exit(1)

RESULTS = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments")

EXPS = [
    ("exp_orb_baseline",     "Baseline (no plateau)"),
    ("exp15_orb_spherical",  "exp15 Spherical plateau"),
    ("exp16_orb_ellipsoidal","exp16 Ellipsoidal plateau"),
    ("exp17_orb_metric3d",   "exp17 Metric3D monodepth"),
    ("exp18_orb_depthpro",   "exp18 Depth Pro monodepth"),
    ("exp19_mps_depthpro",   "exp19 MPS depthpro base"),
    ("exp20_mps_scheduled",  "exp20 MPS lambda sched"),
    ("exp21_mps_opacity_weighted", "exp21 MPS opacity wt"),
    ("exp22_mps_exploss",    "exp22 MPS exp loss"),
    ("exp23_mps_adaptive_prune", "exp23 MPS adaptive prune"),
    ("exp24_mps_exp_and_prune",  "exp24 MPS exp+prune"),
    ("exp25_mps_tau_enlarged",   "exp25 MPS tau enlarged"),
    ("exp26_mps_lambda1",    "exp26 MPS lambda1"),
]

PSNR_TAG = "train/loss_viewpoint - psnr"

print(f"\n{'Experiment':<30} {'PSNR@7k':>10} {'PSNR@30k':>10}")
print("-" * 55)

for prefix, label in EXPS:
    dirs = sorted(RESULTS.glob(f"{prefix}_*"), key=lambda p: p.name)
    # only dirs (not .log files), take most recent
    dirs = [d for d in dirs if d.is_dir()]
    if not dirs:
        print(f"{label:<30} {'N/A':>10} {'N/A':>10}")
        continue

    exp_dir = dirs[-1]
    tf_files = list(exp_dir.glob("events.out.tfevents.*"))
    if not tf_files:
        print(f"{label:<30} {'no TF':>10} {'no TF':>10}")
        continue

    ea = EventAccumulator(str(tf_files[0]))
    ea.Reload()

    if PSNR_TAG not in ea.Tags().get("scalars", []):
        print(f"{label:<30} {'no tag':>10} {'no tag':>10}")
        continue

    events = {e.step: e.value for e in ea.Scalars(PSNR_TAG)}
    p7k  = f"{events.get(7000, float('nan')):.4f}"
    p30k = f"{events.get(30000, float('nan')):.4f}"
    print(f"{label:<30} {p7k:>10} {p30k:>10}")

print()
print("Reference: exp08 OpenMAVIS PSNR@30k = 33.012")
