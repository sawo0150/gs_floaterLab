"""Prepare fair event-budget ablation without executing training or changing inputs."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/exp77_budget_ablation_plan'

def main():
    OUT.mkdir(parents=True,exist_ok=False)
    jobs=[]
    for scene in ('utmm_square1_full','rpng_table01_full'):
        old=json.loads((ROOT/'outputs/exp77_full_v2_seed0'/scene/'commands_s0.json').read_text())
        payload=json.loads(Path(old['arrivals']).read_text())
        mapping=payload['arrival_iteration_by_name']
        assert all((v-1)%60==0 for v in mapping.values())
        for budget in (15,30):
            arrival={name:1+((v-1)//60)*budget for name,v in mapping.items()}
            total=max(arrival.values())
            dest=OUT/f'{scene}_event{budget}.json'
            dest.write_text(json.dumps({'arrival_iteration_by_name':arrival,'total_iterations':total,
                'source_schedule':old['arrivals'],'updates_per_event':budget,'tail_iters':0},indent=2))
            for arm in ('rr','ercb','coverage1'):
                base=old['commands'][0 if arm=='rr' else 1]
                argv=list(base['argv'])
                replacements={'--arm':arm,'--view_schedule':str(dest),'--iterations':str(total),
                    '--position_lr_max_steps':str(total),'-m':str(OUT/scene/f'event{budget}'/(arm+'_s0'))}
                for flag,value in replacements.items():argv[argv.index(flag)+1]=value
                start=argv.index('--test_iterations')+1;end=argv.index('--save_iterations')
                argv[start:end]=list(map(str,sorted(set((max(1,total//4),max(1,total//2),total)))))
                argv[argv.index('--save_iterations')+1]=str(total)
                jobs.append(dict(scene=scene,budget=budget,arm=arm,argv=argv,cwd=base['cwd']))
    (OUT/'manifest.json').write_text(json.dumps({'status':'PREPARED_NOT_RUN',
        'contract':'all frames/events retained; same per-event budget for every arm; original event60 results retained',
        'caveat':'normalized LR schedule per budget; cannot isolate budget from LR across budgets, within-budget comparison matched',
        'jobs':jobs},indent=2))
    print(OUT/'manifest.json')

if __name__=='__main__':main()
