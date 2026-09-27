#!/usr/bin/env python3
"""Exp111: reallocate the auxiliary-KF slot to true dense repeat service."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp110_rr_ticket_ablation as prior


ROOT = prior.prior.prior.base.WORKSPACE / "results/experiments/exp111_dense_repeat_ercb"
DOCS = (
    prior.prior.prior.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp111_dense_repeat_ercb_20260924"
)
SCENES = (
    ("utmm", "square-1", "scarce-work repeat-activity gate"),
    ("rpng", "table_01", "R4 quality-floor gate"),
    ("aria", "aria1253", "cross-family transfer gate"),
)
ARMS = ("r4_control", "dense_repeat_normalized", "dense_repeat_rr")
SOURCE_PATHS = tuple(dict.fromkeys((
    *prior.SOURCE_PATHS,
    prior.prior.prior.base.PAPER_ROOT / "vigs/gs_backend.py",
    Path(__file__),
)))


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
            raise RuntimeError("Exp111 source changed after start; use a new root")
        return
    vigs_head = subprocess.check_output(
        (
            "git",
            "-C",
            str(prior.prior.prior.base.PAPER_ROOT),
            "rev-parse",
            "HEAD",
        ),
        text=True,
    ).strip()
    lab_head = subprocess.check_output(
        (
            "git",
            "-C",
            str(prior.prior.prior.base.WORKSPACE),
            "rev-parse",
            "HEAD",
        ),
        text=True,
    ).strip()
    write_json(
        path,
        {
            "protocol": "exp111_dense_repeat_ercb_v1",
            "vigs_head": vigs_head,
            "lab_head": lab_head,
            "scenes": [list(scene[:2]) for scene in SCENES],
            "arms": list(ARMS),
            "quality_stop_db": -0.5,
            "no_scene_retuning": True,
            "sha256": current,
        },
    )


def scene_paths(row: dict) -> dict[str, Path]:
    common = prior.prior.prior.base.sequence_paths(
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
    command = prior.prior.prior.base.mapping_command(
        "candidate", row["dataset"], row["scene"], ROOT
    )
    command[command.index("--output") + 1] = str(output)
    command.extend(("--ercb-selection-potential", "normalized_variance"))
    command.append("--dense-topology-first-persistence-ticket")
    if arm != "r4_control":
        command.append("--stage6r-aux-kf-to-dense-repeat")
    if arm == "dense_repeat_rr":
        command.extend(("--ercb-rr-family", "dense"))
    return command


def run_mapper(arm: str, row: dict, paths: dict[str, Path]) -> None:
    output = paths[arm]
    if (output / "mapping_replay_runtime.json").exists():
        return
    if output.exists():
        raise FileExistsError(f"incomplete Exp111 output exists: {output}")
    prior.prior.prior.panel.v2.gpu_idle()
    command = mapping_command(arm, row, output)
    write_json(output / "mapping_command.json", command)
    prior.prior.prior.panel.v2.run_to_file(
        command, output / "mapping.log", custom=True
    )


def evaluate(arm: str, row: dict, paths: dict[str, Path]) -> dict:
    return prior.prior.prior.panel.run_evaluation_twice(
        paths[arm],
        row["dataset"],
        row["scene"],
        paths["fixed_manifest"],
    )


def opportunity_skeleton(runtime: dict, field: str) -> list[dict]:
    return prior.prior.prior.panel.v2.opportunity_skeleton(runtime, field)


def slot_skeleton(runtime: dict, field: str) -> list[tuple[int, int, int, int]]:
    return [
        (
            int(row["event_id"]),
            int(row["map_generation"]),
            int(row["optimizer_steps_completed"]),
            int(row["rasterized_view_updates"]),
        )
        for row in runtime[field]
    ]


def dense_trace(runtime: dict) -> list:
    result = []
    for primary, repeat in zip(
        runtime["fixed_event_dense_opportunity_ledger"],
        runtime["fixed_event_dense_repeat_opportunity_ledger"],
    ):
        result.extend((primary["selected_keys"], repeat["selected_keys"]))
    return result


def verify(row: dict, paths: dict[str, Path]) -> dict:
    runtimes = {
        arm: read_json(paths[arm] / "mapping_replay_runtime.json")
        for arm in ARMS
    }
    control = runtimes["r4_control"]
    normalized = runtimes["dense_repeat_normalized"]
    rr = runtimes["dense_repeat_rr"]
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
            "same_primary_opportunities": opportunity_skeleton(
                runtime, "fixed_event_dense_opportunity_ledger"
            )
            == opportunity_skeleton(
                control, "fixed_event_dense_opportunity_ledger"
            ),
            "zero_tail": runtime["post_eos_optimizer_updates"] == 0,
            "mapping_disjoint": (
                runtime["heldout_mapping_overlap_count"] == 0
                and runtime["heldout_gaussian_origin_overlap_count"] == 0
            ),
        }
    method = {
        "control_has_aux_not_repeat": (
            len(control["fixed_event_keyframe_opportunity_ledger"]) > 0
            and not control["fixed_event_dense_repeat_opportunity_ledger"]
        ),
        "normalized_reallocates_same_slot_count": (
            not normalized["fixed_event_keyframe_opportunity_ledger"]
            and slot_skeleton(
                normalized,
                "fixed_event_dense_repeat_opportunity_ledger",
            )
            == slot_skeleton(
                control,
                "fixed_event_keyframe_opportunity_ledger",
            )
        ),
        "rr_reallocates_same_slot_count": (
            not rr["fixed_event_keyframe_opportunity_ledger"]
            and slot_skeleton(
                rr,
                "fixed_event_dense_repeat_opportunity_ledger",
            )
            == slot_skeleton(
                control,
                "fixed_event_keyframe_opportunity_ledger",
            )
        ),
        "normalized_dense_only_selector": (
            normalized["ercb_selection_potential_by_family"]
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
        "primary_clock_matches_control": (
            normalized["dense_primary_service_updates"]
            == control["mapping_replay_summary"]["dense_updates"]
            and rr["dense_primary_service_updates"]
            == control["mapping_replay_summary"]["dense_updates"]
        ),
        "normalized_repeat_is_active": (
            normalized["mapping_replay_summary"].get(
                "service_shortfall_first_service_floor"
            )
            == 1
            and normalized["mapping_replay_summary"].get(
                "service_shortfall_repeat_draws", 0
            )
            > 0
            and normalized["mapping_replay_summary"]["selection_count_max"]
            > 1
        ),
        "rr_repeat_is_active": (
            rr["mapping_replay_summary"].get(
                "service_shortfall_first_service_floor"
            )
            == 1
            and rr["mapping_replay_summary"].get(
                "service_shortfall_repeat_draws", 0
            )
            > 0
            and rr["mapping_replay_summary"]["selection_count_max"] > 1
        ),
        "tickets_add_no_work": all(
            runtime["dense_topology_ticket"]["extra_renders"] == 0
            and runtime["dense_topology_ticket"]["extra_adam_steps"] == 0
            for runtime in runtimes.values()
        ),
    }
    trace = {
        "normalized_vs_rr_dense_different_rows": sum(
            left != right
            for left, right in zip(dense_trace(normalized), dense_trace(rr))
        ),
        "normalized_dense_services": int(
            normalized["mapping_replay_summary"]["dense_updates"]
        ),
        "normalized_repeat_draws": int(
            normalized["mapping_replay_summary"][
                "service_shortfall_repeat_draws"
            ]
        ),
        "normalized_selection_count_min": int(
            normalized["mapping_replay_summary"]["selection_count_min"]
        ),
        "normalized_selection_count_max": int(
            normalized["mapping_replay_summary"]["selection_count_max"]
        ),
    }
    report = {
        "protocol": "exp111_dense_repeat_verification_v1",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "common_checks": common,
        "method_checks": method,
        "selection_trace": trace,
    }
    report["valid"] = (
        all(value for checks in common.values() for value in checks.values())
        and all(method.values())
        and trace["normalized_vs_rr_dense_different_rows"] > 0
    )
    write_json(paths["verification"], report)
    return report


def metrics(paths: dict[str, Path], arm: str) -> dict:
    return read_json(
        paths[arm] / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]


def run_one(row: dict) -> dict:
    paths = scene_paths(row)
    prior.prior.prior.panel.v2.preflight(
        row, prior.prior.prior.panel.scene_paths(row)
    )
    check_source_lock()
    evaluations = {}
    for arm in ("r4_control", "dense_repeat_normalized"):
        run_mapper(arm, row, paths)
        evaluations[arm] = evaluate(arm, row, paths)
    control_metrics = metrics(paths, "r4_control")
    normalized_metrics = metrics(paths, "dense_repeat_normalized")
    quality_delta = float(normalized_metrics["mean_psnr"]) - float(
        control_metrics["mean_psnr"]
    )
    if quality_delta < -0.5:
        raise RuntimeError(
            f"Exp111 quality stop {row['dataset']}/{row['scene']}: "
            f"dense-repeat minus R4={quality_delta:+.6f} dB"
        )
    run_mapper("dense_repeat_rr", row, paths)
    evaluations["dense_repeat_rr"] = evaluate(
        "dense_repeat_rr", row, paths
    )
    verification = verify(row, paths)
    if not verification["valid"]:
        raise RuntimeError(
            f"Exp111 structural stop: {row['dataset']}/{row['scene']}"
        )
    arm_metrics = {arm: metrics(paths, arm) for arm in ARMS}
    runtimes = {
        arm: read_json(paths[arm] / "mapping_replay_runtime.json")
        for arm in ARMS
    }
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
                "double_evaluation_pass": bool(evaluations[arm]["pass"]),
            }
            for arm in ARMS
        },
        "normalized_minus_r4_db": quality_delta,
        "normalized_minus_rr_db": (
            float(arm_metrics["dense_repeat_normalized"]["mean_psnr"])
            - float(arm_metrics["dense_repeat_rr"]["mean_psnr"])
        ),
        "selection_trace": verification["selection_trace"],
        "valid": verification["valid"]
        and all(value["pass"] for value in evaluations.values()),
    }
    write_json(paths["result"], result)
    print(
        f"Exp111 {row['dataset']}/{row['scene']}: "
        f"repeat-R4={result['normalized_minus_r4_db']:+.6f}, "
        f"normalized-RR={result['normalized_minus_rr_db']:+.6f}",
        flush=True,
    )
    return result


def write_summary(rows: list[dict]) -> None:
    completed = []
    lines = [
        "# Exp111 — first-service floor + dense repeat ERCB isolation",
        "",
        "The candidate replaces the existing auxiliary-keyframe one-view slot",
        "with a dense repeat slot. It adds no render or Adam step. Only the",
        "primary dense service mints admission credit; every newly admitted",
        "view receives a hard first service, then repeat slots use the",
        "normalized-variance Gibbs law over the admitted pool.",
        "",
        "| Scene | R4 | Dense repeat N | Dense repeat RR | N-R4 | N-RR | Dense trace diff | Repeat/count range | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        path = ROOT / row["dataset"] / row["scene"] / "ablation_result.json"
        if not path.exists():
            lines.append(
                f"| {row['dataset']}/{row['scene']} | — | — | — | — | — | — | — | PENDING |"
            )
            continue
        item = read_json(path)
        completed.append(item)
        arms = item["arms"]
        trace = item["selection_trace"]
        lines.append(
            f"| {item['dataset']}/{item['scene']} | "
            f"{arms['r4_control']['psnr']:.6f} | "
            f"{arms['dense_repeat_normalized']['psnr']:.6f} | "
            f"{arms['dense_repeat_rr']['psnr']:.6f} | "
            f"{item['normalized_minus_r4_db']:+.6f} | "
            f"{item['normalized_minus_rr_db']:+.6f} | "
            f"{trace['normalized_vs_rr_dense_different_rows']} | "
            f"{trace['normalized_repeat_draws']}/"
            f"{trace['normalized_selection_count_min']}-"
            f"{trace['normalized_selection_count_max']} | "
            f"{'PASS' if item['valid'] else 'FAIL'} |"
        )
    lines.extend(("", f"Completed scenes: **{len(completed)}/{len(rows)}**."))
    if completed:
        mean_r4 = sum(x["normalized_minus_r4_db"] for x in completed) / len(
            completed
        )
        mean_rr = sum(x["normalized_minus_rr_db"] for x in completed) / len(
            completed
        )
        lines.extend(
            (
                f"Mean dense-repeat minus R4: **{mean_r4:+.6f} dB**.",
                f"Mean normalized minus dense-only RR: **{mean_rr:+.6f} dB**.",
            )
        )
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def selected_rows() -> list[dict]:
    inventory = prior.prior.prior.panel.v2.install_inventory()
    indexed = {
        (row["dataset"], row["scene"]): row for row in inventory
    }
    rows = []
    for dataset, scene, _ in SCENES:
        key = (dataset, scene)
        if key not in indexed:
            raise RuntimeError(f"Exp111 scene missing from inventory: {key}")
        rows.append(indexed[key])
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run-one", "run-all"))
    parser.add_argument("--scene")
    args = parser.parse_args()
    rows = selected_rows()
    prior.prior.prior.exp94.check_evaluation_contract(rows)
    if args.action == "preflight":
        for row in rows:
            prior.prior.prior.panel.v2.preflight(
                row, prior.prior.prior.panel.scene_paths(row)
            )
        check_source_lock()
        print(f"Exp111 preflight PASS: {len(rows)} scenes x {len(ARMS)} arms")
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
