"""Prepare causal official tracker archive then compare fixed40 main vs vanilla on rot."""
import argparse,json,subprocess,sys,hashlib,traceback
from pathlib import Path
import run_online_dense_training as trial
import main_validation_rot_adapter as adapter
import run_main_validation as panel
import run_protected_prune_comparison as prune
ROOT,HERE,MAIN=panel.ROOT,panel.HERE,panel.MAIN
INPUT=adapter.INPUT
read=panel.read;write=panel.write

def run(cmd,log,env,cwd=None):
 trial.common.evaluation.panel.v2.gpu_idle()
 write(log.with_suffix('.command.json'),cmd)
 with log.open('x') as f:subprocess.run(cmd,env=env,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,check=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
 adapter.install();base=trial.BASE;py=str(base.PYTHON_ENV/'bin/python');official=base.mapping_environment(False);official['PYTHONPATH']=str(base.OFFICIAL_ROOT)+':'+str(ROOT/'benchmarks/online_gs')+':'+str(base.BUILT_THIRDPARTY_ROOT)+':'+official['PYTHONPATH']
 custom=trial.environment();custom['EXP78B_CUSTOM_ROOT']=str(MAIN);custom['PYTHONPATH']=str(MAIN/'vigs')+':'+str(MAIN)+':'+str(HERE)+':'+custom['PYTHONPATH']
 commit=subprocess.check_output(['git','-C',str(MAIN),'rev-parse','HEAD'],text=True).strip();assert commit.startswith('5fa8c76e')
 source={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in list((MAIN/'vigs').rglob('*.py'))+list((MAIN/'scripts/selected_mapping').glob('*.py'))+[MAIN/'configs/selected_mapping_fixed40.json',Path(__file__).resolve(),Path(adapter.__file__).resolve()]}
 write(a.output/'source_lock.json',source)
 paths=base.sequence_paths('aria',adapter.SCENE)
 if not (INPUT/'archive/archive_manifest.json').exists():
  print('START rot official tracker capture',flush=True)
  cmd=[py,str(ROOT/'benchmarks/online_gs/exp78b_capture_frozen_tracker.py'),'--dataset','aria','--sequence',adapter.SCENE,'--imagedir',str(paths['image_dir']),'--imufile',str(INPUT/adapter.SCENE/'imu.txt'),'--calib',str(paths['calibration']),'--config',str(paths['vanilla_config']),'--weights',str(base.OFFICIAL_ROOT/'pretrained_models/droid.pth'),'--output',str(INPUT/'archive'),'--heldout-manifest',str(paths['fixed_manifest']),'--seed','0','--length','1521','--buffer','700','--IMU_poseinit_after','20']
  run(cmd,a.output/'capture.log',official,base.BUILT_THIRDPARTY_ROOT)
 run([py,str(base.ARCHIVE_VALIDATOR),str(INPUT/'archive'),'--output',str(a.output/'archive_validation.json')],a.output/'archive_validation.log',official)
 if not (INPUT/'setup/native_setup.pt').exists():
  run([py,str(Path(adapter.__file__)),'--mode','setup','--output',str(INPUT/'setup')],a.output/'setup.log',custom)
 rows=[]
 for arm in ['ours','vanilla']:
  out=a.output/arm;print('START rot',arm,flush=True)
  cmd=[py,str(Path(adapter.__file__)),'--mode',arm,'--output',str(out)]
  if arm=='vanilla':cmd+=['--reference',str(a.output/'ours/render_result.json')]
  row={'dataset':'aria_rot','scene':adapter.SCENE,'arm':arm,'output':str(out),'pass':False,'error':None}
  try:
   run(cmd,a.output/(arm+'_launcher.log'),custom if arm=='ours' else official)
   x=read(out/'render_result.json');assert x['valid_execution'] and all(x['checks'].values())
   ev=trial.common.evaluation.panel.run_evaluation_twice(out,'aria',adapter.SCENE,paths['fixed_manifest']);assert ev['pass']
   if arm=='ours':
    assert x['batch_quotas']==[3,3,6] and x['schedule']=='unified' and x['selector']=='ervs' and x['kappa']==16 and x['tau']==4 and x['birth_density']['downsample_multiplier']==.8
    assert x['main_optimizer_steps']==x['render_counts']['training']==40*x['kf_render_budget']['kf_admissions']
    top=x['densify_prune_ablation'];assert top['pass'] and top['threshold']==.1 and top['period_completed_renders']==300 and top['protect_recent_birth_batches']==10
    assert all(e['protected_removed']==0 and e['alignment_pass'] and e['completed_at']<=x['last_input_at'] for e in top['events'])
    audit=prune.final_map_count_audit(out,x)
   else:
    ours=read(a.output/'ours/render_result.json');assert x['render_counts']==ours['render_counts']
    assert [(r['uid'],r['training_renders']) for r in x['render_prefixes']]==[(r['uid'],r['training_renders']) for r in ours['render_prefixes']]
    for name in ['traj_full_beforeBA.txt','traj_kf_beforeBA.txt']:assert (out/name).read_bytes()==(a.output/'ours'/name).read_bytes()
    ours_metric=read(a.output/'ours/psnr/strict_fixed_manifest/final_result.json');m=read(out/'psnr/strict_fixed_manifest/final_result.json');assert [(r['uid'],r['predeclared_fixed_manifest_split']) for r in m['per_view']]==[(r['uid'],r['predeclared_fixed_manifest_split']) for r in ours_metric['per_view']]
    audit={'same_prefix_work_and_trajectory_cohort':True}
   assert not [p for p,h in source.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
   audit.update(pass_=True,source_unchanged=True,checks=x['checks']);write(out/'main_validation_audit.json',audit)
   row.update({'pass':True,'psnr':ev['fixed_psnr_first'],'gaussians':x['gaussians'],'mapping_seconds':x['mapping_seconds'],'renders':x['render_counts'],'adam':x.get('main_optimizer_steps')})
  except Exception:row['error']=traceback.format_exc()
  rows.append(row);write(a.output/'summary.json',rows);panel.journal(row);print('DONE rot',arm,row.get('psnr'),row['pass'],flush=True)
  if not row['pass']:raise RuntimeError(row['error'])
 print('MAIN_ROT_VALIDATION_COMPLETE',flush=True)
if __name__=='__main__':main()
