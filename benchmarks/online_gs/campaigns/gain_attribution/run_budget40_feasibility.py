#!/usr/bin/env python3
"""Current vanilla/paired, exact40 work then actual-live40 cap; no new policy."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import run_online_dense_training as trial

HERE=Path(__file__).resolve().parent
CARD='campaigns/06_gain_attribution/render_budget40_feasibility/README.md'
SCENES={'aria':'aria1253','rpng':'table_06','utmm':'square-1'}


def write(p,x):
    p.write_text(json.dumps(x,indent=2,default=str)+'\n')


def journal(row):
    msg=(f"**2026-09-25 (40 renders/KF / {row['phase']} / {row['dataset']} / {row['arm']}):** "
         f"execution={row['valid_execution']}, PSNR={row['psnr']}. Result={row['output']}")
    card=trial.BASE.WORKSPACE/'context/experiments'/CARD
    with card.open('a') as f:
        f.write('\n'+msg+'\n\n```json\n'+json.dumps(row,indent=2,default=str)+'\n```\n')
    for file,head,link in [('context/STATUS.md','## 최근 흐름 (최신순)\n','experiments/'+CARD),
                          ('context/experiments/INDEX.md','# Experiment Index\n',CARD)]:
        p=trial.BASE.WORKSPACE/file;s=p.read_text();assert head in s
        p.write_text(s.replace(head,head+'\n- '+msg+' → [카드]('+link+')\n',1))


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--phases',nargs='+',choices=['fixed','live'],default=['fixed','live'])
    p.add_argument('--datasets',nargs='+',choices=list(SCENES),default=list(SCENES))
    a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
    write(a.output/'protocol.json',{'renders_per_kf':40,'phases':a.phases,'datasets':a.datasets,
        'seed':0,'architecture':'current paired, no changes to idle gate/role allocation/selection',
        'fixed':'same causal poses/events and exact prefix work; no live timing claim',
        'live':'actual tracking, original timestamps1x, frontend4/2, IMU prediction20/20/15, zero optimizer tail'})
    backend=Path('/home/intern/VIGS-SLAM-online-worker-integration')
    custom=trial.environment();custom['EXP78B_CUSTOM_ROOT']=str(backend)
    custom['PYTHONPATH']=str(backend/'vigs')+':'+str(backend)+':'+custom['PYTHONPATH']
    official=trial.BASE.mapping_environment(False)
    official['PYTHONPATH']=str(trial.BASE.WORKSPACE/'benchmarks/online_gs')+':'+official['PYTHONPATH']
    base=trial.ROOT/'live_worker_integration_audit'
    sources=[Path(__file__).resolve(),HERE/'run_kf15_render_worker.py',HERE/'run_kf15_vanilla.py',
             HERE/'measure_live_render_capacity.py',HERE/'measure_vanilla_live_capacity.py',
             HERE/'keyframe_render_budget.py',HERE/'render_work_audit.py']+list((backend/'vigs').glob('*.py'))
    source=a.output/'source';source.mkdir();lock={}
    for file in sources:
        data=file.read_bytes();sha=hashlib.sha256(data).hexdigest();dest=source/(sha[:12]+'_'+file.name)
        dest.write_bytes(data);lock[str(file)]={'sha256':sha,'copy':str(dest)}
    write(a.output/'source_lock.json',lock)
    rows=[]
    for phase in a.phases:
        phase_rows=[];phase_root=a.output/phase;phase_root.mkdir()
        for dataset in a.datasets:
            scene=SCENES[dataset]
            for arm in (['paired','vanilla'] if phase=='fixed' else ['vanilla','paired']):
                trial.common.evaluation.panel.v2.gpu_idle()
                out=phase_root/dataset/arm;out.parent.mkdir(parents=True,exist_ok=True)
                if phase=='fixed':
                    runner=HERE/('run_kf15_render_worker.py' if arm=='paired' else 'run_kf15_vanilla.py')
                    cmd=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(runner),'--output',str(out),'--renders-per-kf','40','--seed','0']
                    if arm=='paired':
                        setup=base/('v5_packet_identity/aria_setup' if dataset=='aria' else f'v9_productive_worker/three_scene/{dataset}_setup')
                        cmd+=['--setup',str(setup),'--extensions',str(base/'v6_current_stream_extensions'),
                              '--membership','immediate','--selector','ervs','--schedule','paired_kf_dense']
                    else:
                        cmd+=['--dataset',dataset,'--scene',scene,'--reference',str(out.parent/'paired/render_result.json')]
                    env=custom if arm=='paired' else official
                else:
                    runner=HERE/('measure_live_render_capacity.py' if arm=='paired' else 'measure_vanilla_live_capacity.py')
                    cmd=[sys.executable,str(runner),'--dataset',dataset,'--renders-per-kf','40','--output',str(out)]
                    env=None
                write(out.parent/(arm+'_command.json'),cmd)
                print('START',phase,dataset,arm,flush=True)
                with (out.parent/(arm+'_launcher.log')).open('x') as f:
                    code=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
                path=out/('render_result.json' if phase=='fixed' else 'result.json')
                runtime=json.loads(path.read_text()) if path.exists() else None
                if phase=='fixed':
                    valid=bool(code==0 and runtime and runtime['valid_execution'])
                else:
                    valid=bool(code==0 and runtime and not runtime.get('error') and runtime['source_unchanged']
                               and runtime['tracked_frames']==runtime['input_frames'] and runtime['zero_tail_observed'])
                evaluation=None;error=None
                if valid:
                    try:
                        evaluation=trial.common.evaluation.panel.run_evaluation_twice(
                            out,dataset,scene,trial.BASE.sequence_paths(dataset,scene)['fixed_manifest'])
                    except Exception as e:
                        error=repr(e);write(out/'evaluation_error.json',{'error':error})
                changed=[f for f,v in lock.items() if hashlib.sha256(Path(f).read_bytes()).hexdigest()!=v['sha256']]
                row={'phase':phase,'dataset':dataset,'scene':scene,'arm':arm,'seed':0,'output':str(out),
                     'returncode':code,'valid_execution':valid,'evaluation':evaluation,'evaluation_error':error,
                     'psnr':evaluation['fixed_psnr_first'] if evaluation and evaluation['pass'] else None,
                     'source_changed':changed}
                if phase=='fixed' and runtime:
                    row.update(mapping_seconds=runtime['mapping_seconds'],renders=runtime['render_counts'],checks=runtime['checks'])
                else:row['runtime']=runtime
                rows.append(row);phase_rows.append(row)
                write(a.output/'progress.json',rows);write(phase_root/'summary.json',phase_rows);journal(row)
                print('DONE',phase,dataset,arm,'valid',valid,'PSNR',row['psnr'],flush=True)
                if changed or not valid or row['psnr'] is None:
                    raise RuntimeError('Invalid run; preserve artifacts and inspect before continuing')
        if phase=='live':
            subprocess.run([sys.executable,str(HERE/'analyze_live_capacity_comparison.py'),'--panel',str(phase_root)],check=True,stdout=subprocess.DEVNULL)
    write(a.output/'summary.json',rows)
    print('FEASIBILITY_PANEL_COMPLETE',flush=True)


if __name__=='__main__':main()
