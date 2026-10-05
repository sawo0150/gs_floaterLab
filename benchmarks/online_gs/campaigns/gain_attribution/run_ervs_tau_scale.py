#!/usr/bin/env python3
"""ERVS K16 with tau 8 / 16 (PREREG: context/experiments/campaigns/06_gain_attribution/ervs_tau_scale/PREREG.md).

  python run_ervs_tau_scale.py      # seed 0 on all scenes, then seeds 1-2 (19 scenes), FAST-LIVO2 seed 0 only
"""
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

OUT = base.ROOT / 'results/campaigns/gain_attribution/ervs_tau_scale/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/ervs_tau_scale/PREREG.md'
PINNED = ('aria', 'rpng', 'rot', 'utmm')
FASTLIVO = ('Retail_Street', 'HKU_Campus', 'CBD_Building_01', 'SYSU_01', 'CBD_Building_02')
TAUS = (8, 16)


def plan():
    keys = list(PINNED) + list(X.SCENES)
    p = [(k, t, 0) for k in keys + list(FASTLIVO) for t in TAUS]
    p += [(k, t, s) for s in (1, 2) for k in keys for t in TAUS]
    return p


def main():
    assert os.environ.get('ROGO_MACHINE_PROFILE', '').endswith('rtx5070ti_extra_datasets.json'), 'extra profile required'
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
            prereg=str(PREREG), prereg_sha256=base.sha(PREREG), main_head=base.head(base.MAIN),
            lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE), plan=plan(),
            patch_sha256={x: base.sha(HERE / x) for x in ('group_k_patch.py', 'legacy_imu_launcher.py',
                                                          'extra_scene_launcher.py', 'pool_cap.py')},
            machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                         '--format=csv,noheader'], text=True).strip()))
    pf_extra = X.make_preflight(trial, verify_files, load_lock)
    pf_local = C.make_preflight(trial, verify_files, load_lock)
    rows = []
    for key, tau, seed in plan():
        name = f'ervs_t{tau}_s{seed}'
        env = dict(B_GROUP_K='16', B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'))
        if key in PINNED:
            pf, worker = preflight, HERE / 'group_k_patch.py'
        elif key in X.SCENES:
            pf, worker = pf_extra, HERE / 'legacy_imu_launcher.py'; env['B_PATCH_WORKER'] = str(HERE / 'group_k_patch.py')
        else:
            pf, worker = pf_local, HERE / 'extra_scene_launcher.py'
            sp = trial.BASE.sequence_paths(C.SCENES[key]['dataset'], key)
            env.update(B_PATCH_WORKER=str(HERE / 'group_k_patch.py'), B_POOL_CAP='700', B_EXTRA_SCENES=json.dumps(
                {key: dict(dataset=C.SCENES[key]['dataset'], **{k: str(v) for k, v in sp.items()})}))
        ctx = (lock, trial, pf, lambda: None, recipe_environment)
        print('START', key, 25, name, flush=True)
        C.wait_gpu_idle()
        try:
            base.OUT = OUT
            row = base.run_one('scenes', key, 25, name, ['--tau', str(tau), '--seed', str(seed)], ctx, worker=worker,
                               env_extra=env)
            out = Path(row['output'])
            pol = base.read(out / 'render_result.json')['training']['generations'][-1]['policy']
            assert abs(float(pol['tau']) - tau) < 1e-9, pol['tau']
            g = base.read(out / 'group_k.json'); assert g['stats'].get('groups/dense'), g
            row.update(seed=seed, tau=tau, group_k=g)
            base.write(out.parent / f'{name}.row.json', row)
        except Exception:
            base.write(OUT / 'failure.json', dict(key=key, arm=name, traceback=traceback.format_exc(), time=time.time()))
            raise
        rows.append(row); base.summarize(rows)
        print('DONE', key, 25, name, f"psnr={row['psnr']:.4f}", flush=True)
    print('TAU_SCALE_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
