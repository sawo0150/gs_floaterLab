#!/usr/bin/env python3
"""Rule A: ERVS K16 + one stale-first dense slot (PREREG: context/experiments/campaigns/06_gain_attribution/stale_slot/PREREG.md).

  python run_stale_slot.py
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
import run_ervs_vs_iid_scenes as X  # noqa: E402

OUT = base.ROOT / 'results/campaigns/gain_attribution/stale_slot/v1'
base.OUT = OUT   # set after importing X (X re-points base.OUT)
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/stale_slot/PREREG.md'
PLAN = ['utmm', 'table_03', 'table_07', 'ego-drive', 'fast-straight', 'square-2', 'slow-straight-1', 'slow-straight-2']
NAME = 'ervs_stale1_s0'


def main():
    assert os.environ.get('ROGO_MACHINE_PROFILE'), 'machine profile required'
    sys.path.insert(0, str(base.SEL))
    from selected_mapping_check import load_lock, preflight, gpu_idle, verify_files
    lock = load_lock()
    sys.path.insert(0, lock['benchmark_helpers'])
    import run_online_dense_training as trial
    from selected_recipe import recipe_environment, install_scene_adapter
    install_scene_adapter()
    for scene, dataset in X.SCENES.items():
        lock['datasets'][scene] = dict(dataset=dataset, scene=scene, setup=str(X.SETUPS / dataset / scene / 'setup'))
    OUT.mkdir(parents=True, exist_ok=True)
    if not (OUT / 'protocol.json').exists():
        base.write(OUT / 'protocol.json', dict(
            prereg=str(PREREG), prereg_sha256=base.sha(PREREG), main_head=base.head(base.MAIN),
            lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE), plan=PLAN,
            patch_sha256={p: base.sha(HERE / p) for p in ('stale_slot_patch.py', 'group_k_patch.py')},
            machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                         '--format=csv,noheader'], text=True).strip()))
    extra_pf = X.make_preflight(trial, verify_files, load_lock)
    rows = []
    for key in PLAN:
        pinned = key == 'utmm'
        ctx = (lock, trial, preflight if pinned else extra_pf, gpu_idle, recipe_environment)
        env = dict(B_GROUP_K='16', B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'))
        worker = HERE / 'stale_slot_patch.py'
        if not pinned:
            env['B_PATCH_WORKER'] = str(worker); worker = HERE / 'legacy_imu_launcher.py'
        print('START', key, 25, NAME, flush=True)
        try:
            base.OUT = OUT
            row = base.run_one('rule_a', key, 25, NAME, ['--seed', '0'], ctx, worker=worker, env_extra=env)
            out = Path(row['output'])
            st = base.read(out / 'stale_slot.json'); g = base.read(out / 'group_k.json')
            assert st['stats'].get('replaced', 0) > 0, st
            assert g['stats'].get('groups/keyframe') and g['stats'].get('groups/dense'), g
            row['stale_slot'] = st; row['group_k'] = g
            base.write(out.parent / f'{NAME}.row.json', row)
        except Exception:
            base.write(OUT / 'failure.json', dict(key=key, traceback=traceback.format_exc(), time=time.time()))
            raise
        rows.append(row); base.summarize(rows)
        print('DONE', key, 25, NAME, f"psnr={row['psnr']:.4f}", 'replaced', st['stats'].get('replaced'),
              'mean_idle', st['mean_idle_of_replacements'], flush=True)
    print('RULE_A_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
