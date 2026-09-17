#!/usr/bin/env python3
"""Repeat exp92 branch capture with preprocessing argv/hash instrumentation."""

from pathlib import Path

import run_exp92_capture_evaluator_branch as capture


capture.ROOT = Path("/home/intern/gs_floaterLab/results/experiments/exp93_preprocess_branch_capture")
capture.OUT = capture.ROOT / "rpng/table_01/normalized_s0"


if __name__ == "__main__":
    capture.main()
