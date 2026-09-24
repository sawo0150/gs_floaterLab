#!/usr/bin/env python3
"""Select one normalized-variance dense temperature without PSNR tuning.

This replays Exp111's immutable causal candidate pools through the production
queue.  The development scene is UTMM square-1 only.  The selected gamma is
the smallest fixed constant that changes at least 10% of repeat choices from
the zero-energy RR control and lowers final-generation count CV by at least
10%.  No image, validation metric, or future view is read.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[2]
PAPER_ROOT = Path("/home/intern/VIGS-SLAM-paper-full")
sys.path.insert(0, str(PAPER_ROOT / "vigs"))

from map_scheduler import ServiceShortfallIntervalReplayQueue  # noqa: E402


DEFAULT_RUNTIME = (
    WORKSPACE
    / "results/experiments/exp111_dense_repeat_ercb/utmm/square-1"
    / "dense_repeat_normalized/mapping_replay_runtime.json"
)
DEFAULT_RR_RUNTIME = DEFAULT_RUNTIME.parents[1] / (
    "dense_repeat_rr/mapping_replay_runtime.json"
)
GAMMA_CANDIDATES = (
    math.log(1.25),
    math.log(1.5),
    math.log(3.0),
    2.0,
    4.0,
    8.0,
    16.0,
    32.0,
    64.0,
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def recorded_trace(runtime: dict) -> tuple[list[int], list[int]]:
    full = []
    repeats = []
    for primary, repeat in zip(
        runtime["fixed_event_dense_opportunity_ledger"],
        runtime["fixed_event_dense_repeat_opportunity_ledger"],
    ):
        primary_uid = int(primary["selected_keys"][0][1])
        repeat_uid = int(repeat["selected_keys"][0][1])
        full.extend((primary_uid, repeat_uid))
        repeats.append(repeat_uid)
    return full, repeats


def replay(runtime: dict, gamma: float, potential: str) -> dict:
    queue = ServiceShortfallIntervalReplayQueue(
        seed=0,
        gamma=gamma,
        block_size=1,
        first_service_floor=True,
        selection_potential=potential,
    )
    generation = None
    full_trace = []
    repeat_trace = []
    final_pool = set()
    for primary, repeat in zip(
        runtime["fixed_event_dense_opportunity_ledger"],
        runtime["fixed_event_dense_repeat_opportunity_ledger"],
    ):
        current_generation = int(primary["map_generation"])
        if current_generation != generation:
            queue.reset()
            generation = current_generation
        candidates = {
            ("dense", int(uid)) for uid in primary["pool_uids_before"]
        }
        intervals = {candidate: candidate for candidate in candidates}
        final_pool = candidates
        for is_repeat in (False, True):
            selected = queue.draw(
                candidates,
                1,
                interval_by_candidate=intervals,
            )
            queue.commit_pending_draw(selected)
            uid = int(selected[0][1])
            full_trace.append(uid)
            if is_repeat:
                repeat_trace.append(uid)
    counts = [int(queue.selection_counts[key]) for key in final_pool]
    mean = math.fsum(counts) / len(counts)
    std = math.sqrt(
        math.fsum((count - mean) ** 2 for count in counts) / len(counts)
    )
    return {
        "full_trace": full_trace,
        "repeat_trace": repeat_trace,
        "final_count_min": min(counts),
        "final_count_max": max(counts),
        "final_count_cv": std / mean,
        "entropy_ratio": queue.summary(final_pool)[
            "service_shortfall_entropy_ratio"
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--rr-runtime", type=Path, default=DEFAULT_RR_RUNTIME)
    args = parser.parse_args()

    runtime = read_json(args.runtime)
    rr_runtime = read_json(args.rr_runtime)
    rr = replay(runtime, 0.0, "rr")
    recorded_normalized, _ = recorded_trace(runtime)
    recorded_rr, _ = recorded_trace(rr_runtime)
    baseline = replay(runtime, math.log(1.5), "normalized_variance")
    if baseline["full_trace"] != recorded_normalized:
        raise RuntimeError("production log(1.5) trace replay mismatch")
    if rr["full_trace"] != recorded_rr:
        raise RuntimeError("production RR trace replay mismatch")

    rows = []
    repeat_count = len(rr["repeat_trace"])
    for gamma in GAMMA_CANDIDATES:
        candidate = replay(runtime, gamma, "normalized_variance")
        repeat_differences = sum(
            left != right
            for left, right in zip(
                candidate["repeat_trace"], rr["repeat_trace"]
            )
        )
        repeat_fraction = repeat_differences / repeat_count
        cv_reduction = 1.0 - (
            candidate["final_count_cv"] / rr["final_count_cv"]
        )
        rows.append(
            {
                "gamma": gamma,
                "repeat_differences_vs_rr": repeat_differences,
                "repeat_difference_fraction": repeat_fraction,
                "final_count_cv": candidate["final_count_cv"],
                "final_count_cv_reduction_vs_rr": cv_reduction,
                "final_count_range": [
                    candidate["final_count_min"],
                    candidate["final_count_max"],
                ],
                "entropy_ratio": candidate["entropy_ratio"],
                "passes_predeclared_activity_gate": (
                    repeat_fraction >= 0.10 and cv_reduction >= 0.10
                ),
            }
        )
    passing = [
        row for row in rows if row["passes_predeclared_activity_gate"]
    ]
    if not passing:
        raise RuntimeError("no fixed gamma passes the activity gate")
    selected = min(passing, key=lambda row: row["gamma"])
    print(
        json.dumps(
            {
                "protocol": "exp112_temperature_trace_selection_v1",
                "development_scene": "utmm/square-1",
                "uses_image_or_quality_metric": False,
                "formula": "p_i proportional exp(-gamma*n_i/(T+1))",
                "gamma_is_constant_not_scaled_by_T": True,
                "baseline_trace_replay_pass": True,
                "rr_trace_replay_pass": True,
                "selection_rule": (
                    "smallest gamma with >=10% repeat-trace divergence "
                    "and >=10% final-generation count-CV reduction vs RR"
                ),
                "selected_gamma": selected["gamma"],
                "rows": rows,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
