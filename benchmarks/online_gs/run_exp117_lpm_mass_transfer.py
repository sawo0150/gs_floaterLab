#!/usr/bin/env python3
"""Exp117: frozen LPM mass-prior transfer to RPNG and Aria."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp116_lpm_mass_prior as prior


BASE = prior.BASE
PANEL = prior.PANEL
ROOT = BASE.WORKSPACE / "results/experiments/exp117_lpm_mass_transfer"
DOCS = (
    BASE.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp117_lpm_mass_transfer_20260924"
)
SCENES = (
    ("rpng", "table_01"),
    ("aria", "aria1253"),
)
ARMS = prior.ARMS
SOURCE_PATHS = tuple(dict.fromkeys((*prior.SOURCE_PATHS, Path(__file__))))


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
    current = {str(path): sha256(path) for path in SOURCE_PATHS}
    path = ROOT / "source_lock.json"
    if path.exists():
        if read_json(path)["sha256"] != current:
            raise RuntimeError("Exp117 source changed after start; use a new root")
        return
    write_json(
        path,
        {
            "protocol": "exp117_lpm_mass_transfer_v1",
            "scenes_in_stop_order": [list(scene) for scene in SCENES],
            "arms": list(ARMS),
            "development_experiment": "exp116_lpm_mass_prior",
            "formula_frozen_before_transfer": (
                "q_i=(active_pixels+256)/(H*W+256); "
                "p_i proportional to q_i*exp(-16*n_i/(T+1))"
            ),
            "quality_metric_used_to_retune": False,
            "scene_or_dataset_hyperparameters": False,
            "stop_if_any_normalized_delta_db_below": -0.5,
            "stop_if_any_fairness_or_activity_gate_fails": True,
            "full_panel_allowed_by_this_experiment": False,
            "lab_head_before_runner_commit": subprocess.check_output(
                ("git", "-C", str(BASE.WORKSPACE), "rev-parse", "HEAD"),
                text=True,
            ).strip(),
            "vigs_head": subprocess.check_output(
                ("git", "-C", str(BASE.PAPER_ROOT), "rev-parse", "HEAD"),
                text=True,
            ).strip(),
            "sha256": current,
        },
    )


def selected_rows() -> list[dict]:
    inventory = PANEL.v2.install_inventory()
    rows = []
    for dataset, scene in SCENES:
        matches = [
            row
            for row in inventory
            if (row["dataset"], row["scene"]) == (dataset, scene)
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"Exp117 scene inventory mismatch: {dataset}/{scene} "
                f"has {len(matches)} rows"
            )
        rows.append(matches[0])
    return rows


def scene_paths(row: dict) -> dict[str, Path]:
    common = BASE.sequence_paths(row["dataset"], row["scene"])
    local = ROOT / row["dataset"] / row["scene"]
    return {
        **common,
        **{arm: local / arm for arm in ARMS},
        "verification": local / "verification.json",
        "result": local / "result.json",
    }


def run_mapper(arm: str, row: dict, paths: dict[str, Path]) -> None:
    output = paths[arm]
    if (output / "mapping_replay_runtime.json").exists():
        return
    if output.exists():
        raise FileExistsError(f"incomplete Exp117 output exists: {output}")
    PANEL.v2.gpu_idle()
    command = prior.mapping_command(arm, row, output)
    write_json(output / "mapping_command.json", command)
    PANEL.v2.run_to_file(command, output / "mapping.log", custom=True)


def evaluate(arm: str, row: dict, paths: dict[str, Path]) -> dict:
    return PANEL.run_evaluation_twice(
        paths[arm], row["dataset"], row["scene"], paths["fixed_manifest"]
    )


def verify_transfer(
    row: dict,
    paths: dict[str, Path],
    evaluations: dict[str, dict],
) -> dict:
    result = prior.verify(row, paths, evaluations)
    verification = read_json(paths["verification"])
    verification["protocol"] = "exp117_lpm_mass_transfer_verification_v1"
    verification["formula_frozen_from_exp116"] = True
    verification["scene_retuning"] = False
    write_json(paths["verification"], verification)
    result["protocol"] = "exp117_lpm_mass_transfer_result_v1"
    result["formula_frozen_from_exp116"] = True
    result["scene_retuning"] = False
    write_json(paths["result"], result)
    return result


def write_summary(results: list[dict]) -> None:
    lines = [
        "# Exp117 — frozen LPM mass-prior transfer",
        "",
        "Exp116's formula and gamma are transferred without retuning.",
        "A failure or a normalized-arm drop below -0.5 dB stops later scenes.",
        "",
    ]
    if not results:
        lines.append("Status: **PENDING**.")
    else:
        lines.extend(
            (
                "| Dataset / scene | Arm | PSNR | Delta | Trace rows changed | Renders | Adam | GS |",
                "|---|---|---:|---:|---:|---:|---:|---:|",
            )
        )
        for result in results:
            label = f"{result['dataset']} / {result['scene']}"
            for arm in ARMS:
                item = result["arms"][arm]
                lines.append(
                    f"| {label} | {arm} | {item['psnr']:.6f} | "
                    f"{item['psnr_delta_db']:+.6f} | "
                    f"{item['trace_difference_rows']} | {item['renders']} | "
                    f"{item['adam']} | {item['gaussians']} |"
                )
        all_valid = len(results) == len(SCENES) and all(
            result["valid"] for result in results
        )
        lines.extend(
            (
                "",
                f"Completed scenes: **{len(results)}/{len(SCENES)}**.",
                f"Gate: **{'PASS' if all_valid else 'FAIL/INCOMPLETE'}**.",
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
    rows = selected_rows()
    prior.prior.prior.prior.prior.prior.prior.prior.exp94.check_evaluation_contract(
        rows
    )
    for row in rows:
        PANEL.v2.preflight(row, PANEL.scene_paths(row))
    check_source_lock()
    if args.action == "preflight":
        write_summary([])
        print("Exp117 preflight PASS: 2 transfer scenes x 3 fresh arms")
        return 0

    results = []
    try:
        for row in rows:
            paths = scene_paths(row)
            evaluations = {}
            for arm in ARMS:
                run_mapper(arm, row, paths)
                evaluations[arm] = evaluate(arm, row, paths)
            result = verify_transfer(row, paths, evaluations)
            results.append(result)
            write_summary(results)
            if not result["valid"]:
                raise RuntimeError(
                    "Exp117 transfer stop at "
                    f"{row['dataset']}/{row['scene']}"
                )
        print(
            "Exp117 PASS: "
            + ", ".join(
                f"{result['dataset']}/{result['scene']}="
                f"{result['arms']['lpm_mass_normalized']['psnr_delta_db']:+.6f}dB/"
                f"{result['arms']['lpm_mass_normalized']['trace_difference_rows']}rows"
                for result in results
            ),
            flush=True,
        )
    except Exception:
        write_summary(results)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
