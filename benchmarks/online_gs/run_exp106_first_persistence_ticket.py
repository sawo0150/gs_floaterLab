#!/usr/bin/env python3
"""Exp106: one mid-cycle ticket at first persistent dense evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp105_dense_ticket_transfer as prior


ROOT = (
    prior.base.WORKSPACE
    / "results/experiments/exp106_first_persistence_ticket"
)
DOCS = (
    prior.base.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp106_first_persistence_ticket_20260924"
)
SOURCE_PATHS = (
    *prior.SOURCE_PATHS,
    prior.base.PAPER_ROOT / "vigs/gaussian/scene/gaussian_model.py",
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


def check_source_lock() -> None:
    current = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in SOURCE_PATHS
    }
    path = ROOT / "source_lock.json"
    if path.exists():
        if read_json(path)["sha256"] != current:
            raise RuntimeError("Exp106 source changed after start; use a new root")
        return
    write_json(
        path,
        {
            "protocol": "exp106_first_persistence_ticket_v1",
            "vigs_commit": "f6a90853",
            "trigger": "first repeated dense evidence per map generation",
            "ticket": 1024,
            "sha256": current,
        },
    )


def paths(row: dict) -> dict[str, Path]:
    historical = prior.panel.scene_paths(row)
    local = ROOT / row["dataset"] / row["scene"]
    return {
        **prior.base.sequence_paths(row["dataset"], row["scene"]),
        "candidate": local / "first_persistence_ticket_s0",
        "vanilla": local / "native_vanilla_render_matched_s0",
        "historical_r4": historical["candidate"],
        "pair": local / "pair_verification.json",
        "gate": local / "quality_gate.json",
        "result": local / "pair_result.json",
    }


def run_mapper(arm: str, row: dict, scene_paths: dict[str, Path]) -> None:
    run = scene_paths[arm]
    if (run / "mapping_replay_runtime.json").exists():
        return
    if run.exists():
        raise FileExistsError(f"incomplete Exp106 output exists: {run}")
    prior.panel.v2.gpu_idle()
    command = prior.base.mapping_command(
        "candidate" if arm == "candidate" else "vanilla",
        row["dataset"],
        row["scene"],
        ROOT,
    )
    command[command.index("--output") + 1] = str(run)
    if arm == "candidate":
        command.extend(
            (
                "--ercb-selection-potential",
                "normalized_variance",
                "--dense-topology-first-persistence-ticket",
            )
        )
    else:
        command[command.index("--reference-service-runtime") + 1] = str(
            scene_paths["candidate"] / "mapping_replay_runtime.json"
        )
    write_json(run / "mapping_command.json", command)
    prior.panel.v2.run_to_file(
        command, run / "mapping.log", custom=(arm == "candidate")
    )


def gate(row: dict, scene_paths: dict[str, Path]) -> dict:
    report = prior.gate(row, scene_paths)
    ticket = report["ticket"]
    first_events = [
        event for event in ticket["events"]
        if event.get("trigger") == "first_persistent_dense_step"
    ]
    checks = {
        "first_persistence_mode": (
            ticket.get("service_mode") == "first_persistence"
            and ticket.get("budget_mode")
            == "one_topk_ticket_at_first_persistence_per_generation"
        ),
        "active_on_short_scene": int(ticket["selected_mutations"]) > 0,
        "native_stats_preserved": (
            bool(first_events)
            and all(
                event.get("preserved_densification_stats") is True
                for event in first_events
            )
        ),
        "at_most_one_service_per_generation": (
            len(first_events)
            == len({event["map_generation"] for event in first_events})
        ),
    }
    report["protocol"] = "exp106_first_persistence_ticket_gate_v1"
    report["checks"].update(checks)
    report["stop"] = bool(report["stop"] or not all(checks.values()))
    write_json(scene_paths["gate"], report)
    return report


def run_one(row: dict) -> dict:
    scene_paths = paths(row)
    prior.panel.v2.preflight(row, prior.panel.scene_paths(row))
    check_source_lock()
    run_mapper("candidate", row, scene_paths)
    candidate_eval = prior.panel.run_evaluation_twice(
        scene_paths["candidate"],
        row["dataset"],
        row["scene"],
        scene_paths["fixed_manifest"],
    )
    quality = gate(row, scene_paths)
    if quality["stop"]:
        raise RuntimeError(
            f"Exp106 quality/structure stop: "
            f"{quality['candidate_minus_r4_db']:+.4f} dB vs R4"
        )
    run_mapper("vanilla", row, scene_paths)
    vanilla_eval = prior.panel.run_evaluation_twice(
        scene_paths["vanilla"],
        row["dataset"],
        row["scene"],
        scene_paths["fixed_manifest"],
    )
    subprocess.run(
        [
            str(prior.base.PYTHON_ENV / "bin/python"),
            str(prior.base.RENDER_VERIFIER),
            "--d1-run", str(scene_paths["candidate"]),
            "--vanilla-run", str(scene_paths["vanilla"]),
            "--output", str(scene_paths["pair"]),
        ],
        cwd=prior.base.WORKSPACE,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    pair = read_json(scene_paths["pair"])
    if not pair.get("valid"):
        raise RuntimeError("Exp106 fresh pair verification failed")
    result = {
        "dataset": row["dataset"],
        "scene": row["scene"],
        "candidate_psnr": pair["result"]["d1"]["psnr"],
        "vanilla_psnr": pair["result"]["vanilla"]["psnr"],
        "candidate_minus_vanilla_db": pair["result"]["d1_minus_vanilla"]["psnr"],
        "candidate_minus_r4_db": quality["candidate_minus_r4_db"],
        "selected_mutations": quality["ticket"]["selected_mutations"],
        "double_evaluation_pass": candidate_eval["pass"] and vanilla_eval["pass"],
        "fairness_pass": pair["valid"],
    }
    write_json(scene_paths["result"], result)
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "summary.md").write_text(
        "\n".join(
            (
                "# Exp106 — first-persistence local topology",
                "",
                f"Scene: `{row['dataset']}/{row['scene']}`.",
                f"PSNR: **{result['candidate_psnr']:.6f} dB**.",
                f"Candidate−Exp94 R4: **{result['candidate_minus_r4_db']:+.6f} dB**.",
                f"Candidate−fresh vanilla: **{result['candidate_minus_vanilla_db']:+.6f} dB**.",
                f"Selected mid-cycle mutations: **{result['selected_mutations']:,}**.",
                f"Double evaluation/fairness: **{'PASS' if result['double_evaluation_pass'] and result['fairness_pass'] else 'FAIL'}**.",
            )
        ) + "\n",
        encoding="utf-8",
    )
    print(
        f"Exp106 {row['dataset']}/{row['scene']}: "
        f"ticket−R4={result['candidate_minus_r4_db']:+.4f}, "
        f"ticket−vanilla={result['candidate_minus_vanilla_db']:+.4f}, "
        f"mutations={result['selected_mutations']}",
        flush=True,
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run"))
    args = parser.parse_args()
    rows = prior.panel.v2.install_inventory()
    prior.exp94.check_evaluation_contract(rows)
    check_source_lock()
    target = [
        row for row in rows
        if row["dataset"] == "utmm" and row["scene"] == "slow-straight-2"
    ][0]
    if args.action == "preflight":
        print("Exp106 preflight PASS: UTMM short-scene first-persistence ticket")
        return 0
    run_one(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
