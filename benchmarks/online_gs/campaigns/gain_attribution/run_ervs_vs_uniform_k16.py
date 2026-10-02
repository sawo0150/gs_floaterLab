#!/usr/bin/env python3
"""ERVS (K=16) vs uniform K=16 vs uniform with replacement on held-out scenes aria1253, table_06; budgets 15/25; seed 0
(PREREG: context/experiments/campaigns/06_gain_attribution/ervs_vs_uniform_k16/PREREG.md).

  ROGO_MACHINE_PROFILE=.../rtx5070ti_b_ablation.json PYTHONPATH=.../rtx5070ti_profile python run_ervs_vs_uniform_k16.py
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

base.OUT = base.ROOT / 'results/campaigns/gain_attribution/ervs_vs_uniform_k16/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/ervs_vs_uniform_k16/PREREG.md'
ARMS = [('ervs_k16', [], 'group_k_patch.py', dict(B_GROUP_K='16')),
        ('uniform_k16', ['--tau', '1e12'], 'group_k_patch.py', dict(B_GROUP_K='16')),
        ('uniform_iid', ['--tau', '1e12'], 'sampling_mode_patch.py', dict(B_WITH_REPLACEMENT='1'))]
SCENES, BUDGETS = ('aria', 'rpng'), (15, 25)


def gate(row, arm):
    out = Path(row['output'])
    if arm.endswith('k16'):
        g = base.read(out / 'group_k.json')
        if not (g['stats'].get('groups/keyframe') and g['stats'].get('groups/dense')):
            raise RuntimeError(f'group queue not used: {g}')
        row['group_k'] = g
    if arm.startswith('uniform'):
        tau = base.read(out / 'render_result.json')['training']['generations'][-1]['policy']['tau']
        if float(tau) < 1e11:
            raise RuntimeError(f'uniform tau not applied: {tau}')
    if arm == 'uniform_iid':
        st = base.read(out / 'sampling_mode.json')['stats']
        if not (st.get('repeat_in_batch/keyframe', 0) + st.get('repeat_in_batch/dense', 0)):
            raise RuntimeError(f'no repeated in-batch draws: {st}')
        row['sampling_mode'] = st
    base.write(out.parent / f'{arm}.row.json', row)
    return row


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
    if not (base.OUT / 'protocol.json').exists():
        base.write(base.OUT / 'protocol.json', dict(
            prereg=str(PREREG), prereg_sha256=base.sha(PREREG), main_head=base.head(base.MAIN),
            lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE), arms=ARMS, scenes=SCENES, budgets=BUDGETS,
            seed=0, patch_sha256={p: base.sha(HERE / p) for p in ('group_k_patch.py', 'sampling_mode_patch.py')},
            machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                         '--format=csv,noheader'], text=True).strip()))
    ctx = (lock, trial, preflight, gpu_idle, recipe_environment)
    rows = []
    for key in SCENES:
        for budget in BUDGETS:
            for arm, extra, patch, env in ARMS:
                print('START', key, budget, arm, flush=True)
                try:
                    env_extra = dict(env, B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'))
                    row = base.run_one('cmp', key, budget, arm, extra, ctx, worker=HERE / patch, env_extra=env_extra)
                    row = gate(row, arm)
                except Exception:
                    base.write(base.OUT / 'failure.json', dict(key=key, budget=budget, arm=arm,
                                                               traceback=traceback.format_exc(), time=time.time()))
                    raise
                rows.append(row)
                base.summarize(rows)
                print('DONE', key, budget, arm, f"psnr={row['psnr']:.4f}", f"map_s={row['mapping_seconds']:.1f}",
                      flush=True)
    print('ABLATION_PASS_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
