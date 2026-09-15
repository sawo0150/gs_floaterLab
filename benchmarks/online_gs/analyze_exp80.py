#!/usr/bin/env python3
from pathlib import Path
import re,json,statistics
ROOT=Path(__file__).resolve().parents[2]
r=ROOT/'results/benchmarks/fixed1x_sensor_eos_zero_tail_v1/vigs_final_v7_5090_clean/exp80_2a3eeeb5_dirty_20260910'
state=json.loads((r/'queue_state.json').read_text())
paths=[('aria79_'+str(i),ROOT/f'results/experiments/exp79_aria_1x_zero_tail_20260910/baseline_repeat{i}',1303) for i in range(2)]
paths +=[(key,r/key/'seed0',v['frames']) for key,v in state['sequences'].items()]
rows=[]
for name,p,n in paths:
 f=p/'run.log'
 if not f.exists():continue
 s=f.read_text();row={'name':name,'frames':n}
 a=p/'sensor_eos_audit.json'
 if a.exists():
  a=json.loads(a.read_text());row.update(budget_s=a['budget_seconds'],adam_completed=a['completed_adam_steps'],adam_skipped=a['skipped_adam_calls'],input_fps=(n-1)/a['budget_seconds'])
 m=re.search(r'GPU_PIPELINE_TELEMETRY (.*?)(?:GSBackend: GPU_PIPELINE_PHASE|GPU_PIPELINE_PHASE)',s,re.S)
 if m:
  d=dict(re.findall(r'(\w+)=([^\s]+)',m[1]));row['pipeline']={k:float(d[k]) for k in ['online_wall_s','track_wall_ms','dispatch_wall_ms','idle_replay_wall_ms','gate_allowed','gate_allowed_tracking','deadline_slack_ms_max','reject_tracking','reject_model','reject_deadline'] if k in d}
 phases={}
 for m in re.finditer(r'GPU_PIPELINE_PHASE phase=(\w+)\s+calls=(\d+)\s+wall_ms=([\d.]+)',s):phases[m[1]]={'calls':int(m[2]),'wall_ms':float(m[3])}
 row['phases']=phases
 m=re.search(r'^MAP_RR_DONE (.*)',s,re.M)
 if m:
  d=dict(re.findall(r'(\w+)=([^ ]+)',m[1]));row['replay']={k:d.get(k) for k in ['steps','active_candidates','wall_ms_ema','selection_count_mean','selection_count_last_to_first','model_pose_revision_observations','model_rematuration_cycles','model_phase']}
 last=None
 for line in s.splitlines():
  m=re.search(r'Processing keyframe (\d+) gs (\d+):.*?\| (\d+)/(\d+) ',line)
  if m:last={'kf':int(m[1]),'gaussians':int(m[2]),'frame':int(m[3]),'fraction':int(m[3])/int(m[4])}
  if 'Begin IMU Initialization' in line and last:row['imu_init_start_progress']=last;break
 f=p/'psnr/online_final/final_result.json'
 if f.exists():
  x=json.loads(f.read_text());views=[v for v in x['per_view'] if v.get('is_fixed_eval_view')];row.update(psnr=x['fixed_eval_mean_psnr'],heldout_views=len(views))
  row['psnr_thirds']=[statistics.mean(v['psnr'] for v in views if i/3<=v['frame_idx']/n<(i+1)/3) for i in range(3)]
  if row.get('replay',{}).get('active_candidates') is not None:row['final_replay_pool_fraction_of_nonheldout']=int(row['replay']['active_candidates'])/(n-len(views))
 rows.append(row)
(r/'diagnostics.json').write_text(json.dumps({'rows':rows},indent=2))
for row in rows:
 print(row['name'], 'PSNR',round(row.get('psnr',0),3),'budget',round(row.get('budget_s',0),2),'init',row.get('imu_init_start_progress'),'replay',row.get('replay'))
