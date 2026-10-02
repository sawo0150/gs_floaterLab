#!/usr/bin/env python3
"""Uniform-sampling baseline (ERVS Gibbs energy -> 0 via --tau 1e12) on B, four scenes, budgets 5/10/15/25, seed 0
(PREREG: context/experiments/campaigns/06_gain_attribution/ervs_vs_uniform/PREREG.md).

  ROGO_MACHINE_PROFILE=.../rtx5070ti_b_ablation.json PYTHONPATH=.../rtx5070ti_profile python run_ervs_vs_uniform.py
"""
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_b_ablation_chain as base  # noqa: E402

PILOT = base.OUT
base.OUT = base.ROOT / 'results/campaigns/gain_attribution/ervs_vs_uniform/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/ervs_vs_uniform/PREREG.md'
SCENES, BUDGETS = ('rot', 'rpng', 'aria', 'utmm'), (5, 10, 15, 25)
UNIFORM = ['--tau', '1e12']


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
            lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE), uniform_overrides=UNIFORM,
            scenes=SCENES, budgets=BUDGETS, seed=0, machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                         '--format=csv,noheader'], text=True).strip()))
    ctx = (lock, trial, preflight, gpu_idle, recipe_environment)
    rows = []
    for key in SCENES:
        for budget in BUDGETS:
            print('START', key, budget, 'uniform', flush=True)
            try:
                row = base.run_one('uniform', key, budget, 'uniform', UNIFORM, ctx)
                rep = base.read(Path(row['output']) / 'render_result.json')
                tau = rep['training']['generations'][-1]['policy']['tau']
                if float(tau) < 1e11:
                    raise RuntimeError(f'uniform override not applied: tau={tau}')
            except Exception:
                base.write(base.OUT / 'failure.json', dict(key=key, budget=budget,
                                                           traceback=traceback.format_exc(), time=time.time()))
                raise
            rows.append(row)
            base.summarize(rows)
            print('DONE', key, budget, 'uniform', f"psnr={row['psnr']:.4f}", f"map_s={row['mapping_seconds']:.1f}",
                  flush=True)
    print('ABLATION_PASS_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
