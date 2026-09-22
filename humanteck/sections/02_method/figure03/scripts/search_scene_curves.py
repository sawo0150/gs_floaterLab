#!/usr/bin/env python3
"""Measure three alternative native system curves; preserve all outcomes."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from run_convergence_pair import mapping_environment

WORK=Path('/home/intern/gs_floaterLab')
ROOT=Path(__file__).resolve().parent.parent
SOURCE=WORK/'results/experiments/exp94_normalized_metric_v2_fixed_eval'
OUT=WORK/'results/figure03_scene_search_20260921'
PANEL=[('utmm','square-1',50),('rpng','table_01',200),('rpng','table_06',200)]


def main():
    OUT.mkdir(exist_ok=True)
    (OUT/'plan.json').write_text(json.dumps({'panel':PANEL,'selection':'Table01/table06: final gap plus existing visual candidates; square-1: no pose-scale correction and largest endpoint gain among no-correction UTMM sequences. Exploratory illustration search, not a predeclared validation benchmark.','curves':'Same full fixed held-out sets and native cumulative Gaussian Adam steps as Fig3 A; preserve all candidate results without smoothing.'},indent=2)+'\n')
    lock=json.loads((OUT.parent/'figure03_convergence_20260921/aria301_305/source_lock.json').read_text())
    unused={'run_exp78b_stage6rx4_cross_sequence.py','run_exp91_normalized_metric_v2_reliable.py','run_exp94_normalized_metric_v2_fixed_eval.py'}
    changes=[p for p,h in lock.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    assert all(Path(p).name in unused for p in changes),changes
    (OUT/'source_audit.json').write_text(json.dumps({'active_sources_match':True,'changed_unused_launchers':changes},indent=2)+'\n')
    for family,scene,interval in PANEL:
        dest=OUT/family/scene;dest.mkdir(parents=True,exist_ok=True)
        for arm,old in [('ours','normalized_variance_s0'),('baseline','native_vanilla_render_matched_s0')]:
            target=dest/arm
            if (target/'capture_manifest.json').exists():continue
            active=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],text=True).strip()
            assert not active,active
            target.mkdir(exist_ok=True)
            cmd=[sys.executable,str(ROOT/'scripts/capture_convergence.py'),'--arm',arm,'--source-run',str(SOURCE/family/scene/old),'--output',str(target),'--checkpoint-interval',str(interval)]
            if arm=='baseline':cmd+=['--reference-runtime',str(dest/'ours/mapping_replay_runtime.json')]
            print('START',family,scene,arm,flush=True)
            with (target/'mapping.log').open('wb') as f:
                subprocess.run(cmd,cwd=WORK,env=mapping_environment(arm=='ours'),stdout=f,stderr=subprocess.STDOUT,check=True)
            runtime=json.loads((target/'mapping_replay_runtime.json').read_text())
            ref=json.loads((SOURCE/family/scene/old/'mapping_replay_runtime.json').read_text())
            assert runtime['rasterized_view_updates']==ref['rasterized_view_updates']
            print('DONE',scene,arm,runtime['optimizer_steps_completed'],flush=True)
        with (dest/'evaluation.log').open('wb') as f:
            subprocess.run([sys.executable,str(ROOT/'scripts/evaluate_scene_curves.py'),'--family',family,'--scene',scene],cwd=WORK,env=mapping_environment(True),stdout=f,stderr=subprocess.STDOUT,check=True)
        print('EVALUATED',scene,flush=True)


if __name__=='__main__':main()
