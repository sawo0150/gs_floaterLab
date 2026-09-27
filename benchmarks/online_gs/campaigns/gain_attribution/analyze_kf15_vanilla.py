#!/usr/bin/env python3
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--panel',type=Path,required=True);p.add_argument('--reference-panel',type=Path,required=True)
    args=p.parse_args();rows=read(args.panel/'progress.json');prior=read(args.reference_panel/'verified_summary.json')
    if not prior['verified'] or len(rows)!=3 or {r['dataset'] for r in rows}!={'aria','rpng','utmm'}:raise ValueError('Incomplete panel')
    summary=[]
    for row in rows:
        root=Path(row['output']);r=read(root/'render_result.json');refroot=args.reference_panel/row['dataset']/'legacy_growth/seed0'
        ref=read(refroot/'render_result.json');ev=read(root/'evaluation_consistency.json')
        if not(row['valid'] and r['valid_execution'] and ev['pass'] and all(r['checks'].values())):raise ValueError('Invalid run')
        if r['reference_sha256']!=sha(refroot/'render_result.json'):raise ValueError('Reference changed')
        if r['official_commit']!='22ffe24c6df81d0bf63bd20057565c00c51d2996':raise ValueError('Wrong official source')
        for f,v in read(root/'source_lock.json').items():
            if sha(Path(v['copy']))!=v['sha256']:raise ValueError('Snapshot mismatch')
        safe='/home/intern/VIGS-SLAM-online-worker-integration/vigs/gaussian/utils/slam_utils.py'
        if read(root/'source_lock.json')[safe]['sha256']!=read(refroot/'source_lock.json')[safe]['sha256']:raise ValueError('Different safe loss source')
        audit=read(root/'render_audit.json');train=[x for x in audit if x['grad_enabled']]
        if len(train)!=r['render_counts']['training'] or not all(x['backward'] for x in train):raise ValueError('Render/backward mismatch')
        by_uid=Counter(x['arrival_uid'] for x in train);all_by_uid=Counter(x['arrival_uid'] for x in audit)
        cum=all_cum=0
        for x,y in zip(r['render_prefixes'],ref['render_prefixes']):
            cum+=by_uid[x['uid']];all_cum+=all_by_uid[x['uid']]
            if (x['uid'],cum,all_cum)!=(y['uid'],y['training_renders'],y['all_renders']):raise ValueError('Input prefix count mismatch')
        if len(r['render_prefixes'])!=len(ref['render_prefixes']):raise ValueError('Prefix length mismatch')
        if [x['event_id'] for x in r['submitted_events']]!=[x['event_id'] for x in ref['submitted_events']]:raise ValueError('Event mismatch')
        for file in ['traj_full_beforeBA.txt','traj_kf_beforeBA.txt']:
            if sha(root/file)!=sha(refroot/file):raise ValueError('Evaluation trajectory mismatch')
        a=read(root/'psnr/strict_fixed_manifest/final_result.json');b=read(refroot/'psnr/strict_fixed_manifest/final_result.json')
        keys=lambda m:[(x['frame_index'],x['uid'],x['predeclared_fixed_manifest_split']) for x in m['per_view']]
        if keys(a)!=keys(b):raise ValueError('Evaluation cohort mismatch')
        others={x['arm']:x for x in prior['rows'] if x['dataset']==row['dataset']}
        summary.append({**row,'legacy_psnr':others['legacy_growth']['psnr'],'paired_psnr':others['paired']['psnr'],
            'vanilla_optimizer_steps':r['telemetry']['optimizer_steps_completed'],'vanilla_gaussians':r['gaussians'],
            'prefix_count':len(r['render_prefixes'])})
    result={'verified':True,'rows':summary,'mean_paired_minus_vanilla':statistics.mean(x['paired_minus_vanilla'] for x in summary),
            'mean_legacy_minus_vanilla':statistics.mean(x['legacy_growth_minus_vanilla'] for x in summary),
            'seed':0,'all_input_prefix_total_renders_equal':True,'limitations':['fixed-work replay, not concurrent tracking','numeric safe mask/heldout birth UID/budget adapters applied','no independent sampler/loss ablation']}
    (args.panel/'verified_summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
