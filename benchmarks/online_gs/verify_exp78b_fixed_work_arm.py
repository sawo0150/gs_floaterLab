#!/usr/bin/env python3
"""Verify a fixed-work exp78-B candidate against a frozen vanilla reference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_evaluation(run: Path) -> dict[str, Any]:
    result = run / "psnr" / "strict_fixed_manifest" / "final_result.json"
    if result.is_file():
        return read_json(result)
    text = (run / "evaluation.log").read_text(encoding="utf-8")
    marker = '\n{\n  "protocol": "exp78_split_audit_v2"'
    offset = text.rfind(marker)
    if offset < 0:
        raise ValueError(f"could not locate evaluation JSON in {run}")
    return json.loads(text[offset + 1 :])


def event_credit_ledger(
    runtime: dict[str, Any], *, include_view_updates: bool
) -> list[dict[str, Any]]:
    keys = (
        "event_id",
        "kind",
        "filtered_frame_uids",
        "optimizer_steps_completed",
        "completed",
        "policy_skip",
    )
    if include_view_updates:
        keys = (*keys, "rasterized_view_updates")
    output = []
    for event in runtime.get("events", []):
        record = {key: event.get(key) for key in keys}
        record["filtered_frame_uids"] = record["filtered_frame_uids"] or []
        record["optimizer_steps_completed"] = (
            record["optimizer_steps_completed"] or 0
        )
        if include_view_updates:
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


def metrics(run: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    runtime = read_json(run / "mapping_replay_runtime.json")
    evaluation = read_evaluation(run)["predeclared_fixed_manifest_posthoc"]
    return runtime, evaluation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-dense-selection", action="store_true")
    parser.add_argument("--require-compute-paced", action="store_true")
    parser.add_argument("--require-imu-shaper", action="store_true")
    parser.add_argument("--require-ercb", action="store_true")
    parser.add_argument("--require-online-density", action="store_true")
    parser.add_argument("--require-density-disabled", action="store_true")
    parser.add_argument("--require-auto-topology", action="store_true")
    parser.add_argument("--forbid-auto-topology", action="store_true")
    parser.add_argument(
        "--require-newborn-consolidation", action="store_true"
    )
    parser.add_argument(
        "--require-dedicated-dense-allocation", action="store_true"
    )
    parser.add_argument(
        "--mode",
        choices=("fixed-iteration", "fixed-iteration-allocation", "exact-view"),
        default="fixed-iteration",
    )
    args = parser.parse_args()

    reference, reference_eval = metrics(args.reference)
    candidate, candidate_eval = metrics(args.candidate)
    reference_validation = read_json(
        args.reference / "frozen_archive_validation.json"
    )
    candidate_validation = read_json(
        args.candidate / "frozen_archive_validation.json"
    )

    checks: dict[str, bool] = {}
    checks["archive_validation_valid"] = bool(
        reference_validation.get("valid") and candidate_validation.get("valid")
    )
    checks["archive_sha_equal"] = (
        reference.get("archive_manifest_sha256")
        == candidate.get("archive_manifest_sha256")
        == reference_validation.get("archive_manifest_sha256")
        == candidate_validation.get("archive_manifest_sha256")
    )
    checks["fixed_iteration_contract"] = all(
        runtime.get("work_contract")
        in {"official_event_credit_v1", "official_event_adam_v1"}
        and runtime.get("time_scale") == "unbounded"
        for runtime in (reference, candidate)
    )
    checks["event_ids_equal_complete"] = (
        reference.get("event_ids_fully_processed")
        == candidate.get("event_ids_fully_processed")
        and len(reference.get("event_ids_fully_processed", []))
        == int(reference.get("events_in_archive", -1))
        and len(candidate.get("event_ids_fully_processed", []))
        == int(candidate.get("events_in_archive", -1))
    )
    checks["event_iteration_ledger_equal"] = (
        event_credit_ledger(reference, include_view_updates=False)
        == event_credit_ledger(candidate, include_view_updates=False)
    )
    checks["optimizer_steps_equal"] = (
        reference.get("optimizer_steps_completed")
        == candidate.get("optimizer_steps_completed")
    )
    reference_view_updates = int(reference.get("rasterized_view_updates", -1))
    candidate_view_updates = int(candidate.get("rasterized_view_updates", -1))
    candidate_dense_draws = int(
        candidate.get("mapping_replay_summary", {}).get("draw_count", 0)
    )
    if args.mode == "exact-view":
        checks["view_updates_equal"] = (
            reference_view_updates == candidate_view_updates
        )
    elif args.mode == "fixed-iteration":
        reference_events = {
            int(event["event_id"]): int(event.get("rasterized_view_updates", 0))
            for event in reference.get("events", [])
        }
        candidate_events = {
            int(event["event_id"]): int(event.get("rasterized_view_updates", 0))
            for event in candidate.get("events", [])
        }
        per_event_extra = {
            event_id: candidate_events[event_id] - reference_views
            for event_id, reference_views in reference_events.items()
        }
        checks["candidate_never_removes_reference_views"] = all(
            extra >= 0 for extra in per_event_extra.values()
        )
        checks["auxiliary_dense_views_exactly_accounted"] = (
            candidate_view_updates - reference_view_updates
            == candidate_dense_draws
            == sum(per_event_extra.values())
        )
    else:
        checks["method_specific_view_allocation_declared"] = (
            candidate.get("comparison_contract")
            == "official_event_adam_v1_with_method_specific_view_allocation"
        )
    checks["tracking_gaussian_origin_uids_equal"] = (
        reference.get("gaussian_origin_uids")
        == candidate.get("gaussian_origin_uids")
    )

    scheduler_zero_fields = (
        "mapping_packets_dropped_oldest",
        "mapping_packets_flushed_by_reset",
        "mapping_packets_preempted_by_control",
        "mapping_packets_pending_at_stop",
        "timeline_items_not_ingested",
    )
    checks["no_drop_preempt_pending"] = all(
        int(runtime["common_scheduler"].get(field, -1)) == 0
        for runtime in (reference, candidate)
        for field in scheduler_zero_fields
    )
    checks["packets_equal_complete"] = (
        reference["common_scheduler"].get("mapping_packets_completed")
        == candidate["common_scheduler"].get("mapping_packets_completed")
        == reference["common_scheduler"].get("mapping_packets_enqueued")
        == candidate["common_scheduler"].get("mapping_packets_enqueued")
    )
    checks["zero_overlap"] = all(
        int(runtime.get("heldout_mapping_overlap_count", -1)) == 0
        and int(runtime.get("heldout_gaussian_origin_overlap_count", -1)) == 0
        for runtime in (reference, candidate)
    )
    checks["zero_tail"] = all(
        int(runtime.get("post_eos_optimizer_updates", -1)) == 0
        for runtime in (reference, candidate)
    )
    checks["no_fixed_work_idle_updates"] = all(
        int(runtime.get("idle_replay_calls_completed", -1)) == 0
        for runtime in (reference, candidate)
    )
    checks["eval_view_count_equal"] = (
        reference_eval.get("view_count") == candidate_eval.get("view_count")
    )
    checks["eval_mapping_disjoint"] = all(
        bool(value.get("mapping_disjoint"))
        and int(value.get("mapping_view_overlap_count", -1)) == 0
        for value in (reference_eval, candidate_eval)
    )
    if args.require_dense_selection:
        checks["dense_selection_nonzero"] = (
            (
                (
                    int(candidate.get("fixed_work_dense_global_views", 0)) > 0
                    and candidate.get("fixed_work_dense_selector")
                    in {"rr", "ercb"}
                )
                or candidate.get(
                    "fixed_iteration_projected_dense_selector"
                )
                in {"rr", "ercb"}
                or candidate.get(
                    "fixed_iteration_dedicated_dense_selector"
                )
                in {"rr"}
                or candidate.get("mapping_profile")
                == "d1_fixed_state_rr_imu"
            )
            and int(candidate.get("dense_selected_unique_views", 0)) > 0
            and candidate_dense_draws > 0
        )
    if args.require_dedicated_dense_allocation:
        replay_summary = candidate.get("mapping_replay_summary", {})
        dedicated_steps = int(
            replay_summary.get("dedicated_dense_steps", 0)
        )
        dedicated_views = int(
            replay_summary.get("dedicated_dense_view_updates", 0)
        )
        dedicated_batch = int(
            candidate.get("fixed_iteration_dedicated_dense_batch_size", 0)
        )
        checks["dedicated_dense_protocol"] = (
            args.mode == "fixed-iteration-allocation"
            and candidate.get("fixed_iteration_dedicated_dense_selector") == "rr"
            and int(candidate.get("fixed_iteration_dedicated_dense_iters", 0)) > 0
            and candidate.get("fixed_iteration_dedicated_dense_scope")
            in {"appearance", "appearance_opacity"}
            and candidate.get("fixed_iteration_projected_dense_selector") == "off"
            and candidate.get("dense_input_policy")
            == "causal_dense_owns_fixed_adam_iteration_allocation"
        )
        checks["dedicated_dense_accounting"] = (
            dedicated_steps > 0
            and dedicated_batch > 0
            and dedicated_views == candidate_dense_draws
            and dedicated_views <= dedicated_steps * dedicated_batch
            and dedicated_views >= dedicated_steps
        )
    if args.require_compute_paced:
        admission = candidate.get("compute_paced_dense_admission_summary") or {}
        token_cost = int(admission.get("token_cost_dense_view_updates", 0))
        paid = int(admission.get("paid_admissions", -1))
        bootstrap = int(admission.get("bootstrap_admissions", -1))
        checks["compute_paced_requested"] = bool(
            candidate.get("compute_paced_dense_admission")
        )
        checks["compute_paced_global_seed_exact"] = bootstrap == 1
        checks["compute_paced_paid_accounting"] = (
            token_cost > 0
            and int(admission.get("service_updates_spent", -1))
            == paid * token_cost
            and int(admission.get("service_accounting_error", -1)) == 0
        )
        checks["compute_paced_no_prepurchase"] = (
            int(admission.get("no_prepurchase_violations", -1)) == 0
            and int(admission.get("service_credit_remaining", -1))
            < token_cost
        )
        checks["compute_paced_service_clock_exact"] = (
            int(admission.get("last_completed_dense_view_updates", -1))
            == candidate_dense_draws
        )
        checks["compute_paced_materialization_exact"] = (
            int(candidate.get("dense_registered_unique_views", -1))
            == bootstrap + paid
        )
    if args.require_imu_shaper:
        imu = candidate.get("dense_pose_shaper") or {}
        checks["imu_dense_pose_protocol"] = (
            imu.get("protocol") == "exp78b_dense_imu_rotation_shape_v1"
        )
        checks["imu_dense_pose_strict_causal"] = (
            bool(imu.get("strict_causal_imu_pass"))
            and float(imu.get("max_future_imu_margin_seconds", 1.0)) <= 0.0
            and not bool(imu.get("post_eos_trajectory_used", True))
            and not bool(imu.get("translation_changed_by_rotation_shape", True))
        )
        checks["imu_dense_pose_nonzero"] = int(imu.get("records_shaped", 0)) > 0
    if args.require_ercb:
        checks["ercb_selector"] = (
            candidate.get("fixed_iteration_projected_dense_selector") == "ercb"
            and float(candidate.get("fixed_work_ercb_beta", -1.0)) == 0.02
            and int(candidate.get("fixed_work_ercb_block_size", -1)) == 128
        )
    if args.require_online_density:
        density = candidate.get("density_policy") or {}
        observed = candidate.get("online_density_summary") or {}
        checks["online_density_bundle"] = (
            density.get("policy") == "online_rank"
            and bool(density.get("effective_ppm_sampling"))
            and int(density.get("effective_pcd_downsample", -1)) == 256
            and int(density.get("effective_pcd_downsample_init", -1)) == 64
            and float(
                density.get(
                    "effective_adaptive_density_growth_allowance", -1.0
                )
            )
            == 2.0
        )
        checks["online_density_observed_nonzero"] = (
            int(observed.get("unique_frames", 0)) > 0
            and not bool(observed.get("future_frames_used", True))
            and not bool(observed.get("dataset_name_used", True))
        )
    if args.require_density_disabled:
        checks["online_density_disabled"] = (
            (candidate.get("density_policy") or {}).get("policy")
            == "disabled"
            and candidate.get("online_density_summary") is None
        )
    if args.require_auto_topology:
        checks["auto_topology_requested"] = bool(
            candidate.get("auto_topology_freeze_requested")
        )
    if args.forbid_auto_topology:
        checks["auto_topology_not_requested"] = not bool(
            candidate.get("auto_topology_freeze_requested")
        )
        checks["auto_topology_not_frozen"] = not bool(
            candidate.get("auto_topology_frozen_final")
        )
    if args.require_newborn_consolidation:
        consolidation = candidate.get(
            "observation_conditioned_newborn_consolidation_summary"
        ) or {}
        checks["newborn_consolidation_requested"] = bool(
            candidate.get(
                "observation_conditioned_newborn_consolidation_requested"
            )
        )
        checks["newborn_consolidation_protocol"] = (
            consolidation.get("protocol")
            == "exp78b_observation_conditioned_newborn_consolidation_v3"
        )
        checks["newborn_consolidation_causal_no_cutoff"] = (
            bool(consolidation.get("causal_completed_service_only"))
            and not bool(consolidation.get("dataset_name_used", True))
            and not bool(
                consolidation.get("frame_or_iteration_cutoff_used", True)
            )
            and not bool(consolidation.get("stream_horizon_used", True))
            and not bool(consolidation.get("gaussian_count_cutoff_used", True))
            and not bool(consolidation.get("global_topology_freeze_used", True))
        )
        checks["newborn_consolidation_final_v7_evidence"] = (
            int(
                consolidation.get(
                    "required_distinct_dense_opportunities", -1
                )
            )
            == 2
            and int(consolidation.get("two_pass_epoch_advance", -1)) == 3
        )
        checks["newborn_consolidation_row_commit_evidence"] = (
            consolidation.get("direct_maturity_evidence")
            == (
                "stable_point_visible_nonzero_projected_appearance_gradient_"
                "two_committed_adam_steps_distinct_dense_uid"
            )
            and not bool(
                consolidation.get("endpoint_draw_matures_lineage", True)
            )
            and int(consolidation.get("row_service_commits", 0)) > 0
            and int(
                consolidation.get("row_service_commits_with_rows", 0)
            )
            > 0
            and int(consolidation.get("row_service_pairs_committed", 0)) > 0
            and int(consolidation.get("pending_row_service_pairs", -1)) == 0
            and consolidation.get("maturity_granularity")
            == "stable_gaussian_point_id"
            and bool(
                consolidation.get(
                    "one_certificate_per_point_per_adam_step"
                )
            )
        )
        checks["newborn_consolidation_exercised"] = (
            int(consolidation.get("dense_draws_observed", 0)) > 0
            and int(consolidation.get("topology_queries", 0)) > 0
            and int(consolidation.get("protected_point_query_sum", 0)) > 0
            and len(consolidation.get("topology_events", [])) > 0
        )

    delta = {
        name: float(candidate_eval[f"mean_{name}"])
        - float(reference_eval[f"mean_{name}"])
        for name in ("psnr", "ssim", "lpips")
    }
    result = {
        "protocol": "exp78b_fixed_iteration_arm_verifier_v6",
        "mode": args.mode,
        "valid": all(checks.values()),
        "checks": checks,
        "reference": {
            "run": str(args.reference.resolve()),
            "psnr": reference_eval["mean_psnr"],
            "ssim": reference_eval["mean_ssim"],
            "lpips": reference_eval["mean_lpips"],
            "optimizer_steps": reference["optimizer_steps_completed"],
            "view_updates": reference["rasterized_view_updates"],
            "gaussians": reference["gaussians"],
            "mapping_wall_seconds": reference["mapping_wall_seconds"],
        },
        "candidate": {
            "run": str(args.candidate.resolve()),
            "method": candidate.get("method"),
            "selector": (
                candidate.get("fixed_iteration_projected_dense_selector")
                if candidate.get("fixed_iteration_projected_dense_selector")
                != "off"
                else (
                    candidate.get("fixed_iteration_dedicated_dense_selector")
                    if candidate.get("fixed_iteration_dedicated_dense_selector")
                    != "off"
                    else (
                        "rr_state_replay"
                        if candidate.get("mapping_profile")
                        == "d1_fixed_state_rr_imu"
                        else candidate.get("fixed_work_dense_selector")
                    )
                )
            ),
            "psnr": candidate_eval["mean_psnr"],
            "ssim": candidate_eval["mean_ssim"],
            "lpips": candidate_eval["mean_lpips"],
            "optimizer_steps": candidate["optimizer_steps_completed"],
            "view_updates": candidate["rasterized_view_updates"],
            "gaussians": candidate["gaussians"],
            "mapping_wall_seconds": candidate["mapping_wall_seconds"],
            "dense_draws": candidate_dense_draws,
            "dense_selected_unique_views": candidate.get(
                "dense_selected_unique_views", 0
            ),
            "compute_paced_dense_admission_summary": candidate.get(
                "compute_paced_dense_admission_summary"
            ),
            "dense_pose_shaper": candidate.get("dense_pose_shaper"),
            "observation_conditioned_newborn_consolidation_summary": (
                candidate.get(
                    "observation_conditioned_newborn_consolidation_summary"
                )
            ),
        },
        "delta_candidate_minus_reference": {
            **delta,
            "gaussians": int(candidate["gaussians"])
            - int(reference["gaussians"]),
            "mapping_wall_seconds": float(candidate["mapping_wall_seconds"])
            - float(reference["mapping_wall_seconds"]),
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
