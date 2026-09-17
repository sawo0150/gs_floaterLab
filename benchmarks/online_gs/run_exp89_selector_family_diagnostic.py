#!/usr/bin/env python3
"""RPNG table_01 normalized-potential selector-family isolation.

Diagnostic only.  This never launches the 17-scene metric panel and never
uses an old vanilla number as a paired v2 result.  Child stdout goes directly
to a regular file, matching the high-quality direct-file R4 control.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp78b_stage6rx4_cross_sequence as base
import run_exp78b_r4_all_scenes as all_scenes


ROOT = base.WORKSPACE / "results/experiments/exp89_selector_family_diagnostic"
CONTROL = (
    base.WORKSPACE / "results/experiments/exp87_normalized_variance_r4"
    / "rpng/table_01/service_shortfall_direct_s0_repeat3"
)
DATASET = "rpng"
SCENE = "table_01"
FAMILIES = ("dense", "aux_kf", "native_kf")
PROFILES = {
    "control": (),
    "dense": ("dense",),
    "aux_kf": ("aux_kf",),
    "native_kf": ("native_kf",),
    "dense_aux_kf": ("dense", "aux_kf"),
    "dense_native_kf": ("dense", "native_kf"),
    "aux_native_kf": ("aux_kf", "native_kf"),
    "all": FAMILIES,
}
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


def gpu_idle() -> None:
    active = subprocess.check_output(
        ("nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"),
        text=True,
    ).strip()
    if active:
        raise RuntimeError(f"GPU has another compute process; wait: {active}")


def run_to_file(command: list[str], log: Path) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("wb") as sink:
        subprocess.run(
            command, cwd=base.WORKSPACE, env=base.mapping_environment(True),
            stdout=sink, stderr=subprocess.STDOUT, check=True,
        )


def first_selection_difference(current: list[dict], baseline: list[dict], key: str) -> dict:
    for index, (one, two) in enumerate(zip(current, baseline)):
        if one.get(key) != two.get(key):
            return {
                "index": index,
                "event_id": one.get("event_id"),
                "map_generation": one.get("map_generation"),
                "optimizer_steps_completed": one.get("optimizer_steps_completed"),
                "candidate": one.get(key),
                "control": two.get(key),
            }
    return {"index": None, "length_candidate": len(current), "length_control": len(baseline)}


def report(family: str, output: Path) -> dict:
    current = read_json(output / "mapping_replay_runtime.json")
    baseline = read_json(CONTROL / "mapping_replay_runtime.json")
    evaluated = read_json(output / "psnr/strict_fixed_manifest/final_result.json")
    control_eval = read_json(CONTROL / "psnr/strict_fixed_manifest/final_result.json")
    checks = {
        "same_archive": current["archive_manifest_sha256"] == baseline["archive_manifest_sha256"],
        "same_config": current["effective_config_sha256"] == baseline["effective_config_sha256"],
        "same_events": current["event_ids_fully_processed"] == baseline["event_ids_fully_processed"],
        "same_adam": current["optimizer_steps_completed"] == baseline["optimizer_steps_completed"],
        "same_renders": current["rasterized_view_updates"] == baseline["rasterized_view_updates"],
        "same_dense_admission": current["dense_registered_frame_uids"] == baseline["dense_registered_frame_uids"],
        "zero_tail": current["post_eos_optimizer_updates"] == 0,
        "heldout_disjoint": current["heldout_mapping_overlap_count"] == 0 and current["heldout_gaussian_origin_overlap_count"] == 0,
        "requested_family_profile": current["ercb_selection_potential_by_family"] == {
            name: "normalized_variance" if name in PROFILES[family] else "service_shortfall"
            for name in FAMILIES
        },
        "same_dense_opportunities": [
            {field: item.get(field) for field in OPPORTUNITY_FIELDS}
            for item in current["fixed_event_dense_opportunity_ledger"]
        ] == [
            {field: item.get(field) for field in OPPORTUNITY_FIELDS}
            for item in baseline["fixed_event_dense_opportunity_ledger"]
        ],
    }
    ledgers = {
        "dense": ("fixed_event_dense_opportunity_ledger", "selected_keys"),
        "aux_kf": ("fixed_event_keyframe_opportunity_ledger", "selected_keys"),
        "native_kf": ("stage6r_native_global_keyframe_selection_ledger", "selected_uids"),
    }
    differences = {}
    for name, (ledger, key) in ledgers.items():
        one, two = current[ledger], baseline[ledger]
        differences[name] = {
            "different_rows": sum(a.get(key) != b.get(key) for a, b in zip(one, two)),
            "row_count_candidate": len(one),
            "row_count_control": len(two),
            "first": first_selection_difference(one, two, key),
        }
    psnr = evaluated["predeclared_fixed_manifest_posthoc"]["mean_psnr"]
    old = control_eval["predeclared_fixed_manifest_posthoc"]["mean_psnr"]
    result = {
        "family": family,
        "candidate": str(output),
        "control": str(CONTROL),
        "psnr": psnr,
        "control_psnr": old,
        "delta_db": psnr - old,
        "checks": checks,
        "first_selection_differences": differences,
        "candidate_adam": current["optimizer_steps_completed"],
        "candidate_renders": current["rasterized_view_updates"],
        "source_sha256": {
            str(path): sha256(path)
            for path in (
                base.CUSTOM_HARNESS, base.PAPER_ROOT / "vigs/gs_backend.py",
                base.PAPER_ROOT / "vigs/map_scheduler.py", base.EVALUATOR, Path(__file__),
            )
        },
    }
    write_json(output / "diagnostic_report.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", choices=tuple(PROFILES), required=True)
    parser.add_argument("--venue", choices=("exp89", "exp88_sibling"), default="exp89")
    args = parser.parse_args()
    all_scenes.install_extension()
    family = args.family
    paths = base.sequence_paths(DATASET, SCENE)
    output = ROOT / DATASET / SCENE / f"profile_{family}_s0"
    if family in FAMILIES:
        # Preserve the paths of the three already-completed single-family runs.
        output = ROOT / DATASET / SCENE / f"normalized_{family}_s0"
    if args.venue == "exp88_sibling":
        if family != "all":
            raise ValueError("exp88 sibling reproduction is only for the all-family profile")
        output = (
            base.WORKSPACE / "results/experiments/exp88_normalized_metric_v2"
            / DATASET / SCENE / "normalized_variance_s0_repro1"
        )
    if sha256(paths["fixed_manifest"]) != base.SEQUENCES[(DATASET, SCENE)][2]:
        raise RuntimeError("fixed held-out manifest changed")
    if sha256(paths["archive"] / "archive_manifest.json") != base.SEQUENCES[(DATASET, SCENE)][3]:
        raise RuntimeError("frozen archive changed")
    if not (CONTROL / "psnr/strict_fixed_manifest/final_result.json").is_file():
        raise FileNotFoundError(CONTROL)
    if not (output / "mapping_replay_runtime.json").exists():
        if output.exists():
            raise FileExistsError(f"incomplete output exists; inspect before retry: {output}")
        gpu_idle()
        command = base.mapping_command("candidate", DATASET, SCENE, ROOT)
        command[command.index("--output") + 1] = str(output)
        if family == "all":
            command.extend(("--ercb-selection-potential", "normalized_variance"))
        else:
            for name in PROFILES[family]:
                command.extend(("--ercb-normalized-family", name))
        write_json(output / "mapping_command.json", command)
        run_to_file(command, output / "mapping.log")
    if not (output / "psnr/strict_fixed_manifest/final_result.json").exists():
        gpu_idle()
        command = base.evaluation_command(output, DATASET, SCENE)
        write_json(output / "evaluation_command.json", command)
        run_to_file(command, output / "evaluation.log")
    result = report(family, output)
    print(json.dumps({key: result[key] for key in ("family", "psnr", "control_psnr", "delta_db", "checks", "first_selection_differences")}, indent=2))
    if not all(result["checks"].values()):
        raise RuntimeError("diagnostic fairness check failed")


if __name__ == "__main__":
    main()
