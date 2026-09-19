#!/usr/bin/env python3
"""Render held-out views from the saved point clouds and compute SSIM/LPIPS.

The training loop only logs PSNR, so the paper tables need a second pass: for
every completed run, render the llffhold-8 test split at the final iteration
and run the stock 3DGS metrics script. Results land in each run directory as
results.json, which build_tables.py then reads.

Resumable: a run whose results.json already contains the final iteration is
skipped, so this can be re-run as more arms finish.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom-exp77-budget-5070ti-repro")
PYTHON = "/home/wosas/miniconda3/envs/3dgs/bin/python"
MANIFESTS = ("evidence/manifest_budget.json",)
BUDGET = 120   # Table A's operating point


def done(output: Path, total: int) -> bool:
    path = output / "results.json"
    if not path.is_file():
        return False
    payload = json.loads(path.read_text())
    return any("SSIM" in v for v in payload.values())


def main() -> None:
    only = set(sys.argv[1:]) or None
    jobs = []
    seen = set()
    for name in MANIFESTS:
        path = HERE / name
        if not path.is_file():
            continue
        for job in json.loads(path.read_text())["jobs"]:
            if job.get("state") != "complete":
                continue
            key = job["output"]
            if key in seen:
                continue
            seen.add(key)
            if only and job["arm"] not in only:
                continue
            if job.get("budget") != BUDGET:
                continue
            jobs.append(job)

    todo = [j for j in jobs if not done(Path(j["output"]), j["total_iterations"])]
    print(f"{len(jobs)} completed runs, {len(todo)} need metrics", flush=True)
    for index, job in enumerate(todo, 1):
        output = Path(job["output"])
        label = f"{job['family']}/{job['scene']} {job['arm']}"
        print(f"[{index}/{len(todo)}] {label}", flush=True)
        render = subprocess.run(
            [PYTHON, str(REPO / "render.py"), "-m", str(output), "-s", job["dataset"],
             "--iteration", str(job["total_iterations"]), "--skip_train", "--quiet",
             "-r", "4", "--eval"],
            capture_output=True, text=True, cwd=str(REPO))
        if render.returncode:
            print(f"  RENDER FAILED: {render.stderr.strip().splitlines()[-1:]}", flush=True)
            continue
        metrics = subprocess.run(
            [PYTHON, str(REPO / "metrics.py"), "-m", str(output)],
            capture_output=True, text=True, cwd=str(REPO))
        if metrics.returncode:
            print(f"  METRICS FAILED: {metrics.stderr.strip().splitlines()[-1:]}", flush=True)
    print("metrics pass complete", flush=True)


if __name__ == "__main__":
    main()
