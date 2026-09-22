#!/usr/bin/env python3
"""Common renderer and common causal poses for controlled refinement branches."""
import csv
import hashlib
import json
import subprocess
from pathlib import Path

from evaluate_convergence import (
    torch, np, Image, Camera, getProjectionMatrix2, preprocess_image,
    load_gaussians, render, psnr, save_png,
)
from exp78b_frozen_archive import FrozenTrackerArchive

WORK=Path('/home/intern/gs_floaterLab')
ROOT=Path(__file__).resolve().parent.parent
RUNS=WORK/'results/figure03_refinement_20260921/aria301_305'
ARCHIVE=WORK/'results/experiments/exp78/b_strict_fair_comparison/frozen_tracker/official_22ffe24_trt/aria/aria301_305/seed0'


def main():
    active=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],text=True).strip()
    assert not active,active
    plan=json.loads((RUNS/'plan.json').read_text())
    archive=FrozenTrackerArchive(ARCHIVE)
    out=RUNS/'evaluation';out.mkdir(exist_ok=True)
    assets=ROOT/'candidates/refinement_insets/frame_1180';assets.mkdir(parents=True,exist_ok=True)
    rows=[];audits=[]
    for event in plan['events']:
        event_id=event['event_id']
        manifests={a:json.loads((RUNS/f'event_{event_id:03d}'/a/'refinement_manifest.json').read_text()) for a in ['ours','baseline']}
        ev=manifests['ours']['evaluation_views']
        other=manifests['baseline']['evaluation_views']
        assert [v['frame_index'] for v in ev]==[v['frame_index'] for v in other]
        pa=np.array([v['pose_w2c'] for v in ev]);pb=np.array([v['pose_w2c'] for v in other])
        np.testing.assert_allclose(pa,pb,rtol=0,atol=1e-5)
        assert all(m['pose_unchanged'] and m['heldout_training_overlap']==0 for m in manifests.values())
        audit={'event_id':event_id,'view_count':len(ev),'max_pose_difference':float(abs(pa-pb).max()),
               'pose_sha256':hashlib.sha256(pa.tobytes()).hexdigest(),
               'evaluation_uids':[v['frame_index'] for v in ev],
               'initial_training_renders':{a:m['initial_training_renders'] for a,m in manifests.items()}}
        audits.append(audit)
        cameras=[]
        for v in ev:
            uid=v['frame_index'];source=archive.arrival_by_uid[uid]['source_name']
            rgb,params=preprocess_image(archive.image_dir/source,archive.calibration,archive.preprocessing['undistort'])
            torch.testing.assert_close(rgb,archive.load_rgb(uid),rtol=0,atol=0,check_dtype=False)
            fx,fy,cx,cy,w,h=params
            projection=getProjectionMatrix2(znear=.01,zfar=100.,fx=fx,fy=fy,cx=cx,cy=cy,W=w,H=h).T.cuda()
            camera=Camera.init_from_tracking(rgb.float()/255,None,None,torch.tensor(v['pose_w2c'],dtype=torch.float32,device='cuda'),uid,projection,params)
            gt=camera.original_image.cuda()
            cameras.append((uid,camera,gt,gt>0))
            if uid==1180 and event_id==68:
                save_png(gt,assets/'gt.png')
        for arm,m in manifests.items():
            for snap in m['snapshots']:
                k=snap['additional_iteration']
                dest=out/f'event_{event_id:03d}_{arm}_{k:03d}.json'
                if dest.exists():
                    rows.append(json.loads(dest.read_text())['summary']);continue
                assert snap['additional_renders']==k
                model=load_gaussians(Path(snap['path']))
                values=[]
                with torch.no_grad():
                    for uid,cam,gt,mask in cameras:
                        pred=render(cam,model,torch.ones(3,device='cuda'))['render'].clamp(0,1)
                        q=float(psnr(pred[mask][None],gt[mask][None]).item())
                        values.append({'frame_index':uid,'psnr':q})
                        if uid==1180 and event_id==68 and k in plan['inset_iterations']:
                            save_png(pred,assets/f'{arm}_additional_{k:03d}.png')
                row={'event_id':event_id,'arm':arm,'additional_iteration':k,
                     'mean_psnr':float(np.mean([v['psnr'] for v in values])),
                     'view_count':len(values),'additional_training_renders':k,'map':snap['path']}
                dest.write_text(json.dumps({'summary':row,'per_view':values},indent=2)+'\n')
                rows.append(row)
                print('EVAL',event_id,arm,k,round(row['mean_psnr'],4),flush=True)
                del model
        del cameras
    aggregate=[]
    for arm in ['baseline','ours']:
        for k in plan['additional_iterations']:
            values=[r['mean_psnr'] for r in rows if r['arm']==arm and r['additional_iteration']==k]
            assert len(values)==len(plan['events'])
            aggregate.append({'arm':arm,'additional_iteration':k,'mean_psnr':float(np.mean(values)),
                              'event_count':len(values),'event_psnr':values})
    result={'plan':plan,'audits':audits,'per_event_curves':rows,'mean_curves':aggregate,
            'aggregation':'Arithmetic mean within each fixed held-out event cohort, then equal mean over the same five events at every iteration.',
            'evaluation_pose':'Shared current causal KF interpolation, held fixed within each branch; no post-EOS poses.',
            'limitations':'Single seed, diagnostic continuation. Own online initial maps. Baseline normalized to one view/step, native topology/loss/sampling retained. No claim of native end-to-end speedup.'}
    (out/'curves.json').write_text(json.dumps(result,indent=2)+'\n')
    for name,data in [('per_event_curves.csv',rows),('mean_curves.csv',aggregate)]:
        with (out/name).open('w') as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
    print('MEANS',aggregate,flush=True)


if __name__=='__main__':
    main()
