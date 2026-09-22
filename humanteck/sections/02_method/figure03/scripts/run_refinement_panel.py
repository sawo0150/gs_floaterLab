#!/usr/bin/env python3
"""Five input positions selected without looking at refinement PSNR."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from run_convergence_pair import mapping_environment

WORK = Path('/home/intern/gs_floaterLab')
ROOT = Path(__file__).resolve().parent.parent
OUT = WORK/'results/figure03_refinement_20260921/aria301_305'
ARCHIVE = WORK/'results/experiments/exp78/b_strict_fair_comparison/frozen_tracker/official_22ffe24_trt/aria/aria301_305/seed0'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    archive = json.loads((ARCHIVE/'archive_manifest.json').read_text())
    events = [next(e for e in archive['events'] if e['kind']=='keyframe_update' and e['emitted_at_frame_uid']>=p)
              for p in [500,950,1400,1850,2300]]
    plan = {'scene':'aria301_305','seed':0,'event_selection':'first keyframe-update event at or after input frame 500,950,1400,1850,2300; selected before refinement results',
            'events':[{'event_id':e['event_id'],'input_prefix':e['emitted_at_frame_uid']} for e in events],
            'additional_iterations':[0,5,10,20,30,45,60,90,120],
            'evaluation':'fixed held-out cohort in preceding 300 input frames, bracketed by available causal keyframe poses',
            'representative_event':68,'inset_frame':1180,'inset_iterations':[0,30,120]}
    (OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    lock=json.loads((WORK/'results/figure03_convergence_20260921/aria301_305/source_lock.json').read_text())
    unused={'run_exp78b_stage6rx4_cross_sequence.py','run_exp91_normalized_metric_v2_reliable.py','run_exp94_normalized_metric_v2_fixed_eval.py'}
    changes=[p for p,h in lock.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    assert all(Path(p).name in unused for p in changes),changes
    (OUT/'source_audit.json').write_text(json.dumps({'active_sources_match':True,'changed_unused_launchers':changes},indent=2)+'\n')
    for event in events:
        for arm in ['ours','baseline']:
            dest=OUT/f"event_{event['event_id']:03d}"/arm
            if (dest/'refinement_manifest.json').exists():
                continue
            active=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],text=True).strip()
            assert not active,active
            dest.parent.mkdir(exist_ok=True)
            cmd=[sys.executable,str(ROOT/'scripts/capture_refinement.py'),'--arm',arm,'--event',str(event['event_id']),'--output',str(dest)]
            print('START',event['event_id'],arm,flush=True)
            with (dest.parent/f'{arm}.log').open('wb') as f:
                subprocess.run(cmd,cwd=WORK,env=mapping_environment(arm=='ours'),stdout=f,stderr=subprocess.STDOUT,check=True)
            print('DONE',event['event_id'],arm,flush=True)


if __name__=='__main__':
    main()
