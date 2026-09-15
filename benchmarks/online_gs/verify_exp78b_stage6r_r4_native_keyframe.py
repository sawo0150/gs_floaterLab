#!/usr/bin/env python3
"""Fail-closed verifier for Stage-6R R4 native keyframe ERCB."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable


EXPECTED_PROTOCOL = "exp78b_gsslam_frozen_mapping_replay_v29"
EXPECTED_WORK = (
    "d1_native_fixed_dense_plus_keyframe_opportunity_pair_"
    "with_native_global_audit_v1"
)
CONTROL_CONTRACT = "stage6r_r4_native_global_uniform_control_v1"
CANDIDATE_CONTRACT = "stage6r_r4_native_global_keyframe_ercb_v1"
BALANCED_PHASES = {"balanced", "replay"}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def check(
    report: dict[str, Any], name: str, condition: bool, detail: object
) -> None:
    report["checks"][name] = {"passed": bool(condition), "detail": detail}
    if not condition:
        report["valid"] = False


def tracking_uids(runtime: dict[str, Any]) -> list[int]:
    dense = {int(value) for value in runtime.get("dense_selected_frame_uids", [])}
    mapped = {int(value) for value in runtime.get("mapped_frame_uids", [])}
    return sorted(mapped - dense)


def event_signature(runtime: dict[str, Any]) -> list[dict[str, Any]]:
    keys = (
        "event_id",
        "kind",
        "filtered_frame_uids",
        "policy_skip",
        "completed",
        "frontier_optimizer_steps_completed",
        "frontier_rasterized_view_updates",
        "fixed_dense_optimizer_steps_completed",
        "fixed_dense_rasterized_view_updates",
        "fixed_keyframe_optimizer_steps_completed",
        "fixed_keyframe_rasterized_view_updates",
        "optimizer_steps_completed",
        "rasterized_view_updates",
    )
    return [
        {key: event.get(key) for key in keys}
        for event in runtime.get("events", [])
    ]


def native_alignment_signature(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "audit_index",
        "map_generation",
        "mapping_iteration",
        "frontier_iteration_count_before",
        "controller_phase",
        "pool_uids",
        "requested_slots",
        "uniform_shadow_uids",
    )
    return {key: row.get(key) for key in keys}


def validate_global_residue(
    ledger: list[dict[str, Any]],
) -> tuple[bool, dict[str, Any]]:
    """Replay growing-pool global residue from committed ledger identities."""
    remaining_by_generation: dict[int, set[int]] = {}
    previous_pool_by_generation: dict[int, set[int]] = {}
    epochs_completed = 0
    boundary_crossings = 0
    violations: list[dict[str, Any]] = []
    for row_index, row in enumerate(ledger):
        if not row.get("ercb_active"):
            continue
        generation = int(row.get("map_generation", -1))
        pool = {int(value) for value in row.get("pool_uids", [])}
        selected = [int(value) for value in row.get("selected_uids", [])]
        previous_pool = previous_pool_by_generation.get(generation, set())
        if generation not in remaining_by_generation:
            remaining = set(pool)
        else:
            remaining = remaining_by_generation[generation]
            remaining.difference_update(previous_pool - pool)
            remaining.update(pool - previous_pool)
        if len(selected) != len(set(selected)):
            violations.append(
                {"row": row_index, "reason": "duplicate_within_batch"}
            )
        for uid in selected:
            if uid not in pool:
                violations.append(
                    {"row": row_index, "reason": "selected_outside_pool", "uid": uid}
                )
                continue
            if uid not in remaining:
                if remaining:
                    violations.append(
                        {
                            "row": row_index,
                            "reason": "repeat_before_residue_exhaustion",
                            "uid": uid,
                            "remaining": len(remaining),
                        }
                    )
                else:
                    epochs_completed += 1
                    boundary_crossings += 1
                    remaining = set(pool)
            remaining.discard(uid)
        remaining_by_generation[generation] = remaining
        previous_pool_by_generation[generation] = pool
    return not violations, {
        "ercb_rows": sum(bool(row.get("ercb_active")) for row in ledger),
        "reconstructed_completed_epochs": epochs_completed,
        "reconstructed_boundary_crossings": boundary_crossings,
        "terminal_residue_by_generation": {
            str(key): len(value) for key, value in remaining_by_generation.items()
        },
        "violations": violations[:20],
    }


def anchor_cohort_service_balance(
    ledger: list[dict[str, Any]],
) -> dict[str, Any]:
    """Measure service dispersion for equally long-lived balanced cohorts."""
    rows_by_generation: dict[int, list[dict[str, Any]]] = {}
    for row in ledger:
        if row.get("controller_phase") not in BALANCED_PHASES:
            continue
        rows_by_generation.setdefault(
            int(row.get("map_generation", -1)), []
        ).append(row)
    generations: list[dict[str, Any]] = []
    for generation, rows in sorted(rows_by_generation.items()):
        stable_anchor = set(int(value) for value in rows[0].get("pool_uids", []))
        for row in rows[1:]:
            stable_anchor.intersection_update(
                int(value) for value in row.get("pool_uids", [])
            )
        if not stable_anchor:
            continue
        counts = {uid: 0 for uid in stable_anchor}
        for row in rows:
            for uid in row.get("selected_uids", []):
                uid = int(uid)
                if uid in counts:
                    counts[uid] += 1
        values = list(counts.values())
        service_mean = mean(float(value) for value in values)
        variance = mean(
            (float(value) - service_mean) ** 2 for value in values
        )
        generations.append(
            {
                "map_generation": generation,
                "balanced_rows": len(rows),
                "stable_anchor_keyframes": len(stable_anchor),
                "service_min": min(values),
                "service_max": max(values),
                "service_spread": max(values) - min(values),
                "service_mean": service_mean,
                "service_coefficient_of_variation": (
                    math.sqrt(variance) / service_mean
                    if service_mean > 0.0
                    else math.inf
                ),
            }
        )
    return {
        "generations": generations,
        "eligible_generations": len(generations),
        "mean_service_spread": (
            mean(float(row["service_spread"]) for row in generations)
            if generations
            else math.inf
        ),
        "mean_service_coefficient_of_variation": (
            mean(
                float(row["service_coefficient_of_variation"])
                for row in generations
            )
            if generations
            else math.inf
        ),
    }


def fixed_rows(run: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    result = read_json(
        run / "psnr" / "strict_fixed_manifest" / "final_result.json"
    )
    raw_rows = result.get("per_view", [])
    rows = [
        row
        for row in raw_rows
        if isinstance(row, dict)
        and row.get("predeclared_fixed_manifest_split") is True
    ]
    rows.sort(
        key=lambda row: (int(row.get("frame_index", -1)), str(row.get("uid", "")))
    )
    summary = result.get("predeclared_fixed_manifest_posthoc", {})
    return rows, summary if isinstance(summary, dict) else {}


def mean(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        raise ValueError("cannot average empty values")
    return math.fsum(values) / len(values)


def array_split(values: list[float], parts: int) -> list[list[float]]:
    quotient, remainder = divmod(len(values), parts)
    output: list[list[float]] = []
    start = 0
    for index in range(parts):
        stop = start + quotient + int(index < remainder)
        output.append(values[start:stop])
        start = stop
    return output


def quality_pair(control_run: Path, candidate_run: Path) -> tuple[bool, dict[str, Any]]:
    control_rows, control_summary = fixed_rows(control_run)
    candidate_rows, candidate_summary = fixed_rows(candidate_run)
    control_uids = [str(row.get("uid")) for row in control_rows]
    candidate_uids = [str(row.get("uid")) for row in candidate_rows]
    aligned = (
        len(control_uids) > 0
        and len(set(control_uids)) == len(control_uids)
        and control_uids == candidate_uids
        and int(control_summary.get("view_count", -1)) == len(control_uids)
        and int(candidate_summary.get("view_count", -1)) == len(candidate_uids)
        and control_summary.get("mapping_disjoint") is True
        and candidate_summary.get("mapping_disjoint") is True
    )
    if not aligned:
        return False, {
            "reason": "fixed held-out evaluator UIDs are not aligned and disjoint",
            "control_count": len(control_uids),
            "candidate_count": len(candidate_uids),
            "same_uids": control_uids == candidate_uids,
        }
    control = [float(row["psnr"]) for row in control_rows]
    candidate = [float(row["psnr"]) for row in candidate_rows]
    q1_size = len(control) // 4
    hard_indices = sorted(range(len(control)), key=lambda index: control[index])[
        :q1_size
    ]
    control_thirds = [mean(part) for part in array_split(control, 3)]
    candidate_thirds = [mean(part) for part in array_split(candidate, 3)]
    return True, {
        "view_count": len(control),
        "q1_size": q1_size,
        "control": {
            "psnr": float(control_summary["mean_psnr"]),
            "ssim": float(control_summary["mean_ssim"]),
            "lpips": float(control_summary["mean_lpips"]),
        },
        "candidate": {
            "psnr": float(candidate_summary["mean_psnr"]),
            "ssim": float(candidate_summary["mean_ssim"]),
            "lpips": float(candidate_summary["mean_lpips"]),
        },
        "candidate_minus_control": {
            "psnr": float(candidate_summary["mean_psnr"])
            - float(control_summary["mean_psnr"]),
            "ssim": float(candidate_summary["mean_ssim"])
            - float(control_summary["mean_ssim"]),
            "lpips": float(candidate_summary["mean_lpips"])
            - float(control_summary["mean_lpips"]),
        },
        "control_hard_q1_psnr": mean(control[index] for index in hard_indices),
        "candidate_on_control_hard_q1_psnr": mean(
            candidate[index] for index in hard_indices
        ),
        "control_hard_q1_delta": mean(
            candidate[index] - control[index] for index in hard_indices
        ),
        "temporal_thirds_control": control_thirds,
        "temporal_thirds_candidate": candidate_thirds,
        "temporal_thirds_delta": [
            right - left
            for left, right in zip(control_thirds, candidate_thirds)
        ],
    }


def build_report(
    control_run: Path,
    candidate_run: Path,
    *,
    structural_only: bool,
    render_match_report: Path | None = None,
) -> dict[str, Any]:
    control = read_json(control_run / "mapping_replay_runtime.json")
    candidate = read_json(candidate_run / "mapping_replay_runtime.json")
    control_ledger = control.get(
        "stage6r_native_global_keyframe_selection_ledger"
    ) or []
    candidate_ledger = candidate.get(
        "stage6r_native_global_keyframe_selection_ledger"
    ) or []
    control_summary = control.get(
        "stage6r_native_global_keyframe_selection_summary"
    ) or {}
    candidate_summary = candidate.get(
        "stage6r_native_global_keyframe_selection_summary"
    ) or {}
    report: dict[str, Any] = {
        "protocol": "exp78b_stage6r_r4_native_keyframe_verifier_v1",
        "mode": "structural_only" if structural_only else "final",
        "valid": True,
        "control": str(control_run.resolve()),
        "candidate": str(candidate_run.resolve()),
        "checks": {},
    }

    common_r3 = all(
        run.get("protocol") == EXPECTED_PROTOCOL
        and run.get("work_contract") == EXPECTED_WORK
        and run.get("stage6r_keyframe_appearance_replay") is True
        and run.get("stage6r_native_global_keyframe_selection_audit") is True
        and run.get("c1_c2_global_residue_integration") is True
        and run.get("service_shortfall_ercb_requested") is True
        and run.get("compute_paced_dense_admission") is True
        and int(run.get("compute_paced_dense_token_cost", -1)) == 1
        and int(run.get("fixed_event_dense_opportunities_per_packet", -1)) == 1
        and run.get("mapping_profile") == "dense_rr_imu"
        and run.get("observation_topology_gate_requested") is True
        and run.get("dense_replay_gradient_scope") == "appearance"
        and run.get("include_keyframes_in_replay") is False
        for run in (control, candidate)
    )
    check(
        report,
        "frozen_r3_backbone_and_r4_roles",
        common_r3
        and control.get("stage6r_native_global_keyframe_ercb") is False
        and candidate.get("stage6r_native_global_keyframe_ercb") is True
        and control.get("comparison_contract") == CONTROL_CONTRACT
        and candidate.get("comparison_contract") == CANDIDATE_CONTRACT,
        {
            "control_contract": control.get("comparison_contract"),
            "candidate_contract": candidate.get("comparison_contract"),
            "control_ercb": control.get("stage6r_native_global_keyframe_ercb"),
            "candidate_ercb": candidate.get("stage6r_native_global_keyframe_ercb"),
        },
    )
    control_provenance = control.get("runtime_provenance", {})
    candidate_provenance = candidate.get("runtime_provenance", {})
    check(
        report,
        "same_clean_source_archive_and_config",
        control.get("custom_commit") == candidate.get("custom_commit")
        and control_provenance.get("active_source_sha256")
        == candidate_provenance.get("active_source_sha256")
        and control_provenance.get("custom_git_diff_sha256")
        == candidate_provenance.get("custom_git_diff_sha256")
        == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        and control.get("archive_manifest_sha256")
        == candidate.get("archive_manifest_sha256")
        and control.get("config_sha256") == candidate.get("config_sha256")
        and control.get("effective_config_sha256")
        == candidate.get("effective_config_sha256"),
        {
            "control_commit": control.get("custom_commit"),
            "candidate_commit": candidate.get("custom_commit"),
            "archive": control.get("archive_manifest_sha256"),
            "config": control.get("config_sha256"),
        },
    )
    control_tracking = tracking_uids(control)
    candidate_tracking = tracking_uids(candidate)
    control_events = event_signature(control)
    candidate_events = event_signature(candidate)
    check(
        report,
        "same_event_and_tracking_keyframe_contract",
        control_tracking == candidate_tracking
        and control_events == candidate_events,
        {
            "control_tracking_kfs": len(control_tracking),
            "candidate_tracking_kfs": len(candidate_tracking),
            "control_events": len(control_events),
            "candidate_events": len(candidate_events),
            "same_event_signature": control_events == candidate_events,
        },
    )
    work_keys = (
        "optimizer_steps_completed",
        "main_gaussian_optimizer_steps_completed",
        "auxiliary_adam_steps_completed",
        "rasterized_view_updates",
    )
    check(
        report,
        "same_adam_and_physical_render_work",
        all(control.get(key) == candidate.get(key) for key in work_keys),
        {
            key: {"control": control.get(key), "candidate": candidate.get(key)}
            for key in work_keys
        },
    )
    dense_keys = (
        "fixed_event_dense_opportunity_ledger",
        "dense_admission_ledger",
        "dense_registered_frame_uids",
        "dense_selected_frame_uids",
        "mapping_replay_summary",
    )
    keyframe_keys = (
        "fixed_event_keyframe_opportunity_ledger",
        "stage6r_keyframe_replay_summary",
        "stage6r_keyframe_selected_frame_uids",
        "stage6r_source_lr_steps",
        "effective_replay_source_scope_optimizer_steps",
    )
    check(
        report,
        "exact_dense_and_auxiliary_keyframe_traces",
        all(control.get(key) == candidate.get(key) for key in dense_keys + keyframe_keys),
        {
            "dense_opportunities": len(control.get("fixed_event_dense_opportunity_ledger") or []),
            "keyframe_opportunities": len(control.get("fixed_event_keyframe_opportunity_ledger") or []),
            "dense_trace_equal": all(control.get(key) == candidate.get(key) for key in dense_keys),
            "aux_keyframe_trace_equal": all(control.get(key) == candidate.get(key) for key in keyframe_keys),
        },
    )
    alignment_equal = (
        len(control_ledger) > 0
        and len(control_ledger) == len(candidate_ledger)
        and [native_alignment_signature(row) for row in control_ledger]
        == [native_alignment_signature(row) for row in candidate_ledger]
    )
    check(
        report,
        "same_native_historical_pool_slots_and_uniform_shadow",
        alignment_equal,
        {
            "control_rows": len(control_ledger),
            "candidate_rows": len(candidate_ledger),
            "alignment_equal": alignment_equal,
        },
    )
    control_rows_valid = all(
        row.get("selected_uids") == row.get("uniform_shadow_uids")
        and row.get("ercb_active") is False
        and row.get("optimizer_committed") is True
        and len(row.get("selected_uids") or [])
        == int(row.get("requested_slots", -1))
        for row in control_ledger
    )
    check(
        report,
        "uniform_control_is_exact_native_selector",
        len(control_ledger) > 0
        and control_summary.get("audit_enabled") is True
        and control_summary.get("ercb_after_balanced") is False
        and control_summary.get("final_queue") is None
        and control_rows_valid,
        {
            "rows": len(control_ledger),
            "rows_valid": control_rows_valid,
            "summary": control_summary,
        },
    )
    candidate_rows_valid = all(
        len(row.get("selected_uids") or [])
        == int(row.get("requested_slots", -1))
        and len(set(row.get("selected_uids") or []))
        == len(row.get("selected_uids") or [])
        and set(row.get("selected_uids") or []) <= set(row.get("pool_uids") or [])
        and row.get("optimizer_committed") is True
        and bool(row.get("ercb_active"))
        == (
            row.get("controller_phase") in BALANCED_PHASES
            and int(row.get("requested_slots", 0)) > 0
        )
        and (
            row.get("selected_uids") == row.get("uniform_shadow_uids")
            if row.get("controller_phase") == "frontier"
            else True
        )
        for row in candidate_ledger
    )
    check(
        report,
        "candidate_changes_only_balanced_or_replay_identity",
        len(candidate_ledger) > 0
        and candidate_summary.get("audit_enabled") is True
        and candidate_summary.get("ercb_after_balanced") is True
        and int(candidate_summary.get("balanced_or_replay_entries", 0)) > 0
        and int(candidate_summary.get("ercb_active_entries", -1))
        == int(candidate_summary.get("balanced_or_replay_entries", -2))
        and candidate_rows_valid,
        {
            "rows": len(candidate_ledger),
            "balanced_or_replay": candidate_summary.get("balanced_or_replay_entries"),
            "ercb_active": candidate_summary.get("ercb_active_entries"),
            "rows_valid": candidate_rows_valid,
        },
    )
    residue_valid, residue_detail = validate_global_residue(candidate_ledger)
    queue = candidate_summary.get("final_queue") or {}
    queue_valid = (
        queue.get("protocol") == "native_global_keyframe_ercb_v1"
        and int(queue.get("service_shortfall_block_size", -1)) == 8
        and abs(float(queue.get("service_shortfall_relative_floor_ratio", -1)) - 0.75) < 1e-12
        and abs(float(queue.get("service_shortfall_max_bonus", -1)) - 1.5) < 1e-12
        and int(queue.get("service_shortfall_global_epoch_no_repeat", -1)) == 1
        and int(queue.get("service_shortfall_pending_draw_attempts", -1)) == 0
        and int(queue.get("duplicate_within_batch_violations", -1)) == 0
        and int(queue.get("cancelled_proposals", -1)) == 0
        and queue.get("future_frames_used") is False
        and queue.get("dataset_name_used") is False
        and queue.get("stream_horizon_used") is False
    )
    check(
        report,
        "transactional_global_residue_ercb",
        residue_valid and queue_valid,
        {"reconstruction": residue_detail, "final_queue": queue},
    )
    check(
        report,
        "causal_disjoint_zero_tail_no_final_refinement",
        all(
            int(run.get("post_eos_optimizer_updates", -1)) == 0
            and int(run.get("heldout_mapping_overlap_count", -1)) == 0
            and int(run.get("heldout_gaussian_origin_overlap_count", -1)) == 0
            and run.get("final_ba_performed") is False
            and run.get("final_color_refinement_performed") is False
            and run.get("terminal_pruning_performed") is False
            for run in (control, candidate)
        ),
        {
            "control_tail": control.get("post_eos_optimizer_updates"),
            "candidate_tail": candidate.get("post_eos_optimizer_updates"),
            "control_overlap": control.get("heldout_mapping_overlap_count"),
            "candidate_overlap": candidate.get("heldout_mapping_overlap_count"),
        },
    )

    control_unique = int(control_summary.get("balanced_selected_unique_views", -1))
    candidate_unique = int(candidate_summary.get("balanced_selected_unique_views", -1))
    control_balance = anchor_cohort_service_balance(control_ledger)
    candidate_balance = anchor_cohort_service_balance(candidate_ledger)
    balance_improved = (
        int(control_balance["eligible_generations"]) > 0
        and int(control_balance["eligible_generations"])
        == int(candidate_balance["eligible_generations"])
        and float(candidate_balance["mean_service_spread"])
        < float(control_balance["mean_service_spread"])
        and float(candidate_balance["mean_service_coefficient_of_variation"])
        < float(control_balance["mean_service_coefficient_of_variation"])
    )
    report["structural_result"] = {
        "native_ledger_entries": len(candidate_ledger),
        "balanced_or_replay_entries": candidate_summary.get("balanced_or_replay_entries"),
        "control_balanced_unique_historical_keyframes": control_unique,
        "candidate_balanced_unique_historical_keyframes": candidate_unique,
        "candidate_unique_minus_control": candidate_unique - control_unique,
        "control_anchor_cohort_service_balance": control_balance,
        "candidate_anchor_cohort_service_balance": candidate_balance,
        "anchor_cohort_service_balance_strictly_improved": balance_improved,
        "candidate_final_queue": queue,
        "global_residue_reconstruction": residue_detail,
        "control_gaussians": control.get("gaussians"),
        "candidate_gaussians": candidate.get("gaussians"),
    }
    if structural_only:
        return report

    quality_valid, quality = quality_pair(control_run, candidate_run)
    check(report, "same_fixed_heldout_evaluator", quality_valid, quality)
    render_match = (
        read_json(render_match_report)
        if render_match_report is not None
        else {}
    )
    vanilla = render_match.get("result", {}).get("vanilla", {})
    candidate_psnr = float(quality.get("candidate", {}).get("psnr", -1e9))
    control_psnr = float(quality.get("control", {}).get("psnr", 1e9))
    vanilla_psnr = float(vanilla.get("psnr", 1e9))
    delta_control = candidate_psnr - control_psnr
    delta_vanilla = candidate_psnr - vanilla_psnr
    retention_pass = (
        quality_valid
        and render_match.get("valid") is True
        and delta_control >= -0.10
        and delta_vanilla >= 1.00
    )
    promotion_pass = (
        retention_pass
        and balance_improved
        and delta_control > 0.0
    )
    check(
        report,
        "retains_r3_and_plus_1db_vanilla",
        retention_pass,
        {
            "candidate_psnr": candidate_psnr,
            "control_psnr": control_psnr,
            "vanilla_psnr": vanilla.get("psnr"),
            "candidate_minus_control_db": delta_control,
            "candidate_minus_vanilla_db": delta_vanilla,
            "render_match_valid": render_match.get("valid"),
        },
    )
    report["quality_result"] = quality
    report["quality_result"]["vanilla"] = vanilla
    report["quality_result"]["candidate_minus_vanilla_psnr"] = delta_vanilla
    report["decision"] = {
        "retention_pass": retention_pass,
        "historical_unique_coverage_saturated": candidate_unique == control_unique,
        "anchor_cohort_service_balance_strictly_improved": balance_improved,
        "positive_primary_psnr_delta": delta_control > 0.0,
        "promote_r4_into_full": promotion_pass,
        "outcome": (
            "promote"
            if promotion_pass
            else "retain_as_quality_neutral"
            if retention_pass
            else "reject"
        ),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--render-match-report", type=Path)
    parser.add_argument("--structural-only", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.structural_only and args.render_match_report is None:
        parser.error("final mode requires --render-match-report")
    report = build_report(
        args.control,
        args.candidate,
        structural_only=args.structural_only,
        render_match_report=args.render_match_report,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
