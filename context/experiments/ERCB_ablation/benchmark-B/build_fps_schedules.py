#!/usr/bin/env python3
"""Per-interval farthest-point-in-time subsampled schedules.

Instead of admitting every dense frame in a KF interval (dense_rr/dense_ercb)
or only the interval's own keyframe (kf_rr), cap each interval's admitted
frame count at that interval's average training capacity -- the same
`budget` (updates/event) already used for the fixed-schedule panel, since
total_iterations = 1 + (events-1)*budget means budget already IS the average
number of optimizer updates available per interval. If an interval has more
frames than budget, keep only `budget` of them, chosen by greedy farthest-
point-in-time sampling (each pick maximizes the minimum temporal distance to
frames already kept) so the subsample stays spread across the interval
instead of clustering. Intervals with <= budget frames are kept whole.

Output preserves the exact arrival_iteration_by_name values from the
existing full schedule (evidence/schedules/*.json) for kept names only, so
this plugs into train.py via the existing --eligible_names_file flag with no
further code changes -- same total_iterations, same monotonic order, same
llffhold-8 held-out set as the rr/ercb/kf_rr arms.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEDULES = HERE / "evidence/schedules"
BRACKETS = HERE / "evidence/work_credit_brackets"
OUTPUT = HERE / "evidence/schedules_fps"


def farthest_point_subset(names: list[str], budget: int) -> list[str]:
    if len(names) <= budget:
        return list(names)
    timestamps = [float(name.rsplit(".", 1)[0]) for name in names]
    order = sorted(range(len(names)), key=lambda i: timestamps[i])
    if budget <= 1:
        return [names[order[0]]]
    selected = {order[0], order[-1]}
    remaining = [i for i in order if i not in selected]
    while len(selected) < budget and remaining:
        best_index, best_distance = None, -1.0
        for i in remaining:
            distance = min(abs(timestamps[i] - timestamps[j]) for j in selected)
            if distance > best_distance:
                best_index, best_distance = i, distance
        selected.add(best_index)
        remaining.remove(best_index)
    return [names[i] for i in sorted(selected)]


def build(family: str, scene: str, stride: int, budget: int) -> Path:
    schedule_path = SCHEDULES / family / f"{scene}_stride{stride}_event{budget}.json"
    schedule = json.loads(schedule_path.read_text())
    bracket_path = BRACKETS / family / f"{scene}_stride{stride}.json"
    brackets = json.loads(bracket_path.read_text())["brackets"]
    full_pool = schedule["arrival_iteration_by_name"]
    kept: dict[str, int] = {}
    for names in brackets:
        present = [n for n in names if n in full_pool]
        if not present:
            continue
        subset = farthest_point_subset(present, budget)
        for name in subset:
            kept[name] = full_pool[name]
    destination = OUTPUT / family / f"{scene}_stride{stride}_event{budget}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({
        "arrival_iteration_by_name": kept,
        "total_iterations": schedule["total_iterations"],
        "source_schedule": str(schedule_path),
        "source_brackets": str(bracket_path),
        "per_interval_cap": budget,
        "full_pool_size": len(full_pool),
        "fps_pool_size": len(kept),
    }, indent=2) + "\n")
    return destination


def main() -> None:
    import sys
    if len(sys.argv) != 5:
        raise SystemExit("usage: build_fps_schedules.py <family> <scene> <stride> <budget>")
    family, scene, stride, budget = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    destination = build(family, scene, stride, budget)
    payload = json.loads(destination.read_text())
    print(f"{destination}: fps_pool_size={payload['fps_pool_size']}/{payload['full_pool_size']}")


if __name__ == "__main__":
    main()
