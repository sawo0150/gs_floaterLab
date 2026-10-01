#!/usr/bin/env python3
"""Depth-off diagnostic: per-pool ERVS/RR 2x2 with keyframe depth weight 0, four B scenes, budgets 15/25, seed 0
(PREREG: context/experiments/campaigns/06_gain_attribution/ervs_depth_off/PREREG.md).

  ROGO_MACHINE_PROFILE=.../rtx5070ti_b_ablation.json PYTHONPATH=.../rtx5070ti_profile python run_ervs_depth_off.py
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

base.OUT = base.ROOT / 'results/campaigns/gain_attribution/ervs_depth_off/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/ervs_depth_off/PREREG.md'
ARMS = [('D0-EE', [], None), ('D0-RR', ['--selector', 'rr'], None),
        ('D0-ER', ['--selector', 'rr'], 'dense'), ('D0-RE', ['--selector', 'rr'], 'keyframe')]
SCENES, BUDGETS = ('rot', 'rpng', 'aria', 'utmm'), (15, 25)


def gate(row, rr_role):
    out = Path(row['output'])
    cfg = json.loads((out / 'geometry_runtime.json').read_text())['config']
    if float(cfg['w_plain']) != 0.0:
        raise RuntimeError(f'depth weight not zero: {cfg}')
    if rr_role is None:
        return None
    draws = json.loads((out / 'per_pool_selector.json').read_text())['draws']
    ervs_role = 'keyframe' if rr_role == 'dense' else 'dense'
    if (draws.get(f'ervs/{rr_role}', 0) or draws.get(f'rr/{ervs_role}', 0)
            or not draws.get(f'rr/{rr_role}') or not draws.get(f'ervs/{ervs_role}')):
        raise RuntimeError(f'per-pool draw gate failed: {draws}')
    return draws


def main():
    assert os.environ.get('ROGO_MACHINE_PROFILE'), 'machine profile required'
    sys.path.insert(0, str(base.SEL))
    from selected_mapping_check import load_lock, preflight, gpu_idle
    lock = load_lock()
    sys.path.insert(0, lock['benchmark_helpers'])
    import run_online_dense_training as trial
    from selected_recipe import recipe_environment, install_scene_adapter
    install_scene_adapter()
    base.OUT.mkdir(parents=True, exist_ok=True)
    patch = HERE / 'per_pool_selector.py'
    if not (base.OUT / 'protocol.json').exists():
        base.write(base.OUT / 'protocol.json', dict(
            prereg=str(PREREG), prereg_sha256=base.sha(PREREG), main_head=base.head(base.MAIN),
            lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE), arms=ARMS, scenes=SCENES,
            budgets=BUDGETS, seed=0, kf_depth_weight=0.0, patch=str(patch), patch_sha256=base.sha(patch),
            machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            machine_profile_sha256=base.sha(os.environ['ROGO_MACHINE_PROFILE']),
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                         '--format=csv,noheader'], text=True).strip()))
    ctx = (lock, trial, preflight, gpu_idle, recipe_environment)
    rows = []
    for key in SCENES:
        for budget in BUDGETS:
            for arm, extra, rr_role in ARMS:
                env_extra = dict(B_KF_DEPTH_W='0', B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'))
                if rr_role:
                    env_extra['B_RR_ROLES'] = rr_role
                print('START', key, budget, arm, flush=True)
                try:
                    row = base.run_one('d0', key, budget, arm, extra, ctx, worker=patch, env_extra=env_extra)
                    draws = gate(row, rr_role)
                    if draws:
                        row['per_pool_draws'] = draws
                    row['kf_depth_weight'] = 0.0
                    base.write(Path(row['output']).parent / f'{arm}.row.json', row)
                except Exception:
                    base.write(base.OUT / 'failure.json', dict(key=key, budget=budget, arm=arm,
                                                               traceback=traceback.format_exc(), time=time.time()))
                    raise
                rows.append(row)
                base.summarize(rows)
                print('DONE', key, budget, arm, f"psnr={row['psnr']:.4f}",
                      f"recent={row['recent_third']['psnr']:.4f}", f"map_s={row['mapping_seconds']:.1f}", flush=True)
    print('ABLATION_PASS_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
