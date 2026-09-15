#!/usr/bin/env python3
"""Run the predeclared table_01 Stage-6R R4 selector-only experiment."""

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

PAPER_COMMIT = "eb5fa99fecab4a85408bfb1baa8db197857ea231"
OFFICIAL_COMMIT = "22ffe24c6df81d0bf63bd20057565c00c51d2996"
SEED = 0
EXPECTED_VIEW_COUNT = 502

ARCHIVE = (
    WORKSPACE
    / "results/experiments/exp78/b_strict_fair_comparison/frozen_tracker"
    / "official_22ffe24_trt/rpng/table_01/seed0"
)
CUSTOM_CONFIG = WORKSPACE / "benchmarks/online_gs/config/vigs_final_v7_rpng.yaml"
VANILLA_CONFIG = OFFICIAL_ROOT / "config/rpng.yaml"
FIXED_MANIFEST = (
    WORKSPACE
    / "context/experiments/exp78/b_strict_fair_comparison/manifests"
    / "rpng_table_01.json"
)
IMAGE_DIR = WORKSPACE / "data/benchmarks/rpng/prepared/rpngar/table_01/rgb"
CALIBRATION = OFFICIAL_ROOT / "calib/rpngar.txt"
CUSTOM_HARNESS = WORKSPACE / "benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
VANILLA_HARNESS = WORKSPACE / "benchmarks/online_gs/exp78b_replay_vanilla_mapping.py"
EVALUATOR = WORKSPACE / "benchmarks/online_gs/exp78_evaluate_vigs_ply.py"
ARCHIVE_VALIDATOR = WORKSPACE / "benchmarks/online_gs/validate_exp78b_frozen_tracker.py"
R4_VERIFIER = WORKSPACE / "benchmarks/online_gs/verify_exp78b_stage6r_r4_native_keyframe.py"
RENDER_VERIFIER = WORKSPACE / "benchmarks/online_gs/verify_exp78b_d1_render_match.py"
DEFAULT_ROOT = (
    WORKSPACE
    / "results/experiments/exp78/paper_full_staged_v1"
    / "stage6r_r4_native_global_keyframe/rpng/table_01"
)

EXPECTED_HASHES = {
    CUSTOM_HARNESS: "e0a2bcf50ae1354bb79efe79009f1e23567243942a6d358b95a8c5937c16bf16",
    VANILLA_HARNESS: "cabdb4df902bfb278b0b590af5dcf31b40921bd76a09d3225991a4f9b3741765",
    EVALUATOR: "f854084b249cea724b7be65a1655088ce8906203110f52c6503b052ec3b51c3c",
    ARCHIVE_VALIDATOR: "b2c2e050ddff373cd5e4062460fa021a141d206673a98d87fe531d3b917afccc",
    R4_VERIFIER: "3cc9da551d5fdb08155afbd5c3ae37a74ba3d73a84550ca93c6184a12a259bc6",
    RENDER_VERIFIER: "e3364d6e6fa21e90ef29ad35fe2b802e11edce993302d0156012bf742c739840",
    CUSTOM_CONFIG: "138fdd26a99be125fab900ba9e731d38660ee7d2dd8e5f6833496a16045ccf54",
    VANILLA_CONFIG: "cd1713e83927cf84a4d841b0661207fa6da0c4ba56bcbc3540830b9fcc5421c3",
    FIXED_MANIFEST: "f6bbdd74211c3bf75776f2d381db93fadf07e20fb8f2ec251118211cba925589",
    ARCHIVE / "archive_manifest.json": "cb7e31db582d41ea58ba3f4c4cc09558cfe5e5d049969dd69ad5fbf93cc3c5b0",
}

CUSTOM_FLAGS = (
    "--time-scale", "unbounded",
    "--deadline-reserve-ms", "20",
    "--fixed-event-dense-opportunities-per-packet", "1",
    "--compute-paced-dense-admission",
    "--compute-paced-dense-token-cost", "1",
    "--c1-c2-global-residue-integration",
    "--service-shortfall-ercb",
    "--stage6r-keyframe-appearance-replay",
    "--stage6r-native-global-keyframe-selection-audit",
    "--density-policy", "online_rank",
    "--online-density-mean-multiplier", "2.5",
    "--online-density-span", "2.0",
    "--dense-replay-scope", "appearance",
    "--profile", "dense_rr_imu",
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
    return subprocess.check_output(("git", "-C", str(root), *args), text=True).strip()


def paths_for(root: Path) -> dict[str, Path]:
    verification = root / "verification"
    return {
        "control": root / "r3_uniform_audited_s0",
        "candidate": root / "r4_native_global_keyframe_ercb_s0",
        "vanilla": root / "native_vanilla_render_matched_r4_s0",
        "structure": verification / "r4_structural_prequality_v2.json",
        "render": verification / "r4_render_match.json",
        "final": verification / "r4_final_gate.json",
    }


def mapping_environment(arm: str) -> dict[str, str]:
    env = os.environ.copy()
    torch_lib = PYTHON_ENV / "lib/python3.11/site-packages/torch/lib"
    built = BUILT_THIRDPARTY_ROOT / "thirdparty"
    if arm in {"control", "candidate"}:
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
    env["LD_LIBRARY_PATH"] = ":".join(
        value
        for value in (
            str(torch_lib),
            str(PYTHON_ENV / "lib"),
            env.get("LD_LIBRARY_PATH"),
        )
        if value
    )
    env["PYTHONPATH"] = ":".join(
        value
        for value in (*map(str, components), env.get("PYTHONPATH"))
        if value
    )
    env["PYTHONUNBUFFERED"] = "1"
    return env


def mapping_command(arm: str, output: Path, root: Path) -> list[str]:
    python = str(PYTHON_ENV / "bin/python")
    common = [
        "--archive", str(ARCHIVE),
        "--output", str(output),
        "--seed", str(SEED),
    ]
    if arm in {"control", "candidate"}:
        command = [
            python,
            str(CUSTOM_HARNESS),
            *common,
            "--config", str(CUSTOM_CONFIG),
            *CUSTOM_FLAGS,
        ]
        if arm == "candidate":
            command.append("--stage6r-native-global-keyframe-ercb")
        return command
    if arm == "vanilla":
        reference = paths_for(root)["candidate"] / "mapping_replay_runtime.json"
        return [
            python,
            str(VANILLA_HARNESS),
            *common,
            "--config", str(VANILLA_CONFIG),
            "--time-scale", "unbounded",
            "--deadline-reserve-ms", "20",
            "--mapping-after-metric-init",
            "--reference-service-runtime", str(reference),
        ]
    raise ValueError(f"unsupported arm: {arm}")


def evaluation_command(output: Path) -> list[str]:
    return [
        str(PYTHON_ENV / "bin/python"),
        str(EVALUATOR),
        "--run-dir", str(output),
        "--image-dir", str(IMAGE_DIR),
        "--calib", str(CALIBRATION),
        "--manifest", str(FIXED_MANIFEST),
        "--rgb-file-in-nanoseconds",
        "--undistort",
        "--mapped-uids-json", str(output / "mapped_uids.json"),
        "--result-subdir", "strict_fixed_manifest",
    ]


def require_predeclared_state() -> dict[str, str]:
    required = (
        *EXPECTED_HASHES,
        IMAGE_DIR,
        CALIBRATION,
        PYTHON_ENV / "bin/python",
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing R4 input:\n" + "\n".join(missing))
    paper_commit = git_output(PAPER_ROOT, "rev-parse", "HEAD")
    official_commit = git_output(OFFICIAL_ROOT, "rev-parse", "HEAD")
    if paper_commit != PAPER_COMMIT:
        raise RuntimeError(f"paper source moved: expected {PAPER_COMMIT}, got {paper_commit}")
    if official_commit != OFFICIAL_COMMIT:
        raise RuntimeError(
            f"official source moved: expected {OFFICIAL_COMMIT}, got {official_commit}"
        )
    for root in (PAPER_ROOT, OFFICIAL_ROOT):
        subprocess.run(
            ("git", "-C", str(root), "diff", "--quiet", "--ignore-submodules=dirty"),
            check=True,
        )
        subprocess.run(
            ("git", "-C", str(root), "diff", "--cached", "--quiet", "--ignore-submodules=dirty"),
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
        env=mapping_environment("control"),
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
                "--output", str(cache),
            ],
            output / "archive_validation.log",
            mapping_environment("vanilla"),
        )
    shutil.copy2(cache, output / "frozen_archive_validation.json")


def validate_mapping(output: Path, arm: str) -> dict[str, Any]:
    runtime = read_json(output / "mapping_replay_runtime.json")
    if int(runtime.get("seed", -1)) != SEED:
        raise RuntimeError("runtime mapper seed mismatch")
    if runtime.get("archive_manifest_sha256") != EXPECTED_HASHES[ARCHIVE / "archive_manifest.json"]:
        raise RuntimeError("runtime archive mismatch")
    if int(runtime.get("post_eos_optimizer_updates", -1)) != 0:
        raise RuntimeError("zero-tail violation")
    if runtime.get("final_ba_performed") is not False:
        raise RuntimeError("unexpected final BA")
    if runtime.get("final_color_refinement_performed") is not False:
        raise RuntimeError("unexpected final color refinement")
    if arm in {"control", "candidate"}:
        if runtime.get("protocol") != "exp78b_gsslam_frozen_mapping_replay_v29":
            raise RuntimeError("R4 runtime protocol mismatch")
        if runtime.get("stage6r_native_global_keyframe_selection_audit") is not True:
            raise RuntimeError("R4 native-global audit missing")
        expected_ercb = arm == "candidate"
        if runtime.get("stage6r_native_global_keyframe_ercb") is not expected_ercb:
            raise RuntimeError("R4 arm role mismatch")
    return runtime


def validate_evaluation(output: Path) -> None:
    result = read_json(output / "psnr/strict_fixed_manifest/final_result.json")
    fixed = result.get("predeclared_fixed_manifest_posthoc") or {}
    if int(fixed.get("view_count", -1)) != EXPECTED_VIEW_COUNT:
        raise RuntimeError("fixed held-out view-count mismatch")
    if fixed.get("mapping_disjoint") is not True:
        raise RuntimeError("fixed evaluator is not mapping-disjoint")


def map_arm(root: Path, arm: str, dry_run: bool) -> None:
    require_predeclared_state()
    output = paths_for(root)[arm]
    command = mapping_command(arm, output, root)
    if arm == "vanilla" and not (paths_for(root)["candidate"] / "mapping_replay_runtime.json").is_file():
        raise FileNotFoundError("map the R4 candidate before render-matched vanilla")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    if dry_run:
        print(json.dumps({"mapping": command}, indent=2))
        return
    output.mkdir(parents=True)
    ensure_archive_validation(output)
    run_logged(command, output / "mapping.log", mapping_environment(arm))
    validate_mapping(output, arm)


def verify_structure(root: Path) -> None:
    require_predeclared_state()
    paths = paths_for(root)
    for arm in ("control", "candidate"):
        validate_mapping(paths[arm], arm)
    if paths["structure"].exists():
        raise FileExistsError(f"refusing to overwrite {paths['structure']}")
    subprocess.run(
        [
            str(PYTHON_ENV / "bin/python"),
            str(R4_VERIFIER),
            "--control", str(paths["control"]),
            "--candidate", str(paths["candidate"]),
            "--structural-only",
            "--output", str(paths["structure"]),
        ],
        cwd=WORKSPACE,
        check=True,
    )


def evaluate_arm(root: Path, arm: str, dry_run: bool) -> None:
    require_predeclared_state()
    paths = paths_for(root)
    structure = read_json(paths["structure"])
    if structure.get("valid") is not True:
        raise RuntimeError("pre-quality R4 structural verifier did not pass")
    output = paths[arm]
    validate_mapping(output, arm)
    evaluation_path = output / "psnr/strict_fixed_manifest/final_result.json"
    if evaluation_path.exists():
        raise FileExistsError(f"refusing to overwrite {evaluation_path}")
    command = evaluation_command(output)
    if dry_run:
        print(json.dumps({"evaluation": command}, indent=2))
        return
    run_logged(command, output / "evaluation.log", mapping_environment("vanilla"))
    validate_evaluation(output)
    write_manifest(output, arm, mapping_command(arm, output, root))


def write_manifest(output: Path, arm: str, command: list[str]) -> None:
    harness = CUSTOM_HARNESS if arm in {"control", "candidate"} else VANILLA_HARNESS
    config = CUSTOM_CONFIG if arm in {"control", "candidate"} else VANILLA_CONFIG
    values = {
        "protocol": "stage6r_r4_native_global_keyframe_v1",
        "arm": arm,
        "dataset": "rpng",
        "sequence": "table_01",
        "seed": str(SEED),
        "paper_source_commit": PAPER_COMMIT,
        "official_source_commit": OFFICIAL_COMMIT,
        "lab_source_commit": git_output(WORKSPACE, "rev-parse", "HEAD"),
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
        "runtime_sha256": sha256(output / "mapping_replay_runtime.json"),
        "ply_sha256": sha256(output / "3dgs_before_final.ply"),
        "evaluation_sha256": sha256(output / "psnr/strict_fixed_manifest/final_result.json"),
        "mapping_log_sha256": sha256(output / "mapping.log"),
        "evaluation_log_sha256": sha256(output / "evaluation.log"),
    }
    (output / "source_manifest.txt").write_text(
        "".join(f"{key}={value}\n" for key, value in values.items()),
        encoding="utf-8",
    )


def verify_final(root: Path) -> bool:
    require_predeclared_state()
    paths = paths_for(root)
    structure = read_json(paths["structure"])
    if structure.get("valid") is not True:
        raise RuntimeError("pre-quality structural verification is invalid")
    for arm in ("control", "candidate", "vanilla"):
        validate_mapping(paths[arm], arm)
        validate_evaluation(paths[arm])
    for report in (paths["render"], paths["final"]):
        if report.exists():
            raise FileExistsError(f"refusing to overwrite {report}")
        report.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            str(PYTHON_ENV / "bin/python"),
            str(RENDER_VERIFIER),
            "--d1-run", str(paths["candidate"]),
            "--vanilla-run", str(paths["vanilla"]),
            "--output", str(paths["render"]),
        ],
        cwd=WORKSPACE,
        check=True,
    )
    completed = subprocess.run(
        [
            str(PYTHON_ENV / "bin/python"),
            str(R4_VERIFIER),
            "--control", str(paths["control"]),
            "--candidate", str(paths["candidate"]),
            "--render-match-report", str(paths["render"]),
            "--output", str(paths["final"]),
        ],
        cwd=WORKSPACE,
        check=False,
    )
    return completed.returncode == 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    actions = parser.add_subparsers(dest="action", required=True)
    mapping = actions.add_parser("map")
    mapping.add_argument("--arm", choices=("control", "candidate", "vanilla"), required=True)
    mapping.add_argument("--dry-run", action="store_true")
    actions.add_parser("verify-structure")
    evaluation = actions.add_parser("evaluate")
    evaluation.add_argument("--arm", choices=("control", "candidate", "vanilla"), required=True)
    evaluation.add_argument("--dry-run", action="store_true")
    actions.add_parser("verify-final")
    actions.add_parser("preflight")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if args.action == "map":
        map_arm(root, args.arm, args.dry_run)
    elif args.action == "verify-structure":
        verify_structure(root)
    elif args.action == "evaluate":
        evaluate_arm(root, args.arm, args.dry_run)
    elif args.action == "verify-final":
        passed = verify_final(root)
        print(json.dumps({"r4_final_gate_passed": passed}))
    elif args.action == "preflight":
        print(json.dumps(require_predeclared_state(), indent=2, sort_keys=True))
    else:
        raise AssertionError(args.action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
