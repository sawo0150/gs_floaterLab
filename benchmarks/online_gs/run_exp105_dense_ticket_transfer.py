#!/usr/bin/env python3
"""Exp105: no-retuning transfer of Exp104 with fresh paired vanilla runs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp94_normalized_metric_v2_fixed_eval as exp94


panel = exp94.panel
base = exp94.base
ROOT = base.WORKSPACE / "results/experiments/exp105_dense_ticket_transfer"
DOCS = (
    base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp105_dense_ticket_transfer_20260924"
)
MAX_R4_DROP_DB = 0.5
SOURCE_PATHS = (
    *panel.SOURCE_PATHS,
    base.CUSTOM_HARNESS,
    Path(__file__).with_name("dense_topology_ticket.py"),
    base.PAPER_ROOT / "vigs/gaussian/scene/gaussian_model.py",
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_source_lock() -> None:
    current = {str(path): sha256(path) for path in SOURCE_PATHS}
    path = ROOT / "source_lock.json"
    if path.exists():
        if read_json(path)["sha256"] != current:
            raise RuntimeError("Exp105 source changed after start; use a new root")
        return
    write_json(
        path,
        {
            "protocol": "exp105_dense_ticket_transfer_v1",
            "vigs_commit": "913b9da2",
            "lab_commit": "9cd0402",
            "no_scene_retuning": True,
            "sha256": current,
        },
    )


def paths(row: dict) -> dict[str, Path]:
    dataset, scene = row["dataset"], row["scene"]
    historical = panel.scene_paths(row)
    local = ROOT / dataset / scene
    return {
        **base.sequence_paths(dataset, scene),
        "candidate": local / "dense_ticket_s0",
        "vanilla": local / "native_vanilla_render_matched_s0",
        "historical_r4": historical["candidate"],
        "pair": local / "pair_verification.json",
        "gate": local / "quality_gate.json",
        "result": local / "pair_result.json",
    }


def run_mapper(arm: str, row: dict, scene_paths: dict[str, Path]) -> None:
    run = scene_paths[arm]
    if (run / "mapping_replay_runtime.json").exists():
        return
    if run.exists():
        raise FileExistsError(f"incomplete output exists: {run}")
    panel.v2.gpu_idle()
    command = base.mapping_command(
        "candidate" if arm == "candidate" else "vanilla",
        row["dataset"],
        row["scene"],
        ROOT,
    )
    command[command.index("--output") + 1] = str(run)
    if arm == "candidate":
        command.extend(
            (
                "--ercb-selection-potential",
                "normalized_variance",
                "--dense-topology-ticket",
            )
        )
    else:
        command[command.index("--reference-service-runtime") + 1] = str(
            scene_paths["candidate"] / "mapping_replay_runtime.json"
        )
    write_json(run / "mapping_command.json", command)
    panel.v2.run_to_file(
        command, run / "mapping.log", custom=(arm == "candidate")
    )


def gate(row: dict, scene_paths: dict[str, Path]) -> dict:
    run = scene_paths["candidate"]
    current = read_json(run / "mapping_replay_runtime.json")
    control = read_json(
        scene_paths["historical_r4"] / "mapping_replay_runtime.json"
    )
    result = read_json(
        run / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]
    control_result = read_json(
        scene_paths["historical_r4"]
        / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]
    ticket = current["dense_topology_ticket"]
    checks = {
        "ticket_active_or_evidence_absent": (
            ticket["enabled"] is True
            and int(ticket["selected_mutations"]) >= 0
        ),
        "no_extra_render_or_adam": (
            int(ticket["extra_renders"]) == 0
            and int(ticket["extra_adam_steps"]) == 0
        ),
        "one_observation_per_dense_opportunity": (
            int(ticket["dense_observations"])
            == len(current["fixed_event_dense_opportunity_ledger"])
        ),
        "normalized_selector": (
            current.get("ercb_selection_potential") == "normalized_variance"
        ),
        "same_archive": (
            current["archive_manifest_sha256"]
            == control["archive_manifest_sha256"]
        ),
        "same_config": (
            current["effective_config_sha256"]
            == control["effective_config_sha256"]
        ),
        "same_events": (
            current["event_ids_fully_processed"]
            == control["event_ids_fully_processed"]
        ),
        "same_render_work": (
            current["rasterized_view_updates"]
            == control["rasterized_view_updates"]
        ),
        "same_adam_work": (
            current["optimizer_steps_completed"]
            == control["optimizer_steps_completed"]
        ),
        "same_dense_admission": (
            current["dense_registered_frame_uids"]
            == control["dense_registered_frame_uids"]
        ),
        "same_dense_opportunities": (
            panel.v2.opportunity_skeleton(
                current, "fixed_event_dense_opportunity_ledger"
            )
            == panel.v2.opportunity_skeleton(
                control, "fixed_event_dense_opportunity_ledger"
            )
        ),
        "same_keyframe_opportunities": (
            panel.v2.opportunity_skeleton(
                current, "fixed_event_keyframe_opportunity_ledger"
            )
            == panel.v2.opportunity_skeleton(
                control, "fixed_event_keyframe_opportunity_ledger"
            )
        ),
        "same_final_topology_event_count": (
            current["mapping_replay_summary"]["topology_events"]
            == control["mapping_replay_summary"]["topology_events"]
        ),
        "zero_tail": current["post_eos_optimizer_updates"] == 0,
        "mapping_disjoint": (
            current["heldout_mapping_overlap_count"] == 0
            and current["heldout_gaussian_origin_overlap_count"] == 0
            and result["mapping_disjoint"]
        ),
    }
    psnr = float(result["mean_psnr"])
    control_psnr = float(control_result["mean_psnr"])
    report = {
        "protocol": "exp105_dense_ticket_transfer_gate_v1",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "checks": checks,
        "candidate_psnr": psnr,
        "historical_r4_psnr": control_psnr,
        "candidate_minus_r4_db": psnr - control_psnr,
        "stop": (
            not all(checks.values())
            or control_psnr - psnr > MAX_R4_DROP_DB
        ),
        "ticket": ticket,
    }
    write_json(scene_paths["gate"], report)
    return report


def run_one(row: dict) -> dict:
    scene_paths = paths(row)
    panel.v2.preflight(row, panel.scene_paths(row))
    check_source_lock()
    run_mapper("candidate", row, scene_paths)
    candidate_eval = panel.run_evaluation_twice(
        scene_paths["candidate"],
        row["dataset"],
        row["scene"],
        scene_paths["fixed_manifest"],
    )
    quality = gate(row, scene_paths)
    if quality["stop"]:
        raise RuntimeError(
            f"Exp105 stop at {row['dataset']}/{row['scene']}: "
            f"{quality['candidate_minus_r4_db']:+.4f} dB vs R4"
        )
    run_mapper("vanilla", row, scene_paths)
    vanilla_eval = panel.run_evaluation_twice(
        scene_paths["vanilla"],
        row["dataset"],
        row["scene"],
        scene_paths["fixed_manifest"],
    )
    if not scene_paths["pair"].exists():
        subprocess.run(
            [
                str(base.PYTHON_ENV / "bin/python"),
                str(base.RENDER_VERIFIER),
                "--d1-run",
                str(scene_paths["candidate"]),
                "--vanilla-run",
                str(scene_paths["vanilla"]),
                "--output",
                str(scene_paths["pair"]),
            ],
            cwd=base.WORKSPACE,
            check=True,
            stdout=subprocess.DEVNULL,
        )
    pair = read_json(scene_paths["pair"])
    if not pair.get("valid"):
        raise RuntimeError("fresh candidate/vanilla pair verification failed")
    result = {
        "dataset": row["dataset"],
        "scene": row["scene"],
        "candidate_psnr": pair["result"]["d1"]["psnr"],
        "vanilla_psnr": pair["result"]["vanilla"]["psnr"],
        "candidate_minus_vanilla_db": pair["result"]["d1_minus_vanilla"]["psnr"],
        "candidate_minus_r4_db": quality["candidate_minus_r4_db"],
        "selected_mutations": quality["ticket"]["selected_mutations"],
        "candidate_renders": pair["result"]["d1"]["renders"],
        "vanilla_renders": pair["result"]["vanilla"]["renders"],
        "candidate_adam": pair["result"]["d1"]["optimizer_steps"],
        "vanilla_adam": pair["result"]["vanilla"]["optimizer_steps"],
        "candidate_gaussians": pair["result"]["d1"]["gaussians"],
        "vanilla_gaussians": pair["result"]["vanilla"]["gaussians"],
        "double_evaluation_pass": (
            candidate_eval["pass"] and vanilla_eval["pass"]
        ),
        "fairness_pass": pair["valid"],
    }
    write_json(scene_paths["result"], result)
    print(
        f"{row['dataset']}/{row['scene']}: "
        f"ticket−R4={result['candidate_minus_r4_db']:+.4f}, "
        f"ticket−fresh-vanilla={result['candidate_minus_vanilla_db']:+.4f}, "
        f"mutations={result['selected_mutations']}",
        flush=True,
    )
    return result


def write_summary(rows: list[dict]) -> None:
    completed = []
    lines = [
        "# Exp105 — dense topology ticket no-retuning transfer",
        "",
        "Exp104's top-1,024, two-distinct-dense-UID, matched-regular-addition",
        "ticket is frozen for every scene. Every completed row uses a fresh",
        "candidate and fresh render-matched vanilla pair with double evaluation.",
        "",
        "| Dataset | Scene | Ticket | Fresh vanilla | Δ vanilla | Δ Exp94 R4 | Mutations | Renders T/V | Adam T/V | GS T/V | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        path = ROOT / row["dataset"] / row["scene"] / "pair_result.json"
        if not path.exists():
            continue
        item = read_json(path)
        completed.append(item)
        passed = item["double_evaluation_pass"] and item["fairness_pass"]
        lines.append(
            f"| {item['dataset']} | {item['scene']} | "
            f"{item['candidate_psnr']:.4f} | {item['vanilla_psnr']:.4f} | "
            f"{item['candidate_minus_vanilla_db']:+.4f} | "
            f"{item['candidate_minus_r4_db']:+.4f} | "
            f"{item['selected_mutations']:,} | "
            f"{item['candidate_renders']}/{item['vanilla_renders']} | "
            f"{item['candidate_adam']}/{item['vanilla_adam']} | "
            f"{item['candidate_gaussians']}/{item['vanilla_gaussians']} | "
            f"{'PASS' if passed else 'FAIL'} |"
        )
    lines.extend(
        (
            "",
            f"Completed transfer pairs: **{len(completed)}/17**.",
            "No all-scene claim is made until all 17 fresh pairs complete.",
        )
    )
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run-one"))
    parser.add_argument("--dataset", choices=("rpng", "utmm", "aria"))
    parser.add_argument("--scene")
    args = parser.parse_args()
    rows = panel.v2.install_inventory()
    exp94.check_evaluation_contract(rows)
    check_source_lock()
    if args.action == "preflight":
        print("Exp105 preflight PASS: 17-scene no-retuning inventory")
        return 0
    match = [
        row for row in rows
        if row["dataset"] == args.dataset and row["scene"] == args.scene
    ]
    if len(match) != 1:
        raise ValueError("run-one requires one valid --dataset/--scene")
    run_one(match[0])
    write_summary(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
