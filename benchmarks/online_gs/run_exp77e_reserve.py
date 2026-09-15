#!/usr/bin/env python3
"""Matched table_06 reserve comparison; existing benchmark runner provides audits."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import run_vigs_1x_zero_tail_16 as baseline

ROOT = baseline.WORKSPACE / "results/experiments/exp77e2_reserve_zero_20260911"
WRAPPER = Path(__file__).with_suffix(".sh")


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    baseline.RUNNER = WRAPPER
    # Parent runner passes 'baseline'; the clean exp70 wrapper accepts 'control'.
    # Both arms use detached loss off, set explicitly by our wrapper.
    baseline.RUNSET = "exp77e2_reserve_zero_20260911"
    before = subprocess.check_output(["git", "diff", "HEAD"], cwd=baseline.VIGS_REPO)
    (ROOT / "source_before.patch").write_bytes(before)
    records = []
    for index, reserve in enumerate((20, 0, 0, 20)):
        name = f"run{index}_reserve{reserve}"
        baseline.OUTPUT_ROOT = ROOT / name
        os.environ["EXP77E_RESERVE_MS"] = str(reserve)
        sys.argv = [str(__file__), "--only", "rpng/table_06"]
        started = time.time()
        print(f"EXP77E_START {name}", flush=True)
        code = baseline.main()
        records.append(dict(run=name, reserve_ms=reserve, returncode=code, started_unix=started, finished_unix=time.time()))
        (ROOT / "runs.json").write_text(json.dumps(records, indent=2) + "\n")
        if code:
            raise RuntimeError(f"{name} failed; stop comparison for diagnosis")
    after = subprocess.check_output(["git", "diff", "HEAD"], cwd=baseline.VIGS_REPO)
    (ROOT / "source_after.patch").write_bytes(after)
    assert before == after, "VIGS tracked source changed during comparison"


if __name__ == "__main__":
    main()
