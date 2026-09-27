#!/usr/bin/env python3
"""Audit exact work/poses/cohorts for the paired vs official40 feasibility run."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--panel',type=Path,required=True)
    p.add_argument('--datasets',nargs='+',default=['aria','rpng','utmm']);a=p.parse_args()
    inputs=[r for r in read(a.panel/'summary.json') if r['dataset'] in a.datasets]
    assert {(r['dataset'],r['arm']) for r in inputs}=={(d,arm) for d in a.datasets for arm in ['paired','vanilla']}
    assert len(inputs)==2*len(a.datasets)
    rows=[];groups={}
    for row in inputs:
        root=Path(row['output']);r=read(root/'render_result.json');ev=read(root/'evaluation_consistency.json')
        assert row['valid_execution'] and r['valid_execution'] and ev['pass'] and all(r['checks'].values())
        assert not row['source_changed']
        for entry in read(root/'source_lock.json').values():
            assert sha(Path(entry['copy']))==entry['sha256']
        audit=read(root/'render_audit.json');train=[x for x in audit if x['grad_enabled']]
        assert len(train)==r['render_counts']['training'] and all(x['backward'] for x in train)
        assert len(audit)==r['render_counts']['all'] and all(x['uid']<=x['arrival_uid'] for x in audit)
        per_uid=Counter(x['arrival_uid'] for x in train);all_per_uid=Counter(x['arrival_uid'] for x in audit)
        cumulative=all_cumulative=0
        for prefix in r['render_prefixes']:
            cumulative+=per_uid[prefix['uid']];all_cumulative+=all_per_uid[prefix['uid']]
            assert cumulative==prefix['training_renders'] and all_cumulative==prefix['all_renders']
        if row['arm']=='paired':
            b=r['kf_render_budget'];assert b['renders_per_kf']==40
            assert len(train)==40*b['kf_admissions']
            assert r['native_global_views']==0 and r['membership']=='immediate' and r['schedule']=='paired_kf_dense'
            ss=[s for g in r['training']['generations'] for s in g['services']]
            assert sum(len(s['uids']) for s in ss)==len(train)
            assert all(x['seconds']<=r['last_input_at'] for x in r['boundaries']['optimizer_completions'])
            extra_kf=sum(len(s['uids']) for s in ss if s.get('role')=='keyframe')
            extra_dense=sum(len(s['uids']) for s in ss if s.get('role')=='dense')
            steps=r['main_optimizer_steps']
        else:
            ref=read(Path(r['reference']));b=ref['kf_render_budget']
            assert r['reference_sha256']==sha(Path(r['reference']))
            assert r['renders_per_kf']==40 and len(train)==40*b['kf_admissions']
            assert all(t<=r['last_input_at'] for t in r['optimizer_completions'])
            extra_kf=extra_dense=0;steps=r['telemetry']['optimizer_steps_completed']
        metric=read(root/'psnr/strict_fixed_manifest/final_result.json')
        identity={
            'cohort':[(x['frame_index'],x['uid'],x['predeclared_fixed_manifest_split']) for x in metric['per_view']],
            'trajectories':{f:sha(root/f) for f in ['traj_full_beforeBA.txt','traj_kf_beforeBA.txt']},
            'prefixes':[(x['uid'],x['training_renders'],x['all_renders']) for x in r['render_prefixes']],
            'events':[x['event_id'] for x in r['submitted_events']]}
        if row['dataset'] in groups:assert identity==groups[row['dataset']]
        groups[row['dataset']]=identity
        rows.append({'dataset':row['dataset'],'arm':row['arm'],'verified':True,'psnr':row['psnr'],
            'mapping_seconds':row['mapping_seconds'],'kf_admissions':b['kf_admissions'],
            'distinct_kfs':b['distinct_kf_uids'],'training_renders':len(train),'renders_per_kf':40,
            'all_camera_forwards':len(audit),'optimizer_steps':steps,'extra_kf':extra_kf,'extra_dense':extra_dense,
            'gaussians':r['gaussians']})
    result={'verified':True,'same_pose_events_cohort_and_all_render_prefixes':True,'rows':rows,
        'limits':['fixed-work mapper-only, not real-time','loss/topology/optimizer grouping differ between arms','seed0; repeated evaluation is not repeated training']}
    suffix='' if len(a.datasets)==3 else '_'+('_'.join(a.datasets))
    (a.panel/f'verified_summary{suffix}.json').write_text(json.dumps(result,indent=2)+'\n')
    with (a.panel/f'summary{suffix}.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
