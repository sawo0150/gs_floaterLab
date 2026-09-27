#!/usr/bin/env python3
"""Isolate current-bracket IMU repair from visual refinement at the same map."""
import hashlib
from pathlib import Path
import subprocess
import sys

import run_dense_scope_online as c

ROOT=c.BASE.WORKSPACE/'results/campaigns/gain_attribution/refresh_only_fixed_map_5k'
PARENT=c.BASE.WORKSPACE/'results/campaigns/gain_attribution/dense_gain_recovery/aria/aria1253'


def worker():
    import torch
    from lietorch import SE3
    from util.poses import to_se3_vec
    from exp78b_frozen_archive import FrozenTrackerArchive
    from exp78b_dense_imu_pose import CausalImuDensePoseShaper
    from dense_pose_refresh_repair import bracket,residuals
    import recover_dense_supervision as diagnostic
    checkpoint=torch.load(PARENT/'checkpoint.pt',map_location='cpu',weights_only=False)
    runtime=c.read(PARENT/'base/mapping_replay_runtime.json')
    shaper=CausalImuDensePoseShaper(FrozenTrackerArchive(runtime['archive']))
    kfs={r['uid']:r for r in checkpoint['cameras'] if r['sensor_type']!='rgb_dense'}
    def se3(row):
        p=torch.eye(4);p[:3,:3],p[:3,3]=row['R'],row['T']
        return SE3(torch.tensor(to_se3_vec(p.numpy()),dtype=torch.float32,device='cuda')[None])
    poses={uid:se3(row) for uid,row in kfs.items()}
    changed=[];skipped=[]
    for row in checkpoint['cameras']:
        if row['sensor_type']!='rgb_dense':continue
        uid=row['uid'];pair=bracket(sorted(kfs),uid)
        if pair is None:skipped.append(uid);continue
        left,right=pair
        alpha=float(uid-left)/float(right-left)
        base=(SE3.exp((poses[right]*poses[left].inv()).log()*alpha)*poses[left]).matrix()[0].cpu()
        residual=torch.eye(4)
        residual[:3,:3]=torch.as_tensor(residuals(shaper,left,right,[uid])[uid],dtype=torch.float32)
        pose=residual@base
        row['R'],row['T']=pose[:3,:3].clone(),pose[:3,3].clone();changed.append(uid)
    checkpoint['training_pose_source']='snapshot KF SE3 interpolation plus current-bracket causal raw IMU; offline fixed-map diagnostic'
    out=ROOT/'aria/aria1253';out.mkdir(parents=True)
    torch.save(checkpoint,out/'checkpoint.pt');(out/'base').symlink_to(PARENT/'base',target_is_directory=True)
    c.write(out/'repair.json',{'changed_dense':changed,'unbracketed_unchanged':skipped,'visual_refinement':False,'strict_online':False})
    # Check all Gaussian/Adam tensors and non-pose camera fields against parent.
    parent=torch.load(PARENT/'checkpoint.pt',map_location='cpu',weights_only=False)
    def equal(a,b):
        if isinstance(a,torch.Tensor):return torch.equal(a,b)
        if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
        if isinstance(a,(list,tuple)):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
        return a==b
    assert equal(checkpoint['gaussians'],parent['gaussians'])
    for row,old in zip(checkpoint['cameras'],parent['cameras']):
        for key in set(row)-({'R','T'} if row['sensor_type']=='rgb_dense' else set()):
            assert equal(row[key],old[key])
    del checkpoint,parent
    diagnostic.ROOT=ROOT
    from types import SimpleNamespace
    diagnostic.worker(SimpleNamespace(dataset='aria',scene='aria1253',action='mixed_full',steps=5000,pose_align_steps=0))


if __name__=='__main__':
    if '--worker' in sys.argv:worker()
    else:
        if ROOT.exists():raise FileExistsError(ROOT)
        sources=[Path(__file__),Path(__file__).with_name('dense_pose_refresh_repair.py'),
                 Path(__file__).with_name('recover_dense_supervision.py')]
        c.write(ROOT/'source_lock.json',{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources})
        c.evaluation.panel.v2.gpu_idle()
        cmd=[str(c.BASE.PYTHON_ENV/'bin/python'),str(Path(__file__).resolve()),'--worker']
        c.write(ROOT/'command.json',cmd)
        with (ROOT/'run.log').open('x') as log:
            subprocess.run(cmd,env=c.BASE.mapping_environment(True),stdout=log,stderr=subprocess.STDOUT,check=True)
        print('Refresh-only fixed-map control complete',flush=True)
