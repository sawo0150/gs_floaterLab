#!/usr/bin/env python3
"""Exp118: replace one flexible historical render with unified dense ERCB."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp116_lpm_mass_prior as prior


BASE = prior.BASE
PANEL = prior.PANEL
ROOT = BASE.WORKSPACE / "results/experiments/exp118_unified_dense_global"
DOCS = (
    BASE.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp118_unified_dense_global_20260924"
)
ARMS = (
    "mass_normalized_control",
    "unified_mass_normalized",
    "unified_mass_rr",
)
SOURCE_PATHS = tuple(dict.fromkeys((*prior.SOURCE_PATHS, Path(__file__))))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_source_lock() -> None:
    current = {str(path): sha256(path) for path in SOURCE_PATHS}
    path = ROOT / "source_lock.json"
    if path.exists():
        if read_json(path)["sha256"] != current:
            raise RuntimeError("Exp118 source changed after start; use a new root")
        return
    write_json(
        path,
        {
            "protocol": "exp118_unified_dense_global_v1",
            "scene": "utmm/square-1",
            "arms": list(ARMS),
            "dense_global_replacement_slots": 1,
            "recent_keyframe_window_changed": False,
            "total_native_render_cardinality_changed": False,
            "additional_adam_steps_allowed": 0,
            "reallocated_service_advances_topology_lifecycle": False,
            "mass_prior_frozen_from_exp116": True,
            "quality_stop_db_vs_control": -0.5,
            "scene_or_dataset_hyperparameters": False,
            "lab_head_before_runner_commit": subprocess.check_output(
                ("git", "-C", str(BASE.WORKSPACE), "rev-parse", "HEAD"),
                text=True,
            ).strip(),
            "vigs_head_before_implementation_commit": subprocess.check_output(
                ("git", "-C", str(BASE.PAPER_ROOT), "rev-parse", "HEAD"),
                text=True,
            ).strip(),
            "sha256": current,
        },
    )


def scene_paths(row: dict) -> dict[str, Path]:
    common = BASE.sequence_paths(row["dataset"], row["scene"])
    local = ROOT / row["dataset"] / row["scene"]
    return {
        **common,
        **{arm: local / arm for arm in ARMS},
        "verification": local / "verification.json",
        "result": local / "result.json",
    }


def mapping_command(arm: str, row: dict, output: Path) -> list[str]:
    source_arm = (
        "lpm_mass_rr" if arm == "unified_mass_rr" else "lpm_mass_normalized"
    )
    command = prior.mapping_command(source_arm, row, output)
    if arm != "mass_normalized_control":
        command.extend(("--r4-unified-dense-global-views", "1"))
    return command


def run_mapper(arm: str, row: dict, paths: dict[str, Path]) -> None:
    output = paths[arm]
    if (output / "mapping_replay_runtime.json").exists():
        return
    if output.exists():
        raise FileExistsError(f"incomplete Exp118 output exists: {output}")
    PANEL.v2.gpu_idle()
    command = mapping_command(arm, row, output)
    write_json(output / "mapping_command.json", command)
    PANEL.v2.run_to_file(command, output / "mapping.log", custom=True)


def evaluate(arm: str, row: dict, paths: dict[str, Path]) -> dict:
    return PANEL.run_evaluation_twice(
        paths[arm], row["dataset"], row["scene"], paths["fixed_manifest"]
    )


def metrics(paths: dict[str, Path], arm: str) -> dict:
    return read_json(
        paths[arm] / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]


def global_trace(runtime: dict) -> list[list[int]]:
    return [
        [int(uid) for uid in row["selected_uids"]]
        for row in runtime["mapping_replay_summary"][
            "dense_global_scheduler_ledger"
        ]
    ]


def trace_difference(left: list, right: list) -> int:
    if len(left) != len(right):
        raise ValueError("unified global traces have different lengths")
    return sum(a != b for a, b in zip(left, right))


def verify(
    row: dict,
    paths: dict[str, Path],
    evaluations: dict[str, dict],
) -> dict:
    runtimes = {
        arm: read_json(paths[arm] / "mapping_replay_runtime.json")
        for arm in ARMS
    }
    arm_metrics = {arm: metrics(paths, arm) for arm in ARMS}
    control = runtimes["mass_normalized_control"]
    normalized = runtimes["unified_mass_normalized"]
    rr = runtimes["unified_mass_rr"]
    control_summary = control["mapping_replay_summary"]
    normalized_summary = normalized["mapping_replay_summary"]
    rr_summary = rr["mapping_replay_summary"]
    normalized_ledger = normalized_summary["dense_global_scheduler_ledger"]
    rr_ledger = rr_summary["dense_global_scheduler_ledger"]
    normalized_trace = global_trace(normalized)
    rr_trace = global_trace(rr)
    trace_delta = trace_difference(normalized_trace, rr_trace)
    psnr_control = float(arm_metrics["mass_normalized_control"]["mean_psnr"])
    psnr_delta = {
        arm: float(arm_metrics[arm]["mean_psnr"]) - psnr_control
        for arm in ARMS
    }

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
            "zero_tail": runtime["post_eos_optimizer_updates"] == 0,
            "heldout_disjoint": (
                runtime["heldout_mapping_overlap_count"] == 0
                and runtime["heldout_gaussian_origin_overlap_count"] == 0
            ),
            "double_evaluation": bool(evaluations[arm]["pass"]),
        }

    def ledger_valid(ledger: list[dict]) -> bool:
        return bool(ledger) and all(
            entry["optimizer_committed"]
            and entry["dense_replacement_slots"] == 1
            and len(entry["selected_uids"]) == 1
            and entry["tracked_historical_slots"] + 1
            == entry["native_global_slots"]
            and not entry["cap_applied"]
            and entry["combined_view_count_before_cap"]
            <= entry["max_viewpoints"]
            and bool(entry["recent_window_uids"])
            for entry in ledger
        )

    normalized_commits = int(
        normalized_summary["dense_global_scheduler_commits"]
    )
    rr_commits = int(rr_summary["dense_global_scheduler_commits"]
    )
    normalized_evidence = normalized["lpm_error_zone_evidence"]
    rr_evidence = rr["lpm_error_zone_evidence"]
    method = {
        "control_has_no_global_reallocation": (
            int(control_summary["dense_global_scheduler_enabled"]) == 0
            and int(control_summary["dense_global_scheduler_commits"]) == 0
        ),
        "normalized_global_ledger_valid": ledger_valid(normalized_ledger),
        "rr_global_ledger_valid": ledger_valid(rr_ledger),
        "draws_equal_commits_and_ledger": all(
            int(summary["dense_global_scheduler_draws"])
            == int(summary["dense_global_scheduler_commits"])
            == len(summary["dense_global_scheduler_ledger"])
            for summary in (normalized_summary, rr_summary)
        ),
        "global_service_does_not_advance_lifecycle": (
            int(normalized_summary["model_epoch_clock"])
            == int(control_summary["model_epoch_clock"])
            and int(rr_summary["model_epoch_clock"])
            == int(control_summary["model_epoch_clock"])
        ),
        "queue_draw_increase_equals_reallocation": (
            int(normalized_summary["draw_count"])
            - int(control_summary["draw_count"])
            == normalized_commits
            and int(rr_summary["draw_count"])
            - int(control_summary["draw_count"])
            == rr_commits
        ),
        "all_reallocated_renders_have_lpm_evidence": (
            int(normalized_evidence["calls"])
            - int(control["lpm_error_zone_evidence"]["calls"])
            == normalized_commits
            and int(rr_evidence["calls"])
            - int(control["lpm_error_zone_evidence"]["calls"])
            == rr_commits
        ),
        "normalized_and_rr_global_traces_differ": trace_delta > 0,
        "transactional_evidence_complete": all(
            int(evidence["utility_scores_consumed"])
            == int(evidence["calls"])
            and int(evidence["pending_scores"]) == 0
            and int(evidence["pending_mass_priors"]) == 0
            for evidence in (normalized_evidence, rr_evidence)
        ),
        "normalized_quality_floor": (
            psnr_delta["unified_mass_normalized"] >= -0.5
        ),
        "rr_quality_floor": psnr_delta["unified_mass_rr"] >= -0.5,
    }
    report = {
        "protocol": "exp118_unified_dense_global_verification_v1",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "common_checks": common,
        "method_checks": method,
        "psnr_delta_vs_control": psnr_delta,
        "normalized_vs_rr_global_trace_difference_rows": trace_delta,
        "dense_render_counts": {
            arm: int(runtime["lpm_error_zone_evidence"]["calls"])
            for arm, runtime in runtimes.items()
        },
        "dense_render_shares": {
            arm: (
                int(runtime["lpm_error_zone_evidence"]["calls"])
                / int(runtime["rasterized_view_updates"])
            )
            for arm, runtime in runtimes.items()
        },
        "global_commits": {
            "unified_mass_normalized": normalized_commits,
            "unified_mass_rr": rr_commits,
        },
    }
    report["valid"] = (
        all(value for checks in common.values() for value in checks.values())
        and all(method.values())
    )
    write_json(paths["verification"], report)
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
                "dense_renders": report["dense_render_counts"][arm],
                "dense_share": report["dense_render_shares"][arm],
                "psnr_delta_db": float(psnr_delta[arm]),
            }
            for arm in ARMS
        },
        "global_trace_difference_rows": trace_delta,
        "global_commits": report["global_commits"],
        "method_checks": method,
        "valid": report["valid"],
    }
    write_json(paths["result"], result)
    return result


def write_summary(result: dict | None) -> None:
    lines = [
        "# Exp118 — unified dense global-slot development gate",
        "",
        "One of six flexible historical-keyframe renders is replaced by a",
        "transactional draw from the same LPM-mass dense ERCB pool. The recent",
        "keyframe window, total physical renders, and Adam steps stay fixed.",
        "",
    ]
    if result is None:
        lines.append("Status: **PENDING**.")
    else:
        lines.extend(
            (
                "| Arm | PSNR | Delta | SSIM | LPIPS | Dense renders/share | Renders | Adam | GS |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            )
        )
        for arm in ARMS:
            item = result["arms"][arm]
            lines.append(
                f"| {arm} | {item['psnr']:.6f} | "
                f"{item['psnr_delta_db']:+.6f} | {item['ssim']:.6f} | "
                f"{item['lpips']:.6f} | {item['dense_renders']} / "
                f"{100*item['dense_share']:.2f}% | {item['renders']} | "
                f"{item['adam']} | {item['gaussians']} |"
            )
        lines.extend(
            (
                "",
                "Normalized/RR unified global trace differences: "
                f"**{result['global_trace_difference_rows']} rows**.",
                f"Gate: **{'PASS' if result['valid'] else 'FAIL'}**.",
            )
        )
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run"))
    args = parser.parse_args()
    row = prior.prior.selected_row()
    paths = scene_paths(row)
    prior.prior.prior.prior.prior.prior.prior.prior.exp94.check_evaluation_contract(
        [row]
    )
    PANEL.v2.preflight(row, PANEL.scene_paths(row))
    check_source_lock()
    if args.action == "preflight":
        write_summary(None)
        print("Exp118 preflight PASS: 1 development scene x 3 fresh arms")
        return 0

    result = None
    evaluations = {}
    try:
        for arm in ARMS:
            run_mapper(arm, row, paths)
            evaluations[arm] = evaluate(arm, row, paths)
        result = verify(row, paths, evaluations)
        write_summary(result)
        if not result["valid"]:
            raise RuntimeError("Exp118 verification stop")
        print(
            "Exp118 PASS: unified normalized="
            f"{result['arms']['unified_mass_normalized']['psnr_delta_db']:+.6f} dB, "
            "dense share="
            f"{100*result['arms']['unified_mass_normalized']['dense_share']:.2f}%",
            flush=True,
        )
    except Exception:
        if result is None:
            write_summary(None)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
