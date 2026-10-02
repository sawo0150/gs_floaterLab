#!/usr/bin/env python3
"""Live operating point of the adopted B mapper on this machine (RTX 5070 Ti).

Actual RGB+IMU tracking and B mapping run concurrently at sensor pace x {1, 1.2, 1.5}; the mapper stops at the scaled
sensor deadline (zero tail). Records realised training renders per keyframe admission, tracking lag and held-out PSNR.
Card: context/experiments/campaigns/06_gain_attribution/live_operating_point_5070ti/README.md

  ROGO_MACHINE_PROFILE=.../rtx5070ti_b_ablation.json PYTHONPATH=.../rtx5070ti_profile \
    python run_live_b_operating_point.py [--selector ervs] [--scales 1 1.2 1.5] [--keys aria rot rpng utmm]
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MAIN = Path('/home/intern/VIGS-SLAM-custom')               # relocated by the machine profile
SEL = MAIN / 'scripts/selected_mapping'
RECIPE = MAIN / 'configs/selected_mapping_fixed40.json'
OUT_ROOT = ROOT / 'results/campaigns/gain_attribution/live_operating_point_5070ti'
OLD_VIGS = Path('/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM/pretrained_models')
GEN = Path('/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-main-integration-20260828/pretrained_models')
# TensorRT engines built on this RTX 5070 Ti (TensorRT 10.13); all deserialize and match each scene's resolution.
TRT_ENGINES = {'aria': OLD_VIGS, 'rot': OLD_VIGS, 'rpng': GEN / 'generated_rpng_344x616',
               'utmm': GEN / 'generated_utmm_328x648'}
OMNIDATA = [OLD_VIGS / 'omnidata_depth_512_simplified_fp16.engine', OLD_VIGS / 'omnidata_normal_512_simplified_fp16.engine']
SCENES = {'aria': ('aria', 'aria1253'), 'rot': ('aria', 'aria1253rot'), 'rpng': ('rpng', 'table_06'),
          'utmm': ('utmm', 'square-1')}


def read(p):
    return json.loads(Path(p).read_text())


def write(p, x):
    Path(p).write_text(json.dumps(x, indent=2, default=str) + '\n')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--selector', choices=['ervs', 'rr'], default='ervs')
    p.add_argument('--scales', nargs='+', type=float, default=[1.0, 1.2, 1.5])
    p.add_argument('--keys', nargs='+', choices=list(SCENES), default=['aria', 'rot', 'rpng', 'utmm'])
    p.add_argument('--tag', default='')
    p.add_argument('--trt', action='store_true')
    p.add_argument('--version', default='v1')
    a = p.parse_args()
    assert os.environ.get('ROGO_MACHINE_PROFILE'), 'machine profile required'
    sys.path.insert(0, str(SEL))
    from selected_mapping_check import load_lock, gpu_idle
    lock = load_lock()
    sys.path.insert(0, lock['benchmark_helpers'])
    import run_online_dense_training as trial
    from selected_recipe import recipe_environment, install_scene_adapter
    install_scene_adapter()
    global OUT
    OUT = OUT_ROOT / a.version
    OUT.mkdir(parents=True, exist_ok=True)
    engine_cwd = OUT / ('trt_cwd' if a.trt else 'no_trt_cwd')
    engine_cwd.mkdir(exist_ok=True)
    if a.trt and not (engine_cwd / 'pretrained_models').exists():
        pm = engine_cwd / 'pretrained_models'; pm.mkdir()
        for f in [MAIN / 'pretrained_models/droid.pth', MAIN / 'pretrained_models/omnidata_dpt_depth_v2.ckpt',
                  MAIN / 'pretrained_models/omnidata_dpt_normal_v2.ckpt', *OMNIDATA]:
            (pm / Path(f).name).symlink_to(Path(f).resolve())
    if not a.trt and not (engine_cwd / 'pretrained_models').exists():   # tracking loads weights by relative path
        (engine_cwd / 'pretrained_models').symlink_to(MAIN / 'pretrained_models', target_is_directory=True)
    measure = HERE / 'measure_fifo_live_b.py'
    proto = OUT / 'protocol.json'
    if not proto.exists():
        write(proto, dict(main_head=subprocess.check_output(['git', '-C', str(MAIN), 'rev-parse', 'HEAD'], text=True).strip(),
                          lab_head=subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
                          recipe=read(RECIPE), measure=str(measure), measure_sha256=sha(measure),
                          driver_sha256=sha(Path(__file__)), trt=('enabled: ' + json.dumps({k: str(v) for k, v in TRT_ENGINES.items()}) + ' omnidata ' + str(OMNIDATA)
                              + ' sha ' + json.dumps({str(f): sha(f) for d in set(TRT_ENGINES.values()) for f in sorted(Path(d).glob('*.engine'))}
                                                  | {str(f): sha(f) for f in OMNIDATA})) if a.trt else 'disabled (VIGS_DISABLE_TRT=1)',
                          queue_size=2, renders_per_kf_cap=40, frontend_iters='official',
                          machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
                          gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                                       '--format=csv,noheader'], text=True).strip()))
    summary = OUT / 'summary.json'
    rows = read(summary) if summary.exists() else []
    for scale in a.scales:
        for key in a.keys:
            dataset, scene = SCENES[key]
            name = f"{a.selector}{a.tag}"
            out = OUT / ('scale' + format(scale, 'g').replace('.', 'p')) / key / name
            if any(r['output'] == str(out) and r.get('valid') for r in rows):
                continue
            row = dict(key=key, dataset=dataset, scene=scene, selector=a.selector, time_scale=scale, output=str(out),
                       valid=False)
            print('START', scale, key, name, flush=True)
            try:
                if not (out / 'result.json').exists():
                    out.mkdir(parents=True, exist_ok=False)
                    gpu_idle()
                    env = recipe_environment(trial.BASE.mapping_environment(True), lock)
                    env.update(VIGS_PIPELINE_TELEMETRY='1')
                    if a.trt:
                        d = TRT_ENGINES[key]
                        env.update(VIGS_FNET_TRT_ENGINE=str(d / 'droidnet_fnet_fp16.engine'),
                                   VIGS_UPDATE_TRT_ENGINE=str(d / 'update_module_partial_fp16.engine'),
                                   VIGS_UPDATE_PGBA_TRT_ENGINE=str(d / 'update_module_partial_pgba_fp16.engine'))
                        env.pop('VIGS_DISABLE_TRT', None)
                    else:
                        env['VIGS_DISABLE_TRT'] = '1'
                    cmd = [sys.executable, str(measure), '--worker', '--dataset', key, '--time-scale', str(scale),
                           '--queue-size', '2', '--renders-per-kf', '40', '--frontend-iters', 'official',
                           '--selector', a.selector, '--output', str(out)]
                    write(out / 'driver_command.json', dict(cmd=cmd, env={k: env[k] for k in env if k.startswith(
                        ('FIXED40_', 'FR_', 'VIGS_'))}))
                    with (out / 'run.log').open('x') as f:
                        subprocess.run(cmd, env=env, cwd=engine_cwd, stdout=f, stderr=subprocess.STDOUT, check=True)
                r = read(out / 'result.json')
                log = (out / 'run.log').read_text(errors='replace')
                if a.trt:
                    assert 'falling back to PyTorch' not in log and not r['trt_disabled'], 'TRT fallback detected'
                assert not r['error'] and r['source_unchanged'] and r['zero_tail_observed'], 'execution contract'
                assert r['tracked_frames'] == r['input_frames'] and not r['worker']['error'], 'tracking contract'
                cfg = r['geometry']['config']
                assert cfg['w_plain'] == 0.25 and cfg['w_hard'] == 0 and cfg['w_main'] == 0, f'not B loss: {cfg}'
                gpu_idle()
                ev = trial.common.evaluation.panel.run_evaluation_twice(
                    out, dataset, scene, trial.BASE.sequence_paths(dataset, scene)['fixed_manifest'])
                assert ev['pass'], ev
                row.update(valid=True, psnr=ev['fixed_psnr_first'],
                           renders_per_kf=r['renders_per_kf_admission'], committed_renders=r['committed_renders'],
                           kf_admissions=r['kf_admissions'], unique_kfs=r['unique_mapper_kfs'],
                           tracking_kfs=r['tracking_kfs_final'], duration_s=r['duration_seconds'],
                           tracking_elapsed_s=r['tracking_elapsed_seconds'],
                           over_budget_s=r['tracking_elapsed_seconds'] - r['duration_seconds'],
                           end_lag_ms=r['end_lag_ms'], track_call_ms=r['track_call_ms'],
                           mapper_queue_max=r['mapper_queue_max'], trt_disabled=r['trt_disabled'],
                           overruns=r['overruns'], model_load_s=r['model_load_seconds'], trt=a.trt)
            except Exception:
                row['error'] = traceback.format_exc()
            rows = [x for x in rows if x['output'] != str(out)] + [row]
            write(summary, rows)
            print('DONE', scale, key, name, f"psnr={row.get('psnr')}", f"r/kf={row.get('renders_per_kf')}",
                  f"kfs={row.get('kf_admissions')}", f"over={row.get('over_budget_s')}", f"valid={row['valid']}",
                  flush=True)
            if not row['valid']:
                raise RuntimeError(row['error'])
    print('LIVE_OPERATING_POINT_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
