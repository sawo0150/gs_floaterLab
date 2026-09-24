#!/usr/bin/env python3
"""Exp112: freeze a genuinely active normalized dense temperature."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import run_exp111_dense_repeat_ercb as prior


ROOT = (
    prior.prior.prior.prior.base.WORKSPACE
    / "results/experiments/exp112_normalized_temperature"
)
DOCS = (
    prior.prior.prior.prior.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp112_normalized_temperature_20260924"
)
SCENES = (
    ("utmm", "square-1", "development quality gate"),
    ("rpng", "table_01", "frozen cross-family transfer"),
    ("aria", "aria1253", "frozen cross-family transfer"),
)
ARMS = (
    "r4_control",
    "repeat_log1p5",
    "repeat_gamma16",
    "repeat_rr",
)
BASE_GAMMA = math.log(1.5)
SELECTED_GAMMA = 16.0
SOURCE_PATHS = tuple(
    dict.fromkeys(
        (
            *prior.SOURCE_PATHS,
            Path(__file__).with_name(
                "analyze_exp111_normalized_temperature.py"
            ),
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


def check_source_lock() -> None:
    current = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in SOURCE_PATHS
    }
    path = ROOT / "source_lock.json"
    if path.exists():
        if read_json(path)["sha256"] != current:
            raise RuntimeError("Exp112 source changed after start; use a new root")
        return
    vigs_head = subprocess.check_output(
        (
            "git",
            "-C",
            str(prior.prior.prior.prior.base.PAPER_ROOT),
            "rev-parse",
            "HEAD",
        ),
        text=True,
    ).strip()
    lab_head = subprocess.check_output(
        (
            "git",
            "-C",
            str(prior.prior.prior.prior.base.WORKSPACE),
            "rev-parse",
            "HEAD",
        ),
        text=True,
    ).strip()
    write_json(
        path,
        {
            "protocol": "exp112_normalized_temperature_v1",
            "vigs_head": vigs_head,
            "lab_head": lab_head,
            "scenes": [list(scene[:2]) for scene in SCENES],
            "arms": list(ARMS),
            "development_scene": "utmm/square-1",
            "temperature_selection_used_quality_metric": False,
            "selection_rule": (
                "smallest constant gamma with >=10% repeat-trace "
                "divergence and >=10% final-generation count-CV "
                "reduction versus RR on the development scene"
            ),
            "selected_dense_gamma": SELECTED_GAMMA,
            "gamma_scaled_by_total_service": False,
            "quality_stop_db_vs_r4": -0.5,
            "no_scene_retuning": True,
            "sha256": current,
        },
    )


def scene_paths(row: dict) -> dict[str, Path]:
    common = prior.prior.prior.prior.base.sequence_paths(
        row["dataset"], row["scene"]
    )
    local = ROOT / row["dataset"] / row["scene"]
    return {
        **common,
        **{arm: local / arm for arm in ARMS},
        "verification": local / "ablation_verification.json",
        "result": local / "ablation_result.json",
    }


def mapping_command(arm: str, row: dict, output: Path) -> list[str]:
    command = prior.prior.prior.prior.base.mapping_command(
        "candidate", row["dataset"], row["scene"], ROOT
    )
    command[command.index("--output") + 1] = str(output)
    command.extend(("--ercb-selection-potential", "normalized_variance"))
    command.append("--dense-topology-first-persistence-ticket")
    if arm != "r4_control":
        command.append("--stage6r-aux-kf-to-dense-repeat")
    gamma = SELECTED_GAMMA if arm in ("repeat_gamma16", "repeat_rr") else BASE_GAMMA
    command.extend(("--dense-ercb-gamma", repr(gamma)))
    if arm == "repeat_rr":
        command.extend(("--ercb-rr-family", "dense"))
    return command


def run_mapper(arm: str, row: dict, paths: dict[str, Path]) -> None:
    output = paths[arm]
    if (output / "mapping_replay_runtime.json").exists():
        return
    if output.exists():
        raise FileExistsError(f"incomplete Exp112 output exists: {output}")
    prior.prior.prior.prior.panel.v2.gpu_idle()
    command = mapping_command(arm, row, output)
    write_json(output / "mapping_command.json", command)
    prior.prior.prior.prior.panel.v2.run_to_file(
        command, output / "mapping.log", custom=True
    )


def evaluate(arm: str, row: dict, paths: dict[str, Path]) -> dict:
    return prior.prior.prior.prior.panel.run_evaluation_twice(
        paths[arm],
        row["dataset"],
        row["scene"],
        paths["fixed_manifest"],
    )


def metrics(paths: dict[str, Path], arm: str) -> dict:
    return read_json(
        paths[arm] / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]


def selector_gamma(runtime: dict) -> float:
    return float(
        runtime["mapping_replay_summary"]["service_shortfall_gamma"]
    )


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
    control = runtimes["r4_control"]
    selected = runtimes["repeat_gamma16"]
    rr = runtimes["repeat_rr"]
    baseline = runtimes["repeat_log1p5"]
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
            "same_primary_slot_work": prior.slot_skeleton(
                runtime, "fixed_event_dense_opportunity_ledger"
            )
            == prior.slot_skeleton(
                control, "fixed_event_dense_opportunity_ledger"
            ),
            "zero_tail": runtime["post_eos_optimizer_updates"] == 0,
            "mapping_disjoint": (
                runtime["heldout_mapping_overlap_count"] == 0
                and runtime["heldout_gaussian_origin_overlap_count"] == 0
            ),
            "double_evaluation": bool(evaluations[arm]["pass"]),
        }
    method = {
        "control_has_aux_not_repeat": (
            bool(control["fixed_event_keyframe_opportunity_ledger"])
            and not control["fixed_event_dense_repeat_opportunity_ledger"]
        ),
        "repeat_arms_replace_aux_slot": all(
            not runtimes[arm]["fixed_event_keyframe_opportunity_ledger"]
            and prior.slot_skeleton(
                runtimes[arm],
                "fixed_event_dense_repeat_opportunity_ledger",
            )
            == prior.slot_skeleton(
                control, "fixed_event_keyframe_opportunity_ledger"
            )
            for arm in ARMS[1:]
        ),
        "baseline_gamma_is_log1p5": math.isclose(
            selector_gamma(baseline), BASE_GAMMA, abs_tol=1.0e-12
        ),
        "selected_gamma_is_constant_16": math.isclose(
            selector_gamma(selected), SELECTED_GAMMA, abs_tol=1.0e-12
        ),
        "rr_control_has_matching_gamma": math.isclose(
            selector_gamma(rr), SELECTED_GAMMA, abs_tol=1.0e-12
        ),
        "keyframe_gamma_frozen": all(
            math.isclose(
                float(runtime["service_shortfall_ercb_parameters"]["keyframe_gamma"]),
                BASE_GAMMA,
                abs_tol=1.0e-12,
            )
            for runtime in runtimes.values()
        ),
        "selected_dense_only_normalized": (
            selected["ercb_selection_potential_by_family"]
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
        "first_service_floor_active": all(
            runtimes[arm]["mapping_replay_summary"].get(
                "service_shortfall_first_service_floor"
            )
            == 1
            and runtimes[arm]["mapping_replay_summary"].get(
                "service_shortfall_repeat_draws", 0
            )
            > 0
            for arm in ARMS[1:]
        ),
        "tickets_add_no_work": all(
            runtime["dense_topology_ticket"]["extra_renders"] == 0
            and runtime["dense_topology_ticket"]["extra_adam_steps"] == 0
            for runtime in runtimes.values()
        ),
    }
    selected_trace = prior.dense_trace(selected)
    rr_trace = prior.dense_trace(rr)
    trace = {
        "selected_vs_rr_different_rows": sum(
            left != right
            for left, right in zip(selected_trace, rr_trace)
        ),
        "total_dense_rows": len(selected_trace),
        "selected_count_cv": float(
            selected["mapping_replay_summary"]["selection_count_cv"]
        ),
        "rr_count_cv": float(
            rr["mapping_replay_summary"]["selection_count_cv"]
        ),
        "selected_entropy_ratio": float(
            selected["mapping_replay_summary"][
                "service_shortfall_entropy_ratio"
            ]
        ),
    }
    quality = {
        "selected_minus_r4_db": (
            float(arm_metrics["repeat_gamma16"]["mean_psnr"])
            - float(arm_metrics["r4_control"]["mean_psnr"])
        ),
        "selected_minus_log1p5_db": (
            float(arm_metrics["repeat_gamma16"]["mean_psnr"])
            - float(arm_metrics["repeat_log1p5"]["mean_psnr"])
        ),
        "selected_minus_rr_db": (
            float(arm_metrics["repeat_gamma16"]["mean_psnr"])
            - float(arm_metrics["repeat_rr"]["mean_psnr"])
        ),
    }
    report = {
        "protocol": "exp112_normalized_temperature_verification_v1",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "common_checks": common,
        "method_checks": method,
        "selection_trace": trace,
        "quality": quality,
    }
    report["valid"] = (
        all(value for checks in common.values() for value in checks.values())
        and all(method.values())
        and trace["selected_vs_rr_different_rows"] > 0
        and quality["selected_minus_r4_db"] >= -0.5
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
                "dense_updates": int(
                    runtimes[arm]["mapping_replay_summary"]["dense_updates"]
                ),
                "keyframe_updates": int(
                    runtimes[arm]["mapping_replay_summary"]["keyframe_updates"]
                ),
            }
            for arm in ARMS
        },
        **quality,
        "selection_trace": trace,
        "valid": report["valid"],
    }
    write_json(paths["result"], result)
    return result


def run_one(row: dict) -> dict:
    paths = scene_paths(row)
    prior.prior.prior.prior.panel.v2.preflight(
        row, prior.prior.prior.prior.panel.scene_paths(row)
    )
    evaluations = {}
    for arm in ("r4_control", "repeat_log1p5", "repeat_gamma16"):
        run_mapper(arm, row, paths)
        evaluations[arm] = evaluate(arm, row, paths)
    selected_delta = (
        float(metrics(paths, "repeat_gamma16")["mean_psnr"])
        - float(metrics(paths, "r4_control")["mean_psnr"])
    )
    if selected_delta < -0.5:
        raise RuntimeError(
            f"Exp112 quality stop {row['dataset']}/{row['scene']}: "
            f"gamma16 minus R4={selected_delta:+.6f} dB"
        )
    run_mapper("repeat_rr", row, paths)
    evaluations["repeat_rr"] = evaluate("repeat_rr", row, paths)
    result = verify(row, paths, evaluations)
    if not result["valid"]:
        raise RuntimeError(
            f"Exp112 verification stop: {row['dataset']}/{row['scene']}"
        )
    print(
        f"Exp112 {row['dataset']}/{row['scene']}: "
        f"gamma16-R4={result['selected_minus_r4_db']:+.6f}, "
        f"gamma16-log1p5={result['selected_minus_log1p5_db']:+.6f}, "
        f"gamma16-RR={result['selected_minus_rr_db']:+.6f}",
        flush=True,
    )
    return result


def write_summary(rows: list[dict]) -> None:
    completed = []
    lines = [
        "# Exp112 — active normalized-variance dense temperature",
        "",
        "`gamma=16` was selected before image-quality evaluation on UTMM",
        "`square-1`: it is the smallest tested constant with at least 10%",
        "repeat-trace divergence and 10% final-generation count-CV reduction",
        "versus RR. The implemented law remains",
        "`p_i proportional exp(-gamma*n_i/(T+1))`; gamma is never scaled by",
        "`T`, and native/auxiliary keyframe queues retain `log(1.5)`.",
        "",
        "| Scene | R4 | repeat log1.5 | repeat gamma16 | repeat RR | g16-R4 | g16-log1.5 | g16-RR | trace diff | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        path = ROOT / row["dataset"] / row["scene"] / "ablation_result.json"
        if not path.exists():
            lines.append(
                f"| {row['dataset']}/{row['scene']} | — | — | — | — | — | — | — | — | PENDING |"
            )
            continue
        item = read_json(path)
        completed.append(item)
        arms = item["arms"]
        lines.append(
            f"| {item['dataset']}/{item['scene']} | "
            f"{arms['r4_control']['psnr']:.6f} | "
            f"{arms['repeat_log1p5']['psnr']:.6f} | "
            f"{arms['repeat_gamma16']['psnr']:.6f} | "
            f"{arms['repeat_rr']['psnr']:.6f} | "
            f"{item['selected_minus_r4_db']:+.6f} | "
            f"{item['selected_minus_log1p5_db']:+.6f} | "
            f"{item['selected_minus_rr_db']:+.6f} | "
            f"{item['selection_trace']['selected_vs_rr_different_rows']} | "
            f"{'PASS' if item['valid'] else 'FAIL'} |"
        )
    lines.extend(("", f"Completed scenes: **{len(completed)}/{len(rows)}**."))
    if completed:
        for field, label in (
            ("selected_minus_r4_db", "gamma16 minus R4"),
            ("selected_minus_log1p5_db", "gamma16 minus log1.5"),
            ("selected_minus_rr_db", "gamma16 minus RR"),
        ):
            value = sum(item[field] for item in completed) / len(completed)
            lines.append(f"Mean {label}: **{value:+.6f} dB**.")
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def selected_rows() -> list[dict]:
    inventory = prior.prior.prior.prior.panel.v2.install_inventory()
    indexed = {(row["dataset"], row["scene"]): row for row in inventory}
    rows = []
    for dataset, scene, _ in SCENES:
        key = (dataset, scene)
        if key not in indexed:
            raise RuntimeError(f"Exp112 scene missing from inventory: {key}")
        rows.append(indexed[key])
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run-one", "run-all"))
    parser.add_argument("--scene")
    args = parser.parse_args()
    rows = selected_rows()
    prior.prior.prior.prior.exp94.check_evaluation_contract(rows)
    if args.action == "preflight":
        for row in rows:
            prior.prior.prior.prior.panel.v2.preflight(
                row, prior.prior.prior.prior.panel.scene_paths(row)
            )
        check_source_lock()
        print(f"Exp112 preflight PASS: {len(rows)} scenes x {len(ARMS)} arms")
        return 0
    if args.action == "run-one":
        chosen = [row for row in rows if row["scene"] == args.scene]
        if len(chosen) != 1:
            raise ValueError("run-one requires one selected --scene")
    else:
        chosen = rows
    check_source_lock()
    try:
        for row in chosen:
            run_one(row)
    finally:
        write_summary(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
