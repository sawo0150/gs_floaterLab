#!/usr/bin/env python3
from pathlib import Path
import json,csv,statistics,math,re
ROOT=Path(__file__).resolve().parents[2]
r=ROOT/'results/benchmarks/fixed1x_sensor_eos_zero_tail_v1/vigs_final_v7_5090_clean/exp80_2a3eeeb5_dirty_20260910'
old=json.loads((ROOT/'context/experiments/exp77/evidence/aggregate.json').read_text())
oldrows={(v['dataset'],v['sequence']):v for v in old['rows']}
state=json.loads((r/'queue_state.json').read_text());rows=[]
for key,v in state['sequences'].items():
 ds,seq=key.split('/');p=r/ds/seq/'seed0'
 row=dict(dataset=ds,sequence=seq,status=v['status'])
 log=p/'run.log'
 if log.exists():
  text=log.read_text();m=re.search(r'^MAP_RR_DONE (.*)',text,re.M)
  if m:
   fields=dict(re.findall(r'(\w+)=([^ ]+)',m[1]))
   for name in ['steps','active_candidates','selection_count_mean','selection_count_last_to_first']:
    row['replay_'+name]=fields.get(name)
 ply=p/'3dgs_before_final.ply'
 if ply.exists():
  with ply.open('rb') as f:
   for _ in range(100):
    line=f.readline()
    if line.startswith(b'element vertex '):row['gaussians']=int(line.split()[-1])
    if line.strip()==b'end_header':break

 f=p/'psnr/online_final/final_result.json';af=p/'sensor_eos_audit.json'
 if af.exists():
  a=json.loads(af.read_text());row.update({k:a[k] for k in ['budget_seconds','completed_adam_steps','skipped_adam_calls','updates_completed_after_deadline','updates_completed_after_sensor_eos']})
  row['optimizer_contract_pass']=a['updates_completed_after_deadline']==0 and a['updates_completed_after_sensor_eos']==0
 if f.exists() and v['status']=='complete':
  x=json.loads(f.read_text());row.update(psnr=x['fixed_eval_mean_psnr'],ssim=x['fixed_eval_mean_ssim'],lpips=x['fixed_eval_mean_lpips'],eval_views=x['fixed_eval_view_count'])
  t=v.get('tracking',{});row.update(ate_cm=t.get('ate_rmse_cm'),recall10=t.get('recall_at_10cm_percent'),scale_error_percent=t.get('scale_error_percent'))
  b=oldrows.get((ds,seq));row['exp77_psnr']=b['heldout_mean_psnr'] if b else None;row['delta_psnr']=row['psnr']-row['exp77_psnr'] if b else None
 rows.append(row)
agg={}
for ds in ['utmm','rpng','all']:
 a=[v for v in rows if (ds=='all' or v['dataset']==ds) and 'psnr' in v]
 if a:
  paired=[v for v in a if v.get('delta_psnr') is not None]
  ates=[v['ate_cm'] for v in a if v.get('ate_cm') is not None]
  agg[ds]={'evaluated':len(a),'psnr_mean':statistics.mean(v['psnr'] for v in a),'psnr_27_pass_count':sum(v['psnr']>=27 for v in a),'ate_median_cm':statistics.median(ates) if ates else None,'paired_delta_mean':statistics.mean(v['delta_psnr'] for v in paired) if paired else None}
x={'protocol':'fixed1x_sensor_eos_zero_tail_v1','queue_status':state.get('status','running'),'rows':rows,'aggregates':agg}
(r/'aggregate.json').write_text(json.dumps(x,indent=2))
print(json.dumps({'queue':x['queue_status'],'states':[(v['dataset']+'/'+v['sequence'],v['status'],round(v['psnr'],3) if 'psnr' in v else None) for v in rows],'aggregates':agg},indent=2))
