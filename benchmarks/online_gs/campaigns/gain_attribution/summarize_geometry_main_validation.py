"""Summarize fresh merged-main D3/vanilla comparisons without reclassifying old runs."""
import json
from pathlib import Path
ROOT=Path('/home/intern/gs_floaterLab')
BASE=ROOT/'results/campaigns/gain_attribution/geometry_main_validation'
read=lambda p:json.loads(p.read_text())
rows=read(BASE/'gpu_v1/summary.json')
assert len(rows)==8 and all(r['pass'] for r in rows)
old={r['scene']:r for r in read(ROOT/'results/campaigns/gain_attribution/main_validation/comparison.json')['rows']}
result=[]
for key in ['aria','rpng','utmm','rot']:
 d=next(r for r in rows if r['key']==key and r['arm']=='d3')
 v=next(r for r in rows if r['key']==key and r['arm']=='vanilla')
 o=old[d['scene']]
 result.append({'scene':d['scene'],'previous_native_psnr':o['main_psnr'],'fresh_d3_psnr':d['psnr'],
  'fresh_vanilla_psnr':v['psnr'],'d3_gain_over_vanilla_db':d['psnr']-v['psnr'],
  'd3_minus_previous_native_db':d['psnr']-o['main_psnr'],
  'fresh_vanilla_minus_previous_db':v['psnr']-o['vanilla_psnr'],
  'd3_gaussians':d['gaussians'],'vanilla_gaussians':v['gaussians'],
  'd3_mapping_seconds':d['mapping_seconds'],'vanilla_mapping_seconds':v['mapping_seconds'],
  'training_renders_each':d['renders']['training'],'d3_auxiliary_depth_renders':d['aux_renders'],
  'd3_training_plus_proxy_renders':d['renders']['training']+d['aux_renders'],
  'd3_output':str((ROOT/d['output']).resolve()),'vanilla_output':str((ROOT/v['output']).resolve()),
  'same_prefix_trajectory_cohort':d['same_prefix_trajectory_cohort'] and v['same_prefix_trajectory_cohort']})
x={'date':'2026-09-30','tested_main':read(BASE/'gpu_v1/protocol.json')['main'],
 'fresh_runs':8,'seed':0,'rows':result,'all_four_gains_positive':all(r['d3_gain_over_vanilla_db']>0 for r in result),
 'mean_gain_db':sum(r['d3_gain_over_vanilla_db'] for r in result)/4,
 'mean_d3_minus_previous_native_db':sum(r['d3_minus_previous_native_db'] for r in result)/4,
 'scope':'D3 + fixed depth backward + warp; maintenance off, density unchanged; previous native numbers are historical',
 'equal_total_render_budget':False,'live_tracking_benchmark':False,'independent_geometry_gt_measured':False}
(BASE/'comparison.json').write_text(json.dumps(x,indent=2)+'\n')
lines=['# Merged-main D3 validation — 2026-09-30','',
 'Four fresh D3 runs and four fresh official-vanilla runs; each saved map evaluated twice.',
 'Original native fixed40 PSNR below is the previous main validation, not a newly run native control.','',
 '| Scene | Previous native | Fresh D3 | Fresh vanilla | D3 gain | D3 − previous native |',
 '|---|---:|---:|---:|---:|---:|']
for r in result:lines.append(f"| {r['scene']} | {r['previous_native_psnr']:.3f} | {r['fresh_d3_psnr']:.3f} | {r['fresh_vanilla_psnr']:.3f} | {r['d3_gain_over_vanilla_db']:+.3f} | {r['d3_minus_previous_native_db']:+.3f} |")
lines+=['','| Scene | Main training renders (each) | D3 extra proxy renders | D3 / vanilla seconds | D3 / vanilla GS |','|---|---:|---:|---:|---:|']
for r in result:lines.append(f"| {r['scene']} | {r['training_renders_each']} | {r['d3_auxiliary_depth_renders']} | {r['d3_mapping_seconds']:.2f} / {r['vanilla_mapping_seconds']:.2f} | {r['d3_gaussians']} / {r['vanilla_gaussians']} |")
lines+=['','Same frozen causal inputs, per-arrival 40 training renders/KF, trajectories and held-out cohorts were checked.',
 'D3 adds proxy renders and an additional backward traversal, so this is not an equal-total-work comparison.',
 'Times are single-run mapping measurements, not concurrent tracking FPS or isolated D3 cost.',
 'D3 and the raster fixes were enabled together; their separate effects are not identified here.',
 'No new independent ground-truth geometry evaluation was performed. Maintenance and density overrides remain untested in this panel.',
 '',f"Main tested: `{x['tested_main']}`. Raw results: `{BASE/'gpu_v1'}`.",
 f"Mean gain over fresh vanilla: **{x['mean_gain_db']:+.3f} dB**. Mean change from prior native: **{x['mean_d3_minus_previous_native_db']:+.3f} dB**."]
(ROOT/'context/experiments/campaigns/06_gain_attribution/geometry_main_validation/SUMMARY.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(x,indent=2))
