#!/usr/bin/env python3
"""Exp122: isolate unified dense-view native topology statistics on RPNG."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp120_unified_dense_transfer as prior


BASE = prior.BASE
PANEL = prior.PANEL
ROOT = (
    BASE.WORKSPACE
    / "results/experiments/exp122_dense_global_topology_stats_isolation"
)
DOCS = (
    BASE.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp122_dense_global_topology_stats_isolation_20260924"
)
SCENE = ("rpng", "table_01")
ARMS = (
    "mass_normalized_control",
    "unified_stats_on",
    "unified_stats_off",
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
        raise RuntimeError(f"Exp122 inventory mismatch: {len(matches)} rows")
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
            raise RuntimeError("Exp122 source changed after start; use a new root")
        return
    write_json(
        path,
        {
            "protocol": "exp122_dense_global_topology_stats_isolation_v1",
            "scene": "/".join(SCENE),
            "arms": list(ARMS),
            "single_factor": (
                "whether the unified RGB dense replacement contributes "
                "radii and viewspace-gradient observations to native "
                "densification statistics"
            ),
            "dense_render_loss_adam_selector_unchanged": True,
            "keyframe_topology_statistics_unchanged": True,
            "new_scheduler_or_pruner": False,
            "quality_stop_db_vs_fresh_control": -0.5,
            "exact_render_and_adam_parity_required": True,
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
    command = prior.prior.prior.mapping_command(source_arm, row, output)
    if arm == "unified_stats_off":
        command.append("--r4-unified-dense-global-no-topology-stats")
    return command


def run_mapper(arm: str, row: dict, paths: dict[str, Path]) -> None:
    output = paths[arm]
    if (output / "mapping_replay_runtime.json").exists():
        return
    if output.exists():
        raise FileExistsError(f"incomplete Exp122 output exists: {output}")
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


def regular_topology(summary: dict) -> dict:
    regular = summary["topology_mutations"]["lifetime"].get("regular", {})
    return {
        "events": int(regular.get("events", 0)),
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
    psnr_control = float(
        arm_metrics["mass_normalized_control"]["mean_psnr"]
    )
    deltas = {
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

    control_summary = summaries["mass_normalized_control"]
    stats_on = summaries["unified_stats_on"]
    stats_off = summaries["unified_stats_off"]
    on_commits = int(stats_on["dense_global_scheduler_commits"])
    off_commits = int(stats_off["dense_global_scheduler_commits"])
    method = {
        "control_has_no_global_reallocation": (
            int(control_summary["dense_global_scheduler_enabled"]) == 0
            and int(control_summary["dense_global_scheduler_commits"]) == 0
        ),
        "stats_on_ledger_valid": prior.prior.corrected_ledger_valid(
            stats_on["dense_global_scheduler_ledger"]
        ),
        "stats_off_ledger_valid": prior.prior.corrected_ledger_valid(
            stats_off["dense_global_scheduler_ledger"]
        ),
        "stats_on_enabled_and_none_skipped": (
            int(stats_on["dense_global_topology_stats_enabled"]) == 1
            and int(stats_on["dense_global_topology_stats_skipped"]) == 0
        ),
        "stats_off_disabled_and_each_commit_skipped": (
            off_commits > 0
            and int(stats_off["dense_global_topology_stats_enabled"]) == 0
            and int(stats_off["dense_global_topology_stats_skipped"])
            == off_commits
        ),
        "same_reallocated_service_count": on_commits == off_commits,
        "stats_on_quality_floor": deltas["unified_stats_on"] >= -0.5,
        "stats_off_quality_floor": deltas["unified_stats_off"] >= -0.5,
    }
    verification = {
        "protocol": "exp122_dense_global_topology_stats_verification_v1",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "common_checks": common,
        "method_checks": method,
        "psnr_delta_vs_control": deltas,
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
        "protocol": "exp122_dense_global_topology_stats_result_v1",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "arms": {
            arm: {
                "psnr": float(arm_metrics[arm]["mean_psnr"]),
                "ssim": float(arm_metrics[arm]["mean_ssim"]),
                "lpips": float(arm_metrics[arm]["mean_lpips"]),
                "psnr_delta_db": float(deltas[arm]),
                "renders": int(runtimes[arm]["rasterized_view_updates"]),
                "adam": int(runtimes[arm]["optimizer_steps_completed"]),
                "gaussians": int(runtimes[arm]["gaussians"]),
                "mapping_wall_seconds": float(
                    runtimes[arm]["mapping_wall_seconds"]
                ),
                "dense_renders": int(
                    runtimes[arm]["lpm_error_zone_evidence"]["calls"]
                ),
                "dense_global_commits": int(
                    summaries[arm]["dense_global_scheduler_commits"]
                ),
                "dense_global_topology_stats_skipped": int(
                    summaries[arm]["dense_global_topology_stats_skipped"]
                ),
                "regular_topology": regular_topology(summaries[arm]),
            }
            for arm in ARMS
        },
        "method_checks": method,
        "valid": verification["valid"],
    }
    write_json(paths["result"], result)
    return result


def write_summary(result: dict | None) -> None:
    lines = [
        "# Exp122 — dense global topology-stat isolation",
        "",
        "The stats-off arm keeps the exact unified dense RGB render, loss,",
        "Adam step, and transactional normalized-variance selector. Only its",
        "native radii/gradient densification-stat observation is suppressed.",
        "",
    ]
    if result is None:
        lines.append("Status: **PENDING**.")
    else:
        lines.extend(
            (
                "| Arm | PSNR | Delta | SSIM | LPIPS | Renders | Adam | GS | Dense commits | Stats skipped | Regular added/removed/churn |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            )
        )
        for arm in ARMS:
            item = result["arms"][arm]
            topology = item["regular_topology"]
            lines.append(
                f"| {arm} | {item['psnr']:.6f} | "
                f"{item['psnr_delta_db']:+.6f} | {item['ssim']:.6f} | "
                f"{item['lpips']:.6f} | {item['renders']} | "
                f"{item['adam']} | {item['gaussians']} | "
                f"{item['dense_global_commits']} | "
                f"{item['dense_global_topology_stats_skipped']} | "
                f"{topology['added']}/{topology['removed']}/"
                f"{topology['churn']} |"
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
    row = selected_row()
    prior.prior.prior.prior.prior.prior.prior.prior.prior.prior.prior.exp94.check_evaluation_contract(
        [row]
    )
    PANEL.v2.preflight(row, PANEL.scene_paths(row))
    check_source_lock()
    if args.action == "preflight":
        write_summary(None)
        print("Exp122 preflight PASS: RPNG table_01 x 3 fresh arms")
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
            raise RuntimeError("Exp122 verification stop")
        print(
            "Exp122 PASS: stats-on="
            f"{result['arms']['unified_stats_on']['psnr_delta_db']:+.6f} dB, "
            "stats-off="
            f"{result['arms']['unified_stats_off']['psnr_delta_db']:+.6f} dB",
            flush=True,
        )
    except Exception:
        if result is None:
            write_summary(None)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
