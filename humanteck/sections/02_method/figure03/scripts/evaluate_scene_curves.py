#!/usr/bin/env python3
"""Full fixed held-out evaluation for alternative scene checkpoints."""
import argparse
import csv
import json
import subprocess
from pathlib import Path
from evaluate_convergence import torch,np,lietorch,Image,Camera,getProjectionMatrix2,preprocess_image,load_gaussians,render,psnr

WORK=Path('/home/intern/gs_floaterLab')
ROOT=Path(__file__).resolve().parent.parent


def main():
    p=argparse.ArgumentParser();p.add_argument('--family',required=True);p.add_argument('--scene',required=True);args=p.parse_args()
    active=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],text=True).strip();assert not active,active
    run=WORK/'results/figure03_scene_search_20260921'/args.family/args.scene
    source=WORK/'results/experiments/exp94_normalized_metric_v2_fixed_eval'/args.family/args.scene
    records={a:json.loads((source/n/'psnr/strict_fixed_manifest/final_result.json').read_text()) for a,n in [('ours','normalized_variance_s0'),('baseline','native_vanilla_render_matched_s0')]}
    selected={a:sorted([v for v in d['per_view'] if v['predeclared_fixed_manifest_split']],key=lambda v:v['frame_index']) for a,d in records.items()}
    views=selected['ours'];assert [v['uid'] for v in views]==[v['uid'] for v in selected['baseline']]
    assert all(not v['is_mapping_view'] for vv in selected.values() for v in vv)
    cmd=json.loads((run/'ours/mapping_command.json').read_text());archive=Path(cmd[cmd.index('--archive')+1]);manifest=json.loads((archive/'archive_manifest.json').read_text())
    calib=np.loadtxt(manifest['input_calibration']);trajectory=np.loadtxt(run/'ours/traj_full_beforeBA.txt')
    np.testing.assert_allclose(trajectory,np.loadtxt(run/'baseline/traj_full_beforeBA.txt'),rtol=0,atol=1e-6)
    np.testing.assert_allclose(trajectory,np.loadtxt(source/'normalized_variance_s0/traj_full_beforeBA.txt'),rtol=0,atol=1e-6)
    cameras=[]
    # Existing Fig2 candidates plus a numerical finalist; images do not affect evaluation.
    ranking=json.loads((ROOT.parent/'figure02/analysis/view_ranking.json').read_text())
    top=sorted([v for v in ranking if v['scene']==args.scene],key=lambda v:v['ours_psnr']-v['baseline_psnr'],reverse=True)
    inset_frames=set([v['frame_index'] for v in top[:2]])
    inset_frames.update({'table_01':[330],'table_06':[1420],'square-1':[]}[args.scene])
    heldout={v['frame_index'] for v in views};inset_frames &= heldout
    assets=ROOT/'candidates/scene_search'/args.scene;assets.mkdir(parents=True,exist_ok=True)
    def save(tensor,path):
        array=tensor.permute(1,2,0).cpu().numpy()
        Image.fromarray((array*255).round().clip(0,255).astype('uint8')).save(path)
    for v in views:
        idx=v['frame_index'];rgb,params=preprocess_image(Path(manifest['input_image_directory'])/v['uid'],calib,manifest['preprocessing']['undistort'])
        fx,fy,cx,cy,w,h=params
        proj=getProjectionMatrix2(znear=.01,zfar=100.,fx=fx,fy=fy,cx=cx,cy=cy,W=w,H=h).T.cuda()
        pose=lietorch.SE3(torch.tensor(trajectory[idx,1:],dtype=torch.float32,device='cuda')).inv().matrix().data
        cam=Camera.init_from_tracking(rgb.float()/255,None,None,pose,idx,proj,params);gt=cam.original_image.cuda()
        cameras.append((v,cam,gt,gt>0))
        if idx in inset_frames:
            folder=assets/f'frame_{idx:04d}';folder.mkdir(exist_ok=True);save(gt,folder/'gt.png')
    out=run/'evaluation';out.mkdir(exist_ok=True);rows=[]
    for arm in ['ours','baseline']:
        capture=json.loads((run/arm/'capture_manifest.json').read_text())
        for snap in capture['snapshots']:
            k=snap['iteration'];label=f'{arm}_{k:05d}'+('_final' if snap['final'] else '')
            file=out/f'{label}.json'
            if file.exists():rows.append(json.loads(file.read_text())['summary']);continue
            model=load_gaussians(Path(snap['path']));values=[]
            with torch.no_grad():
                for v,cam,gt,mask in cameras:
                    pred=render(cam,model,torch.ones(3,device='cuda'))['render'].clamp(0,1)
                    values.append({'frame_index':v['frame_index'],'uid':v['uid'],'psnr':float(psnr(pred[mask][None],gt[mask][None]).item())})
                    if v['frame_index'] in inset_frames:save(pred,assets/f"frame_{v['frame_index']:04d}"/f'{label}.png')
            row={'arm':arm,'iteration':k,'mean_psnr':float(np.mean([v['psnr'] for v in values])),'view_count':len(values),'final':snap['final'],'training_renders':snap['training_renders'],'input_prefix':snap['event'].get('emitted_at_frame_uid'),'map':snap['path']}
            file.write_text(json.dumps({'summary':row,'per_view':values},indent=2)+'\n');rows.append(row)
            print(arm,k,round(row['mean_psnr'],4),flush=True);del model
    endpoint={a:{'original':float(np.mean([v['psnr'] for v in selected[a]])),'new':next(r['mean_psnr'] for r in rows if r['arm']==a and r['final'])} for a in selected}
    data={'family':args.family,'scene':args.scene,'heldout_count':len(views),'curves':rows,'endpoint_checks':endpoint,'inset_frames':sorted(inset_frames),'pose_correction_frames':[e['emitted_at_frame_uid'] for e in manifest['events'] if e['kind']=='pose_scale_correction'],'protocol':'Original full fixed held-out set, post-EOS evaluator poses only, native Gaussian Adam steps, matched total training renders. Includes coverage and pose effects. No smoothing.'}
    (out/'curves.json').write_text(json.dumps(data,indent=2)+'\n')
    with (out/'curves.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(endpoint,flush=True)


if __name__=='__main__':main()
