#!/usr/bin/env python3
"""Extend the frozen R4 B-track runner to the full local benchmark panel.

The mapping, evaluation, and pair-verification implementations remain those of
the hash-locked Stage-6R-X4 runner.  This wrapper adds only the development and
previously exposed RPNG/UTMM sequences omitted from the confirmation cohort.
Aria is added in a separate, source-locked extension after its mapper-neutral
tracker archives have been captured and validated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import run_exp78b_stage6rx4_cross_sequence as base


WORKSPACE = Path("/home/intern/gs_floaterLab")
DEFAULT_ROOT = (
    WORKSPACE
    / "results/experiments/exp78/paper_full_staged_v1"
    / "stage6r_all_scenes_fixed_work"
)

# role, eval count, fixed-manifest SHA-256, archive-manifest SHA-256
EXTRA_SEQUENCES = {
    ("rpng", "table_01"): (
        "development",
        502,
        "f6bbdd74211c3bf75776f2d381db93fadf07e20fb8f2ec251118211cba925589",
        "cb7e31db582d41ea58ba3f4c4cc09558cfe5e5d049969dd69ad5fbf93cc3c5b0",
    ),
    ("rpng", "table_02"): (
        "previously_exposed_validation",
        584,
        "8d688bf6cb04fc3e289de5e28e03248891dc3e8dd63bf286d44033268b626551",
        "e08428c63c97b97b8ec5f4818e69b5edc952ee4a2cc67cbcdf35229a1316fa04",
    ),
    ("rpng", "table_06"): (
        "development",
        555,
        "dc75e1ce0c7a40611c0cf208091d1fc9c47b19127e2efcddd1c0ac8a952e406a",
        "4cca088609e3852706c66566beb2fb23a048fa8e24621d3efa77335fd2f4e322",
    ),
    ("utmm", "ego-drive"): (
        "development",
        281,
        "cdd1037b750df1fee6d9c7700cc8f18f43bb1d2be1548ca067ffdb92ee9e3191",
        "b76d81746d8e9e63f9f75f45ba2baca48465b3666cf90f07b8ddcf4b5ea4c1ba",
    ),
    ("utmm", "square-2"): (
        "development",
        245,
        "9332bc5f5a998579c06113471f70c2ddb7a0a230be43b33254ea4d89970036d7",
        "93eeca4b273dde26a7403e7b04bd03e30934d6c08f2ecb9799db9e27767662e9",
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install_extension() -> None:
    base.SEQUENCES.update(EXTRA_SEQUENCES)
    base.RUN_PROTOCOL = "stage6r_r4_all_scenes_fixed_work_runner_v1"
    base.PANEL = "stage6r_r4_all_scenes"


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
    """Record the extension wrapper and the original split role additively."""
    manifest = base.run_paths(root, *key)[arm] / "source_manifest.txt"
    text = manifest.read_text(encoding="utf-8")
    role = EXTRA_SEQUENCES[key][0]
    marker = "all_scenes_wrapper_sha256="
    if marker in text:
        return
    text = text.replace("role=confirmation\n", f"role={role}\n", 1)
    text += f"all_scenes_wrapper_sha256={sha256(Path(__file__).resolve())}\n"
    manifest.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("preflight")
    run = subparsers.add_parser("run")
    run.add_argument("--arm", choices=("candidate", "vanilla"), required=True)
    run.add_argument("--dataset", choices=("rpng", "utmm"), required=True)
    run.add_argument("--sequence", required=True)
    run.add_argument("--dry-run", action="store_true")
    pair = subparsers.add_parser("verify-pair")
    pair.add_argument("--dataset", choices=("rpng", "utmm"), required=True)
    pair.add_argument("--sequence", required=True)
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
                "all_scenes_wrapper": str(Path(__file__).resolve()),
                "all_scenes_wrapper_sha256": sha256(Path(__file__).resolve()),
                "panel": base.PANEL,
            }
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    key = (args.dataset, args.sequence)
    if key not in EXTRA_SEQUENCES:
        raise ValueError(
            "this extension runs only the five RPNG/UTMM scenes omitted from X4"
        )
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
