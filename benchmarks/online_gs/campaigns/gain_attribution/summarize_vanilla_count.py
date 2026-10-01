"""Compare approximate vanilla-sized PPM maps to fresh unified baselines."""
import argparse
from pathlib import Path
import run_vanilla_birth_budget as panel

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True)
    args=p.parse_args();c=panel.common;rows=c.read(args.output/'summary.json');bases=c.read(args.baseline/'summary.json')
    assert len(rows)==6
    lock=c.read(args.output/'source_lock.json')
    assert not [k for k,v in lock.items() if c.sha(Path(k))!=v['sha256']]
    details=[]
    for row in rows:
        assert row['valid_execution'] and row['audit_pass'] and not row['source_changed'] and not row['error']
        dataset=row['dataset'];budget=row['config']['renders_per_kf'];factor=row['config']['birth_multiplier']
        original=next(r for r in bases if r['dataset']==dataset and r['case']==f'b{budget}_d1')
        x=c.read(Path(row['output'])/'render_result.json');y=c.read(Path(original['output'])/'render_result.json')
        assert x['render_counts']==y['render_counts']
        assert x['main_optimizer_steps']==y['main_optimizer_steps']
        assert [g['services'] for g in x['training']['generations']]==[g['services'] for g in y['training']['generations']]
        births=[r.split(',') for r in (Path(row['output'])/'birth_sampling.csv').read_text().splitlines()]
        old_births=[r.split(',') for r in (Path(original['output'])/'birth_sampling.csv').read_text().splitlines()]
        assert [r[:3]+r[4:] for r in births]==[r[:3]+r[4:] for r in old_births]
        last_init=max(i for i,r in enumerate(births) if int(r[4]))
        assert sum(int(r[3]) for r in births[last_init:])==x['gaussians']
        target={'aria':190533,'rpng':234218,'utmm':162663}[dataset]
        assert abs(x['gaussians']/target-1)<.01
        details.append({'budget':budget,'dataset':dataset,'multiplier':factor,'baseline_psnr':original['psnr'],
            'psnr':row['psnr'],'psnr_delta':row['psnr']-original['psnr'],
            'baseline_seconds':original['mapping_seconds'],'seconds':row['mapping_seconds'],
            'baseline_gaussians':original['gaussians'],'gaussians':row['gaussians'],'vanilla_target':target,
            'count_error_percent':100*(row['gaussians']/target-1),
            'peak_allocated_mib':row['peak_cuda_allocated_bytes']/2**20,
            'same_selection_admissions_work':True})
    result={'pass':True,'details':details,'aggregate':[]}
    for budget in (15,40):
        group=[r for r in details if r['budget']==budget]
        result['aggregate'].append({'budget':budget,'mean_psnr_delta':sum(r['psnr_delta'] for r in group)/3,
            'time_reduction_percent':100*(1-sum(r['seconds'] for r in group)/sum(r['baseline_seconds'] for r in group))})
    c.write(args.output/'comparison.json',result);print(result)

if __name__=='__main__':main()
