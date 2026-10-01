#!/usr/bin/env python3
"""Locate GT feature patches' first supported training observation, on CPU.

Selection uses raw RGB and post-run evaluation poses only, never either map's
quality/depth. SIFT, homography, positive-depth triangulation, parallax and
reprojection checks establish a matched physical patch. This is first supported
feature observation, not proof of absence of every earlier physical sighting.
"""
import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import traceback

import cv2
import numpy as np
from scipy.spatial.transform import Rotation
import torch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from collect_cvpr_assets import ROOT,OUT,RESULTS,read,write,sha


def preprocessing():
    source=ROOT/'benchmarks/online_gs/exp78_evaluate_vigs_ply.py'
    tree=ast.parse(source.read_text())
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='preprocess_image')
    scope={'np':np,'cv2':cv2,'torch':torch,'Path':Path,'TARGET_PIXELS':341*640}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),scope)
    return scope['preprocess_image'],source


def crop_proposals(image):
    gray=cv2.cvtColor(image,cv2.COLOR_RGB2GRAY).astype(float)/255
    gray=cv2.GaussianBlur(gray,(5,5),1)
    gy,gx=np.gradient(gray);energy=np.hypot(gx,gy)
    h,w=gray.shape;cw,ch=w//3,h//3
    scores=[]
    for y in np.linspace(0,h-ch,9,dtype=int):
        for x in np.linspace(0,w-cw,9,dtype=int):
            patch=gray[y:y+ch,x:x+cw]
            score=float(energy[y:y+ch,x:x+cw].mean()*((patch>.04)&(patch<.96)).mean())
            scores.append((score,[int(x),int(y),int(x+cw),int(y+ch)]))
    chosen=[]
    for score,box in sorted(scores,reverse=True):
        def overlap(other):
            x=max(0,min(box[2],other[2])-max(box[0],other[0]))
            y=max(0,min(box[3],other[3])-max(box[1],other[1]))
            return x*y/(cw*ch)
        if all(overlap(b)<.35 for _,b in chosen):chosen.append((score,box))
        if len(chosen)==3:break
    return chosen


def supported_match(query,points,descriptors,k,source_w2c):
    if len(points)<12 or len(query['descriptors'])<12:return None
    matches=cv2.BFMatcher(cv2.NORM_L2).knnMatch(query['descriptors'].astype(np.float32),descriptors.astype(np.float32),k=2)
    good=[a for pair in matches if len(pair)==2 for a,b in [pair] if a.distance < .7*b.distance]
    good=sorted(good,key=lambda m:m.distance)
    unique={}
    for m in good:unique.setdefault(m.trainIdx,m)
    good=list(unique.values())
    if len(good)<12:return None
    a=np.asarray([query['points'][m.queryIdx] for m in good],dtype=np.float64)
    b=np.asarray([points[m.trainIdx] for m in good],dtype=np.float64)
    _,inliers=cv2.findHomography(a,b,cv2.RANSAC,3.0)
    if inliers is None or inliers.sum()<10:return None
    a,b=a[inliers.ravel().astype(bool)],b[inliers.ravel().astype(bool)]
    source_camera=np.linalg.inv(source_w2c);target_camera=np.linalg.inv(query['w2c'])
    if np.linalg.norm(source_camera[:3,3]-target_camera[:3,3])<.02:return None
    world=cv2.triangulatePoints(k@query['w2c'][:3],k@source_w2c[:3],a.T,b.T)
    world=world[:3]/world[3:]
    x=np.vstack([world,np.ones(world.shape[1])])
    target_local=query['w2c'][:3]@x;source_local=source_w2c[:3]@x
    target_pixel=k@target_local;target_pixel=(target_pixel[:2]/target_pixel[2:]).T
    source_pixel=k@source_local;source_pixel=(source_pixel[:2]/source_pixel[2:]).T
    error=np.maximum(np.linalg.norm(target_pixel-a,axis=1),np.linalg.norm(source_pixel-b,axis=1))
    v1=world.T-source_camera[:3,3];v2=world.T-target_camera[:3,3]
    cosine=(v1*v2).sum(1)/np.maximum(np.linalg.norm(v1,axis=1)*np.linalg.norm(v2,axis=1),1e-12)
    angle=np.degrees(np.arccos(np.clip(cosine,-1,1)))
    valid=(error<2)&(angle>.3)&(target_local[2]>.05)&(source_local[2]>.05)&np.isfinite(world).all(0)
    if valid.sum()<8:return None
    return {'feature_inliers':int(valid.sum()),'reprojection_p95_px':float(np.percentile(error[valid],95)),
            'parallax_median_degrees':float(np.median(angle[valid])),
            'triangulated_points_world':world[:,valid].T.tolist()}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--scenes',nargs='+')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    cv2.setNumThreads(1);torch.set_num_threads(1)
    preprocess,source=preprocessing()
    inventory=[r for r in read(OUT/'scene_inventory.json') if not a.scenes or r['scene'] in a.scenes]
    declaration={'candidate_scenes':[r['scene'] for r in inventory], 'query_rule':'three uniform saved held-out positions 2/7,4/7,6/7; three nonoverlapping GT-structure crops each',
        'matcher':'SIFT700, ratio0.7, homography3px/min10, triangulation reprojection2px/min8, parallax0.3deg, camera baseline0.02',
        'first_observation':'first supported match over all preceding non-heldout RGB inputs',
        'new_region_filter':'first supported frame >=15% of sequence; at least two usable later map checkpoints required for a curve',
        'script_sha256':sha(Path(__file__)),'image_preprocessor':str(source),'image_preprocessor_sha256':sha(source),
        'quality_scores_used_for_selection':False,'evaluation_poses_used_by_mapper':False,'cuda_used':False}
    write(a.output/'protocol.json',declaration)
    summary=[]
    for item in inventory:
        d,s=item['dataset'],item['scene'];out=a.output/d/s;out.mkdir(parents=True)
        row={'dataset':d,'scene':s,'status':'failed','output':str(out)}
        try:
            panel=RESULTS/('cvpr_assets/fixed_work_12f_v1' if s=='aria301_12F' else 'cvpr_assets/fixed_work_v1')
            run=panel/'render40'/d/s/'d3'
            reference=np.atleast_2d(np.loadtxt(run/'traj_full_beforeBA.txt'))
            camera=np.repeat(np.eye(4)[None],len(reference),axis=0)
            camera[:,:3,:3]=Rotation.from_quat(reference[:,4:8]).as_matrix();camera[:,:3,3]=reference[:,1:4]
            w2c=np.linalg.inv(camera)
            names=sorted(Path(item['image_dir']).iterdir(),key=lambda x:float(x.stem))
            assert len(names)==len(reference)
            calibration=np.loadtxt(item['calibration'])
            full=read(Path(item['fixed_manifest']));heldout={v['frame_index'] for v in full['views']}
            subset=[full['views'][int(i)]['frame_index'] for i in np.linspace(0,len(full['views'])-1,min(64,len(full['views'])),dtype=int)]
            saved=[subset[int(i)] for i in np.linspace(0,len(subset)-1,min(8,len(subset)),dtype=int)]
            targets=[saved[min(j,len(saved)-1)] for j in [2,4,6]]
            def extract(index):
                image,params=preprocess(names[index],calibration,d!='aria')
                rgb=image.permute(1,2,0).numpy()
                sift=cv2.SIFT_create(nfeatures=700)
                keys,desc=sift.detectAndCompute(cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY),None)
                points=np.array([key.pt for key in keys],dtype=np.float32).reshape(-1,2)
                if desc is None:desc=np.empty((0,128),dtype=np.float32)
                return rgb,params,points,desc
            queries=[]
            for target in targets:
                rgb,params,points,desc=extract(target)
                fx,fy,cx,cy=params[:4];k=np.array([[fx,0,cx],[0,fy,cy],[0,0,1]])
                for rank,(score,box) in enumerate(crop_proposals(rgb)):
                    inside=(points[:,0]>=box[0])&(points[:,0]<box[2])&(points[:,1]>=box[1])&(points[:,1]<box[3])
                    if inside.sum()<12:continue
                    queries.append({'target_frame':int(target),'crop':box,'gt_structure_score':score,'crop_rank':rank,
                        'points':points[inside],'descriptors':desc[inside],'w2c':w2c[target],'match':None})
            for index in range(max(targets)+1):
                if index in heldout:continue
                pending=[q for q in queries if q['match'] is None and index<q['target_frame']]
                if not pending:continue
                _,_,points,desc=extract(index)
                for q in pending:
                    match=supported_match(q,points,desc,k,w2c[index])
                    if match:
                        q['match']={**match,'first_observed_frame':index,'first_observed_sensor_time':float(reference[index,0]),
                            'target_sensor_time':float(reference[q['target_frame'],0]),
                            'qualifies_as_new_region':index>=int(.15*len(reference))}
            regions=[{k:v for k,v in q.items() if k not in {'points','descriptors','w2c'}} for q in queries]
            write(out/'regions.json',{'regions':regions,'selection_uses_prediction':False,
                'trajectory':str(run/'traj_full_beforeBA.txt'),'trajectory_sha256':sha(run/'traj_full_beforeBA.txt'),
                'fixed_manifest':item['fixed_manifest'],'fixed_manifest_sha256':sha(Path(item['fixed_manifest'])),
                'input_rgb_count':len(names),'evaluated_source_run':str(run)})
            row.update(status='measured',candidate_regions=len(regions),supported_regions=sum(r['match'] is not None for r in regions),
                new_regions=sum(r['match'] is not None and r['match']['qualifies_as_new_region'] for r in regions))
        except Exception:row['error']=traceback.format_exc()
        summary.append(row);write(a.output/'summary.json',summary)
        print('FEATURE_REGION',d,s,row['status'],row.get('new_regions'),flush=True)
    from run_cvpr_measurements import journal
    journal({'dataset':'cvpr','scene':'first_supported_region_observations','budget':'CPU_annotation',
        'arm':'shared_RGB_reference','status':'measured' if all(r['status']=='measured' for r in summary) else 'failed','output':str(a.output/'summary.json')})


if __name__=='__main__':main()
