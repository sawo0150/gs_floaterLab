#!/usr/bin/env python3
"""Frozen official tracker capture, archive validation and native setup capture for prepared Oxford sequences.

Same procedure as prepare_cvpr_aria12f.py (official VIGS 22ffe24, TRT dynamic RTX 5090 profile, seed 0, held-out
manifest filtered at replay), then capture_online_worker_setup.py with the Oxford path entries. Run under the colin
worktree profile on an idle GPU. Existing archives/setups are preserved (never overwritten).

  python prepare_oxford_capture.py --sequences ... --execute
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
import run_online_dense_training as trial  # noqa: E402
import oxford_paths  # noqa: E402
from collect_cvpr_assets import ROOT, sha, write  # noqa: E402
import run_b_ablation_chain as base  # noqa: E402

TRT_CWD = Path('/home/intern/gs_floaterLab/results/experiments/exp78/a_paper_reproduction/trt_profiles/'
               'official_readme_dynamic_rtx5090')
V7_ARIA = ROOT / 'benchmarks/online_gs/config/vigs_final_v7_aria.yaml'


def write_mapping_config(d):
    import yaml
    v7 = yaml.safe_load(V7_ARIA.read_text())
    seq_cfg = yaml.safe_load((d / 'config.yaml').read_text())
    v7['IMU'] = seq_cfg['IMU']
    out = d / 'mapping_v7.yaml'
    text = ('# vigs_final_v7_aria.yaml with the Oxford sequence IMU block (prepare_oxford_capture.py)\n'
            + yaml.safe_dump(v7, sort_keys=False))
    if out.exists():
        assert out.read_text() == text, f'{out} differs from regenerated config'
    else:
        out.write_text(text)
    return out

# The capture script only uses --dataset as a metadata label but restricts its choices; allow 'oxford' in memory.
CAPTURE_WRAPPER = '''
import argparse, runpy, sys
_add = argparse._ActionsContainer.add_argument
def add_argument(self, *names, **kw):
    if "--dataset" in names and "choices" in kw:
        kw["choices"] = tuple(kw["choices"]) + ("oxford",)
    return _add(self, *names, **kw)
argparse._ActionsContainer.add_argument = add_argument
sys.argv = {argv!r}
runpy.run_path(sys.argv[0], run_name="__main__")
'''

SETUP_WRAPPER = '''
import sys, runpy
sys.path.insert(0, {here!r})
import run_online_dense_training as trial, oxford_paths
oxford_paths.install(trial)
sys.argv = [{capture!r}, "--dataset", "oxford", "--scene", {seq!r}, "--output", {out!r}]
runpy.run_path({capture!r}, run_name="__main__")
'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--sequences', nargs='+', default=list(oxford_paths.SEQUENCES))
    p.add_argument('--execute', action='store_true')
    a = p.parse_args()
    sys.path.insert(0, str(base.SEL))
    from selected_mapping_check import gpu_idle
    for seq in a.sequences:
        d = oxford_paths.PREP / seq
        x = oxford_paths.paths(seq)
        names = sorted(q.name for q in x['image_dir'].iterdir() if q.suffix == '.jpg')
        cohort = json.loads(x['fixed_manifest'].read_text())
        assert cohort['frame_count'] == len(names) and {v['uid'] for v in cohort['views']} <= set(names)
        capture = ROOT / 'benchmarks/online_gs/exp78b_capture_frozen_tracker.py'
        cmd = [str(trial.BASE.PYTHON_ENV / 'bin/python'), str(capture), '--dataset', 'oxford', '--sequence', seq,
               '--imagedir', str(x['image_dir']), '--imufile', str(d / 'imu.txt'), '--calib', str(x['calibration']),
               '--config', str(x['vanilla_config']),
               '--weights', str(trial.BASE.OFFICIAL_ROOT / 'pretrained_models/droid.pth'),
               '--output', str(x['archive']), '--heldout-manifest', str(x['fixed_manifest']), '--seed', '0',
               '--length', str(len(names)), '--buffer', '700', '--IMU_poseinit_after', '20']
        v7 = write_mapping_config(d)
        write(d / 'capture_command.json', {'cmd': cmd, 'source_sha256': {str(q): sha(q) for q in
              [x['vanilla_config'], x['calibration'], capture, x['fixed_manifest'], d / 'imu.txt', v7, V7_ARIA]},
              'raw_frames': len(names), 'heldout_views': cohort['eval_count'], 'mapping_optimization': False})
        if not a.execute:
            print('PREPARED', seq, len(names), 'frames'); continue
        env = trial.BASE.mapping_environment(False)
        env['PYTHONPATH'] = ':'.join([str(trial.BASE.OFFICIAL_ROOT), str(ROOT / 'benchmarks/online_gs'),
                                      str(trial.BASE.BUILT_THIRDPARTY_ROOT), env['PYTHONPATH']])
        if not x['archive'].exists():
            gpu_idle()
            with (d / 'capture.log').open('x') as log:
                subprocess.run([cmd[0], '-c', CAPTURE_WRAPPER.format(argv=cmd[1:])], env=env, cwd=TRT_CWD,
                               stdout=log, stderr=subprocess.STDOUT, check=True)
            with (d / 'validation.log').open('x') as log:
                subprocess.run([str(trial.BASE.PYTHON_ENV / 'bin/python'), str(trial.BASE.ARCHIVE_VALIDATOR),
                                str(x['archive']), '--output', str(d / 'archive_validation.json')],
                               env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            print('CAPTURE_VALIDATED', seq, flush=True)
        setup = d / 'setup'
        if not setup.exists():
            src = SETUP_WRAPPER.format(here=str(HERE), capture=str(HERE / 'capture_online_worker_setup.py'),
                                       seq=seq, out=str(setup))
            # Setup capture replays through the adopted B mapper: same environment as the mapping runs (run_one).
            from selected_mapping_check import load_lock
            from selected_recipe import recipe_environment
            senv = recipe_environment(trial.BASE.mapping_environment(True), load_lock())
            with (d / 'setup_capture.log').open('x') as log:
                subprocess.run([str(trial.BASE.PYTHON_ENV / 'bin/python'), '-c', src], env=senv,
                               stdout=log, stderr=subprocess.STDOUT, check=True)
            print('SETUP_CAPTURED', seq, flush=True)


if __name__ == '__main__':
    main()
