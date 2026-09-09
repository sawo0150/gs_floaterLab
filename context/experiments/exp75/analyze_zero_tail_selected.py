#!/usr/bin/env python3
"""Focused audit for the selected pure-online exp75 scheduler.

The selected method is one fixed law on every scene:
relative-floor interval softmax random reshuffling, rho=1/2, K=8,
gamma=log(3).  Every run stops at the final training-view arrival.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from analyze_exp75 import scheduler_replay
from analyze_quality_tail_pairs import compare


HERE = Path(__file__).resolve().parent
ROOT = HERE / "evidence" / "zero_tail_runs"
OUTPUT = HERE / "evidence" / "zero_tail_selected_summary.json"
FIGURE = HERE / "evidence" / "zero_tail_selected_ablation.png"
SPECS = {
    "305": (18661, False),
    "12F": (24421, False),
    "3F": (36481, False),
    "1253": (8821, True),
}


def run_path(scene: str, seed: int, candidate: bool) -> Path:
    if candidate:
        return ROOT / f"aria{scene}_zerotail_relative_half_odds3_K8_r4_s{seed}"
    legacy_k = "K32" if seed == 0 and scene != "1253" else "K8"
    return ROOT / f"aria{scene}_zerotail_rr_{legacy_k}_r4_s{seed}"


def point_count(run: Path, iteration: int) -> int:
    ply = run / "point_cloud" / f"iteration_{iteration}" / "point_cloud.ply"
    with ply.open("rb") as stream:
        while True:
            line = stream.readline().decode("ascii").strip()
            if line.startswith("element vertex "):
                return int(line.rsplit(" ", 1)[1])
            if line == "end_header" or not line:
                raise ValueError(f"vertex count missing: {ply}")


def normalized_entropy(values: np.ndarray, bins: int = 16) -> float:
    histogram = np.bincount(values, minlength=bins)
    probability = histogram[histogram > 0] / histogram.sum()
    return float(-(probability * np.log(probability)).sum() / math.log(bins))


def scheduler_audit(run: Path, iteration: int) -> dict:
    summary = json.loads((run / "view_scheduler_summary.json").read_text())
    arrivals = np.asarray(list(summary["arrival_iteration"].values()), dtype=np.int64)
    counts = np.asarray(list(summary["selection_count"].values()), dtype=np.float64)
    history, native_blocks = scheduler_replay(summary)
    history = np.asarray(history, dtype=np.int64)

    # Rank views causally by arrival; this avoids assuming dictionary/image-name order.
    order = np.lexsort((np.arange(len(arrivals)), arrivals))
    temporal_rank = np.empty(len(arrivals), dtype=np.int64)
    temporal_rank[order] = np.arange(len(arrivals))
    sorted_arrivals = arrivals[order]
    window_entropies = []
    for start in range(0, len(history), 128):
        stop = min(start + 128, len(history))
        if stop - start < 32:
            continue
        bins = []
        for offset, selected in enumerate(history[start:stop], start=start + 1):
            eligible = int(np.searchsorted(sorted_arrivals, offset, side="right"))
            if eligible < 16:
                continue
            relative_rank = temporal_rank[selected] / eligible
            bins.append(min(15, int(relative_rank * 16)))
        if len(bins) >= 32:
            window_entropies.append(normalized_entropy(np.asarray(bins)))

    interval_duplicate_blocks = None
    if "frame_interval_id" in summary and summary["name"] != "causal_rr":
        frame_interval = np.asarray([
            summary["frame_interval_id"][name]
            for name in summary["selection_count"]
        ], dtype=np.int64)
        interval_duplicate_blocks = int(sum(
            len(block) != len(set(frame_interval[np.asarray(block, dtype=np.int64)]))
            for block in native_blocks
        ))

    return {
        "total_iterations": int(summary["total_iterations"]),
        "last_arrival": int(arrivals.max()),
        "zero_tail_verified": bool(iteration == arrivals.max() == summary["total_iterations"]),
        "pool_size": int(len(counts)),
        "count_cv": float(counts.std() / counts.mean()),
        "unselected_fraction": float(np.mean(counts == 0)),
        "count_temporal_thirds": [float(x.mean()) for x in np.array_split(counts, 3)],
        "dynamic_window128_temporal_entropy_ratio": float(np.mean(window_entropies)),
        "native_blocks": int(len(native_blocks)),
        "native_blocks_with_interval_duplicates": interval_duplicate_blocks,
        "gaussians": point_count(run, iteration),
    }


def build_rows() -> list[dict]:
    rows = []
    for scene, (iteration, stress_control) in SPECS.items():
        for seed in (0, 1):
            baseline = run_path(scene, seed, False)
            candidate = run_path(scene, seed, True)
            quality = compare(f"{scene}_s{seed}", baseline, candidate, iteration)
            rr_audit = scheduler_audit(baseline, iteration)
            candidate_audit = scheduler_audit(candidate, iteration)
            rows.append({
                "scene": scene,
                "seed": seed,
                "stress_control": stress_control,
                "iteration": iteration,
                "quality": quality,
                "rr": rr_audit,
                "candidate": candidate_audit,
                "count_cv_delta": candidate_audit["count_cv"] - rr_audit["count_cv"],
                "entropy_ratio_delta": (
                    candidate_audit["dynamic_window128_temporal_entropy_ratio"]
                    - rr_audit["dynamic_window128_temporal_entropy_ratio"]
                ),
            })
    return rows


def aggregate(rows: list[dict]) -> dict:
    main = [row for row in rows if not row["stress_control"]]
    metrics = {
        "mean_delta": [row["quality"]["mean_delta"] for row in main],
        "worst_q1_delta": [row["quality"]["worst_q1_delta"] for row in main],
        "rr_hard_q1_delta": [row["quality"]["rr_hard_q1_delta"] for row in main],
        "late_third_delta": [row["quality"]["temporal_thirds_delta"][2] for row in main],
        "count_cv_delta": [row["count_cv_delta"] for row in main],
        "entropy_ratio_delta": [row["entropy_ratio_delta"] for row in main],
    }
    return {
        key: {
            "mean": float(np.mean(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "positive_runs": int(np.sum(np.asarray(values) > 0)),
            "runs": len(values),
        }
        for key, values in metrics.items()
    }


def plot(rows: list[dict]) -> None:
    scene_order = list(SPECS)
    metric_specs = [
        ("Mean held-out PSNR", lambda row: row["quality"]["mean_delta"]),
        ("Worst-Q1 held-out PSNR", lambda row: row["quality"]["worst_q1_delta"]),
        ("Late-third held-out PSNR", lambda row: row["quality"]["temporal_thirds_delta"][2]),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(12.0, 3.5), sharex=True)
    for axis, (title, accessor) in zip(axes, metric_specs):
        axis.axhline(0.0, color="0.35", linewidth=1.0)
        for x, scene in enumerate(scene_order):
            values = [accessor(row) for row in rows if row["scene"] == scene]
            axis.scatter([x - .07, x + .07], values, s=28, color="#2673b8", zorder=3)
            axis.scatter(x, np.mean(values), marker="D", s=30, color="#c33d36", zorder=4)
        axis.set_title(title, fontsize=10)
        axis.set_xticks(range(len(scene_order)), ["305", "12F", "3F", "1253\n(extra)"])
        axis.grid(axis="y", alpha=.22)
        axis.set_ylabel("Proposed − causal RR (dB)")
    fig.suptitle("Pure-online zero-tail ablation (two independent seeds)", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIGURE, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    rows = build_rows()
    payload = {
        "method": {
            "name": "relative_floor_interval_softmax_rr",
            "rho": 0.5,
            "K": 8,
            "gamma": math.log(3),
            "maximum_odds_multiplier": 3.0,
            "admission": "all causal arrivals admitted immediately",
            "tail_updates": 0,
        },
        "rows": rows,
        "main_three_scene_aggregate": aggregate(rows),
    }
    if not all(row["rr"]["zero_tail_verified"] and row["candidate"]["zero_tail_verified"] for row in rows):
        raise AssertionError("zero-tail contract violated")
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n")
    plot(rows)
    print(json.dumps(payload["main_three_scene_aggregate"], indent=2))
    print(OUTPUT)
    print(FIGURE)


if __name__ == "__main__":
    main()
