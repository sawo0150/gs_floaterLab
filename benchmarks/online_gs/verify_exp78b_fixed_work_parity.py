#!/usr/bin/env python3
"""Verify an official/custom exp78-B fixed-work vanilla parity pair."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_evaluation_log(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    marker = '\n{\n  "protocol": "exp78_split_audit_v2"'
    offset = text.rfind(marker)
    if offset < 0:
        if text.startswith('{\n  "protocol": "exp78_split_audit_v2"'):
            offset = -1
        else:
            raise ValueError(f"could not locate evaluation JSON in {path}")
    return json.loads(text[offset + 1 :])


def event_ledger(runtime: dict[str, Any]) -> list[dict[str, Any]]:
    keys = (
        "event_id",
        "kind",
        "filtered_frame_uids",
        "optimizer_steps_completed",
        "rasterized_view_updates",
        "completed",
        "policy_skip",
    )
    output = []
    for event in runtime.get("events", []):
        record = {key: event.get(key) for key in keys}
        record["filtered_frame_uids"] = record["filtered_frame_uids"] or []
        record["optimizer_steps_completed"] = (
            record["optimizer_steps_completed"] or 0
        )
        record["rasterized_view_updates"] = (
            record["rasterized_view_updates"] or 0
        )
        if record["policy_skip"] in (
            "mapping_after_imu_init",
            "mapping_before_metric_init",
        ):
            record["policy_skip"] = "mapping_before_metric_init"
        output.append(record)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("official", type=Path)
    parser.add_argument("custom", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-psnr-delta", type=float, default=0.15)
    parser.add_argument("--max-ssim-delta", type=float, default=0.005)
    parser.add_argument("--max-lpips-delta", type=float, default=0.01)
    parser.add_argument("--max-gaussian-relative-delta", type=float, default=0.05)
    args = parser.parse_args()

    official_runtime = read_json(args.official / "mapping_replay_runtime.json")
    custom_runtime = read_json(args.custom / "mapping_replay_runtime.json")
    official_eval = read_evaluation_log(args.official / "evaluation.log")
    custom_eval = read_evaluation_log(args.custom / "evaluation.log")
    official_validation = read_json(args.official / "frozen_archive_validation.json")
    custom_validation = read_json(args.custom / "frozen_archive_validation.json")
    official_uids = read_json(args.official / "mapped_uids.json")
    custom_uids = read_json(args.custom / "mapped_uids.json")

    checks: dict[str, bool] = {}
    checks["archive_validation_valid"] = bool(
        official_validation.get("valid") and custom_validation.get("valid")
    )
    checks["archive_sha_equal"] = (
        official_runtime.get("archive_manifest_sha256")
        == custom_runtime.get("archive_manifest_sha256")
        == official_validation.get("archive_manifest_sha256")
        == custom_validation.get("archive_manifest_sha256")
    )
    checks["work_contract"] = (
        official_runtime.get("work_contract")
        == custom_runtime.get("work_contract")
        == "official_event_credit_v1"
        and official_runtime.get("time_scale") == "unbounded"
        and custom_runtime.get("time_scale") == "unbounded"
    )
    checks["all_events_processed"] = all(
        len(runtime.get("event_ids_fully_processed", []))
        == int(runtime.get("events_in_archive", -1))
        for runtime in (official_runtime, custom_runtime)
    )
    checks["event_ids_equal"] = (
        official_runtime.get("event_ids_fully_processed")
        == custom_runtime.get("event_ids_fully_processed")
    )
    checks["event_credit_ledger_equal"] = (
        event_ledger(official_runtime) == event_ledger(custom_runtime)
    )
    checks["optimizer_steps_equal"] = (
        official_runtime.get("optimizer_steps_completed")
        == custom_runtime.get("optimizer_steps_completed")
    )
    checks["view_updates_equal"] = (
        official_runtime.get("rasterized_view_updates")
        == custom_runtime.get("rasterized_view_updates")
    )
    checks["mapped_uids_equal"] = official_uids == custom_uids

    scheduler_zero_fields = (
        "mapping_packets_dropped_oldest",
        "mapping_packets_flushed_by_reset",
        "mapping_packets_preempted_by_control",
        "mapping_packets_pending_at_stop",
        "timeline_items_not_ingested",
    )
    checks["no_drop_preempt_pending"] = all(
        int(runtime["common_scheduler"].get(field, -1)) == 0
        for runtime in (official_runtime, custom_runtime)
        for field in scheduler_zero_fields
    )
    checks["packets_equal"] = (
        official_runtime["common_scheduler"].get("mapping_packets_completed")
        == custom_runtime["common_scheduler"].get("mapping_packets_completed")
        == official_runtime["common_scheduler"].get("mapping_packets_enqueued")
        == custom_runtime["common_scheduler"].get("mapping_packets_enqueued")
    )
    checks["zero_mapping_overlap"] = all(
        int(runtime.get("heldout_mapping_overlap_count", -1)) == 0
        and int(runtime.get("heldout_gaussian_origin_overlap_count", -1)) == 0
        for runtime in (official_runtime, custom_runtime)
    )
    checks["zero_tail"] = all(
        int(runtime.get("post_eos_optimizer_updates", -1)) == 0
        for runtime in (official_runtime, custom_runtime)
    )

    official_fixed = official_eval["predeclared_fixed_manifest_posthoc"]
    custom_fixed = custom_eval["predeclared_fixed_manifest_posthoc"]
    psnr_delta = float(custom_fixed["mean_psnr"]) - float(
        official_fixed["mean_psnr"]
    )
    ssim_delta = float(custom_fixed["mean_ssim"]) - float(
        official_fixed["mean_ssim"]
    )
    lpips_delta = float(custom_fixed["mean_lpips"]) - float(
        official_fixed["mean_lpips"]
    )
    checks["eval_view_count_equal"] = (
        official_fixed.get("view_count") == custom_fixed.get("view_count")
    )
    checks["eval_mapping_disjoint"] = all(
        bool(fixed.get("mapping_disjoint"))
        and int(fixed.get("mapping_view_overlap_count", -1)) == 0
        for fixed in (official_fixed, custom_fixed)
    )
    checks["psnr_delta"] = abs(psnr_delta) <= args.max_psnr_delta
    checks["ssim_delta"] = abs(ssim_delta) <= args.max_ssim_delta
    checks["lpips_delta"] = abs(lpips_delta) <= args.max_lpips_delta
    official_gaussians = int(official_runtime["gaussians"])
    custom_gaussians = int(custom_runtime["gaussians"])
    gaussian_relative_delta = abs(custom_gaussians - official_gaussians) / max(
        1, official_gaussians
    )
    checks["gaussian_relative_delta"] = (
        gaussian_relative_delta <= args.max_gaussian_relative_delta
    )

    result = {
        "protocol": "exp78b_fixed_work_parity_verifier_v1",
        "valid": all(checks.values()),
        "checks": checks,
        "official": {
            "run": str(args.official.resolve()),
            "psnr": official_fixed["mean_psnr"],
            "ssim": official_fixed["mean_ssim"],
            "lpips": official_fixed["mean_lpips"],
            "optimizer_steps": official_runtime["optimizer_steps_completed"],
            "view_updates": official_runtime["rasterized_view_updates"],
            "gaussians": official_gaussians,
            "mapping_wall_seconds": official_runtime["mapping_wall_seconds"],
        },
        "custom": {
            "run": str(args.custom.resolve()),
            "psnr": custom_fixed["mean_psnr"],
            "ssim": custom_fixed["mean_ssim"],
            "lpips": custom_fixed["mean_lpips"],
            "optimizer_steps": custom_runtime["optimizer_steps_completed"],
            "view_updates": custom_runtime["rasterized_view_updates"],
            "gaussians": custom_gaussians,
            "mapping_wall_seconds": custom_runtime["mapping_wall_seconds"],
        },
        "delta_custom_minus_official": {
            "psnr": psnr_delta,
            "ssim": ssim_delta,
            "lpips": lpips_delta,
            "gaussian_relative_abs": gaussian_relative_delta,
            "mapping_wall_seconds": float(custom_runtime["mapping_wall_seconds"])
            - float(official_runtime["mapping_wall_seconds"]),
        },
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
