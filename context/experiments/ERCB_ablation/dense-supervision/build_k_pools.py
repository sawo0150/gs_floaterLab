#!/usr/bin/env python3
"""Per-interval supervision pools: keyframe + (K-1) in-between frames.

The dense-vs-keyframe question is not binary. Admitting *every* in-between
frame divides a fixed streaming budget across so many views that none of them
is trained enough; admitting none throws away the viewpoints keyframes miss.
This sweeps the middle: for each VIGS keyframe interval keep the keyframe plus
K-1 of its in-between frames, chosen by greedy farthest-point-in-time sampling
seeded with the keyframe itself, so the extra views are spread across the
interval rather than clustered next to the keyframe.

K=1 reduces exactly to the keyframe-only pool. Large K approaches the full
dense pool. Output is an eligible-names list consumed by train.py's
--eligible_names_file, so arrival timing, monotonic order, total updates and
the llffhold-8 held-out split are untouched.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH_B = HERE.parent / "benchmark-B"
BRACKETS = BENCH_B / "evidence/work_credit_brackets"
KF_POOLS = BENCH_B / "evidence/schedules_kfrr"
SCHEDULES = BENCH_B / "evidence/schedules"
OUTPUT = HERE / "evidence/k_pools"


def timestamp(name: str) -> float:
    return float(name.rsplit(".", 1)[0])


def pick(bracket: list[str], keyframes: set[str], k: int) -> list[str]:
    """Keyframe (if any) plus k-1 farthest-point-in-time in-between frames."""
    anchors = [n for n in bracket if n in keyframes]
    others = [n for n in bracket if n not in keyframes]
    selected = list(anchors)
    quota = k - 1 if anchors else k
    if quota <= 0 or not others:
        return selected
    times = {n: timestamp(n) for n in bracket}
    seeds = [times[n] for n in selected] or [times[others[0]]]
    if not selected:
        selected.append(others.pop(0))
        seeds = [times[selected[0]]]
        quota -= 1
    remaining = list(others)
    while quota > 0 and remaining:
        best, best_distance = None, -1.0
        for candidate in remaining:
            distance = min(abs(times[candidate] - s) for s in seeds)
            if distance > best_distance:
                best, best_distance = candidate, distance
        selected.append(best)
        seeds.append(times[best])
        remaining.remove(best)
        quota -= 1
    return selected


def build(family: str, scene: str, budget: int, k: int) -> Path:
    brackets = json.loads((BRACKETS / family / f"{scene}_stride20.json").read_text())["brackets"]
    keyframes = set(json.loads(
        (KF_POOLS / family / f"{scene}_stride20_event15.json").read_text())["arrival_iteration_by_name"])
    train_pool = set(json.loads(
        (SCHEDULES / family / f"{scene}_stride20_event{budget}.json").read_text())["arrival_iteration_by_name"])
    names: list[str] = []
    for bracket in brackets:
        present = [n for n in bracket if n in train_pool]
        if present:
            names.extend(pick(present, keyframes, k))
    names = sorted(set(names))
    destination = OUTPUT / family / f"{scene}_event{budget}_k{k}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(names, indent=2) + "\n")
    return destination


def main() -> None:
    import sys
    import os
    spec = os.environ.get("K_SCENES")
    scenes = ([tuple(x.split("/")) for x in spec.split(",")] if spec
              else [("aria", "aria1253"), ("utmm", "square-1"), ("rpng", "table_01")])
    ks = [int(v) for v in sys.argv[1:]] or [2, 4, 8]
    rows = []
    for family, scene in scenes:
        for budget in tuple(int(v) for v in os.environ.get('K_BUDGETS','15,30,60').split(',')):
            for k in ks:
                path = build(family, scene, budget, k)
                size = len(json.loads(path.read_text()))
                rows.append((family, scene, budget, k, size))
    for family, scene, budget, k, size in rows:
        if budget == 15:
            print(f"{family}/{scene:10s} e{budget:2d} K={k}: pool={size}")
    (OUTPUT / "inventory.json").write_text(json.dumps([
        {"family": f, "scene": s, "budget": b, "k": k, "pool_size": n} for f, s, b, k, n in rows
    ], indent=2) + "\n")
    print(OUTPUT / "inventory.json")


if __name__ == "__main__":
    main()
