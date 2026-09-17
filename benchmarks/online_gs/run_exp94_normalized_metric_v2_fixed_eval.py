#!/usr/bin/env python3
"""B-track v2.2: source-locked mixed-dataset evaluator contract.

Exp92/93 traced the apparent RPNG 4.8 dB drop to Aria's wrapper replacing
RPNG/UTMM's distortion-aware evaluation command.  Exp94 uses the corrected
adapter, asserts the dataset-specific command before any GPU work, and runs
the otherwise unchanged exp91 render-matched paired protocol in a fresh root.
"""

from pathlib import Path
import sys

import run_exp91_normalized_metric_v2_reliable as panel
import run_exp78b_r4_all_scenes as all_scenes
import run_exp78b_r4_aria as aria
import run_exp78b_stage6rx4_cross_sequence as base


panel.ROOT = base.WORKSPACE / "results/experiments/exp94_normalized_metric_v2_fixed_eval"
panel.DOCS = (
    base.WORKSPACE / "context/experiments/benchmark_custom"
    / "metric_benchmark_v2_fixed_eval_20260917"
)
panel.SOURCE_PATHS = (
    *panel.SOURCE_PATHS,
    Path(base.__file__),
    Path(all_scenes.__file__),
    Path(aria.__file__),
    Path(__file__),
)


def check_evaluation_contract(rows: list[dict]) -> None:
    for row in rows:
        dataset, scene = row["dataset"], row["scene"]
        command = base.evaluation_command(
            panel.ROOT / dataset / scene / "command_check", dataset, scene
        )
        has_undistort = "--undistort" in command
        if has_undistort != (dataset != "aria"):
            raise RuntimeError(
                f"evaluator preprocessing mismatch: {dataset}/{scene}: {command}"
            )


def main() -> int:
    rows = panel.v2.install_inventory()
    check_evaluation_contract(rows)
    return panel.main()


if __name__ == "__main__":
    sys.exit(main())
