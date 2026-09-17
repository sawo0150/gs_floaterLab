#!/usr/bin/env python3
"""3-scene pilot: work-credit admission (exp86-style cycle, r=4) x {kf, dense RR, dense ERCB}.

Ported into this Python harness via train.py's --work_credit_brackets_file
(bracket = one causal keyframe-interval group, from
build_work_credit_brackets.py) + --work_credit_r. Bracket 0 is a free
bootstrap; each further bracket is admitted only once every member of the
currently active pool has been drawn >= r times -- pool growth is paced by
selector service, not by a precomputed per-event iteration budget. The "kf"
arm additionally passes --eligible_names_file (the existing keyframe-only
name set from build_keyframe_only_schedules.py) to filter each bracket down
to its keyframe member(s) only; "dense_rr"/"dense_ercb" use the bracket's
full (keyframe+dense) membership. All three arms share the same
total_iterations per scene (the scene's stride20 event60 total, chosen to
give work-credit admission enough runway) and r=4 (exp86-A's adopted value).

Isolated manifest (evidence/manifest_workcredit_pilot.json); never touches
manifest.json or manifest_kfrr.json.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REPO = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom-exp77-budget-5070ti-repro")
PYTHON = "/home/wosas/miniconda3/envs/3dgs/bin/python"
DATA_ROOT = ROOT / "data/benchmarks/ercb_benchmark_B_stride20"
RESULT_ROOT = ROOT / "results/ERCB_ablation/benchmark-B_5070ti_stride20"
SEED = 0
WORK_CREDIT_R = 4
PILOT_SCENES = (("utmm", "square-1"), ("rpng", "table_01"), ("aria", "aria1253"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    main_manifest = json.loads((HERE / "evidence/manifest.json").read_text())
    total_by_scene = {
        (j["family"], j["scene"]): j["total_iterations"]
        for j in main_manifest["jobs"]
        if j["stride"] == 20 and j["budget"] == 60 and j["arm"] == "rr"
    }
    jobs = []
    for family, scene in PILOT_SCENES:
        total = total_by_scene[(family, scene)]
        checkpoints = sorted({max(1, total // 4), max(1, total // 2), total})
        bracket_file = HERE / "evidence/work_credit_brackets" / family / f"{scene}_stride20.json"
        eligible_file = HERE / "evidence/schedules_kfrr" / family / f"{scene}_stride20_event15.json"
        dataset = DATA_ROOT / family / scene / "stride20"
        for arm, scheduler, eligible in (
            ("kf", "causal_rr", eligible_file),
            ("dense_rr", "causal_rr", None),
            ("dense_ercb", "relative_floor_interval_softmax_rr", None),
        ):
            output = RESULT_ROOT / family / scene / "stride20" / "workcredit_r4" / f"{arm}_s{SEED}"
            run_training_arm = "ercb" if scheduler == "relative_floor_interval_softmax_rr" else "rr"
            argv = [
                PYTHON, str(ROOT / "context/experiments/exp77/run_training.py"),
                "--repo", str(REPO), "--arm", run_training_arm, "--",
                "-s", str(dataset), "-m", str(output), "-r", "4", "--eval",
                "--iterations", str(total), "--test_iterations",
                *[str(value) for value in checkpoints],
                "--save_iterations", str(total),
                "--view_scheduler", scheduler,
                "--work_credit_brackets_file", str(bracket_file),
                "--work_credit_r", str(WORK_CREDIT_R),
                "--scheduler_seed", str(SEED),
                "--scheduler_beta", str(math.log(3.0)),
                "--scheduler_block_size", "8",
                "--position_lr_max_steps", str(total),
                "--densify_until_iter", "0",
                "--depth_l1_weight_init", "0", "--depth_l1_weight_final", "0",
                "--data_device", "cpu", "--fixed_topology_step_before_report",
                "--quiet", "--disable_viewer",
            ]
            if eligible is not None:
                argv += ["--eligible_names_file", str(eligible)]
            jobs.append({
                "family": family, "scene": scene, "arm": arm, "seed": SEED,
                "total_iterations": total, "work_credit_r": WORK_CREDIT_R,
                "bracket_file": str(bracket_file),
                "eligible_names_file": str(eligible) if eligible else None,
                "dataset": str(dataset), "output": str(output),
                "argv": argv, "state": "pending",
            })
    manifest = {
        "protocol": "benchmark-B_workcredit_pilot_kf_vs_dense_rr_vs_dense_ercb",
        "state": "PREPARED_NOT_RUN", "device": "NVIDIA GeForce RTX 5070 Ti",
        "note": "3-scene pilot before a full run; isolated from manifest.json/manifest_kfrr.json",
        "repo_head": subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True
        ).strip(),
        "implementation_sha256": {
            "train.py": sha256(REPO / "train.py"),
            "runtime/scheduler.py": sha256(REPO / "runtime/scheduler.py"),
            "exp77/run_training.py": sha256(ROOT / "context/experiments/exp77/run_training.py"),
        },
        "contract": {
            "admission": "exp86-style cycle work-credit (bootstrap 1 bracket, then "
                          "next bracket admitted once active pool min draws >= r)",
            "work_credit_r": WORK_CREDIT_R,
            "bracket_definition": "one VIGS keyframe interval (same grouping as the "
                                   "fixed-budget schedules' event boundaries)",
            "arms": ["kf (bracket filtered to keyframe member only)",
                     "dense_rr (full bracket, causal_rr)",
                     "dense_ercb (full bracket, relative_floor_interval_softmax_rr)"],
            "total_iterations": "per-scene stride20 event60 total (shared across all 3 arms)",
            "resolution": 4, "loss": "RGB-only", "fixed_topology": True,
            "heldout": "llffhold-8", "seed": SEED,
        },
        "jobs": jobs,
    }
    destination = HERE / "evidence/manifest_workcredit_pilot.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{destination}: {len(jobs)} jobs across {len(PILOT_SCENES)} scenes")


if __name__ == "__main__":
    main()
