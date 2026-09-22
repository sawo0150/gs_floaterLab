#!/usr/bin/env python3
"""Evaluate every saved checkpoint on the same 539 held-out views, PSNR only."""
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch
import lietorch
from PIL import Image

WORK = Path('/home/intern/gs_floaterLab')
ROOT = Path(__file__).resolve().parent.parent
RUNS = WORK / 'results/figure03_convergence_20260921/aria301_305'
SOURCE = WORK / 'results/experiments/exp94_normalized_metric_v2_fixed_eval/aria/aria301_305'
sys.path.insert(0, '/home/intern/VIGS-SLAM-paper-full/vigs')
sys.path.insert(0, str(WORK/'benchmarks/online_gs'))
from exp78_evaluate_vigs_ply import load_gaussians, preprocess_image
from gaussian.renderer import render
from gaussian.utils.camera_utils import Camera
from gaussian.utils.graphics_utils import getProjectionMatrix2
from gaussian.utils.loss_utils import psnr


def main():
    active = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],text=True).strip()
    assert not active, f'GPU occupied: {active}'
    source_metrics = {arm: json.loads((SOURCE/name/'psnr/strict_fixed_manifest/final_result.json').read_text())
                      for arm,name in [('ours','normalized_variance_s0'),('baseline','native_vanilla_render_matched_s0')]}
    selected = {arm: [r for r in m['per_view'] if r['predeclared_fixed_manifest_split']] for arm,m in source_metrics.items()}
    views = sorted(selected['ours'], key=lambda r:r['frame_index'])
    assert len(views) == 539
    assert {r['uid'] for r in views} == {r['uid'] for r in selected['baseline']}
    assert all(not r['is_mapping_view'] for arm in selected.values() for r in arm)
    command = json.loads((RUNS/'ours/mapping_command.json').read_text())
    archive = Path(command[command.index('--archive')+1])
    manifest = json.loads((archive/'archive_manifest.json').read_text())
    calib = np.loadtxt(manifest['input_calibration'])
    trajectory = np.loadtxt(RUNS/'ours/traj_full_beforeBA.txt')
    np.testing.assert_allclose(trajectory,np.loadtxt(RUNS/'baseline/traj_full_beforeBA.txt'),atol=1e-6,rtol=0)
    np.testing.assert_allclose(trajectory,np.loadtxt(SOURCE/'normalized_variance_s0/traj_full_beforeBA.txt'),atol=1e-6,rtol=0)
    images = Path(manifest['input_image_directory'])
    cameras = []
    inset_indices = {980,1180,1220}
    inset_steps = {600,1000,1300}
    assets = ROOT/'candidates/convergence_insets'
    for view in views:
        idx = view['frame_index']
        rgb, params = preprocess_image(images/view['uid'],calib,manifest['preprocessing']['undistort'])
        fx,fy,cx,cy,w,h = params
        projection = getProjectionMatrix2(znear=.01,zfar=100.,fx=fx,fy=fy,cx=cx,cy=cy,W=w,H=h).T.cuda()
        pose = lietorch.SE3(torch.tensor(trajectory[idx,1:],dtype=torch.float32,device='cuda')).inv().matrix().data
        camera = Camera.init_from_tracking(rgb.float()/255,None,None,pose,idx,projection,params)
        gt = camera.original_image.cuda()
        cameras.append((view,camera,gt,gt>0))
        if idx in inset_indices:
            folder = assets/f'frame_{idx:04d}'
            folder.mkdir(parents=True,exist_ok=True)
            save_png(gt,folder/'gt.png')
    eval_dir = RUNS/'evaluation'
    eval_dir.mkdir(exist_ok=True)
    summary = []
    for arm in ('ours','baseline'):
        capture = json.loads((RUNS/arm/'capture_manifest.json').read_text())
        runtime = json.loads((RUNS/arm/'mapping_replay_runtime.json').read_text())
        assert runtime['heldout_mapping_overlap_count'] == 0
        for checkpoint in capture['snapshots']:
            step = checkpoint['iteration']
            label = f'{arm}_{step:05d}{"_final" if checkpoint["final"] else ""}'
            out = eval_dir/f'{label}.json'
            if out.exists():
                record = json.loads(out.read_text())
                summary.append(record['summary'])
                if step in inset_steps:
                    model = None
                    with torch.no_grad():
                        for view,camera,gt,mask in cameras:
                            if view['frame_index'] not in inset_indices:
                                continue
                            path = assets/f"frame_{view['frame_index']:04d}"/f'{arm}_iter_{step:05d}.png'
                            if path.exists():
                                continue
                            if model is None:
                                model=load_gaussians(Path(checkpoint['path']))
                            prediction=render(camera,model,torch.ones(3,device='cuda'))['render'].clamp(0,1)
                            value=float(psnr(prediction[mask][None],gt[mask][None]).item())
                            expected=next(v['psnr'] for v in record['per_view'] if v['frame_index']==view['frame_index'])
                            assert abs(value-expected)<.005
                            save_png(prediction,path)
                    del model
                continue
            model = load_gaussians(Path(checkpoint['path']))
            values = []
            with torch.no_grad():
                for view,camera,gt,mask in cameras:
                    prediction = render(camera,model,torch.ones(3,device='cuda'))['render'].clamp(0,1)
                    value = float(psnr(prediction[mask][None],gt[mask][None]).item())
                    values.append({'frame_index':view['frame_index'],'uid':view['uid'],'psnr':value})
                    if step in inset_steps and view['frame_index'] in inset_indices:
                        path = assets/f"frame_{view['frame_index']:04d}"/f'{arm}_iter_{step:05d}.png'
                        save_png(prediction,path)
            row = {'arm':arm,'iteration':step,'mean_psnr':float(np.mean([v['psnr'] for v in values])),
                   'view_count':len(values),'gaussians':checkpoint['gaussians'],'final':checkpoint['final'],
                   'training_renders':checkpoint['training_renders'],
                   'input_prefix':checkpoint['event'].get('emitted_at_frame_uid'),
                   'map':checkpoint['path']}
            out.write_text(json.dumps({'summary':row,'per_view':values},indent=2)+'\n')
            summary.append(row)
            print(arm,step,f"{row['mean_psnr']:.4f}",flush=True)
            del model
    result = {'scene':'aria301_305','heldout_count':539,'inset_frames':sorted(inset_indices),
              'inset_iterations':sorted(inset_steps),'evaluation_only_fixed_post_eos_poses':True,
              'evaluation_views_sha256':hashlib.sha256(json.dumps([v['uid'] for v in views]).encode()).hexdigest(),
              'curves':summary,'protocol':'PSNR mean per image; original GT>0 mask; fixed manifest; same poses and preprocessing'}
    (eval_dir/'curves.json').write_text(json.dumps(result,indent=2)+'\n')
    with (eval_dir/'curves.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    endpoint_checks={}
    for arm in ('ours','baseline'):
        final=next(r for r in summary if r['arm']==arm and r['final'])
        old=float(np.mean([v['psnr'] for v in selected[arm]]))
        endpoint_checks[arm]={'old_psnr':old,'new_psnr':final['mean_psnr'],'delta':final['mean_psnr']-old}
    (eval_dir/'endpoint_checks.json').write_text(json.dumps(endpoint_checks,indent=2)+'\n')
    print('ENDPOINTS',endpoint_checks,flush=True)


def save_png(tensor,path):
    array=np.rot90(tensor.permute(1,2,0).detach().cpu().numpy(),k=-1).copy()
    Image.fromarray((array*255).round().clip(0,255).astype('uint8')).save(path)


if __name__=='__main__':
    main()
