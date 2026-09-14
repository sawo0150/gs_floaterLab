#!/usr/bin/env python3
"""Derive immutable custom budgets from vanilla's measured map completion."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
HERE = LAB / "context/experiments/benchmark_custom/5070ti_vanilla_matched_time"
SOURCE = (
    LAB
    / "context/experiments/benchmark_vanila/5070ti_1.5x_streaming/evidence/summary.json"
)
JSON_OUT = HERE / "evidence/budget_manifest.json"
CSV_OUT = HERE / "evidence/budget_manifest.csv"


def build() -> dict:
    source_payload = json.loads(SOURCE.read_text())
    records = []
    for raw in source_payload["records"]:
        source_duration = float(raw["source_duration_s"])
        planned_15x = float(raw["budget_duration_s"])
        mapping_lateness = float(raw["mapping_lateness_s"])
        matched_elapsed = planned_15x + mapping_lateness
        if source_duration <= 0 or matched_elapsed <= 0:
            raise ValueError(f"invalid timing for {raw['family']}/{raw['scene']}")
        records.append(
            {
                "family": raw["family"],
                "scene": raw["scene"],
                "source_duration_s": source_duration,
                "vanilla_planned_15x_s": planned_15x,
                "vanilla_producer_lateness_s": float(raw["producer_lateness_s"]),
                "vanilla_tracking_lateness_s": float(raw["tracking_lateness_s"]),
                "vanilla_mapping_lateness_s": mapping_lateness,
                "vanilla_mapping_elapsed_s": matched_elapsed,
                "matched_replay_scale": matched_elapsed / source_duration,
                "vanilla_heldout_psnr": float(raw["heldout_psnr"]),
                "vanilla_heldout_ssim": float(raw["heldout_ssim"]),
                "vanilla_heldout_lpips": float(raw["heldout_lpips"]),
                "vanilla_result_file": str(
                    Path(raw["output_dir"]) / "psnr/after_opt/final_result.json"
                ),
            }
        )
    return {
        "protocol": "vanilla_map_completion_matched_scaled_replay_zero_tail",
        "source_evidence": str(SOURCE),
        "formula": (
            "matched_replay_scale=(1.5*source_duration_s+"
            "vanilla_mapping_lateness_s)/source_duration_s"
        ),
        "records": records,
    }


def write(payload: dict) -> None:
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2) + "\n")
    fields = list(payload["records"][0])
    with CSV_OUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(payload["records"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookup", nargs=2, metavar=("FAMILY", "SCENE"))
    parser.add_argument("--field", default="matched_replay_scale")
    args = parser.parse_args()
    payload = build()
    write(payload)
    if args.lookup:
        family, scene = args.lookup
        matches = [
            row
            for row in payload["records"]
            if row["family"] == family and row["scene"] == scene
        ]
        if len(matches) != 1:
            raise SystemExit(f"no unique budget for {family}/{scene}")
        if args.field not in matches[0]:
            raise SystemExit(f"unknown budget field: {args.field}")
        print(matches[0][args.field])


if __name__ == "__main__":
    main()
