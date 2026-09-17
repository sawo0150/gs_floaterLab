#!/usr/bin/env python3
"""Run/resume the paired init-density pilot without overwriting artifacts."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "evidence/manifest.json"


def completed(output: Path, total: int) -> bool:
    summary_path = output / "view_scheduler_summary.json"
    curve_path = output / "evaluation_curve.jsonl"
    if not summary_path.is_file() or not curve_path.is_file():
        return False
    summary = json.loads(summary_path.read_text())
    curves = [json.loads(line) for line in curve_path.read_text().splitlines() if line]
    tests = [row for row in curves if row.get("split") == "test"]
    return bool(
        summary.get("completed_updates_this_run") == total
        and summary.get("post_update_reporting") is True
        and tests
        and tests[-1].get("iteration") == total
    )


def gpu_busy() -> bool:
    return bool(
        subprocess.check_output(
            ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
            text=True,
        ).strip()
    )


def save(manifest: dict) -> None:
    done = sum(job.get("state") == "complete" for job in manifest["jobs"])
    failed = sum(job.get("state") == "failed" for job in manifest["jobs"])
    manifest["state"] = f"RUNNING_{done}_COMPLETE_{failed}_FAILED_OF_{len(manifest['jobs'])}"
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    for index, job in enumerate(manifest["jobs"], 1):
        output = Path(job["output"])
        label = f"{job['family']}/{job['scene']} {job['density']} {job['arm']}"
        if completed(output, job["total_iterations"]):
            job["state"] = "complete"
            save(manifest)
            print(f"SKIP {index}/{len(manifest['jobs'])} {label}", flush=True)
            continue
        if output.exists():
            raise RuntimeError(f"incomplete output preserved: {output}")
        if gpu_busy():
            raise RuntimeError("GPU compute process active; wait and resume")
        if shutil.disk_usage(HERE).free < 15 * 1024**3:
            raise RuntimeError("less than 15 GiB free")
        output.parent.mkdir(parents=True, exist_ok=True)
        log = output.with_suffix(".train.log")
        print(f"START {index}/{len(manifest['jobs'])} {label}", flush=True)
        started = time.time()
        with log.open("x") as stream:
            result = subprocess.run(job["argv"], stdout=stream, stderr=subprocess.STDOUT)
        job["returncode"] = result.returncode
        job["wall_seconds"] = time.time() - started
        if result.returncode or not completed(output, job["total_iterations"]):
            job["state"] = "failed"
            save(manifest)
            raise RuntimeError(f"run failed; artifacts preserved: {output}")
        job["state"] = "complete"
        save(manifest)
        print(f"DONE {index}/{len(manifest['jobs'])} {label}", flush=True)
    manifest["state"] = f"FINISHED_{len(manifest['jobs'])}_COMPLETE_0_FAILED"
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
