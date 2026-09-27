#!/usr/bin/env python3
"""Common-worker candidate/KF control with whole-clock and repeated evaluation."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import run_online_dense_training as trial


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--setup',required=True,type=Path)
    p.add_argument('--extensions',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--seed',type=int,default=0)
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    identity=json.loads((args.setup/'provenance.json').read_text())
    dataset,scene=identity['dataset'],identity['scene']
    backend=Path('/home/intern/VIGS-SLAM-online-worker-integration')
    env=trial.environment();env['EXP78B_CUSTOM_ROOT']=str(backend)
    env['PYTHONPATH']=str(backend/'vigs')+':'+str(backend)+':'+env['PYTHONPATH']
    rows=[]
    for membership in ('growth','kf_only'):
        trial.common.evaluation.panel.v2.gpu_idle()
        output=(args.output/membership/f'seed{args.seed}').resolve()
        output.parent.mkdir(parents=True)
        command=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(Path(__file__).with_name('run_arrived_online_worker.py').resolve()),
            '--setup',str(args.setup.resolve()),'--extensions',str(args.extensions.resolve()),
            '--output',str(output),'--membership',membership,'--selector','ervs','--seed',str(args.seed)]
        (output.parent/'command.json').write_text(json.dumps(command,indent=2))
        print('START',dataset,scene,membership,flush=True)
        with (output.parent/'mapping.log').open('w') as log:
            ret=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
        runtime=json.loads((output/'worker_result.json').read_text()) if (output/'worker_result.json').exists() else None
        evaluation=None
        if ret==0 and runtime and runtime['valid_execution']:
            evaluation=trial.common.evaluation.panel.run_evaluation_twice(
                output,dataset,scene,trial.BASE.sequence_paths(dataset,scene)['fixed_manifest'])
        row={'membership':membership,'seed':args.seed,'returncode':ret,
            'valid_execution':bool(runtime and runtime['valid_execution']),
            'mapping_seconds':runtime['mapping_seconds'] if runtime else None,
            'heldout_psnr':evaluation['fixed_psnr_first'] if evaluation else None,
            'evaluation_consistent':evaluation['pass'] if evaluation else False,
            'strict_tracking_claim':False,'output':str(output)}
        rows.append(row)
        (args.output/'pair_progress.json').write_text(json.dumps(rows,indent=2))
        print('DONE',json.dumps(row),flush=True)
        card=trial.BASE.WORKSPACE/'context/experiments/campaigns/06_gain_attribution/online_dense_training/README.md'
        detail=(f"{row['heldout_psnr']:.6f}dB, whole mapping {row['mapping_seconds']:.3f}s; "
                '실행계약/독립이중평가PASS' if evaluation else f'실패(exit {ret}); 로그와 상태 보존')
        with card.open('a') as f:f.write(f'\n### Arrived worker {dataset}/{scene}/{membership}/seed{args.seed}\n\n{detail}. '
            f'동일 ERVS를 사용한 dense 포함/제외 비교. Frozen causal tracker inputs; concurrent tracking claim 없음. Artifact: `{output}`.\n')
        msg=f'**2026-09-25 (actual mapper worker / {dataset} {scene} {membership}):** {detail}. seed{args.seed}; 반복/교차장면/수렴/논문정렬 목표미완.'
        for filename,heading,link in [('context/STATUS.md','## 최근 흐름 (최신순)\n','experiments/campaigns/06_gain_attribution/online_dense_training/README.md'),('context/experiments/INDEX.md','# Experiment Index\n','campaigns/06_gain_attribution/online_dense_training/README.md')]:
            path=trial.BASE.WORKSPACE/filename;text=path.read_text()
            if heading not in text:raise RuntimeError('Missing journal heading')
            path.write_text(text.replace(heading,heading+'\n- '+msg+' → [카드]('+link+')\n',1))
        if not evaluation:raise RuntimeError('Failed worker arm; inspect before continuing')
    print('PAIR_COMPLETE',flush=True)


if __name__=='__main__':main()
