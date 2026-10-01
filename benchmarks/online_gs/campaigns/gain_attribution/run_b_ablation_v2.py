#!/usr/bin/env python3
"""ERVS vs RR at budgets 15/25 on the four B scenes, seed 0
(PREREG: context/experiments/campaigns/06_gain_attribution/b_ablation_v2/PREREG.md).

Reuses run_b_ablation_chain's audited run_one/summarize with a different plan and output root. Pilot runs with an
identical configuration (seed 0, budget 15, R4 = ervs, R4rr = rr on rot/rpng) are reused by reference.

  ROGO_MACHINE_PROFILE=.../rtx5070ti_b_ablation.json PYTHONPATH=.../rtx5070ti_profile python run_b_ablation_v2.py
"""
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_b_ablation_chain as base  # noqa: E402

PILOT = base.OUT
base.OUT = base.ROOT / 'results/campaigns/gain_attribution/b_ablation_v2/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/b_ablation_v2/PREREG.md'
ARMS = [('ervs', []), ('rr', ['--selector', 'rr'])]
PLAN = [('ervs', s, b, a, x) for s in ('rot', 'rpng', 'aria', 'utmm') for b in (15, 25) for a, x in ARMS]
REUSE = {('rot', 15, 'ervs'): ('rot', 'R4'), ('rot', 15, 'rr'): ('rot', 'R4rr'),
         ('rpng', 15, 'ervs'): ('rpng', 'R4'), ('rpng', 15, 'rr'): ('rpng', 'R4rr')}


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
            lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE), plan=PLAN, seed=0,
            reuse={f'{k[0]}/{k[1]}/{k[2]}': str(PILOT / 'chain' / v[0] / f'render{k[1]}' / f'{v[1]}.row.json')
                   for k, v in REUSE.items()},
            machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            machine_profile_sha256=base.sha(os.environ['ROGO_MACHINE_PROFILE']),
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                         '--format=csv,noheader'], text=True).strip()))
    ctx = (lock, trial, preflight, gpu_idle, recipe_environment)
    rows = []
    for phase, key, budget, arm, extra in PLAN:
        src = REUSE.get((key, budget, arm))
        if src:
            row = dict(base.read(PILOT / 'chain' / src[0] / f'render{budget}' / f'{src[1]}.row.json'))
            row.update(phase=phase, arm=arm, reused_from=f'b_ablation_chain/{src[0]}/render{budget}/{src[1]}')
        else:
            print('START', phase, key, budget, arm, flush=True)
            try:
                row = base.run_one(phase, key, budget, arm, extra, ctx)
            except Exception:
                base.write(base.OUT / 'failure.json', dict(key=key, budget=budget, arm=arm,
                                                           traceback=traceback.format_exc(), time=time.time()))
                raise
        rows.append(row)
        base.summarize(rows)
        print('DONE', phase, key, budget, arm, f"psnr={row['psnr']:.4f}",
              f"recent={row['recent_third']['psnr']:.4f}", 'reused' if src else f"map_s={row['mapping_seconds']:.1f}",
              flush=True)
    print('ABLATION_PASS_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
