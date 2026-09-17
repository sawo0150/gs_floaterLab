#!/usr/bin/env python3
"""Test whether an explicit post-mapper delay removes RPNG first-eval collapse."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import time

import run_exp78b_stage6rx4_cross_sequence as base
import run_exp78b_r4_all_scenes as all_scenes


OUT = (
    base.WORKSPACE / "results/experiments/exp90_first_eval_delay_probe"
    / "rpng/table_01/control_pipe_delay15_s0"
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gpu_idle() -> None:
    active = subprocess.check_output(
        ("nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"),
        text=True,
    ).strip()
    if active:
        raise RuntimeError(f"GPU busy; wait without terminating: {active}")


def eval_command(subdir: str) -> list[str]:
    command = base.evaluation_command(OUT, "rpng", "table_01")
    command[command.index("--result-subdir") + 1] = subdir
    return command


def main() -> None:
    all_scenes.install_extension()
    if OUT.exists():
        raise FileExistsError(OUT)
    gpu_idle()
    command = base.mapping_command("candidate", "rpng", "table_01", OUT.parent.parent.parent)
    command[command.index("--output") + 1] = str(OUT)
    OUT.mkdir(parents=True)
    (OUT / "mapping_command.json").write_text(json.dumps(command, indent=2) + "\n")
    base.run_logged(command, OUT / "mapping.log", base.mapping_environment(True))
    ply = OUT / "3dgs_before_final.ply"
    before = sha(ply)
    gpu_idle()
    time.sleep(15)
    gpu_idle()
    base.run_logged(
        eval_command("strict_fixed_manifest_first_after_delay"),
        OUT / "evaluation_first.log", base.mapping_environment(True),
    )
    after_first = sha(ply)
    gpu_idle()
    with (OUT / "evaluation_second.log").open("wb") as sink:
        subprocess.run(
            eval_command("strict_fixed_manifest_second"),
            cwd=base.WORKSPACE, env=base.mapping_environment(True),
            stdout=sink, stderr=subprocess.STDOUT, check=True,
        )
    after_second = sha(ply)
    if before != after_first or before != after_second:
        raise RuntimeError("PLY changed during evaluation")
    scores = []
    for subdir in ("strict_fixed_manifest_first_after_delay", "strict_fixed_manifest_second"):
        path = OUT / "psnr" / subdir / "final_result.json"
        result = json.loads(path.read_text())
        scores.append(result["predeclared_fixed_manifest_posthoc"]["mean_psnr"])
    report = {"first_psnr": scores[0], "second_psnr": scores[1],
              "delta_db": scores[1] - scores[0], "ply_sha256": before,
              "post_map_delay_seconds": 15}
    (OUT / "delay_probe_result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
