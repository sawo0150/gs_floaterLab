"""Audit completed live FIFO runs and write compact comparison artifacts."""
import argparse
import hashlib
import json
import math
from pathlib import Path

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();rows=read(a.root/'summary.json');compact=[];cohorts={};sources={}
    for row in rows:
        assert row['valid_execution'] and row['evaluation']['pass'],row
        out=Path(row['output']);r=read(out/'result.json');exp=read(out/'export.json')
        assert math.isfinite(row['psnr'])
        for path,entry in read(out/'source_lock.json').items():
            sources.setdefault(path,entry['sha256'])
            assert sources[path]==entry['sha256'],('source changed across runs',path)
        e=read(out/'psnr/strict_fixed_manifest/final_result.json')
        # Tracker-dependent non-fixed rows may differ. Compare only the
        # predeclared fixed held-out cohort, used for every reported PSNR.
        fixed=[(v['uid'],v['frame_index']) for v in e['per_view'] if v['predeclared_fixed_manifest_split']]
        assert len(fixed)==e['predeclared_fixed_manifest_posthoc']['view_count']
        assert e['predeclared_fixed_manifest_posthoc']['mapping_disjoint']
        cohorts.setdefault(row['key'],fixed)
        assert cohorts[row['key']]==fixed,(row['key'],'fixed cohort mismatch')
        w=r['worker'];q=w['backlog']
        assert not r['error'] and not w['error'] and not r['overruns']
        assert r['tracked_frames']==r['input_frames'] and r['source_unchanged'] and r['zero_tail_observed'] and exp['finite']
        assert w['unfinished_tasks']==0 and q['peak_pending_mapping']<=q['capacity']==2
        if row['arm']=='ours':
            boundary=read(out/'runtime.json')['boundaries']
            prune=r['protected_pruning'];assert prune['pass']
            assert all(x['completed_at']<=boundary['deadline'] and x['protected_removed']==0 for x in prune['events'])
        compact.append({k:row[k] for k in ['key','scene','arm','time_scale','psnr','output']}|{
            'tracking_config':read(out/'effective_config.json')['config']['Tracking'],
            'budget_seconds':r['duration_seconds'],'tracking_seconds':r['tracking_elapsed_seconds'],
            'end_minus_budget_seconds':r['tracking_elapsed_seconds']-r['duration_seconds'],
            'start_lag_p95_ms':r['start_lag_ms']['95'],'start_lag_max_ms':r['start_lag_ms']['100'],
            'completed_training_renders':r['committed_renders'],
            'attempted_training_renders':r['training_renders'],
            'extra_D3_proxy_renders':r.get('geometry',{}).get('stats',{}).get('aux_renders',0),
            'kf_admissions':r['kf_admissions'],'gaussians':exp['gaussians'],
            'overflow_drops':q['dropped_mapping_packets'],'all_cancellations':w['cancelled'],
            'zero_tail':r['zero_tail_observed'],'heldout_count':len(fixed),
            'result_sha256':sha(out/'result.json'),'evaluation_sha256':sha(out/'evaluation_consistency.json')})
    artifact={'protocol':'actual_tracking_fifo_1x_1p5x','seed':0,'rows':compact,'complete':len(compact)==16,
              'interpretation':'End-to-end recipe comparison. Tracking config matches on aria/rot; differs on rpng/utmm (custom motion/window/radius=3.6/15/1, vanilla=2.4/25/2). Not an isolated mapper ablation.',
              'checks':{'fixed_cohorts_match':True,'no_mapping_heldout_overlap':True,'sources_match_across_runs':True,
                        'independent_double_evaluation':True,'no_optimizer_deadline_overrun':True,
                        'pruning_completed_before_deadline':True},
              'sources':sources}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(artifact,indent=2)+'\n')
    text=['| Scene | Time allowance | Vanilla PSNR | Ours PSNR | Gain | Vanilla / ours tracking sec | Vanilla / ours drops |',
          '|---|---:|---:|---:|---:|---:|---:|']
    for key in ['aria','rpng','utmm','rot']:
      for scale in [1.,1.5]:
        arms={r['arm']:r for r in compact if r['key']==key and r['time_scale']==scale}
        if len(arms)!=2:continue
        v,o=arms['vanilla'],arms['ours']
        text.append(f"| {o['scene']} | {scale:g}x | {v['psnr']:.3f} | {o['psnr']:.3f} | {o['psnr']-v['psnr']:+.3f} | {v['tracking_seconds']:.2f} / {o['tracking_seconds']:.2f} | {v['overflow_drops']} / {o['overflow_drops']} |")
    a.output.with_suffix('.md').write_text('\n'.join(text)+'\n')
    print('\n'.join(text))
if __name__=='__main__':main()
