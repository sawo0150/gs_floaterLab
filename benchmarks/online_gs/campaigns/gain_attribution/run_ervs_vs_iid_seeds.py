#!/usr/bin/env python3
"""ERVS K16 vs uniform with replacement, seeds 1–2 (+ square-1 seed-0 iid) on the four B scenes, budgets 15/25
(PREREG: context/experiments/campaigns/06_gain_attribution/ervs_vs_iid_seeds/PREREG.md).
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

base.OUT = base.ROOT / 'results/campaigns/gain_attribution/ervs_vs_iid_seeds/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/ervs_vs_iid_seeds/PREREG.md'
ARMS = {'ervs_k16': ([], 'group_k_patch.py', dict(B_GROUP_K='16')),
        'uniform_iid': (['--tau', '1e12'], 'sampling_mode_patch.py', dict(B_WITH_REPLACEMENT='1'))}
PLAN = ([('utmm', b, 'uniform_iid', 0) for b in (15, 25)]
        + [(k, b, a, s) for s in (1, 2) for k in ('aria', 'rpng', 'rot', 'utmm') for b in (15, 25) for a in ARMS])


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
            lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE), plan=PLAN,
            patch_sha256={p: base.sha(HERE / p) for p in ('group_k_patch.py', 'sampling_mode_patch.py')},
            machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                         '--format=csv,noheader'], text=True).strip()))
    ctx = (lock, trial, preflight, gpu_idle, recipe_environment)
    rows = []
    for key, budget, arm, seed in PLAN:
        name = f'{arm}_s{seed}'
        extra, patch, env = ARMS[arm]
        print('START', key, budget, name, flush=True)
        try:
            env_extra = dict(env, B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'))
            row = base.run_one('seeds', key, budget, name, [*extra, '--seed', str(seed)], ctx,
                               worker=HERE / patch, env_extra=env_extra)
            argv = base.read(Path(row['output']).parent / f'{name}.command.json')['cmd']
            last = len(argv) - 1 - argv[::-1].index('--seed')
            assert argv[last + 1] == str(seed), 'seed not applied'
            out = Path(row['output'])
            if arm == 'ervs_k16':
                g = base.read(out / 'group_k.json')
                assert g['stats'].get('groups/keyframe') and g['stats'].get('groups/dense'), g
                row['group_k'] = g
            else:
                tau = base.read(out / 'render_result.json')['training']['generations'][-1]['policy']['tau']
                assert float(tau) >= 1e11, tau
                st = base.read(out / 'sampling_mode.json')['stats']
                assert st.get('repeat_in_batch/keyframe', 0) + st.get('repeat_in_batch/dense', 0), st
                row['sampling_mode'] = st
            row['seed'] = seed; row['base_arm'] = arm
            base.write(Path(row['output']).parent / f'{name}.row.json', row)
        except Exception:
            base.write(base.OUT / 'failure.json', dict(key=key, budget=budget, arm=name,
                                                       traceback=traceback.format_exc(), time=time.time()))
            raise
        rows.append(row)
        base.summarize(rows)
        print('DONE', key, budget, name, f"psnr={row['psnr']:.4f}", flush=True)
    print('ABLATION_PASS_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
