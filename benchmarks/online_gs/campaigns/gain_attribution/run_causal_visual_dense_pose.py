#!/usr/bin/env python3
"""Test image-based dense pose refinement without changing map work."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import run_dense_scope_online as scope_run

BASE = scope_run.BASE
ROOT = BASE.WORKSPACE / 'results/campaigns/gain_attribution/causal_visual_dense_pose'
CONTROL = BASE.WORKSPACE / 'results/campaigns/gain_attribution/dense_refresh_repair'
WEIGHTS = BASE.PAPER_ROOT / 'pretrained_models/droid.pth'


def smoke():
    import torch
    from types import SimpleNamespace
    from lietorch import SE3
    from causal_visual_dense_pose import VisualRefiner
    checkpoint = torch.load(BASE.WORKSPACE /
        'results/campaigns/gain_attribution/dense_gain_recovery/aria/aria1253/checkpoint.pt',
        map_location='cpu', weights_only=False)
    row = next(x for x in checkpoint['cameras'] if x['sensor_type'] != 'rgb_dense')
    fx, fy, cx, cy, width, height = checkpoint['K']
    def view(uid):
        return SimpleNamespace(uid=uid, original_image=row['image'], depth=row['depth'],
            image_height=int(height), image_width=int(width), fx=fx, fy=fy, cx=cx, cy=cy,
            R=torch.eye(3,device='cuda'), T=torch.zeros(3,device='cuda'))
    refiner = VisualRefiner(WEIGHTS)
    left, right, target = [view(i) for i in range(3)]
    aligned, _ = refiner.refine(left, right, target)
    identity_error = float((aligned-torch.eye(4,device='cuda')).norm())
    offset = torch.tensor([[.02, 0, 0, 0, 0, .02]],device='cuda')
    initial = SE3.exp(offset).matrix()[0]
    target.R, target.T = initial[:3,:3], initial[:3,3]
    aligned, _ = refiner.refine(left, right, target)
    before = float((initial-torch.eye(4,device='cuda')).norm())
    after = float((aligned-torch.eye(4,device='cuda')).norm())
    report = {'identity_error':identity_error,'perturbation_before':before,
              'perturbation_after':after,'pass':identity_error < .01 and after < .7*before}
    scope_run.write(ROOT/'smoke.json',report)
    print(json.dumps(report),flush=True)
    if not report['pass']: raise RuntimeError('Visual pose smoke failed')


def worker(args):
    import torch
    import exp78b_replay_gsslam_mapping as replay
    from dense_pose_refresh_repair import install as repair
    from causal_visual_dense_pose import install as visual
    instances=[]
    def install(mapper, shaper):
        repair(mapper, shaper)
        visual(mapper, WEIGHTS, set(shaper.archive.heldout_uids))
        instances.append(mapper)
    replay.install_dense_imu_pose_refresh = install
    scope_run.ROOT = ROOT
    args.scope='full'
    scope_run.worker(args)
    mapper=instances[-1]
    audit=mapper._visual_pose_audit
    if not audit['calls']: raise RuntimeError('Visual refinement not exercised')
    output=ROOT/args.dataset/args.scene/'full'
    scope_run.write(output/'visual_pose.json',audit)
    # Poses produced during the causal run, not a final trajectory filler call.
    torch.save(mapper._visual_pose_latest,output/'causal_refined_poses.pt')
    scope_run.write(output/'refresh_repair.json',mapper._dense_pose_refresh_repair_audit)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',default='aria',choices=['aria','rpng','utmm'])
    p.add_argument('--scene',default='aria1253')
    p.add_argument('--worker',action='store_true')
    p.add_argument('--smoke',action='store_true')
    args=p.parse_args()
    if args.smoke: return smoke()
    if args.worker: return worker(args)
    output=ROOT/args.dataset/args.scene/'full'
    sources=[Path(__file__),Path(scope_run.__file__),
             Path(__file__).with_name('causal_visual_dense_pose.py'),
             Path(__file__).with_name('dense_pose_refresh_repair.py'),
             BASE.CUSTOM_HARNESS,BASE.PAPER_ROOT/'vigs/gs_backend.py',
             BASE.PAPER_ROOT/'vigs/factor_graph.py',BASE.PAPER_ROOT/'vigs/depth_video.py',
             BASE.PAPER_ROOT/'vigs/modules/droid_net.py',WEIGHTS]
    hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}
    lock=output.parent/'source_lock.json'
    if lock.exists() and scope_run.read(lock)!=hashes: raise RuntimeError('Source lock changed')
    scope_run.write(lock,hashes)
    if not (ROOT/'smoke.json').exists():
        scope_run.evaluation.panel.v2.gpu_idle()
        subprocess.run([str(BASE.PYTHON_ENV/'bin/python'),str(Path(__file__).resolve()),'--smoke'],
                       env=BASE.mapping_environment(True),check=True)
    if not scope_run.read(ROOT/'smoke.json')['pass']: raise RuntimeError('Smoke not passed')
    if not (output/'visual_pose.json').exists():
        if output.exists(): raise FileExistsError(output)
        scope_run.evaluation.panel.v2.gpu_idle()
        cmd=[str(BASE.PYTHON_ENV/'bin/python'),str(Path(__file__).resolve()),'--worker',
             '--dataset',args.dataset,'--scene',args.scene]
        scope_run.write(output/'mapping_command.json',cmd)
        with (output/'mapping.log').open('x') as log:
            subprocess.run(cmd,env=BASE.mapping_environment(True),stdout=log,stderr=subprocess.STDOUT,check=True)
    scope_run.evaluation.panel.run_evaluation_twice(output,args.dataset,args.scene,
        BASE.sequence_paths(args.dataset,args.scene)['fixed_manifest'])
    control=CONTROL/args.dataset/args.scene/'full'
    a,b=[scope_run.read(q/'mapping_replay_runtime.json') for q in [control,output]]
    checks={k:a[k]==b[k] for k in ['rasterized_view_updates','optimizer_steps_completed',
            'dense_registered_frame_uids','archive_manifest_sha256','event_ids_fully_processed']}
    for key in ['fixed_event_dense_opportunity_ledger','fixed_event_dense_repeat_opportunity_ledger']:
        checks[key]=[(r['event_id'],r['map_generation'],r['selected_keys']) for r in a[key]]==[
            (r['event_id'],r['map_generation'],r['selected_keys']) for r in b[key]]
    for key in ['post_eos_optimizer_updates','heldout_mapping_overlap_count','heldout_gaussian_origin_overlap_count']:
        checks[key]=b[key]==a[key]==0
    audit=scope_run.read(output/'visual_pose.json')
    checks['causal_brackets']=all(r['left']<r['uid']<r['right']<=r['latest_mapper_kf'] for r in audit['calls'])
    checks['anchors_depth_fixed']=all(r['anchor_pose_unchanged'] and r['depth_unchanged'] for r in audit['calls'])
    metrics={name:scope_run.read(q/'psnr/strict_fixed_manifest/final_result.json')[
        'predeclared_fixed_manifest_posthoc']['mean_psnr'] for name,q in [('control',control),('visual',output)]}
    report={'checks':checks,'valid':all(checks.values()),'heldout_psnr':metrics,
            'visual_gain_db':metrics['visual']-metrics['control'],
            'refinement_calls':len(audit['calls']),'motion_graph_updates':6*len(audit['calls']),
            'extra_pose_wall_seconds':audit['wall_seconds'],
            'network_load_seconds':audit['network_load_seconds'],
            'mapping_wall_seconds':{k:r['mapping_wall_seconds'] for k,r in [('control',a),('visual',b)]},
            'total_compute_matched':False,'strict_live_claim':False}
    scope_run.write(output/'comparison.json',report)
    print(json.dumps(report),flush=True)
    if not report['valid']: raise RuntimeError('Visual comparison contract failed')


if __name__=='__main__': main()
