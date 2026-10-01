"""Same-budget 2x2 sampler / RGB source comparison, with work differences."""
import argparse
from pathlib import Path
import run_unified_rr_dense_control as control

def main():
    p=argparse.ArgumentParser();p.add_argument('--dense',type=Path,required=True);p.add_argument('--control',type=Path,required=True)
    args=p.parse_args();c=control.common
    dense=c.read(args.dense/'summary.json');kf=c.read(args.control/'summary.json')
    assert len(dense)==len(kf)==6
    locks=[c.read(r/'source_lock.json') for r in (args.dense,args.control)]
    assert all(v['sha256']==locks[1][k]['sha256'] for k,v in locks[0].items())
    assert not [k for k,v in locks[1].items() if c.sha(Path(k))!=v['sha256']]
    rows=[]
    for dataset in c.SCENES:
        record={'dataset':dataset,'arms':{},'comparisons':{}}
        for selector in ('rr','ervs'):
            a=next(x for x in dense if x['dataset']==dataset and x['case']==selector)
            b=next(x for x in kf if x['dataset']==dataset and x['case']==selector)
            for row in (a,b):
                assert row['valid_execution'] and row['audit_pass'] and not row['error'] and not row['source_changed']
            control.audit_run(Path(b['output']),dataset,b['config'])
            x=c.read(Path(a['output'])/'render_result.json');y=c.read(Path(b['output'])/'render_result.json')
            assert x['render_counts']==y['render_counts']
            assert x['kf_render_budget']==y['kf_render_budget']
            assert x['main_optimizer_steps']==y['main_optimizer_steps']
            assert x['gaussians']==y['gaussians']
            assert len(x['training']['generations'])==len(y['training']['generations'])
            for ga,gb in zip(x['training']['generations'],y['training']['generations']):
                assert ga['admissions']==gb['admissions']
                assert ga['policy']['keyframes']==gb['policy']['keyframes']
            for name in ('traj_full_beforeBA.txt','traj_kf_beforeBA.txt'):
                assert c.sha(Path(a['output'])/name)==c.sha(Path(b['output'])/name)
            for name,row,r in (('dense',a,x),('kf_rgb',b,y)):
                record['arms'][name+'_'+selector]={'psnr':row['psnr'],'mapping_seconds':row['mapping_seconds'],
                    'loss_renders':row['audit']['loss_renders'],'role_renders':row['audit']['role_renders'],
                    'batch_size_histogram':row['audit']['batch_size_histogram'],
                    'renders_and_adam':r['main_optimizer_steps'],'gaussians':r['gaussians']}
            loss=lambda r:[s['loss'] for s in r['training']['loss_routes']]
            schedule=lambda r:[(s['lr_render_position'],s['selection_batch_size']) for g in r['training']['generations'] for s in g['services']]
            record['comparisons'][selector]={'dense_gain':a['psnr']-b['psnr'],
                'loss_role_differences':sum(u!=v for u,v in zip(loss(x),loss(y))),
                'batch_lr_differences':sum(u!=v for u,v in zip(schedule(x),schedule(y))),
                'same_prefix_render_adam_admissions_poses_gs':True}
        arms=record['arms']
        record['ervs_gain_dense']=arms['dense_ervs']['psnr']-arms['dense_rr']['psnr']
        record['ervs_gain_kf_rgb']=arms['kf_rgb_ervs']['psnr']-arms['kf_rgb_rr']['psnr']
        rows.append(record)
    result={'pass':True,'rows':rows,
        'mean_dense_gain':{s:sum(r['comparisons'][s]['dense_gain'] for r in rows)/3 for s in ('rr','ervs')},
        'mean_ervs_gain':{name:sum(r['ervs_gain_'+name] for r in rows)/3 for name in ('dense','kf_rgb')}}
    c.write(args.control/'factorial_comparison.json',result)
    print(result)

if __name__=='__main__':main()
