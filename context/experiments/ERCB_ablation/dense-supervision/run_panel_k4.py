#!/usr/bin/env python3
"""Run/resume exp87 sequentially without overwriting artifacts."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "evidence/manifest_k4.json"


def compute_processes() -> list[str]:
    output = subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"], text=True)
    return [line.strip() for line in output.splitlines() if line.strip()]


def completed(output: Path, total: int) -> bool:
    curve_path = output / "evaluation_curve.jsonl"
    cloud = output / f"point_cloud/iteration_{total}/point_cloud.ply"
    if not curve_path.is_file() or not cloud.is_file():
        return False
    rows = [json.loads(line) for line in curve_path.read_text().splitlines() if line]
    tests = [row for row in rows if row.get("split") == "test"]
    return bool(tests and tests[-1].get("iteration") == total)


def save(manifest: dict) -> None:
    done = sum(job.get("state") == "complete" for job in manifest["jobs"])
    failed = sum(job.get("state") == "failed" for job in manifest["jobs"])
    manifest["state"] = f"RUNNING_{done}_COMPLETE_{failed}_FAILED_OF_{len(manifest['jobs'])}"
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    for index, job in enumerate(manifest["jobs"], 1):
        output = Path(job["output"])
        label = f"{job['family']}/{job['scene']} {job['arm']}"
        if completed(output, job["total_iterations"]):
            job["state"] = "complete"
            save(manifest)
            print(f"SKIP {index}/{len(manifest['jobs'])} {label}", flush=True)
            continue
        if output.exists():
            job["state"] = "failed"
            job["error"] = "incomplete output preserved"
            save(manifest)
            print(f"PRESERVE_FAILED {index}/{len(manifest['jobs'])} {label}", flush=True)
            continue
        active = compute_processes()
        if active:
            raise RuntimeError(f"GPU compute process active; wait and resume: {active}")
        if shutil.disk_usage(HERE).free < 20 * 1024**3:
            raise RuntimeError("less than 20 GiB free")
        output.parent.mkdir(parents=True, exist_ok=True)
        log = output.with_suffix(".train.log")
        if log.exists():
            raise RuntimeError(f"log exists: {log}")
        print(f"START {index}/{len(manifest['jobs'])} {label} T={job['total_iterations']}", flush=True)
        started = time.time()
        with log.open("x") as stream:
            result = subprocess.run(job["argv"], stdout=stream, stderr=subprocess.STDOUT)
        job["returncode"] = result.returncode
        job["wall_seconds"] = time.time() - started
        if result.returncode or not completed(output, job["total_iterations"]):
            job["state"] = "failed"
            job["error"] = "nonzero exit or completion contract failure"
            save(manifest)
            print(f"FAILED {index}/{len(manifest['jobs'])} {label}", flush=True)
            continue
        job["state"] = "complete"
        save(manifest)
        print(f"DONE {index}/{len(manifest['jobs'])} {label} "
              f"({job['wall_seconds']/60:.1f} min)", flush=True)
    done = sum(job.get("state") == "complete" for job in manifest["jobs"])
    failed = sum(job.get("state") == "failed" for job in manifest["jobs"])
    manifest["state"] = f"FINISHED_{done}_COMPLETE_{failed}_FAILED_OF_{len(manifest['jobs'])}"
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(manifest["state"], flush=True)


if __name__ == "__main__":
    main()
