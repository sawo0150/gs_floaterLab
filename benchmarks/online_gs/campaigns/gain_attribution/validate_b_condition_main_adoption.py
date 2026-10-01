"""Exercise the official selected-mapping entry point after adopting B in main."""
import json, subprocess, sys
from pathlib import Path
import run_dense_depth_four_scene as P

OUT = P.ROOT/'results/campaigns/gain_attribution/b_condition_main_adoption/v1'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows=[]
    for key, (dataset, scene) in P.SCENES.items():
        out=OUT/key
        old=P.RESULT/key/'seed0/kf_rgbd_dense_rgb'
        cmd=[str(P.trial.BASE.PYTHON_ENV/'bin/python'),str(P.MAIN/'scripts/selected_mapping/run.py'),
             '--dataset',key,'--output',str(out),'--reference',str(old/'render_result.json'),'--evaluate']
        P.write(OUT/f'{key}_command.json',cmd)
        print('START',key,flush=True)
        with (OUT/f'{key}_launcher.log').open('x') as f:
            subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
        x=P.read(out/'render_result.json');previous=P.read(old/'render_result.json')
        assert x['valid_execution'] and all(x['checks'].values())
        assert x['main_optimizer_steps']==previous['main_optimizer_steps']
        prefix=lambda q:[(v['uid'],v['training_renders']) for v in q['render_prefixes']]
        assert prefix(x)==prefix(previous)
        trace=lambda q:[(g['policy']['generation'],s['uids'],s['roles'],s['dense_anchors']) for g in q['training']['generations'] for s in g['services']]
        assert trace(x)==trace(previous)
        for name in ['traj_full_beforeBA.txt','traj_kf_beforeBA.txt']: assert P.sha(out/name)==P.sha(old/name)
        metric=lambda p:P.read(p/'psnr/strict_fixed_manifest/final_result.json')
        cohort=lambda q:[(v['uid'],v['frame_index'],v['predeclared_fixed_manifest_split']) for v in q['per_view']]
        m,oldm=metric(out),metric(old)
        assert cohort(m)==cohort(oldm)
        assert m['predeclared_fixed_manifest_posthoc']['mapping_disjoint']
        assert P.read(out/'evaluation_consistency.json')['pass']
        psnr=m['predeclared_fixed_manifest_posthoc']['mean_psnr'];oldpsnr=oldm['predeclared_fixed_manifest_posthoc']['mean_psnr']
        assert abs(psnr-oldpsnr)<=.05,(scene,psnr,oldpsnr)
        g=P.read(out/'geometry_runtime.json');oldg=P.read(old/'geometry_runtime.json')
        assert g['config']==oldg['config'] and g['dense_config']==oldg['dense_config']
        assert g['stats']==oldg['stats'] and g['raster_sha']==oldg['raster_sha']
        assert g['warp_backward']=='1' and g['condition']=='B'
        row=dict(scene=scene,key=key,psnr=psnr,reference_psnr=oldpsnr,delta_db=psnr-oldpsnr,
                 gaussians=x['gaussians'],updates=x['main_optimizer_steps'],mapping_seconds=x['mapping_seconds'],
                 same_prefix_trace_pose_cohort=True,matched_loss_and_raster=True,double_evaluation_pass=True,
                 passed=True,output=str(out),reference=str(old),ply_sha256=P.sha(out/'3dgs_before_final.ply'))
        rows.append(row);P.write(OUT/'summary.json',rows)
        print('DONE',key,psnr,'delta',psnr-oldpsnr,flush=True)
    print('B_MAIN_ADOPTION_VALIDATED',flush=True)

if __name__=='__main__':main()
