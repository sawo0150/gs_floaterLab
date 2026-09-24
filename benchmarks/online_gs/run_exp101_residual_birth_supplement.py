#!/usr/bin/env python3
"""Exp101: preserve R4 birth and add official residual-local supplement."""

from __future__ import annotations

import argparse
from pathlib import Path

import run_exp100_capacity_matched_local_birth as replacement


prior = replacement.prior
ROOT = (
    prior.common.base.WORKSPACE
    / "results/experiments/exp101_residual_birth_supplement"
)
DOCS = (
    prior.common.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp101_residual_birth_supplement_20260924"
)
SOURCE_PATHS = (*replacement.SOURCE_PATHS, Path(__file__))
RUN = ROOT / "rpng/table_01/residual_supplement_s0"

prior.ROOT = ROOT
prior.DOCS = DOCS


def check_source_lock() -> None:
    lock = ROOT / "source_lock.json"
    current = {str(path): prior.sha256(path) for path in SOURCE_PATHS}
    if lock.exists():
        if prior.read_json(lock)["sha256"] != current:
            raise RuntimeError("Exp101 source changed after start; use a new root")
        return
    prior.write_json(
        lock,
        {
            "protocol": "exp101_residual_birth_supplement_v1",
            "implementation_reference": {
                "repository": "https://github.com/VladimirYugay/Gaussian-SLAM",
                "commit": "eaec10d73ce7511563882b8856896e06d1f804e3",
                "license": "MIT",
            },
            "vigs_commit": "96de04b3",
            "sha256": current,
        },
    )


def run_candidate() -> Path:
    if (RUN / "mapping_replay_runtime.json").exists():
        return RUN
    if RUN.exists():
        raise FileExistsError(f"incomplete Exp101 output exists: {RUN}")
    prior.common.v2.gpu_idle()
    command = prior.common.base.mapping_command(
        "candidate", "rpng", "table_01", ROOT
    )
    command[command.index("--output") + 1] = str(RUN)
    command.extend(
        (
            "--ercb-selection-potential",
            "normalized_variance",
            "--local-birth",
            "--local-birth-budget-mode",
            "residual_supplement",
            "--local-birth-radius",
            str(prior.RADIUS_M),
        )
    )
    prior.write_json(RUN / "mapping_command.json", command)
    prior.common.v2.run_to_file(command, RUN / "mapping.log", custom=True)
    return RUN


def gate(run: Path) -> dict:
    report = prior.gate(run)
    current = prior.read_json(run / "mapping_replay_runtime.json")
    control = prior.read_json(
        prior.CONTROL / "mapping_replay_runtime.json"
    )
    birth = report["local_birth"]
    report["protocol"] = "exp101_residual_birth_supplement_gate_v1"
    report["vigs_commit"] = "96de04b3"
    report["checks"].pop("bounded_ticket", None)
    report["checks"].update(
        {
            "residual_supplement_mode": (
                current.get("local_birth_budget_mode")
                == "residual_supplement"
                and birth.get("budget_mode") == "residual_supplement"
            ),
            "baseline_birth_executed": int(
                birth.get("baseline_births", 0)
            ) > 0,
            "same_full_view_density_trace": (
                replacement._density_trace(current)
                == replacement._density_trace(control)
            ),
        }
    )
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
    lines = [
        "# Exp101 — R4-preserving official residual-birth supplement",
        "",
        "R4 blanket PPM birth and its RNG stream are preserved first. A separate",
        "RNG stream then applies the low-alpha/positive-depth-residual mask and",
        "current-frustum radius rejection ported from Gaussian-SLAM author code",
        "`eaec10d7` (MIT), using one matched-R4 supplemental allocation. VIGS",
        "source: `96de04b3`.",
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
        (
            "Full-view causal density trace parity: **"
            f"{'PASS' if report['checks']['same_full_view_density_trace'] else 'FAIL'}**."
        ),
        "",
        (
            "Birth events/baseline births/residual offered/residual accepted/"
            "duplicate-rejected: "
            f"{int(birth.get('events', 0)):,}/"
            f"{int(birth.get('baseline_births', 0)):,}/"
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
        "This is a one-scene isolation gate. It does not yet establish a dense/",
        "ERCB topology contribution or strict-live feasibility.",
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
        print("Exp101 preflight PASS: R4-preserving residual supplement")
        return 0
    run = run_candidate()
    fixed = prior.common.base.sequence_paths(
        "rpng", "table_01"
    )["fixed_manifest"]
    consistency = prior.common.panel.run_evaluation_twice(
        run, "rpng", "table_01", fixed
    )
    report = gate(run)
    write_summary(report, consistency)
    print(
        "Exp101 table_01: "
        f"PSNR={report['candidate_psnr']:.6f}, "
        f"delta_control={report['candidate_minus_control_db']:+.6f}, "
        f"gate={report['pass']}",
        flush=True,
    )
    if not report["pass"]:
        raise RuntimeError("Exp101 gate failed; stop before dense coupling")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
