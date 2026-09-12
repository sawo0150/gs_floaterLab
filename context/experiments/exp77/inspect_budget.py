"""Validate matched budget groups, including unchanged event60 reference."""
import json
from inspect_coverage import read_run, ROOT

def main():
    rows=[];pending=[]
    for scene in ('utmm_square1_full','rpng_table01_full'):
        for budget in (15,30,60):
            paths={}
            for arm in ('rr','ercb','coverage1'):
                if budget==60:
                    folder='exp77_coverage_screen_s0' if arm=='coverage1' else 'exp77_full_v2_seed0'
                    paths[arm]=ROOT/'outputs'/folder/scene/(arm+'_s0')
                else:paths[arm]=ROOT/'outputs/exp77_budget_ablation_plan'/scene/f'event{budget}'/(arm+'_s0')
            if not all((p/'view_scheduler_summary.json').exists() for p in paths.values()):
                pending.append((scene,budget));continue
            runs={arm:read_run(path) for arm,path in paths.items()}
            bs,br=runs['rr']
            for arm,(s,r) in runs.items():
                assert s['arrival_iteration']==bs['arrival_iteration']
                assert [x['iteration'] for x in r]==[x['iteration'] for x in br]
                assert all(set(x['per_view_psnr'])==set(y['per_view_psnr']) for x,y in zip(r,br))
                rows.append(dict(scene=scene,budget=budget,arm=arm,psnr=r[-1]['psnr'],
                    delta_rr=r[-1]['psnr']-br[-1]['psnr'],zero_service=s['zero_service'],
                    training_gpu_ms=s['training_gpu_ms'],scheduler_cpu_ms=s['scheduler_cpu_ns']/1e6))
    print(json.dumps(dict(scope='matched event-budget development ablation, seed0',rows=rows,pending=pending),indent=2))

if __name__=='__main__':main()
