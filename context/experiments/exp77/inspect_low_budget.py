"""All event15 seeds with paired contracts and timing, no winner selection."""
import json
import statistics
from inspect_coverage import ROOT, read_run

def main():
    rows=[];pending=[]
    for scene in ('utmm_square1_full','rpng_table01_full'):
        for seed in (0,1,2):
            folder=(ROOT/'outputs/exp77_budget_ablation_plan'/scene/'event15' if seed==0
                    else ROOT/'outputs/exp77_low_budget_validation'/scene)
            paths={a:folder/f'{a}_s{seed}' for a in ('rr','ercb','coverage1')}
            if not all((p/'view_scheduler_summary.json').exists() for p in paths.values()):
                pending.append((scene,seed));continue
            runs={a:read_run(p) for a,p in paths.items()};bs,br=runs['rr']
            for arm,(s,r) in runs.items():
                assert s['arrival_iteration']==bs['arrival_iteration']
                assert [x['iteration'] for x in r]==[x['iteration'] for x in br]
                assert all(set(x['per_view_psnr'])==set(y['per_view_psnr']) for x,y in zip(r,br))
                rows.append(dict(scene=scene,seed=seed,arm=arm,psnr=r[-1]['psnr'],
                    delta_rr=r[-1]['psnr']-br[-1]['psnr'],
                    curve_delta_rr=[x['psnr']-y['psnr'] for x,y in zip(r,br)],
                    zero_service=s['zero_service'],gpu_ms=s['training_gpu_ms'],
                    scheduler_cpu_ms=s['scheduler_cpu_ns']/1e6))
    aggregate=[]
    for scene in ('utmm_square1_full','rpng_table01_full'):
        for arm in ('ercb','coverage1'):
            x=[r for r in rows if r['scene']==scene and r['arm']==arm]
            if len(x)==3:
                aggregate.append(dict(scene=scene,arm=arm,mean_delta_rr=statistics.fmean(r['delta_rr'] for r in x),
                    min_delta_rr=min(r['delta_rr'] for r in x),wins=sum(r['delta_rr']>0 for r in x)))
    print(json.dumps(dict(scope='event15 fixed parameters; seed0 development, seeds1/2 replication',
                         rows=rows,aggregate=aggregate,pending=pending),indent=2))

if __name__=='__main__':main()
