"""Collect all completed screens with contract validation; never select winners."""
import json
import statistics
from pathlib import Path
from inspect_coverage import read_run, ROOT

def main():
    report=[]
    roots={"exp77_full_v2_seed0":("rr","ercb","packet"),
           "exp77_coverage_screen_s0":("interval_base","coverage1","coverage2"),
           "exp77_window_screen_s0":("window_control","window")}
    for scene in ("utmm_square1_full","rpng_table01_full"):
        bs,br=read_run(ROOT/"outputs/exp77_full_v2_seed0"/scene/"rr_s0")
        for folder, arms in roots.items():
            for arm in arms:
                path=ROOT/"outputs"/folder/scene/(arm+"_s0")
                if not (path/"view_scheduler_summary.json").exists():continue
                s,r=read_run(path)
                assert s['arrival_iteration']==bs['arrival_iteration']
                assert [x['iteration'] for x in r]==[x['iteration'] for x in br]
                assert all(set(x['per_view_psnr'])==set(y['per_view_psnr']) for x,y in zip(r,br))
                report.append(dict(scene=scene,arm=arm,psnr=r[-1]['psnr'],
                    delta_rr=r[-1]['psnr']-br[-1]['psnr'],
                    curve_delta_rr=[x['psnr']-y['psnr'] for x,y in zip(r,br)],
                    zero_service=s['zero_service'],
                    served_first_delay=statistics.fmean(s['first_service_delay_updates'].values()),
                    scheduler_cpu_ms=s['scheduler_cpu_ns']/1e6,
                    training_gpu_ms=s['training_gpu_ms'],source=str(path)))
    print(json.dumps({'scope':'single-seed development, not generalization evidence','runs':report},indent=2))

if __name__=='__main__':main()
