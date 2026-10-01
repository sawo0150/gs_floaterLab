#!/usr/bin/env python3
"""Serialize measurement stages after a verified existing GPU job.

Only measurement runners are invoked. No production edits, scene tuning,
background agent delegation, or evaluator feedback into mapping occurs.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import run_cvpr_measurements as fixed
from collect_cvpr_assets import ROOT, RESULTS, OUT, read, write, sha


def process_identity(pid):
    path = Path(f'/proc/{pid}')
    try:
        fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
        return {'start': fields[19], 'state': fields[0],
                'cmd': (path / 'cmdline').read_bytes().replace(b'\0', b' ').decode()}
    except FileNotFoundError:
        return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--wait-pid', type=int, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    identity = process_identity(a.wait_pid)
    if identity is not None:
        assert 'run_cvpr_measurements.py' in identity['cmd'] and 'fixed_work_v1' in identity['cmd'], identity
    a.output.mkdir(parents=True, exist_ok=False)
    write(a.output / 'protocol.json', {'wait_pid': a.wait_pid, 'verified_process_identity': identity,
          'script': str(Path(__file__)), 'script_sha256': sha(Path(__file__)),
          'scope': 'serial GPU capture, current fixed-work, checkpoint evaluation and shared-tracker pilot',
          'automatic_scene_selection': False})
    print('PIPELINE_WAIT', a.wait_pid, flush=True)
    while identity is not None:
        now = process_identity(a.wait_pid)
        if now is None or now['state'] == 'Z' or now['start'] != identity['start']:
            break
        write(a.output / 'waiting.json', {'pid': a.wait_pid, 'verified_live': True, 'checked_at': time.time()})
        time.sleep(30)
    print('PIPELINE_PRIMARY_JOB_TERMINAL', flush=True)
    rows = []
    py = str(fixed.trial.BASE.PYTHON_ENV / 'bin/python')
    stages = [
        ('capture_12f', [py, str(HERE / 'prepare_cvpr_aria12f.py'), '--execute']),
        ('fixed_work_12f', [py, str(HERE / 'run_cvpr_measurements.py'), '--output', str(RESULTS / 'cvpr_assets/fixed_work_12f_v1'), '--scenes', 'aria301_12F', '--snapshots']),
        ('pilot_checkpoint_d3', [py, str(HERE / 'evaluate_cvpr_checkpoints.py'), '--run', str(RESULTS / 'cvpr_assets/pilot_v1/render15/aria/aria1253/d3'), '--dataset', 'aria', '--scene', 'aria1253']),
        ('pilot_checkpoint_vanilla', [py, str(HERE / 'evaluate_cvpr_checkpoints.py'), '--run', str(RESULTS / 'cvpr_assets/pilot_v1/render15/aria/aria1253/vanilla'), '--dataset', 'aria', '--scene', 'aria1253']),
        ('shared_tracking_pilot', [py, str(HERE / 'run_cvpr_live_measurements.py'), '--output', str(RESULTS / 'cvpr_assets/live_shared_tracking_v1'), '--scenes', 'aria1253', 'table_01', '--snapshots']),
    ]
    for name, command in stages:
        print('PIPELINE_START', name, flush=True)
        row = {'stage': name, 'command': command, 'status': 'failed'}
        started = time.monotonic()
        try:
            fixed.install_paths()
            sys.path.insert(0, '/home/intern/VIGS-SLAM-custom/scripts/selected_mapping')
            from selected_mapping_check import gpu_idle
            while True:
                try:
                    gpu_idle(); break
                except RuntimeError:
                    write(a.output / 'waiting_gpu.json', {'stage': name, 'checked_at': time.time()})
                    time.sleep(30)
            with (a.output / f'{name}.log').open('x') as log:
                cp = subprocess.run(command, cwd=ROOT, env=fixed.environment('vanilla'),
                                    stdout=log, stderr=subprocess.STDOUT)
            row['returncode'] = cp.returncode
            if cp.returncode == 0:
                row['status'] = 'passed'
                if name == 'capture_12f':
                    row['status'] = 'passed' if any(r['scene'] == 'aria301_12F' and r['ready'] for r in read(OUT / 'scene_inventory.json')) else 'failed'
                elif name == 'fixed_work_12f':
                    panel = read(RESULTS / 'cvpr_assets/fixed_work_12f_v1/summary.json')
                    row['completed_runs'] = len(panel)
                    row['status'] = 'passed' if len(panel) == 4 and all(r['status'] == 'passed' for r in panel) else 'failed'
                elif name == 'shared_tracking_pilot':
                    panel = read(RESULTS / 'cvpr_assets/live_shared_tracking_v1/summary.json')
                    row['status'] = 'passed' if len(panel) == 8 and all(r['status'] == 'passed' for r in panel) else 'failed'
                    row['completed_runs'] = len(panel)
                elif name.startswith('pilot_checkpoint'):
                    arm = 'd3' if name.endswith('d3') else 'vanilla'
                    panel = read(RESULTS / f'cvpr_assets/pilot_v1/render15/aria/aria1253/{arm}/curve_evaluation/summary.json')
                    row['evaluated_states'] = sum(r['status'] == 'evaluated' for r in panel)
                    row['status'] = 'passed' if row['evaluated_states'] > 1 and panel[-1]['status'] == 'evaluated' else 'failed'
        except Exception:
            row['error'] = __import__('traceback').format_exc()
        row['elapsed_seconds'] = time.monotonic() - started
        rows.append(row); write(a.output / 'summary.json', rows)
        fixed.journal({'dataset': 'cvpr', 'scene': name, 'budget': 'measurement_stage',
                       'arm': 'pipeline', 'status': row['status'], 'output': str(a.output / f'{name}.log')})
        print('PIPELINE_DONE', name, row['status'], flush=True)
    print('PIPELINE_FINISHED', flush=True)


if __name__ == '__main__': main()
