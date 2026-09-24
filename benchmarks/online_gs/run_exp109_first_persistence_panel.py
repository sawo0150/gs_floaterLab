#!/usr/bin/env python3
"""Exp109: frozen first-persistence topology over all 17 valid B-track scenes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import run_exp106_first_persistence_ticket as prior


ROOT = (
    prior.prior.base.WORKSPACE
    / "results/experiments/exp109_first_persistence_panel"
)
DOCS = (
    prior.prior.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp109_first_persistence_panel_20260924"
)
SOURCE_PATHS = (*prior.SOURCE_PATHS, Path(__file__))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_source_lock() -> None:
    current = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in SOURCE_PATHS
    }
    path = ROOT / "source_lock.json"
    if path.exists():
        old = read_json(path)
        if old["sha256"] != current:
            raise RuntimeError("Exp109 source changed after start; use a new root")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "protocol": "exp109_first_persistence_panel_v1",
                "vigs_code_commit": "f6a90853",
                "vigs_head_at_start": "51ad7285",
                "lab_commit_at_start": "3ddd720",
                "no_scene_retuning": True,
                "sha256": current,
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )


def write_summary(rows: list[dict]) -> None:
    completed = []
    lines = [
        "# Exp109 — frozen first-persistence 17-scene B-track panel",
        "",
        "Every row is a fresh candidate/official-vanilla pair from this output",
        "root. The method is frozen: normalized-variance ERCB, two distinct",
        "dense-view nominations, one top-1,024 weighted-without-replacement",
        "small-clone ticket at first persistence per map generation, and native",
        "densification-state preservation. No scene-specific parameter is used.",
        "",
        "| Dataset | Scene | Candidate | Vanilla | delta vanilla | delta R4 | Clone | Render C/V | Adam C/V | GS C/V | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        path = ROOT / row["dataset"] / row["scene"] / "pair_result.json"
        if not path.exists():
            lines.append(
                f"| {row['dataset']} | {row['scene']} | — | — | — | — | — | — | — | — | PENDING |"
            )
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
    lines.extend(("", f"Completed formal pairs: **{len(completed)}/17**."))
    if len(completed) == 17:
        mean = sum(x["candidate_minus_vanilla_db"] for x in completed) / 17
        wins = sum(x["candidate_minus_vanilla_db"] > 0 for x in completed)
        valid = all(
            x["double_evaluation_pass"] and x["fairness_pass"]
            for x in completed
        )
        r4_floor = all(x["candidate_minus_r4_db"] >= -0.5 for x in completed)
        accepted = mean >= 0.5 and wins >= 9 and valid and r4_floor
        stretch = mean >= 1.253787 and wins == 17 and valid and r4_floor
        lines.extend(
            (
                f"Scene-arithmetic mean delta PSNR: **{mean:+.6f} dB**; "
                f"wins **{wins}/17**.",
                f"Predeclared minimum acceptance: **{'PASS' if accepted else 'FAIL'}** "
                "(mean >=+0.5 dB, majority wins, all fairness and R4-floor checks).",
                f"Exp94 stretch target (+1.253787 dB, 17/17): "
                f"**{'PASS' if stretch else 'FAIL'}**.",
            )
        )
    else:
        lines.append("No all-scene acceptance claim until all 17 pairs complete.")
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run-one", "run-all"))
    parser.add_argument("--dataset", choices=("rpng", "utmm", "aria"))
    parser.add_argument("--scene")
    args = parser.parse_args()

    prior.ROOT = ROOT
    prior.DOCS = DOCS
    prior.check_source_lock = check_source_lock
    rows = prior.prior.panel.v2.install_inventory()
    prior.prior.exp94.check_evaluation_contract(rows)
    if args.action == "preflight":
        for row in rows:
            prior.prior.panel.v2.preflight(
                row, prior.prior.panel.scene_paths(row)
            )
        check_source_lock()
        print(f"Exp109 preflight PASS: {len(rows)} frozen scenes")
        return 0
    if args.action == "run-one":
        selected = [
            row for row in rows
            if (row["dataset"], row["scene"]) == (args.dataset, args.scene)
        ]
        if len(selected) != 1:
            raise ValueError("run-one requires one valid --dataset/--scene")
    else:
        selected = rows
    check_source_lock()
    try:
        for row in selected:
            prior.run_one(row)
    finally:
        write_summary(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
