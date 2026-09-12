"""Paired seed replication report; missing runs remain explicitly pending."""
import json
import statistics
from inspect_coverage import read_run, ROOT

def main():
    records=[];pending=[]
    for scene in ('utmm_square1_full','rpng_table01_full'):
        for seed in (1,2):
            paths={a:ROOT/'outputs/exp77_coverage_validation'/scene/f'{a}_s{seed}'
                   for a in ('rr','interval_base','coverage1')}
            if not all((p/'view_scheduler_summary.json').exists() for p in paths.values()):
                pending.append(dict(scene=scene,seed=seed));continue
            runs={a:read_run(p) for a,p in paths.items()}
            bs,br=runs['rr']
            for arm,(s,r) in runs.items():
                assert s['arrival_iteration']==bs['arrival_iteration']
                assert [x['iteration'] for x in r]==[x['iteration'] for x in br]
                assert all(set(x['per_view_psnr'])==set(y['per_view_psnr']) for x,y in zip(r,br))
            c=runs['coverage1'][1];n=runs['interval_base'][1]
            records.append(dict(scene=scene,seed=seed,delta_rr=c[-1]['psnr']-br[-1]['psnr'],
                delta_interval_base=c[-1]['psnr']-n[-1]['psnr'],
                curve_delta_rr=[x['psnr']-y['psnr'] for x,y in zip(c,br)],
                zero_service={a:s['zero_service'] for a,(s,r) in runs.items()}))
    out=dict(scope='seed1/2 replication on development scenes',pairs=records,pending=pending)
    if records:
        out['mean_delta_rr']=statistics.fmean(r['delta_rr'] for r in records)
        out['wins_rr']=sum(r['delta_rr']>0 for r in records)
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
