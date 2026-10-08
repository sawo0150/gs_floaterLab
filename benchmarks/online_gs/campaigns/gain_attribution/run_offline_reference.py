#!/usr/bin/env python3
"""Offline (deferred-training) reference on the four B scenes, budget 25
(PREREG: context/experiments/campaigns/06_gain_attribution/offline_reference/PREREG.md).

  python run_offline_reference.py --smoke     # square-1 seed 0 with gates
  python run_offline_reference.py             # smoke gates, then 4 scenes × seeds 0–2
  python run_offline_reference.py --extra     # Amendment 2: 15 extra scenes, seed 0
"""
import argparse
import os
import subprocess
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_b_ablation_chain as base  # noqa: E402
import build_ervs_scenes_page as S  # noqa: E402

base.OUT = OFFLINE_OUT = base.ROOT / 'results/campaigns/gain_attribution/offline_reference/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/offline_reference/PREREG.md'
BUDGET = 25
PLAN = [('utmm', 0)] + [(k, s) for s in (0, 1, 2) for k in ('aria', 'rpng', 'rot', 'utmm') if (k, s) != ('utmm', 0)]


def gates(out, ref_dir):
    r, ref = base.read(out / 'render_result.json'), base.read(ref_dir / 'render_result.json')
    off = base.read(out / 'offline.json')
    g, gr = r['training']['generations'][-1], ref['training']['generations'][-1]
    n = lambda x: sum(len(s['uids']) for s in x['services'])
    counts = g['policy']['counts']
    kf, dense = set(g['policy']['keyframes']), set(g['policy']['admitted_dense'])
    spread = {}
    for name, pool in (('keyframe', kf), ('dense', dense)):
        c = [counts[str(u)] if str(u) in counts else counts.get(u, 0) for u in pool]
        spread[name] = (min(c), max(c))
    res = dict(final_renders=(n(g), n(gr)), dense_same=dense == set(gr['policy']['admitted_dense']),
               kf_same=kf == set(gr['policy']['keyframes']), spread=spread,
               gaussians=(r['gaussians'], ref['gaussians']), final_drained=off['final_drained'])
    # KF counts include window-free RR only; dense RR spread ≤ 1. KF views can also be dense-pool members? no: disjoint.
    ok = (res['final_renders'][0] == res['final_renders'][1] and res['dense_same'] and res['kf_same']
          and spread['dense'][1] - spread['dense'][0] <= 1 and spread['keyframe'][1] - spread['keyframe'][0] <= 1
          and 0.7 <= r['gaussians'] / ref['gaussians'] <= 1.3 and off['final_drained'])
    return ok, res


def main():
    p = argparse.ArgumentParser(); p.add_argument('--smoke', action='store_true'); p.add_argument('--extra', action='store_true')
    p.add_argument('--noscale-scenes', nargs='+', help='scale projection off (B_NO_SCALE_PROJ=1), seed 0, arm offline_noscale')
    a = p.parse_args()
    assert os.environ.get('ROGO_MACHINE_PROFILE'), 'machine profile required'
    sys.path.insert(0, str(base.SEL))
    from selected_mapping_check import load_lock, preflight, gpu_idle
    lock = load_lock()
    sys.path.insert(0, lock['benchmark_helpers'])
    import run_online_dense_training as trial
    from selected_recipe import recipe_environment, install_scene_adapter
    install_scene_adapter()
    base.OUT.mkdir(parents=True, exist_ok=True)
    if not (base.OUT / 'protocol.json').exists():
        base.write(base.OUT / 'protocol.json', dict(
            prereg=str(PREREG), prereg_sha256=base.sha(PREREG), main_head=base.head(base.MAIN),
            lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE), plan=PLAN,
            patch_sha256=base.sha(HERE / 'offline_patch.py'), machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                         '--format=csv,noheader'], text=True).strip()))
    plan = PLAN[:1] if a.smoke else PLAN
    worker, launcher_env, ref_of = HERE / 'offline_patch.py', {}, lambda key, seed: S.pinned_dir(key, 'ervs_k16', seed)
    if a.extra:   # Amendment 2: same patch through the legacy-IMU launcher and preflight used for the online runs
        import run_ervs_vs_iid_scenes as X
        base.OUT = OFFLINE_OUT   # importing X re-points base.OUT at the online scenes folder
        from selected_mapping_check import verify_files
        for scene, dataset in X.SCENES.items():
            lock['datasets'][scene] = dict(dataset=dataset, scene=scene, setup=str(X.SETUPS / dataset / scene / 'setup'))
        preflight = X.make_preflight(trial, verify_files, load_lock)
        plan = [(sc, 0) for sc in X.SCENES]
        worker, launcher_env = HERE / 'legacy_imu_launcher.py', dict(B_PATCH_WORKER=str(HERE / 'offline_patch.py'))
        ref_of = lambda key, seed: S.OUT / f'scenes/{key}/render25/ervs_k16_s{seed}'
    if a.noscale_scenes:
        plan = [(k, 0) for k in a.noscale_scenes]
        launcher_env = dict(launcher_env, B_NO_SCALE_PROJ='1')
    ctx = (lock, trial, preflight, gpu_idle, recipe_environment)
    rows = []
    for key, seed in plan:
        name = f'offline_noscale_s{seed}' if a.noscale_scenes else f'offline_s{seed}'
        ref_dir = ref_of(key, seed)
        ref = base.read(ref_dir / 'render_result.json')
        last_uid = [x['uid'] for x in ref['arrivals'] if not x.get('terminal')][-1]
        print('START', key, BUDGET, name, flush=True)
        try:
            env_extra = dict(B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'),
                             B_OFFLINE_REF=str(ref_dir / 'render_result.json'), B_OFFLINE_LAST_UID=str(last_uid), **launcher_env)
            row = base.run_one('offline', key, BUDGET, name, ['--seed', str(seed)], ctx,
                               worker=worker, env_extra=env_extra)
            out = Path(row['output'])
            ok, res = gates(out, ref_dir)
            row['offline_gates'] = res; row['seed'] = seed; row['reference'] = str(ref_dir)
            base.write(out.parent / f'{name}.row.json', row)
            print('GATES', key, name, 'PASS' if ok else 'FAIL', res, flush=True)
            if not ok:
                raise RuntimeError(f'offline gates failed: {res}')
        except Exception:
            base.write(base.OUT / 'failure.json', dict(key=key, arm=name, traceback=traceback.format_exc(),
                                                       time=time.time()))
            raise
        rows.append(row)
        base.summarize(rows)
        print('DONE', key, BUDGET, name, f"psnr={row['psnr']:.4f}", flush=True)
    print('OFFLINE_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
