#!/usr/bin/env python3
"""Run the existing pair with observational PLY checkpoints; preserve originals."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

WORK = Path('/home/intern/gs_floaterLab')
ROOT = Path(__file__).resolve().parent.parent
SOURCE = WORK / 'results/experiments/exp94_normalized_metric_v2_fixed_eval/aria/aria301_305'
OUTPUT = WORK / 'results/figure03_convergence_20260921/aria301_305'
sys.path.insert(0, str(WORK / 'benchmarks/online_gs'))


def mapping_environment(custom):
    env = os.environ.copy()
    built = Path('/home/intern/VIGS-SLAM-visible-lazy-carve/thirdparty')
    paper = Path('/home/intern/VIGS-SLAM-paper-full')
    official = Path('/home/intern/VIGS-SLAM-official-exp78')
    python_env = Path(sys.executable).parent.parent
    components = ([paper/'vigs', paper, built.parent, built/'diff-gaussian-rasterization']
                  if custom else [official/'vigs',official/'thirdparty/diff-gaussian-rasterization'])
    components += [built/'lietorch_5090', built/'simple-knn']
    if custom:
        env['EXP78B_CUSTOM_ROOT'] = str(paper)
    env['PYTHONPATH'] = ':'.join([str(p) for p in components] + ([env['PYTHONPATH']] if env.get('PYTHONPATH') else []))
    env['LD_LIBRARY_PATH'] = ':'.join([str(python_env/'lib/python3.11/site-packages/torch/lib'),str(python_env/'lib')] + ([env['LD_LIBRARY_PATH']] if env.get('LD_LIBRARY_PATH') else []))
    env['PYTHONUNBUFFERED'] = '1'
    return env


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    lock = json.loads((SOURCE.parents[1] / 'source_lock.json').read_text())['sha256']
    changes = [name for name, h in lock.items() if hashlib.sha256(Path(name).read_bytes()).hexdigest() != h]
    # Old panel launchers are not imported or executed by this capture runner.
    unused_launchers = {'run_exp78b_stage6rx4_cross_sequence.py',
                        'run_exp91_normalized_metric_v2_reliable.py',
                        'run_exp94_normalized_metric_v2_fixed_eval.py'}
    active_changes = [name for name in changes if Path(name).name not in unused_launchers]
    assert not active_changes, active_changes
    (OUTPUT / 'source_lock.json').write_text(json.dumps(lock, indent=2)+'\n')
    (OUTPUT / 'source_audit.json').write_text(json.dumps({'changed_unused_panel_launchers':changes,'active_training_sources_match':True},indent=2)+'\n')
    for arm, original in [('ours', 'normalized_variance_s0'), ('baseline', 'native_vanilla_render_matched_s0')]:
        run = OUTPUT / arm
        if (run / 'capture_manifest.json').exists():
            print(arm, 'already captured', flush=True)
            continue
        active = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],text=True).strip()
        assert not active, f'GPU occupied; wait without terminating: {active}'
        run.mkdir(exist_ok=True)
        command = [sys.executable, str(ROOT/'scripts/capture_convergence.py'), '--arm',arm,
                   '--source-run',str(SOURCE/original),'--output',str(run)]
        if arm == 'baseline':
            command += ['--reference-runtime',str(OUTPUT/'ours/mapping_replay_runtime.json')]
        print('Starting',arm,flush=True)
        with (run/'mapping.log').open('wb') as sink:
            subprocess.run(command, cwd=WORK, env=mapping_environment(arm=='ours'), stdout=sink, stderr=subprocess.STDOUT, check=True)
        runtime = json.loads((run/'mapping_replay_runtime.json').read_text())
        old = json.loads((SOURCE/original/'mapping_replay_runtime.json').read_text())
        keys = ['optimizer_steps_completed','rasterized_view_updates','gaussians']
        comparison = {k:{'original':old[k],'new':runtime[k]} for k in keys}
        (run/'rerun_work_comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
        assert runtime['rasterized_view_updates'] == old['rasterized_view_updates'], comparison
        print('Completed',arm,comparison,flush=True)


if __name__ == '__main__':
    main()
