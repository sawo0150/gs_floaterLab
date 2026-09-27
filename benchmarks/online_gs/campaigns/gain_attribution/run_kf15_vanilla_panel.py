#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import run_online_dense_training as trial

def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--reference-panel',type=Path,required=True)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    refs=json.loads((args.reference_panel/'verified_summary.json').read_text())
    if not refs['verified']:raise RuntimeError('Reference not verified')
    runner=Path(__file__).with_name('run_kf15_vanilla.py').resolve()
    env=trial.BASE.mapping_environment(False)
    env['PYTHONPATH']=str(trial.BASE.WORKSPACE/'benchmarks/online_gs')+':'+env['PYTHONPATH']
    write(args.output/'protocol.json',{'reference_panel':str(args.reference_panel),'renders_per_kf':15,
        'vanilla':'official 22ffe24 KF-only native window + up to 2 historical KFs; original loss/birth/topology',
        'adapters':['per-prefix render cap using established vanilla adapter','first birth UID corrected for heldout0','same safe masked reciprocal depth loss'],
        'post_eos_updates':0,'seed':0,'fixed_time_claim':False,'concurrent_tracking':False})
    rows=[]
    for dataset,scene in [('aria','aria1253'),('rpng','table_06'),('utmm','square-1')]:
        trial.common.evaluation.panel.v2.gpu_idle()
        output=args.output/dataset/'vanilla/seed0';output.parent.mkdir(parents=True,exist_ok=True)
        reference=args.reference_panel/dataset/'legacy_growth/seed0/render_result.json'
        cmd=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(runner),'--dataset',dataset,'--scene',scene,
             '--reference',str(reference),'--output',str(output),'--seed','0']
        write(output.parent/'command_seed0.json',cmd)
        print('START',dataset,'vanilla',flush=True)
        with (output.parent/'mapping_seed0.log').open('x') as f:code=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
        path=output/'render_result.json';r=json.loads(path.read_text()) if path.exists() else None
        ev=None
        if code==0 and r and r['valid_execution']:
            ev=trial.common.evaluation.panel.run_evaluation_twice(output,dataset,scene,trial.BASE.sequence_paths(dataset,scene)['fixed_manifest'])
        valid=bool(code==0 and r and r['valid_execution'] and ev and ev['pass'])
        row={'dataset':dataset,'scene':scene,'arm':'vanilla','seed':0,'output':str(output),'returncode':code,
             'valid':valid,'psnr':ev['fixed_psnr_first'] if ev else None,
             'mapping_seconds':r['mapping_seconds'] if r else None,'renders':r['render_counts'] if r else None}
        if ev:
            for arm in ['legacy_growth','paired']:
                other=next(x for x in refs['rows'] if x['dataset']==dataset and x['arm']==arm)
                row[arm+'_minus_vanilla']=other['psnr']-row['psnr']
        rows.append(row);write(args.output/'progress.json',rows)
        detail=f"{row['psnr']:.6f}dB, {row['renders']['training']} training renders" if valid else '실패; 원본 로그 보존'
        msg=f"**2026-09-25 (15 renders/KF vanilla / {dataset}):** {detail}."
        card=trial.BASE.WORKSPACE/'context/experiments/campaigns/06_gain_attribution/render_matched_kf15/README.md'
        with card.open('a') as f:f.write('\n'+msg+'\n\n```json\n'+json.dumps(row,indent=2)+'\n```\n')
        for name,head,link in [('context/STATUS.md','## 최근 흐름 (최신순)\n','experiments/campaigns/06_gain_attribution/render_matched_kf15/README.md'),('context/experiments/INDEX.md','# Experiment Index\n','campaigns/06_gain_attribution/render_matched_kf15/README.md')]:
            q=trial.BASE.WORKSPACE/name;s=q.read_text();assert head in s;q.write_text(s.replace(head,head+'\n- '+msg+' → [카드]('+link+')\n',1))
        print('DONE',json.dumps(row),flush=True)
        if not valid:raise RuntimeError('Vanilla failed; inspect preserved artifacts')
    print('PANEL_COMPLETE',flush=True)

if __name__=='__main__':main()
