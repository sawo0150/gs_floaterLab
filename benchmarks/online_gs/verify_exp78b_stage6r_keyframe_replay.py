#!/usr/bin/env python3
"""Fail-closed verifier for the predeclared Stage-6R R3 gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fixed_metric(run: Path) -> dict:
    value = read_json(run / "psnr" / "strict_fixed_manifest" / "final_result.json")
    return value["predeclared_fixed_manifest_posthoc"]


def check(report: dict, name: str, condition: bool, detail: object) -> None:
    report["checks"][name] = {"passed": bool(condition), "detail": detail}
    if not condition:
        report["valid"] = False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--r1", type=Path, required=True)
    parser.add_argument("--render-match-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    candidate = read_json(args.candidate / "mapping_replay_runtime.json")
    r1 = read_json(args.r1 / "mapping_replay_runtime.json")
    candidate_fixed = fixed_metric(args.candidate)
    r1_fixed = fixed_metric(args.r1)
    render_match = read_json(args.render_match_report)
    vanilla = render_match.get("result", {}).get("vanilla", {})
    dense_ledger = candidate.get("fixed_event_dense_opportunity_ledger") or []
    r1_dense_ledger = r1.get("fixed_event_dense_opportunity_ledger") or []
    keyframe_ledger = (
        candidate.get("fixed_event_keyframe_opportunity_ledger") or []
    )
    keyframe_summary = candidate.get("stage6r_keyframe_replay_summary") or {}

    report = {
        "protocol": "exp78b_stage6r_r3_keyframe_replay_gate_v1",
        "valid": True,
        "candidate": str(args.candidate.resolve()),
        "r1": str(args.r1.resolve()),
        "checks": {},
    }

    check(
        report,
        "frozen_r3_configuration",
        candidate.get("stage6r_keyframe_appearance_replay") is True
        and candidate.get("stage6r_source_quota_protocol")
        == "fixed_one_dense_then_one_keyframe_per_eligible_packet_v1"
        and candidate.get("comparison_contract")
        == "stage6r_r3_dense_plus_keyframe_appearance_c1_c2_v1"
        and candidate.get("work_contract")
        == "d1_native_fixed_dense_plus_keyframe_opportunity_pair_v1"
        and int(candidate.get("compute_paced_dense_token_cost", -1)) == 1
        and candidate.get("include_keyframes_in_replay") is False
        and candidate.get("dense_replay_gradient_scope") == "appearance",
        {
            "source_quota": candidate.get("stage6r_source_quota_protocol"),
            "comparison": candidate.get("comparison_contract"),
            "work": candidate.get("work_contract"),
            "dense_token_cost": candidate.get("compute_paced_dense_token_cost"),
            "ordinary_mixed_replay": candidate.get("include_keyframes_in_replay"),
            "scope": candidate.get("dense_replay_gradient_scope"),
        },
    )
    check(
        report,
        "same_archive_event_and_tracking_kfs",
        candidate.get("archive_manifest_sha256") == r1.get("archive_manifest_sha256")
        and [event.get("event_id") for event in candidate.get("events", [])]
        == [event.get("event_id") for event in r1.get("events", [])]
        and candidate.get("gaussian_origin_uids") == r1.get("gaussian_origin_uids"),
        {
            "archive": candidate.get("archive_manifest_sha256"),
            "candidate_events": len(candidate.get("events", [])),
            "r1_events": len(r1.get("events", [])),
            "candidate_origin_uids": len(candidate.get("gaussian_origin_uids", [])),
            "r1_origin_uids": len(r1.get("gaussian_origin_uids", [])),
        },
    )
    candidate_dense_trace = [row.get("selected_keys") for row in dense_ledger]
    r1_dense_trace = [row.get("selected_keys") for row in r1_dense_ledger]
    check(
        report,
        "dense_c1_c2_trace_unchanged",
        candidate_dense_trace == r1_dense_trace
        and candidate.get("dense_selected_frame_uids")
        == r1.get("dense_selected_frame_uids")
        and candidate.get("dense_registered_frame_uids")
        == r1.get("dense_registered_frame_uids"),
        {
            "candidate_opportunities": len(candidate_dense_trace),
            "r1_opportunities": len(r1_dense_trace),
            "candidate_selected_unique": candidate.get("dense_selected_unique_views"),
            "r1_selected_unique": r1.get("dense_selected_unique_views"),
            "candidate_registered_unique": candidate.get("dense_registered_unique_views"),
            "r1_registered_unique": r1.get("dense_registered_unique_views"),
        },
    )
    dense_event_ids = [int(row["event_id"]) for row in dense_ledger]
    keyframe_event_ids = [int(row["event_id"]) for row in keyframe_ledger]
    keyframe_rows_valid = all(
        int(row.get("optimizer_steps_completed", -1)) == 1
        and int(row.get("rasterized_view_updates", -1)) == 1
        and len(row.get("selected_keys") or []) == 1
        and row["selected_keys"][0][0] == "keyframe"
        for row in keyframe_ledger
    )
    check(
        report,
        "exact_one_dense_plus_one_keyframe_per_packet",
        len(dense_ledger) > 0
        and dense_event_ids == keyframe_event_ids
        and keyframe_rows_valid,
        {
            "dense_opportunities": len(dense_ledger),
            "keyframe_opportunities": len(keyframe_ledger),
            "same_event_trace": dense_event_ids == keyframe_event_ids,
            "keyframe_rows_valid": keyframe_rows_valid,
        },
    )
    expected_extra = len(keyframe_ledger)
    check(
        report,
        "only_predeclared_work_added",
        int(candidate.get("rasterized_view_updates", -1))
        == int(r1.get("rasterized_view_updates", -2)) + expected_extra
        and int(candidate.get("optimizer_steps_completed", -1))
        == int(r1.get("optimizer_steps_completed", -2)) + expected_extra,
        {
            "candidate_renders": candidate.get("rasterized_view_updates"),
            "r1_renders": r1.get("rasterized_view_updates"),
            "candidate_adam": candidate.get("optimizer_steps_completed"),
            "r1_adam": r1.get("optimizer_steps_completed"),
            "extra_keyframe_steps": expected_extra,
            # Appearance replay does not directly update geometry groups, but
            # it can change later native frontier residuals and therefore the
            # data-dependent topology outcome.  GS count is reported, not
            # equality-gated; the contract gates work paths and gradients.
            "candidate_gaussians": candidate.get("gaussians"),
            "r1_gaussians": r1.get("gaussians"),
        },
    )
    scope = candidate.get("effective_replay_source_scope_optimizer_steps") or {}
    lr_steps = candidate.get("stage6r_source_lr_steps") or {}
    check(
        report,
        "appearance_only_separate_source_clocks",
        int(scope.get("dense:appearance", -1)) == len(dense_ledger)
        and int(scope.get("keyframe:appearance", -1)) == len(keyframe_ledger)
        and set(scope) <= {"dense:appearance", "keyframe:appearance"}
        and int(lr_steps.get("dense", -1))
        == int(lr_steps.get("keyframe", -2)),
        {"scope_steps": scope, "source_lr_steps": lr_steps},
    )
    admitted = int(keyframe_summary.get("admitted_candidates", -1))
    selected = int(keyframe_summary.get("selected_unique_candidates", -1))
    selected_ratio = selected / admitted if admitted > 0 else 0.0
    check(
        report,
        "keyframe_c1_c2_coverage",
        keyframe_summary.get("protocol")
        == "keyframe_c1_service1_global_residue_c2_v1"
        and admitted > 0
        and selected_ratio >= 0.90
        and int(keyframe_summary.get("no_prepurchase_violations", -1)) == 0
        and keyframe_summary.get("future_frames_used") is False
        and keyframe_summary.get("dataset_name_used") is False
        and keyframe_summary.get("stream_horizon_used") is False
        and int(keyframe_summary.get("service_shortfall_global_epoch_no_repeat", -1)) == 1
        and int(keyframe_summary.get("service_shortfall_pending_draw_attempts", -1)) == 0,
        {
            "admitted": admitted,
            "selected_unique": selected,
            "selected_over_admitted": selected_ratio,
            "service_commits": keyframe_summary.get("service_commits"),
            "global_epochs_completed": keyframe_summary.get("service_shortfall_global_epochs_completed"),
            "global_residue": keyframe_summary.get("service_shortfall_global_epoch_remaining"),
        },
    )
    check(
        report,
        "fixed_evaluator_disjoint_zero_tail",
        int(candidate_fixed.get("view_count", -1)) == int(r1_fixed.get("view_count", -2))
        and bool(candidate_fixed.get("mapping_disjoint"))
        and int(candidate.get("heldout_mapping_overlap_count", -1)) == 0
        and int(candidate.get("heldout_gaussian_origin_overlap_count", -1)) == 0
        and int(candidate.get("post_eos_optimizer_updates", -1)) == 0
        and candidate.get("final_ba_performed") is False
        and candidate.get("final_color_refinement_performed") is False,
        {
            "views": candidate_fixed.get("view_count"),
            "mapping_disjoint": candidate_fixed.get("mapping_disjoint"),
            "tail": candidate.get("post_eos_optimizer_updates"),
        },
    )
    retention_delta = float(candidate_fixed["mean_psnr"]) - float(r1_fixed["mean_psnr"])
    vanilla_delta = float(candidate_fixed["mean_psnr"]) - float(vanilla.get("psnr", 1e9))
    check(
        report,
        "r1_quality_retained_within_0p10_db",
        retention_delta >= -0.10,
        {
            "candidate_psnr": candidate_fixed["mean_psnr"],
            "r1_psnr": r1_fixed["mean_psnr"],
            "delta_db": retention_delta,
        },
    )
    check(
        report,
        "render_match_audit_and_plus_1db",
        render_match.get("valid") is True and vanilla_delta >= 1.0,
        {
            "render_match_valid": render_match.get("valid"),
            "candidate_psnr": candidate_fixed["mean_psnr"],
            "vanilla_psnr": vanilla.get("psnr"),
            "delta_db": vanilla_delta,
        },
    )
    report["result"] = {
        "candidate": {
            "psnr": candidate_fixed["mean_psnr"],
            "ssim": candidate_fixed["mean_ssim"],
            "lpips": candidate_fixed["mean_lpips"],
            "renders": candidate.get("rasterized_view_updates"),
            "optimizer_steps": candidate.get("optimizer_steps_completed"),
            "gaussians": candidate.get("gaussians"),
            "dense_selected_unique": candidate.get("dense_selected_unique_views"),
            "keyframe_selected_unique": selected,
        },
        "r1": {
            "psnr": r1_fixed["mean_psnr"],
            "ssim": r1_fixed["mean_ssim"],
            "lpips": r1_fixed["mean_lpips"],
        },
        "vanilla": vanilla,
        "candidate_minus_r1_psnr": retention_delta,
        "candidate_minus_vanilla_psnr": vanilla_delta,
        "keyframe_selected_over_admitted": selected_ratio,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
