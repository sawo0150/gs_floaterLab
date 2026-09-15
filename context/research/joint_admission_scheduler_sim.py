#!/usr/bin/env python3
"""Joint admission/scheduling simulation for a growing causal view pool.

This succeeds ``view_scheduler_long_horizon_sim.py`` with a method-agnostic
problem definition:

1. terminal view counts should be as equal as causally possible;
2. admissions should track completed GPU work, independent of pool size; and
3. each logical minibatch should resemble a full-pool uniform random shuffle.

The main candidate is entropy-regularized count balancing (ERCB). At a batch
boundary, with lifetime selection count n_i, it samples without replacement

    p(i | remaining) proportional to exp(-beta * n_i).

beta=0 is exact full-pool uniform shuffling; beta=infinity is randomized
least-count. A deterministic GPU-token controller admits one frame per kappa
completed optimizer updates. The simulation sweeps beta and kappa.

This models selection/work allocation only; it does not predict 3DGS PSNR.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# The operating point is selected by feasibility, not by a weighted sum whose
# answer can be changed arbitrarily by rescaling one metric.  These thresholds
# are intentionally exposed in the output JSON and report.
FAIRNESS_NRMSE_MAX = 0.10
JAIN_REGRET_MAX = 0.01
COHORT_RATIO_MIN = 0.90
COHORT_RATIO_MAX = 1.10
ENTROPY_RATIO_MIN = 0.95
GRADIENT_RATIO_MEAN_MAX = 2.0
GRADIENT_RATIO_FIELD_MAX = 3.0
TEMPORAL_W1_RATIO_MAX = 2.0


@dataclass(frozen=True)
class Scenario:
    name: str
    steps: int
    initial_views: int
    batch_size: int


@dataclass(frozen=True)
class Policy:
    name: str
    sampler: str
    admission: str = "token"
    beta: float | None = None
    active_size: int = 16
    active_multiplier: float = 3.0


@dataclass(frozen=True)
class GradientField:
    name: str
    values: np.ndarray
    prefix: np.ndarray
    prefix_norm2: np.ndarray


def parse_float_list(text: str) -> list[float]:
    values: list[float] = []
    for item in text.split(","):
        token = item.strip().lower()
        if not token:
            continue
        values.append(math.inf if token in {"inf", "infinity"} else float(token))
    if not values:
        raise ValueError("expected at least one numeric value")
    return values


def parse_int_list(text: str) -> list[int]:
    values = [int(item.strip()) for item in text.split(",") if item.strip()]
    if not values or any(value <= 0 for value in values):
        raise ValueError("expected positive comma-separated integers")
    return values


def beta_label(beta: float) -> str:
    if math.isinf(beta):
        return "inf"
    return f"{beta:g}".replace(".", "p")


def default_scenarios(steps: int, batch_size: int) -> list[Scenario]:
    if batch_size < 2:
        raise ValueError("batch size must be at least two")
    return [
        Scenario("short_stream", max(batch_size, steps // 2), batch_size, batch_size),
        Scenario("base_stream", steps, batch_size, batch_size),
        Scenario("long_stream", steps + steps // 2, batch_size, batch_size),
    ]


def policies_for_betas(betas: Iterable[float], include_controls: bool) -> list[Policy]:
    betas = list(betas)
    # Temporal/cohort mixing metrics are normalized to the exact uniform
    # full-pool shuffle.  Always carry that reference even for a narrow beta
    # refinement sweep whose CLI list omitted zero.
    if not any(beta == 0.0 for beta in betas):
        betas.insert(0, 0.0)
    policies: list[Policy] = []
    for beta in betas:
        if math.isinf(beta):
            policies.append(Policy("ercb_beta_inf", "least_count", beta=beta))
        elif beta == 0.0:
            policies.append(Policy("ercb_beta_0", "softmax", beta=0.0))
        else:
            policies.append(
                Policy(f"ercb_beta_{beta_label(beta)}", "softmax", beta=beta)
            )
    if include_controls:
        policies.extend(
            [
                Policy("active_bonus3", "active_bonus"),
                Policy(
                    "gate_r2_uniform", "softmax", admission="gate_r2", beta=0.0
                ),
                Policy(
                    "gate_r2_active_bonus3", "active_bonus", admission="gate_r2"
                ),
            ]
        )
    unique: dict[str, Policy] = {}
    for policy in policies:
        unique[policy.name] = policy
    return list(unique.values())


def make_gradient_fields(n: int, dim: int, seed: int) -> list[GradientField]:
    rng = np.random.default_rng(seed)
    x = (np.arange(n, dtype=np.float64) + 0.5) / float(n)
    iid = rng.normal(size=(n, dim))
    basis = np.stack(
        [
            np.sin(2.0 * np.pi * x),
            np.cos(2.0 * np.pi * x),
            np.sin(4.0 * np.pi * x),
            np.cos(4.0 * np.pi * x),
            2.0 * x - 1.0,
            np.tanh(10.0 * (x - 0.5)),
        ],
        axis=1,
    )
    smooth = basis @ rng.normal(size=(basis.shape[1], dim))
    smooth += 0.08 * rng.normal(size=(n, dim))
    direction = rng.normal(size=dim)
    direction /= max(np.linalg.norm(direction), 1.0e-12)
    labels = np.where(x < 0.5, -1.0, 1.0)
    regime = 2.5 * labels[:, None] * direction[None, :]
    regime += 0.15 * rng.normal(size=(n, dim))

    fields = []
    for name, values in (
        ("iid", iid),
        ("smooth_order", smooth),
        ("abrupt_regime", regime),
    ):
        centered = values - values.mean(axis=0, keepdims=True)
        scale = math.sqrt(float(np.mean(np.sum(centered * centered, axis=1))))
        normalized = values / max(scale, 1.0e-12)
        fields.append(
            GradientField(
                name=name,
                values=normalized,
                prefix=np.cumsum(normalized, axis=0),
                prefix_norm2=np.cumsum(np.sum(normalized * normalized, axis=1)),
            )
        )
    return fields


def _gumbel_top_k(
    log_weights: np.ndarray, take: int, rng: np.random.Generator
) -> tuple[np.ndarray, float]:
    """Draw an ordered Plackett-Luce sample and return sampled surprisal."""
    n = int(log_weights.size)
    if not 0 < take <= n:
        raise ValueError(f"invalid take={take} for n={n}")
    u = np.clip(rng.random(n), 1.0e-15, 1.0 - 1.0e-15)
    scores = log_weights - np.log(-np.log(u))
    if take == n:
        chosen = np.argsort(scores)[::-1]
    else:
        frontier = np.argpartition(scores, n - take)[n - take :]
        chosen = frontier[np.argsort(scores[frontier])[::-1]]
    weights = np.exp(log_weights)
    outside = np.ones(n, dtype=bool)
    outside[chosen] = False
    outside_sum = np.sum(weights[outside], dtype=np.longdouble)
    chosen_weights = weights[chosen].astype(np.longdouble, copy=False)
    chosen_suffix = np.cumsum(chosen_weights[::-1], dtype=np.longdouble)[::-1]
    negative_log_probability = 0.0
    for position, view_id in enumerate(chosen):
        weight = float(weights[view_id])
        denominator = float(outside_sum + chosen_suffix[position])
        if weight <= 0.0 or denominator <= 0.0:
            raise FloatingPointError("softmax weight underflowed to an empty support")
        negative_log_probability += math.log(denominator) - math.log(weight)
    return chosen.astype(np.int64, copy=False), negative_log_probability


def _least_count_batch(
    counts: np.ndarray, take: int, rng: np.random.Generator
) -> tuple[np.ndarray, float]:
    """Random order within successive minimum-count groups."""
    order = np.argsort(counts, kind="stable")
    chosen: list[int] = []
    negative_log_probability = 0.0
    cursor = 0
    while len(chosen) < take:
        value = counts[order[cursor]]
        end = cursor + 1
        while end < order.size and counts[order[end]] == value:
            end += 1
        group = order[cursor:end].copy()
        rng.shuffle(group)
        group_take = min(take - len(chosen), int(group.size))
        chosen.extend(int(view_id) for view_id in group[:group_take])
        negative_log_probability += math.lgamma(group.size + 1.0)
        negative_log_probability -= math.lgamma(group.size - group_take + 1.0)
        cursor = end
    return np.asarray(chosen, dtype=np.int64), negative_log_probability


def sample_batch(
    policy: Policy,
    counts: np.ndarray,
    take: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, float]:
    n = int(counts.size)
    if take > n:
        raise ValueError("logical minibatch cannot exceed the admitted pool")
    if policy.sampler == "least_count":
        return _least_count_batch(counts, take, rng)
    if policy.sampler == "softmax":
        beta = float(policy.beta or 0.0)
        shifted_counts = counts.astype(np.float64) - float(np.min(counts))
        log_weights = np.maximum(-beta * shifted_counts, -700.0)
        return _gumbel_top_k(log_weights, take, rng)
    if policy.sampler == "active_bonus":
        log_weights = np.zeros(n, dtype=np.float64)
        active_start = max(0, n - policy.active_size)
        log_weights[active_start:] = math.log(policy.active_multiplier)
        return _gumbel_top_k(log_weights, take, rng)
    raise ValueError(f"unknown sampler {policy.sampler!r}")


def jain_index(counts: np.ndarray) -> float:
    values = counts.astype(np.float64)
    denominator = float(values.size * np.sum(values * values))
    if denominator == 0.0:
        return 1.0
    return float(np.sum(values) ** 2 / denominator)


def temporal_wasserstein(chosen: np.ndarray, n: int) -> float:
    observed = (np.sort(chosen.astype(np.float64)) + 0.5) / float(n)
    target = (np.arange(chosen.size, dtype=np.float64) + 0.5) / float(chosen.size)
    return float(np.mean(np.abs(observed - target)))


def cohort_entropy(chosen: np.ndarray, n: int, bins: int = 8) -> float:
    actual_bins = min(bins, n, chosen.size)
    labels = np.minimum(actual_bins - 1, (chosen * actual_bins) // n)
    histogram = np.bincount(labels, minlength=actual_bins).astype(np.float64)
    probabilities = histogram[histogram > 0.0] / float(chosen.size)
    if actual_bins <= 1:
        return 1.0
    return float(-np.sum(probabilities * np.log(probabilities)) / math.log(actual_bins))


def ideal_batch_gradient_mse(field: GradientField, n: int, take: int) -> float:
    if take >= n:
        return 0.0
    mean = field.prefix[n - 1] / float(n)
    mean_norm2 = float(np.dot(mean, mean))
    population_variance = max(
        0.0, float(field.prefix_norm2[n - 1]) / float(n) - mean_norm2
    )
    return (n - take) / float(take * (n - 1)) * population_variance


def causal_balancing_reference(
    initial_views: int, additions: list[int], batch_sizes: list[int]
) -> np.ndarray:
    """Causal count-leveling limit under the same admission trace.

    Every unit of service increments a currently minimum count, with no duplicate
    inside a logical minibatch. Random tie choices cannot change the sorted
    terminal count vector, so deterministic IDs suffice here.
    """
    total_views = initial_views + int(sum(additions))
    counts = np.zeros(total_views, dtype=np.int64)
    admitted = initial_views
    for batch_index, take in enumerate(batch_sizes):
        admitted += additions[batch_index]
        local = counts[:admitted]
        chosen = np.lexsort((np.arange(admitted), local))[:take]
        counts[chosen] += 1
    admitted += additions[len(batch_sizes)]
    if admitted != total_views:
        raise AssertionError("reference admission accounting mismatch")
    return counts


def pool_rate_cv(
    completed: np.ndarray,
    admitted_extra: np.ndarray,
    pool_size: np.ndarray,
    bins: int = 4,
) -> float:
    if completed.size < 3 or admitted_extra[-1] <= 0:
        return 0.0
    window = max(2, (completed.size - 1) // 24)
    rates: list[float] = []
    pools: list[float] = []
    for start in range(0, completed.size - 1, window):
        end = min(completed.size - 1, start + window)
        delta_s = float(completed[end] - completed[start])
        if delta_s <= 0.0:
            continue
        rates.append(float(admitted_extra[end] - admitted_extra[start]) / delta_s)
        pools.append(float(np.mean(pool_size[start : end + 1])))
    if len(rates) < bins:
        return 0.0
    pools_array = np.asarray(pools)
    rates_array = np.asarray(rates)
    edges = np.quantile(pools_array, np.linspace(0.0, 1.0, bins + 1))
    means = []
    for bin_index in range(bins):
        if bin_index == bins - 1:
            mask = (pools_array >= edges[bin_index]) & (
                pools_array <= edges[bin_index + 1]
            )
        else:
            mask = (pools_array >= edges[bin_index]) & (
                pools_array < edges[bin_index + 1]
            )
        if np.any(mask):
            means.append(float(np.mean(rates_array[mask])))
    overall = float(np.mean(means)) if means else 0.0
    if overall <= 0.0:
        return math.inf
    return float(np.std(means) / overall)


def simulate_run(
    scenario: Scenario,
    kappa: int,
    policy: Policy,
    seed: int,
    fields: list[GradientField],
) -> dict[str, float | int | str]:
    rng = np.random.default_rng(seed)
    max_views = scenario.initial_views + scenario.steps // kappa + 2
    counts = np.zeros(max_views, dtype=np.int64)
    arrival_updates = np.full(max_views, -1, dtype=np.int64)
    arrival_updates[: scenario.initial_views] = 0
    admitted = scenario.initial_views
    completed = 0
    additions: list[int] = []
    batch_sizes: list[int] = []

    checkpoint_completed: list[int] = []
    checkpoint_target: list[int] = []
    checkpoint_actual: list[int] = []
    checkpoint_pool: list[int] = []
    entropy_observed = 0.0
    entropy_ideal = 0.0
    temporal_total = 0.0
    cohort_entropy_total = 0.0
    batches_measured = 0
    gradient_error = {field.name: 0.0 for field in fields}
    gradient_ideal = {field.name: 0.0 for field in fields}

    def admit_at_boundary() -> int:
        nonlocal admitted
        target = scenario.initial_views + completed // kappa
        entitled = max(0, target - admitted)
        add_count = 0
        if entitled:
            if policy.admission == "token":
                add_count = entitled
            elif policy.admission == "gate_r2":
                mature = admitted == 0 or int(np.min(counts[:admitted])) >= 2
                add_count = 1 if mature else 0
            else:
                raise ValueError(f"unknown admission policy {policy.admission!r}")
        old_admitted = admitted
        admitted += add_count
        arrival_updates[old_admitted:admitted] = completed
        checkpoint_completed.append(completed)
        checkpoint_target.append(target - scenario.initial_views)
        checkpoint_actual.append(admitted - scenario.initial_views)
        checkpoint_pool.append(admitted)
        return add_count

    while completed < scenario.steps:
        additions.append(admit_at_boundary())
        take = min(scenario.batch_size, scenario.steps - completed)
        if admitted < take:
            raise RuntimeError(
                f"scenario {scenario.name} has pool {admitted} smaller than batch {take}"
            )
        chosen, negative_log_probability = sample_batch(
            policy, counts[:admitted], take, rng
        )
        ideal_entropy = math.lgamma(admitted + 1.0) - math.lgamma(
            admitted - take + 1.0
        )
        entropy_observed += negative_log_probability
        entropy_ideal += ideal_entropy
        temporal_total += temporal_wasserstein(chosen, admitted)
        cohort_entropy_total += cohort_entropy(chosen, admitted)
        batches_measured += 1

        for field in fields:
            pool_mean = field.prefix[admitted - 1] / float(admitted)
            batch_mean = np.mean(field.values[chosen], axis=0)
            difference = batch_mean - pool_mean
            gradient_error[field.name] += float(np.dot(difference, difference))
            gradient_ideal[field.name] += ideal_batch_gradient_mse(
                field, admitted, take
            )

        counts[chosen] += 1
        batch_sizes.append(take)
        completed += take

    # The terminal boundary is part of an anytime/zero-tail checkpoint: credits
    # earned by the last batch may admit frames, but no future service is invented.
    additions.append(admit_at_boundary())
    final_counts = counts[:admitted].copy()
    oracle_counts = causal_balancing_reference(
        scenario.initial_views, additions, batch_sizes
    )
    if oracle_counts.size != final_counts.size:
        raise AssertionError("oracle and policy final pools differ")

    mean_count = float(np.mean(final_counts))
    # Integer equalization can have several equivalent optima that differ only
    # in which tied view gets the final +1. Compare the optimally matched count
    # multisets; arrival-cohort asymmetry is measured separately below.
    fairness_rmse_updates = float(
        np.sqrt(
            np.mean(
                (
                    np.sort(final_counts).astype(np.float64)
                    - np.sort(oracle_counts).astype(np.float64)
                )
                ** 2
            )
        )
    )
    fairness_nrmse = fairness_rmse_updates / max(mean_count, 1.0e-12)
    final_jain = jain_index(final_counts)
    oracle_jain = jain_index(oracle_counts)
    cohort_size = max(1, min(scenario.initial_views, admitted // 10))
    first_mean = float(np.mean(final_counts[:cohort_size]))
    new_view_ids = np.flatnonzero(arrival_updates[:admitted] > 0)
    middle_candidates = (
        new_view_ids if new_view_ids.size > 0 else np.arange(admitted)
    )
    middle_order = np.argsort(
        np.abs(
            arrival_updates[middle_candidates].astype(np.float64)
            - 0.5 * scenario.steps
        ),
        kind="stable",
    )
    middle_ids = middle_candidates[
        middle_order[: min(cohort_size, middle_candidates.size)]
    ]
    middle_mean = float(np.mean(final_counts[middle_ids]))
    cohort_mid_first_ratio = middle_mean / max(first_mean, 1.0e-12)
    oracle_first_mean = float(np.mean(oracle_counts[:cohort_size]))
    oracle_middle_mean = float(np.mean(oracle_counts[middle_ids]))
    oracle_cohort_mid_first_ratio = oracle_middle_mean / max(
        oracle_first_mean, 1.0e-12
    )
    middle_arrival_fraction = float(
        np.mean(arrival_updates[middle_ids]) / max(1, scenario.steps)
    )

    completed_array = np.asarray(checkpoint_completed, dtype=np.float64)
    target_array = np.asarray(checkpoint_target, dtype=np.float64)
    actual_array = np.asarray(checkpoint_actual, dtype=np.float64)
    pool_array = np.asarray(checkpoint_pool, dtype=np.float64)
    admission_error = actual_array - target_array
    final_target = max(1.0, float(target_array[-1]))

    row: dict[str, float | int | str] = {
        "scenario": scenario.name,
        "algorithm": policy.name,
        "sampler": policy.sampler,
        "admission": policy.admission,
        "beta": "inf"
        if policy.beta is not None and math.isinf(policy.beta)
        else ("" if policy.beta is None else float(policy.beta)),
        "kappa": kappa,
        "seed": seed,
        "steps": scenario.steps,
        "batch_size": scenario.batch_size,
        "initial_views": scenario.initial_views,
        "final_views": admitted,
        "target_final_views": scenario.initial_views + int(target_array[-1]),
        "mean_count": mean_count,
        "count_std": float(np.std(final_counts)),
        "count_min": int(np.min(final_counts)),
        "count_max": int(np.max(final_counts)),
        "jain_index": final_jain,
        "oracle_jain_index": oracle_jain,
        "jain_regret": max(0.0, oracle_jain - final_jain),
        "fairness_rmse_updates": fairness_rmse_updates,
        "fairness_nrmse": fairness_nrmse,
        "cohort_mid_first_ratio": cohort_mid_first_ratio,
        "oracle_cohort_mid_first_ratio": oracle_cohort_mid_first_ratio,
        "first_cohort_mean_count": first_mean,
        "middle_cohort_mean_count": middle_mean,
        "oracle_first_cohort_mean_count": oracle_first_mean,
        "oracle_middle_cohort_mean_count": oracle_middle_mean,
        "middle_cohort_arrival_fraction": middle_arrival_fraction,
        "admission_tracking_rmse": float(
            np.sqrt(np.mean(admission_error**2))
        ),
        "admission_tracking_nrmse": float(
            np.sqrt(np.mean(admission_error**2)) / final_target
        ),
        "admission_max_lag": float(np.max(-admission_error)),
        "admission_max_overshoot": float(np.max(admission_error)),
        "admission_rate_ratio": float(actual_array[-1] / final_target),
        "admission_pool_rate_cv": pool_rate_cv(
            completed_array, actual_array, pool_array
        ),
        "budget_violation": float(np.max(np.maximum(admission_error, 0.0))),
        "entropy_ratio": float(
            entropy_observed / max(entropy_ideal, 1.0e-12)
        ),
        "shuffle_kl_norm": float(
            (entropy_ideal - entropy_observed) / max(entropy_ideal, 1.0e-12)
        ),
        "duplicate_rate": 0.0,
        "temporal_w1": temporal_total / max(1, batches_measured),
        "cohort_entropy": cohort_entropy_total / max(1, batches_measured),
    }
    gradient_ratios = []
    for field in fields:
        ratio = gradient_error[field.name] / max(
            gradient_ideal[field.name], 1.0e-12
        )
        row[f"gradient_ratio_{field.name}"] = float(ratio)
        gradient_ratios.append(float(ratio))
    row["gradient_ratio_mean"] = float(np.mean(gradient_ratios))
    row["gradient_ratio_worst"] = float(np.max(gradient_ratios))
    return row


def aggregate_rows(
    rows: list[dict[str, float | int | str]],
) -> list[dict[str, object]]:
    grouped: dict[
        tuple[str, int, str], list[dict[str, float | int | str]]
    ] = collections.defaultdict(list)
    for row in rows:
        key = (
            str(row["scenario"]),
            int(row["kappa"]),
            str(row["algorithm"]),
        )
        grouped[key].append(row)

    identity = {
        "scenario",
        "algorithm",
        "sampler",
        "admission",
        "beta",
        "kappa",
        "seed",
    }
    aggregates: list[dict[str, object]] = []
    for (scenario, kappa, algorithm), group in grouped.items():
        first = group[0]
        result: dict[str, object] = {
            "scenario": scenario,
            "kappa": kappa,
            "algorithm": algorithm,
            "sampler": first["sampler"],
            "admission": first["admission"],
            "beta": first["beta"],
            "seeds": len(group),
        }
        numeric_keys = [
            key
            for key, value in first.items()
            if key not in identity and isinstance(value, (int, float))
        ]
        for key in numeric_keys:
            values = np.asarray(
                [float(row[key]) for row in group], dtype=np.float64
            )
            result[f"{key}_mean"] = float(np.mean(values))
            result[f"{key}_q05"] = float(np.quantile(values, 0.05))
            result[f"{key}_p95"] = float(np.quantile(values, 0.95))
            result[f"{key}_worst"] = float(np.max(values))
        aggregates.append(result)
    aggregates.sort(
        key=lambda row: (row["scenario"], row["kappa"], row["algorithm"])
    )
    return aggregates


def add_reference_ratios(aggregates: list[dict[str, object]]) -> None:
    references: dict[tuple[str, int], dict[str, object]] = {}
    for row in aggregates:
        if row["algorithm"] == "ercb_beta_0" and row["admission"] == "token":
            references[(str(row["scenario"]), int(row["kappa"]))] = row
    for row in aggregates:
        reference = references.get(
            (str(row["scenario"]), int(row["kappa"]))
        )
        if reference is None:
            row["temporal_w1_to_uniform"] = math.nan
            row["cohort_entropy_to_uniform"] = math.nan
            continue
        row["temporal_w1_to_uniform"] = float(
            row["temporal_w1_mean"]
        ) / max(float(reference["temporal_w1_mean"]), 1.0e-12)
        row["temporal_w1_to_uniform_p95"] = float(
            row["temporal_w1_p95"]
        ) / max(float(reference["temporal_w1_mean"]), 1.0e-12)
        row["cohort_entropy_to_uniform"] = float(
            row["cohort_entropy_mean"]
        ) / max(float(reference["cohort_entropy_mean"]), 1.0e-12)


def robust_beta_summary(
    aggregates: list[dict[str, object]], kappas: list[int]
) -> tuple[list[dict[str, object]], dict[str, object]]:
    ercb = [
        row
        for row in aggregates
        if str(row["algorithm"]).startswith("ercb_beta_")
        and row["admission"] == "token"
    ]
    grouped: dict[
        tuple[int, str], list[dict[str, object]]
    ] = collections.defaultdict(list)
    for row in ercb:
        grouped[(int(row["kappa"]), str(row["beta"]))].append(row)

    summaries: list[dict[str, object]] = []
    for (kappa, beta), group in grouped.items():
        summaries.append(
            {
                "kappa": kappa,
                "beta": beta,
                "algorithm": group[0]["algorithm"],
                "scenarios": len(group),
                "fairness_nrmse_worst_scenario": max(
                    float(row["fairness_nrmse_p95"]) for row in group
                ),
                "fairness_rmse_updates_worst_scenario": max(
                    float(row["fairness_rmse_updates_p95"]) for row in group
                ),
                "jain_min_scenario": min(
                    float(row["jain_index_q05"]) for row in group
                ),
                "jain_regret_worst_scenario": max(
                    float(row["jain_regret_p95"]) for row in group
                ),
                "cohort_ratio_min_scenario": min(
                    float(row["cohort_mid_first_ratio_q05"]) for row in group
                ),
                "cohort_ratio_max_scenario": max(
                    float(row["cohort_mid_first_ratio_p95"]) for row in group
                ),
                "oracle_cohort_ratio_min_scenario": min(
                    float(row["oracle_cohort_mid_first_ratio_q05"])
                    for row in group
                ),
                "oracle_cohort_ratio_max_scenario": max(
                    float(row["oracle_cohort_mid_first_ratio_p95"])
                    for row in group
                ),
                "entropy_ratio_min_scenario": min(
                    float(row["entropy_ratio_q05"]) for row in group
                ),
                "shuffle_kl_worst_scenario": max(
                    float(row["shuffle_kl_norm_mean"]) for row in group
                ),
                "gradient_ratio_mean_worst_scenario": max(
                    float(row["gradient_ratio_mean_p95"]) for row in group
                ),
                "gradient_ratio_field_worst_scenario": max(
                    float(row["gradient_ratio_worst_p95"]) for row in group
                ),
                "temporal_w1_ratio_worst_scenario": max(
                    float(row["temporal_w1_to_uniform_p95"]) for row in group
                ),
                "admission_tracking_nrmse_worst_scenario": max(
                    float(row["admission_tracking_nrmse_mean"]) for row in group
                ),
                "admission_pool_rate_cv_worst_scenario": max(
                    float(row["admission_pool_rate_cv_mean"]) for row in group
                ),
                "budget_violation_worst_scenario": max(
                    float(row["budget_violation_worst"]) for row in group
                ),
            }
        )

    def beta_numeric(value: object) -> float:
        return math.inf if str(value) == "inf" else float(value)

    summaries.sort(
        key=lambda row: (int(row["kappa"]), beta_numeric(row["beta"]))
    )
    for row in summaries:
        row["constraint_violation_factor"] = max(
            float(row["fairness_nrmse_worst_scenario"])
            / FAIRNESS_NRMSE_MAX,
            float(row["jain_regret_worst_scenario"]) / JAIN_REGRET_MAX,
            COHORT_RATIO_MIN
            / max(float(row["cohort_ratio_min_scenario"]), 1.0e-12),
            float(row["cohort_ratio_max_scenario"]) / COHORT_RATIO_MAX,
            ENTROPY_RATIO_MIN
            / max(float(row["entropy_ratio_min_scenario"]), 1.0e-12),
            float(row["gradient_ratio_mean_worst_scenario"])
            / GRADIENT_RATIO_MEAN_MAX,
            float(row["gradient_ratio_field_worst_scenario"])
            / GRADIENT_RATIO_FIELD_MAX,
            float(row["temporal_w1_ratio_worst_scenario"])
            / TEMPORAL_W1_RATIO_MAX,
        )
        row["meets_all_quality_constraints"] = (
            float(row["constraint_violation_factor"]) <= 1.0
        )
    # Auditable conjunctive rule: all three objectives must pass.  Among
    # feasible points, choose the smallest kappa (fastest admission), then the
    # highest-entropy beta at that rate.  No arbitrary weighted sum is used.
    feasible = [
        row
        for row in summaries
        if float(row["budget_violation_worst_scenario"]) <= 1.0e-12
        and float(row["admission_tracking_nrmse_worst_scenario"]) <= 1.0e-12
        and float(row["fairness_nrmse_worst_scenario"]) <= FAIRNESS_NRMSE_MAX
        and float(row["jain_regret_worst_scenario"]) <= JAIN_REGRET_MAX
        and float(row["cohort_ratio_min_scenario"]) >= COHORT_RATIO_MIN
        and float(row["cohort_ratio_max_scenario"]) <= COHORT_RATIO_MAX
        and float(row["entropy_ratio_min_scenario"]) >= ENTROPY_RATIO_MIN
        and float(row["gradient_ratio_mean_worst_scenario"])
        <= GRADIENT_RATIO_MEAN_MAX
        and float(row["gradient_ratio_field_worst_scenario"])
        <= GRADIENT_RATIO_FIELD_MAX
        and float(row["temporal_w1_ratio_worst_scenario"])
        <= TEMPORAL_W1_RATIO_MAX
    ]
    if feasible:
        recommendation = min(
            feasible,
            key=lambda row: (
                int(row["kappa"]),
                -float(row["entropy_ratio_min_scenario"]),
                float(row["gradient_ratio_mean_worst_scenario"]),
                beta_numeric(row["beta"]),
            ),
        ).copy()
        recommendation["selection_status"] = (
            "meets_all_predeclared_constraints"
        )
    else:
        recommendation = min(
            summaries,
            key=lambda row: (
                float(row["constraint_violation_factor"]),
                int(row["kappa"]),
                -float(row["entropy_ratio_min_scenario"]),
            ),
        ).copy()
        recommendation["selection_status"] = (
            "no_point_met_predeclared_constraints"
        )
    recommendation["searched_kappas"] = kappas
    recommendation["is_valid_recommendation"] = bool(feasible)
    recommendation["feasible_point_count"] = len(feasible)
    recommendation["constraints"] = {
        "fairness_nrmse_max": FAIRNESS_NRMSE_MAX,
        "jain_regret_max": JAIN_REGRET_MAX,
        "cohort_ratio_min": COHORT_RATIO_MIN,
        "cohort_ratio_max": COHORT_RATIO_MAX,
        "entropy_ratio_min": ENTROPY_RATIO_MIN,
        "gradient_ratio_mean_max": GRADIENT_RATIO_MEAN_MAX,
        "gradient_ratio_field_max": GRADIENT_RATIO_FIELD_MAX,
        "temporal_w1_ratio_max": TEMPORAL_W1_RATIO_MAX,
    }
    return summaries, recommendation


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    keys: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                keys.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def plot_tradeoff(path: Path, summaries: list[dict[str, object]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.5))
    kappas = sorted({int(row["kappa"]) for row in summaries})
    colors = plt.cm.viridis(np.linspace(0.05, 0.95, len(kappas)))
    for color, kappa in zip(colors, kappas):
        rows = [row for row in summaries if int(row["kappa"]) == kappa]
        finite = [row for row in rows if str(row["beta"]) != "inf"]
        finite.sort(key=lambda row: float(row["beta"]))
        x = [float(row["fairness_nrmse_worst_scenario"]) for row in finite]
        y = [1.0 - float(row["entropy_ratio_min_scenario"]) for row in finite]
        axes[0].plot(x, y, marker="o", color=color, label=f"kappa={kappa}")
        for row, x_value, y_value in zip(finite, x, y):
            axes[0].annotate(
                str(row["beta"]),
                (x_value, y_value),
                xytext=(3, 3),
                textcoords="offset points",
                fontsize=6,
            )
        axes[1].plot(
            [float(row["beta"]) for row in finite],
            [
                float(row["gradient_ratio_mean_worst_scenario"])
                for row in finite
            ],
            marker="o",
            color=color,
            label=f"kappa={kappa}",
        )
    axes[0].set_xlabel("Worst terminal-count NRMSE to balancing limit")
    axes[0].set_ylabel("Worst normalized shuffle entropy loss")
    axes[0].set_title("Fairness-randomness Pareto trade-off")
    axes[1].set_xscale("symlog", linthresh=0.01)
    axes[1].axhline(1.0, color="black", linestyle="--", linewidth=1.0)
    axes[1].set_xlabel("beta")
    axes[1].set_ylabel("Worst mean gradient MSE / ideal shuffle MSE")
    axes[1].set_title("Minibatch gradient mixing")
    for ax in axes:
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_feasibility(path: Path, summaries: list[dict[str, object]]) -> None:
    finite = [row for row in summaries if str(row["beta"]) != "inf"]
    kappas = sorted({int(row["kappa"]) for row in finite})
    betas = sorted({float(row["beta"]) for row in finite})
    lookup = {
        (int(row["kappa"]), float(row["beta"])): float(
            row["constraint_violation_factor"]
        )
        for row in finite
    }
    matrix = np.asarray(
        [[lookup.get((kappa, beta), math.nan) for beta in betas] for kappa in kappas]
    )
    fig_width = max(7.5, 0.72 * len(betas) + 3.0)
    fig_height = max(4.5, 0.46 * len(kappas) + 2.0)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    image = ax.imshow(
        np.clip(matrix, 0.0, 3.0),
        aspect="auto",
        cmap="RdYlGn_r",
        vmin=0.5,
        vmax=1.5,
    )
    for row_index, kappa in enumerate(kappas):
        for column_index, beta in enumerate(betas):
            value = matrix[row_index, column_index]
            if math.isfinite(value):
                ax.text(
                    column_index,
                    row_index,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    fontsize=6.5,
                    color="black" if value < 1.25 else "white",
                )
    ax.set_xticks(range(len(betas)), [f"{beta:g}" for beta in betas], rotation=45)
    ax.set_yticks(range(len(kappas)), [str(kappa) for kappa in kappas])
    ax.set_xlabel("beta")
    ax.set_ylabel("kappa (updates per admitted frame)")
    ax.set_title("Joint constraint violation (<= 1 is feasible)")
    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label("maximum normalized constraint ratio")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_admission(path: Path, aggregates: list[dict[str, object]]) -> None:
    rows = [
        row
        for row in aggregates
        if row["algorithm"]
        in {"ercb_beta_0", "gate_r2_uniform", "gate_r2_active_bonus3"}
    ]
    algorithms = sorted({str(row["algorithm"]) for row in rows})
    kappas = sorted({int(row["kappa"]) for row in rows})
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0))
    for algorithm in algorithms:
        values = [
            np.mean(
                [
                    float(row["admission_rate_ratio_mean"])
                    for row in rows
                    if row["algorithm"] == algorithm
                    and int(row["kappa"]) == kappa
                ]
            )
            for kappa in kappas
        ]
        lags = [
            np.mean(
                [
                    float(row["admission_max_lag_mean"])
                    for row in rows
                    if row["algorithm"] == algorithm
                    and int(row["kappa"]) == kappa
                ]
            )
            for kappa in kappas
        ]
        axes[0].plot(kappas, values, marker="o", label=algorithm)
        axes[1].plot(kappas, lags, marker="o", label=algorithm)
    axes[0].axhline(1.0, color="black", linestyle="--", linewidth=1.0)
    axes[0].set_ylabel("Actual / GPU-token target admissions")
    axes[1].set_ylabel("Maximum admission lag (frames)")
    for ax in axes:
        ax.set_xscale("log", base=2)
        ax.set_xlabel("kappa (completed updates per admitted frame)")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def self_test() -> None:
    rng = np.random.default_rng(7)
    counts = np.asarray([0, 1, 2, 3, 4, 5], dtype=np.int64)
    uniform = Policy("uniform", "softmax", beta=0.0)
    chosen, surprisal = sample_batch(uniform, counts, 4, rng)
    assert len(set(int(value) for value in chosen)) == 4
    ideal = math.lgamma(7.0) - math.lgamma(3.0)
    assert abs(surprisal - ideal) < 1.0e-10

    least = Policy("least", "least_count", beta=math.inf)
    chosen, _ = sample_batch(least, counts, 3, np.random.default_rng(8))
    assert set(int(value) for value in chosen) == {0, 1, 2}

    equal = np.zeros(10, dtype=np.int64)
    chosen, surprisal = sample_batch(
        Policy("ercb", "softmax", beta=12.0),
        equal,
        5,
        np.random.default_rng(9),
    )
    assert len(set(int(value) for value in chosen)) == 5
    ideal = math.lgamma(11.0) - math.lgamma(6.0)
    assert abs(surprisal - ideal) < 1.0e-10

    for initial in (16, 160):
        scenario = Scenario(f"test_{initial}", 256, initial, 8)
        final_views = initial + scenario.steps // 8 + 2
        fields = make_gradient_fields(final_views, 4, 11)
        row = simulate_run(scenario, 8, uniform, 13, fields)
        assert row["budget_violation"] == 0.0
        assert row["admission_rate_ratio"] == 1.0
        assert abs(float(row["entropy_ratio"]) - 1.0) < 1.0e-10

    scenario = Scenario("test_reference", 320, 32, 8)
    fields = make_gradient_fields(80, 4, 17)
    row = simulate_run(scenario, 8, least, 19, fields)
    assert float(row["fairness_rmse_updates"]) == 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=8000)
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--gradient-dim", type=int, default=8)
    parser.add_argument("--base-seed", type=int, default=710904)
    parser.add_argument("--kappas", default="2,4,8,16,32")
    parser.add_argument(
        "--betas", default="0,0.01,0.02,0.05,0.1,0.2,0.5,1,2,inf"
    )
    parser.add_argument(
        "--scenario",
        choices=("all", "short", "base", "long"),
        default="all",
    )
    parser.add_argument("--no-controls", action="store_true")
    parser.add_argument("--self-test-only", action="store_true")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).with_name("joint_admission_scheduler_outputs"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    self_test()
    if args.self_test_only:
        print("self-test: PASS")
        return
    if args.steps < args.batch_size:
        raise ValueError("steps must be at least one batch")

    kappas = parse_int_list(args.kappas)
    betas = parse_float_list(args.betas)
    scenarios = default_scenarios(args.steps, args.batch_size)
    if args.scenario != "all":
        wanted = f"{args.scenario}_stream"
        scenarios = [scenario for scenario in scenarios if scenario.name == wanted]
    policies = policies_for_betas(
        betas, include_controls=not args.no_controls
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, float | int | str]] = []
    for scenario_index, scenario in enumerate(scenarios):
        for kappa in kappas:
            max_views = scenario.initial_views + scenario.steps // kappa + 2
            fields = make_gradient_fields(
                max_views,
                args.gradient_dim,
                args.base_seed + 100003 * scenario_index + 101 * kappa,
            )
            for policy_index, policy in enumerate(policies):
                for seed in range(args.seeds):
                    run_seed = (
                        args.base_seed
                        + seed
                        + 1009 * policy_index
                        + 1000003 * scenario_index
                        + 10007 * kappa
                    )
                    rows.append(
                        simulate_run(
                            scenario, kappa, policy, run_seed, fields
                        )
                    )
            print(
                f"completed scenario={scenario.name} kappa={kappa} "
                f"policies={len(policies)} seeds={args.seeds}",
                flush=True,
            )

    # Persist expensive raw runs before derived aggregation so a reporting bug
    # cannot discard a completed sweep.
    write_csv(args.output_dir / "sweep_runs.csv", rows)
    aggregates = aggregate_rows(rows)
    add_reference_ratios(aggregates)
    summaries, recommendation = robust_beta_summary(aggregates, kappas)
    write_csv(args.output_dir / "aggregate.csv", aggregates)
    write_csv(args.output_dir / "beta_kappa_summary.csv", summaries)
    plot_tradeoff(args.output_dir / "tradeoff.png", summaries)
    plot_feasibility(args.output_dir / "feasibility.png", summaries)
    if not args.no_controls:
        plot_admission(args.output_dir / "admission.png", aggregates)

    payload = {
        "configuration": {
            "steps": args.steps,
            "seeds": args.seeds,
            "batch_size": args.batch_size,
            "gradient_dim": args.gradient_dim,
            "base_seed": args.base_seed,
            "kappas": kappas,
            "betas": ["inf" if math.isinf(beta) else beta for beta in betas],
            "scenarios": [scenario.__dict__ for scenario in scenarios],
            "policies": [policy.__dict__ for policy in policies],
        },
        "selection_rule": {
            "budget_violation": 0.0,
            "admission_tracking_nrmse_max": 0.0,
            "fairness_nrmse_max": FAIRNESS_NRMSE_MAX,
            "jain_regret_max": JAIN_REGRET_MAX,
            "cohort_ratio_min": COHORT_RATIO_MIN,
            "cohort_ratio_max": COHORT_RATIO_MAX,
            "entropy_ratio_min": ENTROPY_RATIO_MIN,
            "gradient_ratio_mean_max": GRADIENT_RATIO_MEAN_MAX,
            "gradient_ratio_field_max": GRADIENT_RATIO_FIELD_MAX,
            "temporal_w1_ratio_max": TEMPORAL_W1_RATIO_MAX,
            "then": (
                "minimize kappa (maximize feasible admission rate), then "
                "maximize worst-scenario entropy"
            ),
        },
        "recommendation": recommendation,
    }
    with (args.output_dir / "summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("selection result:")
    print(json.dumps(recommendation, indent=2, sort_keys=True))
    print(f"outputs: {args.output_dir}")


if __name__ == "__main__":
    main()
