#!/usr/bin/env python3
"""Sequential 3-scene official/paired 15-render live comparison and audit."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

import run_online_dense_training as trial


def write(p,x):p.write_text(json.dumps(x,indent=2,default=str)+'\n')


def journal(row):
    rel='campaigns/06_gain_attribution/live_render_capacity/README.md'
    card=trial.BASE.WORKSPACE/'context/experiments'/rel
    r=row.get('runtime') or {}
    msg=(f"**2026-09-25 (5090 live / {row['dataset']} / {row['arm']} / IMU pose init {r.get('IMU_poseinit_after', 'legacy100000')}):** "
         f"renders/KF={r.get('renders_per_kf_admission')}, complete={row['valid_execution']}, "
         f"PSNR={row.get('psnr')}; timing/quality 별도 판정.")
    with card.open('a') as f:f.write('\n'+msg+'\n\n```json\n'+json.dumps(row,indent=2)+'\n```\n')
    for fn,head,link in [('context/STATUS.md','## 최근 흐름 (최신순)\n','experiments/'+rel),
                         ('context/experiments/INDEX.md','# Experiment Index\n',rel)]:
        p=trial.BASE.WORKSPACE/fn;s=p.read_text();assert head in s
        p.write_text(s.replace(head,head+'\n- '+msg+' → [카드]('+link+')\n',1))


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--datasets',nargs='+',default=['aria','rpng','utmm'])
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    rows=[]
    for dataset in a.datasets:
        scene={'aria':'aria1253','rpng':'table_06','utmm':'square-1'}[dataset]
        for arm in ['vanilla','paired']:
            trial.common.evaluation.panel.v2.gpu_idle()
            out=a.output/dataset/arm;out.parent.mkdir(parents=True,exist_ok=True)
            runner=Path(__file__).with_name('measure_vanilla_live_capacity.py' if arm=='vanilla' else 'measure_live_render_capacity.py')
            cmd=[sys.executable,str(runner),'--dataset',dataset,'--renders-per-kf','15','--output',str(out)]
            print('START',dataset,arm,flush=True)
            code=subprocess.run(cmd).returncode
            path=out/'result.json';runtime=json.loads(path.read_text()) if path.exists() else None
            valid=bool(code==0 and runtime and not runtime.get('error') and runtime['source_unchanged']
                and runtime['tracked_frames']==runtime['input_frames'] and runtime['zero_tail_observed'])
            eval_result=None
            if valid and (out/'export.json').exists():
                try:
                    eval_result=trial.common.evaluation.panel.run_evaluation_twice(
                        out,dataset,scene,trial.BASE.sequence_paths(dataset,scene)['fixed_manifest'])
                except Exception as e:
                    write(out/'evaluation_error.json',{'error':repr(e)})
            row={'dataset':dataset,'scene':scene,'arm':arm,'returncode':code,'output':str(out),
                 'valid_execution':valid,'runtime':runtime,'evaluation':eval_result,
                 'psnr':eval_result['fixed_psnr_first'] if eval_result and eval_result['pass'] else None}
            rows.append(row);write(a.output/'progress.json',rows);journal(row)
            print('DONE',dataset,arm,'valid',valid,'PSNR',row['psnr'],flush=True)
    write(a.output/'summary.json',rows)


if __name__=='__main__':main()
