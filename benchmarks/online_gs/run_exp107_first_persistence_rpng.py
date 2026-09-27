#!/usr/bin/env python3
"""Exp107: transfer Exp106 first-persistence ticket to RPNG table_01."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import run_exp106_first_persistence_ticket as prior


ROOT = (
    prior.prior.base.WORKSPACE
    / "results/experiments/exp107_first_persistence_rpng"
)
DOCS = (
    prior.prior.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp107_first_persistence_rpng_20260924"
)
SOURCE_PATHS = (*prior.SOURCE_PATHS, Path(__file__))


def check_source_lock() -> None:
    current = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in SOURCE_PATHS
    }
    path = ROOT / "source_lock.json"
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        if old["sha256"] != current:
            raise RuntimeError("Exp107 source changed after start; use a new root")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "protocol": "exp107_first_persistence_rpng_v1",
                "vigs_commit": "f6a90853",
                "source_lab_commit": "1e8acbd",
                "sha256": current,
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run"))
    args = parser.parse_args()
    prior.ROOT = ROOT
    prior.DOCS = DOCS
    prior.check_source_lock = check_source_lock
    rows = prior.prior.panel.v2.install_inventory()
    prior.prior.exp94.check_evaluation_contract(rows)
    check_source_lock()
    target = [
        row for row in rows
        if row["dataset"] == "rpng" and row["scene"] == "table_01"
    ][0]
    if args.action == "preflight":
        print("Exp107 preflight PASS: RPNG first-persistence transfer")
        return 0
    prior.run_one(target)
    summary = DOCS / "summary.md"
    summary.write_text(
        summary.read_text(encoding="utf-8").replace(
            "# Exp106 —", "# Exp107 —", 1
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
