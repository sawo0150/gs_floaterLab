"""Sequential actual-tracker FIFO comparison; 1.5x means more wall time."""
import argparse
import json
import subprocess
import traceback
from pathlib import Path
import run_online_dense_training as trial
import main_validation_rot_adapter as rot

ROOT=trial.BASE.WORKSPACE
HERE=Path(__file__).resolve().parent
MAIN=Path('/home/intern/VIGS-SLAM-custom')
SCENES={'aria':('aria','aria1253'),'rpng':('rpng','table_06'),'utmm':('utmm','square-1'),'rot':('aria','aria1253rot')}
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,default=str)+'\n')
def journal(row):
    rel='campaigns/06_gain_attribution/fifo_live/README.md'
    r=row.get('runtime') or {}
    msg=(f"2026-09-30 live FIFO {row['time_scale']}x {row['key']}/{row['arm']}: "
         f"PSNR={row.get('psnr')}, execution={row['valid_execution']}, "
         f"tracking={r.get('tracking_elapsed_seconds')}s / budget={r.get('duration_seconds')}s; "
         f"{row['output']}")
    with (ROOT/'context/experiments'/rel).open('a') as f:f.write('\n'+msg+'\n')
    for name,head,link in [('context/STATUS.md','## 최근 흐름 (최신순)\n','experiments/'+rel),('context/experiments/INDEX.md','# Experiment Index\n',rel)]:
        p=ROOT/name;s=p.read_text();assert head in s
        p.write_text(s.replace(head,head+'\n- '+msg+' → [card]('+link+')\n',1))
def environment(arm):
    env=trial.BASE.mapping_environment(arm=='ours')
    paths=[ROOT/'benchmarks/online_gs',HERE]
    if arm=='ours':
        ext=trial.ROOT/'live_worker_integration_audit/v6_current_stream_extensions'
        paths=[ROOT/'results/campaigns/gain_attribution/geometry_main_validation/raster_fixed',ext/'vigs_backends',ext/'lietorch_backends',MAIN/'vigs',MAIN,MAIN/'scripts/selected_mapping',MAIN/'scripts/selected_mapping/geometry_merge']+paths
        env.update(EXP78B_CUSTOM_ROOT=str(MAIN),FIXED40_KF_LOSS='d3',FIXED40_DENSE_SCOPE='full',FR_WARP_BWD='1',VIGS_PIPELINE_TELEMETRY='1')
    else:
        paths=[trial.BASE.OFFICIAL_ROOT/'vigs',trial.BASE.OFFICIAL_ROOT,MAIN/'vigs',MAIN/'scripts/selected_mapping',trial.BASE.BUILT_THIRDPARTY_ROOT]+paths
    env['PYTHONPATH']=':'.join(map(str,paths))+':'+env.get('PYTHONPATH','')
    return env
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--keys',nargs='+',choices=list(SCENES),default=list(SCENES))
    p.add_argument('--scales',nargs='+',type=float,default=[1.,1.5])
    p.add_argument('--arms',nargs='+',choices=['ours','vanilla'],default=['ours','vanilla'])
    a=p.parse_args();rot.install();a.output.mkdir(parents=True,exist_ok=True)
    summary=a.output/'summary.json';rows=read(summary) if summary.exists() else []
    cwd=ROOT/'results/experiments/exp78/a_paper_reproduction/trt_profiles/official_readme_dynamic_rtx5090'
    for scale in a.scales:
      for key in a.keys:
       dataset,scene=SCENES[key]
       for arm in a.arms:
        if any(r['key']==key and r['arm']==arm and r['time_scale']==scale and r['valid_execution'] and r.get('psnr') is not None for r in rows):continue
        out=a.output/('scale'+format(scale,'g').replace('.','p'))/key/arm
        row={'key':key,'dataset':dataset,'scene':scene,'arm':arm,'time_scale':scale,'output':str(out),'valid_execution':False}
        print('START',scale,key,arm,flush=True)
        try:
          if not (out/'export.json').exists():
            out.mkdir(parents=True,exist_ok=False)
            trial.common.evaluation.panel.v2.gpu_idle()
            runner=HERE/('measure_fifo_live_'+arm+'.py')
            cmd=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(runner),'--worker','--dataset',key,'--time-scale',str(scale),'--queue-size','2','--renders-per-kf','40','--output',str(out)]
            if arm=='ours':cmd+=['--frontend-iters','official']
            env=environment(arm)
            write(out/'command.json',{'cmd':cmd,'env':{k:v for k,v in env.items() if k in ['PYTHONPATH','EXP78B_CUSTOM_ROOT','FIXED40_KF_LOSS','FIXED40_DENSE_SCOPE','FR_WARP_BWD']}})
            with (out/'run.log').open('x') as f:subprocess.run(cmd,env=env,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,check=True)
          r=read(out/'result.json');row['runtime']=r
          assert not r['error'] and r['source_unchanged'] and r['zero_tail_observed']
          assert r['tracked_frames']==r['input_frames'] and not r['worker']['error']
          assert read(out/'export.json')['finite']
          trial.common.evaluation.panel.v2.gpu_idle()
          ev=trial.common.evaluation.panel.run_evaluation_twice(out,dataset,scene,trial.BASE.sequence_paths(dataset,scene)['fixed_manifest'])
          assert ev['pass'],ev
          row.update(valid_execution=True,psnr=ev['fixed_psnr_first'],evaluation=ev,export=read(out/'export.json'),elapsed_over_budget_seconds=r['tracking_elapsed_seconds']-r['duration_seconds'])
        except Exception:row['error']=traceback.format_exc()
        rows=[r for r in rows if not (r['key']==key and r['arm']==arm and r['time_scale']==scale)]+[row]
        write(summary,rows);journal(row)
        print('DONE',scale,key,arm,row.get('psnr'),row['valid_execution'],flush=True)
        if not row['valid_execution']:raise RuntimeError(row['error'])
    print('LIVE_FIFO_COMPLETE',flush=True)
if __name__=='__main__':main()
