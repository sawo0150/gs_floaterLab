#!/usr/bin/env python3
"""Long-horizon simulation for causal view replay schedulers.

The simulation deliberately isolates *which view receives an optimizer update*.
It does not pretend to reproduce nonlinear 3DGS training.  Each arrived view owns
a fixed synthetic gradient signature, optionally modulated over time.  We compare
the selected-gradient stream with the full-pool uniform-gradient target and compare
actual per-view update counts with each view's age-adjusted uniform quota.

Outputs (under --output-dir):
  - fairness_runs.csv        per-run exposure metrics
  - gradient_cases.csv       aggregate gradient bias/mixing metrics
  - aggregate_ranking.csv    rank-based cross-scenario summary
  - summary.json             machine-readable configuration and headline result
  - tradeoff.png             fairness vs. gradient mixing
  - representative_counts.png
  - representative_deficit.png

The production controls are mirrored from VIGS-SLAM's CausalShuffleQueue and
ActiveArchiveReplayQueue.  The proposed scheduler is maximum-entropy quota-aware
random reshuffling (ME-QARR): choose the largest age-adjusted service deficit and
sample uniformly among exact ties.  At a fixed pool this is exactly a uniform random
permutation per epoch.  ME-BDS(C) is the maximum-entropy relaxation: sample uniformly
among every action that keeps the service-tag span at most C.
"""

from __future__ import annotations

import argparse
import collections
import csv
import heapq
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


@dataclass(frozen=True)
class Pattern:
    name: str
    arrivals: np.ndarray

    @property
    def steps(self) -> int:
        return int(self.arrivals.size)

    @property
    def final_views(self) -> int:
        return int(self.arrivals.sum())


@dataclass(frozen=True)
class GradientField:
    name: str
    signatures: np.ndarray
    amplitude: np.ndarray
    scale: float


def make_patterns(steps: int) -> list[Pattern]:
    if steps < 100:
        raise ValueError("--steps must be at least 100")

    static = np.zeros(steps, dtype=np.int64)
    static[0] = 256

    steady = np.zeros(steps, dtype=np.int64)
    steady[0] = 32
    steady[12::12] = 1

    bursty = np.zeros(steps, dtype=np.int64)
    bursty[0] = 32
    burst_period = max(100, steps // 14)
    burst_start = max(50, burst_period // 2)
    bursty[burst_start::burst_period] = 48

    accelerating = np.zeros(steps, dtype=np.int64)
    accelerating[0] = 32
    one_third = steps // 3
    two_thirds = 2 * steps // 3
    for t in range(1, steps):
        if t < one_third:
            accelerating[t] = int(t % 30 == 0)
        elif t < two_thirds:
            accelerating[t] = int((t - one_third) % 12 == 0)
        else:
            accelerating[t] = int((t - two_thirds) % 5 == 0)

    near_saturation = np.zeros(steps, dtype=np.int64)
    near_saturation[0] = 32
    near_saturation[2::2] = 1

    return [
        Pattern("static_256", static),
        Pattern("steady_growth", steady),
        Pattern("bursty_growth", bursty),
        Pattern("accelerating_growth", accelerating),
        Pattern("near_saturation", near_saturation),
    ]


def arrival_metadata(pattern: Pattern) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return eligible N_t, each view's arrival step, and pre-arrival fair clock."""
    eligible = np.cumsum(pattern.arrivals)
    if np.any(eligible <= 0):
        raise ValueError(f"pattern {pattern.name} has an empty eligible pool")
    arrival_step = np.repeat(np.arange(pattern.steps), pattern.arrivals)
    inv_pool = 1.0 / eligible.astype(np.float64)
    fair_clock = np.cumsum(inv_pool)
    fair_clock_before = np.concatenate(([0.0], fair_clock[:-1]))
    base = fair_clock_before[arrival_step]
    return eligible, arrival_step, base


def make_gradient_fields(
    pattern: Pattern,
    eligible: np.ndarray,
    arrival_step: np.ndarray,
    *,
    dim: int,
    seed: int,
) -> list[GradientField]:
    """Create fixed and time-modulated gradient stress fields.

    The view index is a proxy for trajectory order.  This intentionally makes the
    non-IID fields adversarial to recent-view bonuses while keeping the target known.
    """
    rng = np.random.default_rng(seed)
    n = pattern.final_views
    order_x = np.linspace(0.0, 1.0, n, dtype=np.float64)

    iid = rng.normal(size=(n, dim))

    features = np.stack(
        [
            np.sin(2.0 * np.pi * order_x),
            np.cos(2.0 * np.pi * order_x),
            np.sin(4.0 * np.pi * order_x),
            np.cos(4.0 * np.pi * order_x),
            2.0 * order_x - 1.0,
            np.tanh(8.0 * (order_x - 0.5)),
        ],
        axis=1,
    )
    projection = rng.normal(size=(features.shape[1], dim))
    smooth = features @ projection + 0.12 * rng.normal(size=(n, dim))

    regime_direction = rng.normal(size=dim)
    regime_direction /= np.linalg.norm(regime_direction)
    regime_label = np.where(order_x < 0.45, 1.0, -1.0)
    regime = (
        2.0 * regime_label[:, None] * regime_direction[None, :]
        + 0.25 * rng.normal(size=(n, dim))
    )

    t = np.arange(pattern.steps, dtype=np.float64)
    stationary = np.ones(pattern.steps, dtype=np.float64)
    # Slow modulation checks whether a scheduler repeatedly aligns one trajectory
    # region with high-gradient phases.  A common additive term would cancel and is
    # therefore intentionally omitted.
    modulated = 1.0 + 0.55 * np.sin(2.0 * np.pi * t / max(64.0, pattern.steps / 5.0))

    def field(name: str, values: np.ndarray, amplitude: np.ndarray) -> GradientField:
        centered = values - values.mean(axis=0, keepdims=True)
        scale = float(np.sqrt(np.mean(np.sum(centered * centered, axis=1))))
        return GradientField(name, values, amplitude, max(scale, 1.0e-12))

    return [
        field("iid_stationary", iid, stationary),
        field("smooth_order", smooth, stationary),
        field("smooth_order_time_modulated", smooth, modulated),
        field("abrupt_regime_time_modulated", regime, modulated),
    ]


class UniformIID:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.n = 0

    def add(self, count: int, fair_clock_before: float) -> None:
        del fair_clock_before
        self.n += int(count)

    def draw(self) -> int:
        return self.rng.randrange(self.n)


class DynamicShuffle:
    """Efficient mirror of the production growing CausalShuffleQueue."""

    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.n = 0
        self.queue: list[int] = []

    def add(self, count: int, fair_clock_before: float) -> None:
        del fair_clock_before
        old_n = self.n
        self.n += int(count)
        # Production behavior: every arrival joins a random location in the
        # unfinished epoch and is visited once before that epoch ends.
        for view_id in range(old_n, self.n):
            position = self.rng.randrange(len(self.queue) + 1)
            self.queue.insert(position, view_id)

    def draw(self) -> int:
        if not self.queue:
            self.queue = list(range(self.n))
            self.rng.shuffle(self.queue)
        return self.queue.pop()


class HeapFairScheduler:
    """Raw least-count or age-adjusted quota scheduler.

    For ME-QARR, a view arriving just before fair clock H receives base tag H.  Its
    priority is base_i + n_i, which is equivalent to choosing the largest deficit
    q_i - n_i because q_i = H - base_i and H is common to all eligible views.
    """

    def __init__(self, seed: int, *, quota_aware: bool, top_k: int = 1):
        self.rng = random.Random(seed)
        self.quota_aware = bool(quota_aware)
        self.top_k = max(1, int(top_k))
        self.heap: list[tuple[float, float, int]] = []
        self.counts: list[int] = []
        self.bases: list[float] = []

    def add(self, count: int, fair_clock_before: float) -> None:
        for _ in range(int(count)):
            view_id = len(self.counts)
            base = float(fair_clock_before) if self.quota_aware else 0.0
            self.counts.append(0)
            self.bases.append(base)
            heapq.heappush(self.heap, (base, self.rng.random(), view_id))

    def draw(self) -> int:
        take = min(self.top_k, len(self.heap))
        frontier = [heapq.heappop(self.heap) for _ in range(take)]
        chosen_pos = self.rng.randrange(take)
        chosen = frontier.pop(chosen_pos)
        for item in frontier:
            heapq.heappush(self.heap, item)
        _, _, view_id = chosen
        self.counts[view_id] += 1
        priority = self.bases[view_id] + self.counts[view_id]
        heapq.heappush(
            self.heap,
            (priority, self.rng.random(), view_id),
        )
        return view_id


class MaxEntropyBoundedDiscrepancy:
    """Uniformly sample every action preserving a hard tag-span cap.

    Let f_i = base_i + n_i.  The fair-clock H is the mean of the current f_i,
    so span(f) <= C implies |n_i - q_i| <= C.  At each draw this class forms the
    feasible set F={i: span(f + e_i) <= C} and samples Uniform(F).  Uniform is
    the unique maximum-Shannon-entropy distribution on that feasible support.

    Rejection sampling makes the common case O(1); the exact O(N) fallback is
    used only if 64 uniform proposals all miss the feasible set.
    """

    def __init__(self, seed: int, *, cap: float):
        self.rng = random.Random(seed)
        self.cap = float(cap)
        if not math.isfinite(self.cap) or self.cap < 1.0:
            raise ValueError("bounded-discrepancy cap must be finite and >= 1")
        self.priorities: list[float] = []
        self.groups: dict[float, set[int]] = collections.defaultdict(set)
        self.min_heap: list[float] = []
        self.max_heap: list[float] = []
        self.min_members: set[float] = set()
        self.max_members: set[float] = set()

    def _ensure_heap_key(self, priority: float) -> None:
        if priority not in self.min_members:
            heapq.heappush(self.min_heap, priority)
            self.min_members.add(priority)
        if priority not in self.max_members:
            heapq.heappush(self.max_heap, -priority)
            self.max_members.add(priority)

    def _clean_min(self) -> float:
        while self.min_heap and not self.groups[self.min_heap[0]]:
            stale = heapq.heappop(self.min_heap)
            self.min_members.discard(stale)
        return self.min_heap[0]

    def _clean_max(self) -> float:
        while self.max_heap and not self.groups[-self.max_heap[0]]:
            stale = -heapq.heappop(self.max_heap)
            self.max_members.discard(stale)
        return -self.max_heap[0]

    def _second_min(self, first: float) -> float | None:
        popped = heapq.heappop(self.min_heap)
        assert popped == first
        self.min_members.discard(first)
        while self.min_heap and not self.groups[self.min_heap[0]]:
            stale = heapq.heappop(self.min_heap)
            self.min_members.discard(stale)
        second = self.min_heap[0] if self.min_heap else None
        heapq.heappush(self.min_heap, first)
        self.min_members.add(first)
        return second

    def add(self, count: int, fair_clock_before: float) -> None:
        priority = float(fair_clock_before)
        for _ in range(int(count)):
            view_id = len(self.priorities)
            self.priorities.append(priority)
            self.groups[priority].add(view_id)
        if count:
            self._ensure_heap_key(priority)

    def _is_feasible(self, view_id: int) -> bool:
        priority = self.priorities[view_id]
        minimum = self._clean_min()
        maximum = self._clean_max()
        if priority == minimum and len(self.groups[minimum]) == 1:
            second = self._second_min(minimum)
            minimum_after = priority + 1.0 if second is None else min(second, priority + 1.0)
        else:
            minimum_after = minimum
        maximum_after = max(maximum, priority + 1.0)
        return maximum_after - minimum_after <= self.cap + 1.0e-12

    def draw(self) -> int:
        n = len(self.priorities)
        for _ in range(64):
            view_id = self.rng.randrange(n)
            if self._is_feasible(view_id):
                break
        else:
            feasible = [view for view in range(n) if self._is_feasible(view)]
            if not feasible:
                raise RuntimeError("bounded-discrepancy feasible set is empty")
            view_id = feasible[self.rng.randrange(len(feasible))]

        old_priority = self.priorities[view_id]
        new_priority = old_priority + 1.0
        self.groups[old_priority].remove(view_id)
        self.groups[new_priority].add(view_id)
        self.priorities[view_id] = new_priority
        self._ensure_heap_key(new_priority)
        return view_id


class ShuffleSubpool:
    """Growing/removable shuffled pool used by the active/archive mirror."""

    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.members: set[int] = set()
        self.epoch_members: set[int] = set()
        self.queue: list[int] = []

    def sync(self, members: Iterable[int]) -> None:
        new_members = set(members)
        self.queue = [view for view in self.queue if view in new_members]
        self.epoch_members.intersection_update(new_members)
        for view in sorted(new_members - self.epoch_members):
            position = self.rng.randrange(len(self.queue) + 1)
            self.queue.insert(position, view)
            self.epoch_members.add(view)
        self.members = new_members

    def draw(self) -> int:
        if not self.queue:
            self.queue = sorted(self.members)
            self.rng.shuffle(self.queue)
            self.epoch_members = set(self.members)
        return self.queue.pop()


class ActiveArchive:
    """Mirror of exp69's active/archive odds and subpool reshuffling."""

    def __init__(self, seed: int, *, active_size: int, demand: float):
        self.rng = random.Random(seed)
        self.active_pool = ShuffleSubpool(seed + 104729)
        self.archive_pool = ShuffleSubpool(seed + 130363)
        self.active_size = max(1, int(active_size))
        self.demand = max(0.0, float(demand))
        self.n = 0

    def add(self, count: int, fair_clock_before: float) -> None:
        del fair_clock_before
        self.n += int(count)
        split = max(0, self.n - self.active_size)
        self.archive_pool.sync(range(0, split))
        self.active_pool.sync(range(split, self.n))

    def draw(self) -> int:
        active_n = len(self.active_pool.members)
        archive_n = len(self.archive_pool.members)
        if archive_n == 0:
            choose_active = True
        elif active_n == 0:
            choose_active = False
        else:
            odds = active_n * (1.0 + self.demand) / archive_n
            p_active = odds / (1.0 + odds)
            choose_active = self.rng.random() < p_active
        return (
            self.active_pool.draw()
            if choose_active
            else self.archive_pool.draw()
        )


def scheduler_specs() -> list[tuple[str, dict[str, object]]]:
    return [
        ("uniform_iid", {"kind": "uniform"}),
        ("production_causal_shuffle", {"kind": "shuffle"}),
        ("active_archive_D0", {"kind": "active", "demand": 0.0}),
        ("exp69_active_archive_D1", {"kind": "active", "demand": 1.0}),
        ("exp69_active_archive_D2", {"kind": "active", "demand": 2.0}),
        ("raw_least_count", {"kind": "heap", "quota": False, "top_k": 1}),
        ("me_qarr", {"kind": "heap", "quota": True, "top_k": 1}),
        ("me_bds_C2", {"kind": "bounded_entropy", "cap": 2.0}),
        ("me_bds_C3", {"kind": "bounded_entropy", "cap": 3.0}),
        ("me_bds_C4", {"kind": "bounded_entropy", "cap": 4.0}),
    ]


def make_scheduler(name: str, spec: dict[str, object], seed: int):
    kind = spec["kind"]
    if kind == "uniform":
        return UniformIID(seed)
    if kind == "shuffle":
        return DynamicShuffle(seed)
    if kind == "active":
        return ActiveArchive(
            seed,
            active_size=16,
            demand=float(spec["demand"]),
        )
    if kind == "heap":
        return HeapFairScheduler(
            seed,
            quota_aware=bool(spec["quota"]),
            top_k=int(spec["top_k"]),
        )
    if kind == "bounded_entropy":
        return MaxEntropyBoundedDiscrepancy(seed, cap=float(spec["cap"]))
    raise ValueError(f"unknown scheduler kind: {kind!r} for {name}")


def simulate_selections(
    pattern: Pattern,
    spec_name: str,
    spec: dict[str, object],
    *,
    seed: int,
) -> np.ndarray:
    scheduler = make_scheduler(spec_name, spec, seed)
    selected = np.empty(pattern.steps, dtype=np.int64)
    eligible, _, _ = arrival_metadata(pattern)
    fair_clock = 0.0
    for t, arrival_count in enumerate(pattern.arrivals):
        if arrival_count:
            scheduler.add(int(arrival_count), fair_clock)
        fair_clock += 1.0 / float(eligible[t])
        selected[t] = scheduler.draw()
    return selected


def quota_at_end(
    pattern: Pattern,
    eligible: np.ndarray,
    base: np.ndarray,
) -> np.ndarray:
    del pattern
    return float(np.sum(1.0 / eligible)) - base


def fairness_metrics(
    selected: np.ndarray,
    quota: np.ndarray,
) -> dict[str, float]:
    counts = np.bincount(selected, minlength=quota.size).astype(np.float64)
    error = counts - quota
    quota_ge_1 = quota >= 1.0 - 1.0e-12
    quota_ge_2 = quota >= 2.0 - 1.0e-12
    return {
        "quota_rmse": float(np.sqrt(np.mean(error * error))),
        "quota_max_abs": float(np.max(np.abs(error))),
        "max_under_service": float(np.max(-error)),
        "max_over_service": float(np.max(error)),
        "zero_rate_quota_ge_1": float(
            np.mean(counts[quota_ge_1] < 1.0) if np.any(quota_ge_1) else 0.0
        ),
        "under_two_rate_quota_ge_2": float(
            np.mean(counts[quota_ge_2] < 2.0) if np.any(quota_ge_2) else 0.0
        ),
        "all_view_two_update_fraction": float(np.mean(counts >= 2.0)),
        "count_min": float(np.min(counts)),
        "count_max": float(np.max(counts)),
    }


def target_gradient_stream(
    eligible: np.ndarray,
    field: GradientField,
) -> np.ndarray:
    prefix = np.cumsum(field.signatures, axis=0)
    means = prefix[eligible - 1] / eligible[:, None]
    return field.amplitude[:, None] * means


def gradient_metrics_for_runs(
    selections: np.ndarray,
    eligible: np.ndarray,
    field: GradientField,
    *,
    window: int,
) -> dict[str, float]:
    target = target_gradient_stream(eligible, field)
    run_errors: list[np.ndarray] = []
    run_window_rms: list[float] = []
    run_window_max: list[float] = []
    for selected in selections:
        sampled = field.amplitude[:, None] * field.signatures[selected]
        difference = sampled - target
        run_errors.append(difference.mean(axis=0))
        blocks = []
        for start in range(0, difference.shape[0], window):
            block = difference[start : start + window]
            blocks.append(np.linalg.norm(block.mean(axis=0)) / field.scale)
        run_window_rms.append(float(np.sqrt(np.mean(np.square(blocks)))))
        run_window_max.append(float(np.max(blocks)))
    errors = np.stack(run_errors)
    normalized_norm = np.linalg.norm(errors, axis=1) / field.scale
    bias = np.linalg.norm(errors.mean(axis=0)) / field.scale
    return {
        "gradient_bias_pct": float(100.0 * bias),
        "gradient_final_rmse_pct": float(
            100.0 * np.sqrt(np.mean(normalized_norm * normalized_norm))
        ),
        "gradient_window_rmse_pct": float(100.0 * np.mean(run_window_rms)),
        "gradient_window_max_pct": float(100.0 * np.mean(run_window_max)),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def rank_aggregate(
    fairness_rows: list[dict[str, object]],
    gradient_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    metrics: dict[str, dict[str, list[float]]] = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )
    for row in fairness_rows:
        algorithm = str(row["algorithm"])
        pattern = str(row["pattern"])
        metrics[f"fair_rmse::{pattern}"][algorithm].append(float(row["quota_rmse"]))
        metrics[f"fair_max::{pattern}"][algorithm].append(float(row["quota_max_abs"]))
    for row in gradient_rows:
        algorithm = str(row["algorithm"])
        case = f"{row['pattern']}::{row['gradient_field']}"
        metrics[f"grad_final::{case}"][algorithm].append(
            float(row["gradient_final_rmse_pct"])
        )
        metrics[f"grad_window::{case}"][algorithm].append(
            float(row["gradient_window_rmse_pct"])
        )

    algorithms = [name for name, _ in scheduler_specs()]
    ranks: dict[str, list[float]] = {name: [] for name in algorithms}
    ratios: dict[str, list[float]] = {name: [] for name in algorithms}
    for case_values in metrics.values():
        averages = {
            name: float(np.mean(values)) for name, values in case_values.items()
        }
        ordered = sorted(averages, key=lambda name: (averages[name], name))
        for rank, name in enumerate(ordered, start=1):
            ranks[name].append(float(rank))
        baseline = max(averages["uniform_iid"], 1.0e-12)
        for name, value in averages.items():
            ratios[name].append(value / baseline)

    rows = []
    for name in algorithms:
        rows.append(
            {
                "algorithm": name,
                "mean_rank_lower_better": float(np.mean(ranks[name])),
                "median_ratio_to_uniform": float(np.median(ratios[name])),
                "worst_ratio_to_uniform": float(np.max(ratios[name])),
                "cases_ranked": len(ranks[name]),
            }
        )
    rows.sort(key=lambda row: (row["mean_rank_lower_better"], row["algorithm"]))
    return rows


def plot_tradeoff(
    output: Path,
    fairness_rows: list[dict[str, object]],
    gradient_rows: list[dict[str, object]],
) -> None:
    fair = collections.defaultdict(list)
    mix = collections.defaultdict(list)
    for row in fairness_rows:
        fair[str(row["algorithm"])].append(float(row["quota_rmse"]))
    for row in gradient_rows:
        mix[str(row["algorithm"])].append(float(row["gradient_window_rmse_pct"]))

    fig, ax = plt.subplots(figsize=(10.5, 7.0))
    for algorithm, values in fair.items():
        x = float(np.mean(values))
        y = float(np.mean(mix[algorithm]))
        marker = "*" if algorithm == "me_qarr" else "o"
        size = 180 if algorithm == "me_qarr" else 65
        ax.scatter(x, y, s=size, marker=marker)
        ax.annotate(algorithm, (x, y), xytext=(5, 4), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Age-adjusted quota RMSE per view (lower is better)")
    ax.set_ylabel("256-step gradient mixing RMSE, % (lower is better)")
    ax.set_title("Long-horizon scheduler trade-off across all simulated cases")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_representative_counts(
    output: Path,
    pattern: Pattern,
    sequences: dict[str, np.ndarray],
) -> None:
    eligible, _, base = arrival_metadata(pattern)
    quota = quota_at_end(pattern, eligible, base)
    algorithms = [
        "uniform_iid",
        "production_causal_shuffle",
        "exp69_active_archive_D1",
        "raw_least_count",
        "me_qarr",
    ]
    fig, axes = plt.subplots(len(algorithms), 1, figsize=(11.5, 12.0), sharex=True)
    for ax, algorithm in zip(axes, algorithms):
        counts = np.bincount(sequences[algorithm], minlength=quota.size)
        ax.plot(quota, color="black", linewidth=1.6, label="uniform age-adjusted quota")
        ax.scatter(np.arange(quota.size), counts, s=5, alpha=0.65, label="actual updates")
        ax.set_ylabel(algorithm, fontsize=8)
        ax.grid(alpha=0.18)
    axes[0].legend(loc="upper right", fontsize=8)
    axes[-1].set_xlabel("View ID (arrival order)")
    fig.suptitle(f"Actual service vs. fair quota: {pattern.name}, seed 0")
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.98))
    fig.savefig(output, dpi=180)
    plt.close(fig)


def deficit_trace(pattern: Pattern, selected: np.ndarray, stride: int = 25):
    eligible, arrival_step, base = arrival_metadata(pattern)
    counts = np.zeros(pattern.final_views, dtype=np.float64)
    times = []
    max_abs = []
    rms = []
    fair_clock = 0.0
    for t, chosen in enumerate(selected):
        fair_clock += 1.0 / float(eligible[t])
        counts[chosen] += 1.0
        if t % stride == 0 or t == pattern.steps - 1:
            n = int(eligible[t])
            quota = fair_clock - base[:n]
            error = counts[:n] - quota
            times.append(t)
            max_abs.append(float(np.max(np.abs(error))))
            rms.append(float(np.sqrt(np.mean(error * error))))
    return np.asarray(times), np.asarray(max_abs), np.asarray(rms)


def plot_deficit(
    output: Path,
    pattern: Pattern,
    sequences: dict[str, np.ndarray],
) -> None:
    algorithms = [
        "uniform_iid",
        "production_causal_shuffle",
        "exp69_active_archive_D1",
        "me_qarr",
        "me_bds_C2",
    ]
    fig, axes = plt.subplots(2, 1, figsize=(11.0, 8.0), sharex=True)
    for algorithm in algorithms:
        t, max_abs, rms = deficit_trace(pattern, sequences[algorithm])
        axes[0].plot(t, max_abs, label=algorithm)
        axes[1].plot(t, rms, label=algorithm)
    axes[0].set_ylabel("max |actual - quota|")
    axes[1].set_ylabel("quota RMSE")
    axes[1].set_xlabel("Optimizer update step")
    axes[0].set_title(f"Exposure discrepancy through time: {pattern.name}, seed 0")
    for ax in axes:
        ax.grid(alpha=0.25)
    axes[0].legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def self_test() -> None:
    # Fixed pool: ME-QARR must be a permutation in every complete epoch.
    arrivals = np.zeros(64, dtype=np.int64)
    arrivals[0] = 8
    pattern = Pattern("test_static", arrivals)
    sequence = simulate_selections(
        pattern,
        "me_qarr",
        {"kind": "heap", "quota": True, "top_k": 1},
        seed=7,
    )
    for start in range(0, 64, 8):
        assert len(set(sequence[start : start + 8])) == 8

    # Arbitrary growing pool: largest-deficit ME-QARR discrepancy stays below one.
    arrivals = np.zeros(1000, dtype=np.int64)
    arrivals[0] = 7
    arrivals[3::7] = 2
    pattern = Pattern("test_growth", arrivals)
    eligible, _, base = arrival_metadata(pattern)
    sequence = simulate_selections(
        pattern,
        "me_qarr",
        {"kind": "heap", "quota": True, "top_k": 1},
        seed=11,
    )
    quota = quota_at_end(pattern, eligible, base)
    counts = np.bincount(sequence, minlength=quota.size)
    assert float(np.max(np.abs(counts - quota))) < 1.0 + 1.0e-10

    # ME-BDS(C) must retain its deterministic discrepancy cap while allowing
    # every currently safe action to participate in a uniform draw.
    for cap in (2.0, 3.0, 4.0):
        sequence_bds = simulate_selections(
            pattern,
            f"me_bds_C{int(cap)}",
            {"kind": "bounded_entropy", "cap": cap},
            seed=13,
        )
        counts_bds = np.bincount(sequence_bds, minlength=quota.size)
        assert float(np.max(np.abs(counts_bds - quota))) < cap + 1.0e-10

    # Fixed-gradient accounting identity used in the report.
    rng = np.random.default_rng(2)
    gradients = rng.normal(size=(pattern.final_views, 5))
    prefix = np.cumsum(gradients, axis=0)
    target_sum = np.sum(prefix[eligible - 1] / eligible[:, None], axis=0)
    sampled_sum = np.sum(gradients[sequence], axis=0)
    count_form = np.sum((counts - quota)[:, None] * gradients, axis=0)
    assert np.allclose(sampled_sum - target_sum, count_form, atol=1.0e-9)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=12000)
    parser.add_argument("--seeds", type=int, default=48)
    parser.add_argument("--gradient-dim", type=int, default=8)
    parser.add_argument("--window", type=int, default=256)
    parser.add_argument("--base-seed", type=int, default=690704)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).with_name("view_scheduler_long_horizon_outputs"),
    )
    parser.add_argument("--self-test-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    self_test()
    if args.self_test_only:
        print("self-test: PASS")
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)
    patterns = make_patterns(args.steps)
    specs = scheduler_specs()
    fairness_rows: list[dict[str, object]] = []
    gradient_rows: list[dict[str, object]] = []
    representative_sequences: dict[str, dict[str, np.ndarray]] = {}

    for pattern_index, pattern in enumerate(patterns):
        eligible, arrival_step, base = arrival_metadata(pattern)
        quota = quota_at_end(pattern, eligible, base)
        fields = make_gradient_fields(
            pattern,
            eligible,
            arrival_step,
            dim=args.gradient_dim,
            seed=args.base_seed + 100003 * pattern_index,
        )
        representative_sequences[pattern.name] = {}
        for algorithm_index, (algorithm, spec) in enumerate(specs):
            sequences = []
            for seed in range(args.seeds):
                run_seed = args.base_seed + seed + 1009 * algorithm_index
                selected = simulate_selections(
                    pattern,
                    algorithm,
                    spec,
                    seed=run_seed,
                )
                sequences.append(selected)
                row: dict[str, object] = {
                    "pattern": pattern.name,
                    "algorithm": algorithm,
                    "seed": seed,
                    "steps": pattern.steps,
                    "final_views": pattern.final_views,
                }
                row.update(fairness_metrics(selected, quota))
                fairness_rows.append(row)
            sequence_array = np.stack(sequences)
            representative_sequences[pattern.name][algorithm] = sequence_array[0]
            for field in fields:
                row = {
                    "pattern": pattern.name,
                    "gradient_field": field.name,
                    "algorithm": algorithm,
                    "seeds": args.seeds,
                    "steps": pattern.steps,
                    "final_views": pattern.final_views,
                }
                row.update(
                    gradient_metrics_for_runs(
                        sequence_array,
                        eligible,
                        field,
                        window=args.window,
                    )
                )
                gradient_rows.append(row)
        print(
            f"completed {pattern.name}: steps={pattern.steps}, "
            f"views={pattern.final_views}, algorithms={len(specs)}"
        )

    ranking = rank_aggregate(fairness_rows, gradient_rows)
    write_csv(args.output_dir / "fairness_runs.csv", fairness_rows)
    write_csv(args.output_dir / "gradient_cases.csv", gradient_rows)
    write_csv(args.output_dir / "aggregate_ranking.csv", ranking)
    plot_tradeoff(args.output_dir / "tradeoff.png", fairness_rows, gradient_rows)
    representative_name = "accelerating_growth"
    plot_representative_counts(
        args.output_dir / "representative_counts.png",
        next(pattern for pattern in patterns if pattern.name == representative_name),
        representative_sequences[representative_name],
    )
    plot_deficit(
        args.output_dir / "representative_deficit.png",
        next(pattern for pattern in patterns if pattern.name == representative_name),
        representative_sequences[representative_name],
    )

    summary = {
        "configuration": {
            "steps": args.steps,
            "seeds": args.seeds,
            "gradient_dim": args.gradient_dim,
            "window": args.window,
            "base_seed": args.base_seed,
            "patterns": [
                {
                    "name": pattern.name,
                    "final_views": pattern.final_views,
                }
                for pattern in patterns
            ],
            "algorithms": [name for name, _ in specs],
        },
        "ranking": ranking,
        "winner_by_mean_rank": ranking[0]["algorithm"],
        "me_qarr_hard_invariant": "max_i |n_i(T)-q_i(T)| < 1",
        "me_qarr_entropy_claim": (
            "At each step, uniform choice among equal maximum deficits maximizes "
            "conditional Shannon entropy over all actions preserving the hard "
            "discrepancy invariant; for a static pool it is exact uniform random "
            "reshuffling over all permutations."
        ),
        "me_bds_entropy_claim": (
            "ME-BDS(C) samples uniformly from every next action preserving "
            "tag-span <= C, hence maximizes one-step conditional Shannon entropy "
            "subject to the deterministic exposure-discrepancy cap."
        ),
        "scope": (
            "Scheduler-only synthetic-gradient simulation; this is not a 3DGS "
            "quality or convergence claim."
        ),
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary["ranking"][:5], indent=2))
    print(f"outputs: {args.output_dir}")


if __name__ == "__main__":
    main()
