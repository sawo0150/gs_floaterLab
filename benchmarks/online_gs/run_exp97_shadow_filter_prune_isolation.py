#!/usr/bin/env python3
"""Exp97: corrected filter-prune isolation with a shadow controller count."""

from __future__ import annotations

import argparse
from pathlib import Path

import run_exp96_filter_prune_isolation as probe


probe.ROOT = (
    probe.base.WORKSPACE
    / "results/experiments/exp97_shadow_filter_prune_isolation"
)
probe.DOCS = (
    probe.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp97_shadow_filter_prune_isolation_20260924"
)
probe.SOURCE_PATHS = (*probe.SOURCE_PATHS, Path(__file__))


def make_gate(run: Path, fixed_manifest: Path) -> dict:
    gate = probe.make_gate(run, fixed_manifest)
    current = probe.read_json(run / "mapping_replay_runtime.json")
    control = probe.read_json(
        probe.CONTROL / "mapping_replay_runtime.json"
    )
    topology = current["mapping_replay_summary"]["topology_mutations"]
    lifetime = topology["lifetime"]["regular"]
    current_events = int(
        current["mapping_replay_summary"]["topology_events"]
    )
    control_events = int(
        control["mapping_replay_summary"]["topology_events"]
    )
    gate["protocol"] = "exp97_shadow_filter_prune_isolation_gate_v1"
    gate["checks"].update(
        {
            "same_final_generation_topology_events": (
                current_events == control_events
            ),
            "shadow_count_active": (
                int(lifetime.get("filter_prune_candidates", 0)) > 0
                and int(lifetime.get("filter_prune_withheld", 0))
                == int(lifetime.get("filter_prune_candidates", 0))
            ),
            "generation_telemetry_present": (
                isinstance(topology.get("completed_generations"), list)
                and int(topology.get("generation", -1)) >= 0
            ),
        }
    )
    gate["pass"] = (
        all(gate["checks"].values())
        and gate["control_drop_db"] <= probe.MAX_CONTROL_DROP_DB
    )
    gate["topology_event_count"] = {
        "candidate": current_events,
        "control": control_events,
    }
    probe.write_json(
        probe.ROOT / "rpng/table_01/isolation_gate.json",
        gate,
    )
    return gate


def write_summary(gate: dict, consistency: dict) -> None:
    vanilla_eval = probe.read_json(
        probe.VANILLA / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]
    candidate = gate["candidate_runtime"]
    topology = candidate["topology_mutations"]
    regular = topology["lifetime"]["regular"]
    completed = topology["completed_generations"]
    lines = [
        "# Exp97 — shadow-count regular filter-prune isolation",
        "",
        "This is a single-scene causal diagnosis, not a method or full-panel claim.",
        "The physical tensor retains ordinary opacity/size prune candidates, while",
        "the existing R4 phase controller receives the counterfactual count it would",
        "have observed after deleting them. Initialization, clone/split, split-parent",
        "replacement, ERCB, render work, and zero-tail remain unchanged.",
        "",
        "| Candidate | PSNR | vs Exp95 R4 | vs fresh vanilla | Renders | Adam | GS |",
        "|---|---:|---:|---:|---:|---:|---:|",
        (
            f"| shadow no-filter-prune | {gate['candidate_psnr']:.6f} | "
            f"{-gate['control_drop_db']:+.6f} | "
            f"{gate['candidate_psnr'] - vanilla_eval['mean_psnr']:+.6f} | "
            f"{candidate['physical_renders']:,} | {candidate['adam_steps']:,} | "
            f"{candidate['gaussians']:,} |"
        ),
        "",
        f"Double evaluation: **{'PASS' if consistency['pass'] else 'FAIL'}**.",
        f"Isolation gate: **{'PASS' if gate['pass'] else 'FAIL'}**.",
        (
            "Final-generation topology events candidate/control: "
            f"**{gate['topology_event_count']['candidate']}/"
            f"{gate['topology_event_count']['control']}**."
        ),
        (
            "Lifetime regular mutations: "
            f"added {int(regular.get('added', 0)):,}, "
            f"split-parent removed {int(regular.get('split_parent_pruned', 0)):,}, "
            f"filter candidates/physically removed/withheld "
            f"{int(regular.get('filter_prune_candidates', 0)):,}/"
            f"{int(regular.get('filter_pruned', 0)):,}/"
            f"{int(regular.get('filter_prune_withheld', 0)):,}."
        ),
        f"Completed mapper generations recorded: **{len(completed)}**.",
        "",
        "Any failed invariant or >0.5 dB loss stops the track before local births.",
    ]
    probe.DOCS.mkdir(parents=True, exist_ok=True)
    (probe.DOCS / "summary.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run"))
    args = parser.parse_args()
    row = probe.table01_row()
    probe.check_source_lock()
    if args.action == "preflight":
        print("Exp97 preflight PASS: rpng/table_01 shadow-count isolation")
        return 0
    run = probe.run_candidate(row)
    fixed_manifest = probe.base.sequence_paths(
        "rpng", "table_01"
    )["fixed_manifest"]
    consistency = probe.panel.run_evaluation_twice(
        run,
        "rpng",
        "table_01",
        fixed_manifest,
    )
    gate = make_gate(run, fixed_manifest)
    write_summary(gate, consistency)
    print(
        "Exp97 table_01: "
        f"PSNR={gate['candidate_psnr']:.6f}, "
        f"delta_control={-gate['control_drop_db']:+.6f}, "
        f"topology_events="
        f"{gate['topology_event_count']['candidate']}/"
        f"{gate['topology_event_count']['control']}, "
        f"gate={gate['pass']}",
        flush=True,
    )
    if not gate["pass"]:
        raise RuntimeError("Exp97 gate failed; stop before local-birth work")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
