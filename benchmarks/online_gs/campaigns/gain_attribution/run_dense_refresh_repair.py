#!/usr/bin/env python3
"""Compare a bracket-consistent IMU refresh to the source-locked scope pair."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import run_dense_scope_online as scope_run

BASE = scope_run.BASE
ROOT = BASE.WORKSPACE / 'results/campaigns/gain_attribution/dense_refresh_repair'
CONTROL = scope_run.ROOT


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', required=True)
    p.add_argument('--scene', required=True)
    p.add_argument('--scope', choices=['appearance','full'], default='full')
    p.add_argument('--worker', action='store_true')
    args = p.parse_args()
    output = ROOT / args.dataset / args.scene / args.scope
    if args.worker:
        import exp78b_replay_gsslam_mapping as replay
        from dense_pose_refresh_repair import install
        instances = []
        def repaired(mapper, shaper):
            install(mapper, shaper)
            instances.append(mapper)
        replay.install_dense_imu_pose_refresh = repaired
        scope_run.ROOT = ROOT
        scope_run.worker(args)
        audit = instances[-1]._dense_pose_refresh_repair_audit
        if not audit['refreshed_views'] or audit['future_imu_used']:
            raise RuntimeError('Repair inactive or noncausal')
        scope_run.write(output / 'refresh_repair.json', audit)
        return
    sources = [Path(__file__), Path(scope_run.__file__),
               Path(__file__).with_name('dense_pose_refresh_repair.py'),
               BASE.CUSTOM_HARNESS, BASE.PAPER_ROOT / 'vigs/gs_backend.py',
               BASE.WORKSPACE / 'benchmarks/online_gs/exp78b_dense_imu_pose.py']
    hashes = {str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}
    lock = output.parent / 'source_lock.json'
    if lock.exists() and scope_run.read(lock)!=hashes:
        raise RuntimeError('Repair source changed')
    scope_run.write(lock,hashes)
    if not (output / 'refresh_repair.json').exists():
        if output.exists(): raise FileExistsError(output)
        scope_run.evaluation.panel.v2.gpu_idle()
        cmd = [str(BASE.PYTHON_ENV / 'bin/python'), str(Path(__file__).resolve()),
               '--worker','--dataset',args.dataset,'--scene',args.scene,'--scope',args.scope]
        scope_run.write(output/'mapping_command.json',cmd)
        with (output/'mapping.log').open('x') as log:
            subprocess.run(cmd,env=BASE.mapping_environment(True),stdout=log,
                           stderr=subprocess.STDOUT,check=True)
    scope_run.evaluation.panel.run_evaluation_twice(output,args.dataset,args.scene,
        BASE.sequence_paths(args.dataset,args.scene)['fixed_manifest'])
    control = CONTROL / args.dataset / args.scene / args.scope
    a = scope_run.read(control/'mapping_replay_runtime.json')
    b = scope_run.read(output/'mapping_replay_runtime.json')
    checks = {k:a[k]==b[k] for k in ['rasterized_view_updates','optimizer_steps_completed',
               'dense_registered_frame_uids','archive_manifest_sha256','event_ids_fully_processed']}
    for key in ['fixed_event_dense_opportunity_ledger','fixed_event_dense_repeat_opportunity_ledger']:
        checks[key+'_same_selection'] = [r['selected_keys'] for r in a[key]]==[r['selected_keys'] for r in b[key]]
    for key in ['post_eos_optimizer_updates','heldout_mapping_overlap_count','heldout_gaussian_origin_overlap_count']:
        checks[key]=b[key]==0
    metrics = {}
    for name,path in [('control',control),('repaired',output)]:
        metrics[name]=scope_run.read(path/'psnr/strict_fixed_manifest/final_result.json')[
            'predeclared_fixed_manifest_posthoc']['mean_psnr']
    report={'checks':checks,'valid':all(checks.values()),'heldout_psnr':metrics,
            'repair_gain_db':metrics['repaired']-metrics['control'],
            'mapping_only_unbounded':True,'strict_live_claim':False}
    scope_run.write(output/'comparison.json',report)
    print(json.dumps(report),flush=True)
    if not report['valid']: raise RuntimeError('Repair comparison contract failed')


if __name__=='__main__': main()
