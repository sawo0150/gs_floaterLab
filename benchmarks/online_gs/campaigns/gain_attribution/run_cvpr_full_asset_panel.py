#!/usr/bin/env python3
"""Continue actual CVPR measurements serially after the verified pilot pipeline.

No production edits, scene-specific tuning, invented results or agent work.
Each stage waits for an idle GPU and checks artifacts, not just exit codes.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import run_cvpr_measurements as fixed
from collect_cvpr_assets import ROOT, RESULTS, OUT, read, write, sha
from run_cvpr_asset_pipeline import process_identity


def wait_gpu():
    from selected_mapping_check import gpu_idle
    while True:
        try:
            gpu_idle(); return
        except RuntimeError:
            time.sleep(30)


def curves_ok(run):
    p = run / 'curve_evaluation/summary.json'
    if not p.exists(): return False
    rows = read(p)
    usable = [r for r in rows if r['status']=='evaluated' and r.get('usable_for_convergence_claim')]
    return len(usable) >= 2 and any(r['name']=='final' for r in usable)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--wait-pid', type=int, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    identity = process_identity(a.wait_pid)
    assert identity is not None and 'run_cvpr_asset_pipeline.py' in identity['cmd'] and 'pipeline_v2' in identity['cmd'], identity
    a.output.mkdir(parents=True, exist_ok=False)
    write(a.output / 'protocol.json', {'wait_for_verified_process': identity, 'pid': a.wait_pid,
        'script_sha256': sha(Path(__file__)), 'candidate_selection': 'entire declared cohort, no metric-driven subset',
        'mapper_source_changes': False, 'stage_gate': 'real checkpoint and shared-tracker pilot artifacts'})
    print('FULL_PANEL_WAIT', a.wait_pid, flush=True)
    while True:
        now = process_identity(a.wait_pid)
        if now is None or now['state']=='Z' or now['start'] != identity['start']: break
        write(a.output / 'waiting.json', {'pid': a.wait_pid, 'verified_live': True, 'checked_at': time.time()})
        time.sleep(30)
    print('FULL_PANEL_PREDECESSOR_TERMINAL', flush=True)
    pipeline = read(RESULTS / 'cvpr_assets/pipeline_v2/summary.json')
    checkpoint_gate = all(any(r['stage']==name and r['status']=='passed' for r in pipeline)
                          for name in ['pilot_checkpoint_d3', 'pilot_checkpoint_vanilla'])
    live_gate = any(r['stage']=='shared_tracking_pilot' and r['status']=='passed' for r in pipeline)
    write(a.output / 'pilot_gates.json', {'checkpoint_pilot': checkpoint_gate, 'shared_tracker_pilot': live_gate})
    fixed.install_paths()
    sys.path.insert(0, '/home/intern/VIGS-SLAM-custom/scripts/selected_mapping')
    py = str(fixed.trial.BASE.PYTHON_ENV / 'bin/python')
    inventory = read(OUT / 'scene_inventory.json')
    jobs = []
    if checkpoint_gate:
        for item in inventory:
            panel = RESULTS / ('cvpr_assets/fixed_work_12f_v1' if item['scene']=='aria301_12F' else 'cvpr_assets/fixed_work_v1')
            for budget in [15, 40]:
                for arm in ['d3', 'vanilla']:
                    run = panel / f'render{budget}' / item['dataset'] / item['scene'] / arm
                    if not (run / 'psnr/strict_fixed_manifest/final_result.json').exists(): continue
                    name = f"curve_{item['dataset']}_{item['scene']}_{budget}_{arm}"
                    jobs.append((name, [py, str(HERE / 'evaluate_cvpr_checkpoints.py'), '--run', str(run),
                        '--dataset', item['dataset'], '--scene', item['scene']], lambda r=run: curves_ok(r)))
    # Controls retain the reference source, tracking trace, render prefixes and cohort.
    ablations = RESULTS / 'cvpr_assets/current_controls_v1'
    ready = [r['scene'] for r in inventory if r['ready']]
    jobs.append(('current_sampler_dense_geometry_controls', [py, str(HERE / 'run_cvpr_ablations.py'),
        '--output', str(ablations), '--scenes', *ready, '--snapshots'],
        lambda: (ablations / 'summary.json').exists() and
        len(read(ablations / 'summary.json'))==len(ready)*7 and
        all(r['status']=='passed' for r in read(ablations / 'summary.json'))))
    if live_gate:
        live = RESULTS / 'cvpr_assets/live_shared_tracking_v1'
        jobs.append(('shared_tracker_full_cohort', [py, str(HERE / 'run_cvpr_live_measurements.py'),
            '--output', str(live), '--snapshots'], lambda: len(read(live / 'summary.json'))==len(inventory)*4 and
            all(r['status']=='passed' for r in read(live / 'summary.json'))))
    results = []
    for name, command, check in jobs:
        print('FULL_PANEL_START', name, flush=True)
        row = {'stage': name, 'command': command, 'status': 'failed'}
        started = time.monotonic()
        try:
            wait_gpu()
            with (a.output / f'{name}.log').open('x') as log:
                cp = subprocess.run(command, cwd=ROOT, env=fixed.environment('vanilla'), stdout=log, stderr=subprocess.STDOUT)
            row['returncode'] = cp.returncode
            row['artifact_check_passed'] = check()
            row['status'] = 'passed' if cp.returncode==0 and row['artifact_check_passed'] else 'failed'
        except Exception:
            row['error'] = traceback.format_exc()
        row['elapsed_seconds'] = time.monotonic()-started
        results.append(row); write(a.output / 'summary.json', results)
        fixed.journal({'dataset': 'cvpr', 'scene': name, 'budget': 'full_asset_panel',
            'arm': 'actual_measurement', 'status': row['status'], 'output': str(a.output / f'{name}.log')})
        print('FULL_PANEL_DONE', name, row['status'], flush=True)
    print('FULL_PANEL_FINISHED', flush=True)


if __name__ == '__main__': main()
