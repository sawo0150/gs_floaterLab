"""Scene-path adapter only; run unchanged main worker with adopted argv on rot."""
import argparse,json,sys,runpy
from pathlib import Path
import run_online_dense_training as trial
ROOT=trial.BASE.WORKSPACE
INPUT=ROOT/'results/campaigns/gain_attribution/main_validation/rot_inputs'
MAIN=Path('/home/intern/VIGS-SLAM-custom')
SCENE='aria1253rot'
def install():
 old_paths=trial.BASE.sequence_paths;old_eval=trial.BASE.evaluation_command
 def paths(d,s):
  if (d,s)!=('aria',SCENE):return old_paths(d,s)
  return {'archive':INPUT/'archive','fixed_manifest':INPUT/'heldout.json','custom_config':ROOT/'benchmarks/online_gs/config/vigs_final_v7_aria.yaml','vanilla_config':ROOT/'benchmarks/online_gs/config/vigs_official_aria_adapter.yaml','image_dir':INPUT/SCENE/'rgb','calibration':MAIN/'calib/aria1253rot.txt'}
 def evaluate(out,d,s):
  if (d,s)!=('aria',SCENE):return old_eval(out,d,s)
  x=paths(d,s)
  return [str(trial.BASE.PYTHON_ENV/'bin/python'),str(trial.BASE.EVALUATOR),'--run-dir',str(out),'--image-dir',str(x['image_dir']),'--calib',str(x['calibration']),'--manifest',str(x['fixed_manifest']),'--rgb-file-in-nanoseconds','--mapped-uids-json',str(out/'mapped_uids.json'),'--result-subdir','strict_fixed_manifest']
 trial.BASE.sequence_paths=paths;trial.BASE.evaluation_command=evaluate
 return paths

def main():
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['setup','ours','vanilla'],required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reference',type=Path);a=p.parse_args();install()
 if a.mode=='setup':
  import capture_online_worker_setup as c
  sys.argv=[c.__file__,'--dataset','aria','--scene',SCENE,'--output',str(a.output)];c.main();return
 if a.mode=='ours':
  worker=MAIN/'scripts/selected_mapping/run_kf15_render_worker.py';recipe=json.loads((MAIN/'configs/selected_mapping_fixed40.json').read_text())['worker_args'];ext=trial.ROOT/'live_worker_integration_audit/v6_current_stream_extensions'
  sys.path.insert(0,str(worker.parent))
  sys.argv=[str(worker),*recipe,'--setup',str(INPUT/'setup'),'--extensions',str(ext),'--output',str(a.output)]
 else:
  worker=Path(__file__).with_name('run_kf15_vanilla.py')
  sys.argv=[str(worker),'--dataset','aria','--scene',SCENE,'--reference',str(a.reference),'--output',str(a.output),'--renders-per-kf','40','--seed','0']
 runpy.run_path(str(worker),run_name='__main__')
if __name__=='__main__':main()
