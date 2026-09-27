#!/usr/bin/env python3
"""Exp96: isolate R4's ordinary regular filter-prune branch.

The scheduler, normalized ERCB selectors, physical render work, clone/split
growth, split-parent replacement, and independent KF caps stay enabled.  The
only candidate change is withholding the regular opacity/size filter prune.
Initialization densify/prune is deliberately unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import run_exp94_normalized_metric_v2_fixed_eval as exp94


panel = exp94.panel
v2 = panel.v2
base = exp94.base
ROOT = base.WORKSPACE / "results/experiments/exp96_filter_prune_isolation"
DOCS = (
    base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp96_filter_prune_isolation_20260924"
)
CONTROL = (
    base.WORKSPACE
    / "results/experiments/exp95_topology_churn_probe"
    / "rpng/table_01/normalized_variance_s0"
)
VANILLA = (
    base.WORKSPACE
    / "results/experiments/exp95_topology_churn_probe"
    / "rpng/table_01/native_vanilla_render_matched_s0"
)
SOURCE_PATHS = (
    base.CUSTOM_HARNESS,
    base.EVALUATOR,
    base.PAPER_ROOT / "demo.py",
    base.PAPER_ROOT / "vigs/gs_backend.py",
    base.PAPER_ROOT / "vigs/gaussian/scene/gaussian_model.py",
    base.PAPER_ROOT / "vigs/gaussian/utils/topology_telemetry.py",
    Path(__file__),
)
MAX_CONTROL_DROP_DB = 0.5


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
    path = ROOT / "source_lock.json"
    current = {str(source): sha256(source) for source in SOURCE_PATHS}
    if path.exists():
        if read_json(path)["sha256"] != current:
            raise RuntimeError("Exp96 source changed after start; use a new root")
        return
    write_json(
        path,
        {"protocol": "exp96_filter_prune_isolation_v1", "sha256": current},
    )


def table01_row() -> dict:
    rows = v2.install_inventory()
    matches = [
        row
        for row in rows
        if (row["dataset"], row["scene"]) == ("rpng", "table_01")
    ]
    if len(matches) != 1:
        raise RuntimeError("frozen inventory lost rpng/table_01")
    row = matches[0]
    v2.preflight(row, v2.scene_paths(row))
    exp94.check_evaluation_contract([row])
    return row


def run_candidate(row: dict) -> Path:
    run = ROOT / row["dataset"] / row["scene"] / "skip_regular_filter_prune_s0"
    runtime_path = run / "mapping_replay_runtime.json"
    if runtime_path.exists():
        return run
    if run.exists():
        raise FileExistsError(f"incomplete Exp96 output exists: {run}")
    v2.gpu_idle()
    command = base.mapping_command("candidate", "rpng", "table_01", ROOT)
    command[command.index("--output") + 1] = str(run)
    command.extend(
        (
            "--ercb-selection-potential",
            "normalized_variance",
            "--skip-regular-filter-prune",
        )
    )
    write_json(run / "mapping_command.json", command)
    v2.run_to_file(command, run / "mapping.log", custom=True)
    return run


def make_gate(run: Path, fixed_manifest: Path) -> dict:
    current = read_json(run / "mapping_replay_runtime.json")
    control = read_json(CONTROL / "mapping_replay_runtime.json")
    evaluation = read_json(
        run / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]
    control_eval = read_json(
        CONTROL / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]
    topology = current["mapping_replay_summary"]["topology_mutations"]
    lifetime_regular = topology["lifetime"]["regular"]
    checks = {
        "requested_skip": current.get(
            "skip_regular_filter_prune_requested"
        ) is True,
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
            v2.opportunity_skeleton(
                current, "fixed_event_dense_opportunity_ledger"
            )
            == v2.opportunity_skeleton(
                control, "fixed_event_dense_opportunity_ledger"
            )
        ),
        "same_keyframe_opportunities": (
            v2.opportunity_skeleton(
                current, "fixed_event_keyframe_opportunity_ledger"
            )
            == v2.opportunity_skeleton(
                control, "fixed_event_keyframe_opportunity_ledger"
            )
        ),
        "zero_tail": current["post_eos_optimizer_updates"] == 0,
        "mapping_disjoint": (
            current["heldout_mapping_overlap_count"] == 0
            and current["heldout_gaussian_origin_overlap_count"] == 0
        ),
        "regular_filter_prune_zero": (
            int(lifetime_regular.get("filter_pruned", 0)) == 0
        ),
        "clone_split_still_active": (
            int(lifetime_regular.get("added", 0)) > 0
            and int(lifetime_regular.get("split_parent_pruned", 0)) > 0
        ),
        "fixed_heldout": (
            evaluation["mapping_disjoint"]
            and evaluation["view_count"] == control_eval["view_count"]
            and sha256(fixed_manifest)
            == sha256(
                base.sequence_paths("rpng", "table_01")["fixed_manifest"]
            )
        ),
    }
    psnr = float(evaluation["mean_psnr"])
    control_psnr = float(control_eval["mean_psnr"])
    drop = control_psnr - psnr
    report = {
        "protocol": "exp96_filter_prune_isolation_gate_v1",
        "checks": checks,
        "pass": all(checks.values()) and drop <= MAX_CONTROL_DROP_DB,
        "candidate_psnr": psnr,
        "control_psnr": control_psnr,
        "control_drop_db": drop,
        "max_control_drop_db": MAX_CONTROL_DROP_DB,
        "candidate_runtime": {
            "physical_renders": current["rasterized_view_updates"],
            "adam_steps": current["optimizer_steps_completed"],
            "gaussians": current["gaussians"],
            "mapping_wall_seconds": current["mapping_wall_seconds"],
            "peak_cuda_allocated_bytes": current[
                "peak_cuda_allocated_bytes"
            ],
            "topology_mutations": topology,
        },
    }
    write_json(ROOT / "rpng/table_01/isolation_gate.json", report)
    return report


def write_summary(run: Path, gate: dict, consistency: dict) -> None:
    vanilla_eval = read_json(
        VANILLA / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]
    candidate = gate["candidate_runtime"]
    regular = candidate["topology_mutations"]["lifetime"]["regular"]
    lines = [
        "# Exp96 — regular filter-prune isolation",
        "",
        "This is a single-scene causal diagnosis, not a new method or a full-panel claim.",
        "Initialization topology, clone/split growth, split-parent replacement, ERCB,",
        "scheduler, and physical render work are unchanged; only ordinary regular",
        "opacity/size filter deletion is withheld.",
        "",
        "| Arm | PSNR | vs Exp95 R4 | vs fresh vanilla | Renders | Adam | GS |",
        "|---|---:|---:|---:|---:|---:|---:|",
        (
            f"| skip regular filter-prune | {gate['candidate_psnr']:.6f} | "
            f"{-gate['control_drop_db']:+.6f} | "
            f"{gate['candidate_psnr'] - vanilla_eval['mean_psnr']:+.6f} | "
            f"{candidate['physical_renders']:,} | {candidate['adam_steps']:,} | "
            f"{candidate['gaussians']:,} |"
        ),
        "",
        f"Double evaluation: **{'PASS' if consistency['pass'] else 'FAIL'}**. ",
        f"Isolation gate: **{'PASS' if gate['pass'] else 'FAIL'}**. ",
        f"Regular lifetime mutations: added {int(regular.get('added', 0)):,}, ",
        f"split-parent removed {int(regular.get('split_parent_pruned', 0)):,}, ",
        f"filter-pruned {int(regular.get('filter_pruned', 0)):,}. ",
        "",
        "A >0.5 dB drop from Exp95 stops further topology implementation.",
    ]
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run"))
    args = parser.parse_args()
    row = table01_row()
    check_source_lock()
    if args.action == "preflight":
        print("Exp96 preflight PASS: rpng/table_01 only")
        return 0
    run = run_candidate(row)
    fixed_manifest = base.sequence_paths("rpng", "table_01")["fixed_manifest"]
    consistency = panel.run_evaluation_twice(
        run,
        "rpng",
        "table_01",
        fixed_manifest,
    )
    gate = make_gate(run, fixed_manifest)
    write_summary(run, gate, consistency)
    print(
        "Exp96 table_01: "
        f"PSNR={gate['candidate_psnr']:.6f}, "
        f"delta_control={-gate['control_drop_db']:+.6f}, "
        f"gate={gate['pass']}",
        flush=True,
    )
    if not gate["pass"]:
        raise RuntimeError("Exp96 gate failed; stop before local-birth work")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
