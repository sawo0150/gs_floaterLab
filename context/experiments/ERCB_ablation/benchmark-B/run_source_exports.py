#!/usr/bin/env python3
"""Run/resume paired stride40/stride20 VIGS exports for all benchmark families."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
VIGS = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-main-integration-20260828")
RUNNER = VIGS / "exp81_axes/run_utmm_strict15x_baseline.sh"
SOURCE_ROOT = ROOT / "results/ERCB_ablation/benchmark-B_stride20_source"
PILOT_ROOT = ROOT / "results/ERCB_ablation/benchmark-A_init_density_source"
INVENTORY = HERE / "evidence/source_inventory.json"


def scenes() -> list[dict]:
    records: list[dict] = []
    utmm_root = ROOT / "data/benchmarks/utmm/prepared/UTMM_Dataset"
    for scene in (
        "ego-centric-1", "ego-centric-2", "ego-drive", "fast-straight",
        "slow-straight-1", "slow-straight-2", "square-1", "square-2",
    ):
        base = utmm_root / scene
        records.append({
            "family": "utmm", "scene": scene, "input": str(base),
            "image_dir": str(base / "rgb_timestamp"),
            "imu": str(base / "imu_ours.txt"),
            "calib": str(base / "intrinsics_ours.txt"),
            "config": str(VIGS / "config/exp81_utmm_baseline.yaml"),
            "undistort": "0", "imu_init": "15",
        })
    rpng_root = ROOT / "data/benchmarks/rpng/prepared/rpngar"
    for index in range(1, 9):
        scene = f"table_{index:02d}"
        base = rpng_root / scene
        records.append({
            "family": "rpng", "scene": scene, "input": str(base),
            "image_dir": str(base / "rgb"), "imu": str(base / "imu.txt"),
            "calib": str(VIGS / "calib/rpngar.txt"),
            "config": str(VIGS / "config/exp83_rpng_baseline.yaml"),
            "undistort": "1", "imu_init": "20",
        })
    for dataset_name, scene in (
        ("aria1253", "aria1253"),
        ("aria1253rot", "aria1253rot"),
        ("aria301_305", "aria301_305"),
        ("aria301_12F", "aria301_12F"),
    ):
        base = VIGS / "data" / dataset_name
        records.append({
            "family": "aria", "scene": scene, "input": str(base),
            "image_dir": str(base / "rgb"), "imu": str(base / "imu.txt"),
            "calib": str(VIGS / "calib" / f"{dataset_name}.txt"),
            "config": str(VIGS / "config/exp82_aria_adopted_rgb_only.yaml"),
            "undistort": "0", "imu_init": "20",
        })
    return records


def valid(path: Path) -> bool:
    return all(
        (path / name).is_file() and (path / name).stat().st_size > 0
        for name in (
            "points3D.txt", "points3D_stride20.txt",
            "traj_full_online_eval.txt", "traj_kf_beforeBA.txt",
        )
    )


def gpu_busy() -> bool:
    return bool(subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
        text=True,
    ).strip())


def save(records: list[dict]) -> None:
    INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY.write_text(json.dumps({
        "protocol": "same-run paired VIGS stride40/stride20 source export",
        "source_root": str(SOURCE_ROOT),
        "scenes_requested": len(records),
        "complete": sum(row.get("state") in ("complete", "reused") for row in records),
        "failed": sum(row.get("state") == "failed" for row in records),
        "records": records,
    }, indent=2) + "\n")


def main() -> None:
    records = scenes()
    previous = {}
    if INVENTORY.is_file():
        previous = {
            (row["family"], row["scene"]): row
            for row in json.loads(INVENTORY.read_text()).get("records", [])
        }
    for index, row in enumerate(records, 1):
        key = (row["family"], row["scene"])
        output = SOURCE_ROOT / row["family"] / row["scene"] / "seed0"
        row["output"] = str(output)
        if valid(output):
            row["state"] = "reused"
            row["primary_points"] = sum(1 for _ in (output / "points3D.txt").open())
            row["stride20_points"] = sum(1 for _ in (output / "points3D_stride20.txt").open())
            save(records)
            print(f"REUSE {index}/{len(records)} {key[0]}/{key[1]}", flush=True)
            continue
        pilot = PILOT_ROOT / row["family"] / row["scene"] / "seed0"
        if not output.exists() and valid(pilot):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.symlink_to(pilot.resolve(), target_is_directory=True)
            row["state"] = "reused"
            row["primary_points"] = sum(1 for _ in (output / "points3D.txt").open())
            row["stride20_points"] = sum(1 for _ in (output / "points3D_stride20.txt").open())
            save(records)
            print(f"LINK {index}/{len(records)} {key[0]}/{key[1]}", flush=True)
            continue
        missing_only_full_trajectory = (
            output.is_dir()
            and not (output / "traj_full_online_eval.txt").exists()
            and all((output / name).is_file() for name in (
                "points3D.txt", "points3D_stride20.txt", "traj_kf_beforeBA.txt",
            ))
        )
        if missing_only_full_trajectory:
            archived = output.with_name("seed0_incomplete_no_full_trajectory")
            if archived.exists():
                row.update({
                    "state": "failed",
                    "reason": f"both retry target and preserved incomplete output exist: {archived}",
                })
                save(records)
                print(f"PRESERVE_FAILED {index}/{len(records)} {key[0]}/{key[1]}", flush=True)
                continue
            output.rename(archived)
            row["preserved_incomplete"] = str(archived)
            print(f"ARCHIVE_RETRY {index}/{len(records)} {key[0]}/{key[1]}", flush=True)
        if output.exists():
            old = previous.get(key, {})
            row.update({
                "state": "failed",
                "reason": old.get("reason", "incomplete output preserved; manual audit required"),
            })
            save(records)
            print(f"PRESERVE_FAILED {index}/{len(records)} {key[0]}/{key[1]}", flush=True)
            continue
        required = [Path(row[name]) for name in ("image_dir", "imu", "calib", "config")]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            row.update({"state": "failed", "reason": f"missing input: {missing}"})
            save(records)
            print(f"MISSING {index}/{len(records)} {key[0]}/{key[1]}", flush=True)
            continue
        if gpu_busy():
            save(records)
            raise RuntimeError("GPU compute process active; wait and resume without killing it")
        output.mkdir(parents=True)
        environment = os.environ.copy()
        environment.update({
            "VIGS_DEPTH_ANCHOR_SECONDARY_LOG": str(output / "points3D_stride20.txt"),
            "VIGS_DEPTH_ANCHOR_SECONDARY_STRIDE": "20",
            "EXP81_HARDWARE_PROFILE": "rtx5070ti",
            "EXP81_REPLAY_TIME_SCALE": "1",
            "EXP81_STREAM_PROTOCOL": "strict_zero_tail",
            "EXP81_FRONTEND_RECIPE": "quality",
            "EXP81_MAPPING_PROFILE": "final_v7",
            "EXP81_DENSITY_RECIPE": "configured",
            "EXP81_DATASET_ROOT": row["input"],
            "EXP81_IMAGE_DIR": row["image_dir"],
            "EXP81_IMU_FILE": row["imu"],
            "EXP81_CALIBRATION": row["calib"],
            "EXP81_CONFIG_FILE": row["config"],
            "EXP81_DATASET_LABEL": f"{row['family']}/{row['scene']}",
            "EXP81_UNDISTORT": row["undistort"],
            "EXP81_IMU_POSEINIT_AFTER": row["imu_init"],
            # Source generation needs pose/KF/anchor exports only.  Final map
            # rendering is a post-stream read-only cost and is evaluated later
            # by the fixed replay panel.
            "EXP69_EVAL_ONLINE_FINAL": "0",
        })
        environment.pop("EXP81_LENGTH", None)
        print(f"START {index}/{len(records)} {key[0]}/{key[1]}", flush=True)
        started = time.time()
        try:
            with (output / "run.log").open("x") as stream:
                result = subprocess.run(
                    ["bash", str(RUNNER), row["scene"], str(output)],
                    env=environment, stdout=stream, stderr=subprocess.STDOUT,
                    timeout=1800,
                )
            row["returncode"] = result.returncode
            row["wall_seconds"] = time.time() - started
            if result.returncode == 0 and valid(output):
                row["state"] = "complete"
                row["primary_points"] = sum(1 for _ in (output / "points3D.txt").open())
                row["stride20_points"] = sum(1 for _ in (output / "points3D_stride20.txt").open())
                print(f"DONE {index}/{len(records)} {key[0]}/{key[1]}", flush=True)
            else:
                row["state"] = "failed"
                row["reason"] = f"returncode={result.returncode} or required export missing"
                print(f"FAILED {index}/{len(records)} {key[0]}/{key[1]}", flush=True)
        except subprocess.TimeoutExpired:
            row["state"] = "failed"
            row["wall_seconds"] = time.time() - started
            row["reason"] = "source export exceeded 1800 seconds"
            print(f"TIMEOUT {index}/{len(records)} {key[0]}/{key[1]}", flush=True)
        save(records)
    save(records)


if __name__ == "__main__":
    main()
