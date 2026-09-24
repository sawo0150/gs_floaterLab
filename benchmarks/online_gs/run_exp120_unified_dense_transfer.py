#!/usr/bin/env python3
"""Exp120: frozen exact-render unified dense transfer to RPNG and Aria."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp119_unified_dense_global_corrected as prior


BASE = prior.BASE
PANEL = prior.PANEL
ROOT = BASE.WORKSPACE / "results/experiments/exp120_unified_dense_transfer"
DOCS = (
    BASE.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp120_unified_dense_transfer_20260924"
)
SCENES = (("rpng", "table_01"), ("aria", "aria1253"))
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
            raise RuntimeError("Exp120 source changed after start; use a new root")
        return
    write_json(
        path,
        {
            "protocol": "exp120_unified_dense_transfer_v1",
            "scenes_in_stop_order": [list(scene) for scene in SCENES],
            "arms": list(ARMS),
            "frozen_from": "exp119_unified_dense_global_corrected",
            "dense_global_replacement_slots": 1,
            "mass_prior_or_gamma_retuned": False,
            "quality_stop_db_vs_fresh_control": -0.5,
            "exact_render_and_adam_parity_required": True,
            "stop_on_first_invalid_scene": True,
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
                f"Exp120 inventory mismatch: {dataset}/{scene} "
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
        raise FileExistsError(f"incomplete Exp120 output exists: {output}")
    PANEL.v2.gpu_idle()
    command = prior.prior.mapping_command(arm, row, output)
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
    result = prior.verify_corrected(row, paths, evaluations)
    verification = read_json(paths["verification"])
    verification["protocol"] = (
        "exp120_unified_dense_transfer_verification_v1"
    )
    verification["formula_and_slot_rule_frozen_from_exp119"] = True
    verification["scene_retuning"] = False
    write_json(paths["verification"], verification)
    result["protocol"] = "exp120_unified_dense_transfer_result_v1"
    result["formula_and_slot_rule_frozen_from_exp119"] = True
    result["scene_retuning"] = False
    write_json(paths["result"], result)
    return result


def write_summary(results: list[dict]) -> None:
    lines = [
        "# Exp120 — frozen exact-render unified dense transfer",
        "",
        "Exp119's one-slot rule, LPM mass prior, and gamma are transferred",
        "without retuning. RPNG must pass before Aria starts.",
        "",
    ]
    if not results:
        lines.append("Status: **PENDING**.")
    else:
        lines.extend(
            (
                "| Dataset / scene | Arm | PSNR | Delta | Dense renders/share | Total renders | Adam | GS |",
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
                    f"{item['dense_renders']} / {100*item['dense_share']:.2f}% | "
                    f"{item['renders']} | {item['adam']} | {item['gaussians']} |"
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
    prior.prior.prior.prior.prior.prior.prior.prior.prior.prior.exp94.check_evaluation_contract(
        rows
    )
    for row in rows:
        PANEL.v2.preflight(row, PANEL.scene_paths(row))
    check_source_lock()
    if args.action == "preflight":
        write_summary([])
        print("Exp120 preflight PASS: 2 transfer scenes x 3 fresh arms")
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
                    "Exp120 transfer stop at "
                    f"{row['dataset']}/{row['scene']}"
                )
        print(
            "Exp120 PASS: "
            + ", ".join(
                f"{result['dataset']}/{result['scene']}="
                f"{result['arms']['unified_mass_normalized']['psnr_delta_db']:+.6f}dB/"
                f"{100*result['arms']['unified_mass_normalized']['dense_share']:.2f}%dense"
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
