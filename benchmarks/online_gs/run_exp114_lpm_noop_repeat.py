#!/usr/bin/env python3
"""Exp114: bracket LPM telemetry with two fresh no-probe controls."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import run_exp113_lpm_error_zone_probe as prior


ROOT = (
    prior.prior.prior.prior.prior.prior.base.WORKSPACE
    / "results/experiments/exp114_lpm_noop_repeat"
)
DOCS = (
    prior.prior.prior.prior.prior.prior.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp114_lpm_noop_repeat_20260924"
)
ARMS = ("control_a", "lpm_probe", "control_b")
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
            raise RuntimeError("Exp114 source changed after start; use a new root")
        return
    lab_head = subprocess.check_output(
        (
            "git",
            "-C",
            str(prior.prior.prior.prior.prior.prior.base.WORKSPACE),
            "rev-parse",
            "HEAD",
        ),
        text=True,
    ).strip()
    vigs_head = subprocess.check_output(
        (
            "git",
            "-C",
            str(prior.prior.prior.prior.prior.prior.base.PAPER_ROOT),
            "rev-parse",
            "HEAD",
        ),
        text=True,
    ).strip()
    write_json(
        path,
        {
            "protocol": "exp114_lpm_noop_repeat_v1",
            "scene": "utmm/square-1",
            "arm_order": list(ARMS),
            "lab_head_before_exp114_runner_commit": lab_head,
            "vigs_head": vigs_head,
            "lpm_commit": prior.LPM_COMMIT,
            "quality_floor_db_vs_control_mean": -0.1,
            "control_repeat_spread_ceiling_db": 0.1,
            "gaussian_count_tolerance_fraction": 0.001,
            "gpu_overhead_fraction_ceiling": 0.05,
            "mapping_wall_overhead_fraction_ceiling": 0.10,
            "exact_ply_hash_is_a_diagnostic_not_a_gate": True,
            "reason": (
                "Exp113 showed exact work/trace but 5-Gaussian and 0.0073dB "
                "differences; prior same-command controls already varied by "
                "22 Gaussians, so two fresh controls estimate CUDA run noise"
            ),
            "sha256": current,
        },
    )


def scene_paths(row: dict) -> dict[str, Path]:
    common = prior.prior.prior.prior.prior.prior.base.sequence_paths(
        row["dataset"], row["scene"]
    )
    local = ROOT / row["dataset"] / row["scene"]
    return {
        **common,
        **{arm: local / arm for arm in ARMS},
        "verification": local / "verification.json",
        "result": local / "result.json",
    }


def mapping_command(arm: str, row: dict, output: Path) -> list[str]:
    return prior.mapping_command(
        "lpm_probe" if arm == "lpm_probe" else "control",
        row,
        output,
    )


def run_mapper(arm: str, row: dict, paths: dict[str, Path]) -> None:
    output = paths[arm]
    if (output / "mapping_replay_runtime.json").exists():
        return
    if output.exists():
        raise FileExistsError(f"incomplete Exp114 output exists: {output}")
    prior.prior.prior.prior.prior.prior.panel.v2.gpu_idle()
    command = mapping_command(arm, row, output)
    write_json(output / "mapping_command.json", command)
    prior.prior.prior.prior.prior.prior.panel.v2.run_to_file(
        command, output / "mapping.log", custom=True
    )


def evaluate(arm: str, row: dict, paths: dict[str, Path]) -> dict:
    return prior.prior.prior.prior.prior.prior.panel.run_evaluation_twice(
        paths[arm], row["dataset"], row["scene"], paths["fixed_manifest"]
    )


def metrics(paths: dict[str, Path], arm: str) -> dict:
    return read_json(
        paths[arm] / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]


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
    reference = runtimes["control_a"]
    evidence = runtimes["lpm_probe"]["lpm_error_zone_evidence"]
    common = {}
    for arm, runtime in runtimes.items():
        common[arm] = {
            "same_archive": (
                runtime["archive_manifest_sha256"]
                == reference["archive_manifest_sha256"]
            ),
            "same_config": (
                runtime["effective_config_sha256"]
                == reference["effective_config_sha256"]
            ),
            "same_events": (
                runtime["event_ids_fully_processed"]
                == reference["event_ids_fully_processed"]
            ),
            "same_renders": (
                runtime["rasterized_view_updates"]
                == reference["rasterized_view_updates"]
            ),
            "same_adam": (
                runtime["optimizer_steps_completed"]
                == reference["optimizer_steps_completed"]
            ),
            "same_dense_admission": (
                runtime["dense_registered_frame_uids"]
                == reference["dense_registered_frame_uids"]
            ),
            "same_dense_selection_trace": (
                prior.prior.prior.dense_trace(runtime)
                == prior.prior.prior.dense_trace(reference)
            ),
            "zero_tail": runtime["post_eos_optimizer_updates"] == 0,
            "heldout_disjoint": (
                runtime["heldout_mapping_overlap_count"] == 0
                and runtime["heldout_gaussian_origin_overlap_count"] == 0
            ),
            "double_evaluation": bool(evaluations[arm]["pass"]),
        }

    control_psnr = [
        float(arm_metrics[arm]["mean_psnr"])
        for arm in ("control_a", "control_b")
    ]
    control_wall = [
        float(runtimes[arm]["mapping_wall_seconds"])
        for arm in ("control_a", "control_b")
    ]
    control_gaussians = [
        int(runtimes[arm]["gaussians"])
        for arm in ("control_a", "control_b")
    ]
    control_psnr_mean = sum(control_psnr) / 2.0
    control_wall_mean = sum(control_wall) / 2.0
    control_gaussian_mean = sum(control_gaussians) / 2.0
    probe_psnr = float(arm_metrics["lpm_probe"]["mean_psnr"])
    probe_wall = float(runtimes["lpm_probe"]["mapping_wall_seconds"])
    probe_gaussians = int(runtimes["lpm_probe"]["gaussians"])
    quality_delta = probe_psnr - control_psnr_mean
    control_spread = abs(control_psnr[1] - control_psnr[0])
    wall_overhead_fraction = (probe_wall - control_wall_mean) / control_wall_mean
    gpu_overhead_fraction = float(evidence["gpu_milliseconds"]) / (
        1000.0 * probe_wall
    )
    gaussian_deviation = abs(probe_gaussians - control_gaussian_mean)
    gaussian_tolerance = math.ceil(0.001 * control_gaussian_mean)
    ply_hashes = {
        arm: sha256(paths[arm] / "3dgs_before_final.ply") for arm in ARMS
    }
    observed_fixed_dense_work = sum(
        int(item["optimizer_steps_completed"])
        for field in (
            "fixed_event_dense_opportunity_ledger",
            "fixed_event_dense_repeat_opportunity_ledger",
        )
        for item in runtimes["lpm_probe"][field]
    )
    method = {
        "controls_probe_disabled": all(
            not runtimes[arm]["lpm_error_zone_evidence_probe_requested"]
            and runtimes[arm]["lpm_error_zone_evidence"] is None
            for arm in ("control_a", "control_b")
        ),
        "probe_enabled_and_pinned": (
            runtimes["lpm_probe"]["lpm_error_zone_evidence_probe_requested"]
            and evidence["enabled"]
            and evidence["source_commit"] == prior.LPM_COMMIT
        ),
        "all_paid_dense_slots_observed": (
            int(evidence["calls"]) == observed_fixed_dense_work
        ),
        "no_extra_work_or_mutation": (
            int(evidence["extra_renders"]) == 0
            and int(evidence["extra_adam_steps"]) == 0
            and int(evidence["mutation_rows"]) == 0
        ),
        "causal_dataset_agnostic": (
            not evidence["future_frames_used"]
            and not evidence["dataset_name_used"]
        ),
        "signal_non_degenerate": (
            int(evidence["score_nonzero_calls"]) > 0
            and int(evidence["score_saturated_calls"]) < int(evidence["calls"])
            and int(evidence["score_unique_values"]) >= 2
            and float(evidence["score_max"]) > float(evidence["score_min"])
            and int(evidence["views_observed_at_least_twice"]) > 0
        ),
        "control_repeat_spread_below_0p1db": control_spread <= 0.1,
        "probe_quality_floor": quality_delta >= -0.1,
        "probe_gaussian_count_within_0p1pct": (
            gaussian_deviation <= gaussian_tolerance
        ),
        "gpu_overhead_below_5pct": gpu_overhead_fraction < 0.05,
        "mapping_wall_overhead_below_10pct": wall_overhead_fraction < 0.10,
    }
    report = {
        "protocol": "exp114_lpm_noop_repeat_verification_v1",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "common_checks": common,
        "method_checks": method,
        "quality": {
            "control_psnr_mean": control_psnr_mean,
            "control_repeat_spread_db": control_spread,
            "probe_minus_control_mean_db": quality_delta,
        },
        "cost": {
            "control_wall_mean_seconds": control_wall_mean,
            "probe_wall_seconds": probe_wall,
            "mapping_wall_overhead_fraction": wall_overhead_fraction,
            "lpm_gpu_overhead_fraction": gpu_overhead_fraction,
        },
        "topology": {
            "control_gaussians": control_gaussians,
            "control_gaussian_mean": control_gaussian_mean,
            "probe_gaussians": probe_gaussians,
            "probe_deviation": gaussian_deviation,
            "tolerance": gaussian_tolerance,
            "ply_sha256": ply_hashes,
            "ply_hash_all_equal": len(set(ply_hashes.values())) == 1,
            "ply_hash_is_gate": False,
        },
        "evidence_summary": {
            key: value for key, value in evidence.items() if key != "records"
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
            }
            for arm in ARMS
        },
        **report["quality"],
        **report["cost"],
        "topology": report["topology"],
        "evidence": report["evidence_summary"],
        "valid": report["valid"],
    }
    write_json(paths["result"], result)
    return result


def write_summary(result: dict | None) -> None:
    lines = [
        "# Exp114 — official-LPM behavior-neutral repeat",
        "",
        "Two fresh no-probe controls bracket one probe run. Exact PLY byte",
        "identity is reported but is not a gate because Exp113 and prior",
        "same-command controls established CUDA/topology run variation.",
        "",
    ]
    if result is None:
        lines.append("Status: **PENDING**.")
    else:
        lines.extend(
            (
                "| Arm | PSNR | SSIM | LPIPS | Renders | Adam | GS | Wall (s) |",
                "|---|---:|---:|---:|---:|---:|---:|---:|",
            )
        )
        for arm in ARMS:
            item = result["arms"][arm]
            lines.append(
                f"| {arm} | {item['psnr']:.6f} | {item['ssim']:.6f} | "
                f"{item['lpips']:.6f} | {item['renders']} | {item['adam']} | "
                f"{item['gaussians']} | {item['wall_seconds']:.3f} |"
            )
        evidence = result["evidence"]
        lines.extend(
            (
                "",
                (
                    "Control PSNR spread / probe minus control mean: "
                    f"**{result['control_repeat_spread_db']:.6f} / "
                    f"{result['probe_minus_control_mean_db']:+.6f} dB**."
                ),
                (
                    "LPM GPU fraction / mapping-wall overhead: "
                    f"**{100*result['lpm_gpu_overhead_fraction']:.3f}% / "
                    f"{100*result['mapping_wall_overhead_fraction']:+.3f}%**."
                ),
                (
                    "Error-zone score min/mean/max/std: "
                    f"**{evidence['score_min']:.6f}/"
                    f"{evidence['score_mean']:.6f}/"
                    f"{evidence['score_max']:.6f}/"
                    f"{evidence['score_population_std']:.6f}**."
                ),
                (
                    "Probe GS deviation / predeclared tolerance: "
                    f"**{result['topology']['probe_deviation']:.1f}/"
                    f"{result['topology']['tolerance']}**."
                ),
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
    prior.prior.prior.prior.prior.prior.exp94.check_evaluation_contract([row])
    prior.prior.prior.prior.prior.prior.panel.v2.preflight(
        row,
        prior.prior.prior.prior.prior.prior.panel.scene_paths(row),
    )
    check_source_lock()
    if args.action == "preflight":
        write_summary(None)
        print("Exp114 preflight PASS: 1 scene x 3 fresh arms")
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
            raise RuntimeError("Exp114 verification stop")
        print(
            "Exp114 PASS: "
            f"probe-control_mean={result['probe_minus_control_mean_db']:+.6f} dB, "
            f"wall={100*result['mapping_wall_overhead_fraction']:+.3f}%",
            flush=True,
        )
    except Exception:
        if result is None:
            write_summary(None)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
