#!/usr/bin/env python3
"""Run the predeclared exp78 Stage-5 mapping-only replication cohort.

The tracker archive is always the immutable seed-0 RPNG table_01 capture.
Seeds 1/2/3 change mapper RNG only.  Each seed is run as C1+RR, C1+C2, and
native vanilla render-matched to the C2 physical-render ledger.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from typing import Any


WORKSPACE = Path("/home/intern/gs_floaterLab")
PAPER_ROOT = Path("/home/intern/VIGS-SLAM-paper-full")
OFFICIAL_ROOT = Path("/home/intern/VIGS-SLAM-official-exp78")
BUILT_THIRDPARTY_ROOT = Path("/home/intern/VIGS-SLAM-visible-lazy-carve")
PYTHON_ENV = Path("/home/colin/miniconda3/envs/vigs-slam-5090")

PAPER_COMMIT = "43dab043f339a59cc6bb31bf9c72dc6d6a1fc452"
OFFICIAL_COMMIT = "22ffe24c6df81d0bf63bd20057565c00c51d2996"
EXPECTED_SEEDS = (1, 2, 3)
EXPECTED_VIEW_COUNT = 502

ARCHIVE = (
    WORKSPACE
    / "results/experiments/exp78/b_strict_fair_comparison/frozen_tracker"
    / "official_22ffe24_trt/rpng/table_01/seed0"
)
CUSTOM_CONFIG = (
    WORKSPACE / "benchmarks/online_gs/config/vigs_final_v7_rpng.yaml"
)
VANILLA_CONFIG = OFFICIAL_ROOT / "config/rpng.yaml"
FIXED_MANIFEST = (
    WORKSPACE
    / "context/experiments/exp78/b_strict_fair_comparison/manifests"
    / "rpng_table_01.json"
)
IMAGE_DIR = (
    WORKSPACE / "data/benchmarks/rpng/prepared/rpngar/table_01/rgb"
)
CALIBRATION = OFFICIAL_ROOT / "calib/rpngar.txt"
CUSTOM_HARNESS = (
    WORKSPACE / "benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
)
VANILLA_HARNESS = (
    WORKSPACE / "benchmarks/online_gs/exp78b_replay_vanilla_mapping.py"
)
EVALUATOR = WORKSPACE / "benchmarks/online_gs/exp78_evaluate_vigs_ply.py"
ARCHIVE_VALIDATOR = (
    WORKSPACE / "benchmarks/online_gs/validate_exp78b_frozen_tracker.py"
)
PAIR_VERIFIER = (
    PAPER_ROOT
    / "paper_full_stages/verify_stage4_c1_c2_global_residue_integration.py"
)
RENDER_VERIFIER = (
    WORKSPACE / "benchmarks/online_gs/verify_exp78b_d1_render_match.py"
)
COHORT_VERIFIER = (
    PAPER_ROOT
    / "paper_full_stages/verify_stage5_full_retention_replication.py"
)
DEFAULT_ROOT = (
    WORKSPACE
    / "results/experiments/exp78/paper_full_staged_v1/rpng/table_01"
    / "stage5_full_retention_replication"
)

EXPECTED_HASHES = {
    CUSTOM_HARNESS: "9d50dbb9d20374b47289dce4327cf3dad23c9d48a5fc055f82241c0a0bf7c67c",
    VANILLA_HARNESS: "7966c28409f20db051f9c4ba824d8ce1f5853929e7846f9f45cf92e547b278c2",
    EVALUATOR: "f854084b249cea724b7be65a1655088ce8906203110f52c6503b052ec3b51c3c",
    ARCHIVE_VALIDATOR: "b2c2e050ddff373cd5e4062460fa021a141d206673a98d87fe531d3b917afccc",
    CUSTOM_CONFIG: "138fdd26a99be125fab900ba9e731d38660ee7d2dd8e5f6833496a16045ccf54",
    FIXED_MANIFEST: "f6bbdd74211c3bf75776f2d381db93fadf07e20fb8f2ec251118211cba925589",
    ARCHIVE / "archive_manifest.json": "cb7e31db582d41ea58ba3f4c4cc09558cfe5e5d049969dd69ad5fbf93cc3c5b0",
}

CUSTOM_FLAGS = (
    "--time-scale",
    "unbounded",
    "--deadline-reserve-ms",
    "20",
    "--fixed-event-dense-opportunities-per-packet",
    "1",
    "--compute-paced-dense-admission",
    "--compute-paced-dense-token-cost",
    "22",
    "--c1-c2-global-residue-integration",
    "--density-policy",
    "online_rank",
    "--online-density-mean-multiplier",
    "2.5",
    "--online-density-span",
    "2.0",
    "--dense-replay-scope",
    "appearance",
    "--profile",
    "dense_rr_imu",
    "--observation-topology-gate",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def git_output(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ("git", "-C", str(root), *args), text=True
    ).strip()


def paths_for(root: Path, seed: int) -> dict[str, Path]:
    return {
        "rr": root / f"c1_rr_s{seed}",
        "c2": root / f"c1_global_residue_c2_s{seed}",
        "vanilla": root / f"native_vanilla_render_matched_s{seed}",
        "pair": root / "verification" / f"stage4_pair_s{seed}.json",
        "render": root / "verification" / f"render_match_s{seed}.json",
        "cohort": root / "verification" / "stage5_cohort.json",
    }


def mapping_command(arm: str, seed: int, output: Path, root: Path) -> list[str]:
    python = str(PYTHON_ENV / "bin/python")
    common = [
        "--archive",
        str(ARCHIVE),
        "--output",
        str(output),
        "--seed",
        str(seed),
    ]
    if arm in ("rr", "c2"):
        command = [
            python,
            str(CUSTOM_HARNESS),
            *common,
            "--config",
            str(CUSTOM_CONFIG),
            *CUSTOM_FLAGS,
        ]
        if arm == "c2":
            command.append("--service-shortfall-ercb")
        return command
    if arm == "vanilla":
        c2_runtime = paths_for(root, seed)["c2"] / "mapping_replay_runtime.json"
        return [
            python,
            str(VANILLA_HARNESS),
            *common,
            "--config",
            str(VANILLA_CONFIG),
            "--time-scale",
            "unbounded",
            "--deadline-reserve-ms",
            "20",
            "--reference-service-runtime",
            str(c2_runtime),
        ]
    raise ValueError(f"unsupported arm: {arm}")


def evaluation_command(output: Path) -> list[str]:
    return [
        str(PYTHON_ENV / "bin/python"),
        str(EVALUATOR),
        "--run-dir",
        str(output),
        "--image-dir",
        str(IMAGE_DIR),
        "--calib",
        str(CALIBRATION),
        "--manifest",
        str(FIXED_MANIFEST),
        "--rgb-file-in-nanoseconds",
        "--undistort",
        "--mapped-uids-json",
        str(output / "mapped_uids.json"),
        "--result-subdir",
        "strict_fixed_manifest",
    ]


def mapping_environment(arm: str) -> dict[str, str]:
    env = os.environ.copy()
    torch_lib = PYTHON_ENV / "lib/python3.11/site-packages/torch/lib"
    old_library_path = env.get("LD_LIBRARY_PATH")
    env["LD_LIBRARY_PATH"] = ":".join(
        value
        for value in (str(torch_lib), str(PYTHON_ENV / "lib"), old_library_path)
        if value
    )
    built = BUILT_THIRDPARTY_ROOT / "thirdparty"
    if arm in ("rr", "c2"):
        components = (
            PAPER_ROOT / "vigs",
            PAPER_ROOT,
            BUILT_THIRDPARTY_ROOT,
            built / "diff-gaussian-rasterization",
            built / "lietorch_5090",
            built / "simple-knn",
        )
        env["EXP78B_CUSTOM_ROOT"] = str(PAPER_ROOT)
    else:
        components = (
            OFFICIAL_ROOT / "vigs",
            OFFICIAL_ROOT / "thirdparty/diff-gaussian-rasterization",
            built / "lietorch_5090",
            built / "simple-knn",
        )
    old_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = ":".join(
        value
        for value in (*map(str, components), old_pythonpath)
        if value
    )
    env["PYTHONUNBUFFERED"] = "1"
    return env


def evaluation_environment() -> dict[str, str]:
    env = mapping_environment("vanilla")
    return env


def require_predeclared_state() -> dict[str, str]:
    required = (
        ARCHIVE / "archive_manifest.json",
        CUSTOM_CONFIG,
        VANILLA_CONFIG,
        FIXED_MANIFEST,
        IMAGE_DIR,
        CALIBRATION,
        CUSTOM_HARNESS,
        VANILLA_HARNESS,
        EVALUATOR,
        ARCHIVE_VALIDATOR,
        PAIR_VERIFIER,
        RENDER_VERIFIER,
        COHORT_VERIFIER,
        PYTHON_ENV / "bin/python",
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing Stage-5 inputs:\n" + "\n".join(missing))
    paper_commit = git_output(PAPER_ROOT, "rev-parse", "HEAD")
    official_commit = git_output(OFFICIAL_ROOT, "rev-parse", "HEAD")
    if paper_commit != PAPER_COMMIT:
        raise RuntimeError(
            f"paper source moved: expected {PAPER_COMMIT}, got {paper_commit}"
        )
    if official_commit != OFFICIAL_COMMIT:
        raise RuntimeError(
            "official source moved: "
            f"expected {OFFICIAL_COMMIT}, got {official_commit}"
        )
    subprocess.run(
        ("git", "-C", str(PAPER_ROOT), "diff", "--quiet", "--ignore-submodules=dirty"),
        check=True,
    )
    subprocess.run(
        (
            "git",
            "-C",
            str(PAPER_ROOT),
            "diff",
            "--cached",
            "--quiet",
            "--ignore-submodules=dirty",
        ),
        check=True,
    )
    subprocess.run(
        ("git", "-C", str(OFFICIAL_ROOT), "diff", "--quiet", "--ignore-submodules=dirty"),
        check=True,
    )
    subprocess.run(
        (
            "git",
            "-C",
            str(OFFICIAL_ROOT),
            "diff",
            "--cached",
            "--quiet",
            "--ignore-submodules=dirty",
        ),
        check=True,
    )
    mismatches = {
        str(path): {"expected": expected, "actual": sha256(path)}
        for path, expected in EXPECTED_HASHES.items()
        if sha256(path) != expected
    }
    if mismatches:
        raise RuntimeError(
            "predeclared source/input hash mismatch:\n"
            + json.dumps(mismatches, indent=2, sort_keys=True)
        )
    subprocess.run(
        (
            str(PYTHON_ENV / "bin/python"),
            "-c",
            "import vigs_backends, lietorch, diff_gaussian_rasterization, simple_knn",
        ),
        cwd=WORKSPACE,
        env=mapping_environment("rr"),
        check=True,
    )
    return {
        "paper_commit": paper_commit,
        "official_commit": official_commit,
        "lab_commit": git_output(WORKSPACE, "rev-parse", "HEAD"),
    }


def run_logged(command: list[str], log: Path, env: dict[str, str]) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as sink:
        process = subprocess.Popen(
            command,
            cwd=WORKSPACE,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            sink.write(line)
            sink.flush()
        return_code = process.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)


def ensure_archive_validation(output: Path) -> None:
    cache = ARCHIVE / "validation.json"
    archive_hash = sha256(ARCHIVE / "archive_manifest.json")
    valid = False
    if cache.is_file():
        try:
            report = read_json(cache)
            valid = (
                report.get("valid") is True
                and report.get("archive_manifest_sha256") == archive_hash
            )
        except (OSError, ValueError, json.JSONDecodeError):
            valid = False
    if not valid:
        run_logged(
            [
                str(PYTHON_ENV / "bin/python"),
                str(ARCHIVE_VALIDATOR),
                str(ARCHIVE),
                "--output",
                str(cache),
            ],
            output / "archive_validation.log",
            mapping_environment("vanilla"),
        )
        report = read_json(cache)
        if report.get("valid") is not True:
            raise RuntimeError("frozen archive validation failed")
    else:
        (output / "archive_validation.log").write_text(
            f"reused {cache}\n", encoding="utf-8"
        )
    shutil.copy2(cache, output / "frozen_archive_validation.json")


def validate_completed_run(output: Path, seed: int) -> dict[str, Any]:
    runtime = read_json(output / "mapping_replay_runtime.json")
    if int(runtime.get("seed", -1)) != seed:
        raise RuntimeError("runtime mapper seed mismatch")
    if runtime.get("archive_manifest_sha256") != EXPECTED_HASHES[
        ARCHIVE / "archive_manifest.json"
    ]:
        raise RuntimeError("runtime frozen archive mismatch")
    if int(runtime.get("post_eos_optimizer_updates", -1)) != 0:
        raise RuntimeError("zero-tail violation")
    if runtime.get("final_ba_performed") is not False:
        raise RuntimeError("unexpected final BA")
    if runtime.get("final_color_refinement_performed") is not False:
        raise RuntimeError("unexpected final color refinement")
    evaluation = read_json(
        output / "psnr/strict_fixed_manifest/final_result.json"
    )
    fixed = evaluation.get("predeclared_fixed_manifest_posthoc") or {}
    if int(fixed.get("view_count", -1)) != EXPECTED_VIEW_COUNT:
        raise RuntimeError("fixed held-out evaluator view-count mismatch")
    if fixed.get("mapping_disjoint") is not True:
        raise RuntimeError("fixed held-out evaluator is not mapping-disjoint")
    return runtime


def write_manifest(
    output: Path,
    arm: str,
    seed: int,
    command: list[str],
    source: dict[str, str],
) -> None:
    runtime_path = output / "mapping_replay_runtime.json"
    ply_path = output / "3dgs_before_final.ply"
    evaluation_path = output / "psnr/strict_fixed_manifest/final_result.json"
    harness = CUSTOM_HARNESS if arm in ("rr", "c2") else VANILLA_HARNESS
    config = CUSTOM_CONFIG if arm in ("rr", "c2") else VANILLA_CONFIG
    arm_name = {
        "rr": "c1_rr",
        "c2": "c1_global_residue_c2",
        "vanilla": "native_vanilla_render_matched",
    }[arm]
    source_commit = (
        source["paper_commit"] if arm in ("rr", "c2")
        else source["official_commit"]
    )
    values = {
        "protocol": "stage5_full_retention_replication_v1",
        "arm": arm_name,
        "dataset": "rpng",
        "sequence": "table_01",
        "seed": str(seed),
        "tracker_archive_seed": "0",
        "mapping_source_commit": source_commit,
        "paper_source_commit": source["paper_commit"],
        "official_source_commit": source["official_commit"],
        "lab_source_commit": source["lab_commit"],
        "archive_manifest_sha256": sha256(ARCHIVE / "archive_manifest.json"),
        "config_sha256": sha256(config),
        "fixed_manifest_sha256": sha256(FIXED_MANIFEST),
        "harness_sha256": sha256(harness),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "evaluator_sha256": sha256(EVALUATOR),
        "mapping_flags": shlex.join(command[2:]),
        "post_eos_optimizer_updates_required": "0",
        "final_ba": "off",
        "final_color_refinement": "off",
        "runtime_sha256": sha256(runtime_path),
        "ply_sha256": sha256(ply_path),
        "evaluation_sha256": sha256(evaluation_path),
        "mapping_log_sha256": sha256(output / "mapping.log"),
        "evaluation_log_sha256": sha256(output / "evaluation.log"),
    }
    (output / "source_manifest.txt").write_text(
        "".join(f"{key}={value}\n" for key, value in values.items()),
        encoding="utf-8",
    )


def run_arm(root: Path, seed: int, arm: str, dry_run: bool) -> None:
    source = require_predeclared_state()
    output = paths_for(root, seed)[arm]
    command = mapping_command(arm, seed, output, root)
    evaluation = evaluation_command(output)
    if arm == "vanilla":
        reference = paths_for(root, seed)["c2"] / "mapping_replay_runtime.json"
        if not reference.is_file():
            raise FileNotFoundError(f"run C2 first; missing {reference}")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    if dry_run:
        print(json.dumps({"mapping": command, "evaluation": evaluation}, indent=2))
        return
    output.mkdir(parents=True)
    ensure_archive_validation(output)
    run_logged(command, output / "mapping.log", mapping_environment(arm))
    run_logged(
        evaluation,
        output / "evaluation.log",
        evaluation_environment(),
    )
    validate_completed_run(output, seed)
    write_manifest(output, arm, seed, command, source)


def run_verifier(command: list[str]) -> None:
    subprocess.run(command, cwd=WORKSPACE, check=True)


def verify_seed(root: Path, seed: int) -> None:
    require_predeclared_state()
    paths = paths_for(root, seed)
    for role in ("rr", "c2", "vanilla"):
        validate_completed_run(paths[role], seed)
    for report in (paths["pair"], paths["render"]):
        if report.exists():
            raise FileExistsError(f"refusing to overwrite {report}")
        report.parent.mkdir(parents=True, exist_ok=True)
    run_verifier(
        [
            str(PYTHON_ENV / "bin/python"),
            str(PAIR_VERIFIER),
            "--rr-run",
            str(paths["rr"]),
            "--ercb-run",
            str(paths["c2"]),
            "--output",
            str(paths["pair"]),
        ]
    )
    run_verifier(
        [
            str(PYTHON_ENV / "bin/python"),
            str(RENDER_VERIFIER),
            "--d1-run",
            str(paths["c2"]),
            "--vanilla-run",
            str(paths["vanilla"]),
            "--output",
            str(paths["render"]),
        ]
    )


def verify_cohort(root: Path) -> None:
    require_predeclared_state()
    cohort = paths_for(root, EXPECTED_SEEDS[0])["cohort"]
    if cohort.exists():
        raise FileExistsError(f"refusing to overwrite {cohort}")
    command = [
        str(PYTHON_ENV / "bin/python"),
        str(COHORT_VERIFIER),
    ]
    for seed in EXPECTED_SEEDS:
        paths = paths_for(root, seed)
        command.extend(
            [
                "--entry",
                str(seed),
                str(paths["rr"]),
                str(paths["c2"]),
                str(paths["vanilla"]),
                str(paths["pair"]),
                str(paths["render"]),
            ]
        )
    cohort.parent.mkdir(parents=True, exist_ok=True)
    command.extend(("--output", str(cohort)))
    run_verifier(command)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    subparsers = parser.add_subparsers(dest="action", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--seed", type=int, choices=EXPECTED_SEEDS, required=True)
    run.add_argument("--arm", choices=("rr", "c2", "vanilla"), required=True)
    run.add_argument("--dry-run", action="store_true")
    seed_verify = subparsers.add_parser("verify-seed")
    seed_verify.add_argument(
        "--seed", type=int, choices=EXPECTED_SEEDS, required=True
    )
    subparsers.add_parser("verify-cohort")
    subparsers.add_parser("preflight")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if args.action == "run":
        run_arm(root, args.seed, args.arm, args.dry_run)
    elif args.action == "verify-seed":
        verify_seed(root, args.seed)
    elif args.action == "verify-cohort":
        verify_cohort(root)
    elif args.action == "preflight":
        print(json.dumps(require_predeclared_state(), indent=2, sort_keys=True))
    else:
        raise AssertionError(args.action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
