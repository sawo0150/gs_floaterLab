#!/usr/bin/env python3
"""Prepare the missing candidate with the unchanged official causal tracker."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import run_online_dense_training as trial
from collect_cvpr_assets import ROOT, RESULTS, MAIN, sha, write, read


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    scene = "aria301_12F"
    raw = Path("/home/intern/p28_5090_20260813/VIGS-SLAM-custom/data") / scene
    out = RESULTS / "cvpr_assets/inputs" / scene
    manifest = out / "heldout.json"
    archive = out / "archive"
    assert manifest.is_file() and (raw / "imu.txt").is_file()
    names = sorted([q.name for q in (raw / "rgb").iterdir() if q.is_file()], key=lambda n: float(Path(n).stem))
    cohort = read(manifest)
    assert cohort["frame_count"] == len(names) and {v["uid"] for v in cohort["views"]}.issubset(names)
    config = ROOT / "benchmarks/online_gs/config/vigs_official_aria_adapter.yaml"
    calib = trial.BASE.PAPER_ROOT / f"calib/{scene}.txt"
    capture = ROOT / "benchmarks/online_gs/exp78b_capture_frozen_tracker.py"
    cmd = [str(trial.BASE.PYTHON_ENV / "bin/python"), str(capture), "--dataset", "aria", "--sequence", scene,
           "--imagedir", str(raw / "rgb"), "--imufile", str(raw / "imu.txt"), "--calib", str(calib),
           "--config", str(config), "--weights", str(trial.BASE.OFFICIAL_ROOT / "pretrained_models/droid.pth"),
           "--output", str(archive), "--heldout-manifest", str(manifest), "--seed", "0", "--length", str(len(names)),
           "--buffer", "700", "--IMU_poseinit_after", "20"]
    write(out / "capture_command.json", {"cmd": cmd, "source_sha256": {str(q): sha(q) for q in [config, calib, capture, manifest]}, "raw_frames": len(names), "heldout_views": cohort["eval_count"], "mapping_optimization": False})
    if not a.execute:
        print("PREPARED", out, "GPU capture not started")
        return
    sys.path.insert(0, str(MAIN / "scripts/selected_mapping"))
    from selected_mapping_check import gpu_idle
    gpu_idle()
    if archive.exists():
        raise FileExistsError("Existing capture is preserved: " + str(archive))
    env = trial.BASE.mapping_environment(False)
    env["PYTHONPATH"] = str(trial.BASE.OFFICIAL_ROOT) + ":" + str(ROOT / "benchmarks/online_gs") + ":" + str(trial.BASE.BUILT_THIRDPARTY_ROOT) + ":" + env["PYTHONPATH"]
    with (out / "capture.log").open("x") as log:
        subprocess.run(cmd, env=env, cwd=ROOT / "results/experiments/exp78/a_paper_reproduction/trt_profiles/official_readme_dynamic_rtx5090", stdout=log, stderr=subprocess.STDOUT, check=True)
    with (out / "validation.log").open("x") as log:
        subprocess.run([str(trial.BASE.PYTHON_ENV / "bin/python"), str(trial.BASE.ARCHIVE_VALIDATOR), str(archive), "--output", str(out / "archive_validation.json")], env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    subprocess.run([sys.executable, str(HERE / "collect_cvpr_assets.py")], check=True)
    print("CAPTURE_VALIDATED", archive)


if __name__ == "__main__":
    main()
