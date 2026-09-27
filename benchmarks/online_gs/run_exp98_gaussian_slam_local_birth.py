#!/usr/bin/env python3
"""Exp98: bounded current-view birth ported from official Gaussian-SLAM."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import run_exp96_filter_prune_isolation as common


ROOT = common.base.WORKSPACE / "results/experiments/exp98_gaussian_slam_local_birth"
DOCS = (
    common.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp98_gaussian_slam_local_birth_20260924"
)
CONTROL = common.CONTROL
VANILLA = common.VANILLA
TICKET = 1024
RADIUS_M = 0.01
MAX_CONTROL_DROP_DB = 0.5
SOURCE_PATHS = (
    common.base.CUSTOM_HARNESS,
    common.base.EVALUATOR,
    common.base.PAPER_ROOT / "demo.py",
    common.base.PAPER_ROOT / "vigs/gs_backend.py",
    common.base.PAPER_ROOT / "vigs/gaussian/scene/gaussian_model.py",
    common.base.PAPER_ROOT / "vigs/gaussian/utils/local_birth.py",
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
    lock = ROOT / "source_lock.json"
    current = {str(path): sha256(path) for path in SOURCE_PATHS}
    if lock.exists():
        if read_json(lock)["sha256"] != current:
            raise RuntimeError("Exp98 source changed after start; use a new root")
        return
    write_json(
        lock,
        {
            "protocol": "exp98_gaussian_slam_local_birth_v1",
            "reference": {
                "repository": "https://github.com/VladimirYugay/Gaussian-SLAM",
                "commit": "eaec10d73ce7511563882b8856896e06d1f804e3",
                "license": "MIT",
            },
            "sha256": current,
        },
    )


def table01_row() -> dict:
    rows = common.v2.install_inventory()
    row = next(
        row
        for row in rows
        if (row["dataset"], row["scene"]) == ("rpng", "table_01")
    )
    common.v2.preflight(row, common.v2.scene_paths(row))
    common.exp94.check_evaluation_contract([row])
    return row


def run_candidate() -> Path:
    run = ROOT / "rpng/table_01/local_birth_s0"
    if (run / "mapping_replay_runtime.json").exists():
        return run
    if run.exists():
        raise FileExistsError(f"incomplete Exp98 output exists: {run}")
    common.v2.gpu_idle()
    command = common.base.mapping_command("candidate", "rpng", "table_01", ROOT)
    command[command.index("--output") + 1] = str(run)
    command.extend(
        (
            "--ercb-selection-potential",
            "normalized_variance",
            "--local-birth",
            "--local-birth-ticket",
            str(TICKET),
            "--local-birth-radius",
            str(RADIUS_M),
        )
    )
    write_json(run / "mapping_command.json", command)
    common.v2.run_to_file(command, run / "mapping.log", custom=True)
    return run


def gate(run: Path) -> dict:
    current = read_json(run / "mapping_replay_runtime.json")
    control = read_json(CONTROL / "mapping_replay_runtime.json")
    result = read_json(
        run / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]
    control_result = read_json(
        CONTROL / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]
    birth = current["mapping_replay_summary"]["local_birth"]
    current_topology = int(
        current["mapping_replay_summary"]["topology_events"]
    )
    control_topology = int(
        control["mapping_replay_summary"]["topology_events"]
    )
    checks = {
        "local_birth_requested": current.get("local_birth_requested") is True,
        "local_birth_enabled": birth.get("enabled") is True,
        "local_birth_executed": int(birth.get("events", 0)) > 0,
        "bounded_ticket": (
            int(birth.get("accepted", 0))
            <= TICKET * int(birth.get("events", 0))
        ),
        "normalized_selector": (
            current.get("ercb_selection_potential") == "normalized_variance"
        ),
        "same_archive": (
            current["archive_manifest_sha256"]
            == control["archive_manifest_sha256"]
        ),
        "same_effective_config": (
            current["effective_config_sha256"]
            == control["effective_config_sha256"]
        ),
        "same_events": (
            current["event_ids_fully_processed"]
            == control["event_ids_fully_processed"]
        ),
        "same_physical_renders": (
            current["rasterized_view_updates"]
            == control["rasterized_view_updates"]
        ),
        "same_adam_steps": (
            current["optimizer_steps_completed"]
            == control["optimizer_steps_completed"]
        ),
        "same_dense_admission": (
            current["dense_registered_frame_uids"]
            == control["dense_registered_frame_uids"]
        ),
        "same_dense_opportunities": (
            common.v2.opportunity_skeleton(
                current, "fixed_event_dense_opportunity_ledger"
            )
            == common.v2.opportunity_skeleton(
                control, "fixed_event_dense_opportunity_ledger"
            )
        ),
        "same_keyframe_opportunities": (
            common.v2.opportunity_skeleton(
                current, "fixed_event_keyframe_opportunity_ledger"
            )
            == common.v2.opportunity_skeleton(
                control, "fixed_event_keyframe_opportunity_ledger"
            )
        ),
        "same_topology_event_count": current_topology == control_topology,
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
        "protocol": "exp98_gaussian_slam_local_birth_gate_v1",
        "checks": checks,
        "candidate_psnr": psnr,
        "control_psnr": control_psnr,
        "candidate_minus_control_db": psnr - control_psnr,
        "max_control_drop_db": MAX_CONTROL_DROP_DB,
        "pass": (
            all(checks.values())
            and control_psnr - psnr <= MAX_CONTROL_DROP_DB
        ),
        "local_birth": birth,
        "topology_events": {
            "candidate": current_topology,
            "control": control_topology,
        },
        "runtime": {
            "physical_renders": current["rasterized_view_updates"],
            "adam_steps": current["optimizer_steps_completed"],
            "gaussians": current["gaussians"],
            "mapping_wall_seconds": current["mapping_wall_seconds"],
            "peak_cuda_allocated_bytes": current["peak_cuda_allocated_bytes"],
            "peak_cuda_reserved_bytes": current["peak_cuda_reserved_bytes"],
        },
    }
    write_json(ROOT / "rpng/table_01/local_birth_gate.json", report)
    return report


def write_summary(report: dict, consistency: dict) -> None:
    vanilla = read_json(
        VANILLA / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]["mean_psnr"]
    birth = report["local_birth"]
    runtime = report["runtime"]
    lines = [
        "# Exp98 — Gaussian-SLAM current-view local birth",
        "",
        "Official-code basis: Gaussian-SLAM commit",
        "`eaec10d73ce7511563882b8856896e06d1f804e3` (MIT). The operator",
        "uses low rendered alpha OR large positive depth residual, a 1,024-row",
        "per-keyframe ticket, current-frustum 1 cm duplicate rejection, and VIGS's",
        "causal online depth/pose. Initial map birth and the R4 scheduler/pruner are",
        "unchanged.",
        "",
        f"Candidate PSNR: **{report['candidate_psnr']:.6f} dB**.",
        f"Candidate−Exp95 R4: **{report['candidate_minus_control_db']:+.6f} dB**.",
        f"Candidate−fresh vanilla: **{report['candidate_psnr'] - vanilla:+.6f} dB**.",
        f"Double evaluation: **{'PASS' if consistency['pass'] else 'FAIL'}**.",
        f"Gate: **{'PASS' if report['pass'] else 'FAIL'}**.",
        "",
        (
            "Birth events/eligible/ticketed/accepted/duplicate-rejected: "
            f"{int(birth.get('events', 0)):,}/"
            f"{int(birth.get('eligible_union', 0)):,}/"
            f"{int(birth.get('offered_after_ticket', 0)):,}/"
            f"{int(birth.get('accepted', 0)):,}/"
            f"{int(birth.get('duplicate_rejected', 0)):,}."
        ),
        (
            "Topology events candidate/control: "
            f"{report['topology_events']['candidate']}/"
            f"{report['topology_events']['control']}."
        ),
        (
            f"Work: {runtime['physical_renders']:,} renders, "
            f"{runtime['adam_steps']:,} Adam, {runtime['gaussians']:,} GS, "
            f"{runtime['mapping_wall_seconds']:.2f} s."
        ),
        "",
        "This one-scene result decides only whether the port survives the R4 quality",
        "and structural gate. It is not yet a dense/ERCB topology contribution.",
    ]
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run"))
    args = parser.parse_args()
    table01_row()
    check_source_lock()
    if args.action == "preflight":
        print("Exp98 preflight PASS: Gaussian-SLAM local birth table_01")
        return 0
    run = run_candidate()
    fixed = common.base.sequence_paths("rpng", "table_01")["fixed_manifest"]
    consistency = common.panel.run_evaluation_twice(
        run, "rpng", "table_01", fixed
    )
    report = gate(run)
    write_summary(report, consistency)
    print(
        "Exp98 table_01: "
        f"PSNR={report['candidate_psnr']:.6f}, "
        f"delta_control={report['candidate_minus_control_db']:+.6f}, "
        f"gate={report['pass']}",
        flush=True,
    )
    if not report["pass"]:
        raise RuntimeError("Exp98 gate failed; stop before dense coupling")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
