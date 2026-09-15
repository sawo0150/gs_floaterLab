#!/usr/bin/env python3
"""Prepare every valid exp80 benchmark scene using the historical exp03 builder.

The builder is deliberately pinned to the exp77 reproduction worktree.  It does
not append a synthetic sensor-EOS boundary, matching the schedule semantics that
produced the historical low-budget +1 dB RPNG result.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REPO = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom-exp77-budget-5070ti-repro")
BUILDER = REPO / "scripts/incremental/build_vigs_benchmark_causal_dataset.py"
PYTHON = Path("/home/wosas/miniconda3/envs/3dgs/bin/python")
SOURCE_ROOT = ROOT / "data/benchmarks/vigs_sources/fixed1x_5090_exp80"
OUTPUT_ROOT = ROOT / "data/benchmarks/ercb_benchmark_A_replay_v2"

SCENES = {
    "utmm": (
        "ego-centric-1", "ego-centric-2", "ego-drive", "fast-straight",
        "slow-straight-2", "square-1", "square-2",
    ),
    "rpng": (
        "table_01", "table_02", "table_03", "table_04", "table_05", "table_06",
    ),
}

UNAVAILABLE = {
    "utmm/slow-straight-1": "VIGS mapping initialization failed; no full pose/init export",
    "rpng/table_07": "VIGS PGBA failed; no full pose trajectory/keyframe export",
    "rpng/table_08": "VIGS OOM; no full pose trajectory/keyframe export",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def valid_dataset(path: Path) -> bool:
    required = (
        path / "causal_arrivals.json",
        path / "vigs_replay_metadata.json",
        path / "sparse/0/cameras.txt",
        path / "sparse/0/images.txt",
        path / "sparse/0/points3D.txt",
    )
    if not all(item.is_file() for item in required) or not (path / "images").is_dir():
        return False
    metadata = json.loads((path / "vigs_replay_metadata.json").read_text())
    schedule = json.loads((path / "causal_arrivals.json").read_text())
    return (
        metadata.get("iters_per_event") == 60
        and metadata.get("tail_iters") == 0
        and schedule.get("tail_iters") == 0
        and len(schedule.get("arrival_iteration_by_name", {}))
        == metadata.get("train_frames")
    )


def main() -> None:
    if not BUILDER.is_file() or not PYTHON.is_file():
        raise FileNotFoundError(f"missing pinned builder/python: {BUILDER}, {PYTHON}")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    records = []
    for family, scenes in SCENES.items():
        prepared_root = ROOT / "data/benchmarks" / family / "prepared" / (
            "UTMM_Dataset" if family == "utmm" else "rpngar"
        )
        for scene in scenes:
            output = OUTPUT_ROOT / family / scene
            source = prepared_root / scene
            vigs_run = SOURCE_ROOT / family / scene / "seed0"
            required_source = (
                vigs_run / "traj_full_online_eval.txt",
                vigs_run / "traj_kf_beforeBA.txt",
                vigs_run / "points3D.txt",
            )
            if valid_dataset(output):
                state = "reused_valid"
            else:
                if output.exists():
                    raise RuntimeError(f"incomplete dataset exists; refusing overwrite: {output}")
                if not source.is_dir() or not all(path.is_file() for path in required_source):
                    raise FileNotFoundError(f"missing input for {family}/{scene}: {source}, {vigs_run}")
                subprocess.run(
                    [
                        str(PYTHON), str(BUILDER), "--kind", family,
                        "--input", str(source), "--vigs-run", str(vigs_run),
                        "--output", str(output), "--iters-per-event", "60",
                    ],
                    check=True,
                )
                if not valid_dataset(output):
                    raise RuntimeError(f"dataset postcondition failed: {output}")
                state = "built"
            metadata = json.loads((output / "vigs_replay_metadata.json").read_text())
            records.append({
                "family": family,
                "scene": scene,
                "state": state,
                "dataset": str(output),
                "events": metadata["events"],
                "train_frames": metadata["train_frames"],
                "heldout_frames": metadata["heldout_frames"],
                "source": str(source),
                "vigs_run": str(vigs_run),
            })
            print(f"{state.upper()} {family}/{scene}", flush=True)
    inventory = {
        "protocol": "benchmark-A historical exp03 replay dataset",
        "builder": str(BUILDER),
        "builder_sha256": sha256(BUILDER),
        "builder_repo_head": subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True
        ).strip(),
        "historical_tail_admission_semantics": True,
        "records": records,
        "unavailable": UNAVAILABLE,
    }
    evidence = HERE / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "dataset_inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    print(evidence / "dataset_inventory.json")


if __name__ == "__main__":
    main()
