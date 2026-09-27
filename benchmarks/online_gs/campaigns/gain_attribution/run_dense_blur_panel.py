#!/usr/bin/env python3
"""Same-work blur admission and no-dense controls, without scene tuning."""
import argparse
from collections import Counter
from pathlib import Path
import subprocess
import run_unified_batch_panel as prior
common=prior.common; trial=common.trial; ROOT=prior.ROOT; HERE=prior.HERE
REFERENCE=ROOT/'results/campaigns/gain_attribution/unified_batch/projected_v1/336m1p'
CARD='campaigns/06_gain_attribution/dense_blur_filter/README.md'
CASES={'off':(3,3,6),'on':(3,3,6),'no_dense':(3,9,0)}


def journal(row):
    message=(f"**2026-09-26 dense blur {row['case']} / {row['dataset']}:** execution={row['valid_execution']}, "
             f"audit={row['audit_pass']}, PSNR={row['psnr']}, error={row['error']}; {row['output']}.")
    with (ROOT/'context/experiments'/CARD).open('a') as f:f.write('\n'+message+'\n')
    for name,heading,link in [('context/STATUS.md','## 최근 흐름 (최신순)\n','experiments/'+CARD),
                             ('context/experiments/INDEX.md','# Experiment Index\n',CARD)]:
        p=ROOT/name;s=p.read_text();assert heading in s
        p.write_text(s.replace(heading,heading+'\n- '+message+' → [카드]('+link+')\n',1))


def audit_run(out,dataset,case):
    audit=prior.audit_run(out,dataset,CASES[case],'336m1p' if case=='off' else case)
    x=common.read(out/'render_result.json');old=common.read(REFERENCE/dataset/'render_result.json')
    assert x['unified_scale_projection']['enabled'] and x['unified_scale_projection']['calls']>0
    assert x['main_optimizer_steps']==x['render_counts']['backward']
    gate=x['dense_blur_filter'];assert gate['enabled']==(case=='on')
    if case=='off':
        for a,b in zip(x['training']['generations'],old['training']['generations']):
            assert a['services']==b['services']
    if case=='no_dense':
        assert audit['role_renders'].get('dense',0)==0
        assert not x['deferred_audit']['prepared_uids']
    rejected=set()
    if case=='on':
        observed={r['uid'] for r in x['arrivals']}
        for d in gate['decisions']:
            assert d['left']<d['uid']<d['right']
            assert all(u in observed and u<=d['right'] for u in d['reference_uids'])
            s=d['score'];r=d['reference']
            reject=(s['laplacian_energy']<gate['energy_ratio']*r['laplacian_energy'] and
                    s['high_frequency_ratio']<gate['frequency_ratio']*r['high_frequency_ratio'])
            assert d['accepted']==(not reject)
            if reject:rejected.add(d['uid'])
        assert len(rejected)==gate['rejected_images']
        for g in x['training']['generations']:
            assert not rejected.intersection(g['policy']['admitted_dense'])
            for s in g['services']:
                assert not rejected.intersection(u for u,r in zip(s['uids'],s['roles']) if r=='dense')
        assert not rejected.intersection(x['deferred_audit']['prepared_uids'])
    audit.update(blur_decisions_verified=True,rejected_never_used_as_dense=True,
                 rejected=len(rejected),blur_seconds=gate.get('seconds',0.))
    return audit


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cases',nargs='+',choices=list(CASES),default=list(CASES))
    p.add_argument('--scenes',nargs='+',choices=list(common.SCENES),default=list(common.SCENES))
    p.add_argument('--blur-energy-ratio',type=float,default=.8)
    p.add_argument('--blur-frequency-ratio',type=float,default=.9)
    args=p.parse_args();args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=False)
    common.write(args.output/'protocol.json',{'cases':{k:CASES[k] for k in args.cases},
        'scenes':{k:common.SCENES[k] for k in args.scenes},'renders_per_kf':40,'seed':0,
        'optimizer_batch_size':1,'scale_projection':True,'densify_prune':False,
        'blur_thresholds':{'energy_ratio':args.blur_energy_ratio,'frequency_ratio':args.blur_frequency_ratio,'reference_quantile':.75},
        'thresholds_predeclared':True,'no_dense':'dense renders replaced by full KF ERVS',
        'actual_tracking':False,'reference':str(REFERENCE)})
    backend=Path('/home/intern/VIGS-SLAM-online-worker-integration')
    files=list((backend/'vigs').rglob('*.py'))+[Path(__file__).resolve(),HERE/'run_unified_batch_panel.py',
        HERE/'run_cumulative_ervs_panel.py',HERE/'run_kf15_render_worker.py',HERE/'run_arrived_online_worker.py',
        HERE/'render_work_audit.py',HERE/'densify_prune_ablation_audit.py',HERE/'test_dense_blur_filter.py']
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
                '--optimizer-batch-size','1','--unified-scale-projection',
                '--reference',str(REFERENCE/dataset/'render_result.json')]
            if case=='on':cmd.extend(['--dense-blur-filter','--blur-energy-ratio',str(args.blur_energy_ratio),
                                     '--blur-frequency-ratio',str(args.blur_frequency_ratio)])
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
                 'blur_summary':({k:v for k,v in x['dense_blur_filter'].items() if k!='decisions'} if x else None)}
            rows.append(row);common.write(args.output/'progress.json',rows);journal(row)
            print('DONE',case,dataset,'PSNR',row['psnr'],'audit',row['audit_pass'],flush=True)
            if not valid or not row['audit_pass'] or changed or error:raise RuntimeError('Invalid run: '+str(row))
    common.write(args.output/'summary.json',rows);print('BLUR_PANEL_COMPLETE',flush=True)


if __name__=='__main__':main()
