#!/usr/bin/env python3
"""Exp110: selector-only RR and ticket-off isolation on scarce-work scenes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp106_first_persistence_ticket as prior


ROOT = prior.prior.base.WORKSPACE / "results/experiments/exp110_rr_ticket_ablation"
DOCS = (
    prior.prior.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp110_rr_ticket_ablation_20260924"
)
SCENES = (
    ("utmm", "fast-straight", "no-native-service negative control"),
    ("utmm", "ego-centric-2", "low-work active-native selector"),
    ("utmm", "square-1", "historical ERCB stress scene"),
)
ARMS = (
    "normalized_ticket",
    "rr_ticket",
    "normalized_no_ticket",
)
SOURCE_PATHS = (
    *prior.SOURCE_PATHS,
    prior.prior.base.PAPER_ROOT / "vigs/map_scheduler.py",
    prior.prior.base.PAPER_ROOT / "vigs/gaussian/scene/gaussian_model.py",
    Path(__file__),
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
            raise RuntimeError("Exp110 source changed after start; use a new root")
        return
    vigs_head = subprocess.check_output(
        ("git", "-C", str(prior.prior.base.PAPER_ROOT), "rev-parse", "HEAD"),
        text=True,
    ).strip()
    lab_head = subprocess.check_output(
        ("git", "-C", str(prior.prior.base.WORKSPACE), "rev-parse", "HEAD"),
        text=True,
    ).strip()
    write_json(
        path,
        {
            "protocol": "exp110_rr_ticket_ablation_v1",
            "vigs_head": vigs_head,
            "lab_head": lab_head,
            "scenes": [list(scene[:2]) for scene in SCENES],
            "arms": list(ARMS),
            "no_scene_retuning": True,
            "sha256": current,
        },
    )


def scene_paths(row: dict) -> dict[str, Path]:
    common = prior.prior.base.sequence_paths(row["dataset"], row["scene"])
    local = ROOT / row["dataset"] / row["scene"]
    return {
        **common,
        **{arm: local / arm for arm in ARMS},
        "verification": local / "ablation_verification.json",
        "result": local / "ablation_result.json",
    }


def run_mapper(arm: str, row: dict, paths: dict[str, Path]) -> None:
    output = paths[arm]
    if (output / "mapping_replay_runtime.json").exists():
        return
    if output.exists():
        raise FileExistsError(f"incomplete Exp110 output exists: {output}")
    prior.prior.panel.v2.gpu_idle()
    command = prior.prior.base.mapping_command(
        "candidate", row["dataset"], row["scene"], ROOT
    )
    command[command.index("--output") + 1] = str(output)
    potential = "rr" if arm == "rr_ticket" else "normalized_variance"
    command.extend(("--ercb-selection-potential", potential))
    if arm != "normalized_no_ticket":
        command.append("--dense-topology-first-persistence-ticket")
    write_json(output / "mapping_command.json", command)
    prior.prior.panel.v2.run_to_file(
        command, output / "mapping.log", custom=True
    )


def opportunity_skeleton(runtime: dict, field: str) -> list[dict]:
    return prior.prior.panel.v2.opportunity_skeleton(runtime, field)


def selected_trace(runtime: dict, field: str, key: str) -> list:
    return [row.get(key) for row in runtime[field]]


def verify(row: dict, paths: dict[str, Path]) -> dict:
    runtimes = {
        arm: read_json(paths[arm] / "mapping_replay_runtime.json")
        for arm in ARMS
    }
    reference = runtimes["normalized_ticket"]
    invariant_checks = {}
    for arm, runtime in runtimes.items():
        invariant_checks[arm] = {
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
            "same_dense_opportunities": (
                opportunity_skeleton(
                    runtime, "fixed_event_dense_opportunity_ledger"
                )
                == opportunity_skeleton(
                    reference, "fixed_event_dense_opportunity_ledger"
                )
            ),
            "same_keyframe_opportunities": (
                opportunity_skeleton(
                    runtime, "fixed_event_keyframe_opportunity_ledger"
                )
                == opportunity_skeleton(
                    reference, "fixed_event_keyframe_opportunity_ledger"
                )
            ),
            "zero_tail": runtime["post_eos_optimizer_updates"] == 0,
            "mapping_disjoint": (
                runtime["heldout_mapping_overlap_count"] == 0
                and runtime["heldout_gaussian_origin_overlap_count"] == 0
            ),
        }
    selector_checks = {
        "normalized_all_families": (
            reference["ercb_selection_potential_by_family"]
            == {
                "dense": "normalized_variance",
                "aux_kf": "normalized_variance",
                "native_kf": "normalized_variance",
            }
        ),
        "rr_all_families": (
            runtimes["rr_ticket"]["ercb_selection_potential_by_family"]
            == {"dense": "rr", "aux_kf": "rr", "native_kf": "rr"}
        ),
        "rr_native_queue_inactive_ercb": (
            runtimes["rr_ticket"][
                "stage6r_native_global_keyframe_selection_summary"
            ]["final_queue"].get("ercb_active")
            == 0
        ),
        "normalized_ticket_active": (
            reference["dense_topology_ticket"] is not None
            and reference["dense_topology_ticket"]["selected_mutations"] > 0
        ),
        "rr_ticket_active": (
            runtimes["rr_ticket"]["dense_topology_ticket"] is not None
            and runtimes["rr_ticket"]["dense_topology_ticket"][
                "selected_mutations"
            ]
            > 0
        ),
        "ticket_off_is_off": (
            runtimes["normalized_no_ticket"]["dense_topology_ticket"] is None
        ),
        "tickets_add_no_work": all(
            runtime["dense_topology_ticket"] is None
            or (
                runtime["dense_topology_ticket"]["extra_renders"] == 0
                and runtime["dense_topology_ticket"]["extra_adam_steps"] == 0
            )
            for runtime in runtimes.values()
        ),
    }
    traces = {
        "normalized_vs_rr_dense_different_rows": sum(
            left != right
            for left, right in zip(
                selected_trace(
                    reference,
                    "fixed_event_dense_opportunity_ledger",
                    "selected_keys",
                ),
                selected_trace(
                    runtimes["rr_ticket"],
                    "fixed_event_dense_opportunity_ledger",
                    "selected_keys",
                ),
            )
        ),
        "normalized_vs_rr_aux_kf_different_rows": sum(
            left != right
            for left, right in zip(
                selected_trace(
                    reference,
                    "fixed_event_keyframe_opportunity_ledger",
                    "selected_keys",
                ),
                selected_trace(
                    runtimes["rr_ticket"],
                    "fixed_event_keyframe_opportunity_ledger",
                    "selected_keys",
                ),
            )
        ),
        "normalized_vs_rr_native_kf_different_rows": sum(
            left != right
            for left, right in zip(
                selected_trace(
                    reference,
                    "stage6r_native_global_keyframe_selection_ledger",
                    "selected_uids",
                ),
                selected_trace(
                    runtimes["rr_ticket"],
                    "stage6r_native_global_keyframe_selection_ledger",
                    "selected_uids",
                ),
            )
        ),
    }
    report = {
        "protocol": "exp110_rr_ticket_ablation_verification_v1",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "invariant_checks": invariant_checks,
        "selector_checks": selector_checks,
        "selection_trace_differences": traces,
    }
    report["valid"] = all(
        value
        for checks in invariant_checks.values()
        for value in checks.values()
    ) and all(selector_checks.values())
    write_json(paths["verification"], report)
    return report


def evaluate(arm: str, row: dict, paths: dict[str, Path]) -> dict:
    return prior.prior.panel.run_evaluation_twice(
        paths[arm],
        row["dataset"],
        row["scene"],
        paths["fixed_manifest"],
    )


def run_one(row: dict) -> dict:
    paths = scene_paths(row)
    prior.prior.panel.v2.preflight(row, prior.prior.panel.scene_paths(row))
    check_source_lock()
    evaluations = {}
    for arm in ARMS:
        run_mapper(arm, row, paths)
        evaluations[arm] = evaluate(arm, row, paths)
    verification = verify(row, paths)
    if not verification["valid"]:
        raise RuntimeError(
            f"Exp110 structural stop: {row['dataset']}/{row['scene']}"
        )
    metrics = {
        arm: read_json(
            paths[arm] / "psnr/strict_fixed_manifest/final_result.json"
        )["predeclared_fixed_manifest_posthoc"]
        for arm in ARMS
    }
    runtimes = {
        arm: read_json(paths[arm] / "mapping_replay_runtime.json")
        for arm in ARMS
    }
    result = {
        "dataset": row["dataset"],
        "scene": row["scene"],
        "arms": {
            arm: {
                "psnr": float(metrics[arm]["mean_psnr"]),
                "ssim": float(metrics[arm]["mean_ssim"]),
                "lpips": float(metrics[arm]["mean_lpips"]),
                "renders": int(runtimes[arm]["rasterized_view_updates"]),
                "adam": int(runtimes[arm]["optimizer_steps_completed"]),
                "gaussians": int(runtimes[arm]["gaussians"]),
                "wall_seconds": float(runtimes[arm]["mapping_wall_seconds"]),
                "ticket_mutations": int(
                    (runtimes[arm]["dense_topology_ticket"] or {}).get(
                        "selected_mutations", 0
                    )
                ),
                "double_evaluation_pass": bool(evaluations[arm]["pass"]),
            }
            for arm in ARMS
        },
        "normalized_minus_rr_db": (
            float(metrics["normalized_ticket"]["mean_psnr"])
            - float(metrics["rr_ticket"]["mean_psnr"])
        ),
        "ticket_minus_off_db": (
            float(metrics["normalized_ticket"]["mean_psnr"])
            - float(metrics["normalized_no_ticket"]["mean_psnr"])
        ),
        "selection_trace_differences": verification[
            "selection_trace_differences"
        ],
        "valid": verification["valid"]
        and all(value["pass"] for value in evaluations.values()),
    }
    write_json(paths["result"], result)
    print(
        f"Exp110 {row['dataset']}/{row['scene']}: "
        f"normalized-RR={result['normalized_minus_rr_db']:+.6f}, "
        f"ticket-off={result['ticket_minus_off_db']:+.6f}",
        flush=True,
    )
    return result


def write_summary(rows: list[dict]) -> None:
    completed = []
    lines = [
        "# Exp110 — normalized ERCB / RR / ticket-off isolation",
        "",
        "All arms preserve R4 admission, birth, pruning, physical renders,",
        "Adam work, causal pool, growing no-repeat epochs, and transactional",
        "commit. RR sets the Gibbs energy to zero in all three selector",
        "families. The ticket-off arm changes only bounded dense-evidence clone",
        "service.",
        "",
        "| Scene | Normalized+ticket | RR+ticket | Norm. ticket-off | Norm-RR | Ticket-off | Clone N/RR/off | Dense/Aux/Native differing rows | Gate |",
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
        trace = item["selection_trace_differences"]
        lines.append(
            f"| {item['dataset']}/{item['scene']} | "
            f"{arms['normalized_ticket']['psnr']:.6f} | "
            f"{arms['rr_ticket']['psnr']:.6f} | "
            f"{arms['normalized_no_ticket']['psnr']:.6f} | "
            f"{item['normalized_minus_rr_db']:+.6f} | "
            f"{item['ticket_minus_off_db']:+.6f} | "
            f"{arms['normalized_ticket']['ticket_mutations']}/"
            f"{arms['rr_ticket']['ticket_mutations']}/0 | "
            f"{trace['normalized_vs_rr_dense_different_rows']}/"
            f"{trace['normalized_vs_rr_aux_kf_different_rows']}/"
            f"{trace['normalized_vs_rr_native_kf_different_rows']} | "
            f"{'PASS' if item['valid'] else 'FAIL'} |"
        )
    lines.extend(("", f"Completed scenes: **{len(completed)}/{len(rows)}**."))
    if len(completed) == len(rows):
        norm_rr = sum(x["normalized_minus_rr_db"] for x in completed) / len(rows)
        ticket = sum(x["ticket_minus_off_db"] for x in completed) / len(rows)
        lines.extend(
            (
                f"Mean normalized-RR: **{norm_rr:+.6f} dB**.",
                f"Mean ticket-off: **{ticket:+.6f} dB**.",
                "This pilot is mechanism isolation, not an all-scene method claim.",
            )
        )
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def selected_rows() -> list[dict]:
    inventory = prior.prior.panel.v2.install_inventory()
    wanted = {(dataset, scene) for dataset, scene, _ in SCENES}
    rows = [
        row for row in inventory
        if (row["dataset"], row["scene"]) in wanted
    ]
    if len(rows) != len(SCENES):
        raise RuntimeError("Exp110 scene inventory mismatch")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run-one", "run-all"))
    parser.add_argument("--scene")
    args = parser.parse_args()
    rows = selected_rows()
    prior.prior.exp94.check_evaluation_contract(rows)
    if args.action == "preflight":
        for row in rows:
            prior.prior.panel.v2.preflight(
                row, prior.prior.panel.scene_paths(row)
            )
        check_source_lock()
        print(f"Exp110 preflight PASS: {len(rows)} scenes x {len(ARMS)} arms")
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
