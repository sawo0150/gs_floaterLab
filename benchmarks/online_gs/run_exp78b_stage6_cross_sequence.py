#!/usr/bin/env python3
"""Run Stage-6 cross-sequence Full and C2 mapping-only confirmation panels."""

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

PAPER_COMMIT = "6f6b7d545d55be9fdcaec3d801a082c49698952e"
OFFICIAL_COMMIT = "22ffe24c6df81d0bf63bd20057565c00c51d2996"
MAPPER_SEED = 0

ARCHIVE_ROOT = (
    WORKSPACE
    / "results/experiments/exp78/b_strict_fair_comparison/frozen_tracker"
    / "official_22ffe24_trt"
)
MANIFEST_ROOT = (
    WORKSPACE / "context/experiments/exp78/b_strict_fair_comparison/manifests"
)
DEFAULT_ROOT = (
    WORKSPACE
    / "results/experiments/exp78/paper_full_staged_v1"
    / "stage6_cross_sequence_confirmation"
)

CUSTOM_HARNESS = WORKSPACE / "benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
VANILLA_HARNESS = WORKSPACE / "benchmarks/online_gs/exp78b_replay_vanilla_mapping.py"
EVALUATOR = WORKSPACE / "benchmarks/online_gs/exp78_evaluate_vigs_ply.py"
ARCHIVE_VALIDATOR = WORKSPACE / "benchmarks/online_gs/validate_exp78b_frozen_tracker.py"
RENDER_VERIFIER = WORKSPACE / "benchmarks/online_gs/verify_exp78b_d1_render_match.py"
PAIR_VERIFIER = PAPER_ROOT / "paper_full_stages/verify_stage3d_global_residue_isolation.py"
WORKLOAD_ANALYZER = PAPER_ROOT / "paper_full_stages/analyze_stage6_service_regime.py"
COHORT_VERIFIER = PAPER_ROOT / "paper_full_stages/verify_stage6_cross_sequence_confirmation.py"

# role, eval count, fixed-manifest SHA-256, archive-manifest SHA-256
SEQUENCES: dict[tuple[str, str], tuple[str, int, str, str]] = {
    ("rpng", "table_01"): ("development", 502, "f6bbdd74211c3bf75776f2d381db93fadf07e20fb8f2ec251118211cba925589", "cb7e31db582d41ea58ba3f4c4cc09558cfe5e5d049969dd69ad5fbf93cc3c5b0"),
    ("rpng", "table_02"): ("validation", 584, "8d688bf6cb04fc3e289de5e28e03248891dc3e8dd63bf286d44033268b626551", "e08428c63c97b97b8ec5f4818e69b5edc952ee4a2cc67cbcdf35229a1316fa04"),
    ("rpng", "table_03"): ("validation", 1402, "4b4a53e1e7fd804838cf862a19e091f983c6463a8e5747fb65c22d47ea27e608", "307eef0076dab57b94f3c3c3100fe3e0a24998b7e0924160aeadb4e9fccc17ba"),
    ("rpng", "table_04"): ("validation", 1215, "47516fdce0a657211da7d5a80a9d576ce11c2e05307e2b1996475c4b5cd90ca5", "1f56dd70b341de879f57b7e613d22a68a0831124b0612952694743b1c8e34367"),
    ("rpng", "table_05"): ("validation", 1234, "7e8c31e06280b52a217a8daf8046021d2654aee51049a88dcd71e96058d0fd37", "3c85628754e646801aefad2d8a72ecd05ec10effae775d9a45b30dad0d17c110"),
    ("rpng", "table_06"): ("development", 555, "dc75e1ce0c7a40611c0cf208091d1fc9c47b19127e2efcddd1c0ac8a952e406a", "4cca088609e3852706c66566beb2fb23a048fa8e24621d3efa77335fd2f4e322"),
    ("rpng", "table_07"): ("validation", 958, "091271497abbc6b56d36e4b0fcc6dd82e70d50ebe4ea46318bf8b4cde1c7d227", "bfa9c64c323ea6ec04e9ab6be403e44474f24e07756a9cb48f13a4251b1af468"),
    ("rpng", "table_08"): ("validation", 1698, "a9824cbcdbbedee592ae6eb107e8244753a15eb175c13480b814308b4e6b952f", "1a65a6e3baa9754ba965e26db7a282227dfeb1327650b9c0eac49aad8c5c2b52"),
    ("utmm", "ego-centric-1"): ("validation", 308, "398bf1bb30316a7f01908db42f860e488b9f62b70a875ebf5492cec2e1c2e62a", "77b8b9a843a8f3bbce9a41ceb2ac70d89074512fee206103362a12d96435ab99"),
    ("utmm", "ego-centric-2"): ("validation", 261, "07c485155b2bd90e6e45175c6c8d598ba734c331871850a5109ad83309788f7b", "9697429d3c543b5b5799764090c5bcd277fcbb4f551bd38a3162dbfd287b6663"),
    ("utmm", "ego-drive"): ("development", 281, "cdd1037b750df1fee6d9c7700cc8f18f43bb1d2be1548ca067ffdb92ee9e3191", "b76d81746d8e9e63f9f75f45ba2baca48465b3666cf90f07b8ddcf4b5ea4c1ba"),
    ("utmm", "fast-straight"): ("validation", 68, "4b4bd4d88d4224ed07817e95a5b84a2d82313b89d33f85421e1347f6eea0ea94", "1162b1659a925c357bc6f5a3620db5a8f3549e2625d0e49863763d43cc44bf17"),
    ("utmm", "slow-straight-1"): ("validation", 80, "a3dae3101602971e20cd18936c6b671dbe3c996749341a5f843dbd874cf0e924", "7843e9df6b154bbaa4534300c4166922c9fb9ba9802b1de0f0fdc9cc28b5334d"),
    ("utmm", "slow-straight-2"): ("validation", 121, "86ae7000517b7559016bda1b8ae9e94656795dbf342a419076b8f66eb6c102ba", "b213977e13cb047e5183536a577ff485ffb529848fd5cdf6b52ae77693d1e928"),
    ("utmm", "square-1"): ("validation", 324, "6a54fdd3ccf272b762c4c4ebca13803f09e28efe4f43cbddf940cbb80dba8e26", "db5de0b9d08ca77a08b45faeeeb406ae5c350fac1b2a6e901a9aa66a89a38dfb"),
    ("utmm", "square-2"): ("development", 245, "9332bc5f5a998579c06113471f70c2ddb7a0a230be43b33254ea4d89970036d7", "93eeca4b273dde26a7403e7b04bd03e30934d6c08f2ecb9799db9e27767662e9"),
}

EXPECTED_HASHES = {
    CUSTOM_HARNESS: "9d50dbb9d20374b47289dce4327cf3dad23c9d48a5fc055f82241c0a0bf7c67c",
    VANILLA_HARNESS: "cabdb4df902bfb278b0b590af5dcf31b40921bd76a09d3225991a4f9b3741765",
    EVALUATOR: "f854084b249cea724b7be65a1655088ce8906203110f52c6503b052ec3b51c3c",
    ARCHIVE_VALIDATOR: "b2c2e050ddff373cd5e4062460fa021a141d206673a98d87fe531d3b917afccc",
    RENDER_VERIFIER: "e3364d6e6fa21e90ef29ad35fe2b802e11edce993302d0156012bf742c739840",
    PAIR_VERIFIER: "0d2aa98d17cb0f31ddeee80813c039125ca3de73999cb877a795ddad4c05e2cb",
    WORKLOAD_ANALYZER: "2dcc65a6b6610408e3b80328ad15709fcb0c1721f0187425fa5e432c381f569d",
    COHORT_VERIFIER: "f6937742eae5044d6fca9745fb84a5a8c42164f988238c55357f28a6646aecc5",
    WORKSPACE / "benchmarks/online_gs/config/vigs_final_v7_rpng.yaml": "138fdd26a99be125fab900ba9e731d38660ee7d2dd8e5f6833496a16045ccf54",
    WORKSPACE / "benchmarks/online_gs/config/vigs_final_v7_utmm.yaml": "b68693bf2d91291af1b5bd8cbd5489427445b7ff6048722f5736d14e1a6516c4",
    OFFICIAL_ROOT / "config/rpng.yaml": "cd1713e83927cf84a4d841b0661207fa6da0c4ba56bcbc3540830b9fcc5421c3",
    OFFICIAL_ROOT / "config/utmm.yaml": "9fe132f363244207f74d8952d9a1715e6e965b1968e8076433b9a606dc103af1",
}

FULL_FLAGS = (
    "--time-scale", "unbounded", "--deadline-reserve-ms", "20",
    "--fixed-event-dense-opportunities-per-packet", "1",
    "--compute-paced-dense-admission", "--compute-paced-dense-token-cost", "22",
    "--c1-c2-global-residue-integration", "--service-shortfall-ercb",
    "--density-policy", "online_rank", "--online-density-mean-multiplier", "2.5",
    "--online-density-span", "2.0", "--dense-replay-scope", "appearance",
    "--profile", "dense_rr_imu", "--observation-topology-gate",
)

C2_COMMON_FLAGS = (
    "--time-scale", "unbounded", "--deadline-reserve-ms", "20",
    "--fixed-event-dense-opportunities-per-packet", "1",
    "--c2-global-residue-isolation", "--density-policy", "online_rank",
    "--online-density-mean-multiplier", "2.5", "--online-density-span", "2.0",
    "--dense-replay-scope", "appearance", "--profile", "dense_rr_imu",
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


def sequence_paths(dataset: str, sequence: str) -> dict[str, Path]:
    if (dataset, sequence) not in SEQUENCES:
        raise ValueError(f"unsupported sequence: {dataset}/{sequence}")
    archive = ARCHIVE_ROOT / dataset / sequence / "seed0"
    manifest = MANIFEST_ROOT / f"{dataset}_{sequence}.json"
    custom_config = WORKSPACE / f"benchmarks/online_gs/config/vigs_final_v7_{dataset}.yaml"
    vanilla_config = OFFICIAL_ROOT / f"config/{dataset}.yaml"
    if dataset == "rpng":
        image_dir = WORKSPACE / f"data/benchmarks/rpng/prepared/rpngar/{sequence}/rgb"
        calibration = OFFICIAL_ROOT / "calib/rpngar.txt"
    else:
        base = WORKSPACE / f"data/benchmarks/utmm/prepared/UTMM_Dataset/{sequence}"
        image_dir = base / "rgb_timestamp"
        calibration = base / "intrinsics_ours.txt"
    return {
        "archive": archive,
        "manifest": manifest,
        "custom_config": custom_config,
        "vanilla_config": vanilla_config,
        "image_dir": image_dir,
        "calibration": calibration,
    }


def run_paths(root: Path, dataset: str, sequence: str) -> dict[str, Path]:
    base = root / dataset / sequence
    return {
        "full": base / "stage6a_c1_global_residue_c2_full_s0",
        "vanilla": base / "stage6a_native_vanilla_render_matched_s0",
        "rr": base / "stage6b_c1_off_rr_s0",
        "c2": base / "stage6b_c1_off_global_residue_c2_s0",
        "full_report": base / "verification/stage6a_render_match_s0.json",
        "c2_report": base / "verification/stage6b_pair_s0.json",
    }


def workload_path(output: Path) -> Path:
    return output / "stage6_service_regime.json"


def mapping_command(
    panel: str, arm: str, dataset: str, sequence: str, root: Path
) -> list[str]:
    paths = sequence_paths(dataset, sequence)
    outputs = run_paths(root, dataset, sequence)
    common = [
        "--archive", str(paths["archive"]), "--output", str(outputs[arm]),
        "--seed", str(MAPPER_SEED),
    ]
    python = str(PYTHON_ENV / "bin/python")
    if panel == "full" and arm == "full":
        return [python, str(CUSTOM_HARNESS), *common, "--config",
                str(paths["custom_config"]), *FULL_FLAGS]
    if panel == "full" and arm == "vanilla":
        reference = outputs["full"] / "mapping_replay_runtime.json"
        return [
            python, str(VANILLA_HARNESS), *common, "--config",
            str(paths["vanilla_config"]), "--time-scale", "unbounded",
            "--deadline-reserve-ms", "20", "--mapping-after-metric-init",
            "--reference-service-runtime", str(reference),
        ]
    if panel == "c2" and arm in ("rr", "c2"):
        command = [python, str(CUSTOM_HARNESS), *common, "--config",
                   str(paths["custom_config"]), *C2_COMMON_FLAGS]
        if arm == "c2":
            command.append("--service-shortfall-ercb")
        return command
    raise ValueError(f"arm {arm!r} is invalid for panel {panel!r}")


def evaluation_command(output: Path, dataset: str, sequence: str) -> list[str]:
    paths = sequence_paths(dataset, sequence)
    return [
        str(PYTHON_ENV / "bin/python"), str(EVALUATOR), "--run-dir", str(output),
        "--image-dir", str(paths["image_dir"]), "--calib", str(paths["calibration"]),
        "--manifest", str(paths["manifest"]), "--rgb-file-in-nanoseconds",
        "--undistort", "--mapped-uids-json", str(output / "mapped_uids.json"),
        "--result-subdir", "strict_fixed_manifest",
    ]


def mapping_environment(custom: bool) -> dict[str, str]:
    env = os.environ.copy()
    torch_lib = PYTHON_ENV / "lib/python3.11/site-packages/torch/lib"
    old_library_path = env.get("LD_LIBRARY_PATH")
    env["LD_LIBRARY_PATH"] = ":".join(
        value for value in (str(torch_lib), str(PYTHON_ENV / "lib"), old_library_path)
        if value
    )
    built = BUILT_THIRDPARTY_ROOT / "thirdparty"
    if custom:
        components = (
            PAPER_ROOT / "vigs", PAPER_ROOT, BUILT_THIRDPARTY_ROOT,
            built / "diff-gaussian-rasterization", built / "lietorch_5090",
            built / "simple-knn",
        )
        env["EXP78B_CUSTOM_ROOT"] = str(PAPER_ROOT)
    else:
        components = (
            OFFICIAL_ROOT / "vigs",
            OFFICIAL_ROOT / "thirdparty/diff-gaussian-rasterization",
            built / "lietorch_5090", built / "simple-knn",
        )
    old_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = ":".join(
        value for value in (*map(str, components), old_pythonpath) if value
    )
    env["PYTHONUNBUFFERED"] = "1"
    return env


def require_predeclared_state() -> dict[str, Any]:
    required = [
        CUSTOM_HARNESS, VANILLA_HARNESS, EVALUATOR, ARCHIVE_VALIDATOR,
        RENDER_VERIFIER, PAIR_VERIFIER, WORKLOAD_ANALYZER, COHORT_VERIFIER,
        PYTHON_ENV / "bin/python", *EXPECTED_HASHES,
    ]
    for dataset, sequence in SEQUENCES:
        paths = sequence_paths(dataset, sequence)
        required.extend(paths.values())
    missing = sorted({str(path) for path in required if not path.exists()})
    if missing:
        raise FileNotFoundError("missing Stage-6 inputs:\n" + "\n".join(missing))
    paper_commit = git_output(PAPER_ROOT, "rev-parse", "HEAD")
    official_commit = git_output(OFFICIAL_ROOT, "rev-parse", "HEAD")
    if paper_commit != PAPER_COMMIT:
        raise RuntimeError(f"paper source moved: expected {PAPER_COMMIT}, got {paper_commit}")
    if official_commit != OFFICIAL_COMMIT:
        raise RuntimeError(
            f"official source moved: expected {OFFICIAL_COMMIT}, got {official_commit}"
        )
    for repository in (PAPER_ROOT, OFFICIAL_ROOT):
        subprocess.run(("git", "-C", str(repository), "diff", "--quiet",
                        "--ignore-submodules=dirty"), check=True)
        subprocess.run(("git", "-C", str(repository), "diff", "--cached", "--quiet",
                        "--ignore-submodules=dirty"), check=True)
    mismatches = {
        str(path): {"expected": expected, "actual": sha256(path)}
        for path, expected in EXPECTED_HASHES.items() if sha256(path) != expected
    }
    for (dataset, sequence), (_, _, fixed_hash, archive_hash) in SEQUENCES.items():
        paths = sequence_paths(dataset, sequence)
        for path, expected in (
            (paths["manifest"], fixed_hash),
            (paths["archive"] / "archive_manifest.json", archive_hash),
        ):
            actual = sha256(path)
            if actual != expected:
                mismatches[str(path)] = {"expected": expected, "actual": actual}
    if mismatches:
        raise RuntimeError(
            "predeclared source/input hash mismatch:\n"
            + json.dumps(mismatches, indent=2, sort_keys=True)
        )
    subprocess.run(
        (str(PYTHON_ENV / "bin/python"), "-c",
         "import vigs_backends, lietorch, diff_gaussian_rasterization, simple_knn"),
        cwd=WORKSPACE, env=mapping_environment(True), check=True,
    )
    validation = sum(spec[0] == "validation" for spec in SEQUENCES.values())
    return {
        "paper_commit": paper_commit, "official_commit": official_commit,
        "lab_commit": git_output(WORKSPACE, "rev-parse", "HEAD"),
        "sequences": len(SEQUENCES), "validation_sequences": validation,
    }


def run_logged(command: list[str], log: Path, env: dict[str, str]) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as sink:
        process = subprocess.Popen(
            command, cwd=WORKSPACE, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1,
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


def ensure_archive_validation(archive: Path, output: Path) -> None:
    cache = archive / "validation.json"
    archive_hash = sha256(archive / "archive_manifest.json")
    valid = False
    if cache.is_file():
        try:
            report = read_json(cache)
            valid = report.get("valid") is True and report.get("archive_manifest_sha256") == archive_hash
        except (OSError, ValueError, json.JSONDecodeError):
            valid = False
    if not valid:
        run_logged(
            [str(PYTHON_ENV / "bin/python"), str(ARCHIVE_VALIDATOR), str(archive),
             "--output", str(cache)],
            output / "archive_validation.log", mapping_environment(False),
        )
        if read_json(cache).get("valid") is not True:
            raise RuntimeError("frozen archive validation failed")
    else:
        (output / "archive_validation.log").write_text(
            f"reused {cache}\n", encoding="utf-8"
        )
    shutil.copy2(cache, output / "frozen_archive_validation.json")


def validate_completed_run(output: Path, dataset: str, sequence: str) -> dict[str, Any]:
    role, expected_count, _, archive_hash = SEQUENCES[(dataset, sequence)]
    runtime = read_json(output / "mapping_replay_runtime.json")
    if int(runtime.get("seed", -1)) != MAPPER_SEED:
        raise RuntimeError("runtime mapper seed mismatch")
    if runtime.get("archive_manifest_sha256") != archive_hash:
        raise RuntimeError("runtime frozen archive mismatch")
    if int(runtime.get("post_eos_optimizer_updates", -1)) != 0:
        raise RuntimeError("zero-tail violation")
    if runtime.get("final_ba_performed") is not False:
        raise RuntimeError("unexpected final BA")
    if runtime.get("final_color_refinement_performed") is not False:
        raise RuntimeError("unexpected final color refinement")
    fixed = read_json(
        output / "psnr/strict_fixed_manifest/final_result.json"
    ).get("predeclared_fixed_manifest_posthoc") or {}
    if int(fixed.get("view_count", -1)) != expected_count:
        raise RuntimeError("fixed held-out evaluator view-count mismatch")
    if fixed.get("mapping_disjoint") is not True:
        raise RuntimeError("fixed held-out evaluator is not mapping-disjoint")
    return {"runtime": runtime, "role": role}


def write_manifest(
    output: Path, panel: str, arm: str, dataset: str, sequence: str,
    command: list[str], source: dict[str, Any],
) -> None:
    paths = sequence_paths(dataset, sequence)
    role = SEQUENCES[(dataset, sequence)][0]
    custom = arm != "vanilla"
    config = paths["custom_config"] if custom else paths["vanilla_config"]
    harness = CUSTOM_HARNESS if custom else VANILLA_HARNESS
    arm_name = {
        "full": "c1_global_residue_c2_full",
        "vanilla": "native_vanilla_render_matched",
        "rr": "c1_off_rr",
        "c2": "c1_off_global_residue_c2",
    }[arm]
    files = {
        "runtime_sha256": output / "mapping_replay_runtime.json",
        "ply_sha256": output / "3dgs_before_final.ply",
        "evaluation_sha256": output / "psnr/strict_fixed_manifest/final_result.json",
        "mapping_log_sha256": output / "mapping.log",
        "evaluation_log_sha256": output / "evaluation.log",
        "archive_validation_sha256": output / "frozen_archive_validation.json",
    }
    if custom:
        files["workload_report_sha256"] = workload_path(output)
    values = {
        "protocol": "stage6_cross_sequence_confirmation_runner_v1",
        "panel": panel, "arm": arm_name, "dataset": dataset,
        "sequence": sequence, "role": role, "seed": str(MAPPER_SEED),
        "tracker_archive_seed": "0",
        "mapping_source_commit": source["paper_commit"] if custom else source["official_commit"],
        "paper_source_commit": source["paper_commit"],
        "official_source_commit": source["official_commit"],
        "lab_source_commit": source["lab_commit"],
        "archive_manifest_sha256": sha256(paths["archive"] / "archive_manifest.json"),
        "config_sha256": sha256(config), "fixed_manifest_sha256": sha256(paths["manifest"]),
        "harness_sha256": sha256(harness), "runner_sha256": sha256(Path(__file__).resolve()),
        "evaluator_sha256": sha256(EVALUATOR), "mapping_flags": shlex.join(command[2:]),
        "post_eos_optimizer_updates_required": "0", "final_ba": "off",
        "final_color_refinement": "off",
        **{key: sha256(path) for key, path in files.items()},
    }
    (output / "source_manifest.txt").write_text(
        "".join(f"{key}={value}\n" for key, value in values.items()), encoding="utf-8"
    )


def run_arm(
    root: Path, panel: str, arm: str, dataset: str, sequence: str, dry_run: bool
) -> None:
    source = require_predeclared_state()
    outputs = run_paths(root, dataset, sequence)
    output = outputs[arm]
    command = mapping_command(panel, arm, dataset, sequence, root)
    evaluation = evaluation_command(output, dataset, sequence)
    if dry_run:
        print(json.dumps({"mapping": command, "evaluation": evaluation}, indent=2))
        return
    if arm == "vanilla" and not (
        outputs["full"] / "mapping_replay_runtime.json"
    ).is_file():
        raise FileNotFoundError("run Stage-6A Full before its vanilla match")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    paths = sequence_paths(dataset, sequence)
    output.mkdir(parents=True)
    ensure_archive_validation(paths["archive"], output)
    custom = arm != "vanilla"
    run_logged(command, output / "mapping.log", mapping_environment(custom))
    if custom:
        run_logged(
            [str(PYTHON_ENV / "bin/python"), str(WORKLOAD_ANALYZER),
             "--runtime", str(output / "mapping_replay_runtime.json"),
             "--archive", str(paths["archive"]), "--output", str(workload_path(output))],
            output / "workload_analysis.log", mapping_environment(True),
        )
    run_logged(evaluation, output / "evaluation.log", mapping_environment(False))
    validate_completed_run(output, dataset, sequence)
    write_manifest(output, panel, arm, dataset, sequence, command, source)


def verify_pair(root: Path, panel: str, dataset: str, sequence: str) -> None:
    require_predeclared_state()
    paths = run_paths(root, dataset, sequence)
    if panel == "full":
        arms, report = ("full", "vanilla"), paths["full_report"]
        command = [
            str(PYTHON_ENV / "bin/python"), str(RENDER_VERIFIER),
            "--d1-run", str(paths["full"]), "--vanilla-run", str(paths["vanilla"]),
            "--output", str(report),
        ]
    else:
        arms, report = ("rr", "c2"), paths["c2_report"]
        command = [
            str(PYTHON_ENV / "bin/python"), str(PAIR_VERIFIER),
            "--rr-run", str(paths["rr"]), "--ercb-run", str(paths["c2"]),
            "--output", str(report),
        ]
    for arm in arms:
        validate_completed_run(paths[arm], dataset, sequence)
        if arm != "vanilla" and not workload_path(paths[arm]).is_file():
            raise FileNotFoundError(f"missing workload report for {paths[arm]}")
    if report.exists():
        raise FileExistsError(f"refusing to overwrite {report}")
    report.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(command, cwd=WORKSPACE, check=True)


def validation_entries(root: Path, panel: str) -> list[dict[str, str]]:
    entries = []
    for (dataset, sequence), (role, _, _, _) in sorted(SEQUENCES.items()):
        if role != "validation":
            continue
        paths = run_paths(root, dataset, sequence)
        if panel == "full":
            entries.append({
                "dataset": dataset, "sequence": sequence,
                "full_run": str(paths["full"]), "vanilla_run": str(paths["vanilla"]),
                "render_report": str(paths["full_report"]),
                "workload_report": str(workload_path(paths["full"])),
            })
        else:
            entries.append({
                "dataset": dataset, "sequence": sequence,
                "rr_run": str(paths["rr"]), "c2_run": str(paths["c2"]),
                "pair_report": str(paths["c2_report"]),
                "rr_workload_report": str(workload_path(paths["rr"])),
                "c2_workload_report": str(workload_path(paths["c2"])),
            })
    return entries


def verify_cohort(root: Path, panel: str) -> None:
    require_predeclared_state()
    verification = root / "verification"
    entries_path = verification / f"stage6{panel}_validation_entries.json"
    report_path = verification / f"stage6{panel}_validation_cohort.json"
    for path in (entries_path, report_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite {path}")
    verification.mkdir(parents=True, exist_ok=True)
    entries_path.write_text(
        json.dumps(validation_entries(root, panel), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    subprocess.run(
        [str(PYTHON_ENV / "bin/python"), str(COHORT_VERIFIER), "--panel", panel,
         "--entries", str(entries_path), "--output", str(report_path)],
        cwd=WORKSPACE, check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    subparsers = parser.add_subparsers(dest="action", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--panel", choices=("full", "c2"), required=True)
    run.add_argument("--arm", choices=("full", "vanilla", "rr", "c2"), required=True)
    run.add_argument("--dataset", choices=("rpng", "utmm"), required=True)
    run.add_argument("--sequence", required=True)
    run.add_argument("--dry-run", action="store_true")
    pair = subparsers.add_parser("verify-pair")
    pair.add_argument("--panel", choices=("full", "c2"), required=True)
    pair.add_argument("--dataset", choices=("rpng", "utmm"), required=True)
    pair.add_argument("--sequence", required=True)
    cohort = subparsers.add_parser("verify-cohort")
    cohort.add_argument("--panel", choices=("full", "c2"), required=True)
    subparsers.add_parser("preflight")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if args.action == "run":
        run_arm(root, args.panel, args.arm, args.dataset, args.sequence, args.dry_run)
    elif args.action == "verify-pair":
        verify_pair(root, args.panel, args.dataset, args.sequence)
    elif args.action == "verify-cohort":
        verify_cohort(root, args.panel)
    elif args.action == "preflight":
        print(json.dumps(require_predeclared_state(), indent=2, sort_keys=True))
    else:
        raise AssertionError(args.action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
