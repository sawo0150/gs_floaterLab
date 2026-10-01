#!/usr/bin/env python3
"""ERVS per pool 2x2 on the four B scenes, budgets 15/25, seed 0
(PREREG: context/experiments/campaigns/06_gain_attribution/ervs_per_pool/PREREG.md).

EE/RR are reused from b_ablation_v2 (or the pilot for rot/rpng at 15). ER/RE run the official B worker through
per_pool_selector.py with --selector rr and B_RR_ROLES.

  ROGO_MACHINE_PROFILE=.../rtx5070ti_b_ablation.json PYTHONPATH=.../rtx5070ti_profile python run_ervs_per_pool.py
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

PILOT = base.OUT
V2 = base.ROOT / 'results/campaigns/gain_attribution/b_ablation_v2/v1'
base.OUT = base.ROOT / 'results/campaigns/gain_attribution/ervs_per_pool/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/ervs_per_pool/PREREG.md'
NEW = [('ER', 'dense'), ('RE', 'keyframe')]
SCENES, BUDGETS = ('rot', 'rpng', 'aria', 'utmm'), (15, 25)


def reference(key, budget, ref, pilot_arm):
    src = V2 / 'ervs' / key / f'render{budget}' / f'{ref}.row.json'
    if not src.exists():
        src = PILOT / 'chain' / key / f'render{budget}' / f'{pilot_arm}.row.json'
    return src


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
            lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE), new_arms=NEW, scenes=SCENES,
            budgets=BUDGETS, seed=0, patch=str(patch), patch_sha256=base.sha(patch),
            machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            machine_profile_sha256=base.sha(os.environ['ROGO_MACHINE_PROFILE']),
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                         '--format=csv,noheader'], text=True).strip()))
    ctx = (lock, trial, preflight, gpu_idle, recipe_environment)
    rows = []
    for key in SCENES:
        for budget in BUDGETS:
            for arm, ref, pilot_arm in (('EE', 'ervs', 'R4'), ('RR', 'rr', 'R4rr')):
                src = reference(key, budget, ref, pilot_arm)
                row = dict(base.read(src))
                row.update(phase='pool', arm=arm, reused_from=str(src.relative_to(base.ROOT / 'results/campaigns')))
                rows.append(row)
            for arm, rr_role in NEW:
                print('START', key, budget, arm, flush=True)
                env_extra = dict(B_RR_ROLES=rr_role, B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'))
                try:
                    row = base.run_one('pool', key, budget, arm, ['--selector', 'rr'], ctx,
                                       worker=patch, env_extra=env_extra)
                    out = Path(row['output'])
                    draws = json.loads((out / 'per_pool_selector.json').read_text())['draws']
                    ervs_role = 'keyframe' if rr_role == 'dense' else 'dense'
                    wrong = draws.get(f'ervs/{rr_role}', 0) + draws.get(f'rr/{ervs_role}', 0)
                    if wrong or not draws.get(f'rr/{rr_role}') or not draws.get(f'ervs/{ervs_role}'):
                        raise RuntimeError(f'per-pool draw gate failed: {draws}')
                    row['per_pool_draws'] = draws
                    base.write(out.parent / f'{arm}.row.json', row)
                except Exception:
                    base.write(base.OUT / 'failure.json', dict(key=key, budget=budget, arm=arm,
                                                               traceback=traceback.format_exc(), time=time.time()))
                    raise
                rows.append(row)
                base.summarize(rows)
                print('DONE', key, budget, arm, f"psnr={row['psnr']:.4f}",
                      f"recent={row['recent_third']['psnr']:.4f}", f"draws={draws}", flush=True)
    base.summarize(rows)
    print('ABLATION_PASS_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
