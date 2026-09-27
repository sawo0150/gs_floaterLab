#!/usr/bin/env python3
"""Independent render audit, prefix equality, source and evaluation verification."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

def read(p):return p.read_text() and json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--panel',type=Path,required=True);args=p.parse_args()
    protocol=read(args.panel/'protocol.json');progress=read(args.panel/'progress.json')
    expected={(d,a,s) for d in ('aria','rpng','utmm') for a in ('legacy_growth','paired') for s in protocol['seeds']}
    if len(progress)!=len(expected) or {(r['dataset'],r['arm'],r['seed']) for r in progress}!=expected:
        raise ValueError('Incomplete panel')
    common=None;groups={};rows=[]
    for row in progress:
        root=Path(row['output']);r=read(root/'render_result.json')
        ev=read(root/'evaluation_consistency.json')
        if not(row['valid'] and r['valid_execution'] and ev['pass'] and all(r['checks'].values())):
            raise ValueError('Invalid run')
        lock=read(root/'source_lock.json')
        digests={f:v['sha256'] for f,v in lock.items()}
        for f,v in lock.items():
            if sha(Path(v['copy']))!=v['sha256']:raise ValueError('Snapshot source mismatch')
        if common is None:common=digests
        if common!=digests:raise ValueError('Source mismatch')
        audit=read(root/'render_audit.json')
        training=[x for x in audit if x['grad_enabled']]
        if not all(x['backward'] for x in training):raise ValueError('Unconsumed training render')
        service_count=sum(len(s['uids']) for g in r['training']['generations'] for s in g['services'])
        if len(training)!=service_count or len(training)!=r['render_counts']['training']:
            raise ValueError('Independent render count mismatch')
        by_arrival=Counter(x['arrival_uid'] for x in training)
        cumulative=0
        for prefix in r['render_prefixes']:
            cumulative+=by_arrival[prefix['uid']]
            if cumulative!=prefix['training_renders']:raise ValueError('Prefix render audit mismatch')
        metric=read(root/'psnr/strict_fixed_manifest/final_result.json')
        cohort=[(x['frame_index'],x['uid'],x['predeclared_fixed_manifest_split']) for x in metric['per_view']]
        trajectories={f:sha(root/f) for f in ('traj_full_beforeBA.txt','traj_kf_beforeBA.txt')}
        identity=(cohort,trajectories,[(x['uid'],x['training_renders']) for x in r['render_prefixes']],
                  [x['event_id'] for x in r['submitted_events']],r['clock_reference_sha256'])
        group=(row['dataset'],row['seed'])
        if group in groups and groups[group]!=identity:raise ValueError('Input/work/evaluation mismatch')
        groups[group]=identity
        if any(x['seconds']>r['last_input_at'] for x in r['boundaries']['optimizer_completions']):
            raise ValueError('Post EOS optimizer')
        if row['arm']=='paired':
            if r['schedule']!='paired_kf_dense' or r['native_global_views']!=0:raise ValueError('Wrong paired arm')
            if sha(Path(r['fixed_reference']))!=r['fixed_reference_sha256']:raise ValueError('Reference changed')
        rows.append({**row,'native_renders':sum(x['phase']=='native' for x in training),
                     'additional_renders':sum(x['phase']=='additional' for x in training),
                     'pose_seconds':(r.get('visual_pose_audit') or {}).get('wall_seconds',0.),
                     'gaussians':r['gaussians'],'prefixes':len(r['render_prefixes'])})
    deltas=[r['delta_psnr'] for r in rows if r['arm']=='paired']
    result={'verified':True,'protocol':protocol,'rows':rows,'mean_delta_psnr':statistics.mean(deltas),
            'interpretation':'Equal per-prefix training camera renders; distinct losses/grouping/admission remain; not realtime or sampler-only claim.'}
    (args.panel/'verified_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
