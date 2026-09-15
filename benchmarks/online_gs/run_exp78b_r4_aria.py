#!/usr/bin/env python3
"""Run the frozen exp78 R4 B-track pair on the two local Aria scenes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp78b_stage6rx4_cross_sequence as base


WORKSPACE = Path("/home/intern/gs_floaterLab")
DATA_ROOT = Path("/home/intern/p28_5090_20260813/VIGS-SLAM-custom/data")
DEFAULT_ROOT = (
    WORKSPACE
    / "results/experiments/exp78/paper_full_staged_v1"
    / "stage6r_all_scenes_fixed_work"
)
CUSTOM_CONFIG = WORKSPACE / "benchmarks/online_gs/config/vigs_final_v7_aria.yaml"
VANILLA_CONFIG = (
    WORKSPACE / "benchmarks/online_gs/config/vigs_official_aria_adapter.yaml"
)
CAPTURE_HARNESS = WORKSPACE / "benchmarks/online_gs/exp78b_capture_frozen_tracker.py"

# role, evaluation count, fixed-manifest SHA-256, archive-manifest SHA-256
ARIA_SEQUENCES = {
    ("aria", "aria1253"): (
        "development",
        262,
        "40df31333e5bddd13ba178c7246d7d8fb364a32886a1345ac0d5e9748572713f",
        "4ce6b0a74dff8906e16cd65db0033003073b1cffb0c8bd3cb5d1f9ea4d0ca142",
    ),
    ("aria", "aria301_305"): (
        "transfer",
        539,
        "8f1a27d5e48e2b2c04ad1ae9eab37eb93cbebfb331b0171bb8f52fc143d1d259",
        "8f6d744a0e5b3fd166703c444a013aa4250b7d9e5974c0f2cf890d0151e76cf5",
    ),
}

ORIGINAL_SEQUENCE_PATHS = base.sequence_paths


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sequence_paths(dataset: str, sequence: str) -> dict[str, Path]:
    key = (dataset, sequence)
    if key not in ARIA_SEQUENCES:
        return ORIGINAL_SEQUENCE_PATHS(dataset, sequence)
    data_dir = DATA_ROOT / ("aria1253_repro" if sequence == "aria1253" else sequence)
    return {
        "archive": base.ARCHIVE_ROOT / dataset / sequence / "seed0",
        "fixed_manifest": base.MANIFEST_ROOT / f"aria_{sequence}.json",
        "custom_config": CUSTOM_CONFIG,
        "vanilla_config": VANILLA_CONFIG,
        "image_dir": data_dir / "rgb",
        "calibration": base.PAPER_ROOT / f"calib/{sequence}.txt",
    }


def evaluation_command(output: Path, dataset: str, sequence: str) -> list[str]:
    paths = sequence_paths(dataset, sequence)
    return [
        str(base.PYTHON_ENV / "bin/python"),
        str(base.EVALUATOR),
        "--run-dir", str(output),
        "--image-dir", str(paths["image_dir"]),
        "--calib", str(paths["calibration"]),
        "--manifest", str(paths["fixed_manifest"]),
        "--rgb-file-in-nanoseconds",
        "--mapped-uids-json", str(output / "mapped_uids.json"),
        "--result-subdir", "strict_fixed_manifest",
    ]


def install_extension() -> None:
    base.SEQUENCES.update(ARIA_SEQUENCES)
    base.sequence_paths = sequence_paths
    base.evaluation_command = evaluation_command
    base.RUN_PROTOCOL = "stage6r_r4_aria_fixed_work_runner_v1"
    base.PANEL = "stage6r_r4_all_scenes"
    base.EXPECTED_HASHES.update(
        {
            CUSTOM_CONFIG: "5410e4ee3bb8303d21aa72557cb1735e3117b097d2889c7e5d0b0c5979d9b572",
            VANILLA_CONFIG: "36435b4195e345244788d2d9c26a9ed7fcc4b923d8fd4c1d5201035f15720257",
            CAPTURE_HARNESS: "ad0650ab7e6f88658f75c8be2854372d9e8130ded6d90901ad7bb08fed11ae92",
        }
    )


def require_wrapper_clean() -> None:
    path = Path(__file__).resolve()
    subprocess.run(
        ("git", "-C", str(WORKSPACE), "ls-files", "--error-unmatch", str(path)),
        stdout=subprocess.DEVNULL,
        check=True,
    )
    subprocess.run(
        ("git", "-C", str(WORKSPACE), "diff", "--quiet", "--", str(path)),
        check=True,
    )
    subprocess.run(
        ("git", "-C", str(WORKSPACE), "diff", "--cached", "--quiet", "--", str(path)),
        check=True,
    )


def annotate_manifest(root: Path, arm: str, key: tuple[str, str]) -> None:
    manifest = base.run_paths(root, *key)[arm] / "source_manifest.txt"
    content = manifest.read_text(encoding="utf-8")
    if "aria_wrapper_sha256=" in content:
        return
    role = ARIA_SEQUENCES[key][0]
    content = content.replace("role=confirmation\n", f"role={role}\n", 1)
    content += f"aria_wrapper_sha256={sha256(Path(__file__).resolve())}\n"
    content += f"capture_harness_sha256={sha256(CAPTURE_HARNESS)}\n"
    manifest.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("preflight")
    run = subparsers.add_parser("run")
    run.add_argument("--arm", choices=("candidate", "vanilla"), required=True)
    run.add_argument("--sequence", choices=("aria1253", "aria301_305"), required=True)
    run.add_argument("--dry-run", action="store_true")
    pair = subparsers.add_parser("verify-pair")
    pair.add_argument("--sequence", choices=("aria1253", "aria301_305"), required=True)
    return parser.parse_args()


def main() -> int:
    install_extension()
    require_wrapper_clean()
    args = parse_args()
    root = args.root.resolve()
    if args.action == "preflight":
        report = base.require_predeclared_state()
        report.update(
            {
                "aria_wrapper": str(Path(__file__).resolve()),
                "aria_wrapper_sha256": sha256(Path(__file__).resolve()),
                "aria_sequences": len(ARIA_SEQUENCES),
                "panel": base.PANEL,
            }
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    key = ("aria", args.sequence)
    if args.action == "run":
        base.run_arm(root, args.arm, *key, args.dry_run)
        if not args.dry_run and args.arm == "candidate":
            annotate_manifest(root, "candidate", key)
        return 0
    if args.action == "verify-pair":
        valid = base.verify_pair(root, *key)
        if valid:
            annotate_manifest(root, "vanilla", key)
        return 0 if valid else 1
    raise AssertionError(args.action)


if __name__ == "__main__":
    raise SystemExit(main())
