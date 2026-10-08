#!/usr/bin/env python3
"""Birth-triggered repair replay (PREREG: context/experiments/campaigns/06_gain_attribution/birth_repair/PREREG.md).

  python run_birth_repair.py --scenes aria utmm
"""
import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_b_ablation_chain as base  # noqa: E402
import run_ervs_vs_iid_scenes as X  # noqa: E402
import run_ervs_colin5090 as C  # noqa: E402
import build_ervs_scenes_page as S  # noqa: E402

OUT = base.ROOT / 'results/campaigns/gain_attribution/birth_repair/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/birth_repair/PREREG.md'
PINNED = ('aria', 'rpng', 'rot', 'utmm')
EXTRA_LOCAL = S.R / 'extra_local_5070ti/v1'
ARMS = {'repair6': (dict(B_REPAIR_N='6', B_REPAIR_LAG='6', B_REPAIR_MIN='0.2'), [])}
PATCH = 'birth_repair_patch.py'


def ref_dir(key, arm):
    if key in PINNED:
        return S.pinned_dir(key, arm, 0)
    if key in X.SCENES:
        return S.OUT / f'scenes/{key}/render25/{arm}_s0'
    return EXTRA_LOCAL / f'scenes/{key}/render25/{arm}_s0'


def main():
    p = argparse.ArgumentParser(); p.add_argument('--scenes', nargs='+', required=True)
    p.add_argument('--arms', nargs='+', default=list(ARMS)); a = p.parse_args()
    assert os.environ.get('ROGO_MACHINE_PROFILE', '').endswith('rtx5070ti_extra_datasets.json')
    sys.path.insert(0, str(base.SEL))
    from selected_mapping_check import load_lock, preflight, verify_files
    lock = load_lock()
    sys.path.insert(0, lock['benchmark_helpers'])
    import run_online_dense_training as trial
    from selected_recipe import recipe_environment, install_scene_adapter
    install_scene_adapter()
    C.install_paths(trial)
    for scene, ds in X.SCENES.items():
        lock['datasets'][scene] = dict(dataset=ds, scene=scene, setup=str(X.SETUPS / ds / scene / 'setup'))
    for scene, s in C.SCENES.items():
        lock['datasets'][scene] = dict(dataset=s['dataset'], scene=scene, setup=str(s['setup']))
    base.OUT = OUT
    OUT.mkdir(parents=True, exist_ok=True)
    if not (OUT / 'protocol.json').exists():
        base.write(OUT / 'protocol.json', dict(
            prereg=str(PREREG), prereg_sha256=base.sha(PREREG), main_head=base.head(base.MAIN), lab_head=base.head(base.ROOT),
            recipe=base.read(base.RECIPE), patch_sha256=base.sha(HERE / PATCH),
            machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version', '--format=csv,noheader'], text=True).strip()))
    pf_extra = X.make_preflight(trial, verify_files, load_lock)
    pf_local = C.make_preflight(trial, verify_files, load_lock)
    rows = []
    for key in a.scenes:
        for arm in a.arms:
            env, extra = ARMS[arm]
            name = f'{arm}_s0'
            env = dict(env, B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'), B_GROUP_K='16')
            if key in PINNED:
                pf, worker = preflight, HERE / PATCH
            elif key in X.SCENES:
                pf, worker = pf_extra, HERE / 'legacy_imu_launcher.py'; env['B_PATCH_WORKER'] = str(HERE / PATCH)
            else:
                pf, worker = pf_local, HERE / 'extra_scene_launcher.py'
                sp = trial.BASE.sequence_paths(C.SCENES[key]['dataset'], key)
                env.update(B_PATCH_WORKER=str(HERE / PATCH), B_POOL_CAP='700', B_EXTRA_SCENES=json.dumps(
                    {key: dict(dataset=C.SCENES[key]['dataset'], **{k: str(v) for k, v in sp.items()})}))
            print('START', key, 25, name, flush=True)
            C.wait_gpu_idle()
            try:
                base.OUT = OUT
                row = base.run_one('repair', key, 25, name, [*extra, '--seed', '0'], (lock, trial, pf, lambda: None, recipe_environment),
                                   worker=worker, env_extra=env)
                out = Path(row['output'])
                L = base.read(out / 'birth_repair.json')
                row.update(repair={k: v for k, v in L.items() if k != 'events'}, gate_ok=bool(L['stats'].get('birth_repair_events')) and not L['stats'].get('repair_error'))
                base.write(out.parent / f'{name}.row.json', row)
            except Exception:
                base.write(OUT / 'failure.json', dict(key=key, arm=name, traceback=traceback.format_exc(), time=time.time()))
                print('FAILED', key, name, flush=True)
                continue
            rows.append(row); base.summarize(rows)
            print('DONE', key, 25, name, f"psnr={row['psnr']:.4f}", L['stats'], flush=True)
    print('REPAIR_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
