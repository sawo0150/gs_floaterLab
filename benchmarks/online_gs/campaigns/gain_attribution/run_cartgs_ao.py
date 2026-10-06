#!/usr/bin/env python3
"""CaRtGS adaptive optimization as a sampler (PREREG: context/experiments/campaigns/06_gain_attribution/cartgs_ao/PREREG.md).

  python run_cartgs_ao.py --scenes utmm ego-centric-1 ... --seeds 0
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
import run_ervs_vs_iid_scenes as X  # noqa: E402

OUT = base.ROOT / 'results/campaigns/gain_attribution/cartgs_ao/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/cartgs_ao/PREREG.md'
PINNED = ('aria', 'rpng', 'rot', 'utmm')


def main():
    p = argparse.ArgumentParser(); p.add_argument('--scenes', nargs='+', required=True)
    p.add_argument('--seeds', nargs='+', type=int, default=[0]); a = p.parse_args()
    assert os.environ.get('ROGO_MACHINE_PROFILE'), 'machine profile required'
    sys.path.insert(0, str(base.SEL))
    from selected_mapping_check import load_lock, preflight, verify_files
    lock = load_lock()
    sys.path.insert(0, lock['benchmark_helpers'])
    import run_online_dense_training as trial
    from selected_recipe import recipe_environment, install_scene_adapter
    install_scene_adapter()
    for scene, ds in X.SCENES.items():
        lock['datasets'][scene] = dict(dataset=ds, scene=scene, setup=str(X.SETUPS / ds / scene / 'setup'))
    base.OUT = OUT
    OUT.mkdir(parents=True, exist_ok=True)
    if not (OUT / 'protocol.json').exists():
        base.write(OUT / 'protocol.json', dict(
            prereg=str(PREREG), prereg_sha256=base.sha(PREREG), main_head=base.head(base.MAIN),
            lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE),
            patch_sha256={x: base.sha(HERE / x) for x in ('cartgs_ao_patch.py', 'train_signal.py', 'legacy_imu_launcher.py')},
            machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version', '--format=csv,noheader'], text=True).strip()))
    pf_extra = X.make_preflight(trial, verify_files, load_lock)
    rows = []
    for seed in a.seeds:
        for key in a.scenes:
            name = f'cartgs_ao_s{seed}'
            env = dict(B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'))
            if key in PINNED:
                pf, worker = preflight, HERE / 'cartgs_ao_patch.py'
            else:
                pf, worker = pf_extra, HERE / 'legacy_imu_launcher.py'; env['B_PATCH_WORKER'] = str(HERE / 'cartgs_ao_patch.py')
            print('START', key, 25, name, flush=True)
            try:
                base.OUT = OUT
                row = base.run_one('scenes', key, 25, name, ['--seed', str(seed)], (lock, trial, pf, lambda: None, recipe_environment),
                                   worker=worker, env_extra=env)
                out = Path(row['output'])
                st = base.read(out / 'cartgs_ao.json')['stats']
                draws = sum(v for k, v in st.items() if k.startswith(('draw/', 'fallback/', 'borrow/')))
                fb = sum(v for k, v in st.items() if k.startswith(('fallback/', 'borrow/')))
                assert st.get('refill/keyframe') and st.get('refill/dense'), st
                assert fb <= 0.20 * draws, st   # Amendment 2: window picks + distinct-view batches force borrows
                assert st.get('refill_top/keyframe') and st.get('refill_top/dense'), st
                row.update(seed=seed, cartgs_ao=st)
                base.write(out.parent / f'{name}.row.json', row)
            except Exception:
                base.write(OUT / 'failure.json', dict(key=key, arm=name, traceback=traceback.format_exc(), time=time.time()))
                raise
            rows.append(row); base.summarize(rows)
            print('DONE', key, 25, name, f"psnr={row['psnr']:.4f}", st, flush=True)
    print('CARTGS_AO_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
