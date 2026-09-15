#!/usr/bin/env python3
"""Fail-closed audit for native-D1 versus native-vanilla render matching."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


MAPPING_KINDS = {"keyframe_update", "pose_scale_correction"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check(report: dict, name: str, condition: bool, detail: object) -> None:
    report["checks"][name] = {"passed": bool(condition), "detail": detail}
    if not condition:
        report["valid"] = False


def _uid_set(value: object) -> tuple[set[int], bool]:
    """Return an integer UID set and whether the source is a valid UID list."""
    if not isinstance(value, list):
        return set(), False
    try:
        return {int(uid) for uid in value}, True
    except (TypeError, ValueError):
        return set(), False


def tracking_keyframe_identity(
    d1: dict, vanilla: dict
) -> tuple[bool, dict[str, object]]:
    """Audit tracker-input identity without using surviving Gaussian origins.

    Custom runs append dense-supervision UIDs to ``mapped_frame_uids`` whereas
    native vanilla records only tracking keyframes.  New runtimes may expose a
    direct ``tracking_mapped_frame_uids`` list.  For legacy runtimes, recover
    the tracker set from the custom mapped-union minus dense-selected set, but
    fail closed when a dense UID is also a vanilla tracking UID because that
    decomposition would then be ambiguous.

    ``gaussian_origin_uids`` is deliberately diagnostic only: pruning can
    remove every Gaussian born from a valid input keyframe, so survivor
    provenance cannot prove which tracking packets entered the mapper.
    """
    vanilla_tracking, vanilla_valid = _uid_set(vanilla.get("mapped_frame_uids"))
    direct = d1.get("tracking_mapped_frame_uids")
    mapped_union, mapped_valid = _uid_set(d1.get("mapped_frame_uids"))
    dense_selected, dense_valid = _uid_set(d1.get("dense_selected_frame_uids"))

    ambiguous_overlap: set[int] = set()
    direct_within_mapped_union = True
    if direct is not None:
        d1_tracking, source_valid = _uid_set(direct)
        source = "direct_tracking_mapped_frame_uids"
        direct_within_mapped_union = mapped_valid and d1_tracking <= mapped_union
    else:
        source = "legacy_mapped_union_minus_dense_selected"
        source_valid = mapped_valid and dense_valid
        ambiguous_overlap = dense_selected & vanilla_tracking
        d1_tracking = mapped_union - dense_selected if source_valid else set()

    declared_count = d1.get("tracking_mapped_unique_views")
    count_valid = True
    if declared_count is not None:
        try:
            count_valid = int(declared_count) == len(d1_tracking)
        except (TypeError, ValueError):
            count_valid = False

    survivor_origins, survivor_valid = _uid_set(
        d1.get("gaussian_origin_uids", [])
    )
    missing_from_d1 = vanilla_tracking - d1_tracking
    extra_in_d1 = d1_tracking - vanilla_tracking
    valid = (
        vanilla_valid
        and source_valid
        and direct_within_mapped_union
        and not ambiguous_overlap
        and count_valid
        and not missing_from_d1
        and not extra_in_d1
    )
    detail: dict[str, object] = {
        "identity_source": source,
        "d1_count": len(d1_tracking),
        "vanilla_count": len(vanilla_tracking),
        "missing_from_d1": sorted(missing_from_d1),
        "extra_in_d1": sorted(extra_in_d1),
        "ambiguous_dense_tracking_overlap": sorted(ambiguous_overlap),
        "declared_tracking_count": declared_count,
        "declared_tracking_count_valid": count_valid,
        "direct_within_mapped_union": direct_within_mapped_union,
        "gaussian_origin_role": "diagnostic_survivors_only",
        "gaussian_origin_list_valid": survivor_valid,
        "surviving_origin_count": len(survivor_origins),
        "tracking_uids_without_surviving_origin": sorted(
            d1_tracking - survivor_origins
        ),
    }
    return valid, detail


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--d1-run", type=Path, required=True)
    parser.add_argument("--vanilla-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    d1_runtime_path = args.d1_run / "mapping_replay_runtime.json"
    vanilla_runtime_path = args.vanilla_run / "mapping_replay_runtime.json"
    d1_eval_path = (
        args.d1_run
        / "psnr"
        / "strict_fixed_manifest"
        / "final_result.json"
    )
    vanilla_eval_path = (
        args.vanilla_run
        / "psnr"
        / "strict_fixed_manifest"
        / "final_result.json"
    )
    d1 = read_json(d1_runtime_path)
    vanilla = read_json(vanilla_runtime_path)
    d1_eval = read_json(d1_eval_path)
    vanilla_eval = read_json(vanilla_eval_path)
    ledger = vanilla.get("d1_render_service_ledger") or {}
    summary = vanilla.get("d1_render_match_summary") or {}

    report = {
        "protocol": "exp78b_d1_native_render_match_verifier_v1",
        "tracking_identity_protocol": (
            "direct_or_fail_closed_mapped_union_decomposition_v2"
        ),
        "valid": True,
        "d1_run": str(args.d1_run.resolve()),
        "vanilla_run": str(args.vanilla_run.resolve()),
        "checks": {},
    }

    check(
        report,
        "same_frozen_archive",
        d1.get("archive_manifest_sha256")
        == vanilla.get("archive_manifest_sha256"),
        {
            "d1": d1.get("archive_manifest_sha256"),
            "vanilla": vanilla.get("archive_manifest_sha256"),
        },
    )
    check(
        report,
        "reference_runtime_hash_locked",
        ledger.get("reference_runtime_sha256")
        == hashlib.sha256(d1_runtime_path.read_bytes()).hexdigest(),
        ledger.get("reference_runtime_sha256"),
    )
    check(
        report,
        "comparison_contract",
        vanilla.get("comparison_contract")
        == "native_d1_vs_native_vanilla_render_matched_v2"
        and vanilla.get("work_contract")
        == "d1_native_total_render_budget_v2"
        and summary.get("vanilla_dense_update_path_added") is False,
        {
            "comparison": vanilla.get("comparison_contract"),
            "work": vanilla.get("work_contract"),
            "vanilla_dense_update_path_added": summary.get(
                "vanilla_dense_update_path_added"
            ),
        },
    )

    d1_selected = {
        int(record["event_id"])
        for record in d1.get("events", [])
        if record.get("kind") in MAPPING_KINDS
    }
    vanilla_selected = {
        int(record["event_id"])
        for record in vanilla.get("events", [])
        if record.get("kind") in MAPPING_KINDS
        and record.get("policy_skip")
        != "not_selected_by_d1_native_service_trace"
    }
    check(
        report,
        "same_d1_mapping_service_trace",
        d1_selected == vanilla_selected,
        {
            "d1_count": len(d1_selected),
            "vanilla_count": len(vanilla_selected),
            "missing": sorted(d1_selected - vanilla_selected),
            "extra": sorted(vanilla_selected - d1_selected),
        },
    )
    same_tracking, tracking_detail = tracking_keyframe_identity(d1, vanilla)
    check(
        report,
        "same_tracking_kf_uids",
        same_tracking,
        tracking_detail,
    )

    d1_renders = int(d1.get("rasterized_view_updates", -1))
    vanilla_renders = int(vanilla.get("rasterized_view_updates", -2))
    check(
        report,
        "exact_total_physical_render_match",
        d1_renders == vanilla_renders
        == int(ledger.get("vanilla_native_render_target", -3))
        == int(summary.get("render_credit_consumed", -4)),
        {
            "d1": d1_renders,
            "vanilla": vanilla_renders,
            "target": ledger.get("vanilla_native_render_target"),
            "consumed": summary.get("render_credit_consumed"),
        },
    )
    check(
        report,
        "reference_committed_render_accounting",
        int(ledger.get("d1_total_committed_renders", -1))
        + int(ledger.get("vanilla_extra_useful_render_advantage", -1))
        == d1_renders,
        {
            "d1_committed": ledger.get("d1_total_committed_renders"),
            "uncommitted_given_to_vanilla": ledger.get(
                "vanilla_extra_useful_render_advantage"
            ),
        },
    )
    check(
        report,
        "zero_tail_and_no_final_refinement",
        all(
            int(run.get("post_eos_optimizer_updates", -1)) == 0
            and run.get("final_ba_performed") is False
            and run.get("final_color_refinement_performed") is False
            for run in (d1, vanilla)
        ),
        {
            "d1_tail": d1.get("post_eos_optimizer_updates"),
            "vanilla_tail": vanilla.get("post_eos_optimizer_updates"),
        },
    )
    check(
        report,
        "mapping_disjoint",
        all(
            int(run.get("heldout_mapping_overlap_count", -1)) == 0
            and int(run.get("heldout_gaussian_origin_overlap_count", -1)) == 0
            for run in (d1, vanilla)
        ),
        {
            "d1_overlap": d1.get("heldout_mapping_overlap_count"),
            "vanilla_overlap": vanilla.get("heldout_mapping_overlap_count"),
        },
    )

    d1_fixed = d1_eval["predeclared_fixed_manifest_posthoc"]
    vanilla_fixed = vanilla_eval["predeclared_fixed_manifest_posthoc"]
    check(
        report,
        "same_fixed_heldout_evaluator",
        int(d1_fixed["view_count"]) == int(vanilla_fixed["view_count"])
        and bool(d1_fixed["mapping_disjoint"])
        and bool(vanilla_fixed["mapping_disjoint"]),
        {
            "d1_views": d1_fixed["view_count"],
            "vanilla_views": vanilla_fixed["view_count"],
        },
    )

    report["result"] = {
        "d1": {
            "psnr": d1_fixed["mean_psnr"],
            "ssim": d1_fixed["mean_ssim"],
            "lpips": d1_fixed["mean_lpips"],
            "optimizer_steps": d1.get("optimizer_steps_completed"),
            "renders": d1_renders,
            "gaussians": d1.get("gaussians"),
        },
        "vanilla": {
            "psnr": vanilla_fixed["mean_psnr"],
            "ssim": vanilla_fixed["mean_ssim"],
            "lpips": vanilla_fixed["mean_lpips"],
            "optimizer_steps": vanilla.get("optimizer_steps_completed"),
            "renders": vanilla_renders,
            "gaussians": vanilla.get("gaussians"),
        },
        "d1_minus_vanilla": {
            "psnr": d1_fixed["mean_psnr"] - vanilla_fixed["mean_psnr"],
            "ssim": d1_fixed["mean_ssim"] - vanilla_fixed["mean_ssim"],
            "lpips": d1_fixed["mean_lpips"] - vanilla_fixed["mean_lpips"],
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
