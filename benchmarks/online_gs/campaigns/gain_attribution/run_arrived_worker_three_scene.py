#!/usr/bin/env python3
"""One source/policy across the three predeclared online worker scenes."""
import json
from pathlib import Path
import subprocess
import sys
import run_online_dense_training as trial


def main():
    root=trial.ROOT/'live_worker_integration_audit'
    output=root/'v9_productive_worker/three_scene'
    output.mkdir(parents=True,exist_ok=False)
    backend=Path('/home/intern/VIGS-SLAM-online-worker-integration')
    env=trial.environment();env['EXP78B_CUSTOM_ROOT']=str(backend)
    env['PYTHONPATH']=str(backend/'vigs')+':'+str(backend)+':'+env['PYTHONPATH']
    scripts=Path(__file__).resolve().parent
    rows=[]
    for dataset,scene in [('rpng','table_06'),('utmm','square-1'),('aria','aria1253')]:
        setup=root/'v5_packet_identity/aria_setup' if dataset=='aria' else output/(dataset+'_setup')
        if dataset!='aria':
            trial.common.evaluation.panel.v2.gpu_idle()
            command=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(scripts/'capture_online_worker_setup.py'),
                '--dataset',dataset,'--scene',scene,'--output',str(setup)]
            subprocess.run(command,env=env,check=True)
        pair=output/(dataset+'_seed0')
        command=[sys.executable,str(scripts/'run_arrived_worker_pair.py'),
            '--setup',str(setup),'--extensions',str(root/'v6_current_stream_extensions'),
            '--output',str(pair)]
        subprocess.run(command,check=True)
        arms=json.loads((pair/'pair_progress.json').read_text())
        rows.append({'dataset':dataset,'scene':scene,'arms':arms,
                     'dense_minus_kf_db':arms[0]['heldout_psnr']-arms[1]['heldout_psnr']})
        (output/'panel_progress.json').write_text(json.dumps(rows,indent=2))
    print('THREE_SCENE_COMPLETE',json.dumps(rows),flush=True)


if __name__=='__main__':main()
