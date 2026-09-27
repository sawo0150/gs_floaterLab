#!/usr/bin/env python3
"""Exp104: active generation-scoped dense/ERCB bounded topology ticket."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import run_exp102_dense_topology_evidence_probe as base


ROOT = (
    base.prior.common.base.WORKSPACE
    / "results/experiments/exp104_dense_topology_ticket"
)
DOCS = (
    base.prior.common.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp104_dense_topology_ticket_20260924"
)
RUN = ROOT / "rpng/table_01/matched_regular_ticket_s0"
CONTROL = base.CONTROL
VANILLA = base.VANILLA
MAX_CONTROL_DROP_DB = 0.5
SOURCE_PATHS = (
    *base.SOURCE_PATHS,
    Path(__file__).with_name("dense_topology_ticket.py"),
    Path(
        "/home/intern/VIGS-SLAM-paper-full/vigs/gaussian/scene/"
        "gaussian_model.py"
    ),
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


def source_lock() -> None:
    current = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in SOURCE_PATHS
    }
    path = ROOT / "source_lock.json"
    if path.exists():
        if read_json(path)["sha256"] != current:
            raise RuntimeError("Exp104 source changed after start; use a new root")
        return
    write_json(
        path,
        {
            "protocol": "exp104_dense_topology_ticket_v1",
            "vigs_commit": "913b9da2",
            "implementation_references": [
                {
                    "repository": "https://github.com/humansensinglab/taming-3dgs",
                    "commit": "fd0f7d9edfe135eb4eefd3be82ee56dada7f2a16",
                    "ported_operator": "weighted multinomial without replacement",
                },
                {
                    "repository": "https://github.com/hugoycj/TileGS",
                    "commit": "7f109a403ed522ba5ec7610f3d4778c363b68b11",
                    "adapted_concept": "persistent per-Gaussian evidence",
                },
            ],
            "sha256": current,
        },
    )


def run_candidate() -> Path:
    if (RUN / "mapping_replay_runtime.json").exists():
        return RUN
    if RUN.exists():
        raise FileExistsError(f"incomplete Exp104 output exists: {RUN}")
    base.prior.common.v2.gpu_idle()
    command = base.prior.common.base.mapping_command(
        "candidate", "rpng", "table_01", ROOT
    )
    command[command.index("--output") + 1] = str(RUN)
    command.extend(
        (
            "--ercb-selection-potential",
            "normalized_variance",
            "--dense-topology-ticket",
        )
    )
    write_json(RUN / "mapping_command.json", command)
    base.prior.common.v2.run_to_file(
        command, RUN / "mapping.log", custom=True
    )
    return RUN


def gate(run: Path) -> dict:
    current = read_json(run / "mapping_replay_runtime.json")
    control = read_json(CONTROL / "mapping_replay_runtime.json")
    result = read_json(
        run / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]
    control_result = read_json(
        CONTROL / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]
    ticket = current["dense_topology_ticket"]
    lifetime_events = int(
        current["mapping_replay_summary"]["topology_mutations"]
        ["lifetime"]["regular"]["events"]
    )
    event_accounting = all(
        int(row["selected_without_replacement"])
        <= int(row["regular_added_ticket"])
        for row in ticket["events"]
    )
    checks = {
        "ticket_requested_and_enabled": (
            current.get("dense_topology_ticket_requested") is True
            and ticket.get("enabled") is True
        ),
        "author_operator_active": (
            ticket.get("weighted_without_replacement") is True
            and int(ticket.get("selected_mutations", 0)) > 0
        ),
        "matched_regular_ticket": (
            ticket.get("budget_mode") == "match_regular_additions"
            and event_accounting
        ),
        "one_observation_per_dense_opportunity": (
            int(ticket["dense_observations"])
            == len(current["fixed_event_dense_opportunity_ledger"])
        ),
        "one_ticket_per_lifetime_topology_event": (
            int(ticket["topology_events"]) == lifetime_events
        ),
        "no_extra_render_or_adam": (
            int(ticket["extra_renders"]) == 0
            and int(ticket["extra_adam_steps"]) == 0
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
            base.prior.common.v2.opportunity_skeleton(
                current, "fixed_event_dense_opportunity_ledger"
            )
            == base.prior.common.v2.opportunity_skeleton(
                control, "fixed_event_dense_opportunity_ledger"
            )
        ),
        "same_keyframe_opportunities": (
            base.prior.common.v2.opportunity_skeleton(
                current, "fixed_event_keyframe_opportunity_ledger"
            )
            == base.prior.common.v2.opportunity_skeleton(
                control, "fixed_event_keyframe_opportunity_ledger"
            )
        ),
        "same_final_generation_topology_event_count": (
            int(current["mapping_replay_summary"]["topology_events"])
            == int(control["mapping_replay_summary"]["topology_events"])
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
        "protocol": "exp104_dense_topology_ticket_gate_v1",
        "checks": checks,
        "candidate_psnr": psnr,
        "control_psnr": control_psnr,
        "candidate_minus_control_db": psnr - control_psnr,
        "max_control_drop_db": MAX_CONTROL_DROP_DB,
        "pass": (
            all(checks.values())
            and control_psnr - psnr <= MAX_CONTROL_DROP_DB
        ),
        "ticket": ticket,
        "runtime": {
            "physical_renders": current["rasterized_view_updates"],
            "adam_steps": current["optimizer_steps_completed"],
            "gaussians": current["gaussians"],
            "mapping_wall_seconds": current["mapping_wall_seconds"],
            "peak_cuda_allocated_bytes": current[
                "peak_cuda_allocated_bytes"
            ],
            "peak_cuda_reserved_bytes": current[
                "peak_cuda_reserved_bytes"
            ],
        },
    }
    write_json(ROOT / "rpng/table_01/ticket_gate.json", report)
    return report


def write_summary(report: dict, consistency: dict) -> None:
    vanilla = read_json(
        VANILLA / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]["mean_psnr"]
    ticket = report["ticket"]
    runtime = report["runtime"]
    lines = [
        "# Exp104 — active dense/ERCB bounded topology ticket",
        "",
        "The normalized-ERCB dense backward nominates the top-1,024 `f_dc`",
        "gradient rows. A parent must be nominated by at least two distinct",
        "dense UIDs in the current map generation. At each existing native",
        "topology event, its ticket equals that event's regular clone+split",
        "additions. Taming 3DGS's weighted multinomial sampling without",
        "replacement selects small-Gaussian parents. R4 birth/prune/cadence",
        "remain active; dense RGB supplies no depth and adds no render/Adam.",
        "",
        f"Candidate PSNR: **{report['candidate_psnr']:.6f} dB**.",
        (
            "Candidate−Exp95 normalized R4: "
            f"**{report['candidate_minus_control_db']:+.6f} dB**."
        ),
        (
            "Candidate−fresh vanilla: "
            f"**{report['candidate_psnr'] - vanilla:+.6f} dB**."
        ),
        f"Double evaluation: **{'PASS' if consistency['pass'] else 'FAIL'}**.",
        f"Structural/quality gate: **{'PASS' if report['pass'] else 'FAIL'}**.",
        "",
        (
            "Dense observations/topology tickets/requested/selected: "
            f"{ticket['dense_observations']}/"
            f"{ticket['topology_events']}/"
            f"{ticket['requested_mutations']:,}/"
            f"{ticket['selected_mutations']:,}."
        ),
        (
            "Final-generation nominated/repeated/consumed parents: "
            f"{ticket['current_generation_nominated_points']:,}/"
            f"{ticket['current_generation_repeated_points']:,}/"
            f"{ticket['consumed_parent_ids']:,}."
        ),
        (
            f"Work: {runtime['physical_renders']:,} renders, "
            f"{runtime['adam_steps']:,} Adam, {runtime['gaussians']:,} GS, "
            f"{runtime['mapping_wall_seconds']:.2f} s."
        ),
        "",
        "| Gen | Regular-add ticket | Repeated candidates | Small eligible | Selected |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in ticket["events"]:
        lines.append(
            f"| {row['map_generation']} | "
            f"{row['regular_added_ticket']:,} | "
            f"{row['persistent_candidates_before_scale_filter']:,} | "
            f"{row['small_scale_eligible']:,} | "
            f"{row['selected_without_replacement']:,} |"
        )
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run"))
    args = parser.parse_args()
    base.prior.table01_row()
    source_lock()
    if args.action == "preflight":
        print("Exp104 preflight PASS: dense topology ticket")
        return 0
    run = run_candidate()
    fixed = base.prior.common.base.sequence_paths(
        "rpng", "table_01"
    )["fixed_manifest"]
    consistency = base.prior.common.panel.run_evaluation_twice(
        run, "rpng", "table_01", fixed
    )
    report = gate(run)
    write_summary(report, consistency)
    print(
        "Exp104 table_01: "
        f"PSNR={report['candidate_psnr']:.6f}, "
        f"delta_control={report['candidate_minus_control_db']:+.6f}, "
        f"selected={report['ticket']['selected_mutations']}, "
        f"gate={report['pass']}",
        flush=True,
    )
    if not report["pass"]:
        raise RuntimeError("Exp104 gate failed; stop before transfer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
