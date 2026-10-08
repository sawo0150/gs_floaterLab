#!/usr/bin/env python3
"""Event probe (PREREG: context/experiments/campaigns/06_gain_attribution/track/PREREG.md, Amendment 1).

  python run_event_probe.py --scenes aria utmm
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

OUT = base.ROOT / 'results/campaigns/gain_attribution/event_probe/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/track/PREREG.md'
PINNED = ('aria', 'rpng', 'rot', 'utmm')
EXTRA_LOCAL = S.R / 'extra_local_5070ti/v1'
ARMS = {'event_noscale_iid': (dict(B_WITH_REPLACEMENT='1', B_NO_SCALE_PROJ='1'), ['--tau', '1e12']),
        'event_lowop_noscale_iid': (dict(B_WITH_REPLACEMENT='1', B_NO_SCALE_PROJ='1', B_BIRTH_OPACITY='0.12'), ['--tau', '1e12']),
        'event_selop002_noscale_iid': (dict(B_WITH_REPLACEMENT='1', B_NO_SCALE_PROJ='1', B_COVERED_OPACITY='0.02'), ['--tau', '1e12']),
        'event_selop002_noscale_ervs': (dict(B_GROUP_K='16', B_NO_SCALE_PROJ='1', B_COVERED_OPACITY='0.02'), []),
        'event_selop002_noscale_iid_lag6': (dict(B_WITH_REPLACEMENT='1', B_NO_SCALE_PROJ='1', B_COVERED_OPACITY='0.02', B_WINDOW_LAG='6'), ['--tau', '1e12']),
        'event_selop002_noscale_ervs_t05': (dict(B_GROUP_K='16', B_NO_SCALE_PROJ='1', B_COVERED_OPACITY='0.02'), ['--tau', '0.5']),
        'event_selop002_noscale_ervs_t01': (dict(B_GROUP_K='16', B_NO_SCALE_PROJ='1', B_COVERED_OPACITY='0.02'), ['--tau', '0.1']),
        'event_noscale_iid_rowadam': (dict(B_WITH_REPLACEMENT='1', B_NO_SCALE_PROJ='1', B_ROW_ADAM='1'), ['--tau', '1e12']),
        'event_selop002_noscale_iid_rowadam': (dict(B_WITH_REPLACEMENT='1', B_NO_SCALE_PROJ='1', B_COVERED_OPACITY='0.02', B_ROW_ADAM='1'), ['--tau', '1e12']),
        'event_selop002_noscale_ervs_nowin70': (dict(B_GROUP_K='16', B_NO_SCALE_PROJ='1', B_COVERED_OPACITY='0.02', B_WINDOW_OFF_FRAC='0.7'), []),
        'event_selop002_noscale_ervs_cu60': (dict(B_GROUP_K='16', B_NO_SCALE_PROJ='1', B_COVERED_OPACITY='0.02', B_CATCHUP_FRAC='0.6', B_CATCHUP_SLOTS='3'), [])}
PATCH = 'event_probe_patch.py'


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
            env = dict(env, B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'))
            if 'B_WINDOW_OFF_FRAC' in env:         # stream fraction -> frame uid (final-generation span of the uniform_iid reference)
                import build_ervs_scenes_page as S
                rr = base.read(S.pinned_dir(key, 'uniform_iid', 0) / 'render_result.json')
                lr = rr['training']['loss_routes']; g = max(x['generation'] for x in lr)
                first = min(x['uid'] for x in lr if x['generation'] == g)
                last = [x['uid'] for x in rr['arrivals'] if not x.get('terminal')][-1]
                env['B_WINDOW_OFF_FROM_UID'] = str(int(first + float(env['B_WINDOW_OFF_FRAC']) * (last - first)))
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
                row = base.run_one('event_probe', key, 25, name, [*extra, '--seed', '0'], (lock, trial, pf, lambda: None, recipe_environment),
                                   worker=worker, env_extra=env)
                out = Path(row['output'])
                E = base.read(out / 'event_probe.json')['events']
                from collections import Counter
                L = dict(kinds=dict(Counter(e['kind'] for e in E)), errors=sum('error' in e for e in E))
                L['optimizer'] = base.read(out / 'event_probe.json').get('optimizer')
                row.update(event_probe=L, gate_ok=len(E) > 0 and L['errors'] == 0 and (env.get('B_ROW_ADAM') != '1' or L['optimizer'] == 'RowAdam'))
                base.write(out.parent / f'{name}.row.json', row)
            except Exception:
                base.write(OUT / 'failure.json', dict(key=key, arm=name, traceback=traceback.format_exc(), time=time.time()))
                print('FAILED', key, name, flush=True)
                continue
            rows.append(row); base.summarize(rows)
            print('DONE', key, 25, name, f"psnr={row['psnr']:.4f}", L, flush=True)
    print('EVENT_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
