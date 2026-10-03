#!/usr/bin/env python3
"""Self-recorded Aria VRS → VIGS inputs → frozen tracker archive → setup (dataset key 'selfaria').

--extract (CPU, aria-tools venv): scripts/incremental/build_vigs_aria_input.py (same procedure as aria1253/305/12F)
  into selfaria_paths.PREP/<seq>/{rgb,imu.txt}; Tcb parsed from its log; config.yaml = official Aria adapter with this
  recording's Tcb; calib.txt = 500 500 512 512 0 0 0 0; heldout.json = every 5th frame + final; mapping_v7.yaml =
  vigs_final_v7_aria.yaml with that IMU block.
--execute (GPU): frozen official tracker capture (seed 0, TRT dynamic RTX 5090), validation, setup capture.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
import run_online_dense_training as trial  # noqa: E402
import selfaria_paths as SP  # noqa: E402
from collect_cvpr_assets import ROOT, sha, write  # noqa: E402
import run_b_ablation_chain as base  # noqa: E402
from prepare_oxford_capture import TRT_CWD, V7_ARIA, SETUP_WRAPPER  # noqa: E402
from prepare_fastlivo_capture import CAPTURE_WRAPPER as _CW  # noqa: E402

CAPTURE_WRAPPER = _CW.replace('("fastlivo",)', '("selfaria",)')
SETUP_WRAPPER_SA = SETUP_WRAPPER.replace('oxford_paths', 'selfaria_paths').replace('"oxford"', '"selfaria"')
ARIA_ENV = Path('/ssd/intern/paperExperiments/envs/aria-tools/bin/python')
BUILDER = ROOT / 'scripts/incremental/build_vigs_aria_input.py'
ADAPTER = ROOT / 'benchmarks/online_gs/config/vigs_official_aria_adapter.yaml'


def extract(seq):
    import yaml
    d = SP.PREP / seq
    if (d / 'rgb').exists():
        raise FileExistsError(f'{d}/rgb exists; extracted inputs are preserved')
    d.mkdir(parents=True, exist_ok=True)
    with (d / 'extract.log').open('x') as log:
        subprocess.run([str(ARIA_ENV), str(BUILDER), '--vrs', str(SP.VRS_ROOT / SP.VRS[seq]), '--output', str(d)],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    text = (d / 'extract.log').read_text()
    rows = re.findall(r'^\s*\[([-0-9.e, ]+)\]\s*$', text.split('[calib] Tcb')[1].split('[rgb]')[0], re.M)
    Tcb = [[float(v) for v in r.split(',')] for r in rows]
    assert len(Tcb) == 4 and all(len(r) == 4 for r in Tcb), Tcb
    cfg = yaml.safe_load(ADAPTER.read_text())
    cfg['IMU']['Tcb_np'] = Tcb
    (d / 'config.yaml').write_text('# official Aria adapter with this recording\'s Tcb (prepare_selfaria.py)\n'
                                   + yaml.safe_dump(cfg, sort_keys=False))
    (d / 'calib.txt').write_text('500.0 500.0 512.0 512.0 0.0 0.0 0.0 0.0\n')
    names = sorted((q.name for q in (d / 'rgb').iterdir() if q.suffix == '.jpg'), key=lambda n: int(n[:-4]))
    views = [dict(frame_index=i, timestamp_token=n[:-4], uid=n) for i, n in enumerate(names)
             if i % 5 == 0 or i == len(names) - 1]
    sj = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()
    (d / 'heldout.json').write_text(json.dumps(dict(
        dataset='selfaria', sequence=seq, role='transfer', selection_rule='zero_based_frame_index % 5 == 0 OR final frame',
        mapping_disjoint_required=True, frame_count=len(names), eval_count=len(views),
        all_input_uids_sha256=sj(names), eval_uids_sha256=sj([v['uid'] for v in views]), views=views), indent=1))
    v7 = yaml.safe_load(V7_ARIA.read_text()); v7['IMU'] = cfg['IMU']
    (d / 'mapping_v7.yaml').write_text('# vigs_final_v7_aria.yaml with this recording\'s Tcb (prepare_selfaria.py)\n'
                                       + yaml.safe_dump(v7, sort_keys=False))
    write(d / 'prep.json', dict(sequence=seq, vrs=str(SP.VRS_ROOT / SP.VRS[seq]), frames=len(names), Tcb=Tcb,
                                sources={str(p): sha(p) for p in (BUILDER, ADAPTER, V7_ARIA)}))
    print('EXTRACTED', seq, len(names), 'frames', len(views), 'held-out', flush=True)


def capture(seq, buffer):
    sys.path.insert(0, str(base.SEL))
    from selected_mapping_check import gpu_idle, load_lock
    from selected_recipe import recipe_environment
    d = SP.PREP / seq; x = SP.paths(seq)
    names = sorted(q.name for q in x['image_dir'].iterdir() if q.suffix == '.jpg')
    cap = ROOT / 'benchmarks/online_gs/exp78b_capture_frozen_tracker.py'
    cmd = [str(trial.BASE.PYTHON_ENV / 'bin/python'), str(cap), '--dataset', 'selfaria', '--sequence', seq,
           '--imagedir', str(x['image_dir']), '--imufile', str(d / 'imu.txt'), '--calib', str(x['calibration']),
           '--config', str(x['vanilla_config']), '--weights', str(trial.BASE.OFFICIAL_ROOT / 'pretrained_models/droid.pth'),
           '--output', str(x['archive']), '--heldout-manifest', str(x['fixed_manifest']), '--seed', '0',
           '--length', str(len(names)), '--buffer', str(buffer), '--IMU_poseinit_after', '20']
    write(d / 'capture_command.json', {'cmd': cmd, 'source_sha256': {str(q): sha(q) for q in
          [x['vanilla_config'], x['calibration'], cap, x['fixed_manifest'], d / 'imu.txt', x['custom_config']]},
          'raw_frames': len(names), 'mapping_optimization': False})
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
    if not (d / 'setup').exists():
        src = SETUP_WRAPPER_SA.format(here=str(HERE), capture=str(HERE / 'capture_online_worker_setup.py'),
                                      seq=seq, out=str(d / 'setup'))
        senv = recipe_environment(trial.BASE.mapping_environment(True), load_lock())
        with (d / 'setup_capture.log').open('x') as log:
            subprocess.run([str(trial.BASE.PYTHON_ENV / 'bin/python'), '-c', src], env=senv,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        print('SETUP_CAPTURED', seq, flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--sequences', nargs='+', default=list(SP.SEQUENCES))
    p.add_argument('--extract', action='store_true')
    p.add_argument('--execute', action='store_true')
    p.add_argument('--buffer', type=int, default=700)
    a = p.parse_args()
    for seq in a.sequences:
        if a.extract:
            extract(seq)
        if a.execute:
            capture(seq, a.buffer)


if __name__ == '__main__':
    main()
