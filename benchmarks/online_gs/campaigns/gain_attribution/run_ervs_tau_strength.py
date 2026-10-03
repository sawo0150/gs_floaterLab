#!/usr/bin/env python3
"""ERVS K16 balancing strength τ ∈ {1, 0.25} on the four B scenes, budget 25, seed 0
(PREREG: context/experiments/campaigns/06_gain_attribution/ervs_tau_strength/PREREG.md).
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

base.OUT = base.ROOT / 'results/campaigns/gain_attribution/ervs_tau_strength/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/ervs_tau_strength/PREREG.md'
TAUS = ('1', '0.25')
SCENES, BUDGET = ('aria', 'rpng', 'rot', 'utmm'), 25


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
            lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE), taus=TAUS, scenes=SCENES, budget=BUDGET,
            seed=0, patch_sha256=base.sha(HERE / 'group_k_patch.py'), machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                         '--format=csv,noheader'], text=True).strip()))
    ctx = (lock, trial, preflight, gpu_idle, recipe_environment)
    rows = []
    for tau in TAUS:
        for key in SCENES:
            arm = f'ervs_tau{tau}'
            print('START', key, BUDGET, arm, flush=True)
            try:
                env_extra = dict(B_GROUP_K='16', B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'))
                row = base.run_one('tau', key, BUDGET, arm, ['--tau', tau], ctx, worker=HERE / 'group_k_patch.py',
                                   env_extra=env_extra)
                out = Path(row['output'])
                rec = base.read(out / 'render_result.json')['training']['generations'][-1]['policy']['tau']
                assert abs(float(rec) - float(tau)) < 1e-9, f'tau not applied: {rec}'
                g = base.read(out / 'group_k.json')
                assert g['stats'].get('groups/keyframe') and g['stats'].get('groups/dense'), g
                row['group_k'] = g; row['tau'] = float(tau)
                base.write(out.parent / f'{arm}.row.json', row)
            except Exception:
                base.write(base.OUT / 'failure.json', dict(key=key, arm=arm, traceback=traceback.format_exc(),
                                                           time=time.time()))
                raise
            rows.append(row)
            base.summarize(rows)
            print('DONE', key, BUDGET, arm, f"psnr={row['psnr']:.4f}", flush=True)
    print('ABLATION_PASS_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
