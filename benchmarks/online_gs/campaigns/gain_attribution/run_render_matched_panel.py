#!/usr/bin/env python3
"""Prefix-matched render work, using unchanged legacy and paired runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import run_online_dense_training as trial


def write(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n')


def journal(row):
    card=trial.BASE.WORKSPACE/'context/experiments/campaigns/06_gain_attribution/render_matched/README.md'
    detail=(f"{row['psnr']:.6f}dB, mapping {row['mapping_seconds']:.3f}s" if row['psnr'] is not None
            else '실행/평가 실패; 원본 보존')
    msg=f"**2026-09-25 (render-matched / {row['dataset']} / {row['arm']} / seed{row['seed']}):** {detail}."
    with card.open('a') as f:
        f.write('\n'+msg+'\n\n```json\n'+json.dumps(row,indent=2)+'\n```\n')
    for file,heading,link in [('context/STATUS.md','## 최근 흐름 (최신순)\n','experiments/campaigns/06_gain_attribution/render_matched/README.md'),
                              ('context/experiments/INDEX.md','# Experiment Index\n','campaigns/06_gain_attribution/render_matched/README.md')]:
        path=trial.BASE.WORKSPACE/file;text=path.read_text()
        if heading not in text:raise RuntimeError('Missing journal heading')
        path.write_text(text.replace(heading,heading+'\n- '+msg+' → [카드]('+link+')\n',1))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seeds',nargs='+',type=int,default=[0])
    p.add_argument('--arms',nargs='+',choices=['legacy_growth','paired'],
                   default=['legacy_growth','paired'])
    args=p.parse_args()
    if args.arms!=['legacy_growth','paired']:raise ValueError('Run baseline then paired')
    args.output.mkdir(parents=True,exist_ok=False)
    base=trial.ROOT/'live_worker_integration_audit'
    backend=Path('/home/intern/VIGS-SLAM-online-worker-integration')
    env=trial.environment();env['EXP78B_CUSTOM_ROOT']=str(backend)
    env['PYTHONPATH']=str(backend/'vigs')+':'+str(backend)+':'+env['PYTHONPATH']
    runner=Path(__file__).with_name('run_render_matched_worker.py').resolve()
    snapshot=args.output/'implementation';snapshot.mkdir()
    sources=list((backend/'vigs').glob('*.py'))+list((backend/'tests').glob('test_*.py'))
    sources += [runner,Path(__file__).resolve(),Path(__file__).with_name('arrived_input_boundary.py').resolve(),
                Path(__file__).with_name('test_arrived_input_boundary.py').resolve(),
                Path(__file__).with_name('render_work_audit.py').resolve(),
                Path(__file__).with_name('test_render_work_audit.py').resolve(),
                Path(__file__).with_name('run_arrived_online_worker.py').resolve(),
                backend/'vigs/gaussian/utils/slam_utils.py',backend/'vigs/gaussian/utils/loss_utils.py']
    lock={}
    for f in sources:
        digest=hashlib.sha256(f.read_bytes()).hexdigest();target=snapshot/(digest[:12]+'_'+f.name)
        shutil.copy2(f,target);lock[str(f)]={'sha256':digest,'copy':str(target)}
    write(snapshot/'index.json',lock)
    write(args.output/'protocol.json',{'scenes':['aria1253','table_06','square-1'],'seeds':args.seeds,
        'arms':args.arms,'time_scale':None,'post_eos_updates':0,'concurrent_tracking':False,
        'work_budget':'Equal differentiable camera renders at EVERY arrival prefix; native and additional included',
        'reference_quota':'Prior v2 legacy additional-step completions binned by arrived uid; no PSNR-based tuning',
        'claim':'Fixed-work causal diagnostic, NOT strict 1.5x live timing; losses retained per arm',
        'paired':{'native':'recent KF window only, original losses and topology',
                  'additional':'KF RGBD+normal once, dense RGB once, separate role ERVS',
                  'membership':'all causally available training views; no capacity gate',
                  'counts':'recent refinement selections per role','entropy_weight':'1/N per role',
                  'interruption':'retain turn across inputs; never finish pair after EOS'},
        'comparison':'PSNR differences reported without presuming equivalence or improvement'})
    rows=[]
    for seed in args.seeds:
        for dataset,scene in [('aria','aria1253'),('rpng','table_06'),('utmm','square-1')]:
            setup=base/('v5_packet_identity/aria_setup' if dataset=='aria'
                        else f'v9_productive_worker/three_scene/{dataset}_setup')
            for arm in args.arms:
                trial.common.evaluation.panel.v2.gpu_idle()
                output=args.output/dataset/arm/f'seed{seed}';output.parent.mkdir(parents=True,exist_ok=True)
                paired=arm!='legacy_growth'
                membership='growth' if not paired else 'kf_only' if arm=='paired_kf_only' else 'immediate'
                command=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(runner),
                    '--setup',str(setup),'--extensions',str(base/'v6_current_stream_extensions'),
                    '--output',str(output),'--membership',membership,'--selector','ervs',
                    '--schedule','paired_kf_dense' if paired else 'mixed','--seed',str(seed)]
                clock_ref=trial.BASE.WORKSPACE/f'results/campaigns/gain_attribution/paired_full_pool/v2/{dataset}/legacy_growth/seed{seed}/worker_result.json'
                command+=['--clock-reference',str(clock_ref)]
                if paired:
                    reference=args.output/dataset/'legacy_growth'/f'seed{seed}'/'render_result.json'
                    command+=['--reference',str(reference)]
                write(output.parent/f'command_seed{seed}.json',command)
                print('START',dataset,arm,seed,flush=True)
                with (output.parent/f'mapping_seed{seed}.log').open('x') as log:
                    result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
                path=output/'render_result.json';runtime=json.loads(path.read_text()) if path.exists() else None
                evaluation=None
                if result.returncode==0 and runtime and runtime['valid_execution']:
                    evaluation=trial.common.evaluation.panel.run_evaluation_twice(
                        output,dataset,scene,trial.BASE.sequence_paths(dataset,scene)['fixed_manifest'])
                for f,entry in lock.items():
                    if hashlib.sha256(Path(f).read_bytes()).hexdigest()!=entry['sha256']:
                        raise RuntimeError('Source changed during panel: '+f)
                row={'dataset':dataset,'scene':scene,'arm':arm,'seed':seed,
                     'output':str(output),'returncode':result.returncode,
                     'valid':bool(runtime and runtime['valid_execution'] and evaluation and evaluation['pass']),
                     'psnr':evaluation['fixed_psnr_first'] if evaluation else None,
                     'mapping_seconds':runtime['mapping_seconds'] if runtime else None}
                if runtime:
                    final=runtime['training']['generations'][-1]
                    row['final_map']={'keyframes':len(final['policy']['keyframes']),
                        'dense_admitted':len(final['policy']['admitted_dense']),
                        'role_commits':final['policy'].get('role_commits'),
                        'native_steps':sum(s['source']=='native' for s in final['services'])}
                    row['checks']=runtime['checks']
                    row['renders']=runtime['render_counts']
                    row['native_steps']=runtime['native_commits']
                    row['additional_steps']=runtime['photometric_commits']
                    row['clock_budget']=runtime['former_clock_budget_seconds']
                    if paired:
                        baseline=next(r for r in rows if r['dataset']==dataset and r['seed']==seed and r['arm']=='legacy_growth')
                        row['delta_psnr']=row['psnr']-baseline['psnr'] if row['psnr'] is not None else None
                        if row['renders']['training']!=baseline['renders']['training']:raise RuntimeError('Unequal rendering counts')
                rows.append(row);write(args.output/'progress.json',rows);journal(row)
                print('DONE',json.dumps(row),flush=True)
                if not row['valid']:raise RuntimeError('Invalid arm; inspect preserved evidence')
    print('PANEL_COMPLETE',flush=True)


if __name__=='__main__':main()
