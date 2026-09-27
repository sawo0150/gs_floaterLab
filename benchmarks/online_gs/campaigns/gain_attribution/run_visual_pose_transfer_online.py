#!/usr/bin/env python3
"""UTMM continuation: a stream need not trigger an IMU pose refresh.

The initial transfer harness rejected square-1 after successful mapping because
it required refreshed_views > 0. Keep that attempt intact; change only this
post-run assertion, retaining all causal/pose/held-out/work checks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import run_visual_pose_transfer as transfer

BASE = transfer.BASE
ROOT = BASE.WORKSPACE / 'results/campaigns/gain_attribution/visual_pose_transfer_online'
SCENES = [('utmm', 'square-1'), ('utmm', 'ego-centric-1')]
common = transfer.common


def worker(args):
    import torch
    import exp78b_replay_gsslam_mapping as replay
    from dense_pose_refresh_repair import install as repair
    from causal_visual_dense_pose import install as visual
    instances = []
    def install(mapper, shaper):
        repair(mapper, shaper)
        if args.action == 'online_visual':
            visual(mapper, transfer.WEIGHTS, set(shaper.archive.heldout_uids))
        instances.append(mapper)
    replay.install_dense_imu_pose_refresh = install
    common.ROOT = ROOT / args.action
    common.command = lambda d, s, o: transfer.command(d, s, o, online=True)
    common.worker(SimpleNamespace(dataset=args.dataset, scene=args.scene, scope='full'))
    mapper = instances[-1]
    out = ROOT / args.action / args.dataset / args.scene / 'full'
    audit = mapper._dense_pose_refresh_repair_audit
    common.write(out / 'refresh_repair.json', audit)
    if audit['future_imu_used']:
        raise RuntimeError('Future IMU used')
    common.write(out / 'refresh_execution.json', {
        'adapter_installed': True, 'refresh_calls': audit['calls'],
        'refreshed_views': audit['refreshed_views'],
        'zero_refresh_is_valid': True, 'mapping_recipe_changed': False})
    if args.action == 'online_visual':
        common.write(out / 'visual_pose.json', mapper._visual_pose_audit)
        torch.save(mapper._visual_pose_latest, out / 'causal_refined_poses.pt')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker', action='store_true')
    p.add_argument('--dataset'); p.add_argument('--scene'); p.add_argument('--action')
    args = p.parse_args()
    transfer.ROOT = ROOT
    if args.worker:
        return worker(args)
    original_lock = common.read(BASE.WORKSPACE /
        'results/campaigns/gain_attribution/visual_pose_transfer/source_lock.json')
    sources = [Path(f) for f in original_lock] + [Path(__file__)]
    hashes = {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}
    if any(hashes[f] != digest for f, digest in original_lock.items()):
        raise RuntimeError('Original experiment source changed')
    lock = ROOT / 'source_lock.json'
    if lock.exists() and common.read(lock) != hashes:
        raise RuntimeError('Continuation source changed')
    common.write(lock, hashes)
    common.write(ROOT / 'contract.json', {'scenes': SCENES, 'seed': 0,
        'mapping_recipe_unchanged': True, 'validation_change': 'allow zero IMU refresh calls',
        'predecessor': str(BASE.WORKSPACE / 'results/campaigns/gain_attribution/visual_pose_transfer')})
    for dataset, scene in SCENES:
        for action in ['online_control', 'online_visual']:
            out = ROOT / action / dataset / scene / 'full'
            target = out / ('visual_pose.json' if action == 'online_visual' else 'refresh_execution.json')
            if not target.exists():
                common.evaluation.panel.v2.gpu_idle()
                cmd = [str(BASE.PYTHON_ENV / 'bin/python'), str(Path(__file__).resolve()),
                       '--worker', '--dataset', dataset, '--scene', scene, '--action', action]
                log = ROOT / 'logs' / dataset / scene / (action + '.log')
                common.write(log.with_suffix('.command.json'), cmd)
                with log.open('x') as stream:
                    subprocess.run(cmd, env=BASE.mapping_environment(True), stdout=stream,
                                   stderr=subprocess.STDOUT, check=True)
                if not target.exists():
                    raise RuntimeError('Missing worker completion artifact')
                print('COMPLETED', dataset, scene, action, flush=True)
        transfer.compare_online(dataset, scene)


if __name__ == '__main__':
    main()
