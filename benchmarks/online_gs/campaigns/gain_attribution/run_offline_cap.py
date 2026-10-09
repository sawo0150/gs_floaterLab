#!/usr/bin/env python3
"""Offline reference with scale cap 0.5 on any pinned / ervs_vs_iid-scenes key (RPNG decomposition; PREREG:
context/experiments/campaigns/06_gain_attribution/decomposition_rpng/PREREG.md). Same patch and gates as
run_offline_reference.py; output offline_reference/v1/offline/<key>/render25/offline_cap05_s0.
  python run_offline_cap.py --scenes rpng table_01 ...
"""
import argparse
import os
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_b_ablation_chain as base  # noqa: E402
import build_ervs_scenes_page as S  # noqa: E402
import run_offline_reference as O  # noqa: E402
import run_ervs_vs_iid_scenes as X  # noqa: E402

PINNED = ('aria', 'rpng', 'rot', 'utmm')


def main():
    p = argparse.ArgumentParser(); p.add_argument('--scenes', nargs='+', required=True); a = p.parse_args()
    sys.path.insert(0, str(base.SEL))
    from selected_mapping_check import load_lock, preflight, gpu_idle, verify_files
    lock = load_lock()
    sys.path.insert(0, lock['benchmark_helpers'])
    import run_online_dense_training as trial
    from selected_recipe import recipe_environment, install_scene_adapter
    install_scene_adapter()
    for scene, dataset in X.SCENES.items():
        lock['datasets'][scene] = dict(dataset=dataset, scene=scene, setup=str(X.SETUPS / dataset / scene / 'setup'))
    pf_x = X.make_preflight(trial, verify_files, load_lock)
    base.OUT = O.OFFLINE_OUT
    for key in a.scenes:
        name = 'offline_cap05_s0'
        if key in PINNED:
            ref_dir, worker, env = S.pinned_dir(key, 'ervs_k16', 0), HERE / 'offline_patch.py', {}
            ctx = (lock, trial, preflight, gpu_idle, recipe_environment)
        else:
            ref_dir, worker = S.OUT / f'scenes/{key}/render25/ervs_k16_s0', HERE / 'legacy_imu_launcher.py'
            env = dict(B_PATCH_WORKER=str(HERE / 'offline_patch.py'))
            ctx = (lock, trial, pf_x, gpu_idle, recipe_environment)
        ref = base.read(ref_dir / 'render_result.json')
        last_uid = [x['uid'] for x in ref['arrivals'] if not x.get('terminal')][-1]
        print('START', key, 25, name, flush=True)
        try:
            base.OUT = O.OFFLINE_OUT
            row = base.run_one('offline', key, 25, name, ['--seed', '0'], ctx, worker=worker, env_extra=dict(
                B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'), B_OFFLINE_REF=str(ref_dir / 'render_result.json'),
                B_OFFLINE_LAST_UID=str(last_uid), B_SCALE_CAP='0.5', **env))
            out = Path(row['output'])
            ok, res = O.gates(out, ref_dir)
            row['offline_gates'] = res; row['reference'] = str(ref_dir)
            base.write(out.parent / f'{name}.row.json', row)
            print('GATES', key, name, 'PASS' if ok else 'FAIL', res, flush=True)
            print('DONE', key, 25, name, f"psnr={row['psnr']:.4f}", flush=True)
        except Exception:
            base.write(O.OFFLINE_OUT / 'failure_cap05.json', dict(key=key, traceback=traceback.format_exc()))
            print('FAILED', key, name, flush=True)
    print('OFFLINE_CAP_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
