#!/usr/bin/env python3
"""Capture first-frame render tensors on three post-mapper RPNG evaluations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import run_exp88_normalized_metric_v2 as v2


base = v2.base
ROOT = base.WORKSPACE / "results/experiments/exp92_evaluator_branch_capture"
OUT = ROOT / "rpng/table_01/normalized_s0"
WRAPPER = base.WORKSPACE / "benchmarks/online_gs/diagnose_exp92_evaluator_tensor_probe.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_probe(number: int) -> dict:
    v2.gpu_idle()
    command = base.evaluation_command(OUT, "rpng", "table_01")
    command[command.index("--result-subdir") + 1] = f"strict_fixed_manifest_probe{number}"
    probe_path = OUT / f"tensor_probe{number}.json"
    cmd = [command[0], str(WRAPPER), "--probe-output", str(probe_path), *command[2:]]
    with (OUT / f"evaluation_probe{number}.log").open("wb") as sink:
        subprocess.run(
            cmd, cwd=base.WORKSPACE, env=base.mapping_environment(True),
            stdout=sink, stderr=subprocess.STDOUT, check=True,
        )
    result_path = OUT / "psnr" / f"strict_fixed_manifest_probe{number}" / "final_result.json"
    result = v2.read_json(result_path)
    probe = v2.read_json(probe_path)
    return {
        "pass_index": number,
        "fixed_psnr": result["predeclared_fixed_manifest_posthoc"]["mean_psnr"],
        "first_view_psnr": result["per_view"][0]["psnr"],
        "probe_first_view_psnr": probe["first_frame_psnr"],
        "probe": probe,
    }


def main() -> None:
    v2.install_inventory()
    paths = base.sequence_paths("rpng", "table_01")
    if sha(paths["fixed_manifest"]) != base.SEQUENCES[("rpng", "table_01")][2]:
        raise RuntimeError("fixed manifest changed")
    if OUT.exists():
        raise FileExistsError(OUT)
    v2.gpu_idle()
    command = base.mapping_command("candidate", "rpng", "table_01", ROOT)
    command[command.index("--output") + 1] = str(OUT)
    command.extend(("--ercb-selection-potential", "normalized_variance"))
    v2.write_json(OUT / "mapping_command.json", command)
    v2.run_to_file(command, OUT / "mapping.log", custom=True)
    ply = OUT / "3dgs_before_final.ply"
    before = sha(ply)
    runs = []
    for number in (1, 2, 3):
        runs.append(run_probe(number))
        if sha(ply) != before:
            raise RuntimeError("PLY changed during evaluator branch capture")
        print(
            f"probe{number}: fixed {runs[-1]['fixed_psnr']:.6f}, "
            f"first view {runs[-1]['first_view_psnr']:.6f}", flush=True,
        )
    report = {
        "ply_sha256": before,
        "archive_manifest_sha256": sha(paths["archive"] / "archive_manifest.json"),
        "fixed_manifest_sha256": sha(paths["fixed_manifest"]),
        "mapper_harness_sha256": sha(base.CUSTOM_HARNESS),
        "evaluator_sha256": sha(base.EVALUATOR),
        "tensor_probe_wrapper_sha256": sha(WRAPPER),
        "evaluations": runs,
    }
    v2.write_json(OUT / "capture_report.json", report)


if __name__ == "__main__":
    main()
