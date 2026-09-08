#!/usr/bin/env python3
"""Aggregate exp75 held-out quality and scheduler diagnostics.

Every complete rendered checkpoint is reported.  The JSON output is regenerated
after each render batch so the endpoint and anytime/crossover claims can both be
audited against machine-readable evidence.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REPO = Path("/home/intern/gs_floaterLab/repos/main/3dgs-custom")
sys.path.insert(0, str(REPO))
from runtime.scheduler import make_scheduler  # noqa: E402


def heldout_psnr_values(run: Path, iteration: int = 30000) -> np.ndarray:
    root = run / "test" / f"ours_{iteration}"
    renders = sorted((root / "renders").glob("*.png"))
    gt = sorted((root / "gt").glob("*.png"))
    if not renders or len(renders) != len(gt):
        raise FileNotFoundError(f"incomplete render set: {run} ({len(renders)} vs {len(gt)})")
    values = []
    for rendered, target in zip(renders, gt):
        a = np.asarray(Image.open(rendered), dtype=np.float32) / 255.0
        b = np.asarray(Image.open(target), dtype=np.float32) / 255.0
        values.append(float(-10.0 * np.log10(np.mean((a - b) ** 2))))
    return np.asarray(values, dtype=np.float64)


def heldout_psnr(run: Path, iteration: int = 30000) -> tuple[float, list[float], int]:
    values = heldout_psnr_values(run, iteration)
    thirds = [float(np.mean(part)) for part in np.array_split(values, 3)]
    return float(np.mean(values)), thirds, len(values)


def scheduler_replay(summary: dict) -> tuple[list[int], list[list[int]]]:
    names = list(summary["selection_count"])
    arrivals = list(summary["arrival_iteration"].values())
    scheduler = make_scheduler(
        summary["name"], summary.get("seed", 0), summary.get("beta", 0.0),
        summary.get("block_size", 128), summary.get("phase_start", 0),
    )
    history: list[int] = []
    native_blocks: list[list[int]] = []
    block: list[int] = []
    next_arrival = 0
    total = int(summary["total_iterations"])
    for iteration in range(1, total + 1):
        added = []
        while next_arrival < len(names) and arrivals[next_arrival] <= iteration:
            added.append(next_arrival)
            next_arrival += 1
        was_weighted = getattr(scheduler, "weighted_phase", False)
        was_staged = getattr(scheduler, "staged_phase", False)
        scheduler.add(added)
        is_weighted = getattr(scheduler, "weighted_phase", False)
        is_staged = getattr(scheduler, "staged_phase", False)
        if summary["name"] == "stable_pool_block_rr" and is_weighted and not was_weighted:
            block = []
        if summary["name"] in (
            "staged_interval_size_softmax_rr",
            "staged_bounded_interval_size_softmax_rr",
            "staged_two_pass_interval_size_softmax_rr",
        ) and is_staged and not was_staged:
            block = []
        block_scheduler = summary["name"] in (
            "block_weighted_rr", "entropy_floor_rr", "interval_softmax_rr",
            "interval_size_softmax_rr", "normalized_interval_size_softmax_rr",
            "bounded_interval_size_softmax_rr",
            "two_pass_interval_size_softmax_rr",
            "relative_floor_interval_softmax_rr",
        ) or is_weighted or (
            summary["name"] in (
                "staged_interval_size_softmax_rr",
                "staged_bounded_interval_size_softmax_rr",
                "staged_two_pass_interval_size_softmax_rr",
            ) and is_staged
        )
        starts_block = block_scheduler and not scheduler.remaining
        if starts_block and block:
            native_blocks.append(block)
            block = []
        selected = scheduler.draw()
        history.append(selected)
        block.append(selected)
    if block:
        native_blocks.append(block)
    return history, native_blocks


def entropy_ratio(values: np.ndarray, pool_size: int, bins: int = 16) -> float:
    hist = np.bincount(np.minimum(values * bins // pool_size, bins - 1), minlength=bins)
    p = hist[hist > 0] / len(values)
    return float(-(p * np.log(p)).sum() / math.log(bins))


def scheduler_metrics(summary: dict) -> dict:
    counts = np.asarray(list(summary["selection_count"].values()), dtype=np.float64)
    history, native_blocks = scheduler_replay(summary)
    arrivals = np.asarray(list(summary["arrival_iteration"].values()))
    tail = np.asarray(history[max(arrivals) - 1 :], dtype=np.int64)
    chunks = np.array_split(tail, max(1, math.ceil(len(tail) / 128)))
    entropy = float(np.mean([entropy_ratio(c, len(counts)) for c in chunks if len(c)]))
    duplicate_blocks = sum(len(b) != len(set(b)) for b in native_blocks)
    result = {
        "count_cv": float(counts.std() / counts.mean()),
        "count_min": int(counts.min()),
        "count_max": int(counts.max()),
        "count_temporal_thirds": [float(np.mean(x)) for x in np.array_split(counts, 3)],
        "tail_block128_temporal_entropy_ratio": entropy,
        "tail_updates": int(len(tail)),
        "native_blocks": len(native_blocks),
        "native_blocks_with_duplicates": duplicate_blocks,
    }
    if "interval_selection_count" in summary:
        interval_counts = np.asarray(
            list(summary["interval_selection_count"].values()), dtype=np.float64
        )
        frame_interval = {
            frame_id: int(summary["frame_interval_id"][name])
            for frame_id, name in enumerate(summary["selection_count"])
        }
        interval_blocks = [[frame_interval[item] for item in block] for block in native_blocks]
        interval_duplicates = sum(len(block) != len(set(block)) for block in interval_blocks)
        interval_entropies = []
        for block in interval_blocks:
            if len(block) <= 1:
                continue
            _, frequencies = np.unique(block, return_counts=True)
            probabilities = frequencies / len(block)
            interval_entropies.append(
                float(-(probabilities * np.log(probabilities)).sum() / math.log(len(block)))
            )
        result.update({
            "interval_count_cv": float(interval_counts.std() / interval_counts.mean()),
            "interval_count_min": int(interval_counts.min()),
            "interval_count_max": int(interval_counts.max()),
            "native_blocks_with_interval_duplicates": interval_duplicates,
            "native_block_interval_entropy_ratio": float(np.mean(interval_entropies)),
        })
    return result


def checkpoint_scheduler_metrics(
    summary: dict, history: list[int], iteration: int
) -> dict:
    """Exposure and recent mixing diagnostics available at one checkpoint."""
    arrivals = np.asarray(list(summary["arrival_iteration"].values()), dtype=np.int64)
    eligible = arrivals <= iteration
    pool_size = int(eligible.sum())
    selected = np.asarray(history[:iteration], dtype=np.int64)
    counts = np.bincount(selected, minlength=len(arrivals))[eligible].astype(np.float64)
    recent = selected[max(0, iteration - 1024) : iteration]
    return {
        "eligible_pool_size": pool_size,
        "count_cv": float(counts.std() / counts.mean()),
        "count_min": int(counts.min()),
        "count_max": int(counts.max()),
        "unselected_fraction": float(np.mean(counts == 0)),
        "recent1024_temporal_entropy_ratio": entropy_ratio(recent, pool_size),
    }


def parse_run(run: Path) -> dict:
    summary = json.loads((run / "view_scheduler_summary.json").read_text())
    history, _ = scheduler_replay(summary)
    checkpoint_results = {}
    for render_root in sorted((run / "test").glob("ours_*")):
        match = re.fullmatch(r"ours_(\d+)", render_root.name)
        if match is None:
            continue
        iteration = int(match.group(1))
        try:
            values = heldout_psnr_values(run, iteration)
        except FileNotFoundError:
            continue
        mean = float(np.mean(values))
        thirds = [float(np.mean(part)) for part in np.array_split(values, 3)]
        n = len(values)
        q1_size = int(math.ceil(n * .25))
        checkpoint_results[str(iteration)] = {
            "heldout_psnr": mean,
            "heldout_psnr_temporal_thirds": thirds,
            "heldout_psnr_worst_q1": float(np.mean(np.sort(values)[:q1_size])),
            "heldout_views": n,
            **checkpoint_scheduler_metrics(summary, history, iteration),
        }
    if not checkpoint_results:
        raise FileNotFoundError(f"no complete checkpoints: {run}")
    preferred = checkpoint_results.get("30000", checkpoint_results[max(checkpoint_results, key=int)])
    out = {
        "scene": run.name.split("_", 1)[0].removeprefix("aria"),
        "scheduler": summary["name"],
        "K": int(summary.get("block_size", 128)),
        "beta": float(summary.get("beta", 0.0)),
        # Backward-compatible 30k fields for the earlier exp75 tables.
        "heldout_psnr": preferred["heldout_psnr"],
        "heldout_psnr_temporal_thirds": preferred["heldout_psnr_temporal_thirds"],
        "heldout_views": preferred["heldout_views"],
        "checkpoints": checkpoint_results,
    }
    out.update(scheduler_metrics(summary))
    return out


def main() -> None:
    roots = [HERE / "evidence" / name for name in
             ("runs", "block_runs", "transfer_runs", "stable_runs", "floor_runs",
              "saturation_runs", "anytime_runs", "interval_runs", "external_runs",
              "shared_branch", "zero_tail_runs")]
    runs = []
    for root in roots:
        if root.exists():
            runs.extend(p for p in root.iterdir() if p.is_dir())
    result = {}
    for run in sorted(runs):
        if "_shared_loss_" in run.name:
            continue
        render_dirs = list((run / "test").glob("ours_*/renders"))
        if render_dirs:
            result[run.name] = parse_run(run)
    output = HERE / "evidence" / "exp75_results.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
