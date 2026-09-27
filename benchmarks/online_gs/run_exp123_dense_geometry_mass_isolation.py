#!/usr/bin/env python3
"""Exp123: test aggregate geometry-loss mass in unified dense replacement."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp122_dense_global_topology_stats_isolation as prior


BASE = prior.BASE
PANEL = prior.PANEL
ROOT = BASE.WORKSPACE / "results/experiments/exp123_dense_geometry_mass_isolation"
DOCS = (
    BASE.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp123_dense_geometry_mass_isolation_20260924"
)
SCENE = ("rpng", "table_01")
ARMS = (
    "mass_normalized_control",
    "unified_stats_off",
    "unified_stats_off_geometry_mass",
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


def selected_row() -> dict:
    matches = [
        row
        for row in PANEL.v2.install_inventory()
        if (row["dataset"], row["scene"]) == SCENE
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Exp123 inventory mismatch: {len(matches)} rows")
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


def check_source_lock() -> None:
    current = {str(path): sha256(path) for path in SOURCE_PATHS}
    path = ROOT / "source_lock.json"
    if path.exists():
        if read_json(path)["sha256"] != current:
            raise RuntimeError("Exp123 source changed after start; use a new root")
        return
    write_json(
        path,
        {
            "protocol": "exp123_dense_geometry_mass_isolation_v1",
            "scene": "/".join(SCENE),
            "arms": list(ARMS),
            "single_factor": (
                "scale only remaining RGB-D depth and normal loss by "
                "(D+1)/D when one RGB-only dense view replaces one RGB-D view"
            ),
            "topology_stats_disabled_in_both_unified_arms": True,
            "rgb_render_adam_selector_unchanged": True,
            "new_paper_method_port": False,
            "diagnostic_not_method_claim": True,
            "quality_stop_db_vs_fresh_control": -0.5,
            "substantial_recovery_fraction": 0.5,
            "weak_recovery_fraction": 0.2,
            "scene_or_dataset_hyperparameters": False,
            "lab_head": subprocess.check_output(
                ("git", "-C", str(BASE.WORKSPACE), "rev-parse", "HEAD"),
                text=True,
            ).strip(),
            "vigs_head": subprocess.check_output(
                ("git", "-C", str(BASE.PAPER_ROOT), "rev-parse", "HEAD"),
                text=True,
            ).strip(),
            "sha256": current,
        },
    )


def mapping_command(arm: str, row: dict, output: Path) -> list[str]:
    source_arm = (
        "mass_normalized_control"
        if arm == "mass_normalized_control"
        else "unified_mass_normalized"
    )
    command = prior.prior.prior.prior.mapping_command(
        source_arm, row, output
    )
    if arm != "mass_normalized_control":
        command.append("--r4-unified-dense-global-no-topology-stats")
    if arm == "unified_stats_off_geometry_mass":
        command.append(
            "--r4-unified-dense-global-preserve-geometry-mass"
        )
    return command


def run_mapper(arm: str, row: dict, paths: dict[str, Path]) -> None:
    output = paths[arm]
    if (output / "mapping_replay_runtime.json").exists():
        return
    if output.exists():
        raise FileExistsError(f"incomplete Exp123 output exists: {output}")
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


def topology_open_rows(ledger: list[dict]) -> int:
    return sum(
        row["optimizer_committed"] and row["controller_phase"] == "frontier"
        for row in ledger
    )


def expected_geometry_scales(ledger: list[dict]) -> list[float]:
    values = []
    for row in ledger:
        if not row["optimizer_committed"]:
            continue
        depth_carriers = len(row["recent_window_uids"]) + len(
            row["tracked_global_uids"]
        )
        if depth_carriers <= 0:
            raise RuntimeError("unified ledger has no RGB-D carrier")
        values.append((depth_carriers + 1) / depth_carriers)
    return values


def regular_topology(summary: dict) -> dict:
    regular = summary["topology_mutations"]["lifetime"].get("regular", {})
    return {
        "added": int(regular.get("added", 0)),
        "removed": int(regular.get("removed", 0)),
        "churn": int(regular.get("churn", 0)),
    }


def verify(
    row: dict,
    paths: dict[str, Path],
    evaluations: dict[str, dict],
) -> dict:
    runtimes = {
        arm: read_json(paths[arm] / "mapping_replay_runtime.json")
        for arm in ARMS
    }
    summaries = {
        arm: runtime["mapping_replay_summary"]
        for arm, runtime in runtimes.items()
    }
    arm_metrics = {arm: metrics(paths, arm) for arm in ARMS}
    control = runtimes["mass_normalized_control"]
    psnr = {
        arm: float(arm_metrics[arm]["mean_psnr"])
        for arm in ARMS
    }
    deltas = {arm: value - psnr["mass_normalized_control"] for arm, value in psnr.items()}

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

    base_summary = summaries["unified_stats_off"]
    mass_summary = summaries["unified_stats_off_geometry_mass"]
    base_ledger = base_summary["dense_global_scheduler_ledger"]
    mass_ledger = mass_summary["dense_global_scheduler_ledger"]
    expected_scales = expected_geometry_scales(mass_ledger)
    expected_mean = sum(expected_scales) / len(expected_scales)
    expected_max = max(expected_scales)
    method = {
        "control_has_no_global_reallocation": int(
            summaries["mass_normalized_control"]["dense_global_scheduler_commits"]
        )
        == 0,
        "both_unified_ledgers_valid": (
            prior.prior.prior.corrected_ledger_valid(base_ledger)
            and prior.prior.prior.corrected_ledger_valid(mass_ledger)
        ),
        "same_reallocated_service_count": int(
            base_summary["dense_global_scheduler_commits"]
        )
        == int(mass_summary["dense_global_scheduler_commits"]),
        "topology_stats_disabled_and_complete": all(
            int(summary["dense_global_topology_stats_enabled"]) == 0
            and int(summary["dense_global_topology_stats_skipped"])
            == topology_open_rows(summary["dense_global_scheduler_ledger"])
            for summary in (base_summary, mass_summary)
        ),
        "base_geometry_mass_disabled": (
            int(base_summary["dense_global_geometry_mass_preservation"]) == 0
            and int(base_summary["dense_global_geometry_mass_steps"]) == 0
        ),
        "mass_geometry_steps_equal_commits": (
            int(mass_summary["dense_global_geometry_mass_preservation"]) == 1
            and int(mass_summary["dense_global_geometry_mass_steps"])
            == len(expected_scales)
            == int(mass_summary["dense_global_scheduler_commits"])
        ),
        "mass_geometry_scale_matches_ledger": (
            abs(
                float(mass_summary["dense_global_geometry_scale_mean"])
                - expected_mean
            )
            < 1e-12
            and abs(
                float(mass_summary["dense_global_geometry_scale_max"])
                - expected_max
            )
            < 1e-12
        ),
        "base_quality_floor": deltas["unified_stats_off"] >= -0.5,
        "mass_quality_floor": deltas["unified_stats_off_geometry_mass"] >= -0.5,
    }
    gap = psnr["mass_normalized_control"] - psnr["unified_stats_off"]
    recovery = (
        psnr["unified_stats_off_geometry_mass"]
        - psnr["unified_stats_off"]
    )
    recovery_fraction = recovery / gap if gap > 0 else None
    if recovery_fraction is None:
        diagnosis = "baseline_has_no_positive_gap"
    elif recovery_fraction >= 0.5:
        diagnosis = "aggregate_geometry_mass_is_substantial"
    elif recovery_fraction <= 0.2:
        diagnosis = "view_specific_geometry_coverage_dominates"
    else:
        diagnosis = "mixed_geometry_mass_and_coverage"

    verification = {
        "protocol": "exp123_dense_geometry_mass_verification_v1",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "common_checks": common,
        "method_checks": method,
        "psnr_delta_vs_control": deltas,
        "recovery_db": recovery,
        "recovery_fraction": recovery_fraction,
        "predeclared_diagnosis": diagnosis,
        "valid": (
            all(
                value
                for checks in common.values()
                for value in checks.values()
            )
            and all(method.values())
        ),
    }
    write_json(paths["verification"], verification)

    result = {
        "protocol": "exp123_dense_geometry_mass_result_v1",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "arms": {
            arm: {
                "psnr": psnr[arm],
                "ssim": float(arm_metrics[arm]["mean_ssim"]),
                "lpips": float(arm_metrics[arm]["mean_lpips"]),
                "psnr_delta_db": deltas[arm],
                "renders": int(runtimes[arm]["rasterized_view_updates"]),
                "adam": int(runtimes[arm]["optimizer_steps_completed"]),
                "gaussians": int(runtimes[arm]["gaussians"]),
                "dense_global_commits": int(
                    summaries[arm]["dense_global_scheduler_commits"]
                ),
                "geometry_mass_steps": int(
                    summaries[arm]["dense_global_geometry_mass_steps"]
                ),
                "geometry_scale_mean": float(
                    summaries[arm]["dense_global_geometry_scale_mean"]
                ),
                "regular_topology": regular_topology(summaries[arm]),
            }
            for arm in ARMS
        },
        "recovery_db": recovery,
        "recovery_fraction": recovery_fraction,
        "diagnosis": diagnosis,
        "method_checks": method,
        "valid": verification["valid"],
    }
    write_json(paths["result"], result)
    return result


def write_summary(result: dict | None) -> None:
    lines = [
        "# Exp123 — dense replacement geometry-mass isolation",
        "",
        "Both unified arms suppress dense-origin native topology statistics.",
        "The candidate alone rescales remaining RGB-D depth/normal terms by",
        "`(D+1)/D`; it adds no render, Adam step, or paper-method component.",
        "",
    ]
    if result is None:
        lines.append("Status: **PENDING**.")
    else:
        lines.extend(
            (
                "| Arm | PSNR | Delta | SSIM | LPIPS | Render | Adam | GS | Dense commits | Geometry steps/mean scale | Churn |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            )
        )
        for arm in ARMS:
            item = result["arms"][arm]
            lines.append(
                f"| {arm} | {item['psnr']:.6f} | "
                f"{item['psnr_delta_db']:+.6f} | {item['ssim']:.6f} | "
                f"{item['lpips']:.6f} | {item['renders']} | "
                f"{item['adam']} | {item['gaussians']} | "
                f"{item['dense_global_commits']} | "
                f"{item['geometry_mass_steps']} / "
                f"{item['geometry_scale_mean']:.6f} | "
                f"{item['regular_topology']['churn']} |"
            )
        fraction = result["recovery_fraction"]
        lines.extend(
            (
                "",
                f"Recovery: **{result['recovery_db']:+.6f} dB** "
                + (
                    f"(**{100 * fraction:.2f}%** of the stats-off gap)."
                    if fraction is not None
                    else "(undefined because the base gap is non-positive)."
                ),
                f"Predeclared diagnosis: `{result['diagnosis']}`.",
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
    prior.prior.prior.prior.prior.prior.prior.prior.prior.prior.prior.prior.exp94.check_evaluation_contract(
        [row]
    )
    PANEL.v2.preflight(row, PANEL.scene_paths(row))
    check_source_lock()
    if args.action == "preflight":
        write_summary(None)
        print("Exp123 preflight PASS: RPNG table_01 x 3 fresh arms")
        return 0

    paths = scene_paths(row)
    evaluations = {}
    result = None
    try:
        for arm in ARMS:
            run_mapper(arm, row, paths)
            evaluations[arm] = evaluate(arm, row, paths)
        result = verify(row, paths, evaluations)
        write_summary(result)
        if not result["valid"]:
            raise RuntimeError("Exp123 verification stop")
        print(
            "Exp123 PASS: recovery="
            f"{result['recovery_db']:+.6f} dB, "
            f"diagnosis={result['diagnosis']}",
            flush=True,
        )
    except Exception:
        if result is None:
            write_summary(None)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
