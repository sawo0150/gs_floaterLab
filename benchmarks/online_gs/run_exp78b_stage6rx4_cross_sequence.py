#!/usr/bin/env python3
"""Run the frozen Stage-6R-X4 R4 Full cross-sequence B-track cohort."""

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

PAPER_COMMIT = "07a09aa7d3a1461f9d67106e45dc094f6c9724ee"
OFFICIAL_COMMIT = "22ffe24c6df81d0bf63bd20057565c00c51d2996"
MAPPER_SEED = 0
RUN_PROTOCOL = "stage6rx4_cross_sequence_confirmation_runner_v1"
PANEL = "stage6rx4"

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
    / "stage6rx4_cross_sequence_confirmation"
)

CUSTOM_HARNESS = WORKSPACE / "benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
VANILLA_HARNESS = WORKSPACE / "benchmarks/online_gs/exp78b_replay_vanilla_mapping.py"
EVALUATOR = WORKSPACE / "benchmarks/online_gs/exp78_evaluate_vigs_ply.py"
ARCHIVE_VALIDATOR = WORKSPACE / "benchmarks/online_gs/validate_exp78b_frozen_tracker.py"
RENDER_VERIFIER = WORKSPACE / "benchmarks/online_gs/verify_exp78b_d1_render_match.py"
WORKLOAD_ANALYZER = PAPER_ROOT / "paper_full_stages/analyze_stage6_service_regime.py"
STRUCTURE_VERIFIER = PAPER_ROOT / "paper_full_stages/verify_stage6r_r4_full_structure.py"
COHORT_VERIFIER = (
    PAPER_ROOT
    / "paper_full_stages/verify_stage6r_r4_cross_sequence_confirmation.py"
)

# role, eval count, fixed-manifest SHA-256, archive-manifest SHA-256
SEQUENCES: dict[tuple[str, str], tuple[str, int, str, str]] = {
    ("rpng", "table_03"): ("confirmation", 1402, "4b4a53e1e7fd804838cf862a19e091f983c6463a8e5747fb65c22d47ea27e608", "307eef0076dab57b94f3c3c3100fe3e0a24998b7e0924160aeadb4e9fccc17ba"),
    ("rpng", "table_04"): ("confirmation", 1215, "47516fdce0a657211da7d5a80a9d576ce11c2e05307e2b1996475c4b5cd90ca5", "1f56dd70b341de879f57b7e613d22a68a0831124b0612952694743b1c8e34367"),
    ("rpng", "table_05"): ("confirmation", 1234, "7e8c31e06280b52a217a8daf8046021d2654aee51049a88dcd71e96058d0fd37", "3c85628754e646801aefad2d8a72ecd05ec10effae775d9a45b30dad0d17c110"),
    ("rpng", "table_07"): ("confirmation", 958, "091271497abbc6b56d36e4b0fcc6dd82e70d50ebe4ea46318bf8b4cde1c7d227", "bfa9c64c323ea6ec04e9ab6be403e44474f24e07756a9cb48f13a4251b1af468"),
    ("rpng", "table_08"): ("confirmation", 1698, "a9824cbcdbbedee592ae6eb107e8244753a15eb175c13480b814308b4e6b952f", "1a65a6e3baa9754ba965e26db7a282227dfeb1327650b9c0eac49aad8c5c2b52"),
    ("utmm", "ego-centric-1"): ("confirmation", 308, "398bf1bb30316a7f01908db42f860e488b9f62b70a875ebf5492cec2e1c2e62a", "77b8b9a843a8f3bbce9a41ceb2ac70d89074512fee206103362a12d96435ab99"),
    ("utmm", "ego-centric-2"): ("confirmation", 261, "07c485155b2bd90e6e45175c6c8d598ba734c331871850a5109ad83309788f7b", "9697429d3c543b5b5799764090c5bcd277fcbb4f551bd38a3162dbfd287b6663"),
    ("utmm", "fast-straight"): ("confirmation", 68, "4b4bd4d88d4224ed07817e95a5b84a2d82313b89d33f85421e1347f6eea0ea94", "1162b1659a925c357bc6f5a3620db5a8f3549e2625d0e49863763d43cc44bf17"),
    ("utmm", "slow-straight-1"): ("confirmation", 80, "a3dae3101602971e20cd18936c6b671dbe3c996749341a5f843dbd874cf0e924", "7843e9df6b154bbaa4534300c4166922c9fb9ba9802b1de0f0fdc9cc28b5334d"),
    ("utmm", "slow-straight-2"): ("confirmation", 121, "86ae7000517b7559016bda1b8ae9e94656795dbf342a419076b8f66eb6c102ba", "b213977e13cb047e5183536a577ff485ffb529848fd5cdf6b52ae77693d1e928"),
    ("utmm", "square-1"): ("confirmation", 324, "6a54fdd3ccf272b762c4c4ebca13803f09e28efe4f43cbddf940cbb80dba8e26", "db5de0b9d08ca77a08b45faeeeb406ae5c350fac1b2a6e901a9aa66a89a38dfb"),
}

SENTINELS = (("utmm", "fast-straight"), ("rpng", "table_07"))

EXPECTED_HASHES = {
    CUSTOM_HARNESS: "e0a2bcf50ae1354bb79efe79009f1e23567243942a6d358b95a8c5937c16bf16",
    VANILLA_HARNESS: "cabdb4df902bfb278b0b590af5dcf31b40921bd76a09d3225991a4f9b3741765",
    EVALUATOR: "f854084b249cea724b7be65a1655088ce8906203110f52c6503b052ec3b51c3c",
    ARCHIVE_VALIDATOR: "b2c2e050ddff373cd5e4062460fa021a141d206673a98d87fe531d3b917afccc",
    RENDER_VERIFIER: "6ced1153ccf985653617c74b1085af1a589d214f7035275744739cfe5f6130a3",
    WORKLOAD_ANALYZER: "2dcc65a6b6610408e3b80328ad15709fcb0c1721f0187425fa5e432c381f569d",
    STRUCTURE_VERIFIER: "dbd38b76d23c6fbcca45b677884df0a84b26541b1f8cd5005e96ed8499f0d088",
    COHORT_VERIFIER: "0daf822dbb0b746fbe756db72a537bcc93676862a09c1a9cbe881555a30d0678",
    WORKSPACE / "benchmarks/online_gs/config/vigs_final_v7_rpng.yaml": "138fdd26a99be125fab900ba9e731d38660ee7d2dd8e5f6833496a16045ccf54",
    WORKSPACE / "benchmarks/online_gs/config/vigs_final_v7_utmm.yaml": "b68693bf2d91291af1b5bd8cbd5489427445b7ff6048722f5736d14e1a6516c4",
    OFFICIAL_ROOT / "config/rpng.yaml": "cd1713e83927cf84a4d841b0661207fa6da0c4ba56bcbc3540830b9fcc5421c3",
    OFFICIAL_ROOT / "config/utmm.yaml": "9fe132f363244207f74d8952d9a1715e6e965b1968e8076433b9a606dc103af1",
}

R4_FLAGS = (
    "--time-scale", "unbounded",
    "--deadline-reserve-ms", "20",
    "--fixed-event-dense-opportunities-per-packet", "1",
    "--compute-paced-dense-admission",
    "--compute-paced-dense-token-cost", "1",
    "--c1-c2-global-residue-integration",
    "--service-shortfall-ercb",
    "--stage6r-keyframe-appearance-replay",
    "--stage6r-native-global-keyframe-selection-audit",
    "--stage6r-native-global-keyframe-ercb",
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
    return subprocess.check_output(
        ("git", "-C", str(root), *args), text=True
    ).strip()


def sequence_paths(dataset: str, sequence: str) -> dict[str, Path]:
    if (dataset, sequence) not in SEQUENCES:
        raise ValueError(f"unsupported X4 sequence: {dataset}/{sequence}")
    archive = ARCHIVE_ROOT / dataset / sequence / "seed0"
    fixed_manifest = MANIFEST_ROOT / f"{dataset}_{sequence}.json"
    custom_config = (
        WORKSPACE / f"benchmarks/online_gs/config/vigs_final_v7_{dataset}.yaml"
    )
    vanilla_config = OFFICIAL_ROOT / f"config/{dataset}.yaml"
    if dataset == "rpng":
        image_dir = (
            WORKSPACE / f"data/benchmarks/rpng/prepared/rpngar/{sequence}/rgb"
        )
        calibration = OFFICIAL_ROOT / "calib/rpngar.txt"
    else:
        base = WORKSPACE / f"data/benchmarks/utmm/prepared/UTMM_Dataset/{sequence}"
        image_dir = base / "rgb_timestamp"
        calibration = base / "intrinsics_ours.txt"
    return {
        "archive": archive,
        "fixed_manifest": fixed_manifest,
        "custom_config": custom_config,
        "vanilla_config": vanilla_config,
        "image_dir": image_dir,
        "calibration": calibration,
    }


def run_paths(root: Path, dataset: str, sequence: str) -> dict[str, Path]:
    base = root / dataset / sequence
    verification = base / "verification"
    return {
        "candidate": base / "stage6rx4_r4_full_s0",
        "vanilla": base / "stage6rx4_native_vanilla_render_matched_s0",
        "structure": verification / "stage6rx4_r4_structure_s0.json",
        "render": verification / "stage6rx4_render_match_s0.json",
        "render_repaired": verification / "stage6rx4_render_match_s0_v2.json",
    }


def workload_path(candidate: Path) -> Path:
    return candidate / "stage6_service_regime.json"


def active_render_report(paths: dict[str, Path]) -> Path:
    """Prefer an additive source-neutral repair while retaining the v1 report."""
    repaired = paths["render_repaired"]
    return repaired if repaired.is_file() else paths["render"]


def mapping_command(
    arm: str, dataset: str, sequence: str, root: Path
) -> list[str]:
    paths = sequence_paths(dataset, sequence)
    outputs = run_paths(root, dataset, sequence)
    python = str(PYTHON_ENV / "bin/python")
    common = [
        "--archive", str(paths["archive"]),
        "--output", str(outputs[arm]),
        "--seed", str(MAPPER_SEED),
    ]
    if arm == "candidate":
        return [
            python,
            str(CUSTOM_HARNESS),
            *common,
            "--config", str(paths["custom_config"]),
            *R4_FLAGS,
        ]
    if arm == "vanilla":
        reference = outputs["candidate"] / "mapping_replay_runtime.json"
        return [
            python,
            str(VANILLA_HARNESS),
            *common,
            "--config", str(paths["vanilla_config"]),
            "--time-scale", "unbounded",
            "--deadline-reserve-ms", "20",
            "--mapping-after-metric-init",
            "--reference-service-runtime", str(reference),
        ]
    raise ValueError(f"unsupported X4 arm: {arm}")


def evaluation_command(output: Path, dataset: str, sequence: str) -> list[str]:
    paths = sequence_paths(dataset, sequence)
    return [
        str(PYTHON_ENV / "bin/python"),
        str(EVALUATOR),
        "--run-dir", str(output),
        "--image-dir", str(paths["image_dir"]),
        "--calib", str(paths["calibration"]),
        "--manifest", str(paths["fixed_manifest"]),
        "--rgb-file-in-nanoseconds",
        "--undistort",
        "--mapped-uids-json", str(output / "mapped_uids.json"),
        "--result-subdir", "strict_fixed_manifest",
    ]


def mapping_environment(custom: bool) -> dict[str, str]:
    env = os.environ.copy()
    torch_lib = PYTHON_ENV / "lib/python3.11/site-packages/torch/lib"
    built = BUILT_THIRDPARTY_ROOT / "thirdparty"
    if custom:
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
            str(torch_lib), str(PYTHON_ENV / "lib"), env.get("LD_LIBRARY_PATH")
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


def require_predeclared_state() -> dict[str, Any]:
    required: list[Path] = [
        *EXPECTED_HASHES,
        PYTHON_ENV / "bin/python",
        Path(__file__).resolve(),
    ]
    for dataset, sequence in SEQUENCES:
        required.extend(sequence_paths(dataset, sequence).values())
    missing = sorted({str(path) for path in required if not path.exists()})
    if missing:
        raise FileNotFoundError("missing X4 input:\n" + "\n".join(missing))

    paper_commit = git_output(PAPER_ROOT, "rev-parse", "HEAD")
    official_commit = git_output(OFFICIAL_ROOT, "rev-parse", "HEAD")
    if paper_commit != PAPER_COMMIT:
        raise RuntimeError(
            f"paper source moved: expected {PAPER_COMMIT}, got {paper_commit}"
        )
    if official_commit != OFFICIAL_COMMIT:
        raise RuntimeError(
            f"official source moved: expected {OFFICIAL_COMMIT}, got {official_commit}"
        )
    for repository in (PAPER_ROOT, OFFICIAL_ROOT):
        subprocess.run(
            ("git", "-C", str(repository), "diff", "--quiet", "--ignore-submodules=dirty"),
            check=True,
        )
        subprocess.run(
            ("git", "-C", str(repository), "diff", "--cached", "--quiet", "--ignore-submodules=dirty"),
            check=True,
        )
    for critical in (Path(__file__).resolve(), CUSTOM_HARNESS):
        subprocess.run(
            ("git", "-C", str(WORKSPACE), "ls-files", "--error-unmatch", str(critical)),
            stdout=subprocess.DEVNULL,
            check=True,
        )
        subprocess.run(
            ("git", "-C", str(WORKSPACE), "diff", "--quiet", "--", str(critical)),
            check=True,
        )
        subprocess.run(
            ("git", "-C", str(WORKSPACE), "diff", "--cached", "--quiet", "--", str(critical)),
            check=True,
        )

    mismatches = {
        str(path): {"expected": expected, "actual": sha256(path)}
        for path, expected in EXPECTED_HASHES.items()
        if sha256(path) != expected
    }
    for (dataset, sequence), (_, _, fixed_hash, archive_hash) in SEQUENCES.items():
        paths = sequence_paths(dataset, sequence)
        for path, expected in (
            (paths["fixed_manifest"], fixed_hash),
            (paths["archive"] / "archive_manifest.json", archive_hash),
        ):
            actual = sha256(path)
            if actual != expected:
                mismatches[str(path)] = {"expected": expected, "actual": actual}
    if mismatches:
        raise RuntimeError(
            "predeclared X4 source/input hash mismatch:\n"
            + json.dumps(mismatches, indent=2, sort_keys=True)
        )

    subprocess.run(
        (
            str(PYTHON_ENV / "bin/python"),
            "-c",
            "import vigs_backends, lietorch, diff_gaussian_rasterization, simple_knn",
        ),
        cwd=WORKSPACE,
        env=mapping_environment(True),
        check=True,
    )
    return {
        "paper_commit": paper_commit,
        "official_commit": official_commit,
        "lab_commit": git_output(WORKSPACE, "rev-parse", "HEAD"),
        "sequences": len(SEQUENCES),
        "sentinels": [list(value) for value in SENTINELS],
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


def ensure_archive_validation(archive: Path, output: Path) -> None:
    cache = archive / "validation.json"
    archive_hash = sha256(archive / "archive_manifest.json")
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
                str(archive),
                "--output", str(cache),
            ],
            output / "archive_validation.log",
            mapping_environment(False),
        )
        report = read_json(cache)
        if report.get("valid") is not True:
            raise RuntimeError("frozen archive validation failed")
    else:
        (output / "archive_validation.log").write_text(
            f"reused {cache}\n", encoding="utf-8"
        )
    shutil.copy2(cache, output / "frozen_archive_validation.json")


def validate_mapping(
    output: Path, arm: str, dataset: str, sequence: str
) -> dict[str, Any]:
    _, _, _, archive_hash = SEQUENCES[(dataset, sequence)]
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
    if arm == "candidate":
        if runtime.get("custom_commit") != PAPER_COMMIT:
            raise RuntimeError("candidate paper source commit mismatch")
        if runtime.get("protocol") != "exp78b_gsslam_frozen_mapping_replay_v29":
            raise RuntimeError("candidate R4 runtime protocol mismatch")
        if runtime.get("comparison_contract") != "stage6r_r4_native_global_keyframe_ercb_v1":
            raise RuntimeError("candidate R4 comparison contract mismatch")
        if runtime.get("stage6r_native_global_keyframe_selection_audit") is not True:
            raise RuntimeError("candidate native-global audit missing")
        if runtime.get("stage6r_native_global_keyframe_ercb") is not True:
            raise RuntimeError("candidate native-global ERCB missing")
    return runtime


def validate_evaluation(output: Path, dataset: str, sequence: str) -> None:
    _, expected_count, _, _ = SEQUENCES[(dataset, sequence)]
    result = read_json(output / "psnr/strict_fixed_manifest/final_result.json")
    fixed = result.get("predeclared_fixed_manifest_posthoc") or {}
    if int(fixed.get("view_count", -1)) != expected_count:
        raise RuntimeError("fixed held-out evaluator view-count mismatch")
    if fixed.get("mapping_disjoint") is not True:
        raise RuntimeError("fixed evaluator is not mapping-disjoint")


def structure_command(run: Path, output: Path) -> list[str]:
    return [
        str(PYTHON_ENV / "bin/python"),
        str(STRUCTURE_VERIFIER),
        "--run", str(run),
        "--output", str(output),
    ]


def write_manifest(
    output: Path,
    arm: str,
    dataset: str,
    sequence: str,
    command: list[str],
    source: dict[str, Any],
    *,
    structure_report: Path | None = None,
    render_report: Path | None = None,
) -> None:
    paths = sequence_paths(dataset, sequence)
    custom = arm == "candidate"
    config = paths["custom_config"] if custom else paths["vanilla_config"]
    harness = CUSTOM_HARNESS if custom else VANILLA_HARNESS
    values = {
        "protocol": RUN_PROTOCOL,
        "panel": PANEL,
        "arm": "stage6r_r4_full" if custom else "native_vanilla_render_matched",
        "dataset": dataset,
        "sequence": sequence,
        "role": "confirmation",
        "seed": str(MAPPER_SEED),
        "tracker_archive_seed": "0",
        "mapping_source_commit": source["paper_commit"] if custom else source["official_commit"],
        "paper_source_commit": source["paper_commit"],
        "official_source_commit": source["official_commit"],
        "lab_source_commit": source["lab_commit"],
        "archive_manifest_sha256": sha256(paths["archive"] / "archive_manifest.json"),
        "config_sha256": sha256(config),
        "fixed_manifest_sha256": sha256(paths["fixed_manifest"]),
        "harness_sha256": sha256(harness),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "evaluator_sha256": sha256(EVALUATOR),
        "mapping_flags": shlex.join(command[2:]),
        "post_eos_optimizer_updates_required": "0",
        "final_ba": "off",
        "final_color_refinement": "off",
        "runtime_sha256": sha256(output / "mapping_replay_runtime.json"),
        "ply_sha256": sha256(output / "3dgs_before_final.ply"),
        "evaluation_sha256": sha256(
            output / "psnr/strict_fixed_manifest/final_result.json"
        ),
        "mapping_log_sha256": sha256(output / "mapping.log"),
        "evaluation_log_sha256": sha256(output / "evaluation.log"),
        "archive_validation_sha256": sha256(
            output / "frozen_archive_validation.json"
        ),
    }
    if custom:
        if structure_report is None:
            raise ValueError("candidate manifest requires structural report")
        values["workload_report_sha256"] = sha256(workload_path(output))
        values["structure_report_sha256"] = sha256(structure_report)
    else:
        if render_report is None:
            raise ValueError("vanilla manifest requires render-match report")
        values["render_report_sha256"] = sha256(render_report)
        values["render_verifier_sha256"] = sha256(RENDER_VERIFIER)
    manifest = output / "source_manifest.txt"
    if manifest.exists():
        raise FileExistsError(f"refusing to overwrite {manifest}")
    manifest.write_text(
        "".join(f"{key}={value}\n" for key, value in values.items()),
        encoding="utf-8",
    )


def run_arm(
    root: Path,
    arm: str,
    dataset: str,
    sequence: str,
    dry_run: bool,
) -> None:
    source = require_predeclared_state()
    outputs = run_paths(root, dataset, sequence)
    output = outputs[arm]
    command = mapping_command(arm, dataset, sequence, root)
    evaluation = evaluation_command(output, dataset, sequence)
    if dry_run:
        payload: dict[str, Any] = {
            "mapping": command,
            "evaluation": evaluation,
        }
        if arm == "candidate":
            payload["workload"] = [
                str(PYTHON_ENV / "bin/python"),
                str(WORKLOAD_ANALYZER),
                "--runtime", str(output / "mapping_replay_runtime.json"),
                "--archive", str(sequence_paths(dataset, sequence)["archive"]),
                "--output", str(workload_path(output)),
            ]
            payload["structural_prequality"] = structure_command(
                output, outputs["structure"]
            )
        print(json.dumps(payload, indent=2))
        return
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    if arm == "vanilla":
        candidate = outputs["candidate"]
        if not (candidate / "source_manifest.txt").is_file():
            raise FileNotFoundError("complete the X4 candidate before vanilla")
        structure_report = read_json(outputs["structure"])
        if structure_report.get("valid") is not True:
            raise RuntimeError("candidate structural verifier did not pass")

    paths = sequence_paths(dataset, sequence)
    output.mkdir(parents=True)
    ensure_archive_validation(paths["archive"], output)
    run_logged(command, output / "mapping.log", mapping_environment(arm == "candidate"))
    validate_mapping(output, arm, dataset, sequence)

    if arm == "candidate":
        run_logged(
            [
                str(PYTHON_ENV / "bin/python"),
                str(WORKLOAD_ANALYZER),
                "--runtime", str(output / "mapping_replay_runtime.json"),
                "--archive", str(paths["archive"]),
                "--output", str(workload_path(output)),
            ],
            output / "workload_analysis.log",
            mapping_environment(True),
        )
        run_logged(
            structure_command(output, outputs["structure"]),
            output / "structural_prequality.log",
            mapping_environment(True),
        )
        if read_json(outputs["structure"]).get("valid") is not True:
            raise RuntimeError("R4 structural pre-quality verifier failed")

    # Candidate quality is opened only after its quality-blind structure passes.
    run_logged(evaluation, output / "evaluation.log", mapping_environment(False))
    validate_evaluation(output, dataset, sequence)
    if arm == "candidate":
        write_manifest(
            output,
            arm,
            dataset,
            sequence,
            command,
            source,
            structure_report=outputs["structure"],
        )


def _failed_checks(report: dict[str, Any]) -> set[str]:
    checks = report.get("checks")
    if not isinstance(checks, dict):
        return {"__malformed_checks__"}
    return {
        str(name)
        for name, value in checks.items()
        if not isinstance(value, dict) or value.get("passed") is not True
    }


def _eligible_for_source_neutral_reverification(report: dict[str, Any]) -> bool:
    failures = _failed_checks(report)
    return (
        report.get("valid") is True and not failures
    ) or (
        report.get("valid") is False
        and failures == {"same_tracking_kf_uids"}
    )


def _repair_vanilla_manifest(
    manifest: Path, original_report: Path, repaired_report: Path
) -> None:
    """Preserve the original manifest, then point its live copy at v2 evidence."""
    preserved = manifest.with_name("source_manifest_pre_render_verifier_v2.txt")
    if preserved.exists():
        raise FileExistsError(f"refusing to overwrite {preserved}")
    original_text = manifest.read_text(encoding="utf-8")
    original_manifest_hash = sha256(manifest)
    original_report_hash = sha256(original_report)
    lines = original_text.splitlines()
    indices = [
        index
        for index, line in enumerate(lines)
        if line.startswith("render_report_sha256=")
    ]
    if len(indices) != 1:
        raise RuntimeError("expected exactly one render_report_sha256 field")
    lines[indices[0]] = f"render_report_sha256={sha256(repaired_report)}"
    lines.extend(
        (
            "render_verifier_revalidation_protocol=tracking_identity_provenance_v2",
            f"render_verifier_sha256={sha256(RENDER_VERIFIER)}",
            f"pre_repair_report_sha256={original_report_hash}",
            f"pre_repair_source_manifest_sha256={original_manifest_hash}",
        )
    )
    shutil.copy2(manifest, preserved)
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_pair(
    root: Path,
    dataset: str,
    sequence: str,
    *,
    reverify_source_neutral: bool = False,
) -> bool:
    source = require_predeclared_state()
    paths = run_paths(root, dataset, sequence)
    validate_mapping(paths["candidate"], "candidate", dataset, sequence)
    validate_mapping(paths["vanilla"], "vanilla", dataset, sequence)
    validate_evaluation(paths["candidate"], dataset, sequence)
    validate_evaluation(paths["vanilla"], dataset, sequence)
    structure = read_json(paths["structure"])
    if structure.get("valid") is not True:
        raise RuntimeError("candidate structural verifier is invalid")
    original_report: dict[str, Any] | None = None
    render_output = paths["render"]
    if reverify_source_neutral:
        if not paths["render"].is_file():
            raise FileNotFoundError(
                "source-neutral reverification requires a v1 report"
            )
        original_report = read_json(paths["render"])
        if not _eligible_for_source_neutral_reverification(original_report):
            raise RuntimeError(
                "reverification accepts only a valid legacy report or the "
                "known tracking-identity-only failure"
            )
        render_output = paths["render_repaired"]
    if render_output.exists():
        raise FileExistsError(f"refusing to overwrite {render_output}")
    render_output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            str(PYTHON_ENV / "bin/python"),
            str(RENDER_VERIFIER),
            "--d1-run", str(paths["candidate"]),
            "--vanilla-run", str(paths["vanilla"]),
            "--output", str(render_output),
        ],
        cwd=WORKSPACE,
        check=False,
    )
    report = read_json(render_output)
    valid = completed.returncode == 0 and report.get("valid") is True
    if reverify_source_neutral:
        assert original_report is not None
        if not valid:
            return False
        if report.get("result") != original_report.get("result"):
            raise RuntimeError("source-neutral reverification changed quality results")
        _repair_vanilla_manifest(
            paths["vanilla"] / "source_manifest.txt",
            paths["render"],
            render_output,
        )
    else:
        write_manifest(
            paths["vanilla"],
            "vanilla",
            dataset,
            sequence,
            mapping_command("vanilla", dataset, sequence, root),
            source,
            render_report=render_output,
        )
    return valid


def cohort_entries(root: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for dataset, sequence in sorted(SEQUENCES):
        paths = run_paths(root, dataset, sequence)
        entries.append(
            {
                "dataset": dataset,
                "sequence": sequence,
                "candidate_run": str(paths["candidate"]),
                "vanilla_run": str(paths["vanilla"]),
                "render_report": str(active_render_report(paths)),
                "structure_report": str(paths["structure"]),
                "workload_report": str(workload_path(paths["candidate"])),
            }
        )
    return entries


def verify_cohort(root: Path) -> bool:
    require_predeclared_state()
    verification = root / "verification"
    entries_path = verification / "stage6rx4_confirmation_entries.json"
    report_path = verification / "stage6rx4_confirmation_cohort.json"
    for path in (entries_path, report_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite {path}")
    verification.mkdir(parents=True, exist_ok=True)
    entries_path.write_text(
        json.dumps(cohort_entries(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            str(PYTHON_ENV / "bin/python"),
            str(COHORT_VERIFIER),
            "--entries", str(entries_path),
            "--output", str(report_path),
        ],
        cwd=WORKSPACE,
        check=False,
    )
    report = read_json(report_path)
    return (
        completed.returncode == 0
        and report.get("valid") is True
        and report.get("promotion_gate_passed") is True
    )


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
    pair.add_argument("--reverify-source-neutral", action="store_true")
    subparsers.add_parser("verify-cohort")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if args.action == "preflight":
        print(json.dumps(require_predeclared_state(), indent=2, sort_keys=True))
        return 0
    if args.action == "run":
        if (args.dataset, args.sequence) not in SEQUENCES:
            raise ValueError("sequence is not in the frozen X4 cohort")
        run_arm(
            root,
            args.arm,
            args.dataset,
            args.sequence,
            args.dry_run,
        )
        return 0
    if args.action == "verify-pair":
        if (args.dataset, args.sequence) not in SEQUENCES:
            raise ValueError("sequence is not in the frozen X4 cohort")
        return 0 if verify_pair(
            root,
            args.dataset,
            args.sequence,
            reverify_source_neutral=args.reverify_source_neutral,
        ) else 1
    if args.action == "verify-cohort":
        return 0 if verify_cohort(root) else 1
    raise AssertionError(args.action)


if __name__ == "__main__":
    raise SystemExit(main())
