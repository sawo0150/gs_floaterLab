#!/usr/bin/env python3
"""
One-off script: save anchor files into existing v3 and v4 diagnostic folders.
Runs render_completed_plateau_ellipsoids.main() twice with different settings.
"""
import sys
import importlib
from pathlib import Path

SCRIPT_DIR = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/scripts/diagnostic")
sys.path.insert(0, str(SCRIPT_DIR))

import render_completed_plateau_ellipsoids as R

BASE_DIAG = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/diagnostic")

RUNS = [
    {
        "label": "v3 (D=0.35m)",
        "folder": BASE_DIAG / "plateau_ellipsoid_v3_depthguide_20260705_034954",
        "d_target": 0.35,
    },
    {
        "label": "v4 (D=0.50m)",
        "folder": BASE_DIAG / "plateau_ellipsoid_v4_20260705_041132",
        "d_target": 0.50,
    },
]

for run in RUNS:
    print(f"\n{'='*60}")
    print(f"  Saving anchors for {run['label']}  ->  {run['folder'].name}")
    print(f"{'='*60}")
    # Monkey-patch module-level constants
    R.D_TARGET = run["d_target"]
    R.OUT_DIR  = run["folder"]
    run["folder"].mkdir(parents=True, exist_ok=True)
    R.main()
    print(f"Done: {run['label']}")
