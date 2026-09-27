#!/usr/bin/env python3
"""Fixed-map pose isolation using only snapshot training RGB/pose/depth."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import run_dense_scope_online as common

BASE=common.BASE
ROOT=BASE.WORKSPACE/'results/campaigns/gain_attribution/causal_visual_dense_pose_fixed_map'
PARENT=BASE.WORKSPACE/'results/campaigns/gain_attribution/dense_gain_recovery/aria/aria1253'


def worker():
    import torch
    from types import SimpleNamespace
    import recover_dense_supervision as diagnostic
    from causal_visual_dense_pose import VisualRefiner
    from dense_pose_refresh_repair import bracket
    output=ROOT/'aria/aria1253'
    output.mkdir(parents=True,exist_ok=True)
    checkpoint=torch.load(PARENT/'checkpoint.pt',map_location='cpu',weights_only=False)
    k=checkpoint['K']
    views={}
    for row in checkpoint['cameras']:
        views[row['uid']]=SimpleNamespace(uid=row['uid'], original_image=row['image'],
            depth=row['depth'], R=row['R'].cuda(),T=row['T'].cuda(),
            image_height=int(k[-1]),image_width=int(k[-2]),fx=k[0],fy=k[1],cx=k[2],cy=k[3])
    kf=sorted(row['uid'] for row in checkpoint['cameras'] if row['sensor_type']!='rgb_dense')
    refiner=VisualRefiner(BASE.PAPER_ROOT/'pretrained_models/droid.pth')
    audit={'calls':[],'skipped':[], 'post_eos_pose_refinement':True,
           'pose_source':'snapshot training keyframes; no evaluation trajectory',
           'strict_online':False,'network_load_seconds':refiner.load_seconds}
    torch.cuda.synchronize();start=time.perf_counter()
    for row in checkpoint['cameras']:
        if row['sensor_type']!='rgb_dense':continue
        uid=row['uid'];pair=bracket(kf,uid)
        if pair is None:
            audit['skipped'].append(uid);continue
        value,stats=refiner.refine(views[pair[0]],views[pair[1]],views[uid])
        row['R'],row['T']=value[:3,:3].cpu().clone(),value[:3,3].cpu().clone()
        audit['calls'].append({'uid':uid,'left':pair[0],'right':pair[1],**stats})
    torch.cuda.synchronize();audit['pose_wall_seconds']=time.perf_counter()-start
    # Ensure every non-pose field and KF pose still equals the parent snapshot.
    parent=torch.load(PARENT/'checkpoint.pt',map_location='cpu',weights_only=False)
    def equal(a,b):
        if isinstance(a,torch.Tensor):return torch.equal(a,b)
        if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
        if isinstance(a,(list,tuple)):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
        return a==b
    checks={'gaussians_and_adam_unchanged':equal(checkpoint['gaussians'],parent['gaussians'])}
    camera_checks=[]
    for row,old in zip(checkpoint['cameras'],parent['cameras']):
        keys=set(row)-({'R','T'} if row['sensor_type']=='rgb_dense' else set())
        camera_checks.extend(equal(row[k],old[k]) for k in keys)
    checks['only_dense_pose_changed']=all(camera_checks)
    if not all(checks.values()):raise RuntimeError('Pose-only checkpoint isolation failed')
    audit['checks']=checks
    checkpoint['training_pose_source']='actual mapper KF poses; dense visually refined against snapshot anchors at EOS (offline diagnostic)'
    torch.save(checkpoint,output/'checkpoint.pt')
    (output/'base').symlink_to(PARENT/'base',target_is_directory=True)
    common.write(output/'pose_refinement.json',audit)
    del parent,checkpoint,refiner,views
    torch.cuda.empty_cache()
    diagnostic.ROOT=ROOT
    args=SimpleNamespace(dataset='aria',scene='aria1253',action='mixed_full',steps=1000,pose_align_steps=0)
    diagnostic.worker(args)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--worker',action='store_true');args=p.parse_args()
    if args.worker:return worker()
    output=ROOT/'aria/aria1253'
    if output.exists():raise FileExistsError(output)
    sources=[Path(__file__),Path(__file__).with_name('causal_visual_dense_pose.py'),
             Path(__file__).with_name('recover_dense_supervision.py'),
             BASE.PAPER_ROOT/'vigs/factor_graph.py',BASE.PAPER_ROOT/'vigs/depth_video.py']
    common.write(ROOT/'source_lock.json',{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources})
    common.evaluation.panel.v2.gpu_idle()
    cmd=[str(BASE.PYTHON_ENV/'bin/python'),str(Path(__file__).resolve()),'--worker']
    common.write(ROOT/'command.json',cmd)
    with (ROOT/'run.log').open('x') as log:
        subprocess.run(cmd,env=BASE.mapping_environment(True),stdout=log,stderr=subprocess.STDOUT,check=True)
    old=common.read(PARENT/'mixed_full/result.json');new=common.read(output/'mixed_full/result.json')
    kf=common.read(PARENT/'kf_full/result.json')
    checks={k:old[k]==new[k] for k in ['initial_psnr','selection_sha256','training_views',
           'heldout_views','heldout_overlap','same_gaussian_count','post_eos_optimizer_updates']}
    checks['saved_reload_exact']=new['saved_reload_max_psnr_difference']==0
    report={'valid':all(checks.values()),'checks':checks,'kf_only_psnr':kf['final_psnr'],
        'original_mixed_psnr':old['final_psnr'],'visual_mixed_psnr':new['final_psnr'],
        'visual_gain_db':new['final_psnr']-old['final_psnr'],
        'mixed_minus_kf':new['final_psnr']-kf['final_psnr'],
        'strict_online':False,'total_compute_matched':False}
    common.write(output/'comparison.json',report);print(json.dumps(report),flush=True)
    if not report['valid']:raise RuntimeError('Fixed-map pose comparison failed')


if __name__=='__main__':main()
