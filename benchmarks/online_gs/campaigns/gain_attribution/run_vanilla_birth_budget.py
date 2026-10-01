#!/usr/bin/env python3
"""Keep PPM unchanged; approximately match prior vanilla Gaussian counts."""
import argparse
from collections import Counter
from pathlib import Path
import subprocess
import run_unified_batch_panel as prior
common=prior.common;trial=common.trial;ROOT=prior.ROOT;HERE=prior.HERE
REFERENCE=ROOT/'results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/dense_rgb'
CARD='campaigns/06_gain_attribution/init_density/vanilla_budget/README.md'


def journal(row):
    message=(f"**2026-09-27 init density budget{row['config'].get('renders_per_kf',40)} {row['case']} / {row['dataset']}:** "
             f"execution={row['valid_execution']}, audit={row['audit_pass']}, PSNR={row['psnr']}, "
             f"error={row['error']}; {row['output']}.")
    with (ROOT/'context/experiments'/CARD).open('a') as f:f.write('\n'+message+'\n')
    for name,heading,link in [('context/STATUS.md','## 최근 흐름 (최신순)\n','experiments/'+CARD),
                             ('context/experiments/INDEX.md','# Experiment Index\n',CARD)]:
        p=ROOT/name;s=p.read_text();assert heading in s
        p.write_text(s.replace(heading,heading+'\n- '+message+' → [카드]('+link+')\n',1))


def audit_run(out,dataset,config):
    quotas=(3,3,6)
    budget=config.get('renders_per_kf',40)
    x=common.read(out/'render_result.json');old=common.read(prior.CONTROL/dataset/'render_result.json')
    ra=common.read(out/'render_audit.json');training=[r for r in ra if r['grad_enabled']]
    assert x['valid_execution'] and all(x['checks'].values())
    assert x['schedule']=='unified' and x['native_commits']==0
    assert x['selector']==config['selector']
    old_budget=old['kf_render_budget']['renders_per_kf']
    assert x['kf_render_budget']['renders_per_kf']==budget
    assert x['render_counts']['no_grad']==old['render_counts']['no_grad']
    assert len(training)==budget*x['kf_render_budget']['kf_admissions']
    normalized=lambda x:[{k:v for k,v in a.items() if k!='renders'} for a in x['kf_render_budget']['admissions']]
    assert normalized(x)==normalized(old)
    assert all(a['renders']==budget for a in x['kf_render_budget']['admissions'])
    assert all(r['backward'] and r['uid']<=r['arrival_uid'] for r in training)
    assert all(r['uid']<=r['arrival_uid'] for r in ra)
    assert [(r['uid'],r['training_renders'],r['all_renders']) for r in x['render_prefixes']]==[
        (r['uid'],r['training_renders']*budget//old_budget,
         r['all_renders']-r['training_renders']+r['training_renders']*budget//old_budget) for r in old['render_prefixes']]
    assert [r['event_id'] for r in x['submitted_events']]==[r['event_id'] for r in old['submitted_events']]
    assert len(x['unified_packets'])==len(x['render_prefixes'])==x['worker']['accepted']==x['worker']['completed']
    assert x['worker']['productive_idle_calls']==0
    by_arrival=Counter(r['arrival_uid'] for r in training);total=0
    for packet,prefix in zip(x['unified_packets'],x['render_prefixes']):
        total+=by_arrival[prefix['uid']]
        assert packet['arrival_uid']==prefix['uid']
        assert packet['renders']==by_arrival[prefix['uid']]
        assert packet['completed']==packet['target']==total==prefix['training_renders']
    assert all(r['seconds']<=x['last_input_at'] for r in x['boundaries']['optimizer_completions'])
    roles=Counter();sizes=Counter();services=0
    for g in x['training']['generations']:
        p=g['policy'];counts=Counter();assert p['selection_count_scope']=='all_rgb'
        assert p['batch_quotas']==list(quotas) and set(p['admitted_dense'])<=set(p['offered_dense'])
        assert p['membership']==('immediate' if config['kappa'] is None else 'growth')
        assert p['tau']==config['tau'] and p['growth_budget_scope']=='dense_only'
        for i,admission in enumerate(g['admissions']):
            if config['kappa'] is not None:
                assert i+1<=admission['rgb_steps']//config['kappa']
        if config['kappa'] is None:
            assert set(p['admitted_dense'])==set(p['offered_dense'])
        for role,weight in p['sampler_pool_tau'].items():
            assert weight==config['tau']/max(1,len(p['admitted_dense'] if role=='dense' else p['keyframes']))
        for s in g['services']:
            assert s['source']=='photometric' and len(s['uids'])==len(set(s['uids']))<=sum(quotas)
            assert [counts[u] for u in s['uids']]==s['counts_before']
            assert len(s['uids'])==len(s['roles'])
            assert all(u in s['window_uids'] for u,r in zip(s['uids'],s['roles']) if r=='window')
            assert [s['roles'].count(r) for r in p['roles']]==s['actual_quotas']
            assert all(left<int(u)<right for u,(left,right) in s['dense_anchors'].items())
            counts.update(s['uids']);roles.update(s['roles']);sizes[len(s['uids'])]+=1;services+=1
        expected={int(u):counts[int(u)] for u in p['counts']}
        assert {int(u):n for u,n in p['counts'].items()}==expected
        assert {int(u):n for u,n in p['photometric_counts'].items()}==expected
    assert services==x['main_optimizer_steps']==x['photometric_commits']
    assert sum(roles.values())==len(training)
    assert x['densify_prune_ablation']['pass'] and not x['densify_prune_ablation']['forbidden_calls']
    metric=common.read(out/'psnr/strict_fixed_manifest/final_result.json')
    old_metric=common.read(prior.CONTROL/dataset/'psnr/strict_fixed_manifest/final_result.json')
    cohort=lambda m:[(r['frame_index'],r['uid'],r['predeclared_fixed_manifest_split']) for r in m['per_view']]
    assert cohort(metric)==cohort(old_metric)
    for name in ('traj_full_beforeBA.txt','traj_kf_beforeBA.txt'):
        assert common.sha(out/name)==common.sha(prior.CONTROL/dataset/name)
    assert x['main_optimizer_steps']==len(training)
    assert x['unified_scale_projection']['enabled'] and x['unified_scale_projection']['calls']>0
    assert x['dense_blur_filter']['enabled']==config['blur']
    expected=[]
    for g in x['training']['generations']:
        assert g['policy']['auxiliary_mode']=='dense_rgb'
        for service in g['services']:
            for uid,role in zip(service['uids'],service['roles']):
                expected.append({'generation':g['policy']['generation'], 'uid':uid, 'role':role,
                    'loss':'rgb_only' if role in ('dense','keyframe_rgb') else 'native_rgbd_normal'})
    assert x['training']['loss_routes']==expected, 'Actual loss routing disagrees with assigned slots'
    assert [r['uid'] for r in training]==[r['uid'] for r in expected]
    gate=x['dense_blur_filter'];rejected=set()
    observed={row['uid'] for row in x['arrivals']}
    if config['blur']:
        for decision in gate['decisions']:
            assert decision['left']<decision['uid']<decision['right']
            assert all(u in observed and u<=decision['right'] for u in decision['reference_uids'])
            score,ref=decision['score'],decision['reference']
            reject=(score['laplacian_energy']<gate['energy_ratio']*ref['laplacian_energy'] and
                    score['high_frequency_ratio']<gate['frequency_ratio']*ref['high_frequency_ratio'])
            assert decision['accepted']==(not reject)
            if reject:rejected.add(decision['uid'])
        assert len(rejected)==gate['rejected_images']
        assert not rejected.intersection(x['deferred_audit']['prepared_uids'])
        for g in x['training']['generations']:
            assert not rejected.intersection(g['policy']['admitted_dense'])
            for service in g['services']:
                assert not rejected.intersection(u for u,role in zip(service['uids'],service['roles']) if role=='dense')
    if config=={'kappa':None,'tau':1.,'blur':True}:
        oldblur=common.read(ROOT/'results/campaigns/gain_attribution/dense_blur_filter/gpu40_v2/on'/dataset/'render_result.json')
        assert [g['services'] for g in x['training']['generations']]==[g['services'] for g in oldblur['training']['generations']]
    return {'pass':True,'one_packet_per_arrival':True,'separate_native_optimizer_steps':0,
            'growth_admission_capacity_verified':True,'blur_rejection_verified':True,
            'actual_loss_routes_verified':True, 'loss_renders':dict(Counter(r['loss'] for r in expected)),
            'scale_projection':x.get('unified_scale_projection'),
            'same_prefix_renders_poses_events_cohort':True,'cumulative_counts_verified':True,
            'densify_prune_off':True,'training_renders':len(training),'optimizer_steps':services,
            'role_renders':dict(roles),'batch_size_histogram':dict(sizes)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=False)
    common.write(args.output/'protocol.json',{'budgets':[15,40],'birth_downsample_multipliers':{'aria':1.01,'rpng':1.52,'utmm':.87},'count_targets':{'aria':190533,'rpng':234218,'utmm':162663},
        'scope':'initial and every subsequent keyframe birth', 'kappa':16,'tau':4.,'blur':False,
        'optimizer_batch_size':1,'batch_quotas':[3,3,6],'seed':0,'selector':'ervs','auxiliary_mode':'dense_rgb',
        'growth_scope':'dense_only','scenes':common.SCENES,'fresh_baselines':False,'baseline':'init_density/gpu15_40_v1 b15_d1 and b40_d1',
        'interpretation':'user-requested approximate capacity match; PPM/content-adaptive weights retained; scene constants for ablation only, not deployment policy',
        'actual_tracking':False,'primary_metric':'held-out PSNR, mapper seconds, final Gaussian count'})
    backend=Path('/home/intern/VIGS-SLAM-online-worker-integration')
    files=list((backend/'vigs').rglob('*.py'))+list(HERE.glob('*.py'))
    source=args.output/'source';source.mkdir();lock={}
    for path in files:
        digest=common.sha(path);dest=source/(digest[:12]+'_'+path.name);dest.write_bytes(path.read_bytes())
        lock[str(path)]={'sha256':digest,'copy':str(dest)}
    common.write(args.output/'source_lock.json',lock)
    env=trial.environment();env['EXP78B_CUSTOM_ROOT']=str(backend)
    env['PYTHONPATH']=str(backend/'vigs')+':'+str(backend)+':'+env['PYTHONPATH']
    tests=['test_unified_rr','test_unified_growth','test_unified_view_training','test_paired_cumulative_counts','test_dense_blur_filter','test_kf_rgb_control']
    cp=subprocess.run([str(trial.BASE.PYTHON_ENV/'bin/python'),'-m','unittest',*tests],cwd=HERE,env=env,capture_output=True,text=True)
    common.write(args.output/'cpu_tests.json',{'tests':tests,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr})
    assert cp.returncode==0
    base=trial.ROOT/'live_worker_integration_audit';rows=[];configs={}
    def run_case(case,config):
        for dataset,scene in common.SCENES.items():
            config={**config,'birth_multiplier':{'aria':1.01,'rpng':1.52,'utmm':.87}[dataset]}
            configs[case+'/'+dataset]=config;common.write(args.output/'cases.json',configs)
            trial.common.evaluation.panel.v2.gpu_idle()
            out=args.output/case/dataset;out.parent.mkdir(parents=True,exist_ok=True)
            setup=base/('v5_packet_identity/aria_setup' if dataset=='aria' else f'v9_productive_worker/three_scene/{dataset}_setup')
            cmd=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(HERE/'run_kf15_render_worker.py'),
                '--setup',str(setup),'--extensions',str(base/'v6_current_stream_extensions'),
                '--output',str(out),'--renders-per-kf',str(config['renders_per_kf']),'--seed','0',
                '--membership','immediate' if config['kappa'] is None else 'growth',
                '--kappa',str(config['kappa'] or 64),'--tau',str(config['tau']),
                '--growth-budget-scope','dense_only','--selector',config['selector'],'--schedule','unified',
                '--selection-count-scope','all_rgb','--batch-quotas','3','3','6','--disable-densify-prune',
                '--optimizer-batch-size','1','--unified-scale-projection','--birth-downsample-multiplier',str(config['birth_multiplier'])]
            reference=ROOT/'results/campaigns/gain_attribution/unified_rr_ervs'/f"gpu{config['renders_per_kf']}_v1"/'ervs'/dataset/'render_result.json'
            cmd.extend(['--reference',str(reference)])
            if config['blur']:cmd.append('--dense-blur-filter')
            common.write(out.parent/(dataset+'_command.json'),cmd);print('START',case,dataset,flush=True)
            with (out.parent/(dataset+'_launcher.log')).open('x') as log:
                code=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
            x=common.read(out/'render_result.json') if (out/'render_result.json').exists() else None
            valid=bool(code==0 and x and x['valid_execution']);evaluation=audit=None;error=None
            if valid:
                try:
                    evaluation=trial.common.evaluation.panel.run_evaluation_twice(out,dataset,scene,
                        trial.BASE.sequence_paths(dataset,scene)['fixed_manifest'])
                    assert evaluation['pass'];audit=audit_run(out,dataset,config)
                    baseline=common.read(reference)
                    assert [g['services'] for g in x['training']['generations']]==[g['services'] for g in baseline['training']['generations']]
                    assert [g['admissions'] for g in x['training']['generations']]==[g['admissions'] for g in baseline['training']['generations']]
                    factor=config['birth_multiplier']
                    assert x['birth_density']['pcd_downsample_init']==64*factor
                    assert x['birth_density']['pcd_downsample']==256*factor
                    assert abs(x['gaussians']*factor/baseline['gaussians']-1)<.02
                    target={'aria':190533,'rpng':234218,'utmm':162663}[dataset]
                    assert abs(x['gaussians']/target-1)<.01
                    birth_rows=[line.split(',') for line in (out/'birth_sampling.csv').read_text().splitlines()]
                    assert birth_rows and {int(r[4]) for r in birth_rows}=={0,1}
                    audit.update(same_selection_admissions_as_original=True, gaussian_ratio=x['gaussians']/baseline['gaussians'],birth_calls=len(birth_rows))
                    common.write(out/'independent_audit.json',audit)
                except Exception as exc:
                    import traceback
                    error=traceback.format_exc()
            changed=[path for path,v in lock.items() if common.sha(Path(path))!=v['sha256']]
            row={'case':case,'config':config,'dataset':dataset,'scene':scene,'output':str(out),'returncode':code,
                 'valid_execution':valid,'audit_pass':bool(audit and audit['pass']),'error':error,
                 'evaluation':evaluation,'source_changed':changed,'audit':audit,
                 'psnr':evaluation['fixed_psnr_first'] if evaluation and evaluation['pass'] else None,
                 'mapping_seconds':x['mapping_seconds'] if x else None,
                 'gaussians':x['gaussians'] if x else None,
                 'peak_cuda_allocated_bytes':x['peak_cuda_allocated_bytes'] if x else None,
                 'peak_cuda_reserved_bytes':x['peak_cuda_reserved_bytes'] if x else None,
                 'final_pool':({k:len(x['training']['generations'][-1]['policy'][k]) for k in ('keyframes','offered_dense','admitted_dense')} if x else None),
                 'dense_prepared':len(set(x['deferred_audit']['prepared_uids'])) if x else None}
            rows.append(row);common.write(args.output/'progress.json',rows);journal(row)
            print('DONE',case,dataset,'PSNR',row['psnr'],'audit',row['audit_pass'],flush=True)
            if not valid or not row['audit_pass'] or changed or error:raise RuntimeError('Invalid run: '+str(row))
    for budget in (15,40):
        run_case(f'b{budget}_vanilla_count',{'kappa':16,'tau':4.,'blur':False,'selector':'ervs','renders_per_kf':budget})
    common.write(args.output/'summary.json',rows)
    print('VANILLA_COUNT_PANEL_COMPLETE',flush=True)

if __name__=='__main__':main()
