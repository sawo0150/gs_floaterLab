#!/usr/bin/env python3
"""Fail-closed verifier for the predeclared Stage-6R R1 gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check(report: dict, name: str, condition: bool, detail: object) -> None:
    report["checks"][name] = {"passed": bool(condition), "detail": detail}
    if not condition:
        report["valid"] = False


def fixed_metric(run: Path) -> dict:
    result = read_json(run / "psnr" / "strict_fixed_manifest" / "final_result.json")
    return result["predeclared_fixed_manifest_posthoc"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--render-match-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    candidate = read_json(args.candidate / "mapping_replay_runtime.json")
    reference = read_json(args.reference / "mapping_replay_runtime.json")
    workload = read_json(args.candidate / "stage6_service_regime.json")
    render_match = read_json(args.render_match_report)
    candidate_fixed = fixed_metric(args.candidate)
    reference_fixed = fixed_metric(args.reference)
    vanilla_result = render_match.get("result", {}).get("vanilla", {})

    report = {
        "protocol": "exp78b_stage6r_r1_gate_v1",
        "valid": True,
        "candidate": str(args.candidate.resolve()),
        "reference": str(args.reference.resolve()),
        "checks": {},
    }

    check(
        report,
        "same_archive",
        candidate.get("archive_manifest_sha256")
        == reference.get("archive_manifest_sha256"),
        {
            "candidate": candidate.get("archive_manifest_sha256"),
            "reference": reference.get("archive_manifest_sha256"),
        },
    )
    check(
        report,
        "same_native_work",
        all(
            candidate.get(key) == reference.get(key)
            for key in (
                "rasterized_view_updates",
                "optimizer_steps_completed",
                "fixed_event_dense_opportunities_per_packet",
            )
        ),
        {
            key: {
                "candidate": candidate.get(key),
                "reference": reference.get(key),
            }
            for key in (
                "rasterized_view_updates",
                "optimizer_steps_completed",
                "fixed_event_dense_opportunities_per_packet",
            )
        },
    )
    candidate_events = [
        int(item["event_id"])
        for item in candidate.get("fixed_event_dense_opportunity_ledger", [])
    ]
    reference_events = [
        int(item["event_id"])
        for item in reference.get("fixed_event_dense_opportunity_ledger", [])
    ]
    check(
        report,
        "same_dense_opportunity_events",
        candidate_events == reference_events,
        {
            "candidate_count": len(candidate_events),
            "reference_count": len(reference_events),
        },
    )
    c2 = candidate.get("service_shortfall_ercb_parameters") or {}
    check(
        report,
        "frozen_r1_c1_c2_configuration",
        candidate.get("compute_paced_dense_admission") is True
        and int(candidate.get("compute_paced_dense_token_cost", -1)) == 1
        and candidate.get("c1_c2_global_residue_integration") is True
        and candidate.get("service_shortfall_ercb_requested") is True
        and candidate.get("include_keyframes_in_replay") is False
        and candidate.get("dense_replay_gradient_scope") == "appearance"
        and int(c2.get("block_size", -1)) == 8
        and abs(float(c2.get("relative_floor_ratio", -1.0)) - 0.75) < 1e-12
        and abs(float(c2.get("maximum_bonus", -1.0)) - 1.5) < 1e-12
        and c2.get("global_epoch_no_repeat") is True,
        {
            "token_cost": candidate.get("compute_paced_dense_token_cost"),
            "keyframes_in_replay": candidate.get("include_keyframes_in_replay"),
            "gradient_scope": candidate.get("dense_replay_gradient_scope"),
            "c2": c2,
        },
    )
    admission = candidate.get("compute_paced_dense_admission_summary") or {}
    check(
        report,
        "transactional_causal_admission",
        int(admission.get("no_prepurchase_violations", -1)) == 0
        and admission.get("future_frames_used") is False
        and admission.get("dataset_name_used") is False
        and admission.get("stream_horizon_used") is False
        and int(admission.get("service_accounting_error", -1)) == 0
        and int(admission.get("token_cost", -1)) == 1,
        admission,
    )
    check(
        report,
        "zero_tail_disjoint_fixed_evaluator",
        int(candidate.get("post_eos_optimizer_updates", -1)) == 0
        and candidate.get("final_ba_performed") is False
        and candidate.get("final_color_refinement_performed") is False
        and int(candidate.get("heldout_mapping_overlap_count", -1)) == 0
        and int(candidate.get("heldout_gaussian_origin_overlap_count", -1)) == 0
        and bool(candidate_fixed.get("mapping_disjoint")),
        {
            "tail": candidate.get("post_eos_optimizer_updates"),
            "mapping_overlap": candidate.get("heldout_mapping_overlap_count"),
            "origin_overlap": candidate.get("heldout_gaussian_origin_overlap_count"),
            "fixed_views": candidate_fixed.get("view_count"),
        },
    )
    candidate_unique = int(candidate.get("dense_selected_unique_views", -1))
    reference_unique = int(reference.get("dense_selected_unique_views", -1))
    coverage_ratio = candidate_unique / reference_unique if reference_unique > 0 else 0.0
    check(
        report,
        "at_least_10x_unique_dense_coverage",
        reference_unique > 0 and coverage_ratio >= 10.0,
        {
            "candidate": candidate_unique,
            "reference": reference_unique,
            "ratio": coverage_ratio,
        },
    )
    check(
        report,
        "ercb_global_residue_audit",
        workload.get("valid") is True
        and int(workload.get("final_S", -1)) <= int(workload.get("final_U", -2))
        and all(int(generation.get("repeat_services", -1)) == 0 for generation in workload.get("generations", [])),
        {
            "valid": workload.get("valid"),
            "final_S": workload.get("final_S"),
            "final_U": workload.get("final_U"),
            "final_regime": workload.get("final_regime"),
            "repeat_services": [g.get("repeat_services") for g in workload.get("generations", [])],
        },
    )

    retention_delta = float(candidate_fixed["mean_psnr"]) - float(reference_fixed["mean_psnr"])
    check(
        report,
        "reference_quality_retained_within_0p10_db",
        retention_delta >= -0.10,
        {
            "candidate_psnr": candidate_fixed["mean_psnr"],
            "reference_psnr": reference_fixed["mean_psnr"],
            "delta_db": retention_delta,
        },
    )
    vanilla_delta = float(candidate_fixed["mean_psnr"]) - float(vanilla_result.get("psnr", 1e9))
    check(
        report,
        "render_match_audit_and_plus_1db",
        render_match.get("valid") is True and vanilla_delta >= 1.0,
        {
            "render_match_valid": render_match.get("valid"),
            "candidate_psnr": candidate_fixed["mean_psnr"],
            "vanilla_psnr": vanilla_result.get("psnr"),
            "delta_db": vanilla_delta,
        },
    )

    report["result"] = {
        "candidate": {
            "psnr": candidate_fixed["mean_psnr"],
            "ssim": candidate_fixed["mean_ssim"],
            "lpips": candidate_fixed["mean_lpips"],
            "gaussians": candidate.get("gaussians"),
            "renders": candidate.get("rasterized_view_updates"),
            "optimizer_steps": candidate.get("optimizer_steps_completed"),
            "dense_unique_selected": candidate_unique,
        },
        "reference": {
            "psnr": reference_fixed["mean_psnr"],
            "ssim": reference_fixed["mean_ssim"],
            "lpips": reference_fixed["mean_lpips"],
            "dense_unique_selected": reference_unique,
        },
        "vanilla": vanilla_result,
        "candidate_minus_reference_psnr": retention_delta,
        "candidate_minus_vanilla_psnr": vanilla_delta,
        "unique_dense_coverage_ratio": coverage_ratio,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
