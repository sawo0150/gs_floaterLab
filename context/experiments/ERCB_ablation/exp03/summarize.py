#!/usr/bin/env python3
"""Validate exp03 pairs and write a machine-readable reproduction summary."""

import json
import math
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
EXP = Path(__file__).resolve().parent


def read_run(job):
    output = Path(job["output"])
    summary = json.loads((output / "view_scheduler_summary.json").read_text())
    curves = [json.loads(line) for line in (output / "evaluation_curve.jsonl").read_text().splitlines()]
    tests = [row for row in curves if row["split"] == "test"]
    total = job["total_iterations"]
    if summary.get("post_update_reporting") is not True:
        raise ValueError(f"not post-update: {output}")
    if summary.get("completed_updates_this_run") != total:
        raise ValueError(f"update mismatch: {output}")
    if sum(summary["selection_count"].values()) != total:
        raise ValueError(f"draw mismatch: {output}")
    if max(summary["arrival_iteration"].values()) != total:
        raise ValueError(f"non-zero-tail schedule: {output}")
    if not tests or tests[-1]["iteration"] != total:
        raise ValueError(f"missing final held-out evaluation: {output}")
    values = list(tests[-1]["per_view_psnr"].values())
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError(f"invalid held-out metric: {output}")
    return {
        "psnr": statistics.fmean(values),
        "heldout_views": len(values),
        "zero_service": summary["zero_service"],
        "unique_selected": summary["unique_selected"],
        "training_gpu_ms": summary["training_gpu_ms"],
        "scheduler_cpu_ms": summary["scheduler_cpu_ns"] / 1e6,
        "selection_count": summary["selection_count"],
        "arrival_iteration": summary["arrival_iteration"],
        "curve": [{"iteration": row["iteration"], "psnr": row["psnr"]} for row in tests],
        "output": str(output),
    }


def main():
    manifest = json.loads((EXP / "evidence/manifest.json").read_text())
    reference = json.loads((ROOT / "context/experiments/exp77/evidence/final_ablation.json").read_text())
    reference_rows = {
        (row["scene"], row["budget"], row["arm"]): row["delta_rr"]
        for row in reference["budget"]["rows"]
        if row["arm"] in ("rr", "ercb")
    }
    for row in reference["low_budget"]["rows"]:
        if row["arm"] in ("rr", "ercb"):
            reference_rows[(row["scene"], 15, row["arm"], row["seed"])] = row["delta_rr"]
    indexed = {}
    for job in manifest["jobs"]:
        indexed[(job["scene"], job["budget"], job["seed"], job["arm"])] = read_run(job)
    pairs = []
    for scene in ("utmm_square1_full", "rpng_table01_full"):
        for budget in (15, 30, 60):
            seeds = (0, 1, 2) if budget in (15, 60) else (0,)
            for seed in seeds:
                rr = indexed[(scene, budget, seed, "rr")]
                ercb = indexed[(scene, budget, seed, "ercb")]
                if rr["arrival_iteration"] != ercb["arrival_iteration"]:
                    raise ValueError(f"arrival mismatch: {scene} b{budget} s{seed}")
                if set(rr["selection_count"]) != set(ercb["selection_count"]):
                    raise ValueError(f"training membership mismatch: {scene} b{budget} s{seed}")
                delta = ercb["psnr"] - rr["psnr"]
                if budget == 15:
                    ref_delta = reference_rows[(scene, budget, "ercb", seed)]
                elif seed == 0:
                    ref_delta = reference_rows[(scene, budget, "ercb")]
                else:
                    ref_delta = None
                # Keep the persisted evidence compact. The full per-view counters
                # remain in each run's view_scheduler_summary.json and are used
                # above for contract validation, but add no value when duplicated
                # in the aggregate summary.
                rr_compact = {key: value for key, value in rr.items()
                              if key not in ("selection_count", "arrival_iteration")}
                ercb_compact = {key: value for key, value in ercb.items()
                                if key not in ("selection_count", "arrival_iteration")}
                pairs.append({
                    "scene": scene, "budget": budget, "seed": seed,
                    "total_iterations": max(rr["arrival_iteration"].values()),
                    "rr": rr_compact, "ercb": ercb_compact, "delta_ercb_minus_rr": delta,
                    "exp77_reference_delta": ref_delta,
                    "delta_difference_vs_exp77": None if ref_delta is None else delta - ref_delta,
                })
    low = {}
    for scene in ("utmm_square1_full", "rpng_table01_full"):
        values = [pair["delta_ercb_minus_rr"] for pair in pairs
                  if pair["scene"] == scene and pair["budget"] == 15]
        low[scene] = {
            "mean_delta": statistics.fmean(values),
            "min_delta": min(values),
            "wins": sum(value > 0 for value in values),
            "values": values,
        }
    seed0_trends = {
        scene: [next(pair["delta_ercb_minus_rr"] for pair in pairs
                     if pair["scene"] == scene and pair["budget"] == budget and pair["seed"] == 0)
                for budget in (15, 30, 60)]
        for scene in ("utmm_square1_full", "rpng_table01_full")
    }
    full = {}
    for scene in ("utmm_square1_full", "rpng_table01_full"):
        values = [pair["delta_ercb_minus_rr"] for pair in pairs
                  if pair["scene"] == scene and pair["budget"] == 60]
        full[scene] = {
            "mean_delta": statistics.fmean(values),
            "min_delta": min(values),
            "max_delta": max(values),
            "wins": sum(value > 0 for value in values),
            "values": values,
        }
    result = {
        "protocol": manifest["protocol"],
        "status": "COMPLETE_VALIDATED",
        "pairs": pairs,
        "budget15_aggregate": low,
        "budget60_aggregate": full,
        "seed0_delta_by_budget_15_30_60": seed0_trends,
        "reproduction_gates": {
            "budget15_positive_both_scenes": all(row["mean_delta"] > 0 for row in low.values()),
            "budget15_all_seed_wins": all(row["wins"] == 3 for row in low.values()),
            "seed0_delta_decreases_with_budget_both_scenes": all(
                values[0] > values[1] > values[2] for values in seed0_trends.values()
            ),
            "budget60_mean_gain_smaller_than_budget15_both_scenes": all(
                full[scene]["mean_delta"] < low[scene]["mean_delta"]
                for scene in full
            ),
        },
    }
    destination = EXP / "evidence/summary.json"
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"budget15_aggregate": low, "budget60_aggregate": full,
                      "seed0_trends": seed0_trends,
                      "gates": result["reproduction_gates"]}, indent=2))


if __name__ == "__main__":
    main()
