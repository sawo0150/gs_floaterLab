#!/usr/bin/env python3
"""Held-out manifest, configs, frozen official tracker capture, validation and setup capture for FAST-LIVO2.

Mirrors prepare_oxford_capture.py: official VIGS 22ffe24 with the official config/fastlivo.yaml (tracking contract
unchanged), --undistort (radtan intrinsics), seed 0, TRT dynamic RTX 5090 profile; held-out = every 5th frame + final;
mapping config = vigs_final_v7_aria.yaml with the fastlivo IMU block and Tcb_np from the sequence extrinsics.txt (VIGS
reads the same file at runtime for 'livo2' paths). Existing archives/setups are preserved.

  python prepare_fastlivo_capture.py --sequences ... [--execute] [--buffer 700]
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
import run_online_dense_training as trial  # noqa: E402
import fastlivo_paths as FP  # noqa: E402
from collect_cvpr_assets import ROOT, sha, write  # noqa: E402
import run_b_ablation_chain as base  # noqa: E402
from prepare_oxford_capture import TRT_CWD, V7_ARIA, SETUP_WRAPPER  # noqa: E402

CAPTURE_WRAPPER = '''
import argparse, runpy, sys
_add = argparse._ActionsContainer.add_argument
def add_argument(self, *names, **kw):
    if "--dataset" in names and "choices" in kw:
        kw["choices"] = tuple(kw["choices"]) + ("fastlivo",)
    return _add(self, *names, **kw)
argparse._ActionsContainer.add_argument = add_argument
sys.argv = {argv!r}
runpy.run_path(sys.argv[0], run_name="__main__")
'''
SETUP_WRAPPER_FL = SETUP_WRAPPER.replace('oxford_paths', 'fastlivo_paths').replace('"oxford"', '"fastlivo"')


def write_inputs(seq):
    import yaml
    d = FP.PREP / seq; d.mkdir(parents=True, exist_ok=True)
    raw = FP.RAW / seq
    names = sorted(q.name for q in (raw / 'rgb').iterdir() if q.suffix == '.png')
    names.sort(key=lambda n: int(Path(n).stem))
    views = [dict(frame_index=i, timestamp_token=n[:-4], uid=n) for i, n in enumerate(names)
             if i % 5 == 0 or i == len(names) - 1]
    sj = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()
    manifest = dict(dataset='fastlivo', sequence=seq, role='transfer',
                    selection_rule='zero_based_frame_index % 5 == 0 OR final frame', mapping_disjoint_required=True,
                    frame_count=len(names), eval_count=len(views), all_input_uids_sha256=sj(names),
                    eval_uids_sha256=sj([v['uid'] for v in views]), views=views)
    text = json.dumps(manifest, indent=1)
    hm = d / 'heldout.json'
    if hm.exists():
        assert hm.read_text() == text, 'existing held-out manifest differs'
    else:
        hm.write_text(text)
    official = trial.BASE.OFFICIAL_ROOT / 'config/fastlivo.yaml'
    cfg = official.read_text()
    (d / 'config.yaml').write_text(cfg) if not (d / 'config.yaml').exists() else None
    assert (d / 'config.yaml').read_text() == cfg
    v7 = yaml.safe_load(V7_ARIA.read_text())
    imu = yaml.safe_load(cfg)['IMU']
    imu['Tcb_np'] = np.loadtxt(raw / 'extrinsics.txt').tolist()
    v7['IMU'] = imu
    vt = ('# vigs_final_v7_aria.yaml with the official fastlivo IMU block and this sequence extrinsics.txt '
          '(prepare_fastlivo_capture.py)\n' + yaml.safe_dump(v7, sort_keys=False))
    out = d / 'mapping_v7.yaml'
    if out.exists():
        assert out.read_text() == vt
    else:
        out.write_text(vt)
    return names, manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--sequences', nargs='+', default=list(FP.SEQUENCES))
    p.add_argument('--execute', action='store_true')
    p.add_argument('--buffer', type=int, default=700)
    a = p.parse_args()
    sys.path.insert(0, str(base.SEL))
    from selected_mapping_check import gpu_idle, load_lock
    from selected_recipe import recipe_environment
    for seq in a.sequences:
        d = FP.PREP / seq
        names, manifest = write_inputs(seq)
        x = FP.paths(seq)
        capture = ROOT / 'benchmarks/online_gs/exp78b_capture_frozen_tracker.py'
        cmd = [str(trial.BASE.PYTHON_ENV / 'bin/python'), str(capture), '--dataset', 'fastlivo', '--sequence', seq,
               '--imagedir', str(x['image_dir']), '--imufile', str(FP.RAW / seq / 'imu.txt'),
               '--calib', str(x['calibration']), '--config', str(x['vanilla_config']),
               '--weights', str(trial.BASE.OFFICIAL_ROOT / 'pretrained_models/droid.pth'),
               '--output', str(x['archive']), '--heldout-manifest', str(x['fixed_manifest']), '--seed', '0',
               '--length', str(len(names)), '--buffer', str(a.buffer), '--IMU_poseinit_after', '25', '--undistort']  # official eval_fastlivo_mono.py value (= config imu_late_init_from)
        write(d / 'capture_command.json', {'cmd': cmd, 'source_sha256': {str(q): sha(q) for q in
              [x['vanilla_config'], x['calibration'], capture, x['fixed_manifest'], FP.RAW / seq / 'imu.txt',
               FP.RAW / seq / 'extrinsics.txt', x['custom_config'], V7_ARIA]},
              'raw_frames': len(names), 'heldout_views': manifest['eval_count'], 'mapping_optimization': False})
        if not a.execute:
            print('PREPARED', seq, len(names), 'frames', manifest['eval_count'], 'held-out', flush=True); continue
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
            src = SETUP_WRAPPER_FL.format(here=str(HERE), capture=str(HERE / 'capture_online_worker_setup.py'),
                                          seq=seq, out=str(setup))
            senv = recipe_environment(trial.BASE.mapping_environment(True), load_lock())
            with (d / 'setup_capture.log').open('x') as log:
                subprocess.run([str(trial.BASE.PYTHON_ENV / 'bin/python'), '-c', src], env=senv,
                               stdout=log, stderr=subprocess.STDOUT, check=True)
            print('SETUP_CAPTURED', seq, flush=True)


if __name__ == '__main__':
    main()
