#!/usr/bin/env python3
"""Validate matched evaluation/source contracts and report paired quality deltas."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics


def read(path):return json.loads(path.read_text())


def main():
    p=argparse.ArgumentParser();p.add_argument('--panel',required=True,type=Path)
    p.add_argument('--extra-panel',type=Path,nargs='*',default=[]);args=p.parse_args()
    protocol=read(args.panel/'protocol.json');progress=read(args.panel/'progress.json')
    for extra in args.extra_panel:
        additional=read(extra/'protocol.json')
        if additional['seeds']!=protocol['seeds']:
            raise ValueError('Extra panel seeds differ')
        protocol['arms']=list(dict.fromkeys(protocol['arms']+additional['arms']))
        progress.extend(read(extra/'progress.json'))
    expected={(d,a,s) for d in ['aria','rpng','utmm'] for a in protocol['arms'] for s in protocol['seeds']}
    actual={(r['dataset'],r['arm'],r['seed']) for r in progress}
    if actual!=expected or len(progress)!=len(expected):raise ValueError('Panel is incomplete or duplicated')
    rows=[];common=None;groups={};paired_count_scopes=set()
    for row in progress:
        root=Path(row['output']);runtime=read(root/'worker_result.json')
        evaluation=read(root/'evaluation_consistency.json');metric=read(root/'psnr/strict_fixed_manifest/final_result.json')
        if not(row['valid'] and runtime['valid_execution'] and evaluation['pass'] and all(runtime['checks'].values())):
            raise ValueError('Invalid execution/evaluation')
        lock={f:v['sha256'] for f,v in read(root/'source_lock.json').items()}
        if common is None:common=lock
        if common!=lock:raise ValueError('Different sources in panel')
        cohort=[(r['frame_index'],r['uid'],r['predeclared_fixed_manifest_split']) for r in metric['per_view']]
        trajectories={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in ['traj_full_beforeBA.txt','traj_kf_beforeBA.txt']}
        group=(row['dataset'],row['seed']);identity=(cohort,trajectories,runtime['budget_seconds'])
        if group in groups and groups[group]!=identity:raise ValueError('Cohort, trajectory or budget mismatch')
        groups[group]=identity
        policy=runtime['training']['generations'][-1]['policy']
        if row['arm'].startswith('paired'):
            if runtime['native_global_views']!=0 or policy['schedule']!='paired_kf_dense':
                raise ValueError('Wrong paired architecture')
            if policy['selector']!='ervs' or policy['selection_count_scope'] not in ('all_rgb','photometric','recent_photometric'):
                raise ValueError('Wrong paired sampling')
            paired_count_scopes.add(policy['selection_count_scope'])
        copied=dict(row)
        copied['selection_count_scope']=policy['selection_count_scope']
        copied['budget_seconds']=runtime['budget_seconds']
        copied['whole_run_steps']={'native':runtime['native_commits'],'additional':runtime['photometric_commits']}
        copied['pose_seconds']=(runtime.get('visual_pose_audit') or {}).get('wall_seconds',0.)
        copied['gaussians']=runtime['gaussians'];rows.append(copied)
    if len(paired_count_scopes)>1:
        raise ValueError('Paired controls use different selection-count scopes')
    comparisons=[]
    for dataset in ['aria','rpng','utmm']:
        seed_rows=[]
        for seed in protocol['seeds']:
            arms={r['arm']:r for r in rows if r['dataset']==dataset and r['seed']==seed}
            r={'seed':seed,'psnr':{a:x['psnr'] for a,x in arms.items()}}
            for control in ['legacy_growth','paired_kf_only']:
                if control in arms and 'paired' in arms:r['paired_minus_'+control]=arms['paired']['psnr']-arms[control]['psnr']
            seed_rows.append(r)
        summary={'dataset':dataset,'seeds':seed_rows}
        for control in ['legacy_growth','paired_kf_only']:
            key='paired_minus_'+control;values=[r[key] for r in seed_rows if key in r]
            if values:summary[key]={'mean':statistics.mean(values),'min':min(values),'max':max(values),
                                   'sample_stdev':statistics.stdev(values) if len(values)>1 else None}
        comparisons.append(summary)
    result={'verified':True,'concurrent_tracking':False,'rows':rows,'comparisons':comparisons,
            'paired_selection_count_scopes':sorted(paired_count_scopes),
            'panels':[str(args.panel)]+[str(p) for p in args.extra_panel],
            'equivalence_claim':False,'note':'PSNR differences only; no retrospective equivalence margin.',
            'remaining':['stream quality curves','paper alignment','broader goal production comparison/ablations']}
    (args.panel/'verified_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(comparisons,indent=2))


if __name__=='__main__':main()
