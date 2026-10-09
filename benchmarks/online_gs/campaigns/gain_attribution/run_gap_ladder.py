#!/usr/bin/env python3
"""Online → offline gap ladder (PREREG: context/experiments/campaigns/06_gain_attribution/gap_ladder/PREREG.md).

  python run_gap_ladder.py --scenes aria rot utmm rpng ego-drive Retail_Street --arms seq cnt hyb85
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

OUT = base.ROOT / 'results/campaigns/gain_attribution/gap_ladder/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/gap_ladder/PREREG.md'
PINNED = ('aria', 'rpng', 'rot', 'utmm')
EXTRA_LOCAL = S.R / 'extra_local_5070ti/v1'
ARMS = {'seq': (dict(B_LADDER_MODE='sequence'), []), 'cnt': (dict(B_LADDER_MODE='counts'), []),
        'hyb85': (dict(B_LADDER_MODE='hybrid', B_HYBRID_FRAC='0.85', B_GROUP_K='16'), []),
        'seq_noscale': (dict(B_LADDER_MODE='sequence', B_NO_SCALE_PROJ='1'), []),
        'cnt_noscale': (dict(B_LADDER_MODE='counts', B_NO_SCALE_PROJ='1'), []),
        'hyb85_selop_noscale': (dict(B_LADDER_MODE='hybrid', B_HYBRID_FRAC='0.85', B_GROUP_K='16', B_NO_SCALE_PROJ='1', B_COVERED_OPACITY='0.02'), []),
        'seq_cap05': (dict(B_LADDER_MODE='sequence', B_SCALE_CAP='0.5', SEQ_FROM_VALIDATION='Bp_iid_cap05'), []),
        'cnt_cap05': (dict(B_LADDER_MODE='counts', B_SCALE_CAP='0.5', SEQ_FROM_VALIDATION='Bp_iid_cap05'), []),
        'hyb85_selop_cap05': (dict(B_LADDER_MODE='hybrid', B_HYBRID_FRAC='0.85', B_GROUP_K='16', B_SCALE_CAP='0.5', B_COVERED_OPACITY='0.02'), [])}


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
            recipe=base.read(base.RECIPE), patch_sha256=base.sha(HERE / 'offline_ladder_patch.py'),
            machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version', '--format=csv,noheader'], text=True).strip()))
    pf_extra = X.make_preflight(trial, verify_files, load_lock)
    pf_local = C.make_preflight(trial, verify_files, load_lock)
    rows = []
    for key in a.scenes:
        rd = ref_dir(key, 'uniform_iid')
        ref = base.read(rd / 'render_result.json')
        last_uid = [x['uid'] for x in ref['arrivals'] if not x.get('terminal')][-1]
        for arm in a.arms:
            env, extra = ARMS[arm]
            name = f'{arm}_s0'
            env = dict(env, B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'),
                       B_OFFLINE_REF=str(rd / 'render_result.json'), B_SEQ_REF=str(rd / 'render_result.json'),
                       B_OFFLINE_LAST_UID=str(last_uid))
            if env.get('SEQ_FROM_VALIDATION'):     # replay the sequence of the matching online run (same cap)
                env['B_SEQ_REF'] = str(base.ROOT / 'results/campaigns/gain_attribution/validation/v1/validation' / key /
                                       'render25' / f"{env.pop('SEQ_FROM_VALIDATION')}_s0" / 'render_result.json')
            if key in PINNED:
                pf, worker = preflight, HERE / 'offline_ladder_patch.py'
            elif key in X.SCENES:
                pf, worker = pf_extra, HERE / 'legacy_imu_launcher.py'; env['B_PATCH_WORKER'] = str(HERE / 'offline_ladder_patch.py')
            else:
                pf, worker = pf_local, HERE / 'extra_scene_launcher.py'
                sp = trial.BASE.sequence_paths(C.SCENES[key]['dataset'], key)
                env.update(B_PATCH_WORKER=str(HERE / 'offline_ladder_patch.py'), B_POOL_CAP='700', B_EXTRA_SCENES=json.dumps(
                    {key: dict(dataset=C.SCENES[key]['dataset'], **{k: str(v) for k, v in sp.items()})}))
            print('START', key, 25, name, flush=True)
            C.wait_gpu_idle()
            try:
                base.OUT = OUT
                row = base.run_one('ladder', key, 25, name, [*extra, '--seed', '0'], (lock, trial, pf, lambda: None, recipe_environment),
                                   worker=worker, env_extra=env)
                out = Path(row['output'])
                L = base.read(out / 'ladder.json')
                row.update(ladder=L, gate_ok=bool(L['final_drained']))
                base.write(out.parent / f'{name}.row.json', row)
            except Exception:
                base.write(OUT / 'failure.json', dict(key=key, arm=name, traceback=traceback.format_exc(), time=time.time()))
                print('FAILED', key, name, flush=True)
                continue
            rows.append(row); base.summarize(rows)
            print('DONE', key, 25, name, f"psnr={row['psnr']:.4f}", L['stats'], flush=True)
    print('LADDER_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
