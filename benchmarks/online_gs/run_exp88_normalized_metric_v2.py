#!/usr/bin/env python3
"""Fail-fast B-track metric v2: normalized ERCB versus native vanilla.

The child mapper writes stdout directly to a regular file.  Do not route it
through the line-forwarding run_logged helper: exp87 RPNG table_01 showed a
large, still-unexplained quality split between that launcher and direct file
redirection despite identical source, selected views, and completed work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import run_exp78b_stage6rx4_cross_sequence as base
import run_exp78b_r4_all_scenes as all_scenes
import run_exp78b_r4_aria as aria


ROOT = base.WORKSPACE / "results/experiments/exp88_normalized_metric_v2"
HISTORICAL = (
    base.WORKSPACE
    / "context/experiments/benchmark_custom/r4_all_scenes_fixed_work_20260915/provenance.json"
)
SOURCE_PATHS = (
    base.CUSTOM_HARNESS,
    base.VANILLA_HARNESS,
    base.EVALUATOR,
    base.WORKSPACE / "benchmarks/online_gs/exp78b_frozen_archive.py",
    base.PAPER_ROOT / "vigs/gs_backend.py",
    base.PAPER_ROOT / "vigs/map_scheduler.py",
    Path(__file__),
)
MAX_R4_DROP_DB = 0.5
OPPORTUNITY_FIELDS = (
    "event_id", "map_generation", "opportunity_index",
    "optimizer_steps_completed", "rasterized_view_updates",
    "pool_uids_before", "completed_dense_service_before",
    "completed_dense_service_after",
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources() -> dict[str, str]:
    return {str(path): sha256(path) for path in SOURCE_PATHS}


def install_inventory() -> list[dict]:
    all_scenes.install_extension()
    aria.install_extension()
    rows = read_json(HISTORICAL)["pairs"]
    if len(rows) != 17 or len({(row["dataset"], row["scene"]) for row in rows}) != 17:
        raise RuntimeError("historical 17-scene inventory changed")
    return rows


def scene_paths(row: dict) -> dict[str, Path]:
    dataset, scene = row["dataset"], row["scene"]
    base_paths = base.sequence_paths(dataset, scene)
    local = ROOT / dataset / scene
    return {
        **base_paths,
        "candidate": local / "normalized_variance_s0",
        "vanilla": local / "native_vanilla_render_matched_s0",
        "pair": local / "pair_verification.json",
        "gate": local / "quality_gate.json",
        "historical_candidate": base.WORKSPACE / row["candidate_run"],
        "historical_vanilla": base.WORKSPACE / row["vanilla_run"],
    }


def check_source_lock() -> None:
    path = ROOT / "source_lock.json"
    current = sources()
    if path.exists():
        if read_json(path)["sha256"] != current:
            raise RuntimeError("v2 source changed after the first run; stop the panel")
    else:
        write_json(path, {"protocol": "exp88_normalized_metric_v2", "sha256": current})


def preflight(row: dict, paths: dict[str, Path]) -> None:
    dataset, scene = row["dataset"], row["scene"]
    if (dataset, scene) not in base.SEQUENCES:
        raise RuntimeError(f"not in frozen B-track inventory: {dataset}/{scene}")
    _, views, fixed_hash, archive_hash = base.SEQUENCES[(dataset, scene)]
    if sha256(paths["fixed_manifest"]) != fixed_hash:
        raise RuntimeError("fixed held-out manifest changed")
    if sha256(paths["archive"] / "archive_manifest.json") != archive_hash:
        raise RuntimeError("tracker archive manifest changed")
    historical = read_json(paths["historical_candidate"] / "mapping_replay_runtime.json")
    if historical["config_sha256"] != sha256(paths["custom_config"]):
        raise RuntimeError("custom config changed")
    for arm in ("historical_candidate", "historical_vanilla"):
        result = read_json(paths[arm] / "psnr/strict_fixed_manifest/final_result.json")
        if result["predeclared_fixed_manifest_posthoc"]["view_count"] != views:
            raise RuntimeError(f"historical {arm} fixed view count changed")


def gpu_idle() -> None:
    command = ["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"]
    active = subprocess.check_output(command, text=True).strip()
    if active:
        raise RuntimeError(f"GPU has another compute process; wait without terminating it: {active}")


def run_to_file(command: list[str], log: Path, *, custom: bool) -> None:
    """Regular-file stdout is a predeclared v2 condition, not a convenience."""
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("wb") as sink:
        subprocess.run(
            command, cwd=base.WORKSPACE, env=base.mapping_environment(custom),
            stdout=sink, stderr=subprocess.STDOUT, check=True,
        )


def opportunity_skeleton(runtime: dict, key: str) -> list[dict]:
    return [
        {field: record.get(field) for field in OPPORTUNITY_FIELDS}
        for record in runtime[key]
    ]


def quality_gate(row: dict, paths: dict[str, Path]) -> dict:
    current = read_json(paths["candidate"] / "mapping_replay_runtime.json")
    historical = read_json(paths["historical_candidate"] / "mapping_replay_runtime.json")
    evaluation = read_json(paths["candidate"] / "psnr/strict_fixed_manifest/final_result.json")
    old_eval = read_json(paths["historical_candidate"] / "psnr/strict_fixed_manifest/final_result.json")
    old_vanilla = read_json(paths["historical_vanilla"] / "psnr/strict_fixed_manifest/final_result.json")
    checks = {
        "normalized_selector": current.get("ercb_selection_potential") == "normalized_variance",
        "same_archive": current["archive_manifest_sha256"] == historical["archive_manifest_sha256"],
        "same_config": current["effective_config_sha256"] == historical["effective_config_sha256"],
        "same_events": current["event_ids_fully_processed"] == historical["event_ids_fully_processed"],
        "same_render_work": current["rasterized_view_updates"] == historical["rasterized_view_updates"],
        "same_adam_work": current["optimizer_steps_completed"] == historical["optimizer_steps_completed"],
        "same_dense_admission": current["dense_registered_frame_uids"] == historical["dense_registered_frame_uids"],
        "same_dense_opportunities": opportunity_skeleton(current, "fixed_event_dense_opportunity_ledger") == opportunity_skeleton(historical, "fixed_event_dense_opportunity_ledger"),
        "same_keyframe_opportunities": opportunity_skeleton(current, "fixed_event_keyframe_opportunity_ledger") == opportunity_skeleton(historical, "fixed_event_keyframe_opportunity_ledger"),
        "zero_tail": current["post_eos_optimizer_updates"] == 0,
        "mapping_disjoint": current["heldout_mapping_overlap_count"] == 0 and current["heldout_gaussian_origin_overlap_count"] == 0,
        "fixed_heldout": evaluation["predeclared_fixed_manifest_posthoc"]["mapping_disjoint"] and evaluation["predeclared_fixed_manifest_posthoc"]["view_count"] == old_eval["predeclared_fixed_manifest_posthoc"]["view_count"],
    }
    psnr = evaluation["predeclared_fixed_manifest_posthoc"]["mean_psnr"]
    old_psnr = old_eval["predeclared_fixed_manifest_posthoc"]["mean_psnr"]
    vanilla_psnr = old_vanilla["predeclared_fixed_manifest_posthoc"]["mean_psnr"]
    drop = old_psnr - psnr
    stopped = not all(checks.values()) or drop > MAX_R4_DROP_DB
    report = {
        "protocol": "exp88_v2_fail_fast_quality_gate",
        "dataset": row["dataset"], "scene": row["scene"],
        "checks": checks, "normalized_psnr": psnr,
        "historical_r4_psnr": old_psnr, "historical_vanilla_psnr": vanilla_psnr,
        "r4_drop_db": drop, "historical_vanilla_gain_db": psnr - vanilla_psnr,
        "catastrophic_drop_threshold_db": MAX_R4_DROP_DB,
        "stop": stopped,
        "stop_reason": "invariant failure or >0.5 dB R4 drop" if stopped else None,
    }
    write_json(paths["gate"], report)
    return report


def run_one(row: dict) -> dict:
    paths = scene_paths(row)
    preflight(row, paths)
    check_source_lock()
    dataset, scene = row["dataset"], row["scene"]
    candidate = paths["candidate"]
    if not (candidate / "mapping_replay_runtime.json").exists():
        gpu_idle()
        command = base.mapping_command("candidate", dataset, scene, ROOT)
        command[command.index("--output") + 1] = str(candidate)
        command.extend(("--ercb-selection-potential", "normalized_variance"))
        write_json(candidate / "mapping_command.json", command)
        run_to_file(command, candidate / "mapping.log", custom=True)
    if not (candidate / "psnr/strict_fixed_manifest/final_result.json").exists():
        gpu_idle()
        run_to_file(base.evaluation_command(candidate, dataset, scene), candidate / "evaluation.log", custom=True)
    gate = quality_gate(row, paths)
    print(f"{dataset}/{scene}: normalized {gate['normalized_psnr']:.4f}, historical R4 {gate['historical_r4_psnr']:.4f}, old vanilla {gate['historical_vanilla_psnr']:.4f}; stop={gate['stop']}", flush=True)
    if gate["stop"]:
        raise RuntimeError(f"quality gate stopped the panel at {dataset}/{scene}: {gate['stop_reason']}")
    vanilla = paths["vanilla"]
    if not (vanilla / "mapping_replay_runtime.json").exists():
        gpu_idle()
        command = base.mapping_command("vanilla", dataset, scene, ROOT)
        command[command.index("--output") + 1] = str(vanilla)
        command[command.index("--reference-service-runtime") + 1] = str(candidate / "mapping_replay_runtime.json")
        write_json(vanilla / "mapping_command.json", command)
        run_to_file(command, vanilla / "mapping.log", custom=False)
    if not (vanilla / "psnr/strict_fixed_manifest/final_result.json").exists():
        gpu_idle()
        run_to_file(base.evaluation_command(vanilla, dataset, scene), vanilla / "evaluation.log", custom=False)
    if not paths["pair"].exists():
        command = [
            str(base.PYTHON_ENV / "bin/python"),
            str(base.RENDER_VERIFIER),
            "--d1-run", str(candidate), "--vanilla-run", str(vanilla),
            "--output", str(paths["pair"]),
        ]
        subprocess.run(command, cwd=base.WORKSPACE, check=True, stdout=subprocess.DEVNULL)
    pair = read_json(paths["pair"])
    if not pair.get("valid"):
        raise RuntimeError(f"render-matched pair verification failed: {dataset}/{scene}")
    return {"dataset": dataset, "scene": scene, "gate": gate, "pair": pair["result"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "run-one", "run-all"))
    parser.add_argument("--dataset", choices=("rpng", "utmm", "aria"))
    parser.add_argument("--scene")
    args = parser.parse_args()
    rows = install_inventory()
    if args.action == "preflight":
        for row in rows:
            preflight(row, scene_paths(row))
        check_source_lock()
        print(f"v2 preflight PASS: {len(rows)} eligible scenes; UTMM slow-straight-1 N/A")
        return 0
    if args.action == "run-one":
        rows = [row for row in rows if (row["dataset"], row["scene"]) == (args.dataset, args.scene)]
        if len(rows) != 1:
            raise ValueError("run-one requires one valid --dataset/--scene")
    for row in rows:
        run_one(row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
