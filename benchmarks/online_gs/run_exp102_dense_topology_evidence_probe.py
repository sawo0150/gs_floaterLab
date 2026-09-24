#!/usr/bin/env python3
"""Exp102: behavior-neutral ERCB dense-gradient topology evidence probe."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import run_exp98_gaussian_slam_local_birth as prior


ROOT = (
    prior.common.base.WORKSPACE
    / "results/experiments/exp102_dense_topology_evidence_probe"
)
DOCS = (
    prior.common.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp102_dense_topology_evidence_probe_20260924"
)
CONTROL = prior.CONTROL
VANILLA = prior.VANILLA
RUN = ROOT / "rpng/table_01/normalized_probe_s0"
MAX_CONTROL_DROP_DB = 0.5
SOURCE_PATHS = (
    *prior.SOURCE_PATHS,
    Path(__file__).with_name("dense_topology_evidence.py"),
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
            raise RuntimeError("Exp102 source changed after start; use a new root")
        return
    write_json(
        lock,
        {
            "protocol": "exp102_dense_topology_evidence_probe_v1",
            "implementation_references": [
                {
                    "repository": "https://github.com/hugoycj/TileGS",
                    "commit": "7f109a403ed522ba5ec7610f3d4778c363b68b11",
                    "use": "persistent per-Gaussian evidence concept only",
                },
                {
                    "repository": "https://github.com/humansensinglab/taming-3dgs",
                    "commit": "fd0f7d9edfe135eb4eefd3be82ee56dada7f2a16",
                    "use": "explicit mutation-ticket structure for next stage",
                },
            ],
            "vigs_commit": "2306b6f9",
            "sha256": current,
        },
    )


def run_candidate() -> Path:
    if (RUN / "mapping_replay_runtime.json").exists():
        return RUN
    if RUN.exists():
        raise FileExistsError(f"incomplete Exp102 output exists: {RUN}")
    prior.common.v2.gpu_idle()
    command = prior.common.base.mapping_command(
        "candidate", "rpng", "table_01", ROOT
    )
    command[command.index("--output") + 1] = str(RUN)
    command.extend(
        (
            "--ercb-selection-potential",
            "normalized_variance",
            "--dense-topology-evidence-probe",
        )
    )
    write_json(RUN / "mapping_command.json", command)
    prior.common.v2.run_to_file(command, RUN / "mapping.log", custom=True)
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
    evidence = current["dense_topology_evidence"]
    dense_opportunities = current["fixed_event_dense_opportunity_ledger"]
    opportunity_uids = [
        int(row["selected_keys"][0][1]) for row in dense_opportunities
    ]
    probe_uids = [
        int(row["dense_uid"]) for row in evidence["records"]
    ]
    current_topology = int(
        current["mapping_replay_summary"]["topology_events"]
    )
    control_topology = int(
        control["mapping_replay_summary"]["topology_events"]
    )
    checks = {
        "probe_requested": (
            current.get("dense_topology_evidence_probe_requested") is True
        ),
        "probe_behavior_neutral": (
            evidence.get("behavior_neutral") is True
            and int(evidence.get("extra_renders", -1)) == 0
            and int(evidence.get("mutation_rows", -1)) == 0
        ),
        "one_probe_per_dense_opportunity": (
            int(evidence.get("opportunities", -1))
            == len(dense_opportunities)
        ),
        "probe_uid_order_matches_ledger": probe_uids == opportunity_uids,
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
            prior.common.v2.opportunity_skeleton(
                current, "fixed_event_dense_opportunity_ledger"
            )
            == prior.common.v2.opportunity_skeleton(
                control, "fixed_event_dense_opportunity_ledger"
            )
        ),
        "same_keyframe_opportunities": (
            prior.common.v2.opportunity_skeleton(
                current, "fixed_event_keyframe_opportunity_ledger"
            )
            == prior.common.v2.opportunity_skeleton(
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
        "protocol": "exp102_dense_topology_evidence_gate_v1",
        "checks": checks,
        "candidate_psnr": psnr,
        "control_psnr": control_psnr,
        "candidate_minus_control_db": psnr - control_psnr,
        "max_control_drop_db": MAX_CONTROL_DROP_DB,
        "pass": (
            all(checks.values())
            and control_psnr - psnr <= MAX_CONTROL_DROP_DB
        ),
        "evidence": evidence,
        "topology_events": {
            "candidate": current_topology,
            "control": control_topology,
        },
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
    write_json(ROOT / "rpng/table_01/evidence_gate.json", report)
    return report


def write_summary(report: dict, consistency: dict) -> None:
    vanilla = read_json(
        VANILLA / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]["mean_psnr"]
    evidence = report["evidence"]
    persistence = evidence["persistent_nominations"]
    mass = evidence["mean_gradient_mass_fraction"]
    lines = [
        "# Exp102 — behavior-neutral dense topology evidence",
        "",
        "The probe reads per-Gaussian `f_dc` gradients already produced by each",
        "paid normalized-ERCB dense replay. It adds no render, Adam step, or map",
        "mutation. Persistent-counter semantics are informed by downloaded",
        "TileGS code; the CUDA implementation is not copied. Candidate ticket",
        "sizes are diagnostic powers of two, not active method parameters.",
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
            "Consecutive top-1,024 Jaccard: "
            f"{evidence['mean_consecutive_top1024_jaccard']:.4f}."
        ),
        "",
        "| Diagnostic top-K | Lifetime unique | Repeated ≥2 | Repeated ≥3 | Live repeated ≥2 |",
        "|---:|---:|---:|---:|---:|",
    ]
    for k in ("256", "1024", "4096"):
        row = persistence[k]
        lines.append(
            f"| {int(k):,} | {row['unique_lifetime']:,} | "
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
            "This run selects the evidence representation for the next bounded",
            "mutation experiment. It does not claim a topology quality gain.",
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
    prior.table01_row()
    check_source_lock()
    if args.action == "preflight":
        print("Exp102 preflight PASS: dense topology evidence")
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
        "Exp102 table_01: "
        f"PSNR={report['candidate_psnr']:.6f}, "
        f"delta_control={report['candidate_minus_control_db']:+.6f}, "
        f"gate={report['pass']}",
        flush=True,
    )
    if not report["pass"]:
        raise RuntimeError("Exp102 isolation failed; do not mutate topology")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
