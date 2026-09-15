#!/usr/bin/env python3
"""Run/resume benchmark-A sequentially while preserving every artifact."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "evidence/manifest.json"


def compute_processes() -> list[str]:
    result = subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],
        text=True,
    )
    return [line.strip() for line in result.splitlines() if line.strip()]


def completed(output: Path, total: int) -> bool:
    summary_path = output / "view_scheduler_summary.json"
    curve_path = output / "evaluation_curve.jsonl"
    if not summary_path.is_file() or not curve_path.is_file():
        return False
    summary = json.loads(summary_path.read_text())
    rows = [json.loads(line) for line in curve_path.read_text().splitlines() if line.strip()]
    tests = [row for row in rows if row.get("split") == "test"]
    return bool(
        summary.get("post_update_reporting") is True
        and summary.get("completed_updates_this_run") == total
        and tests
        and tests[-1].get("iteration") == total
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
        label = f"{job['family']}/{job['scene']} {job['arm']} s{job['seed']}"
        if completed(output, job["total_iterations"]):
            job["state"] = "complete"
            print(f"SKIP_COMPLETE {index}/{len(manifest['jobs'])} {label}", flush=True)
            save(manifest)
            continue
        if output.exists():
            job["state"] = "failed"
            job["error"] = "incomplete output exists; preserved and not overwritten"
            print(f"PRESERVE_INCOMPLETE {index}/{len(manifest['jobs'])} {label}", flush=True)
            save(manifest)
            continue
        active = compute_processes()
        if active:
            raise RuntimeError(f"GPU compute process active; wait and resume: {active}")
        if shutil.disk_usage(HERE).free < 15 * 1024**3:
            raise RuntimeError("less than 15 GiB free; refusing to start another job")
        output.parent.mkdir(parents=True, exist_ok=True)
        log = output.with_suffix(".train.log")
        if log.exists():
            raise RuntimeError(f"log exists; refusing overwrite: {log}")
        print(
            f"START {index}/{len(manifest['jobs'])} {label} T={job['total_iterations']}",
            flush=True,
        )
        started = time.time()
        try:
            with log.open("x") as stream:
                result = subprocess.run(
                    job["argv"], stdout=stream, stderr=subprocess.STDOUT, check=False
                )
            job["returncode"] = result.returncode
            job["wall_seconds"] = time.time() - started
            if result.returncode != 0 or not completed(output, job["total_iterations"]):
                job["state"] = "failed"
                job["error"] = "nonzero exit or post-run contract failure; artifacts preserved"
                print(f"FAILED {index}/{len(manifest['jobs'])} {label}", flush=True)
            else:
                job["state"] = "complete"
                print(f"DONE {index}/{len(manifest['jobs'])} {label}", flush=True)
        except BaseException as exc:
            job["state"] = "failed"
            job["error"] = repr(exc)
            save(manifest)
            raise
        save(manifest)
    complete = sum(job.get("state") == "complete" for job in manifest["jobs"])
    failed = sum(job.get("state") == "failed" for job in manifest["jobs"])
    manifest["state"] = f"FINISHED_{complete}_COMPLETE_{failed}_FAILED_OF_{len(manifest['jobs'])}"
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(manifest["state"], flush=True)


if __name__ == "__main__":
    main()
