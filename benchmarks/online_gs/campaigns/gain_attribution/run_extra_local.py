#!/usr/bin/env python3
"""Extra datasets on the RTX 5070 Ti: 3 online arms + offline reference, seed 0
(PREREG: context/experiments/campaigns/06_gain_attribution/offline_reference/PREREG.md, Amendment 3).

Inputs were copied from colin (/ssd/intern/paperExperiments/data/...) to the external volume and are relocated by
results/local_machine_profiles/rtx5070ti_extra_datasets.json. Scenes, preflight and paths come from
run_ervs_colin5090.py; FIFO pool cap 700 as on colin (inert for these scenes, checked per run).

  python run_extra_local.py --scenes Retail_Street [--smoke]
"""
import argparse
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_b_ablation_chain as base  # noqa: E402
import run_ervs_colin5090 as C  # noqa: E402
from run_ervs_vs_iid_scenes import ARMS  # noqa: E402
import run_offline_reference as R  # noqa: E402

OUT = base.ROOT / 'results/campaigns/gain_attribution/extra_local_5070ti/v1'
CAP = 700
ORDER = ('ervs_k16', 'uniform_iid', 'uniform_k16', 'offline')


def main():
    p = argparse.ArgumentParser(); p.add_argument('--scenes', nargs='+', required=True)
    p.add_argument('--smoke', action='store_true', help='first scene: ervs_k16 + offline only')
    a = p.parse_args()
    assert os.environ.get('ROGO_MACHINE_PROFILE', '').endswith('rtx5070ti_extra_datasets.json'), 'extra profile required'
    sys.path.insert(0, str(base.SEL))
    from selected_mapping_check import load_lock, verify_files
    lock = load_lock()
    sys.path.insert(0, lock['benchmark_helpers'])
    import run_online_dense_training as trial
    from selected_recipe import recipe_environment, install_scene_adapter
    install_scene_adapter()
    C.install_paths(trial)
    for scene, s in C.SCENES.items():
        lock['datasets'][scene] = dict(dataset=s['dataset'], scene=scene, setup=str(s['setup']))
    base.OUT = OUT
    OUT.mkdir(parents=True, exist_ok=True)
    if not (OUT / 'protocol.json').exists():
        base.write(OUT / 'protocol.json', dict(
            main_head=base.head(base.MAIN), lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE),
            runner_sha256=base.sha(Path(__file__)), machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            patch_sha256={x: base.sha(HERE / x) for x in ('group_k_patch.py', 'sampling_mode_patch.py', 'offline_patch.py',
                                                          'pool_cap.py', 'extra_scene_launcher.py')},
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                         '--format=csv,noheader'], text=True).strip()))
    ctx = (lock, trial, C.make_preflight(trial, verify_files, load_lock), lambda: None, recipe_environment)
    rows = []
    for scene in a.scenes:
        sp = trial.BASE.sequence_paths(C.SCENES[scene]['dataset'], scene)
        extra_scenes = {scene: dict(dataset=C.SCENES[scene]['dataset'], **{k: str(v) for k, v in sp.items()})}
        for arm in (('ervs_k16', 'offline') if a.smoke else ORDER):
            name = f'{arm}_s0'
            ref_dir = OUT / f'scenes/{scene}/render25/ervs_k16_s0'
            if arm == 'offline':
                ref = base.read(ref_dir / 'render_result.json')
                last_uid = [x['uid'] for x in ref['arrivals'] if not x.get('terminal')][-1]
                extra, patch = ['--seed', '0'], 'offline_patch.py'
                env = dict(B_OFFLINE_REF=str(ref_dir / 'render_result.json'), B_OFFLINE_LAST_UID=str(last_uid))
            else:
                x, patch, env = ARMS[arm]; extra = [*x, '--seed', '0']; env = dict(env)
            env.update(B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'), B_PATCH_WORKER=str(HERE / patch),
                       B_EXTRA_SCENES=__import__('json').dumps(extra_scenes), B_POOL_CAP=str(CAP))
            print('START', scene, 25, name, flush=True)
            C.wait_gpu_idle()
            try:
                row = base.run_one('scenes', scene, 25, name, extra, ctx, worker=HERE / 'extra_scene_launcher.py',
                                   env_extra=env)
                out = Path(row['output'])
                pc = base.read(out / 'pool_cap.json')
                assert pc['cap'] == CAP and pc['reserve_calls'] > 0, pc
                row['pool_cap'] = pc
                if arm == 'offline':
                    ok, res = R.gates(out, ref_dir)
                    row['offline_gates'] = res
                    print('GATES', scene, 'PASS' if ok else 'FAIL', res, flush=True)
                    if not ok:
                        raise RuntimeError(f'offline gates failed: {res}')
                elif arm in ('ervs_k16', 'uniform_k16'):
                    g = base.read(out / 'group_k.json'); assert g['stats'].get('groups/dense'), g
                row['seed'] = 0; row['base_arm'] = arm
                base.write(out.parent / f'{name}.row.json', row)
            except Exception:
                base.write(OUT / 'failure.json', dict(scene=scene, arm=name, traceback=traceback.format_exc(),
                                                      time=time.time()))
                raise
            rows.append(row); base.summarize(rows)
            print('DONE', scene, 25, name, f"psnr={row['psnr']:.4f}", 'capped_calls', pc['capped_calls'], flush=True)
    print('EXTRA_LOCAL_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
