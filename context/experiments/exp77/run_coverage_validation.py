"""Fixed seed1/2 replication of coverage1, RR and interval-base; no retuning."""
import json
import time
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/exp77_coverage_validation'

def main():
    OUT.mkdir(parents=True,exist_ok=False)
    jobs=[]
    for seed in (1,2):
        for scene in ('utmm_square1_full','rpng_table01_full'):
            manifest=json.loads((ROOT/'outputs/exp77_full_v2_seed0'/scene/'commands_s0.json').read_text())
            # Rotate ordering across seeds; never choose based on measured outcomes.
            arms=('coverage1','interval_base','rr') if seed==1 else ('interval_base','rr','coverage1')
            for arm in arms:
                base=manifest['commands'][0 if arm=='rr' else 1]
                argv=list(base['argv'])
                argv[argv.index('--arm')+1]=arm
                argv[argv.index('--scheduler_seed')+1]=str(seed)
                argv[argv.index('-m')+1]=str(OUT/scene/f'{arm}_s{seed}')
                jobs.append(dict(scene=scene,seed=seed,arm=arm,argv=argv,cwd=base['cwd']))
    (OUT/'manifest.json').write_text(json.dumps({'scope':'seed replication on development scenes, not held-out scene generalization',
        'parameters':'coverage quota1, gamma log3, K8 unchanged', 'jobs':jobs},indent=2))
    proc=Path('/proc/36130/cmdline')
    while proc.exists():
        try: active=b'run_window_screen.py' in proc.read_bytes()
        except FileNotFoundError: break
        if not active:break
        print('WAIT window PID 36130',flush=True);time.sleep(10)
    for scene in ('utmm_square1_full','rpng_table01_full'):
        for arm in ('window','window_control'):
            if not (ROOT/'outputs/exp77_window_screen_s0'/scene/(arm+'_s0')/'view_scheduler_summary.json').exists():
                raise RuntimeError('Window incomplete; inspect before continuing')
    for job in jobs:
        if shutil.disk_usage(ROOT).free<3*1024**3:raise RuntimeError('Disk reserve')
        folder=OUT/job['scene'];folder.mkdir(exist_ok=True)
        print(job['scene'],job['seed'],job['arm'],'START',flush=True)
        with (folder/f"{job['arm']}_s{job['seed']}.log").open('x') as log:
            subprocess.run(job['argv'],cwd=job['cwd'],stdout=log,stderr=subprocess.STDOUT,check=True)
        print(job['scene'],job['seed'],job['arm'],'DONE',flush=True)

if __name__=='__main__':main()
