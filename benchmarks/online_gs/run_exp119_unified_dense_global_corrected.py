#!/usr/bin/env python3
"""Exp119: corrected exact-render unified dense global-slot gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp118_unified_dense_global as prior


BASE = prior.BASE
PANEL = prior.PANEL
ROOT = (
    BASE.WORKSPACE
    / "results/experiments/exp119_unified_dense_global_corrected"
)
DOCS = (
    BASE.WORKSPACE
    / "context/experiments/benchmark_custom"
    / "exp119_unified_dense_global_corrected_20260924"
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
            raise RuntimeError("Exp119 source changed after start; use a new root")
        return
    write_json(
        path,
        {
            "protocol": "exp119_unified_dense_global_corrected_v1",
            "scene": "utmm/square-1",
            "arms": list(ARMS),
            "corrects": "exp118 early-pool supplemental render bug",
            "cardinality_rule": (
                "G=min(n_global_views,available_history); "
                "dense=min(1,G,available_dense); tracked=G-dense"
            ),
            "quality_stop_db_vs_control": -0.5,
            "render_count_must_match_exactly": True,
            "adam_count_must_match_exactly": True,
            "scene_or_dataset_hyperparameters": False,
            "lab_head_before_runner_commit": subprocess.check_output(
                ("git", "-C", str(BASE.WORKSPACE), "rev-parse", "HEAD"),
                text=True,
            ).strip(),
            "vigs_head_before_fix_commit": subprocess.check_output(
                ("git", "-C", str(BASE.PAPER_ROOT), "rev-parse", "HEAD"),
                text=True,
            ).strip(),
            "sha256": current,
        },
    )


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
        raise FileExistsError(f"incomplete Exp119 output exists: {output}")
    PANEL.v2.gpu_idle()
    command = prior.mapping_command(arm, row, output)
    write_json(output / "mapping_command.json", command)
    PANEL.v2.run_to_file(command, output / "mapping.log", custom=True)


def evaluate(arm: str, row: dict, paths: dict[str, Path]) -> dict:
    return PANEL.run_evaluation_twice(
        paths[arm], row["dataset"], row["scene"], paths["fixed_manifest"]
    )


def corrected_ledger_valid(ledger: list[dict]) -> bool:
    return bool(ledger) and all(
        entry["optimizer_committed"]
        and entry["dense_replacement_slots"] == 1
        and len(entry["selected_uids"]) == 1
        and entry["control_global_slots"]
        == min(entry["native_global_slots"], entry["historical_pool_size"])
        and entry["tracked_historical_slots"]
        + entry["dense_replacement_slots"]
        == entry["control_global_slots"]
        and entry["combined_view_count_before_cap"]
        == len(entry["recent_window_uids"]) + entry["control_global_slots"]
        and not entry["cap_applied"]
        and entry["combined_view_count_before_cap"] <= entry["max_viewpoints"]
        and bool(entry["recent_window_uids"])
        for entry in ledger
    )


def verify_corrected(
    row: dict,
    paths: dict[str, Path],
    evaluations: dict[str, dict],
) -> dict:
    result = prior.verify(row, paths, evaluations)
    verification = read_json(paths["verification"])
    normalized_ledger = read_json(
        paths["unified_mass_normalized"] / "mapping_replay_runtime.json"
    )["mapping_replay_summary"]["dense_global_scheduler_ledger"]
    rr_ledger = read_json(
        paths["unified_mass_rr"] / "mapping_replay_runtime.json"
    )["mapping_replay_summary"]["dense_global_scheduler_ledger"]
    verification["protocol"] = (
        "exp119_unified_dense_global_corrected_verification_v1"
    )
    verification["corrected_cardinality_rule"] = True
    verification["method_checks"]["normalized_global_ledger_valid"] = (
        corrected_ledger_valid(normalized_ledger)
    )
    verification["method_checks"]["rr_global_ledger_valid"] = (
        corrected_ledger_valid(rr_ledger)
    )
    verification["valid"] = (
        all(
            value
            for checks in verification["common_checks"].values()
            for value in checks.values()
        )
        and all(verification["method_checks"].values())
    )
    write_json(paths["verification"], verification)
    result["protocol"] = "exp119_unified_dense_global_corrected_result_v1"
    result["corrected_cardinality_rule"] = True
    result["method_checks"] = verification["method_checks"]
    result["valid"] = verification["valid"]
    write_json(paths["result"], result)
    return result


def write_summary(result: dict | None) -> None:
    lines = [
        "# Exp119 — corrected exact-render unified dense global slot",
        "",
        "Control-equivalent global cardinality is frozen before one actual",
        "historical slot is reassigned to the unified LPM-mass dense pool.",
        "",
    ]
    if result is None:
        lines.append("Status: **PENDING**.")
    else:
        lines.extend(
            (
                "| Arm | PSNR | Delta | SSIM | LPIPS | Dense renders/share | Renders | Adam | GS |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            )
        )
        for arm in ARMS:
            item = result["arms"][arm]
            lines.append(
                f"| {arm} | {item['psnr']:.6f} | "
                f"{item['psnr_delta_db']:+.6f} | {item['ssim']:.6f} | "
                f"{item['lpips']:.6f} | {item['dense_renders']} / "
                f"{100*item['dense_share']:.2f}% | {item['renders']} | "
                f"{item['adam']} | {item['gaussians']} |"
            )
        lines.extend(
            (
                "",
                "Normalized/RR unified global trace differences: "
                f"**{result['global_trace_difference_rows']} rows**.",
                f"Gate: **{'PASS' if result['valid'] else 'FAIL'}**.",
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
    row = prior.prior.prior.selected_row()
    paths = scene_paths(row)
    prior.prior.prior.prior.prior.prior.prior.prior.prior.exp94.check_evaluation_contract(
        [row]
    )
    PANEL.v2.preflight(row, PANEL.scene_paths(row))
    check_source_lock()
    if args.action == "preflight":
        write_summary(None)
        print("Exp119 preflight PASS: 1 development scene x 3 fresh arms")
        return 0

    result = None
    evaluations = {}
    try:
        for arm in ARMS:
            run_mapper(arm, row, paths)
            evaluations[arm] = evaluate(arm, row, paths)
        result = verify_corrected(row, paths, evaluations)
        write_summary(result)
        if not result["valid"]:
            raise RuntimeError("Exp119 verification stop")
        print(
            "Exp119 PASS: unified normalized="
            f"{result['arms']['unified_mass_normalized']['psnr_delta_db']:+.6f} dB, "
            "dense share="
            f"{100*result['arms']['unified_mass_normalized']['dense_share']:.2f}%",
            flush=True,
        )
    except Exception:
        if result is None:
            write_summary(None)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
