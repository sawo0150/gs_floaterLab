#!/usr/bin/env python3
"""Tracker-only control for live budget measurement, same raw inputs and engines."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import measure_live_render_capacity as measurement


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dataset',default='rpng')
    p.add_argument('--frontend-iters',choices=['official','current'],default='official')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--worker',action='store_true')
    a=p.parse_args()
    if not a.worker:
        measurement.trial.common.evaluation.panel.v2.gpu_idle()
        a.output.mkdir(parents=True,exist_ok=False)
        env=measurement.trial.environment()
        env['EXP78B_CUSTOM_ROOT']=str(measurement.BACKEND)
        env['PYTHONPATH']=str(measurement.BACKEND/'vigs')+':'+str(measurement.BACKEND)+':'+env['PYTHONPATH']
        cmd=[str(measurement.trial.BASE.PYTHON_ENV/'bin/python'),str(Path(__file__).resolve()),
             '--worker','--dataset',a.dataset,'--frontend-iters',a.frontend_iters,'--output',str(a.output.resolve())]
        measurement.write(a.output/'command.json',cmd)
        cwd=measurement.ROOT/'results/experiments/exp78/a_paper_reproduction/trt_profiles/official_readme_dynamic_rtx5090'
        with (a.output/'run.log').open('x') as log:
            r=subprocess.run(cmd,env=env,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
        raise SystemExit(r.returncode)
    for name in ('vigs_backends','lietorch_backends'):
        sys.path.insert(0,str(measurement.AUDIT_ROOT/'v6_current_stream_extensions'/name))
    import vigs
    import export_live_capacity_map
    original=vigs.VIGS.__init__
    def init(host,*args,**kwargs):
        original(host,*args,**kwargs)
        host.gsmapping=False
        host.video.gs=None
    vigs.VIGS.__init__=init
    export_live_capacity_map.export=lambda *args,**kwargs:None
    sys.argv=[str(Path(measurement.__file__).resolve()),'--worker','--dataset',a.dataset,
              '--frontend-iters',a.frontend_iters,'--renders-per-kf','0','--output',str(a.output)]
    measurement.main()
    path=a.output/'result.json';result=json.loads(path.read_text())
    result['protocol']='tracking_only_capacity_control'
    assert result['training_renders']==0
    measurement.write(path,result)


if __name__=='__main__':main()
