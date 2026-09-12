"""Wait for the specific coverage process, then run fixed window/control screen."""
import json
import os
import time
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/exp77_window_screen_s0"

def main():
    OUT.mkdir(parents=True, exist_ok=False)
    jobs=[]
    for scene in ("utmm_square1_full", "rpng_table01_full"):
        ref=ROOT / "outputs/exp77_full_v2_seed0" / scene / "commands_s0.json"
        base=json.loads(ref.read_text())["commands"][1]
        for arm in ("window_control", "window"):
            argv=list(base["argv"])
            argv[argv.index("--arm")+1]=arm
            argv[argv.index("-m")+1]=str(OUT/scene/(arm+"_s0"))
            jobs.append(dict(scene=scene,arm=arm,argv=argv,cwd=base["cwd"]))
    (OUT/"manifest.json").write_text(json.dumps({"scope":"development screen", "jobs":jobs},indent=2))
    # Check identity, not just PID existence; never kill another process.
    proc=Path('/proc/35165/cmdline')
    while proc.exists():
        try: active=b'run_coverage_screen.py' in proc.read_bytes()
        except FileNotFoundError: break
        if not active: break
        print('WAIT coverage PID 35165',flush=True)
        time.sleep(10)
    for scene in ("utmm_square1_full", "rpng_table01_full"):
        for arm in ("interval_base", "coverage1", "coverage2"):
            p=ROOT/"outputs/exp77_coverage_screen_s0"/scene/(arm+"_s0")/"view_scheduler_summary.json"
            if not p.exists(): raise RuntimeError('Coverage incomplete; inspect before continuing')
    for job in jobs:
        if shutil.disk_usage(ROOT).free<3*1024**3: raise RuntimeError('Disk reserve')
        folder=OUT/job['scene'];folder.mkdir(exist_ok=True)
        print(job['scene'],job['arm'],'START',flush=True)
        with (folder/(job['arm']+'.log')).open('x') as log:
            subprocess.run(job['argv'],cwd=job['cwd'],stdout=log,stderr=subprocess.STDOUT,check=True)
        print(job['scene'],job['arm'],'DONE',flush=True)

if __name__=='__main__':main()
