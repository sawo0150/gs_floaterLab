"""Resume the handoff's fixed-work panels without rerunning passed controls.

Run under the explicit machine profile. Transfer processes are observed, never
killed. Input readiness and result gates are checked independently of exit codes.
Failed runs stop this queue and require a fresh output namespace for retry.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_cvpr_measurements as fixed
from collect_cvpr_assets import ROOT, MAIN, OUT, read, write, sha

PILOTS = {"aria1253", "table_06", "square-1"}


def geometry_files(reference):
    # The frozen reader accepts bundled v2 tensors and split depth/normal v3.
    return [reference] if isinstance(reference, str) else [reference['depth'], reference['normal']]


def pending_input_files(row, cache):
    """Readiness only; the full input hash audit still runs before training."""
    key = (row['dataset'], row['scene'])
    archive = Path(row['archive'])
    manifest = archive / 'archive_manifest.json'
    if not manifest.is_file(): return [str(manifest)]
    if key not in cache:
        assert sha(manifest) == row['archive_sha256'], manifest
        m = read(manifest)
        arrivals = archive / m['arrivals']
        if not arrivals.is_file(): return [str(arrivals)]
        paths = {Path(row[k]) for k in ('fixed_manifest', 'calibration', 'imu', 'input_config')}
        paths.add(arrivals)
        for k in ('final_tracker_state', 'evaluation_only_post_eos_trajectory'):
            if m.get(k): paths.add(archive / m[k])
        for event in m['events']:
            paths.add(archive / event['payload'])
            for g in event.get('geometry_refs', []):
                paths.update(archive / f for f in geometry_files(g))
        for line in arrivals.read_text().splitlines():
            if line: paths.add(Path(row['image_dir']) / json.loads(line)['source_name'])
        cache[key] = paths
    cache[key] = {p for p in cache[key] if not p.is_file()}
    return cache[key]


def alive(pid):
    stat = Path(f"/proc/{pid}/stat")
    return stat.exists() and stat.read_text().rsplit(")", 1)[1].split()[0] != "Z"


def wait_for(pids, status, stage):
    while any(alive(pid) for pid in pids):
        write(status, {"stage": stage, "waiting_pids": [p for p in pids if alive(p)], "updated": time.time()})
        time.sleep(10)


def inputs_ready(rows):
    for r in rows:
        archive = Path(r["archive"])
        assert sha(archive / "archive_manifest.json") == r["archive_sha256"], r["scene"]
        assert sha(Path(r["fixed_manifest"])) == r["fixed_manifest_sha256"], r["scene"]
        m = read(archive / "archive_manifest.json")
        files = {m["arrivals"]}
        for k in ("final_tracker_state", "evaluation_only_post_eos_trajectory"):
            if m.get(k): files.add(m[k])
        for e in m["events"]:
            files.add(e["payload"])
            assert sha(archive / e["payload"]) == e["payload_sha256"], e["payload"]
            for g in e.get("geometry_refs", []):
                files.update(geometry_files(g))
        missing = [name for name in files if not (archive / name).is_file()]
        assert not missing, (r["scene"], missing[:5])
        for k in ("calibration", "imu", "input_config"):
            assert Path(r[k]).is_file(), r[k]
        arrivals = [json.loads(line) for line in (archive / m["arrivals"]).read_text().splitlines() if line]
        assert all((Path(r["image_dir"]) / a["source_name"]).is_file() for a in arrivals), r["image_dir"]


def passed(directory, expected):
    rows = read(directory / "summary.json")
    assert len(rows) == expected and all(r["status"] == "passed" for r in rows), directory
    return rows


def run(command, log, status, stage):
    while subprocess.check_output(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"], text=True).strip():
        write(status, {"stage": "waiting_gpu", "next": stage, "updated": time.time()})
        time.sleep(10)
    write(status, {"stage": stage, "command": command, "log": str(log), "updated": time.time()})
    env = fixed.environment("vanilla")
    env["PYTHONPATH"] = str(MAIN / "scripts/selected_mapping") + os.pathsep + env["PYTHONPATH"]
    with log.open("x") as f:
        subprocess.run(command, env=env, stdout=f, stderr=subprocess.STDOUT, check=True)


def evaluate_curves(rows, logs, status, label):
    for i, r in enumerate(rows):
        directory = Path(r["output"])
        expected = len(read(directory / "snapshots/manifest.json")["snapshots"]) + 1
        result = directory / "curve_evaluation/summary.json"
        if result.exists():
            curves = read(result)
            if len(curves) == expected and all(c["status"] == "evaluated" for c in curves):
                continue
            raise RuntimeError(f"Partial/failed curve evaluation requires inspection: {result}")
        run([sys.executable, str(HERE / "evaluate_cvpr_checkpoints.py"), "--run", r["output"],
             "--dataset", r["dataset"], "--scene", r["scene"]],
            logs / f"{label}_{i:03d}.log", status, label)
        curves = read(result)
        assert len(curves) == expected and all(c["status"] == "evaluated" for c in curves), r["output"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pilot", type=Path, required=True)
    p.add_argument("--controls", type=Path, required=True)
    p.add_argument("--reference", type=Path, required=True)
    p.add_argument("--initial-panel-pid", type=int, required=True)
    p.add_argument("--pilot-transfer-pid", type=int, required=True)
    p.add_argument("--remaining-transfer-pid", type=int, required=True)
    p.add_argument("--reuse-controls-manifest", type=Path,
                   help="Inspected passed pilot controls to preserve in a fresh namespace")
    p.add_argument("--reuse-source-lock", type=Path)
    a = p.parse_args()
    assert os.environ.get("ROGO_MACHINE_PROFILE"), "An explicit machine profile is required"
    a.controls.mkdir(parents=True, exist_ok=False)
    status = a.controls / "queue_status.json"
    try:
        if a.reuse_controls_manifest:
            reused = read(a.reuse_controls_manifest)
            assert len(reused) == 21 and all(r['status'] == 'passed' for r in reused)
            assert a.reuse_source_lock and a.reuse_source_lock.is_file()
            for row in reused:
                original = Path(row['output'])
                assert read(original / 'render_result.json')['valid_execution']
                assert read(original / 'evaluation_consistency.json')['pass']
                target = a.controls / f"render{row['budget']}" / row['dataset'] / row['scene'] / row['arm']
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(original.resolve(), target_is_directory=True)
                row['output'] = str(target)
            write(a.controls / 'summary.json', reused)
            shutil.copyfile(a.reuse_source_lock, a.controls / 'source_lock.json')
            write(a.controls / 'reused_controls_provenance.json', {
                'manifest': str(a.reuse_controls_manifest), 'sha256': sha(a.reuse_controls_manifest),
                'training_rerun': False})
        profile = Path(os.environ["ROGO_MACHINE_PROFILE"])
        write(a.controls / "machine_provenance.json", {
            "profile": read(profile), "profile_sha256": sha(profile),
            "adapter_sha256": sha(HERE / "rtx5070ti_profile/sitecustomize.py"),
            "queue_sha256": sha(Path(__file__)), "lab_head": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
            "custom_head": subprocess.check_output(["git", "-C", str(MAIN), "rev-parse", "HEAD"], text=True).strip(),
            "gpu": subprocess.check_output(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"], text=True).strip(),
            "time_comparison": False,
            "scene_execution_order": "input availability only; no metric-based selection",
            "training_policy_changed": False})
        inventory = read(OUT / "scene_inventory.json")
        pilots = [r for r in inventory if r["scene"] in PILOTS]
        completed = ROOT / "context/experiments/campaigns/06_gain_attribution/handoff_5070ti/completed_controls.json"
        wait_for([a.initial_panel_pid], status, "waiting_initial_pilot")
        initial_rows = read(a.pilot / "summary.json")
        # A fresh queue may resume after the complete migration pilot, too.
        assert len(initial_rows) in (4, 12), "Incomplete pilot requires inspection"
        evaluate_curves(passed(a.pilot, len(initial_rows)), a.controls, status, "initial_pilot_curves")
        wait_for([a.pilot_transfer_pid], status, "waiting_pilot_transfer")
        inputs_ready(pilots)
        for r in pilots:
            rel = Path("inputs") / r["dataset"] / r["scene"] / "setup"
            dst = a.pilot / rel
            if not dst.exists(): shutil.copytree(fixed.RESULTS / "cvpr_assets/fixed_work_v1" / rel, dst)
        py = sys.executable
        run([py, str(HERE / "run_cvpr_measurements.py"), "--output", str(a.pilot), "--scenes", *sorted(PILOTS),
             "--budgets", "15", "40", "--arms", "d3", "vanilla", "--snapshots"],
            a.controls / "pilot_remaining.log", status, "three_scene_pilot")
        evaluate_curves(passed(a.pilot, 12), a.controls, status, "pilot_curves")
        references = []
        for r in inventory:
            d, s = r["dataset"], r["scene"]
            origin = a.pilot if s in PILOTS else fixed.RESULTS / ("cvpr_assets/fixed_work_12f_v1" if s == "aria301_12F" else "cvpr_assets/fixed_work_v1")
            for prefix in ("inputs", "render15", "render40"):
                rel = Path(prefix) / d / s
                dest = a.reference / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.symlink_to((origin / rel).resolve(), target_is_directory=True)
            references.append({"dataset": d, "scene": s, "reference": str(origin), "same_gpu": s in PILOTS})
        write(a.reference / "provenance.json", {"references": references, "cross_gpu_time_comparison": False})
        control = [py, str(HERE / "run_cvpr_ablations.py"), "--output", str(a.controls), "--reference-root", str(a.reference),
                   "--skip-completed", str(completed), "--budgets", "15", "40", "--snapshots"]
        run([*control, "--scenes", *sorted(PILOTS)], a.controls / "pilot_controls.log", status, "pilot_controls")
        passed(a.controls, 21)
        historical = read(completed)
        skipped = lambda r: sum(x['status'] == 'passed' and (x['dataset'], x['scene']) == (r['dataset'], r['scene']) for x in historical)
        pending = [r for r in inventory if r['scene'] not in PILOTS and skipped(r) < 7]
        cache = {}
        while pending:
            ready = [r for r in pending if not pending_input_files(r, cache)]
            if not ready:
                # Use otherwise idle GPU time for already trained maps.
                evaluate_curves(read(a.controls / 'summary.json'), a.controls, status, 'control_curves')
                if not alive(a.remaining_transfer_pid):
                    inputs_ready(pending)  # Raise with the missing/corrupt input, never retry training.
                write(status, {'stage': 'waiting_scene_inputs', 'transfer_pid': a.remaining_transfer_pid,
                               'pending_scenes': [r['scene'] for r in pending], 'updated': time.time()})
                time.sleep(10)
                continue
            for r in ready:
                inputs_ready([r])
                count = len(read(a.controls / 'summary.json'))
                log = a.controls / f"controls_{r['dataset']}_{r['scene']}.log"
                run([*control, '--scenes', r['scene']], log, status, 'remaining_controls')
                passed(a.controls, count + 7 - skipped(r))
                pending.remove(r)
        # This only skips passed outputs and restores the full-cohort protocol metadata.
        run(control, a.controls / 'finalize_controls.log', status, 'finalize_control_metadata')
        rows = passed(a.controls, 121)
        evaluate_curves(rows, a.controls, status, "control_curves")
        wait_for([a.remaining_transfer_pid], status, 'waiting_final_input_transfer')
        inputs_ready(inventory)
        write(status, {"stage": "fixed_work_controls_and_curves_complete", "controls_passed": 121,
                       "previous_controls_passed": 19, "geometry_and_original_sampler": "pending_followup", "updated": time.time()})
    except BaseException:
        write(status, {"stage": "failed", "traceback": traceback.format_exc(), "updated": time.time()})
        raise


if __name__ == "__main__": main()
