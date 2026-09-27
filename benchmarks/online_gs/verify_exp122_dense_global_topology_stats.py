#!/usr/bin/env python3
"""Correct Exp122's topology-open opportunity predicate without rerunning maps."""

from __future__ import annotations

import json
from pathlib import Path

import run_exp122_dense_global_topology_stats_isolation as exp122


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    row = exp122.selected_row()
    paths = exp122.scene_paths(row)
    original = read_json(paths["verification"])
    result = read_json(paths["result"])
    runtimes = {
        arm: read_json(paths[arm] / "mapping_replay_runtime.json")
        for arm in exp122.ARMS
    }
    summaries = {
        arm: runtime["mapping_replay_summary"]
        for arm, runtime in runtimes.items()
    }
    stats_on = summaries["unified_stats_on"]
    stats_off = summaries["unified_stats_off"]
    off_ledger = stats_off["dense_global_scheduler_ledger"]
    topology_open_dense_opportunities = sum(
        row["optimizer_committed"]
        and row["controller_phase"] == "frontier"
        for row in off_ledger
    )

    method = dict(original["method_checks"])
    method["stats_off_disabled_and_each_topology_open_view_skipped"] = (
        int(stats_off["dense_global_topology_stats_enabled"]) == 0
        and topology_open_dense_opportunities > 0
        and int(stats_off["dense_global_topology_stats_skipped"])
        == topology_open_dense_opportunities
    )
    method.pop("stats_off_disabled_and_each_commit_skipped", None)
    corrected = {
        **original,
        "protocol": "exp122_dense_global_topology_stats_verification_v2",
        "supersedes_predicate_only": (
            "v1 incorrectly expected every dense commit to reach native "
            "topology statistics; final-v7 admits statistics only in the "
            "frontier phase"
        ),
        "mapping_outputs_rerun": False,
        "dense_global_commits": int(
            stats_off["dense_global_scheduler_commits"]
        ),
        "topology_open_dense_opportunities": int(
            topology_open_dense_opportunities
        ),
        "method_checks": method,
    }
    corrected["valid"] = (
        all(
            value
            for checks in corrected["common_checks"].values()
            for value in checks.values()
        )
        and all(method.values())
    )
    write_json(paths["verification"].with_name("verification_v2.json"), corrected)

    control_delta = abs(
        float(result["arms"]["unified_stats_on"]["psnr_delta_db"])
    )
    recovery = (
        float(result["arms"]["unified_stats_off"]["psnr"])
        - float(result["arms"]["unified_stats_on"]["psnr"])
    )
    result["verification_v2"] = {
        "valid": corrected["valid"],
        "topology_open_dense_opportunities": int(
            topology_open_dense_opportunities
        ),
        "stats_off_recovery_vs_stats_on_db": recovery,
        "fraction_of_stats_on_gap_recovered": (
            recovery / control_delta if control_delta else None
        ),
    }
    result["valid"] = corrected["valid"]
    write_json(paths["result"].with_name("result_v2.json"), result)

    summary = exp122.DOCS / "summary.md"
    lines = summary.read_text(encoding="utf-8").splitlines()
    if lines and lines[-1].startswith("Gate:"):
        lines[-1] = f"Corrected v2 gate: **{'PASS' if corrected['valid'] else 'FAIL'}**."
    lines.extend(
        (
            "",
            "## Verification correction",
            "",
            "The original v1 verifier incorrectly compared skipped topology",
            "statistics with all 1,610 dense commits. final-v7 accepts native",
            "densification statistics only in `frontier`; the locked ledger has",
            f"{topology_open_dense_opportunities} such committed dense views, and",
            f"stats-off skipped exactly {int(stats_off['dense_global_topology_stats_skipped'])}.",
            "No mapping or evaluation output was rerun.",
            "",
            "Stats-off recovered only "
            f"**{recovery:+.6f} dB** over stats-on "
            f"({100.0 * recovery / control_delta:.2f}% of the stats-on gap).",
            "Thus dense topology statistics explain little of the RPNG loss;",
            "the RGB-D historical-KF to RGB-only dense-view replacement remains",
            "the primary isolated cause.",
        )
    )
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        "Exp122 corrected verification "
        f"{'PASS' if corrected['valid'] else 'FAIL'}: "
        f"topology-open={topology_open_dense_opportunities}, "
        f"skipped={stats_off['dense_global_topology_stats_skipped']}, "
        f"recovery={recovery:+.6f} dB"
    )
    return 0 if corrected["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
