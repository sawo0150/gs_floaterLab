#!/usr/bin/env python3
"""Render the held-out split from each saved map and compute SSIM/LPIPS.

Training only logs PSNR, so both paper tables need a second pass. For every
completed run, render the llffhold-8 test split at the final step and run the
stock 3DGS metrics script; results land in each run directory as results.json.

Covers both deliverables:
  Table 1  dense-supervision manifest_curve.json, budget 60   (38 runs)
  Table 2  paper-figures manifest_view_ordering.json          (114 runs, 19 shared)

Resumable: a run whose results.json already carries SSIM is skipped.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DENSE = HERE.parent / "dense-supervision"
REPO = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom-exp77-budget-5070ti-repro")
PYTHON = "/home/wosas/miniconda3/envs/3dgs/bin/python"
SOURCES = ((DENSE / "evidence/manifest_curve.json", "table1"),
           (HERE / "evidence/manifest_view_ordering.json", "table2"))


def done(output: Path) -> bool:
    path = output / "results.json"
    if not path.is_file():
        return False
    return any("SSIM" in value for value in json.loads(path.read_text()).values())


def main() -> None:
    only = set(sys.argv[1:]) or None
    jobs, seen = [], set()
    for path, tag in SOURCES:
        if only and tag not in only:
            continue
        for job in json.loads(path.read_text())["jobs"]:
            if job.get("state") != "complete" or job["output"] in seen:
                continue
            seen.add(job["output"])
            jobs.append((tag, job))

    todo = [(tag, job) for tag, job in jobs if not done(Path(job["output"]))]
    print(f"{len(jobs)} completed runs, {len(todo)} need metrics", flush=True)
    failed = []
    for index, (tag, job) in enumerate(todo, 1):
        output = Path(job["output"])
        label = f"{tag} {job['family']}/{job['scene']} b{job['budget']} {job['arm']}"
        print(f"[{index}/{len(todo)}] {label}", flush=True)
        render = subprocess.run(
            [PYTHON, str(REPO / "render.py"), "-m", str(output), "-s", job["dataset"],
             "--iteration", str(job["total_iterations"]), "--skip_train", "--quiet",
             "-r", "4", "--eval"],
            capture_output=True, text=True, cwd=str(REPO))
        if render.returncode:
            failed.append((label, "render", render.stderr.strip().splitlines()[-1:]))
            print(f"  RENDER FAILED: {failed[-1][2]}", flush=True)
            continue
        metrics = subprocess.run(
            [PYTHON, str(REPO / "metrics.py"), "-m", str(output)],
            capture_output=True, text=True, cwd=str(REPO))
        if metrics.returncode:
            failed.append((label, "metrics", metrics.stderr.strip().splitlines()[-1:]))
            print(f"  METRICS FAILED: {failed[-1][2]}", flush=True)
    print(f"metrics pass complete; {len(failed)} failures", flush=True)
    for label, stage, detail in failed:
        print(f"  {label}: {stage} {detail}", flush=True)


if __name__ == "__main__":
    main()
