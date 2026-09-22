#!/usr/bin/env python3
"""Render alternative held-out frames at the existing Fig3 checkpoints."""
import json
import subprocess
from pathlib import Path
from evaluate_convergence import torch,np,lietorch,Image,Camera,getProjectionMatrix2,preprocess_image,load_gaussians,render,psnr

ROOT=Path(__file__).resolve().parent.parent
WORK=Path('/home/intern/gs_floaterLab')
RUN=WORK/'results/figure03_scene_search_20260921/rpng/table_06'
FRAMES=[205,355,685,905,950,1110,1630,2370]
STEPS=[800,1400,2600]


def main():
    active=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],text=True).strip();assert not active,active
    command=json.loads((RUN/'ours/mapping_command.json').read_text())
    manifest=json.loads((Path(command[command.index('--archive')+1])/'archive_manifest.json').read_text())
    calib=np.loadtxt(manifest['input_calibration']);trajectory=np.loadtxt(RUN/'ours/traj_full_beforeBA.txt')
    np.testing.assert_allclose(trajectory,np.loadtxt(RUN/'baseline/traj_full_beforeBA.txt'),atol=1e-6,rtol=0)
    ref=json.loads((RUN/'evaluation/ours_00800.json').read_text())
    views=[v for v in ref['per_view'] if v['frame_index'] in FRAMES];assert len(views)==len(FRAMES)
    assets=ROOT/'candidates/table06_revision';assets.mkdir(exist_ok=True)
    def save(t,p):
        a=t.permute(1,2,0).cpu().numpy();Image.fromarray((a*255).round().clip(0,255).astype('uint8')).save(p)
    cameras=[];checks=[]
    for v in views:
        idx=v['frame_index'];rgb,params=preprocess_image(Path(manifest['input_image_directory'])/v['uid'],calib,manifest['preprocessing']['undistort'])
        fx,fy,cx,cy,w,h=params
        proj=getProjectionMatrix2(znear=.01,zfar=100.,fx=fx,fy=fy,cx=cx,cy=cy,W=w,H=h).T.cuda()
        pose=lietorch.SE3(torch.tensor(trajectory[idx,1:],device='cuda',dtype=torch.float32)).inv().matrix().data
        cam=Camera.init_from_tracking(rgb.float()/255,None,None,pose,idx,proj,params);gt=cam.original_image.cuda()
        cameras.append((idx,cam,gt,gt>0));folder=assets/f'frame_{idx:04d}';folder.mkdir(exist_ok=True);save(gt,folder/'gt.png')
    for arm in ['baseline','ours']:
        for k in STEPS:
            record=json.loads((RUN/f'evaluation/{arm}_{k:05d}.json').read_text());model=load_gaussians(Path(record['summary']['map']))
            expected={v['frame_index']:v['psnr'] for v in record['per_view']}
            with torch.no_grad():
                for idx,cam,gt,mask in cameras:
                    pred=render(cam,model,torch.ones(3,device='cuda'))['render'].clamp(0,1)
                    q=float(psnr(pred[mask][None],gt[mask][None]).item());assert abs(q-expected[idx])<.005
                    save(pred,assets/f'frame_{idx:04d}'/f'{arm}_{k:05d}.png')
                    checks.append({'frame':idx,'arm':arm,'iteration':k,'psnr':q,'reference':expected[idx]})
            del model
    (assets/'render_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    print('Verified',len(checks),'renders',flush=True)


if __name__=='__main__':main()
