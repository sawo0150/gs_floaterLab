"""Replicate fixed event15 comparison at seeds1/2, without tuning."""
import json
import time
import shutil
import subprocess
from pathlib import Path
from inspect_coverage import ROOT, read_run

def main():
    out=ROOT/'outputs/exp77_low_budget_validation'
    out.mkdir(parents=True,exist_ok=False)
    original=json.loads((ROOT/'outputs/exp77_budget_ablation_plan/manifest.json').read_text())
    jobs=[]
    for seed in (1,2):
        chosen=[j for j in original['jobs'] if j['budget']==15]
        # Fixed rotated ordering, not outcome-based.
        chosen=sorted(chosen,key=lambda j:(j['scene'], {'ercb':0,'coverage1':1,'rr':2}[j['arm']] if seed==1 else {'coverage1':0,'rr':1,'ercb':2}[j['arm']]))
        for base in chosen:
            j=dict(base);a=list(base['argv']);j['seed']=seed
            a[a.index('--scheduler_seed')+1]=str(seed)
            a[a.index('-m')+1]=str(out/j['scene']/f"{j['arm']}_s{seed}")
            j['argv']=a;jobs.append(j)
    (out/'manifest.json').write_text(json.dumps({'scope':'event15 seed replication, same development scenes','jobs':jobs},indent=2))
    proc=Path('/proc/38506/cmdline')
    while proc.exists():
        try:active=b'run_budget_ablation.py' in proc.read_bytes()
        except FileNotFoundError:break
        if not active:break
        print('WAIT budget PID 38506',flush=True);time.sleep(10)
    for j in original['jobs']:
        read_run(Path(j['argv'][j['argv'].index('-m')+1]))
    for j in jobs:
        if shutil.disk_usage(ROOT).free<3*1024**3:raise RuntimeError('Disk reserve')
        folder=out/j['scene'];folder.mkdir(exist_ok=True)
        print(j['scene'],j['seed'],j['arm'],'START',flush=True)
        with (folder/f"{j['arm']}_s{j['seed']}.log").open('x') as log:
            subprocess.run(j['argv'],cwd=j['cwd'],stdout=log,stderr=subprocess.STDOUT,check=True)
        print(j['scene'],j['seed'],j['arm'],'DONE',flush=True)

if __name__=='__main__':main()
