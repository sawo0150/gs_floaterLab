#!/usr/bin/env python3
"""Independently audit live timing/work records and summarize measured capacity."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import run_online_dense_training as trial


def main():
    p=argparse.ArgumentParser();p.add_argument('--panel',type=Path,required=True)
    a=p.parse_args();rows=json.loads((a.panel/'summary.json').read_text())
    audited=[]
    for row in rows:
        out=Path(row['output']);r=row.get('runtime')
        if not r:
            audited.append({'dataset':row['dataset'],'arm':row['arm'],'valid':False,'reason':'no result'})
            continue
        frames=json.loads((out/'frames.json').read_text())
        audit=json.loads((out/'renders.json').read_text())
        lock=json.loads((out/'source_lock.json').read_text())
        budget=json.loads((out/'kf_admissions.json').read_text())
        admissions=budget['admissions'] if isinstance(budget,dict) else budget
        cap=r['renders_per_kf_cap']
        checks={
            'tracking_frames_complete':len(frames)==r['input_frames'],
            'uids_in_order':all(a['uid']<b['uid'] for a,b in zip(frames,frames[1:])),
            'no_early_input':all(f['start_seconds']>=f['sensor_seconds']-1e-5 for f in frames),
            'render_rows_match':len(audit['rows'])==audit['counts']['all'],
            'training_count_matches':sum(x['grad_enabled'] for x in audit['rows'])==r['training_renders'],
            'backward_count_matches':sum(x['backward'] for x in audit['rows'])==r['backward_renders'],
            'causal_render_uid':all(x['uid']<=x['arrival_uid'] for x in audit['rows']),
            'kf_admission_count':len({(x['generation'],x['uid']) for x in admissions})==r['kf_admissions'],
            'work_cap':r['committed_renders']<=cap*r['kf_admissions'] if cap else True,
            'zero_tail_observed':r['zero_tail_observed'],
            'source_snapshot_hashes':all(hashlib.sha256(Path(v['copy']).read_bytes()).hexdigest()==v['sha256'] for v in lock.values()),
            'no_worker_error':not r.get('error') and not r.get('worker_errors') and not r.get('worker',{}).get('error'),
            'source_unchanged_at_run_end':r['source_unchanged'],
            'double_evaluation_agrees':bool((row.get('evaluation') or {}).get('pass')),
        }
        # Reconstruct completed work independently from each actual trainer.
        if row['arm']=='paired':
            runtime=json.loads((out/'runtime.json').read_text())
            services=[s for g in runtime['training']['generations'] for s in g['services']]
            checks['commits_match']=sum(len(s['uids']) for s in services)==r['committed_renders']
            extra_kf=sum(len(s['uids']) for s in services if s.get('role')=='keyframe')
            extra_dense=sum(len(s['uids']) for s in services if s.get('role')=='dense')
        else:
            services=json.loads((out/'services.json').read_text())
            checks['commits_match']=(services[-1]['renders'] if services else 0)==r['committed_renders']
            extra_kf=extra_dense=0
        result={'dataset':row['dataset'],'arm':row['arm'],'valid':all(checks.values()),'checks':checks,
            'input_seconds':r['duration_seconds'],'tracking_seconds':r['tracking_elapsed_seconds'],
            'renders':r['committed_renders'],'kf_admissions':r['kf_admissions'],
            'renders_per_kf':r['renders_per_kf_admission'],'input_lag_p95_ms':r['start_lag_ms'].get('95'),
            'input_lag_max_ms':r['start_lag_ms'].get('100'),'psnr':row.get('psnr'),
            'source_unchanged_at_run_end':r['source_unchanged']}
        effective=out/'effective_config.json'
        settings=json.loads(effective.read_text()) if effective.exists() else {}
        settings_args=settings.get('args',{})
        result['frontend_iterations']=r.get('frontend_iterations',settings.get('frontend_iterations',[4,2]))
        result['IMU_poseinit_after']=r.get('IMU_poseinit_after',settings_args.get('IMU_poseinit_after',100000))
        result.update(extra_kf_renders=extra_kf,extra_dense_renders=extra_dense)
        result['all_camera_forwards']=audit['counts']['all']
        result['auxiliary_camera_forwards']=audit['counts']['all']-r['training_renders']
        result['all_camera_forwards_per_kf']=audit['counts']['all']/r['kf_admissions'] if r['kf_admissions'] else None
        result['frames_started_after_mapping_deadline']=sum(f['start_seconds']>r['duration_seconds'] for f in frames)
        path=out/'traj_kf_beforeBA.txt'
        if path.exists():
            root=trial.BASE.sequence_paths(row['dataset'],row['scene'])['archive']
            manifest=json.loads((root/'archive_manifest.json').read_text())
            arrivals=[json.loads(line) for line in (root/manifest['arrivals']).read_text().splitlines() if line]
            by_time={round(float(x['sensor_timestamp']),8):x for x in arrivals}
            kfs=[by_time[round(float(line.split()[0]),8)] for line in path.read_text().splitlines() if line.strip()]
            eligible={int(k['frame_uid']) for k in kfs if not k['held_out']}
            generation=max((x['generation'] for x in admissions),default=0)
            mapped={x['uid'] for x in admissions if x['generation']==generation}
            result['final_tracking_training_kfs']=len(eligible)
            result['final_tracking_kfs_in_map']=len(eligible&mapped)
            result['renders_per_final_tracking_training_kf']=r['committed_renders']/len(eligible) if eligible else None
        audited.append(result)
    (a.panel/'verified_summary.json').write_text(json.dumps(audited,indent=2)+'\n')
    fields=['dataset','arm','valid','frontend_iterations','IMU_poseinit_after','input_seconds','tracking_seconds','renders','kf_admissions','renders_per_kf','all_camera_forwards','auxiliary_camera_forwards','all_camera_forwards_per_kf','extra_kf_renders','extra_dense_renders','final_tracking_training_kfs','final_tracking_kfs_in_map','frames_started_after_mapping_deadline','input_lag_p95_ms','input_lag_max_ms','psnr']
    with (a.panel/'summary.csv').open('w') as f:
        writer=csv.DictWriter(f,fields,extrasaction='ignore');writer.writeheader();writer.writerows(audited)
    caps=sorted({row['runtime']['renders_per_kf_cap'] for row in rows if row.get('runtime')})
    budget_label='/'.join(str(c) for c in caps)
    text=[f'# RTX 5090 live tracking + mapping, {budget_label} renders/KF cap','',
          'Native RGB timestamps, metric-init gate, no post-EOS mapping. Seed0 only. Frontend iterations and IMU pose prediction setting are recorded per row in CSV.',
          'Model engine loading and evaluation are outside the stream clock; per-frame processing and map initialization are inside.',
          'Official source is unchanged; heldout/deadline/render-budget/reset-lock adapters are explicit. This is not untouched default-budget VIGS-SLAM.', '',
          '| Scene | Arm | Committed renders/KF | Tracker elapsed / input (s) | Input lag p95 / max (ms) | Held-out PSNR | Audit |',
          '|---|---|---:|---:|---:|---:|---|']
    for r in audited:
        if 'renders_per_kf' not in r:continue
        fmt=lambda v:f'{v:.2f}' if isinstance(v,(float,int)) else 'N/A'
        text.append(f"| {r['dataset']} | {r['arm']} | {fmt(r['renders_per_kf'])} | {fmt(r['tracking_seconds'])} / {fmt(r['input_seconds'])} | {fmt(r['input_lag_p95_ms'])} / {fmt(r['input_lag_max_ms'])} | {fmt(r['psnr'])} | {'PASS' if r['valid'] else 'FAIL'} |")
    text+=['','Interpretation: an audit PASS checks the recorded execution, not low-latency real-time performance.',
           'The per-KF cap counts training camera renders; auxiliary no-grad rendering is timed and separately counted in CSV.',
           'Matching frontend iteration counts does not force identical online tracker/PGBA histories. Therefore final KF counts and total work may differ.',
           'These end-to-end results must not be substituted for the prior equal-pose/equal-total-render mapper ablation.',
           'The configured cap is a candidate operating point, not an established maximum capacity or a guarantee per incoming KF.']
    (a.panel/'SUMMARY.md').write_text('\n'.join(text)+'\n')
    print(json.dumps(audited,indent=2))


if __name__=='__main__':main()
