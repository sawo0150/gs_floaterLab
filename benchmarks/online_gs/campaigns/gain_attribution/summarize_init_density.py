"""Audit per-birth budgets and summarize the two-budget density experiment."""
import argparse
from pathlib import Path
import run_init_density_panel as panel

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    root=args.output.resolve();c=panel.common;rows=c.read(root/'summary.json')
    assert len(rows)==18
    lock=c.read(root/'source_lock.json')
    assert not [path for path,v in lock.items() if c.sha(Path(path))!=v['sha256']]
    details=[]
    for budget in (15,40):
        for dataset in c.SCENES:
            baseline=next(r for r in rows if r['case']==f'b{budget}_d1' and r['dataset']==dataset)
            base_path=Path(baseline['output'])
            original=c.read(base_path/'render_result.json')
            original_births=[r.split(',') for r in (base_path/'birth_sampling.csv').read_text().splitlines()]
            for factor in (1,2,4):
                row=next(r for r in rows if r['case']==f'b{budget}_d{factor}' and r['dataset']==dataset)
                assert row['valid_execution'] and row['audit_pass'] and not row['error'] and not row['source_changed']
                path=Path(row['output']);x=c.read(path/'render_result.json')
                births=[r.split(',') for r in (path/'birth_sampling.csv').read_text().splitlines()]
                assert len(births)==len(original_births)
                assert [r[:3]+r[4:] for r in births]==[r[:3]+r[4:] for r in original_births]
                assert all(abs(int(a[3])*factor-int(b[3]))<=4*factor for a,b in zip(births,original_births))
                last_init=max(i for i,r in enumerate(births) if int(r[4]))
                assert sum(int(r[3]) for r in births[last_init:])==x['gaussians']
                assert [g['services'] for g in x['training']['generations']]==[g['services'] for g in original['training']['generations']]
                details.append({'budget':budget,'dataset':dataset,'factor':factor,'psnr':row['psnr'],
                    'psnr_delta':row['psnr']-baseline['psnr'],'mapping_seconds':row['mapping_seconds'],
                    'time_reduction_percent':100*(1-row['mapping_seconds']/baseline['mapping_seconds']),
                    'gaussians':row['gaussians'],'gaussian_ratio':row['gaussians']/baseline['gaussians'],
                    'peak_allocated_mib':row['peak_cuda_allocated_bytes']/2**20,
                    'peak_reserved_mib':row['peak_cuda_reserved_bytes']/2**20,
                    'renders_and_adam':x['main_optimizer_steps'],'per_birth_count_audit':True})
    for dataset in c.SCENES:
        for factor in (1,2,4):
            a,b=[r for r in details if r['dataset']==dataset and r['factor']==factor]
            assert a['gaussians']==b['gaussians']
    aggregate=[]
    for budget in (15,40):
        original=sum(r['mapping_seconds'] for r in details if r['budget']==budget and r['factor']==1)
        for factor in (1,2,4):
            group=[r for r in details if r['budget']==budget and r['factor']==factor]
            aggregate.append({'budget':budget,'factor':factor,'mean_psnr_delta':sum(r['psnr_delta'] for r in group)/3,
                'worst_psnr_delta':min(r['psnr_delta'] for r in group),
                'all_scenes_within_0_1db':all(r['psnr_delta']>=-.1 for r in group),
                'time_reduction_percent':100*(1-sum(r['mapping_seconds'] for r in group)/original)})
    c.write(root/'comparison.json',{'pass':True,'details':details,'aggregate':aggregate})
    print(aggregate)

if __name__=='__main__':main()
