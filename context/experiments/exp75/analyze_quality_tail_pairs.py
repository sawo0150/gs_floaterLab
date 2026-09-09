#!/usr/bin/env python3
"""Paired lower-tail held-out PSNR audit for exp75 scheduler runs."""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"


@lru_cache(maxsize=None)
def psnr_values(run: Path, iteration: int) -> np.ndarray:
    root = run / "test" / f"ours_{iteration}"
    renders = sorted((root / "renders").glob("*.png"))
    targets = sorted((root / "gt").glob("*.png"))
    if not renders or len(renders) != len(targets):
        raise FileNotFoundError(run)
    values = []
    for rendered, target in zip(renders, targets):
        prediction = np.asarray(Image.open(rendered), dtype=np.float32) / 255.0
        reference = np.asarray(Image.open(target), dtype=np.float32) / 255.0
        values.append(float(-10.0 * np.log10(np.mean((prediction - reference) ** 2))))
    return np.asarray(values, dtype=np.float64)


def compare(label: str, baseline: Path, candidate: Path, iteration: int) -> dict:
    rr = psnr_values(baseline, iteration)
    proposed = psnr_values(candidate, iteration)
    if len(rr) != len(proposed):
        raise ValueError(f"unaligned pair {label}: {len(rr)} vs {len(proposed)}")
    q1_size = int(math.ceil(len(rr) * .25))
    rr_hard = np.argsort(rr)[:q1_size]
    rr_thirds = [float(part.mean()) for part in np.array_split(rr, 3)]
    candidate_thirds = [float(part.mean()) for part in np.array_split(proposed, 3)]
    return {
        "label": label,
        "iteration": iteration,
        "heldout_views": len(rr),
        "mean_rr": float(rr.mean()),
        "mean_candidate": float(proposed.mean()),
        "mean_delta": float(proposed.mean() - rr.mean()),
        "temporal_thirds_rr": rr_thirds,
        "temporal_thirds_candidate": candidate_thirds,
        "temporal_thirds_delta": [
            float(candidate - baseline)
            for baseline, candidate in zip(rr_thirds, candidate_thirds)
        ],
        "worst_q1_rr": float(np.sort(rr)[:q1_size].mean()),
        "worst_q1_candidate": float(np.sort(proposed)[:q1_size].mean()),
        "worst_q1_delta": float(np.sort(proposed)[:q1_size].mean() - np.sort(rr)[:q1_size].mean()),
        "rr_hard_q1_candidate": float(proposed[rr_hard].mean()),
        "rr_hard_q1_delta": float(proposed[rr_hard].mean() - rr[rr_hard].mean()),
        "per_view_improved_fraction": float(np.mean(proposed > rr)),
    }


def main() -> None:
    pair_specs = [
        ("305_size_aware", EVIDENCE / "saturation_runs/aria305_rr_r4_45k_s0",
         EVIDENCE / "interval_runs/aria305_interval_size_K32_b002_r4_45k_s0", (30000, 45000)),
        ("12F_size_aware", EVIDENCE / "saturation_runs/aria12F_rr_r4_45k_s0",
         EVIDENCE / "interval_runs/aria12F_interval_size_K32_b002_r4_45k_s0", (30000, 45000)),
        ("305_staged", EVIDENCE / "saturation_runs/aria305_rr_r4_45k_s0",
         EVIDENCE / "interval_runs/aria305_staged_interval_size_K32_b002_r4_45k_s0", (30000, 45000)),
        ("12F_staged", EVIDENCE / "saturation_runs/aria12F_rr_r4_45k_s0",
         EVIDENCE / "interval_runs/aria12F_staged_interval_size_K32_b002_r4_45k_s0", (30000, 45000)),
        ("3F_size_aware", EVIDENCE / "external_runs/aria3F_rr_K32_b002_r4_79081_s0",
         EVIDENCE / "external_runs/aria3F_interval_size_K32_b002_r4_79081_s0", (45000, 79081)),
        ("3F_staged", EVIDENCE / "external_runs/aria3F_rr_K32_b002_r4_79081_s0",
         EVIDENCE / "external_runs/aria3F_staged_interval_size_K32_b002_r4_79081_s0", (45000, 79081)),
        ("3F_arrival_aligned", EVIDENCE / "external_runs/aria3F_rr_K32_b002_du36500_r4_79081_s0",
         EVIDENCE / "external_runs/aria3F_staged_interval_size_K32_b002_du36500_r4_79081_s0", (45000, 79081)),
        ("305_shared_branch", EVIDENCE / "shared_branch/aria305_shared_rr_K32_b002_r4_45k_s0",
         EVIDENCE / "shared_branch/aria305_shared_interval_size_K32_b002_r4_45k_s0", (30000, 45000)),
        ("305_shared_beta005", EVIDENCE / "shared_branch/aria305_shared_rr_K32_b002_r4_45k_s0",
         EVIDENCE / "shared_branch/aria305_shared_interval_size_b005_K32_r4_45k_s0", (30000, 45000)),
        ("305_shared_beta01", EVIDENCE / "shared_branch/aria305_shared_rr_K32_b002_r4_45k_s0",
         EVIDENCE / "shared_branch/aria305_shared_interval_size_b01_K32_r4_45k_s0", (30000, 45000)),
        ("12F_shared_beta002", EVIDENCE / "shared_branch/aria12F_shared_rr_K32_r4_45k_s0",
         EVIDENCE / "shared_branch/aria12F_shared_interval_size_b002_K32_r4_45k_s0", (30000, 45000)),
        ("12F_shared_beta005", EVIDENCE / "shared_branch/aria12F_shared_rr_K32_r4_45k_s0",
         EVIDENCE / "shared_branch/aria12F_shared_interval_size_b005_K32_r4_45k_s0", (30000, 45000)),
        ("12F_shared_beta01", EVIDENCE / "shared_branch/aria12F_shared_rr_K32_r4_45k_s0",
         EVIDENCE / "shared_branch/aria12F_shared_interval_size_b01_K32_r4_45k_s0", (30000, 45000)),
        ("3F_shared_beta005", EVIDENCE / "shared_branch/aria3F_shared_rr_K32_r4_79081_s0",
         EVIDENCE / "shared_branch/aria3F_shared_interval_size_b005_K32_r4_79081_s0",
         (30000, 45000, 60000, 79081)),
        ("305_shared_bounded_odds2", EVIDENCE / "shared_branch/aria305_shared_rr_K32_b002_r4_45k_s0",
         EVIDENCE / "shared_branch/aria305_shared_bounded_odds2_K32_r4_45k_s0", (30000, 45000)),
        ("305_shared_bounded_odds4", EVIDENCE / "shared_branch/aria305_shared_rr_K32_b002_r4_45k_s0",
         EVIDENCE / "shared_branch/aria305_shared_bounded_odds4_K32_r4_45k_s0", (30000, 45000)),
        ("305_shared_bounded_odds8", EVIDENCE / "shared_branch/aria305_shared_rr_K32_b002_r4_45k_s0",
         EVIDENCE / "shared_branch/aria305_shared_bounded_odds8_K32_r4_45k_s0", (30000, 45000)),
        ("12F_shared_bounded_odds2", EVIDENCE / "shared_branch/aria12F_shared_rr_K32_r4_45k_s0",
         EVIDENCE / "shared_branch/aria12F_shared_bounded_odds2_K32_r4_45k_s0", (30000, 45000)),
        ("12F_shared_bounded_odds4", EVIDENCE / "shared_branch/aria12F_shared_rr_K32_r4_45k_s0",
         EVIDENCE / "shared_branch/aria12F_shared_bounded_odds4_K32_r4_45k_s0", (30000, 45000)),
        ("12F_shared_bounded_odds8", EVIDENCE / "shared_branch/aria12F_shared_rr_K32_r4_45k_s0",
         EVIDENCE / "shared_branch/aria12F_shared_bounded_odds8_K32_r4_45k_s0", (30000, 45000)),
        ("305_shared_bounded_odds2_s1", EVIDENCE / "shared_branch/aria305_shared_rr_K32_r4_45k_s1",
         EVIDENCE / "shared_branch/aria305_shared_bounded_odds2_K32_r4_45k_s1", (30000, 45000)),
        ("12F_shared_bounded_odds2_s1", EVIDENCE / "shared_branch/aria12F_shared_rr_K32_r4_45k_s1",
         EVIDENCE / "shared_branch/aria12F_shared_bounded_odds2_K32_r4_45k_s1", (30000, 45000)),
        ("305_shared_two_pass_odds2_s1", EVIDENCE / "shared_branch/aria305_shared_rr_K32_r4_45k_s1",
         EVIDENCE / "shared_branch/aria305_shared_two_pass_odds2_K32_r4_45k_s1", (30000, 45000)),
        ("305_shared_two_pass_odds4_s1", EVIDENCE / "shared_branch/aria305_shared_rr_K32_r4_45k_s1",
         EVIDENCE / "shared_branch/aria305_shared_two_pass_odds4_K32_r4_45k_s1", (30000, 45000)),
        ("305_shared_two_pass_odds8_s1", EVIDENCE / "shared_branch/aria305_shared_rr_K32_r4_45k_s1",
         EVIDENCE / "shared_branch/aria305_shared_two_pass_odds8_K32_r4_45k_s1", (30000, 45000)),
        ("12F_shared_two_pass_odds2_s1", EVIDENCE / "shared_branch/aria12F_shared_rr_K32_r4_45k_s1",
         EVIDENCE / "shared_branch/aria12F_shared_two_pass_odds2_K32_r4_45k_s1", (30000, 45000)),
        ("12F_shared_two_pass_odds4_s1", EVIDENCE / "shared_branch/aria12F_shared_rr_K32_r4_45k_s1",
         EVIDENCE / "shared_branch/aria12F_shared_two_pass_odds4_K32_r4_45k_s1", (30000, 45000)),
        ("12F_shared_two_pass_odds8_s1", EVIDENCE / "shared_branch/aria12F_shared_rr_K32_r4_45k_s1",
         EVIDENCE / "shared_branch/aria12F_shared_two_pass_odds8_K32_r4_45k_s1", (30000, 45000)),
        ("305_zerotail_two_pass_odds2_s0", EVIDENCE / "zero_tail_runs/aria305_zerotail_rr_K32_r4_s0",
         EVIDENCE / "zero_tail_runs/aria305_zerotail_two_pass_odds2_K32_r4_s0", (18661,)),
        ("12F_zerotail_two_pass_odds2_s0", EVIDENCE / "zero_tail_runs/aria12F_zerotail_rr_K32_r4_s0",
         EVIDENCE / "zero_tail_runs/aria12F_zerotail_two_pass_odds2_K32_r4_s0", (24421,)),
        ("3F_zerotail_two_pass_odds2_s0", EVIDENCE / "zero_tail_runs/aria3F_zerotail_rr_K32_r4_s0",
         EVIDENCE / "zero_tail_runs/aria3F_zerotail_two_pass_odds2_K32_r4_s0", (36481,)),
        ("305_zerotail_relative_half_odds2_s0", EVIDENCE / "zero_tail_runs/aria305_zerotail_rr_K32_r4_s0",
         EVIDENCE / "zero_tail_runs/aria305_zerotail_relative_half_odds2_K8_r4_s0", (18661,)),
        ("305_zerotail_relative_half_odds4_s0", EVIDENCE / "zero_tail_runs/aria305_zerotail_rr_K32_r4_s0",
         EVIDENCE / "zero_tail_runs/aria305_zerotail_relative_half_odds4_K8_r4_s0", (18661,)),
        ("12F_zerotail_relative_half_odds2_s0", EVIDENCE / "zero_tail_runs/aria12F_zerotail_rr_K32_r4_s0",
         EVIDENCE / "zero_tail_runs/aria12F_zerotail_relative_half_odds2_K8_r4_s0", (24421,)),
        ("12F_zerotail_relative_half_odds4_s0", EVIDENCE / "zero_tail_runs/aria12F_zerotail_rr_K32_r4_s0",
         EVIDENCE / "zero_tail_runs/aria12F_zerotail_relative_half_odds4_K8_r4_s0", (24421,)),
        ("3F_zerotail_relative_half_odds4_s0", EVIDENCE / "zero_tail_runs/aria3F_zerotail_rr_K32_r4_s0",
         EVIDENCE / "zero_tail_runs/aria3F_zerotail_relative_half_odds4_K8_r4_s0", (36481,)),
        ("305_zerotail_relative_half_odds3_s0", EVIDENCE / "zero_tail_runs/aria305_zerotail_rr_K32_r4_s0",
         EVIDENCE / "zero_tail_runs/aria305_zerotail_relative_half_odds3_K8_r4_s0", (18661,)),
        ("305_zerotail_relative_half_odds3_s1", EVIDENCE / "zero_tail_runs/aria305_zerotail_rr_K8_r4_s1",
         EVIDENCE / "zero_tail_runs/aria305_zerotail_relative_half_odds3_K8_r4_s1", (18661,)),
        ("12F_zerotail_relative_half_odds3_s0", EVIDENCE / "zero_tail_runs/aria12F_zerotail_rr_K32_r4_s0",
         EVIDENCE / "zero_tail_runs/aria12F_zerotail_relative_half_odds3_K8_r4_s0", (24421,)),
        ("12F_zerotail_relative_half_odds3_s1", EVIDENCE / "zero_tail_runs/aria12F_zerotail_rr_K8_r4_s1",
         EVIDENCE / "zero_tail_runs/aria12F_zerotail_relative_half_odds3_K8_r4_s1", (24421,)),
        ("3F_zerotail_relative_half_odds3_s0", EVIDENCE / "zero_tail_runs/aria3F_zerotail_rr_K32_r4_s0",
         EVIDENCE / "zero_tail_runs/aria3F_zerotail_relative_half_odds3_K8_r4_s0", (36481,)),
        ("3F_zerotail_relative_half_odds3_s1", EVIDENCE / "zero_tail_runs/aria3F_zerotail_rr_K8_r4_s1",
         EVIDENCE / "zero_tail_runs/aria3F_zerotail_relative_half_odds3_K8_r4_s1", (36481,)),
        ("1253_zerotail_relative_half_odds3_s0", EVIDENCE / "zero_tail_runs/aria1253_zerotail_rr_K8_r4_s0",
         EVIDENCE / "zero_tail_runs/aria1253_zerotail_relative_half_odds3_K8_r4_s0", (8821,)),
        ("1253_zerotail_relative_half_odds3_s1", EVIDENCE / "zero_tail_runs/aria1253_zerotail_rr_K8_r4_s1",
         EVIDENCE / "zero_tail_runs/aria1253_zerotail_relative_half_odds3_K8_r4_s1", (8821,)),
    ]
    rows = []
    for label, baseline, candidate, iterations in pair_specs:
        for iteration in iterations:
            try:
                rows.append(compare(label, baseline, candidate, iteration))
            except FileNotFoundError:
                pass
    output = EVIDENCE / "quality_tail_pairs.json"
    output.write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
