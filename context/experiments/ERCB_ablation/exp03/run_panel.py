#!/usr/bin/env python3
"""Run or resume the fixed exp03 manifest without overwriting any output."""

import json
import shutil
import subprocess
from pathlib import Path


EXP = Path(__file__).resolve().parent
MANIFEST = EXP / "evidence/manifest.json"


def compute_processes():
    result = subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"], text=True
    )
    return [line.strip() for line in result.splitlines() if line.strip()]


def completed(output, total):
    summary_file = output / "view_scheduler_summary.json"
    curve_file = output / "evaluation_curve.jsonl"
    if not summary_file.is_file() or not curve_file.is_file():
        return False
    summary = json.loads(summary_file.read_text())
    curves = [json.loads(line) for line in curve_file.read_text().splitlines()]
    tests = [row for row in curves if row["split"] == "test"]
    return (
        summary.get("post_update_reporting") is True
        and summary.get("completed_updates_this_run") == total
        and tests and tests[-1]["iteration"] == total
    )


def main():
    manifest = json.loads(MANIFEST.read_text())
    for index, job in enumerate(manifest["jobs"], 1):
        output = Path(job["output"])
        if completed(output, job["total_iterations"]):
            print(f"SKIP_COMPLETE {index}/{len(manifest['jobs'])} {job['scene']} "
                  f"b{job['budget']} {job['arm']} s{job['seed']}", flush=True)
            continue
        if output.exists():
            raise RuntimeError(f"incomplete output exists; refusing overwrite: {output}")
        if compute_processes():
            raise RuntimeError("GPU compute process active; wait and resume later")
        if shutil.disk_usage(EXP).free < 20 * 1024**3:
            raise RuntimeError("less than 20 GiB free; refusing to start")
        output.parent.mkdir(parents=True, exist_ok=True)
        log = output.with_suffix(".train.log")
        if log.exists():
            raise RuntimeError(f"log exists; refusing overwrite: {log}")
        print(f"START {index}/{len(manifest['jobs'])} {job['scene']} "
              f"b{job['budget']} {job['arm']} s{job['seed']} T={job['total_iterations']}",
              flush=True)
        with log.open("x") as stream:
            subprocess.run(job["argv"], stdout=stream, stderr=subprocess.STDOUT, check=True)
        if not completed(output, job["total_iterations"]):
            raise RuntimeError(f"post-run contract failed: {output}")
        print(f"DONE {index}/{len(manifest['jobs'])} {job['scene']} "
              f"b{job['budget']} {job['arm']} s{job['seed']}", flush=True)


if __name__ == "__main__":
    main()
