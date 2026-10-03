#!/usr/bin/env python3
"""Training-signal study on the four B scenes, budget 25, seed 0 (PREREG: .../ervs_train_signal/PREREG.md).

  python run_ervs_train_signal.py --stage 1   # logging only: uniform_iid, ervs_tau4
  python run_ervs_train_signal.py --stage 2   # signal samplers
"""
import argparse
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_b_ablation_chain as base  # noqa: E402

base.OUT = base.ROOT / 'results/campaigns/gain_attribution/ervs_train_signal/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/ervs_train_signal/PREREG.md'
SCENES, BUDGET = ('aria', 'rpng', 'rot', 'utmm'), 25
STAGE1 = {'uniform_iid_log': (['--tau', '1e12'], 'sampling_mode_patch.py', dict(B_WITH_REPLACEMENT='1')),
          'ervs_tau4_log': ([], 'group_k_patch.py', dict(B_GROUP_K='16'))}
MODES = ('forget_stale', 'progress_stale', 'loss_stale', 'catchup', 'age_norm')


def main():
    p = argparse.ArgumentParser(); p.add_argument('--stage', type=int, choices=(1, 2), required=True)
    a = p.parse_args()
    assert os.environ.get('ROGO_MACHINE_PROFILE'), 'machine profile required'
    sys.path.insert(0, str(base.SEL))
    from selected_mapping_check import load_lock, preflight, gpu_idle
    lock = load_lock()
    sys.path.insert(0, lock['benchmark_helpers'])
    import run_online_dense_training as trial
    from selected_recipe import recipe_environment, install_scene_adapter
    install_scene_adapter()
    base.OUT.mkdir(parents=True, exist_ok=True)
    proto = base.OUT / f'protocol_stage{a.stage}.json'
    if not proto.exists():
        base.write(proto, dict(prereg=str(PREREG), prereg_sha256=base.sha(PREREG), main_head=base.head(base.MAIN),
                               lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE), stage=a.stage,
                               patch_sha256={x: base.sha(HERE / x) for x in
                                             ('train_signal.py', 'group_k_patch.py', 'sampling_mode_patch.py')},
                               machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
                               gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                                            '--format=csv,noheader'], text=True).strip()))
    ctx = (lock, trial, preflight, gpu_idle, recipe_environment)
    sel_worker = str(base.SEL / 'run_selected_worker.py')
    if a.stage == 1:
        plan = [(k, arm, *STAGE1[arm]) for arm in STAGE1 for k in SCENES]
    else:
        plan = [(k, f'sig_{m}', [], 'group_k_patch.py', dict(B_SIGNAL_MODE=m)) for m in MODES for k in SCENES]
    rows = []
    for key, arm, extra, patch, env in plan:
        print('START', key, BUDGET, arm, flush=True)
        try:
            env_extra = dict(env, B_SELECTED_WORKER=sel_worker, B_PATCH_WORKER=str(HERE / patch))
            row = base.run_one(f'stage{a.stage}', key, BUDGET, arm, extra, ctx, worker=HERE / 'train_signal.py',
                               env_extra=env_extra)
            out = Path(row['output'])
            sig = base.read(out / 'train_signal.json')
            assert len(sig['rows']) == row['training_renders'], (len(sig['rows']), row['training_renders'])
            if a.stage == 2:
                s = base.read(out / 'signal_sampler.json')['stats']
                assert s.get('groups/keyframe') and s.get('groups/dense'), s
                row['signal_sampler'] = s
            base.write(out.parent / f'{arm}.row.json', row)
        except Exception:
            base.write(base.OUT / f'failure_stage{a.stage}.json', dict(key=key, arm=arm,
                       traceback=traceback.format_exc(), time=time.time()))
            raise
        rows.append(row)
        base.summarize(rows)
        print('DONE', key, BUDGET, arm, f"psnr={row['psnr']:.4f}", flush=True)
    print('STAGE_COMPLETE', a.stage, len(rows), flush=True)


if __name__ == '__main__':
    main()
