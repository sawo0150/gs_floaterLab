#!/usr/bin/env python3
"""Exp116: LPM significant-zone mass as the dense ERCB KL prior."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp115_lpm_view_utility as prior


BASE = prior.BASE
PANEL = prior.PANEL
ROOT = BASE.WORKSPACE / "results/experiments/exp116_lpm_mass_prior"
DOCS = (
    BASE.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp116_lpm_mass_prior_20260924"
)
ARMS = ("normalized_control", "lpm_mass_normalized", "lpm_mass_rr")
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
            raise RuntimeError("Exp116 source changed after start; use a new root")
        return
    write_json(
        path,
        {
            "protocol": "exp116_lpm_mass_prior_v1",
            "scene": "utmm/square-1",
            "arms": list(ARMS),
            "lpm_commit": prior.prior.LPM_COMMIT,
            "formula": (
                "q_i=(active_pixels+256)/(H*W+256); "
                "p_i proportional to q_i*exp(-16*n_i/(T+1))"
            ),
            "one_patch_pseudocount": True,
            "quality_metric_used_to_choose_formula": False,
            "scene_or_dataset_hyperparameters": False,
            "quality_stop_db_vs_fresh_control": -0.5,
            "active_gate": "at least one dense repeat selection changes",
            "no_full_panel_before_development_pass": True,
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
    command = prior.prior.mapping_command(
        "control" if arm == "normalized_control" else "lpm_probe",
        row,
        output,
    )
    if arm != "normalized_control":
        command.append("--lpm-error-zone-mass-prior")
    if arm == "lpm_mass_rr":
        command.extend(("--ercb-rr-family", "dense"))
    return command


def run_mapper(arm: str, row: dict, paths: dict[str, Path]) -> None:
    output = paths[arm]
    if (output / "mapping_replay_runtime.json").exists():
        return
    if output.exists():
        raise FileExistsError(f"incomplete Exp116 output exists: {output}")
    PANEL.v2.gpu_idle()
    command = mapping_command(arm, row, output)
    write_json(output / "mapping_command.json", command)
    PANEL.v2.run_to_file(command, output / "mapping.log", custom=True)


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
    arm_metrics = {arm: prior.metrics(paths, arm) for arm in ARMS}
    control = runtimes["normalized_control"]
    reference_trace = prior.DENSE_TRACE(control)
    trace_delta = {
        arm: trace_difference(reference_trace, prior.DENSE_TRACE(runtime))
        for arm, runtime in runtimes.items()
    }
    psnr_control = float(arm_metrics["normalized_control"]["mean_psnr"])
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

    normalized = runtimes["lpm_mass_normalized"]
    rr = runtimes["lpm_mass_rr"]
    normalized_evidence = normalized["lpm_error_zone_evidence"]
    rr_evidence = rr["lpm_error_zone_evidence"]
    normalized_summary = normalized["mapping_replay_summary"]
    rr_summary = rr["mapping_replay_summary"]
    expected_formula = (
        "p_i proportional to ((active_pixels+256)/(H*W+256))*"
        "exp(-gamma*n_i/(T+1))"
    )
    method = {
        "formula_declared_exactly": (
            normalized["lpm_error_zone_mass_prior_formula"]
            == expected_formula
            and rr["lpm_error_zone_mass_prior_formula"] == expected_formula
        ),
        "normalized_mass_prior_enabled": (
            normalized_summary["candidate_utility_mode"]
            == "lpm_error_zone_mass"
            and normalized_summary["selection_potential"]
            == "normalized_variance"
        ),
        "rr_mass_prior_enabled": (
            rr_summary["candidate_utility_mode"]
            == "lpm_error_zone_mass"
            and rr_summary["selection_potential"] == "rr"
        ),
        "normalized_mass_prior_is_active": (
            trace_delta["lpm_mass_normalized"] > 0
        ),
        "rr_mass_prior_is_active": trace_delta["lpm_mass_rr"] > 0,
        "transactional_evidence_complete": all(
            int(evidence["utility_scores_consumed"])
            == int(evidence["calls"])
            and int(evidence["pending_scores"]) == 0
            and int(evidence["pending_mass_priors"]) == 0
            and not evidence["behavior_neutral"]
            for evidence in (normalized_evidence, rr_evidence)
        ),
        "queue_pending_is_zero": (
            int(normalized_summary["candidate_utility_pending"]) == 0
            and int(rr_summary["candidate_utility_pending"]) == 0
        ),
        "normalized_quality_floor": psnr_delta["lpm_mass_normalized"] >= -0.5,
        "rr_quality_floor": psnr_delta["lpm_mass_rr"] >= -0.5,
        "source_operator_pinned_and_causal": all(
            evidence["source_commit"] == prior.prior.LPM_COMMIT
            and not evidence["uses_lightglue"]
            and not evidence["uses_triangulation"]
            and not evidence["future_frames_used"]
            and not evidence["dataset_name_used"]
            and int(evidence["extra_renders"]) == 0
            and int(evidence["extra_adam_steps"]) == 0
            and int(evidence["mutation_rows"]) == 0
            for evidence in (normalized_evidence, rr_evidence)
        ),
    }
    report = {
        "protocol": "exp116_lpm_mass_prior_verification_v1",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "common_checks": common,
        "method_checks": method,
        "trace_difference_rows_vs_normalized_control": trace_delta,
        "psnr_delta_vs_normalized_control": psnr_delta,
        "selector_summaries": {
            "lpm_mass_normalized": normalized_summary,
            "lpm_mass_rr": rr_summary,
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
        "# Exp116 — LPM significant-zone mass prior",
        "",
        "The source-derived prior is `q=(active_pixels+256)/(H*W+256)`,",
        "where 256 pixels are exactly one official 16x16 LPM patch.",
        "No learned/tuned multiplier or additional physical work is used.",
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
    row = prior.selected_row()
    paths = scene_paths(row)
    prior.prior.prior.prior.prior.prior.prior.exp94.check_evaluation_contract(
        [row]
    )
    PANEL.v2.preflight(row, PANEL.scene_paths(row))
    check_source_lock()
    if args.action == "preflight":
        write_summary(None)
        print("Exp116 preflight PASS: 1 development scene x 3 fresh arms")
        return 0

    result = None
    evaluations = {}
    try:
        for arm in ARMS:
            run_mapper(arm, row, paths)
            evaluations[arm] = prior.evaluate(arm, row, paths)
        result = verify(row, paths, evaluations)
        write_summary(result)
        if not result["valid"]:
            raise RuntimeError("Exp116 verification stop")
        print(
            "Exp116 PASS: normalized mass delta="
            f"{result['arms']['lpm_mass_normalized']['psnr_delta_db']:+.6f} dB, "
            "trace rows="
            f"{result['arms']['lpm_mass_normalized']['trace_difference_rows']}",
            flush=True,
        )
    except Exception:
        if result is None:
            write_summary(None)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
