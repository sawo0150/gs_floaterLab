#!/usr/bin/env python3
"""Exp103: repeat Exp102 with map-generation-scoped stable point IDs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import run_exp102_dense_topology_evidence_probe as prior


ROOT = (
    prior.prior.common.base.WORKSPACE
    / "results/experiments/exp103_generation_scoped_dense_evidence"
)
DOCS = (
    prior.prior.common.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp103_generation_scoped_dense_evidence_20260924"
)
RUN = ROOT / "rpng/table_01/normalized_probe_s0"
SOURCE_PATHS = (*prior.SOURCE_PATHS, Path(__file__))


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
            raise RuntimeError("Exp103 source changed after start; use a new root")
        return
    write_json(
        path,
        {
            "protocol": "exp103_generation_scoped_dense_evidence_v1",
            "corrects": "exp102 cross-generation point-ID collision",
            "vigs_commit": "913b9da2",
            "sha256": current,
        },
    )


def configure_prior() -> None:
    prior.ROOT = ROOT
    prior.DOCS = DOCS
    prior.RUN = RUN


def corrected_gate(run: Path) -> dict:
    report = prior.gate(run)
    evidence = report["evidence"]
    generation_checks = {
        "generation_namespace_present": (
            int(evidence.get("map_generations", 0)) > 1
        ),
        "final_generation_recorded": (
            isinstance(evidence.get("final_map_generation"), int)
        ),
        "all_records_generation_scoped": all(
            "map_generation" in row for row in evidence["records"]
        ),
    }
    report["protocol"] = "exp103_generation_scoped_dense_evidence_gate_v1"
    report["checks"].update(generation_checks)
    report["pass"] = bool(report["pass"] and all(generation_checks.values()))
    write_json(ROOT / "rpng/table_01/evidence_gate.json", report)
    return report


def write_summary(report: dict, consistency: dict) -> None:
    vanilla = read_json(
        prior.VANILLA / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]["mean_psnr"]
    evidence = report["evidence"]
    persistence = evidence["persistent_nominations"]
    mass = evidence["mean_gradient_mass_fraction"]
    lines = [
        "# Exp103 — generation-scoped dense topology evidence",
        "",
        "This rerun corrects Exp102's persistence accounting. VIGS restarts",
        "model-local point IDs after map reset, so every identity is now the",
        "pair `(map_generation, point_id)`. Consecutive-set overlap is reset",
        "at each generation boundary. Mapping behavior remains unchanged.",
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
        f"Isolation gate: **{'PASS' if report['pass'] else 'FAIL'}**.",
        "",
        (
            f"Observed map generations: {evidence['map_generations']}; final "
            f"generation: {evidence['final_map_generation']}."
        ),
        (
            f"Dense opportunities/unique UIDs: {evidence['opportunities']}/"
            f"{evidence['unique_dense_uids']}."
        ),
        (
            "Mean positive-gradient rows/share: "
            f"{evidence['mean_positive_gradient_rows']:.1f}/"
            f"{100.0 * evidence['mean_positive_fraction']:.2f}%."
        ),
        (
            "Mean gradient-mass captured by top 256/1,024/4,096 rows: "
            f"{100.0 * mass['256']:.2f}%/"
            f"{100.0 * mass['1024']:.2f}%/"
            f"{100.0 * mass['4096']:.2f}%."
        ),
        (
            "Within-generation consecutive top-1,024 Jaccard: "
            f"{evidence['mean_consecutive_top1024_jaccard']:.4f}."
        ),
        "",
        "| Diagnostic top-K | Generation-scoped unique | Repeated ≥2 | Repeated ≥3 | Final-generation live repeated ≥2 |",
        "|---:|---:|---:|---:|---:|",
    ]
    for key in ("256", "1024", "4096"):
        row = persistence[key]
        lines.append(
            f"| {int(key):,} | {row['unique_lifetime']:,} | "
            f"{row['nominated_at_least_2']:,} | "
            f"{row['nominated_at_least_3']:,} | "
            f"{row['live_nominated_at_least_2']:,} |"
        )
    lines.extend(
        (
            "",
            (
                "Probe host/top-k wall time: "
                f"{evidence['probe_wall_seconds']:.3f} s."
            ),
            "",
            "Only this corrected persistence table may be used to design the",
            "bounded mutation ticket. Exp102 remains valid for quality and",
            "gradient concentration, but not for cross-run identity counts.",
        )
    )
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run"))
    args = parser.parse_args()
    configure_prior()
    prior.prior.table01_row()
    source_lock()
    if args.action == "preflight":
        print("Exp103 preflight PASS: generation-scoped dense evidence")
        return 0
    run = prior.run_candidate()
    fixed = prior.prior.common.base.sequence_paths(
        "rpng", "table_01"
    )["fixed_manifest"]
    consistency = prior.prior.common.panel.run_evaluation_twice(
        run, "rpng", "table_01", fixed
    )
    report = corrected_gate(run)
    write_summary(report, consistency)
    print(
        "Exp103 table_01: "
        f"PSNR={report['candidate_psnr']:.6f}, "
        f"delta_control={report['candidate_minus_control_db']:+.6f}, "
        f"generations={report['evidence']['map_generations']}, "
        f"gate={report['pass']}",
        flush=True,
    )
    if not report["pass"]:
        raise RuntimeError("Exp103 corrected evidence isolation failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
