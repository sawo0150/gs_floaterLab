#!/usr/bin/env python3
"""Derive causal admission brackets for work-credit admission from causal_arrivals.json.

Each dataset's causal_arrivals.json (written by prepare_datasets.py) maps every
train frame name to a raw event-bracket iteration (iters_per_event=60, one
bracket per VIGS keyframe interval -- the same event grouping used to build
the fixed-budget schedules/*.json). This script just recovers the bracket
grouping (event id -> member names, in causal order) and writes it in the
{"brackets": [[name, ...], ...]} shape train.py's --work_credit_brackets_file
expects. No budget/iteration values are involved -- work-credit admission
paces bracket admission by service, not by a precomputed iteration schedule.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DATA_ROOT = ROOT / "data/benchmarks/ercb_benchmark_B_stride20"
OUTPUT = HERE / "evidence/work_credit_brackets"


def build(family: str, scene: str, stride: int) -> Path:
    causal = DATA_ROOT / family / scene / f"stride{stride}" / "causal_arrivals.json"
    payload = json.loads(causal.read_text())
    if payload.get("iters_per_event") != 60 or payload.get("tail_iters") != 0:
        raise ValueError(f"unexpected causal_arrivals.json: {causal}")
    by_event: dict[int, list[str]] = {}
    for name, value in payload["arrival_iteration_by_name"].items():
        event = (int(value) - 1) // 60
        by_event.setdefault(event, []).append(name)
    brackets = [sorted(by_event[event]) for event in sorted(by_event)]
    destination = OUTPUT / family / f"{scene}_stride{stride}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({
        "source": str(causal), "brackets": brackets,
        "n_brackets": len(brackets), "n_frames": sum(len(b) for b in brackets),
    }, indent=2) + "\n")
    return destination


def main() -> None:
    import sys
    if len(sys.argv) != 4:
        raise SystemExit("usage: build_work_credit_brackets.py <family> <scene> <stride>")
    family, scene, stride = sys.argv[1], sys.argv[2], int(sys.argv[3])
    destination = build(family, scene, stride)
    print(destination)


if __name__ == "__main__":
    main()
