#!/usr/bin/env python3
"""Aggregate held-out PSNR, exposure, and tail minibatch entropy for exp74."""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image

REPO=Path('/home/intern/gs_floaterLab/repos/main/3dgs-custom'); sys.path.insert(0,str(REPO))
from runtime.scheduler import make_scheduler
ROOT=Path(__file__).parent/'evidence'/'runs'

RUNS={
 'aria1253_causal_rr':('aria1253_causal_rr_r4_s0','causal_rr',0.,11880),
 'aria1253_count_balanced_rr':('aria1253_count_balanced_rr_r4_s0','count_balanced_rr',0.,11880),
 'aria1253_soft_0005':('aria1253_soft_b0005_r4_s0','soft_count',.005,11880),
 'aria1253_soft_001':('aria1253_soft_b001_r4_s0','soft_count',.01,11880),
 'aria1253_soft_002':('aria1253_soft_b002_r4_s0','soft_count',.02,11880),
 'aria1253_floor_025':('aria1253_floor_a025_r4_s0','floor_rr',.25,11880),
 'aria1253_floor_05':('aria1253_floor_a05_r4_s0','floor_rr',.5,11880),
 'aria305_causal_rr':('aria305_causal_rr_r4_s0','causal_rr',0.,21780),
 'aria305_count_balanced_rr':('aria305_count_balanced_rr_r4_s0','count_balanced_rr',0.,21780),
}

def psnr(path, iteration):
    p=path/'test'/f'ours_{iteration}'; vals=[]
    for r,g in zip(sorted((p/'renders').glob('*.png')),sorted((p/'gt').glob('*.png'))):
        a=np.asarray(Image.open(r),dtype=np.float32)/255.; b=np.asarray(Image.open(g),dtype=np.float32)/255.
        vals.append(float(-10*np.log10(np.mean((a-b)**2))))
    return float(np.mean(vals)),[float(np.mean(x)) for x in np.array_split(vals,4)]

def replay_entropy(summary,name,beta,total,block=128,bins=16):
    names=list(summary['selection_count']); arrivals=list(summary['arrival_iteration'].values()); s=make_scheduler(name,0,beta); history=[]; nxt=0
    for t in range(1,total+1):
        added=[]
        while nxt<len(names) and arrivals[nxt]<=t: added.append(nxt); nxt+=1
        s.add(added); history.append(s.draw())
    start=max(arrivals)-1; ent=[]
    for chunk in np.array_split(np.asarray(history[start:]),max(1,math.ceil((total-start)/block))):
        h=np.bincount(np.minimum(chunk*bins//len(names),bins-1),minlength=bins); p=h[h>0]/len(chunk)
        ent.append(float(-(p*np.log(p)).sum()/math.log(bins)))
    return float(np.mean(ent)),len(history)-start

out={}
for key,(folder,sched,beta,total) in RUNS.items():
    path=ROOT/folder; summary=json.loads((path/'view_scheduler_summary.json').read_text()); counts=np.asarray(list(summary['selection_count'].values()))
    mean_psnr,bins_psnr=psnr(path,total); entropy,tail_n=replay_entropy(summary,sched,beta,total)
    out[key]={'psnr':mean_psnr,'psnr_temporal_quartiles':bins_psnr,'count_cv':float(counts.std()/counts.mean()),
              'count_min':int(counts.min()),'count_max':int(counts.max()),'count_temporal_quartiles':[float(np.mean(x)) for x in np.array_split(counts,4)],
              'tail_block128_temporal_entropy_ratio':entropy,'tail_updates':tail_n}

# Static RR has no causal summary; its count discrepancy is deterministically <=1.
sp=ROOT/'aria1253_static_rr_r4_s0'; m,b=psnr(sp,11880)
out['aria1253_static_rr']={'psnr':m,'psnr_temporal_quartiles':b,'count_cv_upper_bound':1/(11880/1140),'count_min':10,'count_max':11}
(Path(__file__).parent/'evidence'/'exp74_summary.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
