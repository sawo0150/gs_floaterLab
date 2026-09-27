#!/usr/bin/env python3
"""Replace dense slots by KF RGB-only; isolate loss routing with a matched KF native control."""
import argparse
from collections import Counter
from pathlib import Path
import subprocess
import run_unified_batch_panel as prior
common=prior.common; trial=common.trial; ROOT=prior.ROOT; HERE=prior.HERE
REFERENCE=ROOT/'results/campaigns/gain_attribution/unified_batch/projected_v1/336m1p'
CARD='campaigns/06_gain_attribution/kf_rgb_control/README.md'
CASES={mode:(3,3,6) for mode in ('dense_rgb','kf_native','kf_rgb')}


def journal(row):
    message=(f"**2026-09-26 KF RGB control {row['case']} / {row['dataset']}:** execution={row['valid_execution']}, "
             f"audit={row['audit_pass']}, PSNR={row['psnr']}, error={row['error']}; {row['output']}.")
    with (ROOT/'context/experiments'/CARD).open('a') as f:f.write('\n'+message+'\n')
    for name,heading,link in [('context/STATUS.md','## 최근 흐름 (최신순)\n','experiments/'+CARD),
                             ('context/experiments/INDEX.md','# Experiment Index\n',CARD)]:
        p=ROOT/name;s=p.read_text();assert heading in s
        p.write_text(s.replace(heading,heading+'\n- '+message+' → [카드]('+link+')\n',1))


def audit_run(out,dataset,case):
    quotas=CASES[case]
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
        assert p['batch_quotas']==list(quotas) and set(p['admitted_dense'])==set(p['offered_dense'])
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
    assert not x['dense_blur_filter']['enabled']
    expected=[]
    for g in x['training']['generations']:
        assert g['policy']['auxiliary_mode']==case
        for service in g['services']:
            for uid,role in zip(service['uids'],service['roles']):
                expected.append({'generation':g['policy']['generation'], 'uid':uid, 'role':role,
                    'loss':'rgb_only' if role in ('dense','keyframe_rgb') else 'native_rgbd_normal'})
    assert x['training']['loss_routes']==expected, 'Actual loss routing disagrees with assigned slots'
    assert [r['uid'] for r in training]==[r['uid'] for r in expected]
    if case!='dense_rgb':
        assert not x['deferred_audit']['prepared_uids']
        assert not roles['dense']
    else:
        reference=common.read(REFERENCE/dataset/'render_result.json')
        assert [g['services'] for g in x['training']['generations']]==[g['services'] for g in reference['training']['generations']]
    same_selection_and_lr=None
    if case=='kf_rgb':
        native=common.read(out.parent.parent/'kf_native'/dataset/'render_result.json')
        strip_time=lambda rows:[{k:v for k,v in r.items() if k!='seconds'} for r in rows]
        assert strip_time(x['render_prefixes'])==strip_time(native['render_prefixes'])
        assert len(x['training']['generations'])==len(native['training']['generations'])
        for ga,gb in zip(x['training']['generations'],native['training']['generations']):
            normalize=lambda g:[{**s,'roles':['auxiliary' if r.startswith('keyframe_') else r for r in s['roles']],
                'pool_sizes':{('auxiliary' if r.startswith('keyframe_') else r):n for r,n in s['pool_sizes'].items()}} for s in g['services']]
            assert normalize(ga)==normalize(gb), 'KF control selection/batches/LR/counts differ'
        same_selection_and_lr=True
    return {'pass':True,'one_packet_per_arrival':True,'separate_native_optimizer_steps':0,
            'kf_control_identical_selection_batches_counts_lr':same_selection_and_lr,
            'actual_loss_routes_verified':True, 'loss_renders':dict(Counter(r['loss'] for r in expected)),
            'scale_projection':x.get('unified_scale_projection'),
            'same_prefix_renders_poses_events_cohort':True,'cumulative_counts_verified':True,
            'densify_prune_off':True,'training_renders':len(training),'optimizer_steps':services,
            'role_renders':dict(roles),'batch_size_histogram':dict(sizes)}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cases',nargs='+',choices=list(CASES),default=list(CASES))
    p.add_argument('--scenes',nargs='+',choices=list(common.SCENES),default=list(common.SCENES))
    args=p.parse_args();args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=False)
    common.write(args.output/'protocol.json',{'cases':{k:CASES[k] for k in args.cases},
        'scenes':{k:common.SCENES[k] for k in args.scenes},'renders_per_kf':40,'seed':0,
        'optimizer_batch_size':1,'scale_projection':True,'densify_prune':False,
        'blur_filter':False,'auxiliary_modes':['dense_rgb','kf_native','kf_rgb'],
        'design':'KF controls have identical selected images/order/LR; only auxiliary loss changes',
        'actual_tracking':False,'reference':str(REFERENCE)})
    backend=Path('/home/intern/VIGS-SLAM-online-worker-integration')
    files=list((backend/'vigs').rglob('*.py'))+[Path(__file__).resolve(),HERE/'run_unified_batch_panel.py',
        HERE/'run_cumulative_ervs_panel.py',HERE/'run_kf15_render_worker.py',HERE/'run_arrived_online_worker.py',
        HERE/'render_work_audit.py',HERE/'densify_prune_ablation_audit.py',HERE/'test_kf_rgb_control.py']
    source=args.output/'source';source.mkdir();lock={}
    for path in files:
        digest=common.sha(path);dest=source/(digest[:12]+'_'+path.name);dest.write_bytes(path.read_bytes())
        lock[str(path)]={'sha256':digest,'copy':str(dest)}
    common.write(args.output/'source_lock.json',lock)
    env=trial.environment();env['EXP78B_CUSTOM_ROOT']=str(backend)
    env['PYTHONPATH']=str(backend/'vigs')+':'+str(backend)+':'+env['PYTHONPATH']
    base=trial.ROOT/'live_worker_integration_audit';rows=[]
    for dataset in args.scenes:
        scene=common.SCENES[dataset]
        for case in args.cases:
            trial.common.evaluation.panel.v2.gpu_idle()
            out=args.output/case/dataset;out.parent.mkdir(parents=True,exist_ok=True)
            setup=base/('v5_packet_identity/aria_setup' if dataset=='aria' else f'v9_productive_worker/three_scene/{dataset}_setup')
            cmd=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(HERE/'run_kf15_render_worker.py'),
                '--setup',str(setup),'--extensions',str(base/'v6_current_stream_extensions'),
                '--output',str(out),'--renders-per-kf','40','--seed','0','--membership','immediate',
                '--selector','ervs','--schedule','unified','--selection-count-scope','all_rgb',
                '--batch-quotas',*[str(n) for n in CASES[case]],'--disable-densify-prune',
                '--optimizer-batch-size','1','--unified-scale-projection','--auxiliary-mode',case,
                '--reference',str(REFERENCE/dataset/'render_result.json')]
            common.write(out.parent/(dataset+'_command.json'),cmd);print('START',case,dataset,flush=True)
            with (out.parent/(dataset+'_launcher.log')).open('x') as log:
                code=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
            x=common.read(out/'render_result.json') if (out/'render_result.json').exists() else None
            valid=bool(code==0 and x and x['valid_execution']);evaluation=audit=None;error=None
            if valid:
                try:
                    evaluation=trial.common.evaluation.panel.run_evaluation_twice(out,dataset,scene,
                        trial.BASE.sequence_paths(dataset,scene)['fixed_manifest'])
                    assert evaluation['pass'];audit=audit_run(out,dataset,case)
                    common.write(out/'independent_audit.json',audit)
                except Exception as exc:error=repr(exc)
            changed=[path for path,v in lock.items() if common.sha(Path(path))!=v['sha256']]
            row={'case':case,'dataset':dataset,'scene':scene,'output':str(out),'returncode':code,
                 'valid_execution':valid,'audit_pass':bool(audit and audit['pass']),'error':error,
                 'evaluation':evaluation,'source_changed':changed,'audit':audit,
                 'psnr':evaluation['fixed_psnr_first'] if evaluation and evaluation['pass'] else None,
                 'mapping_seconds':x['mapping_seconds'] if x else None,
                 'optimizer_steps':x['main_optimizer_steps'] if x else None}
            rows.append(row);common.write(args.output/'progress.json',rows);journal(row)
            print('DONE',case,dataset,'PSNR',row['psnr'],'audit',row['audit_pass'],flush=True)
            if not valid or not row['audit_pass'] or changed or error:raise RuntimeError('Invalid run: '+str(row))
    common.write(args.output/'summary.json',rows);print('KF_RGB_PANEL_COMPLETE',flush=True)


if __name__=='__main__':main()
