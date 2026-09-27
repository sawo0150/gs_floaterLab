#!/usr/bin/env python3
"""Exp115: source-backed LPM utility in the fixed-work dense ERCB pool."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp113_lpm_error_zone_probe as prior


BASE = prior.prior.prior.prior.prior.prior.base
PANEL = prior.prior.prior.prior.prior.prior.panel
DENSE_TRACE = prior.prior.prior.dense_trace
ROOT = BASE.WORKSPACE / "results/experiments/exp115_lpm_view_utility"
DOCS = (
    BASE.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp115_lpm_view_utility_20260924"
)
SCENE = ("utmm", "square-1")
ARMS = (
    "normalized_control",
    "lpm_probe_control",
    "lpm_normalized_utility",
    "lpm_utility_rr",
)
SOURCE_PATHS = tuple(
    dict.fromkeys(
        (
            *prior.SOURCE_PATHS,
            BASE.PAPER_ROOT / "vigs/map_scheduler.py",
            BASE.PAPER_ROOT
            / "paper_full_stages/test_stage3_service_shortfall_ercb.py",
            Path(__file__),
        )
    )
)


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
    if subprocess.check_output(
        ("git", "-C", str(prior.LPM_ROOT), "rev-parse", "HEAD"),
        text=True,
    ).strip() != prior.LPM_COMMIT:
        raise RuntimeError("pinned LPM checkout changed")
    current = {str(path): sha256(path) for path in SOURCE_PATHS}
    path = ROOT / "source_lock.json"
    if path.exists():
        if read_json(path)["sha256"] != current:
            raise RuntimeError("Exp115 source changed after start; use a new root")
        return
    write_json(
        path,
        {
            "protocol": "exp115_lpm_view_utility_v1",
            "scene": "/".join(SCENE),
            "arms": list(ARMS),
            "development_scene_only": True,
            "lpm_commit": prior.LPM_COMMIT,
            "borrowed_operation": "lpm/utils.py::get_errormap(diff)",
            "scheduler_composition": (
                "p_i proportional to (1+e_i)*exp(-16*n_i/(T+1))"
            ),
            "utility_only_control": "p_i proportional to 1+e_i",
            "scene_or_dataset_hyperparameters": False,
            "quality_metric_used_to_choose_formula": False,
            "quality_stop_db_vs_normalized_control": -0.5,
            "active_gate": "at least one dense repeat selection changes",
            "physical_work_must_match": True,
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


def selected_row() -> dict:
    matches = [
        row
        for row in PANEL.v2.install_inventory()
        if (row["dataset"], row["scene"]) == SCENE
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Exp115 scene inventory mismatch: {len(matches)}")
    return matches[0]


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
    probe = arm != "normalized_control"
    command = prior.mapping_command(
        "lpm_probe" if probe else "control", row, output
    )
    if arm in ("lpm_normalized_utility", "lpm_utility_rr"):
        command.append("--lpm-error-zone-view-utility")
    if arm == "lpm_utility_rr":
        command.extend(("--ercb-rr-family", "dense"))
    return command


def run_mapper(arm: str, row: dict, paths: dict[str, Path]) -> None:
    output = paths[arm]
    if (output / "mapping_replay_runtime.json").exists():
        return
    if output.exists():
        raise FileExistsError(f"incomplete Exp115 output exists: {output}")
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


def trace_difference(left: list, right: list) -> int:
    if len(left) != len(right):
        raise ValueError("dense traces have different lengths")
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
    control = runtimes["normalized_control"]
    probe_control = runtimes["lpm_probe_control"]
    utility = runtimes["lpm_normalized_utility"]
    utility_rr = runtimes["lpm_utility_rr"]
    reference_trace = DENSE_TRACE(control)
    traces = {arm: DENSE_TRACE(runtime) for arm, runtime in runtimes.items()}

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

    utility_evidence = utility["lpm_error_zone_evidence"]
    utility_rr_evidence = utility_rr["lpm_error_zone_evidence"]
    utility_summary = utility["mapping_replay_summary"]
    utility_rr_summary = utility_rr["mapping_replay_summary"]
    psnr_control = float(arm_metrics["normalized_control"]["mean_psnr"])
    psnr_delta = {
        arm: float(arm_metrics[arm]["mean_psnr"]) - psnr_control
        for arm in ARMS
    }
    trace_delta = {
        arm: trace_difference(reference_trace, traces[arm]) for arm in ARMS
    }
    method = {
        "probe_control_is_behavior_neutral": (
            probe_control["lpm_error_zone_evidence"]["behavior_neutral"]
            and trace_delta["lpm_probe_control"] == 0
        ),
        "normalized_utility_formula_declared": (
            utility["lpm_error_zone_view_utility_formula"]
            == "p_i proportional to (1+e_i)*exp(-gamma*n_i/(T+1))"
        ),
        "normalized_utility_selector_enabled": (
            utility_summary["candidate_utility_mode"] == "lpm_error_zone"
            and utility_summary["selection_potential"]
            == "normalized_variance"
        ),
        "utility_only_rr_selector_enabled": (
            utility_rr_summary["candidate_utility_mode"]
            == "lpm_error_zone"
            and utility_rr_summary["selection_potential"] == "rr"
        ),
        "utility_updates_are_completed_work": all(
            int(evidence["utility_scores_consumed"])
            == int(evidence["calls"])
            and int(evidence["pending_scores"]) == 0
            and not evidence["behavior_neutral"]
            for evidence in (utility_evidence, utility_rr_evidence)
        ),
        "queue_has_no_pending_utility": (
            int(utility_summary["candidate_utility_pending"]) == 0
            and int(utility_rr_summary["candidate_utility_pending"]) == 0
        ),
        "utility_is_active": trace_delta["lpm_normalized_utility"] > 0,
        "utility_rr_is_active": trace_delta["lpm_utility_rr"] > 0,
        "normalized_utility_quality_floor": (
            psnr_delta["lpm_normalized_utility"] >= -0.5
        ),
        "utility_rr_quality_floor": psnr_delta["lpm_utility_rr"] >= -0.5,
        "source_operator_pinned": all(
            evidence["source_commit"] == prior.LPM_COMMIT
            and not evidence["uses_lightglue"]
            and not evidence["uses_triangulation"]
            and not evidence["future_frames_used"]
            and not evidence["dataset_name_used"]
            and int(evidence["extra_renders"]) == 0
            and int(evidence["extra_adam_steps"]) == 0
            and int(evidence["mutation_rows"]) == 0
            for evidence in (utility_evidence, utility_rr_evidence)
        ),
    }
    report = {
        "protocol": "exp115_lpm_view_utility_verification_v1",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "common_checks": common,
        "method_checks": method,
        "trace_difference_rows_vs_normalized_control": trace_delta,
        "psnr_delta_vs_normalized_control": psnr_delta,
        "selector_summaries": {
            "lpm_normalized_utility": utility_summary,
            "lpm_utility_rr": utility_rr_summary,
        },
        "evidence_summaries": {
            "lpm_normalized_utility": {
                key: value
                for key, value in utility_evidence.items()
                if key != "records"
            },
            "lpm_utility_rr": {
                key: value
                for key, value in utility_rr_evidence.items()
                if key != "records"
            },
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
                "trace_difference_rows": int(trace_delta[arm]),
                "psnr_delta_db": float(psnr_delta[arm]),
            }
            for arm in ARMS
        },
        "method_checks": method,
        "valid": report["valid"],
    }
    write_json(paths["result"], result)
    return result


def write_summary(result: dict | None) -> None:
    lines = [
        "# Exp115 — source-backed LPM dense-view utility",
        "",
        "The LPM author-code error-zone coverage is an explicit bounded base",
        "measure; normalized-variance ERCB remains a separate energy term.",
        "No extra render, Adam update, topology mutation, or scene knob is allowed.",
        "",
    ]
    if result is None:
        lines.append("Status: **PENDING**.")
    else:
        lines.extend(
            (
                "| Arm | PSNR | Delta | SSIM | LPIPS | Trace rows changed | Renders | Adam | GS | Wall (s) |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            )
        )
        for arm in ARMS:
            item = result["arms"][arm]
            lines.append(
                f"| {arm} | {item['psnr']:.6f} | "
                f"{item['psnr_delta_db']:+.6f} | {item['ssim']:.6f} | "
                f"{item['lpips']:.6f} | {item['trace_difference_rows']} | "
                f"{item['renders']} | {item['adam']} | {item['gaussians']} | "
                f"{item['wall_seconds']:.3f} |"
            )
        lines.extend(
            (
                "",
                "Normalized utility: `p_i proportional to "
                "(1+e_i)*exp(-16*n_i/(T+1))`.",
                "Utility-only RR control: `p_i proportional to 1+e_i`.",
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
    row = selected_row()
    paths = scene_paths(row)
    prior.prior.prior.prior.prior.prior.exp94.check_evaluation_contract([row])
    PANEL.v2.preflight(row, PANEL.scene_paths(row))
    check_source_lock()
    if args.action == "preflight":
        write_summary(None)
        print("Exp115 preflight PASS: 1 development scene x 4 fresh arms")
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
            raise RuntimeError("Exp115 verification stop")
        print(
            "Exp115 PASS: normalized utility delta="
            f"{result['arms']['lpm_normalized_utility']['psnr_delta_db']:+.6f} dB, "
            "trace rows="
            f"{result['arms']['lpm_normalized_utility']['trace_difference_rows']}",
            flush=True,
        )
    except Exception:
        if result is None:
            write_summary(None)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
