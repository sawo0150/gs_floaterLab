#!/usr/bin/env python3
"""Artifact-only Exp111 verifier after the source-locked inline checker bug."""

from __future__ import annotations

import json

import run_exp111_dense_repeat_ercb as exp


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def metrics(path):
    return read_json(
        path / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]


def report_scene(row):
    paths = exp.scene_paths(row)
    if not all(
        (paths[arm] / "mapping_replay_runtime.json").exists()
        and (
            paths[arm]
            / "psnr/strict_fixed_manifest/final_result.json"
        ).exists()
        for arm in exp.ARMS
    ):
        return None
    runtimes = {
        arm: read_json(paths[arm] / "mapping_replay_runtime.json")
        for arm in exp.ARMS
    }
    arm_metrics = {arm: metrics(paths[arm]) for arm in exp.ARMS}
    control = runtimes["r4_control"]
    normalized = runtimes["dense_repeat_normalized"]
    rr = runtimes["dense_repeat_rr"]
    common = {}
    for arm, runtime in runtimes.items():
        common[arm] = {
            "same_archive": runtime["archive_manifest_sha256"]
            == control["archive_manifest_sha256"],
            "same_config": runtime["effective_config_sha256"]
            == control["effective_config_sha256"],
            "same_events": runtime["event_ids_fully_processed"]
            == control["event_ids_fully_processed"],
            "same_renders": runtime["rasterized_view_updates"]
            == control["rasterized_view_updates"],
            "same_adam": runtime["optimizer_steps_completed"]
            == control["optimizer_steps_completed"],
            "same_dense_admission": runtime["dense_registered_frame_uids"]
            == control["dense_registered_frame_uids"],
            "same_primary_slot_work": exp.slot_skeleton(
                runtime, "fixed_event_dense_opportunity_ledger"
            )
            == exp.slot_skeleton(
                control, "fixed_event_dense_opportunity_ledger"
            ),
            "zero_tail": runtime["post_eos_optimizer_updates"] == 0,
            "mapping_disjoint": (
                runtime["heldout_mapping_overlap_count"] == 0
                and runtime["heldout_gaussian_origin_overlap_count"] == 0
            ),
            "double_evaluation": read_json(
                paths[arm] / "evaluation_consistency.json"
            )["pass"],
        }
    method = {
        "control_has_aux_not_repeat": (
            len(control["fixed_event_keyframe_opportunity_ledger"]) > 0
            and not control["fixed_event_dense_repeat_opportunity_ledger"]
        ),
        "normalized_reallocates_same_slot_work": (
            not normalized["fixed_event_keyframe_opportunity_ledger"]
            and exp.slot_skeleton(
                normalized,
                "fixed_event_dense_repeat_opportunity_ledger",
            )
            == exp.slot_skeleton(
                control,
                "fixed_event_keyframe_opportunity_ledger",
            )
        ),
        "rr_reallocates_same_slot_work": (
            not rr["fixed_event_keyframe_opportunity_ledger"]
            and exp.slot_skeleton(
                rr, "fixed_event_dense_repeat_opportunity_ledger"
            )
            == exp.slot_skeleton(
                control, "fixed_event_keyframe_opportunity_ledger"
            )
        ),
        "normalized_dense_only_selector": (
            normalized["ercb_selection_potential_by_family"]
            == {
                "dense": "normalized_variance",
                "aux_kf": "disabled",
                "native_kf": "normalized_variance",
            }
        ),
        "rr_changes_dense_only": (
            rr["ercb_selection_potential_by_family"]
            == {
                "dense": "rr",
                "aux_kf": "disabled",
                "native_kf": "normalized_variance",
            }
        ),
        "primary_clock_matches_control": (
            normalized["dense_primary_service_updates"]
            == control["dense_primary_service_updates"]
            and rr["dense_primary_service_updates"]
            == control["dense_primary_service_updates"]
        ),
        "normalized_repeat_is_active": (
            normalized["mapping_replay_summary"].get(
                "service_shortfall_first_service_floor"
            )
            == 1
            and normalized["mapping_replay_summary"].get(
                "service_shortfall_repeat_draws", 0
            )
            > 0
            and normalized["mapping_replay_summary"]["selection_count_max"]
            > 1
        ),
        "rr_repeat_is_active": (
            rr["mapping_replay_summary"].get(
                "service_shortfall_first_service_floor"
            )
            == 1
            and rr["mapping_replay_summary"].get(
                "service_shortfall_repeat_draws", 0
            )
            > 0
            and rr["mapping_replay_summary"]["selection_count_max"] > 1
        ),
        "quality_stop_pass": (
            float(arm_metrics["dense_repeat_normalized"]["mean_psnr"])
            - float(arm_metrics["r4_control"]["mean_psnr"])
            >= -0.5
        ),
        "tickets_add_no_work": all(
            runtime["dense_topology_ticket"]["extra_renders"] == 0
            and runtime["dense_topology_ticket"]["extra_adam_steps"] == 0
            for runtime in runtimes.values()
        ),
    }
    trace = {
        "normalized_vs_rr_dense_different_rows": sum(
            left != right
            for left, right in zip(
                exp.dense_trace(normalized), exp.dense_trace(rr)
            )
        ),
        "normalized_dense_services": int(
            normalized["mapping_replay_summary"]["dense_updates"]
        ),
        "normalized_repeat_draws": int(
            normalized["mapping_replay_summary"][
                "service_shortfall_repeat_draws"
            ]
        ),
        "normalized_selection_count_min": int(
            normalized["mapping_replay_summary"]["selection_count_min"]
        ),
        "normalized_selection_count_max": int(
            normalized["mapping_replay_summary"]["selection_count_max"]
        ),
    }
    verification = {
        "protocol": "exp111_artifact_verification_v2",
        "inline_verifier_correction": (
            "Compare immutable slot work rather than selector internals, and "
            "compare cumulative primary clocks across arms rather than to "
            "the final-generation dense counter."
        ),
        "dataset": row["dataset"],
        "scene": row["scene"],
        "common_checks": common,
        "method_checks": method,
        "selection_trace": trace,
    }
    verification["valid"] = all(
        value for checks in common.values() for value in checks.values()
    ) and all(method.values())
    write_json(
        paths["verification"].with_name("artifact_verification.json"),
        verification,
    )
    result = {
        "dataset": row["dataset"],
        "scene": row["scene"],
        "arms": {
            arm: {
                "psnr": float(arm_metrics[arm]["mean_psnr"]),
                "ssim": float(arm_metrics[arm]["mean_ssim"]),
                "lpips": float(arm_metrics[arm]["mean_lpips"]),
                "renders": int(runtimes[arm]["rasterized_view_updates"]),
                "adam": int(runtimes[arm]["optimizer_steps_completed"]),
                "gaussians": int(runtimes[arm]["gaussians"]),
                "wall_seconds": float(runtimes[arm]["mapping_wall_seconds"]),
                "dense_updates": int(
                    runtimes[arm]["mapping_replay_summary"]["dense_updates"]
                ),
                "keyframe_updates": int(
                    runtimes[arm]["mapping_replay_summary"]["keyframe_updates"]
                ),
            }
            for arm in exp.ARMS
        },
        "normalized_minus_r4_db": (
            float(arm_metrics["dense_repeat_normalized"]["mean_psnr"])
            - float(arm_metrics["r4_control"]["mean_psnr"])
        ),
        "normalized_minus_rr_db": (
            float(arm_metrics["dense_repeat_normalized"]["mean_psnr"])
            - float(arm_metrics["dense_repeat_rr"]["mean_psnr"])
        ),
        "selection_trace": trace,
        "valid": verification["valid"],
    }
    write_json(paths["result"], result)
    return result


def main():
    rows = exp.selected_rows()
    completed = [result for row in rows if (result := report_scene(row))]
    exp.write_summary(rows)
    print(f"Exp111 artifact report: {len(completed)}/{len(rows)} scenes")


if __name__ == "__main__":
    main()
