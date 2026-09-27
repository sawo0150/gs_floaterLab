#!/usr/bin/env python3
"""Behavior-neutral R4 probe with exact topology mutation accounting.

This wrapper deliberately keeps the Exp94 mapping/evaluation protocol and
flags unchanged.  The only mapper change is diagnostic logging of rows cloned,
split, and pruned inside each existing densify-and-prune transaction.  Results
go to a fresh root and can never be mixed into the preserved Exp94 panel.
"""

from pathlib import Path
import sys

import run_exp94_normalized_metric_v2_fixed_eval as exp94


panel = exp94.panel
base = exp94.base

panel.ROOT = base.WORKSPACE / "results/experiments/exp95_topology_churn_probe"
panel.DOCS = (
    base.WORKSPACE / "context/experiments/benchmark_custom"
    / "exp95_topology_churn_probe_20260924"
)
panel.BENCHMARK_LABEL = "v2.2-exp95-topology-telemetry"
panel.SUMMARY_TITLE = (
    "Exp95 topology churn probe — behavior-neutral R4 vs official vanilla"
)
panel.SOURCE_PATHS = (
    *panel.SOURCE_PATHS,
    base.PAPER_ROOT / "vigs/gaussian/utils/topology_telemetry.py",
    base.PAPER_ROOT / "docs/LOCAL_TOPOLOGY_TWO_TRACK_PLAN.md",
    Path(__file__),
)


def main() -> int:
    rows = panel.v2.install_inventory()
    exp94.check_evaluation_contract(rows)
    return panel.main()


if __name__ == "__main__":
    sys.exit(main())
