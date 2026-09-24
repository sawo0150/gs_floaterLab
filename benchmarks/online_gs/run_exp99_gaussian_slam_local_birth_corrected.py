#!/usr/bin/env python3
"""Exp99: corrected official-code local birth after lineage-cap isolation."""

from __future__ import annotations

import argparse
from pathlib import Path

import run_exp98_gaussian_slam_local_birth as prior


ROOT = (
    prior.common.base.WORKSPACE
    / "results/experiments/exp99_gaussian_slam_local_birth_corrected"
)
DOCS = (
    prior.common.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp99_gaussian_slam_local_birth_corrected_20260924"
)
SOURCE_PATHS = (*prior.SOURCE_PATHS, Path(__file__))

# Reuse the source-locked command and contract machinery without touching the
# stopped Exp98 output. The imported functions resolve these module globals at
# call time.
prior.ROOT = ROOT
prior.DOCS = DOCS


def check_source_lock() -> None:
    lock = ROOT / "source_lock.json"
    current = {str(path): prior.sha256(path) for path in SOURCE_PATHS}
    if lock.exists():
        if prior.read_json(lock)["sha256"] != current:
            raise RuntimeError("Exp99 source changed after start; use a new root")
        return
    prior.write_json(
        lock,
        {
            "protocol": "exp99_gaussian_slam_local_birth_corrected_v1",
            "implementation_reference": {
                "repository": "https://github.com/VladimirYugay/Gaussian-SLAM",
                "commit": "eaec10d73ce7511563882b8856896e06d1f804e3",
                "license": "MIT",
            },
            "vigs_commit": "d00e2263",
            "sha256": current,
        },
    )


def gate(run: Path) -> dict:
    report = prior.gate(run)
    current = prior.read_json(run / "mapping_replay_runtime.json")
    topology = current["mapping_replay_summary"]["topology_mutations"]
    regular = topology.get("lifetime", {}).get(
        "regular", topology.get("regular", {})
    )
    report["protocol"] = "exp99_gaussian_slam_local_birth_corrected_gate_v1"
    report["vigs_commit"] = "d00e2263"
    report["topology_regular"] = regular
    report["cap_diagnostic"] = {
        "cap_pruned": int(regular.get("cap_pruned", 0)),
        "birth_accepted": int(report["local_birth"].get("accepted", 0)),
        "note": (
            "Diagnostic only: cap pruning can include descendants created by "
            "regular densification, so it is not equated one-to-one with births."
        ),
    }
    report["pass"] = (
        all(report["checks"].values())
        and report["control_psnr"] - report["candidate_psnr"]
        <= prior.MAX_CONTROL_DROP_DB
    )
    prior.write_json(ROOT / "rpng/table_01/local_birth_gate.json", report)
    return report


def write_summary(report: dict, consistency: dict) -> None:
    vanilla = prior.read_json(
        prior.VANILLA / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]["mean_psnr"]
    birth = report["local_birth"]
    runtime = report["runtime"]
    cap = report["cap_diagnostic"]
    lines = [
        "# Exp99 — corrected official Gaussian-SLAM local birth",
        "",
        "Implementation basis: Gaussian-SLAM author repository commit",
        "`eaec10d73ce7511563882b8856896e06d1f804e3` (MIT). VIGS source",
        "is `d00e2263`: lineage cap registration now follows the final explicit",
        "birth ticket; the no-ticket R4 path retains its historical arithmetic.",
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
            f"Topology cap diagnostic: {cap['cap_pruned']:,} rows removed; "
            f"{cap['birth_accepted']:,} local births accepted over the run."
        ),
        (
            f"Work: {runtime['physical_renders']:,} renders, "
            f"{runtime['adam_steps']:,} Adam, {runtime['gaussians']:,} GS, "
            f"{runtime['mapping_wall_seconds']:.2f} s."
        ),
        "",
        "This is a one-scene method gate, not a full-panel result and not yet a",
        "dense/ERCB topology contribution. A loss greater than 0.5 dB versus the",
        "Exp95 control stops the track before any dense-topology coupling work.",
    ]
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run"))
    args = parser.parse_args()
    prior.table01_row()
    check_source_lock()
    if args.action == "preflight":
        print("Exp99 preflight PASS: corrected official-code local birth")
        return 0
    run = prior.run_candidate()
    fixed = prior.common.base.sequence_paths(
        "rpng", "table_01"
    )["fixed_manifest"]
    consistency = prior.common.panel.run_evaluation_twice(
        run, "rpng", "table_01", fixed
    )
    report = gate(run)
    write_summary(report, consistency)
    print(
        "Exp99 table_01: "
        f"PSNR={report['candidate_psnr']:.6f}, "
        f"delta_control={report['candidate_minus_control_db']:+.6f}, "
        f"gate={report['pass']}",
        flush=True,
    )
    if not report["pass"]:
        raise RuntimeError("Exp99 gate failed; stop before dense coupling")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
