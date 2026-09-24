#!/usr/bin/env python3
"""Exp113: behavior-neutral official-LPM error-zone telemetry gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp112_normalized_temperature as prior


ROOT = (
    prior.prior.prior.prior.prior.base.WORKSPACE
    / "results/experiments/exp113_lpm_error_zone_probe"
)
DOCS = (
    prior.prior.prior.prior.prior.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp113_lpm_error_zone_probe_20260924"
)
SCENE = ("utmm", "square-1")
ARMS = ("control", "lpm_probe")
LPM_ROOT = Path("/home/intern/gs_topology_references/lpm")
LPM_COMMIT = "7c060267cf55df76992e9ef2b6df42133ba9349f"
SOURCE_PATHS = tuple(
    dict.fromkeys(
        (
            *prior.SOURCE_PATHS,
            Path(__file__).with_name("lpm_error_zone_evidence.py"),
            Path(__file__).with_name("test_lpm_error_zone_evidence.py"),
            Path(__file__),
            LPM_ROOT / "lpm/utils.py",
            LPM_ROOT / "LICENSE.md",
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
    if not LPM_ROOT.is_dir():
        raise FileNotFoundError(f"pinned LPM checkout missing: {LPM_ROOT}")
    lpm_head = subprocess.check_output(
        ("git", "-C", str(LPM_ROOT), "rev-parse", "HEAD"), text=True
    ).strip()
    if lpm_head != LPM_COMMIT:
        raise RuntimeError(f"LPM commit mismatch: {lpm_head} != {LPM_COMMIT}")
    current = {str(path): sha256(path) for path in SOURCE_PATHS}
    path = ROOT / "source_lock.json"
    if path.exists():
        if read_json(path)["sha256"] != current:
            raise RuntimeError("Exp113 source changed after start; use a new root")
        return
    lab_head = subprocess.check_output(
        (
            "git",
            "-C",
            str(prior.prior.prior.prior.prior.base.WORKSPACE),
            "rev-parse",
            "HEAD",
        ),
        text=True,
    ).strip()
    vigs_head = subprocess.check_output(
        (
            "git",
            "-C",
            str(prior.prior.prior.prior.prior.base.PAPER_ROOT),
            "rev-parse",
            "HEAD",
        ),
        text=True,
    ).strip()
    write_json(
        path,
        {
            "protocol": "exp113_lpm_error_zone_probe_v1",
            "scene": "/".join(SCENE),
            "arms": list(ARMS),
            "lpm_repository": (
                "https://github.com/Surrey-UPLab/"
                "Localized-Gaussian-Point-Management"
            ),
            "lpm_commit": LPM_COMMIT,
            "lab_head_before_exp113_code_commit": lab_head,
            "vigs_head": vigs_head,
            "borrowed_operator": "lpm/utils.py::get_errormap(diff)",
            "full_lpm_used": False,
            "lightglue_used": False,
            "triangulation_used": False,
            "additional_renders_allowed": 0,
            "additional_adam_steps_allowed": 0,
            "quality_floor_db_vs_fresh_control": -0.1,
            "gpu_overhead_fraction_ceiling": 0.05,
            "mapping_wall_overhead_fraction_ceiling": 0.10,
            "signal_gate": (
                "nonzero and non-saturated score range, at least two unique "
                "scores, and at least one same-view repeat"
            ),
            "sha256": current,
        },
    )


def selected_row() -> dict:
    inventory = prior.prior.prior.prior.prior.panel.v2.install_inventory()
    matches = [
        row
        for row in inventory
        if (row["dataset"], row["scene"]) == SCENE
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Exp113 scene inventory mismatch: {len(matches)}")
    return matches[0]


def paths(row: dict) -> dict[str, Path]:
    common = prior.prior.prior.prior.prior.base.sequence_paths(
        row["dataset"], row["scene"]
    )
    local = ROOT / row["dataset"] / row["scene"]
    return {
        **common,
        "control": local / "control",
        "lpm_probe": local / "lpm_probe",
        "verification": local / "verification.json",
        "result": local / "result.json",
    }


def mapping_command(arm: str, row: dict, output: Path) -> list[str]:
    command = prior.mapping_command("repeat_gamma16", row, output)
    if arm == "lpm_probe":
        command.append("--lpm-error-zone-evidence-probe")
    return command


def run_mapper(arm: str, row: dict, scene_paths: dict[str, Path]) -> None:
    output = scene_paths[arm]
    if (output / "mapping_replay_runtime.json").exists():
        return
    if output.exists():
        raise FileExistsError(f"incomplete Exp113 output exists: {output}")
    prior.prior.prior.prior.prior.panel.v2.gpu_idle()
    command = mapping_command(arm, row, output)
    write_json(output / "mapping_command.json", command)
    prior.prior.prior.prior.prior.panel.v2.run_to_file(
        command, output / "mapping.log", custom=True
    )


def metrics(scene_paths: dict[str, Path], arm: str) -> dict:
    return read_json(
        scene_paths[arm]
        / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]


def evaluate(arm: str, row: dict, scene_paths: dict[str, Path]) -> dict:
    return prior.prior.prior.prior.prior.panel.run_evaluation_twice(
        scene_paths[arm],
        row["dataset"],
        row["scene"],
        scene_paths["fixed_manifest"],
    )


def verify(
    row: dict,
    scene_paths: dict[str, Path],
    evaluations: dict[str, dict],
) -> dict:
    runtimes = {
        arm: read_json(scene_paths[arm] / "mapping_replay_runtime.json")
        for arm in ARMS
    }
    arm_metrics = {arm: metrics(scene_paths, arm) for arm in ARMS}
    control = runtimes["control"]
    probe_runtime = runtimes["lpm_probe"]
    evidence = probe_runtime["lpm_error_zone_evidence"]
    control_ply_hash = sha256(scene_paths["control"] / "3dgs_before_final.ply")
    probe_ply_hash = sha256(scene_paths["lpm_probe"] / "3dgs_before_final.ply")
    common = {
        "same_archive": (
            control["archive_manifest_sha256"]
            == probe_runtime["archive_manifest_sha256"]
        ),
        "same_config": (
            control["effective_config_sha256"]
            == probe_runtime["effective_config_sha256"]
        ),
        "same_events": (
            control["event_ids_fully_processed"]
            == probe_runtime["event_ids_fully_processed"]
        ),
        "same_renders": (
            control["rasterized_view_updates"]
            == probe_runtime["rasterized_view_updates"]
        ),
        "same_adam": (
            control["optimizer_steps_completed"]
            == probe_runtime["optimizer_steps_completed"]
        ),
        "same_dense_admission": (
            control["dense_registered_frame_uids"]
            == probe_runtime["dense_registered_frame_uids"]
        ),
        "same_dense_selection_trace": (
            prior.prior.dense_trace(control)
            == prior.prior.dense_trace(probe_runtime)
        ),
        "same_saved_map_sha256": control_ply_hash == probe_ply_hash,
        "zero_tail": (
            control["post_eos_optimizer_updates"] == 0
            and probe_runtime["post_eos_optimizer_updates"] == 0
        ),
        "heldout_disjoint": (
            control["heldout_mapping_overlap_count"] == 0
            and probe_runtime["heldout_mapping_overlap_count"] == 0
            and control["heldout_gaussian_origin_overlap_count"] == 0
            and probe_runtime["heldout_gaussian_origin_overlap_count"] == 0
        ),
        "double_evaluation": all(
            bool(evaluations[arm]["pass"]) for arm in ARMS
        ),
    }
    observed_fixed_dense_work = sum(
        int(item["optimizer_steps_completed"])
        for field in (
            "fixed_event_dense_opportunity_ledger",
            "fixed_event_dense_repeat_opportunity_ledger",
        )
        for item in probe_runtime[field]
    )
    gpu_overhead_fraction = float(evidence["gpu_milliseconds"]) / (
        1000.0 * float(probe_runtime["mapping_wall_seconds"])
    )
    wall_overhead_fraction = (
        float(probe_runtime["mapping_wall_seconds"])
        - float(control["mapping_wall_seconds"])
    ) / float(control["mapping_wall_seconds"])
    method = {
        "control_probe_disabled": (
            not control["lpm_error_zone_evidence_probe_requested"]
            and control["lpm_error_zone_evidence"] is None
        ),
        "probe_enabled": (
            probe_runtime["lpm_error_zone_evidence_probe_requested"]
            and evidence["enabled"]
        ),
        "pinned_author_commit": evidence["source_commit"] == LPM_COMMIT,
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
        "gpu_overhead_below_5pct": gpu_overhead_fraction < 0.05,
        "mapping_wall_overhead_below_10pct": wall_overhead_fraction < 0.10,
    }
    quality_delta = (
        float(arm_metrics["lpm_probe"]["mean_psnr"])
        - float(arm_metrics["control"]["mean_psnr"])
    )
    quality = {
        "probe_minus_control_db": quality_delta,
        "quality_floor_pass": quality_delta >= -0.1,
    }
    report = {
        "protocol": "exp113_lpm_error_zone_probe_verification_v1",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "common_checks": common,
        "method_checks": method,
        "quality": quality,
        "control_ply_sha256": control_ply_hash,
        "probe_ply_sha256": probe_ply_hash,
        "gpu_overhead_fraction": gpu_overhead_fraction,
        "mapping_wall_overhead_fraction": wall_overhead_fraction,
        "evidence_summary": {
            key: value
            for key, value in evidence.items()
            if key != "records"
        },
    }
    report["valid"] = (
        all(common.values())
        and all(method.values())
        and quality["quality_floor_pass"]
    )
    write_json(scene_paths["verification"], report)
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
        "probe_minus_control_db": quality_delta,
        "gpu_overhead_fraction": gpu_overhead_fraction,
        "mapping_wall_overhead_fraction": wall_overhead_fraction,
        "evidence": report["evidence_summary"],
        "valid": report["valid"],
    }
    write_json(scene_paths["result"], result)
    return result


def write_summary(result: dict | None) -> None:
    lines = [
        "# Exp113 — official-LPM error-zone telemetry gate",
        "",
        "This experiment ports only the downloaded author implementation's",
        "`lpm/utils.py::get_errormap(diff)` operator at commit",
        f"`{LPM_COMMIT}`. It runs on an already-paid causal dense replay",
        "render/GT pair and performs no LightGlue matching, triangulation,",
        "additional render/Adam step, selection change, or map mutation.",
        "",
    ]
    if result is None:
        lines.append("Status: **PENDING**.")
    else:
        arms = result["arms"]
        evidence = result["evidence"]
        lines.extend(
            (
                "| Arm | PSNR | SSIM | LPIPS | Renders | Adam | Gaussians | Wall (s) |",
                "|---|---:|---:|---:|---:|---:|---:|---:|",
                (
                    f"| control | {arms['control']['psnr']:.6f} | "
                    f"{arms['control']['ssim']:.6f} | {arms['control']['lpips']:.6f} | "
                    f"{arms['control']['renders']} | {arms['control']['adam']} | "
                    f"{arms['control']['gaussians']} | {arms['control']['wall_seconds']:.3f} |"
                ),
                (
                    f"| LPM probe | {arms['lpm_probe']['psnr']:.6f} | "
                    f"{arms['lpm_probe']['ssim']:.6f} | {arms['lpm_probe']['lpips']:.6f} | "
                    f"{arms['lpm_probe']['renders']} | {arms['lpm_probe']['adam']} | "
                    f"{arms['lpm_probe']['gaussians']} | {arms['lpm_probe']['wall_seconds']:.3f} |"
                ),
                "",
                f"Probe minus control: **{result['probe_minus_control_db']:+.6f} dB**.",
                (
                    "LPM GPU evidence time / mapping wall: "
                    f"**{100.0 * result['gpu_overhead_fraction']:.3f}%**."
                ),
                (
                    "Probe-control mapping wall difference: "
                    f"**{100.0 * result['mapping_wall_overhead_fraction']:+.3f}%**."
                ),
                (
                    "Evidence calls/views/repeats: "
                    f"**{evidence['calls']}/{evidence['unique_generation_views']}/"
                    f"{evidence['repeat_calls']}**."
                ),
                (
                    "Error-zone score min/mean/max/std: "
                    f"**{evidence['score_min']:.6f}/"
                    f"{evidence['score_mean']:.6f}/"
                    f"{evidence['score_max']:.6f}/"
                    f"{evidence['score_population_std']:.6f}**."
                ),
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
    row = selected_row()
    scene_paths = paths(row)
    prior.prior.prior.prior.prior.exp94.check_evaluation_contract([row])
    prior.prior.prior.prior.prior.panel.v2.preflight(
        row, prior.prior.prior.prior.prior.panel.scene_paths(row)
    )
    check_source_lock()
    if args.action == "preflight":
        write_summary(None)
        print("Exp113 preflight PASS: 1 scene x 2 arms")
        return 0
    evaluations = {}
    try:
        for arm in ARMS:
            run_mapper(arm, row, scene_paths)
            evaluations[arm] = evaluate(arm, row, scene_paths)
        result = verify(row, scene_paths, evaluations)
        write_summary(result)
        if not result["valid"]:
            raise RuntimeError("Exp113 verification stop")
        print(
            "Exp113 PASS: "
            f"probe-control={result['probe_minus_control_db']:+.6f} dB, "
            f"GPU evidence fraction={100*result['gpu_overhead_fraction']:.3f}%",
            flush=True,
        )
    except Exception:
        write_summary(None)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
