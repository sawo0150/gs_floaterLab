"""Execute the already fixed budget manifest after seed replication completes."""
import json
import time
import shutil
import subprocess
from pathlib import Path
from inspect_coverage import read_run, ROOT

def main():
    out=ROOT/'outputs/exp77_budget_ablation_plan'
    manifest=json.loads((out/'manifest.json').read_text())
    with (out/'execution_started.json').open('x') as f:
        json.dump({'state':'waiting for replication PID 36650'},f)
    proc=Path('/proc/36650/cmdline')
    while proc.exists():
        try:active=b'run_coverage_validation.py' in proc.read_bytes()
        except FileNotFoundError:break
        if not active:break
        print('WAIT replication PID 36650',flush=True);time.sleep(10)
    for scene in ('utmm_square1_full','rpng_table01_full'):
        for seed in (1,2):
            for arm in ('rr','interval_base','coverage1'):
                read_run(ROOT/'outputs/exp77_coverage_validation'/scene/f'{arm}_s{seed}')
    for job in manifest['jobs']:
        if shutil.disk_usage(ROOT).free<3*1024**3:raise RuntimeError('Disk reserve')
        folder=out/job['scene']/f"event{job['budget']}"
        folder.mkdir(parents=True,exist_ok=True)
        print(job['scene'],job['budget'],job['arm'],'START',flush=True)
        with (folder/(job['arm']+'.log')).open('x') as log:
            subprocess.run(job['argv'],cwd=job['cwd'],stdout=log,stderr=subprocess.STDOUT,check=True)
        print(job['scene'],job['budget'],job['arm'],'DONE',flush=True)

if __name__=='__main__':main()
