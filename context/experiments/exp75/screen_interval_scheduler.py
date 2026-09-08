#!/usr/bin/env python3
"""Scheduler-only screen for hierarchical KF-interval softmax RR."""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


REPO = Path("/home/intern/gs_floaterLab/repos/main/3dgs-custom")
DATA = Path("/home/intern/gs_floaterLab/data/exp74_causal_offline")
sys.path.insert(0, str(REPO))
from runtime.scheduler import make_scheduler  # noqa: E402


def entropy_ratio(values: np.ndarray, categories: int) -> float:
    if len(values) == 0 or categories <= 1:
        return 1.0
    hist = np.bincount(values, minlength=categories)
    p = hist[hist > 0] / len(values)
    return float(-(p * np.log(p)).sum() / math.log(min(categories, len(values))))


def mean_chunks(values: np.ndarray, size: int, fn) -> float:
    chunks = [values[start : start + size] for start in range(0, len(values), size)]
    chunks = [chunk for chunk in chunks if len(chunk) == size]
    return float(np.mean([fn(chunk) for chunk in chunks])) if chunks else float("nan")


def simulate(
    scene: str, name: str, beta: float, block_size: int, total: int,
    phase_start: int = 15000,
) -> dict:
    payload = json.loads((DATA / scene / "causal_arrivals.json").read_text())
    arrivals_by_name = payload["arrival_iteration_by_name"]
    names = list(arrivals_by_name)
    arrivals = np.asarray(list(arrivals_by_name.values()), dtype=np.int64)
    scheduler = make_scheduler(name, 0, beta, block_size, phase_start)
    history = []
    next_arrival = 0
    frame_interval = np.full(len(names), -1, dtype=np.int64)
    interval_arrival = []
    interval_members = defaultdict(list)

    for iteration in range(1, total + 1):
        added = []
        while next_arrival < len(names) and arrivals[next_arrival] <= iteration:
            added.append(next_arrival)
            next_arrival += 1
        if added:
            interval_id = len(interval_arrival)
            interval_arrival.append(iteration)
            for item in added:
                frame_interval[item] = interval_id
                interval_members[interval_id].append(item)
        scheduler.add(added)
        history.append(scheduler.draw())

    history = np.asarray(history, dtype=np.int64)
    history_intervals = frame_interval[history]
    frame_counts = np.bincount(history, minlength=len(names)).astype(np.float64)
    interval_counts = np.bincount(history_intervals, minlength=len(interval_arrival)).astype(np.float64)
    tail_start = int(arrivals.max()) - 1
    tail_frames = history[tail_start:]
    tail_intervals = history_intervals[tail_start:]
    temporal_bins = np.minimum(tail_frames * 16 // len(names), 15)
    return {
        "scene": scene,
        "scheduler": name,
        "beta": beta,
        "interval_block_size": block_size,
        "iterations": total,
        "phase_start": phase_start,
        "frames": len(names),
        "intervals": len(interval_arrival),
        "last_arrival": int(arrivals.max()),
        "frame_count_cv": float(frame_counts.std() / frame_counts.mean()),
        "frame_count_min": int(frame_counts.min()),
        "frame_count_max": int(frame_counts.max()),
        "interval_count_cv": float(interval_counts.std() / interval_counts.mean()),
        "interval_count_min": int(interval_counts.min()),
        "interval_count_max": int(interval_counts.max()),
        "tail_temporal_entropy_128": mean_chunks(
            temporal_bins, 128, lambda x: entropy_ratio(x, 16)
        ),
        "tail_interval_entropy_native": mean_chunks(
            tail_intervals, block_size,
            lambda x: entropy_ratio(x, len(interval_arrival)),
        ),
        "tail_interval_unique_fraction_native": mean_chunks(
            tail_intervals, block_size, lambda x: len(np.unique(x)) / len(x)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "evidence" / "interval_scheduler_screen.json",
    )
    args = parser.parse_args()
    cases = []
    for scene in ("aria1253", "aria305", "aria12F"):
        for total in (30000, 45000):
            cases.append(simulate(scene, "causal_rr", 0.0, 16, total))
            for block_size in (8, 16, 32):
                for beta in (0.0, 0.0025, 0.005, 0.01, 0.02):
                    cases.append(simulate(scene, "interval_softmax_rr", beta, block_size, total))
                for beta in (0.0, 0.01, 0.02, 0.05, 0.1):
                    cases.append(simulate(scene, "interval_size_softmax_rr", beta, block_size, total))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(cases, indent=2) + "\n")
    print(f"wrote {len(cases)} cases to {args.output}")


if __name__ == "__main__":
    main()
