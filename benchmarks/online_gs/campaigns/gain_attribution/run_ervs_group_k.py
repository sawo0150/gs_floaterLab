#!/usr/bin/env python3
"""ERVS group size K on B: K16/K32/K64 (persistent per-pool group queue), rot and square-1, budgets 15/25, seed 0
(PREREG: context/experiments/campaigns/06_gain_attribution/ervs_group_k/PREREG.md).

  ROGO_MACHINE_PROFILE=.../rtx5070ti_b_ablation.json PYTHONPATH=.../rtx5070ti_profile python run_ervs_group_k.py
"""
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_b_ablation_chain as base  # noqa: E402

base.OUT = base.ROOT / 'results/campaigns/gain_attribution/ervs_group_k/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/ervs_group_k/PREREG.md'
KS = (16, 32, 64)
SCENES, BUDGETS = ('rot', 'utmm'), (15, 25)


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
    patch = HERE / 'group_k_patch.py'
    if not (base.OUT / 'protocol.json').exists():
        base.write(base.OUT / 'protocol.json', dict(
            prereg=str(PREREG), prereg_sha256=base.sha(PREREG), main_head=base.head(base.MAIN),
            lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE), ks=KS, scenes=SCENES, budgets=BUDGETS,
            seed=0, patch_sha256=base.sha(patch), machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                         '--format=csv,noheader'], text=True).strip()))
    ctx = (lock, trial, preflight, gpu_idle, recipe_environment)
    rows = []
    for key in SCENES:
        for budget in BUDGETS:
            for k in KS:
                arm = f'K{k}'
                print('START', key, budget, arm, flush=True)
                try:
                    env_extra = dict(B_GROUP_K=str(k), B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'))
                    row = base.run_one('groupk', key, budget, arm, [], ctx, worker=patch, env_extra=env_extra)
                    g = base.read(Path(row['output']) / 'group_k.json')
                    if not (g['stats'].get('groups/keyframe') and g['stats'].get('groups/dense')):
                        raise RuntimeError(f'group queue not used: {g}')
                    row['group_k'] = g
                    base.write(Path(row['output']).parent / f'{arm}.row.json', row)
                except Exception:
                    base.write(base.OUT / 'failure.json', dict(key=key, budget=budget, arm=arm,
                                                               traceback=traceback.format_exc(), time=time.time()))
                    raise
                rows.append(row)
                base.summarize(rows)
                print('DONE', key, budget, arm, f"psnr={row['psnr']:.4f}", f"groups={g['stats']}", flush=True)
    print('ABLATION_PASS_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
