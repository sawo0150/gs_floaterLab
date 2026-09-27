#!/usr/bin/env python3
"""Predeclared staged kappa/tau search with the existing blur gate."""
import argparse
from collections import Counter
from pathlib import Path
import subprocess
import run_unified_batch_panel as prior
common=prior.common;trial=common.trial;ROOT=prior.ROOT;HERE=prior.HERE
REFERENCE=ROOT/'results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/dense_rgb'
CARD='campaigns/06_gain_attribution/growth_entropy_blur/README.md'


def journal(row):
    message=(f"**2026-09-26 growth/entropy/blur {row['case']} / {row['dataset']}:** "
             f"execution={row['valid_execution']}, audit={row['audit_pass']}, PSNR={row['psnr']}, "
             f"error={row['error']}; {row['output']}.")
    with (ROOT/'context/experiments'/CARD).open('a') as f:f.write('\n'+message+'\n')
    for name,heading,link in [('context/STATUS.md','## 최근 흐름 (최신순)\n','experiments/'+CARD),
                             ('context/experiments/INDEX.md','# Experiment Index\n',CARD)]:
        p=ROOT/name;s=p.read_text();assert heading in s
        p.write_text(s.replace(heading,heading+'\n- '+message+' → [카드]('+link+')\n',1))


def select_case(rows,cases):
    grouped={case:{row['dataset']:row for row in rows if row['case']==case} for case in cases}
    baseline={row['dataset']:row for row in rows if row['case']=='immediate_t1_blur'}
    scores=[]
    for case,g in grouped.items():
        assert set(g)==set(common.SCENES)
        scores.append({'case':case,'mean_psnr':sum(r['psnr'] for r in g.values())/len(g),
            'mean_mapping_seconds':sum(r['mapping_seconds'] for r in g.values())/len(g),
            'worst_scene_delta':min(g[d]['psnr']-baseline[d]['psnr'] for d in g)})
    eligible=[s for s in scores if s['worst_scene_delta']>=-.05]
    if not eligible:raise RuntimeError('Baseline must remain eligible')
    peak=max(s['mean_psnr'] for s in eligible)
    tied=[s for s in eligible if s['mean_psnr']>=peak-.02]
    best=min(tied,key=lambda s:(s['mean_mapping_seconds'],s['case']))
    return {'selected':best['case'],'scores':scores,'rule':'per-scene drop <=0.05 dB vs blur baseline; within0.02dB of best mean choose fastest'}

def audit_run(out,dataset,config):
    quotas=(3,3,6)
    x=common.read(out/'render_result.json');old=common.read(prior.CONTROL/dataset/'render_result.json')
    ra=common.read(out/'render_audit.json');training=[r for r in ra if r['grad_enabled']]
    assert x['valid_execution'] and all(x['checks'].values())
    assert x['schedule']=='unified' and x['native_commits']==0
    assert x['render_counts']==old['render_counts']
    assert len(training)==40*x['kf_render_budget']['kf_admissions']
    assert x['kf_render_budget']['admissions']==old['kf_render_budget']['admissions']
    assert all(r['backward'] and r['uid']<=r['arrival_uid'] for r in training)
    assert all(r['uid']<=r['arrival_uid'] for r in ra)
    assert [(r['uid'],r['training_renders'],r['all_renders']) for r in x['render_prefixes']]==[
        (r['uid'],r['training_renders'],r['all_renders']) for r in old['render_prefixes']]
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
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--reuse-baseline',type=Path);args=p.parse_args()
    args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=False)
    common.write(args.output/'protocol.json',{'stages':{'kappa':[None,4,8,16],'tau':[.25,1.,4.],'final_blur':[True,False]},
        'renders_per_kf':40,'optimizer_batch_size':1,'batch_quotas':[3,3,6],'seed':0,
        'growth_scope':'dense_only','entropy_weight':'tau/N separately per pool',
        'blur':{'energy_ratio':.8,'frequency_ratio':.9},'scenes':common.SCENES,
        'selection':'per-scene delta >= -0.05 vs immediate tau1 blur; within0.02dB of top mean use lowest mean time',
        'actual_tracking':False,'reference':str(REFERENCE),'not_exhaustive_joint_search':True})
    backend=Path('/home/intern/VIGS-SLAM-online-worker-integration')
    files=list((backend/'vigs').rglob('*.py'))+[Path(__file__).resolve(),HERE/'run_unified_batch_panel.py',
        HERE/'run_cumulative_ervs_panel.py',HERE/'run_kf15_render_worker.py',HERE/'run_arrived_online_worker.py',
        HERE/'render_work_audit.py',HERE/'densify_prune_ablation_audit.py',HERE/'test_unified_growth.py',HERE/'test_unified_view_training.py']
    source=args.output/'source';source.mkdir();lock={}
    for path in files:
        digest=common.sha(path);dest=source/(digest[:12]+'_'+path.name);dest.write_bytes(path.read_bytes())
        lock[str(path)]={'sha256':digest,'copy':str(dest)}
    common.write(args.output/'source_lock.json',lock)
    env=trial.environment();env['EXP78B_CUSTOM_ROOT']=str(backend)
    env['PYTHONPATH']=str(backend/'vigs')+':'+str(backend)+':'+env['PYTHONPATH']
    base=trial.ROOT/'live_worker_integration_audit';rows=[];configs={}
    def run_case(case,config):
        configs[case]=config;common.write(args.output/'cases.json',configs)
        for dataset,scene in common.SCENES.items():
            trial.common.evaluation.panel.v2.gpu_idle()
            out=args.output/case/dataset;out.parent.mkdir(parents=True,exist_ok=True)
            setup=base/('v5_packet_identity/aria_setup' if dataset=='aria' else f'v9_productive_worker/three_scene/{dataset}_setup')
            cmd=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(HERE/'run_kf15_render_worker.py'),
                '--setup',str(setup),'--extensions',str(base/'v6_current_stream_extensions'),
                '--output',str(out),'--renders-per-kf','40','--seed','0',
                '--membership','immediate' if config['kappa'] is None else 'growth',
                '--kappa',str(config['kappa'] or 64),'--tau',str(config['tau']),
                '--growth-budget-scope','dense_only','--selector','ervs','--schedule','unified',
                '--selection-count-scope','all_rgb','--batch-quotas','3','3','6','--disable-densify-prune',
                '--optimizer-batch-size','1','--unified-scale-projection','--reference',str(REFERENCE/dataset/'render_result.json')]
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
                 'final_pool':({k:len(x['training']['generations'][-1]['policy'][k]) for k in ('keyframes','offered_dense','admitted_dense')} if x else None),
                 'dense_prepared':len(set(x['deferred_audit']['prepared_uids'])) if x else None}
            rows.append(row);common.write(args.output/'progress.json',rows);journal(row)
            print('DONE',case,dataset,'PSNR',row['psnr'],'audit',row['audit_pass'],flush=True)
            if not valid or not row['audit_pass'] or changed or error:raise RuntimeError('Invalid run: '+str(row))
    kcases=[]
    for k in (None,4,8,16):
        name=('immediate' if k is None else f'k{k}')+'_t1_blur';kcases.append(name)
        config={'kappa':k,'tau':1.,'blur':True}
        if k is None and args.reuse_baseline:
            previous=common.read(args.reuse_baseline/'progress.json')
            reused=[r for r in previous if r['case']==name]
            assert len(reused)==3 and {r['dataset'] for r in reused}==set(common.SCENES)
            configs[name]=config;common.write(args.output/'cases.json',configs)
            original_lock=common.read(args.reuse_baseline/'source_lock.json')
            changed=[path for path,v in original_lock.items() if common.sha(Path(path))!=v['sha256']]
            assert set(changed)<={str(backend/'vigs/online_mapper_runtime.py'),str(Path(__file__).resolve())}, changed
            for row in reused:
                assert row['valid_execution'] and row['audit_pass'] and row['evaluation']['pass'] and not row['error'] and not row['source_changed']
                audit_run(Path(row['output']),row['dataset'],config)
                rows.append({**row,'reused_from':str(args.reuse_baseline.resolve()),'baseline_source_differences':changed})
            common.write(args.output/'baseline_reuse.json',{'from':str(args.reuse_baseline.resolve()),'source_differences':changed,
                'reason':'only runtime growth authorization guard and panel orchestration changed; immediate path unchanged and CPU runtime regression passed'})
            common.write(args.output/'progress.json',rows);print('REUSED_BASELINE',flush=True)
        else:
            run_case(name,config)
    ks=select_case(rows,kcases);common.write(args.output/'kappa_selection.json',ks);print('KAPPA_SELECTION',ks,flush=True)
    winner=ks['selected'];tcases=[winner]
    for tau in (.25,4.):
        name=winner.replace('_t1_',f'_t{tau:g}_');tcases.append(name)
        run_case(name,{**configs[winner],'tau':tau})
    ts=select_case(rows,kcases+tcases[1:]);common.write(args.output/'tau_selection.json',ts);print('TAU_SELECTION',ts,flush=True)
    winner=ts['selected'];off=winner.replace('_blur','_no_blur')
    run_case(off,{**configs[winner],'blur':False})
    final=select_case(rows,kcases+tcases[1:]+[off]);common.write(args.output/'final_selection.json',final)
    common.write(args.output/'summary.json',rows);print('TUNING_COMPLETE',final,flush=True)

if __name__=='__main__':main()
