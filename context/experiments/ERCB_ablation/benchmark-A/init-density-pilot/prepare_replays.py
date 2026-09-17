#!/usr/bin/env python3
"""Build paired stride40/stride20 replay datasets and the low-budget manifest."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
VIGS_REPO = Path(
    "/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-main-integration-20260828"
)
GS_REPO = Path(
    "/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom-exp77-budget-5070ti-repro"
)
BUILDER = GS_REPO / "scripts/incremental/build_vigs_benchmark_causal_dataset.py"
PYTHON = Path("/home/wosas/miniconda3/envs/3dgs/bin/python")
SOURCE_ROOT = ROOT / "results/ERCB_ablation/benchmark-A_init_density_source"
DATA_ROOT = ROOT / "data/benchmarks/ercb_benchmark_A_init_density_pilot"
RESULT_ROOT = ROOT / "results/ERCB_ablation/benchmark-A_init_density_pilot"
BUDGET = 15
SEED = 0
SCENES = (
    ("utmm", "square-1", "UTMM_Dataset"),
    ("rpng", "table_01", "rpngar"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def transform_schedule(source: Path, destination: Path) -> int:
    payload = json.loads(source.read_text())
    mapping = payload["arrival_iteration_by_name"]
    if payload.get("iters_per_event") != 60 or payload.get("tail_iters") != 0:
        raise ValueError(f"unexpected source schedule: {source}")
    transformed = {
        name: 1 + ((int(value) - 1) // 60) * BUDGET
        for name, value in mapping.items()
    }
    total = max(transformed.values())
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "arrival_iteration_by_name": transformed,
                "total_iterations": total,
                "source_schedule": str(source),
                "source_schedule_sha256": sha256(source),
                "updates_per_event": BUDGET,
                "tail_iters": 0,
            },
            indent=2,
        )
        + "\n"
    )
    return total


def valid_control(path: Path) -> bool:
    required = (
        path / "images",
        path / "sparse/0/cameras.txt",
        path / "sparse/0/images.txt",
        path / "sparse/0/points3D.txt",
        path / "causal_arrivals.json",
        path / "vigs_replay_metadata.json",
    )
    return all(item.exists() for item in required)


def build_control(family: str, scene: str, prepared_family: str) -> Path:
    destination = DATA_ROOT / family / scene / "stride40"
    if valid_control(destination):
        return destination
    if destination.exists():
        raise RuntimeError(f"incomplete control exists: {destination}")
    source = ROOT / "data/benchmarks" / family / "prepared" / prepared_family / scene
    vigs_run = SOURCE_ROOT / family / scene / "seed0"
    subprocess.run(
        [
            str(PYTHON),
            str(BUILDER),
            "--kind", family,
            "--input", str(source),
            "--vigs-run", str(vigs_run),
            "--output", str(destination),
            "--iters-per-event", "60",
        ],
        check=True,
    )
    if not valid_control(destination):
        raise RuntimeError(f"control postcondition failed: {destination}")
    return destination


def build_dense(control: Path, family: str, scene: str) -> Path:
    destination = DATA_ROOT / family / scene / "stride20"
    source_points = SOURCE_ROOT / family / scene / "seed0/points3D_stride20.txt"
    expected = sum(1 for _ in source_points.open())
    metadata_path = destination / "vigs_replay_metadata.json"
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text())
        if metadata.get("point_count") == expected and (destination / "images").exists():
            return destination
        raise RuntimeError(f"invalid existing dense dataset: {destination}")
    if destination.exists():
        raise RuntimeError(f"incomplete dense dataset exists: {destination}")
    sparse = destination / "sparse/0"
    sparse.mkdir(parents=True)
    os.symlink(control.joinpath("images").resolve(), destination / "images")
    for filename in ("cameras.txt", "images.txt"):
        shutil.copy2(control / "sparse/0" / filename, sparse / filename)
    with source_points.open() as source, (sparse / "points3D.txt").open("x") as target:
        for point_id, line in enumerate(source):
            fields = line.split()
            if len(fields) < 4:
                raise ValueError(f"invalid source point: {line!r}")
            target.write(
                f"{point_id} {fields[1]} {fields[2]} {fields[3]} 128 128 128 0\n"
            )
    shutil.copy2(control / "causal_arrivals.json", destination / "causal_arrivals.json")
    metadata = json.loads((control / "vigs_replay_metadata.json").read_text())
    metadata.update(
        {
            "initialization": "same-run VIGS BA-refined depth-anchor log, stride20",
            "depth_anchor_stride": 20,
            "point_count": expected,
            "point_source_sha256": sha256(source_points),
            "paired_control_dataset": str(control),
            "paired_same_pose_depth_run": True,
        }
    )
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    return destination


def main() -> None:
    jobs = []
    dataset_records = []
    schedule_root = HERE / "evidence/schedules"
    for family, scene, prepared_family in SCENES:
        control = build_control(family, scene, prepared_family)
        dense = build_dense(control, family, scene)
        control_metadata = json.loads((control / "vigs_replay_metadata.json").read_text())
        dense_metadata = json.loads((dense / "vigs_replay_metadata.json").read_text())
        if control_metadata["pose_source_sha256"] != dense_metadata["pose_source_sha256"]:
            raise ValueError("pose source differs between density arms")
        if control_metadata["keyframe_source_sha256"] != dense_metadata["keyframe_source_sha256"]:
            raise ValueError("keyframe source differs between density arms")
        dataset_records.append(
            {
                "family": family,
                "scene": scene,
                "control_points": control_metadata["point_count"],
                "dense_points": dense_metadata["point_count"],
                "density_ratio": dense_metadata["point_count"] / control_metadata["point_count"],
                "pose_source_sha256": control_metadata["pose_source_sha256"],
                "keyframe_source_sha256": control_metadata["keyframe_source_sha256"],
            }
        )
        schedule = schedule_root / family / f"{scene}_event{BUDGET}.json"
        total = transform_schedule(control / "causal_arrivals.json", schedule)
        checkpoints = sorted({max(1, total // 2), total})
        for density, dataset in (("stride40", control), ("stride20", dense)):
            for arm in ("rr", "ercb"):
                scheduler = (
                    "causal_rr" if arm == "rr" else "relative_floor_interval_softmax_rr"
                )
                output = RESULT_ROOT / family / scene / density / f"{arm}_s{SEED}"
                argv = [
                    str(PYTHON),
                    str(ROOT / "context/experiments/exp77/run_training.py"),
                    "--repo", str(GS_REPO), "--arm", arm, "--",
                    "-s", str(dataset), "-m", str(output), "-r", "4", "--eval",
                    "--iterations", str(total), "--test_iterations",
                    *[str(value) for value in checkpoints],
                    "--save_iterations", str(total),
                    "--view_schedule", str(schedule),
                    "--view_scheduler", scheduler,
                    "--scheduler_seed", str(SEED),
                    "--scheduler_beta", str(math.log(3.0)),
                    "--scheduler_block_size", "8",
                    "--position_lr_max_steps", str(total),
                    "--densify_until_iter", "0",
                    "--depth_l1_weight_init", "0",
                    "--depth_l1_weight_final", "0",
                    "--data_device", "cpu",
                    "--fixed_topology_step_before_report",
                    "--quiet", "--disable_viewer",
                ]
                jobs.append(
                    {
                        "family": family,
                        "scene": scene,
                        "density": density,
                        "arm": arm,
                        "seed": SEED,
                        "dataset": str(dataset),
                        "schedule": str(schedule),
                        "total_iterations": total,
                        "output": str(output),
                        "argv": argv,
                        "state": "pending",
                    }
                )
    evidence = HERE / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "manifest.json").write_text(
        json.dumps(
            {
                "protocol": "benchmark-A_same-depth-pose_stride40_vs_stride20_low-budget",
                "state": "PREPARED_NOT_RUN",
                "contract": {
                    "updates_per_event": BUDGET,
                    "seed": SEED,
                    "densities": ["stride40", "stride20"],
                    "arms": ["causal_rr", "relative_floor_interval_softmax_rr"],
                    "fixed_topology": True,
                    "loss": "RGB-only",
                    "heldout": "llffhold-8",
                    "tail_updates": 0,
                },
                "source_exporter_sha256": sha256(VIGS_REPO / "vigs/gs_backend.py"),
                "datasets": dataset_records,
                "jobs": jobs,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"prepared {len(jobs)} jobs")


if __name__ == "__main__":
    main()
