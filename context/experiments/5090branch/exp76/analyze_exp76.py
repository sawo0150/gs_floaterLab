#!/usr/bin/env python3
"""Analyze the threshold-free mean-normalized Softmax scheduler sweep."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
EXP75 = HERE.parent / "exp75"
sys.path.insert(0, str(EXP75))
from analyze_quality_tail_pairs import compare  # noqa: E402
from analyze_zero_tail_selected import scheduler_audit  # noqa: E402


ROOT = HERE / "evidence" / "zero_tail_runs"
EXP75_ROOT = EXP75 / "evidence" / "zero_tail_runs"
OUTPUT = HERE / "evidence" / "exp76_summary.json"
SCENES = {"305": 18661, "12F": 24421}
DEVELOPMENT_ODDS = {
    "100": 1.00,
    "110": 1.10,
    "120": 1.20,
    "125": 1.25,
    "130": 1.30,
    "135": 1.35,
    "140": 1.40,
    "150": 1.50,
    "200": 2.00,
}


def candidate_path(scene: str, odds_tag: str, seed: int) -> Path:
    return ROOT / f"aria{scene}_zerotail_normalized_odds{odds_tag}_K8_r4_s{seed}"


def rr_path(scene: str, seed: int) -> Path:
    k = "K32" if seed == 0 else "K8"
    return EXP75_ROOT / f"aria{scene}_zerotail_rr_{k}_r4_s{seed}"


def floor_path(scene: str, seed: int) -> Path:
    return EXP75_ROOT / f"aria{scene}_zerotail_relative_half_odds3_K8_r4_s{seed}"


def compact_quality(result: dict) -> dict:
    return {
        "baseline_psnr": result["mean_rr"],
        "candidate_psnr": result["mean_candidate"],
        "mean_delta": result["mean_delta"],
        "worst_q1_delta": result["worst_q1_delta"],
        "baseline_hard_q1_delta": result["rr_hard_q1_delta"],
        "temporal_thirds_delta": result["temporal_thirds_delta"],
        "per_view_improved_fraction": result["per_view_improved_fraction"],
    }


def evaluate(scene: str, odds_tag: str, seed: int) -> dict:
    iteration = SCENES[scene]
    candidate = candidate_path(scene, odds_tag, seed)
    rr = rr_path(scene, seed)
    floor = floor_path(scene, seed)
    if not candidate.exists():
        raise FileNotFoundError(candidate)
    summary = json.loads((candidate / "view_scheduler_summary.json").read_text())
    audit = scheduler_audit(candidate, iteration)
    return {
        "scene": scene,
        "seed": seed,
        "iteration": iteration,
        "odds": DEVELOPMENT_ODDS[odds_tag],
        "gamma": float(summary["beta"]),
        "vs_causal_rr": compact_quality(compare(f"{scene}_rr", rr, candidate, iteration)),
        "vs_exp75_best": compact_quality(compare(f"{scene}_floor", floor, candidate, iteration)),
        "scheduler": audit,
    }


def aggregate(rows: list[dict], comparison: str) -> dict:
    fields = ("mean_delta", "worst_q1_delta", "baseline_hard_q1_delta")
    result = {}
    for field in fields:
        values = np.asarray([row[comparison][field] for row in rows], dtype=np.float64)
        result[field] = {
            "mean": float(values.mean()),
            "minimum": float(values.min()),
            "positive_runs": int(np.sum(values > 0)),
            "runs": int(len(values)),
        }
    late = np.asarray(
        [row[comparison]["temporal_thirds_delta"][2] for row in rows], dtype=np.float64
    )
    result["late_third_delta"] = {
        "mean": float(late.mean()),
        "minimum": float(late.min()),
        "positive_runs": int(np.sum(late > 0)),
        "runs": int(len(late)),
    }
    return result


def main() -> None:
    development = []
    for odds_tag in DEVELOPMENT_ODDS:
        rows = [evaluate(scene, odds_tag, 0) for scene in SCENES]
        development.append({
            "odds": DEVELOPMENT_ODDS[odds_tag],
            "gamma": math.log(DEVELOPMENT_ODDS[odds_tag]),
            "rows": rows,
            "passes_both_scenes_mean_vs_rr": all(
                row["vs_causal_rr"]["mean_delta"] > 0 for row in rows
            ),
            "passes_both_scenes_mean_and_worst_q1_vs_rr": all(
                row["vs_causal_rr"]["mean_delta"] > 0
                and row["vs_causal_rr"]["worst_q1_delta"] > 0
                for row in rows
            ),
            "mean_delta_vs_rr": float(np.mean([
                row["vs_causal_rr"]["mean_delta"] for row in rows
            ])),
            "mean_delta_vs_exp75_best": float(np.mean([
                row["vs_exp75_best"]["mean_delta"] for row in rows
            ])),
        })

    selected_rows = []
    for scene in SCENES:
        for seed in (0, 1):
            row = evaluate(scene, "125", seed)
            row["causal_rr_scheduler"] = scheduler_audit(
                rr_path(scene, seed), SCENES[scene]
            )
            row["exp75_best_scheduler"] = scheduler_audit(
                floor_path(scene, seed), SCENES[scene]
            )
            selected_rows.append(row)
    payload = {
        "method": {
            "name": "normalized_interval_size_softmax_rr",
            "law": "w_j = |G_j| exp(-gamma * r_j / mean_r)",
            "selected_odds": 1.25,
            "selected_gamma": math.log(1.25),
            "K": 8,
            "inner_sampling": "persistent random reshuffling without replacement",
            "admission": "all causal arrivals admitted immediately",
            "tail_updates": 0,
        },
        "selection_protocol": (
            "Tune one common gamma on 305 and 12F seed 0; require positive mean-PSNR "
            "and worst-Q1 deltas over causal RR on both scenes, then maximize the "
            "two-scene mean delta; freeze it before seed-1 validation."
        ),
        "development_seed0": development,
        "selected_two_seed_rows": selected_rows,
        "selected_aggregate_vs_causal_rr": aggregate(selected_rows, "vs_causal_rr"),
        "selected_aggregate_vs_exp75_best": aggregate(selected_rows, "vs_exp75_best"),
    }
    if not all(row["scheduler"]["zero_tail_verified"] for row in selected_rows):
        raise AssertionError("zero-tail contract violated")
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({
        "selected_aggregate_vs_causal_rr": payload["selected_aggregate_vs_causal_rr"],
        "selected_aggregate_vs_exp75_best": payload["selected_aggregate_vs_exp75_best"],
    }, indent=2))
    print(OUTPUT)


if __name__ == "__main__":
    main()
