"""Fresh main fixed40 vs official vanilla, one pair per requested scene."""
import argparse,json,subprocess,traceback
from pathlib import Path
import run_online_dense_training as trial
import run_init_density_panel as prior
import run_protected_prune_comparison as prune
HERE=Path(__file__).resolve().parent
ROOT=trial.BASE.WORKSPACE
MAIN=Path('/home/intern/VIGS-SLAM-custom')
CARD='campaigns/06_gain_attribution/main_validation/README.md'
SCENES={'aria':'aria1253','rpng':'table_06','utmm':'square-1'}
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,default=str)+'\n')
def journal(row):
 msg=f"**2026-09-29 main validation {row['dataset']}/{row['arm']}:** PSNR={row.get('psnr')}, audit={row.get('pass')}, error={row.get('error')}; {row['output']}."
 with (ROOT/'context/experiments'/CARD).open('a') as f:f.write('\n'+msg+'\n')
 for rel,head,link in [('context/STATUS.md','## 최근 흐름 (최신순)\n','experiments/'+CARD),('context/experiments/INDEX.md','# Experiment Index\n',CARD)]:
  p=ROOT/rel;s=p.read_text();assert head in s;p.write_text(s.replace(head,head+'\n- '+msg+' → [카드]('+link+')\n',1))
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--datasets',nargs='+',choices=list(SCENES),default=list(SCENES));a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
 commit=subprocess.check_output(['git','-C',str(MAIN),'rev-parse','HEAD'],text=True).strip();assert commit.startswith('5fa8c76e')
 write(a.output/'protocol.json',{'main_commit':commit,'recipe':read(MAIN/'configs/selected_mapping_fixed40.json'),'datasets':a.datasets,'fresh_vanilla':True,'fixed_work_not_live':True})
 rows=[]
 for d in a.datasets:
  scene=SCENES[d]
  for arm in ['ours','vanilla']:
   trial.common.evaluation.panel.v2.gpu_idle()
   out=a.output/d/arm;out.parent.mkdir(parents=True,exist_ok=True)
   if arm=='ours':
    cmd=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(MAIN/'scripts/selected_mapping/run.py'),'--dataset',d,'--output',str(out),'--evaluate'];env=None
   else:
    cmd=[str(trial.BASE.PYTHON_ENV/'bin/python'),str(HERE/'run_kf15_vanilla.py'),'--dataset',d,'--scene',scene,'--reference',str(out.parent/'ours/render_result.json'),'--output',str(out),'--renders-per-kf','40','--seed','0'];env=trial.BASE.mapping_environment(False);env['PYTHONPATH']=str(ROOT/'benchmarks/online_gs')+':'+env['PYTHONPATH']
   write(out.parent/(arm+'_command.json'),cmd);print('START',d,arm,flush=True)
   with (out.parent/(arm+'_launcher.log')).open('x') as f:code=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
   row={'dataset':d,'scene':scene,'arm':arm,'output':str(out),'returncode':code,'pass':False,'error':None}
   try:
    assert code==0
    x=read(out/'render_result.json');assert x['valid_execution']
    ev=trial.common.evaluation.panel.run_evaluation_twice(out,d,scene,trial.BASE.sequence_paths(d,scene)['fixed_manifest']);assert ev['pass']
    if arm=='ours':
     audit=prior.audit_run(out,d,{'kappa':16,'tau':4.,'blur':False,'selector':'ervs','renders_per_kf':40,'batch_quotas':(3,3,6)})
     audit.pop('densify_prune_off',None);audit.update(prune.final_map_count_audit(out,x));top=x['densify_prune_ablation'];assert top['threshold']==.1 and top['period_completed_renders']==300 and top['protect_recent_birth_batches']==10
     assert all(e['protected_removed']==0 and e['alignment_pass'] for e in top['events']);assert x['birth_density']['downsample_multiplier']==.8
    else:
     ours=read(out.parent/'ours/render_result.json');assert x['render_counts']==ours['render_counts'];assert [(z['uid'],z['training_renders']) for z in x['render_prefixes']]==[(z['uid'],z['training_renders']) for z in ours['render_prefixes']]
     for name in ['traj_full_beforeBA.txt','traj_kf_beforeBA.txt']:assert (out/name).read_bytes()==(out.parent/'ours'/name).read_bytes()
     m=read(out/'psnr/strict_fixed_manifest/final_result.json');om=read(out.parent/'ours/psnr/strict_fixed_manifest/final_result.json');assert [(z['uid'],z['predeclared_fixed_manifest_split']) for z in m['per_view']]==[(z['uid'],z['predeclared_fixed_manifest_split']) for z in om['per_view']]
     audit={'pass':True,'same_prefix_work':True,'same_eval_trajectory_cohort':True,'checks':x['checks']}
    write(out/'main_validation_audit.json',audit)
    assert subprocess.check_output(['git','-C',str(MAIN),'rev-parse','HEAD'],text=True).strip()==commit
    row.update({'pass':True,'psnr':ev['fixed_psnr_first'],'gaussians':x['gaussians'],'mapping_seconds':x['mapping_seconds'],'renders':x['render_counts'],'adam':x.get('main_optimizer_steps'),'checks':x['checks']})
   except Exception:row['error']=traceback.format_exc()
   rows.append(row);write(a.output/'summary.json',rows);journal(row);print('DONE',d,arm,row.get('psnr'),row['pass'],flush=True)
   if not row['pass']:raise RuntimeError(row['error'])
 print('MAIN_VALIDATION_COMPLETE',flush=True)
if __name__=='__main__':main()
