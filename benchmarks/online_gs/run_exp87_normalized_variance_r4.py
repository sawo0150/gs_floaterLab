#!/usr/bin/env python3
"""Three-family R4 selector-only normalized-variance ablation.

This deliberately bypasses the hash-locked R4 promotion runner: the mapper
source and replay adapter contain an opt-in experimental selector.  It reuses
the same frozen archives, split manifests, configs, service quota and eval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import run_exp78b_stage6rx4_cross_sequence as base
import run_exp78b_r4_all_scenes as all_scenes
import run_exp78b_r4_aria as aria


ROOT = base.WORKSPACE / "results/experiments/exp87_normalized_variance_r4"
BASELINE = {
    ("utmm", "fast-straight"): (
        base.WORKSPACE / "results/experiments/exp78/paper_full_staged_v1"
        / "stage6rx4_cross_sequence_confirmation/utmm/fast-straight/stage6rx4_r4_full_s0"
    ),
    ("utmm", "square-1"): (
        base.WORKSPACE / "results/experiments/exp78/paper_full_staged_v1"
        / "stage6rx4_cross_sequence_confirmation/utmm/square-1/stage6rx4_r4_full_s0"
    ),
    ("rpng", "table_01"): (
        base.WORKSPACE / "results/experiments/exp78/paper_full_staged_v1"
        / "stage6r_r4_native_global_keyframe/rpng/table_01/r4_native_global_keyframe_ercb_s0"
    ),
    ("aria", "aria1253"): (
        base.WORKSPACE / "results/experiments/exp78/paper_full_staged_v1"
        / "stage6r_all_scenes_fixed_work/aria/aria1253/stage6rx4_r4_full_s0"
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate_output(
    dataset: str,
    sequence: str,
    control_replay: bool,
    repeat_index: int,
    unbounded_cache: bool,
) -> Path:
    label = "service_shortfall_replay_s0" if control_replay else "normalized_variance_s0"
    if unbounded_cache:
        label += "_legacy_cache"
    if repeat_index:
        label += f"_repeat{repeat_index}"
    return ROOT / dataset / sequence / label


def opportunity_skeleton(rows: list[dict]) -> list[dict]:
    fields = (
        "event_id",
        "map_generation",
        "opportunity_index",
        "optimizer_steps_completed",
        "rasterized_view_updates",
        "pool_uids_before",
        "completed_dense_service_before",
        "completed_dense_service_after",
    )
    return [{field: row.get(field) for field in fields} for row in rows]


def run(
    dataset: str,
    sequence: str,
    verify_existing: bool = False,
    control_replay: bool = False,
    repeat_index: int = 0,
    unbounded_cache: bool = False,
) -> None:
    key = (dataset, sequence)
    if key not in BASELINE:
        raise ValueError(f"unsupported predeclared ablation scene: {key}")
    all_scenes.install_extension()
    aria.install_extension()
    paths = base.sequence_paths(dataset, sequence)
    _, _, fixed_hash, archive_hash = base.SEQUENCES[key]
    if sha256(paths["fixed_manifest"]) != fixed_hash:
        raise RuntimeError("fixed held-out manifest changed")
    if sha256(paths["archive"] / "archive_manifest.json") != archive_hash:
        raise RuntimeError("frozen tracker archive changed")
    baseline = BASELINE[key]
    for name in ("mapping_replay_runtime.json", "psnr/strict_fixed_manifest/final_result.json"):
        if not (baseline / name).is_file():
            raise FileNotFoundError(baseline / name)
    output = candidate_output(
        dataset, sequence, control_replay, repeat_index, unbounded_cache
    )
    if output.exists() and not verify_existing:
        raise FileExistsError(f"refusing to overwrite {output}")
    command = base.mapping_command("candidate", dataset, sequence, ROOT)
    command[command.index("--output") + 1] = str(output)
    if not control_replay:
        command.extend(("--ercb-selection-potential", "normalized_variance"))
    if unbounded_cache:
        command.extend(("--archive-cache-max-entries", "100000000"))
    evaluation = base.evaluation_command(output, dataset, sequence)
    if not verify_existing:
        base.run_logged(command, output / "mapping.log", base.mapping_environment(True))
        base.run_logged(evaluation, output / "evaluation.log", base.mapping_environment(True))
    current = json.loads((output / "mapping_replay_runtime.json").read_text())
    previous = json.loads((baseline / "mapping_replay_runtime.json").read_text())
    metrics = json.loads((output / "psnr/strict_fixed_manifest/final_result.json").read_text())
    previous_metrics = json.loads((baseline / "psnr/strict_fixed_manifest/final_result.json").read_text())
    fields = (
        "archive_manifest_sha256",
        "event_ids_fully_processed",
        "optimizer_steps_completed",
        "rasterized_view_updates",
        "dense_registered_frame_uids",
        "post_eos_optimizer_updates",
        "heldout_mapping_overlap_count",
        "heldout_gaussian_origin_overlap_count",
    )
    parity = {field: current[field] == previous[field] for field in fields}
    parity["dense_opportunity_skeleton"] = opportunity_skeleton(
        current["fixed_event_dense_opportunity_ledger"]
    ) == opportunity_skeleton(previous["fixed_event_dense_opportunity_ledger"])
    parity["keyframe_opportunity_skeleton"] = opportunity_skeleton(
        current["fixed_event_keyframe_opportunity_ledger"]
    ) == opportunity_skeleton(previous["fixed_event_keyframe_opportunity_ledger"])
    result = {
        "dataset": dataset,
        "sequence": sequence,
        "selector": (
            "service_shortfall_control_replay" if control_replay
            else "normalized_variance_per_view"
        ),
        "gamma": "log(1.5)",
        "legacy_unbounded_geometry_cache": unbounded_cache,
        "formula": (
            "original interval-relative service shortfall"
            if control_replay else
            "log_weight_i = -gamma * n_i / (T+1), up to a common offset"
        ),
        "baseline": str(baseline),
        "candidate": str(output),
        "baseline_psnr": previous_metrics["predeclared_fixed_manifest_posthoc"]["mean_psnr"],
        "candidate_psnr": metrics["predeclared_fixed_manifest_posthoc"]["mean_psnr"],
        "parity": parity,
        "source_sha256": {
            str(path): sha256(path)
            for path in (
                base.CUSTOM_HARNESS,
                base.PAPER_ROOT / "vigs/map_scheduler.py",
                base.PAPER_ROOT / "vigs/gs_backend.py",
                Path(__file__),
            )
        },
        "mapping_command": command,
        "evaluation_command": evaluation,
    }
    result["delta_psnr"] = result["candidate_psnr"] - result["baseline_psnr"]
    report_path = output / ("ablation_pair_verified.json" if verify_existing else "ablation_pair.json")
    report_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if not all(parity.values()):
        raise RuntimeError("selector-only fixed-work parity failed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", choices=("utmm", "rpng", "aria"))
    parser.add_argument("sequence")
    parser.add_argument("--verify-existing", action="store_true")
    parser.add_argument("--control-replay", action="store_true")
    parser.add_argument("--repeat-index", type=int, default=0)
    parser.add_argument("--unbounded-cache", action="store_true")
    args = parser.parse_args()
    run(
        args.dataset,
        args.sequence,
        args.verify_existing,
        args.control_replay,
        args.repeat_index,
        args.unbounded_cache,
    )


if __name__ == "__main__":
    main()
