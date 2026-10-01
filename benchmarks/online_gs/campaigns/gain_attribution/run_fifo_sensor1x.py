"""Validate merged optional D3 against fresh official vanilla on pinned inputs."""
import argparse, atexit, hashlib, json, os, runpy, subprocess, sys, traceback
from pathlib import Path
import run_online_dense_training as trial
import main_validation_rot_adapter as rot
ROOT=trial.BASE.WORKSPACE
HERE=Path(__file__).resolve().parent
MAIN=Path('/home/intern/VIGS-SLAM-custom')
GEOM=MAIN/'scripts/selected_mapping/geometry_merge'
RESULT=ROOT/'results/campaigns/gain_attribution/geometry_main_validation'
CARD='campaigns/06_gain_attribution/fifo_sensor1x/README.md'
SCENES={'aria':('aria','aria1253'),'rpng':('rpng','table_06'),'utmm':('utmm','square-1'),'rot':('aria','aria1253rot')}
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,default=str)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def previous(key,arm):
 return ROOT/'results/campaigns/gain_attribution/main_validation'/('rot_gpu40_v1' if key=='rot' else 'gpu40_v1')/((arm) if key=='rot' else (key+'/'+arm))
def journal(row):
 msg=f"2026-09-30 FIFO sensor1x {row['key']}/{row['arm']}: PSNR={row.get('psnr')}, pass={row['pass']}; {row['output']}"
 with (ROOT/'context/experiments'/CARD).open('a') as f:f.write('\n'+msg+'\n')
 for name,heading,link in [('context/STATUS.md','## 최근 흐름 (최신순)\n','experiments/'+CARD),('context/experiments/INDEX.md','# Experiment Index\n',CARD)]:
  p=ROOT/name;s=p.read_text();assert heading in s;p.write_text(s.replace(heading,heading+'\n- '+msg+' → [card]('+link+')\n',1))
def worker(a):
 rot.install()
 lock=read(MAIN/'scripts/selected_mapping/source_lock.json')
 if a.worker=='vanilla':
  path=MAIN/'scripts/selected_mapping/run_fifo_vanilla_worker.py';d,s=SCENES[a.key]
  sys.argv=[str(path),'--dataset',d,'--scene',s,'--output',str(a.output),'--renders-per-kf','40','--seed','0']
 else:
  sys.path.insert(0,str(GEOM));sys.path.insert(0,str(MAIN/'scripts/selected_mapping'))
  import fixed40_geometry as g
  cfg=g.install()
  import diff_gaussian_rasterization as raster
  assert Path(raster.__file__).resolve().is_relative_to(ROOT/'results/campaigns/gain_attribution/geometry_main_validation/raster_fixed'),raster.__file__
  def dump():
   if a.output.exists():write(a.output/'geometry_runtime.json',{'config':cfg,'stats':g.STATS,'raster_module':raster.__file__,'raster_so_sha256':sha(Path(raster._C.__file__)),'maintenance':'off','warp':os.environ['FR_WARP_BWD']})
  atexit.register(dump)
  path=MAIN/'scripts/selected_mapping/run_fifo_stream_worker.py'
  setup=rot.INPUT/'setup' if a.key=='rot' else Path(lock['datasets'][a.key]['setup'])
  sys.argv=[str(path),*read(MAIN/'configs/selected_mapping_fixed40.json')['worker_args'],'--setup',str(setup),'--extensions',lock['extensions'],'--output',str(a.output)]
 runpy.run_path(str(path),run_name='__main__')
def panel(a):
 rot.install();lock=read(MAIN/'scripts/selected_mapping/source_lock.json')
 sys.path.insert(0,str(MAIN/'scripts/selected_mapping'))
 from selected_mapping_check import verify_files,gpu_idle
 verify_files(lock['sources']);verify_files(lock['extension_files'])
 for v in lock['datasets'].values():verify_files(v['files'])
 a.output.mkdir(parents=True,exist_ok=False)
 commit=subprocess.check_output(['git','-C',str(MAIN),'rev-parse','HEAD'],text=True).strip()
 source={str(p):sha(p) for p in [*MAIN.glob('vigs/**/*.py'),*MAIN.glob('scripts/selected_mapping/*.py'),*GEOM.glob('*.py'),Path(__file__)]}
 write(a.output/'source_lock.json',source)
 write(a.output/'protocol.json',{'main':commit,'recipe':read(MAIN/'configs/selected_mapping_fixed40.json'),'keys':a.keys,'extra_proxy_render_budget':True,'sensor_time_scale':1.,'queue_size':2,'concurrent_tracking':False})
 rows=[]
 for key in a.keys:
  d,s=SCENES[key]
  for arm in ['d3','vanilla']:
   gpu_idle();out=a.output/key/arm;out.parent.mkdir(parents=True,exist_ok=True)
   env=trial.BASE.mapping_environment(arm=='d3')
   parts=[str(ROOT/'benchmarks/online_gs'),str(HERE)]
   if arm=='vanilla':parts=[str(trial.BASE.OFFICIAL_ROOT/'vigs'),str(trial.BASE.OFFICIAL_ROOT),str(MAIN/'vigs'),str(MAIN/'scripts/selected_mapping')]+parts
   if arm=='d3':
    ext=Path(lock['extensions']);parts=[str(ROOT/'results/campaigns/gain_attribution/geometry_main_validation/raster_fixed'),str(ext/'vigs_backends'),str(ext/'lietorch_backends'),str(MAIN/'vigs'),str(MAIN),str(MAIN/'scripts/selected_mapping'),str(GEOM)]+parts
    env.update(EXP78B_CUSTOM_ROOT=str(MAIN),FIXED40_KF_LOSS='d3',FIXED40_DENSE_SCOPE='full',FR_WARP_BWD='1')
   env['PYTHONPATH']=':'.join(parts)+':'+env.get('PYTHONPATH','')
   ref=previous(key,'ours')/'render_result.json' if arm=='d3' else out.parent/'d3/render_result.json'
   cmd=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(Path(__file__).resolve()),'--worker',arm,'--key',key,'--output',str(out),'--reference',str(ref)]
   write(out.parent/(arm+'_command.json'),{'cmd':cmd,'environment':{k:env[k] for k in ['PYTHONPATH','EXP78B_CUSTOM_ROOT','FR_WARP_BWD','FIXED40_KF_LOSS'] if k in env}})
   print('START',key,arm,flush=True)
   row={'key':key,'dataset':d,'scene':s,'arm':arm,'output':str(out),'pass':False}
   try:
    with (out.parent/(arm+'_launcher.log')).open('x') as f:subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
    x=read(out/'render_result.json');assert x['valid_execution'] and all(x['checks'].values()),x['checks']
    ev=trial.common.evaluation.panel.run_evaluation_twice(out,d,s,trial.BASE.sequence_paths(d,s)['fixed_manifest']);assert ev['pass']
    old=previous(key,'ours')
    for n in ['traj_full_beforeBA.txt','traj_kf_beforeBA.txt']:assert sha(out/n)==sha(old/n),n
    cohort=lambda p:[(z['uid'],z['frame_index'],z['predeclared_fixed_manifest_split']) for z in read(p/'psnr/strict_fixed_manifest/final_result.json')['per_view']]
    assert cohort(out)==cohort(old)
    assert all(sha(Path(p))==h for p,h in source.items())
    geo=read(out/'geometry_runtime.json') if arm=='d3' else None
    if geo:assert geo['stats']['aux_renders']==geo['stats']['kf_d3_views']>0 and geo['stats']['soft_main_applied']<=geo['stats']['kf_d3_views']
    row.update(pass_=True,psnr=ev['fixed_psnr_first'],gaussians=x['gaussians'],mapping_seconds=x['mapping_seconds'],renders=x['render_counts'],aux_renders=geo['stats']['aux_renders'] if geo else 0,geometry=geo,same_trajectory_cohort=True,budget_seconds=x['budget_seconds'],worker=x['worker'],checks=x['checks'],main_optimizer_steps=x['main_optimizer_steps'])
    row['pass']=True
   except Exception:row['error']=traceback.format_exc()
   rows.append(row);write(a.output/'summary.json',rows);journal(row);print('DONE',key,arm,row.get('psnr'),row['pass'],flush=True)
   if not row['pass']:raise RuntimeError(row['error'])
 print('FIFO_SENSOR1X_COMPLETE',flush=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--worker',choices=['d3','vanilla']);p.add_argument('--key',choices=list(SCENES));p.add_argument('--keys',nargs='+',choices=list(SCENES),default=list(SCENES));p.add_argument('--reference',type=Path);a=p.parse_args()
 worker(a) if a.worker else panel(a)
if __name__=='__main__':main()
