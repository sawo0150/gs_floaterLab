#!/usr/bin/env python3
"""Three-family pilot for geometry/photometric role-aware mapping service."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ONLINE_GS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ONLINE_GS))

import run_exp111_dense_repeat_ercb as exp111


BASE = exp111.prior.prior.prior.base
PANEL = exp111.prior.prior.prior.panel
EXP94 = exp111.prior.prior.prior.exp94
V2 = PANEL.v2
WORKSPACE = BASE.WORKSPACE
PAPER_ROOT = BASE.PAPER_ROOT
ROOT = (
    WORKSPACE
    / "results/campaigns/gain_attribution/role_aware_dense_service_v3"
)
SCENES = (
    ("utmm", "square-1"),
    ("rpng", "table_01"),
    ("aria", "aria1253"),
)
ARMS = ("r4_backbone", "role_normalized", "role_rr")
SOURCE_PATHS = (
    WORKSPACE / "benchmarks/online_gs/exp78b_replay_gsslam_mapping.py",
    PAPER_ROOT / "demo.py",
    PAPER_ROOT / "vigs/gs_backend.py",
    PAPER_ROOT / "vigs/map_scheduler.py",
    Path(__file__).resolve(),
)
QUALITY_STOP_DB = -0.5
MIN_PHOTOMETRIC_SHARE = 0.05


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


def git_head(root: Path) -> str:
    return subprocess.check_output(
        ("git", "-C", str(root), "rev-parse", "HEAD"), text=True
    ).strip()


def check_source_lock() -> None:
    current = {str(path): sha256(path) for path in SOURCE_PATHS}
    value = {
        "protocol": "role_aware_dense_service_v3",
        "supersedes": (
            "v2 retained R4's auxiliary keyframe appearance slot; v3 "
            "reallocates that identical work to dense repeat service"
        ),
        "scenes": [list(item) for item in SCENES],
        "arms": list(ARMS),
        "quality_stop_db_vs_r4_backbone": QUALITY_STOP_DB,
        "minimum_photometric_render_share": MIN_PHOTOMETRIC_SHARE,
        "scene_specific_hyperparameters": False,
        "role_service_quantum": "one final equal-cardinality iteration",
        "geometry_floor": "at least one complete native RGB-D iteration",
        "normalized_potential": "exp(-16*n_i/(T+1))",
        "vigs_commit": git_head(PAPER_ROOT),
        "lab_commit": git_head(WORKSPACE),
        "sha256": current,
    }
    path = ROOT / "source_lock.json"
    if path.exists():
        previous = read_json(path)
        if previous["sha256"] != current:
            raise RuntimeError(
                "role-aware pilot source changed after start; use a new root"
            )
        return
    write_json(path, value)


def selected_rows() -> list[dict]:
    inventory = V2.install_inventory()
    indexed = {
        (row["dataset"], row["scene"]): row for row in inventory
    }
    rows = []
    for key in SCENES:
        if key not in indexed:
            raise RuntimeError(f"representative scene missing: {key}")
        rows.append(indexed[key])
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


def mapping_command(arm: str, row: dict, output: Path) -> list[str]:
    command = BASE.mapping_command(
        "candidate", row["dataset"], row["scene"], ROOT
    )
    command[command.index("--output") + 1] = str(output)
    command.extend(("--ercb-selection-potential", "normalized_variance"))
    command.append("--dense-topology-first-persistence-ticket")
    if arm in ("role_normalized", "role_rr"):
        command.extend(
            (
                "--stage6r-aux-kf-to-dense-repeat",
                "--role-aware-dense-service",
                "--role-aware-dense-selector",
                "normalized_variance" if arm == "role_normalized" else "rr",
                "--role-aware-dense-gamma",
                "16",
                "--role-aware-dense-scope",
                "appearance",
            )
        )
    return command


def run_mapper(arm: str, row: dict, paths: dict[str, Path]) -> None:
    output = paths[arm]
    if (output / "mapping_replay_runtime.json").exists():
        return
    if output.exists():
        raise FileExistsError(f"incomplete role-aware output exists: {output}")
    V2.gpu_idle()
    command = mapping_command(arm, row, output)
    write_json(output / "mapping_command.json", command)
    V2.run_to_file(command, output / "mapping.log", custom=True)


def evaluate(arm: str, row: dict, paths: dict[str, Path]) -> dict:
    return PANEL.run_evaluation_twice(
        paths[arm],
        row["dataset"],
        row["scene"],
        paths["fixed_manifest"],
    )


def fixed_metrics(output: Path) -> dict:
    return read_json(
        output / "psnr/strict_fixed_manifest/final_result.json"
    )["predeclared_fixed_manifest_posthoc"]


def role_summary(runtime: dict) -> dict:
    return runtime["mapping_replay_summary"]["role_aware_dense_service"]


def selection_trace(runtime: dict) -> list[tuple[int, ...]]:
    return [
        tuple(int(uid) for uid in row["selected_dense_uids"])
        for row in role_summary(runtime)["selection_ledger"]
    ]


def verify(row: dict, paths: dict[str, Path], evaluations: dict) -> dict:
    runtimes = {
        arm: read_json(paths[arm] / "mapping_replay_runtime.json")
        for arm in ARMS
    }
    baseline = runtimes["r4_backbone"]
    common = {}
    for arm, runtime in runtimes.items():
        common[arm] = {
            "same_archive": runtime["archive_manifest_sha256"]
            == baseline["archive_manifest_sha256"],
            "same_config": runtime["effective_config_sha256"]
            == baseline["effective_config_sha256"],
            "same_events": runtime["event_ids_fully_processed"]
            == baseline["event_ids_fully_processed"],
            "same_physical_renders": runtime["rasterized_view_updates"]
            == baseline["rasterized_view_updates"],
            "same_adam_steps": runtime["optimizer_steps_completed"]
            == baseline["optimizer_steps_completed"],
            "same_dense_admission": runtime[
                "dense_registered_frame_uids"
            ]
            == baseline["dense_registered_frame_uids"],
            "zero_tail": runtime["post_eos_optimizer_updates"] == 0,
            "mapping_disjoint": (
                runtime["heldout_mapping_overlap_count"] == 0
                and runtime["heldout_gaussian_origin_overlap_count"] == 0
            ),
            "double_evaluation": bool(evaluations[arm]["pass"]),
        }

    method = {
        "backbone_role_service_disabled": (
            role_summary(baseline)["enabled"] == 0
            and role_summary(baseline)["photometric_renders_completed"] == 0
        )
    }
    for arm, expected_selector in (
        ("role_normalized", "normalized_variance"),
        ("role_rr", "rr"),
    ):
        summary = role_summary(runtimes[arm])
        ledger = summary["selection_ledger"]
        method[f"{arm}_enabled"] = summary["enabled"] == 1
        method[f"{arm}_selector"] = summary["selector"] == expected_selector
        method[f"{arm}_meaningful_share"] = (
            summary["photometric_render_share"] >= MIN_PHOTOMETRIC_SHARE
        )
        method[f"{arm}_geometry_scope_clean"] = (
            summary["geometry_scope_violations"] == 0
        )
        method[f"{arm}_no_pending_transaction"] = (
            summary["pending_render_count"] == 0
            and summary["selector_summary"].get(
                "service_shortfall_pending_draw_attempts", 0
            )
            == 0
        )
        method[f"{arm}_equal_cardinality_ledger"] = bool(ledger) and all(
            entry["optimizer_committed"]
            and entry["mapping_iteration"]
            == entry["requested_iterations"] - 1
            and len(entry["selected_dense_uids"])
            == entry["baseline_render_count"]
            and len(set(entry["selected_dense_uids"]))
            == len(entry["selected_dense_uids"])
            and entry["requested_iterations"] > 1
            for entry in ledger
        )
        method[f"{arm}_transactional_without_replacement"] = (
            summary["selector_summary"].get(
                "service_shortfall_transactional_batch_no_repeat", 0
            )
            == 1
        )
        method[f"{arm}_removes_aux_keyframe_appearance"] = (
            not runtimes[arm]["fixed_event_keyframe_opportunity_ledger"]
            and len(
                runtimes[arm][
                    "fixed_event_dense_repeat_opportunity_ledger"
                ]
            )
            == len(
                baseline["fixed_event_keyframe_opportunity_ledger"]
            )
        )

    normalized_trace = selection_trace(runtimes["role_normalized"])
    rr_trace = selection_trace(runtimes["role_rr"])
    trace_difference = sum(
        left != right
        for left, right in zip(normalized_trace, rr_trace)
    ) + abs(len(normalized_trace) - len(rr_trace))
    method["normalized_rr_selector_is_active"] = trace_difference > 0

    report = {
        "protocol": "role_aware_dense_service_verification_v3",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "common_checks": common,
        "method_checks": method,
        "normalized_rr_trace_difference_rows": trace_difference,
    }
    report["valid"] = (
        all(value for checks in common.values() for value in checks.values())
        and all(method.values())
    )
    write_json(paths["verification"], report)
    return report


def arm_record(
    arm: str,
    paths: dict[str, Path],
    runtime: dict,
    evaluation: dict,
) -> dict:
    metrics = fixed_metrics(paths[arm])
    role = role_summary(runtime)
    return {
        "psnr": float(metrics["mean_psnr"]),
        "ssim": float(metrics["mean_ssim"]),
        "lpips": float(metrics["mean_lpips"]),
        "renders": int(runtime["rasterized_view_updates"]),
        "adam_steps": int(runtime["optimizer_steps_completed"]),
        "gaussians": int(runtime["gaussians"]),
        "mapping_wall_seconds": float(runtime["mapping_wall_seconds"]),
        "role_geometry_renders": int(role["geometry_renders_completed"]),
        "role_photometric_renders": int(
            role["photometric_renders_completed"]
        ),
        "role_photometric_share": float(
            role["photometric_render_share"]
        ),
        "role_photometric_debt": int(role["photometric_render_debt"]),
        "role_selection_count_min": int(
            role["selection_statistics"].get("selection_count_min", 0)
        ),
        "role_selection_count_max": int(
            role["selection_statistics"].get("selection_count_max", 0)
        ),
        "double_evaluation_pass": bool(evaluation["pass"]),
    }


def run_one(row: dict) -> dict:
    paths = scene_paths(row)
    V2.preflight(row, V2.scene_paths(row))
    evaluations = {}
    for arm in ("r4_backbone", "role_normalized"):
        run_mapper(arm, row, paths)
        evaluations[arm] = evaluate(arm, row, paths)

    baseline_psnr = float(fixed_metrics(paths["r4_backbone"])["mean_psnr"])
    normalized_psnr = float(
        fixed_metrics(paths["role_normalized"])["mean_psnr"]
    )
    if normalized_psnr - baseline_psnr < QUALITY_STOP_DB:
        partial = {
            "dataset": row["dataset"],
            "scene": row["scene"],
            "status": "QUALITY_STOP",
            "normalized_minus_backbone_db": normalized_psnr - baseline_psnr,
        }
        write_json(paths["result"], partial)
        raise RuntimeError(
            f"role-aware quality stop {row['dataset']}/{row['scene']}: "
            f"{normalized_psnr - baseline_psnr:+.6f} dB"
        )

    run_mapper("role_rr", row, paths)
    evaluations["role_rr"] = evaluate("role_rr", row, paths)
    verification = verify(row, paths, evaluations)
    runtimes = {
        arm: read_json(paths[arm] / "mapping_replay_runtime.json")
        for arm in ARMS
    }
    arms = {
        arm: arm_record(arm, paths, runtimes[arm], evaluations[arm])
        for arm in ARMS
    }
    result = {
        "protocol": "role_aware_dense_service_result_v3",
        "dataset": row["dataset"],
        "scene": row["scene"],
        "arms": arms,
        "normalized_minus_backbone_db": (
            arms["role_normalized"]["psnr"]
            - arms["r4_backbone"]["psnr"]
        ),
        "rr_minus_backbone_db": (
            arms["role_rr"]["psnr"] - arms["r4_backbone"]["psnr"]
        ),
        "normalized_minus_rr_db": (
            arms["role_normalized"]["psnr"] - arms["role_rr"]["psnr"]
        ),
        "normalized_rr_trace_difference_rows": verification[
            "normalized_rr_trace_difference_rows"
        ],
        "valid": bool(verification["valid"]),
    }
    write_json(paths["result"], result)
    if not result["valid"]:
        raise RuntimeError(
            f"role-aware structural gate failed: "
            f"{row['dataset']}/{row['scene']}"
        )
    return result


def write_summary(rows: list[dict]) -> None:
    completed = []
    lines = [
        "# Role-aware dense service v3 — three-family pilot",
        "",
        "One final native mapping iteration is a flexible render-credit",
        "quantum. The method spends it on an equal-cardinality causal dense",
        "RGB batch, freezes xyz/scale/rotation, and uses normalized-variance",
        "ERCB within the photometric pool. RR is the identical-work selector",
        "ablation. Every multi-view batch is sampled without replacement,",
        "and R4's auxiliary keyframe-appearance slot is reassigned to a dense",
        "repeat without minting admission credit. No scene-specific knob or",
        "phase cutoff is used. v3 supersedes v2 as the paper-aligned candidate.",
        "",
        "| Scene | Backbone | Role N | Role RR | N−B | N−RR | Photo share N/RR | Count range N | Render / Adam | Trace diff | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        path = ROOT / row["dataset"] / row["scene"] / "result.json"
        if not path.exists():
            lines.append(
                f"| {row['dataset']}/{row['scene']} | — | — | — | — | — | — | — | — | — | PENDING |"
            )
            continue
        item = read_json(path)
        if item.get("status") == "QUALITY_STOP":
            lines.append(
                f"| {row['dataset']}/{row['scene']} | — | — | — | "
                f"{item['normalized_minus_backbone_db']:+.6f} | — | — | — | — | — | QUALITY STOP |"
            )
            continue
        completed.append(item)
        arms = item["arms"]
        normalized = arms["role_normalized"]
        rr = arms["role_rr"]
        lines.append(
            f"| {item['dataset']}/{item['scene']} | "
            f"{arms['r4_backbone']['psnr']:.6f} | "
            f"{normalized['psnr']:.6f} | {rr['psnr']:.6f} | "
            f"{item['normalized_minus_backbone_db']:+.6f} | "
            f"{item['normalized_minus_rr_db']:+.6f} | "
            f"{100*normalized['role_photometric_share']:.2f}% / "
            f"{100*rr['role_photometric_share']:.2f}% | "
            f"{normalized['role_selection_count_min']}-"
            f"{normalized['role_selection_count_max']} | "
            f"{normalized['renders']} / {normalized['adam_steps']} | "
            f"{item['normalized_rr_trace_difference_rows']} | "
            f"{'PASS' if item['valid'] else 'FAIL'} |"
        )
    lines.extend(("", f"Completed scenes: **{len(completed)}/{len(rows)}**."))
    if completed:
        mean_backbone = sum(
            item["normalized_minus_backbone_db"] for item in completed
        ) / len(completed)
        mean_rr = sum(
            item["normalized_minus_rr_db"] for item in completed
        ) / len(completed)
        lines.extend(
            (
                f"Mean normalized minus backbone: **{mean_backbone:+.6f} dB**.",
                f"Mean normalized minus RR: **{mean_rr:+.6f} dB**.",
            )
        )
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run-one", "run-all"))
    parser.add_argument("--scene")
    args = parser.parse_args()
    rows = selected_rows()
    EXP94.check_evaluation_contract(rows)
    check_source_lock()

    if args.action == "preflight":
        for row in rows:
            V2.preflight(row, V2.scene_paths(row))
        write_summary(rows)
        print("role-aware dense-service preflight PASS: 3 scenes x 3 arms")
        return 0

    selected = rows
    if args.action == "run-one":
        if not args.scene or "/" not in args.scene:
            raise ValueError("--scene must be dataset/scene")
        dataset, scene = args.scene.split("/", 1)
        selected = [
            row
            for row in rows
            if (row["dataset"], row["scene"]) == (dataset, scene)
        ]
        if not selected:
            raise ValueError(f"unsupported representative scene: {args.scene}")

    for row in selected:
        result = run_one(row)
        write_summary(rows)
        print(
            f"role-aware {row['dataset']}/{row['scene']}: "
            f"N-backbone={result['normalized_minus_backbone_db']:+.6f} dB, "
            f"N-RR={result['normalized_minus_rr_db']:+.6f} dB",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
