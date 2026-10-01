"""Independent-reference evaluation only. Never loads references into training."""
import argparse, importlib.util, json, os, subprocess, sys
from pathlib import Path
import run_dense_depth_four_scene as panel

MPS = {
    'aria1253': Path('/home/intern/aria_data/0416_Data/0416_301-1253/mps_0416_301-1253_vrs/slam'),
    'aria1253rot': Path('/home/intern/aria_data/0416_Data/0416_301-1253-2_rot/mps_0416_301-1253-2_vrs/slam'),
}
def worker(a):
    panel.rot.install()
    sys.path.insert(0, str(panel.GEOM))
    import local_paths as L
    L.sequence_paths = panel.trial.BASE.sequence_paths
    L.install = lambda: panel.trial
    import evaluate_mps_fixed40 as M
    M.MPS.update(MPS)
    M.ALIGN = 'local'
    if a.stage == 'cache':
        import torch
        from exp78b_frozen_archive import FrozenTrackerArchive
        scene = panel.SCENES[a.key][1]
        archive = FrozenTrackerArchive(L.sequence_paths('aria', scene)['archive'])
        cache = L.OUT/'mps_ref'/f'{scene}_d{M.DIST_STD:g}_w{M.WINDOW_S:g}.pt'
        ref = torch.load(cache, weights_only=False) if cache.exists() else M.build_reference(archive, scene, cache)
        lcache = cache.with_name(cache.stem+f'_local{M.LOCAL_KF}.pt')
        local = torch.load(lcache, weights_only=False) if lcache.exists() else M.local_alignment(archive, scene, ref, lcache)
        print(dict(scene=scene, points=ref['points'], global_alignment_rms=ref['align_rms'], local_kf=local['local_kf'], time_gap_us=ref['max_time_gap_us']),flush=True)
    elif a.stage == 'mps':
        sys.argv = ['evaluate_mps_fixed40', '--run-dir',str(a.output),'--dataset','aria','--scene',panel.SCENES[a.key][1]]
        M.main()
    else:
        import termination_metrics as T
        sys.argv = ['termination_metrics', '--run-dir',str(a.output),'--scene',panel.SCENES[a.key][1]]
        T.main()
def main(a):
    sys.path.insert(0, str(panel.MAIN/'scripts/selected_mapping'))
    from selected_mapping_check import gpu_idle
    provenance = dict(evaluation_only=True, mps_used_in_training=False, alignment='local Sim3 nearest 30 KFs, fixed across arms',
        sources={str(p):panel.sha(p) for p in [Path(__file__),panel.GEOM/'evaluate_mps_fixed40.py',panel.GEOM/'termination_metrics.py',panel.GEOM/'raycount.cu']},
        references={str(p):panel.sha(p) for root in MPS.values() for p in root.iterdir() if p.name in ['closed_loop_trajectory.csv','online_calibration.jsonl','semidense_points.csv.gz','semidense_observations.csv.gz']},
        reference_cache={str(p):panel.sha(p) for p in (panel.RESULT/'mps_ref').glob('*.pt')})
    panel.write(panel.RESULT/'independent_geometry_provenance.json',provenance)
    for key in a.keys:
      for seed in a.seeds:
       for arm in a.arms:
        out = panel.RESULT/key/f'seed{seed}'/arm
        assert panel.read(out.parent/f'{arm}_summary.json')['passed']
        original_hashes={name:panel.sha(out/name) for name in ['3dgs_before_final.ply','traj_full_beforeBA.txt','traj_kf_beforeBA.txt']}
        env = panel.environment(arm)
        env.update(MPS_ALIGN='local',MPS_LOCAL_KF='30',MAX_JOBS='4')
        for stage,marker in [('mps','geometry_mps_local.json'),('termination','termination_mps_local.json')]:
            if (out/marker).exists(): continue
            gpu_idle()
            print('START',key,seed,arm,stage,flush=True)
            cmd = [str(panel.trial.BASE.PYTHON_ENV/'bin/python'),str(Path(__file__).resolve()),'--stage',stage,'--key',key,'--output',str(out)]
            with (out.parent/f'{arm}_{stage}.log').open('a') as f: subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
            print('DONE',key,seed,arm,stage,flush=True)
        assert all(panel.sha(out/name)==h for name,h in original_hashes.items())
        panel.write(out/'independent_geometry_input_audit.json',dict(unchanged_inputs=True,sha256=original_hashes))
    if 'aria' in a.keys:
        import evaluate_cvpr_regions as R
        for p,h in R.EXPECTED.items(): assert panel.sha(p)==h
        spec=importlib.util.spec_from_file_location('original_manual_region',R.EVALUATOR)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        runs=[(f'{arm}__seed{seed}',panel.RESULT/'aria'/f'seed{seed}'/arm) for seed in a.seeds for arm in a.arms]
        result=module.evaluate('aria1253',runs,R.POSES,R.MASK)
        result['provenance']=dict(evaluation_only=True,assets={str(p):panel.sha(p) for p in R.EXPECTED},evaluator_sha256=panel.sha(R.EVALUATOR))
        panel.write(panel.RESULT/'manual_region.json',result)
    print('INDEPENDENT_GEOMETRY_COMPLETE',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['cache','mps','termination']);p.add_argument('--key',choices=['aria','rot']);p.add_argument('--output',type=Path)
    p.add_argument('--keys',nargs='+',default=['aria','rot']);p.add_argument('--seeds',type=int,nargs='+',default=[0,1]);p.add_argument('--arms',nargs='+',default=panel.ARMS)
    a=p.parse_args()
    worker(a) if a.stage else main(a)
