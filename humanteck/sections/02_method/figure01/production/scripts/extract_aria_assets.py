#!/usr/bin/env python3
"""Read-only visualization of the user-approved exp94 map. No optimizer.

Run with the VIGS environment through the existing mapping_environment helper.
Outputs are confined to production/assets and production/candidates.
"""
import sys
import argparse
import copy
from pathlib import Path
import hashlib
import json
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont
import cv2
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parent.parent
WORK = Path('/home/intern/gs_floaterLab')
RUN = WORK/'results/experiments/exp94_normalized_metric_v2_fixed_eval/aria/aria1253/normalized_variance_s0'
ARCHIVE = WORK/'results/experiments/exp78/b_strict_fair_comparison/frozen_tracker/official_22ffe24_trt/aria/aria1253/seed0'
OUT = ROOT/'assets/aria1253'
sys.path.insert(0,str(WORK/'benchmarks/online_gs'))
from exp78_evaluate_vigs_ply import load_gaussians, preprocess_image
from gaussian.renderer import render
from gaussian.utils.camera_utils import Camera
from gaussian.utils.graphics_utils import getProjectionMatrix2
from gaussian.utils.slam_utils import depth_to_normal


def font(size,bold=False):
    import subprocess
    path=subprocess.check_output(['fc-match','-f','%{file}','Arial:style=Bold' if bold else 'Arial'],text=True)
    return ImageFont.truetype(path,size)


def keyframe_records():
    archive=json.loads((ARCHIVE/'archive_manifest.json').read_text())
    arrivals=[json.loads(s) for s in (ARCHIVE/'arrivals.jsonl').read_text().splitlines()]
    times=np.array([a['sensor_timestamp'] for a in arrivals])
    rows=np.atleast_2d(np.loadtxt(RUN/'traj_kf_beforeBA.txt'))
    records={}
    for row in rows:
        idx=int(np.argmin(abs(times-row[0])))
        assert abs(times[idx]-row[0])<1e-5
        pose=np.eye(4);pose[:3,:3]=Rotation.from_quat(row[4:8]).as_matrix();pose[:3,3]=row[1:4]
        records[arrivals[idx]['frame_uid']]={'arrival':arrivals[idx],'pose':pose,'row':row}
    return archive,records


def candidate_views():
    """Same saved map and true prefinal KEYFRAME poses, 12 temporal candidates."""
    archive,records=keyframe_records()
    candidates=ROOT/'candidates';candidates.mkdir(exist_ok=True)
    raw=candidates/'frames';raw.mkdir(exist_ok=True)
    images=Path(archive['input_image_directory']);calib=np.loadtxt(archive['input_calibration'])
    mapped=set(json.loads((RUN/'mapped_uids.json').read_text()))
    uids=[201,284,389,487,589,687,786,893,998,1091,1193,1272]
    model=load_gaussians(RUN/'3dgs_before_final.ply')
    background=torch.ones(3,device='cuda')
    report=[]
    def save(p,v):
        if v.dtype!=np.uint8:v=np.round(np.clip(np.nan_to_num(v),0,1)*255).astype(np.uint8)
        Image.fromarray(v).save(p)
    for i,uid in enumerate(uids):
        record=records[uid];a=record['arrival'];assert uid in mapped and not a['held_out']
        folder=raw/f'C{i+1:02d}_uid{uid:04d}';folder.mkdir(exist_ok=True)
        rgb,params=preprocess_image(images/a['source_name'],calib,False)
        def make_camera(pose,cp):
            fx,fy,cx,cy,w,h=cp
            projection=getProjectionMatrix2(znear=.01,zfar=100.,fx=fx,fy=fy,cx=cx,cy=cy,W=w,H=h).T.cuda()
            return Camera.init_from_tracking(rgb.float()/255,None,None,torch.tensor(pose,dtype=torch.float32,device='cuda'),uid,projection,cp)
        ext=np.linalg.inv(record['pose']);cam=make_camera(ext,params)
        with torch.no_grad():
            rr=render(cam,model,background)
            normals,_=depth_to_normal(cam,rr['depth'],world_frame=False)
        arrays={'input':rgb.permute(1,2,0).numpy(),
                'rgb':rr['render'].clamp(0,1).permute(1,2,0).cpu().numpy(),
                'depth':depth_rgb(rr['depth'].squeeze().cpu().numpy()),
                'normal':normal_rgb(normals.cpu().numpy())}
        for name,array in arrays.items():save(folder/f'{name}.png',np.rot90(array,-1))
        # Latest causal priors available for each candidate, for later paired replacement.
        event=[e for e in archive['events'] if uid in e.get('frame_uids',[])][-1]
        ref=event['geometry_refs'][event['frame_uids'].index(uid)]
        for kind in ['depth','normal']:
            t=torch.load(ARCHIVE/ref[kind],map_location='cpu',weights_only=False)['tensor'].numpy()
            array=depth_rgb(t) if kind=='depth' else normal_rgb(t.transpose(1,2,0))
            save(folder/f'prior_{kind}.png',np.rot90(array,-1))
        upright=np.eye(4);upright[:3,:3]=[[0,-1,0],[1,0,0],[0,0,1]]
        wc=make_camera(upright@ext,[450.,450.,500.,300.,1000,600])
        with torch.no_grad():wr=render(wc,model,background)
        save(folder/'wide_map.png',wr['render'].clamp(0,1).permute(1,2,0).cpu().numpy())
        report.append({'candidate':f'C{i+1:02d}','frame_uid':uid,'source_name':a['source_name'],
            'timestamp':a['sensor_timestamp'],'keyframe':True,'held_out':False,'mapped':True,
            'prior_event_id':event['event_id'],'prior_emitted_at_uid':event['emitted_at_frame_uid'],
            'prior_refs':ref,'folder':str(folder.relative_to(ROOT)),
            'camera_to_world':record['pose'].tolist(),
            'files':{p.name:sha(p) for p in sorted(folder.glob('*.png'))}})
        print('rendered',i+1,uid,flush=True)
    meta={'run':str(RUN),'map_sha256':sha(RUN/'3dgs_before_final.ply'),
        'pose_source':str(RUN/'traj_kf_beforeBA.txt'),'pose_source_sha256':sha(RUN/'traj_kf_beforeBA.txt'),
        'policy':'12 fixed approximately time-spaced mapped keyframes including previous UID284; no PSNR ranking',
        'depth_range_m':[.5,7.],'rotation':'90 degrees clockwise, no RGB correction or normal smoothing',
        'note':'Same prefinal map for every candidate. Training-view illustrations, not held-out comparisons. Ray loss disabled.',
        'selected_candidate':None,'candidates':report}
    (candidates/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    candidate_boards(meta)


def candidate_boards(meta):
    candidates=ROOT/'candidates'
    # User-facing summary: one wide map render per candidate.
    board=Image.new('RGB',(1800,1580),'#f4f6fb');d=ImageDraw.Draw(board)
    d.text((24,16),'Aria 1253 | Choose an overview view',font=font(34,True),fill='#12164c')
    d.text((24,62),'C02 = previous view. Same map and display settings; no geometry cleanup or RGB enhancement.',font=font(20),fill='#505c70')
    for i,r in enumerate(meta['candidates']):
        x=20+(i%3)*593;y=105+(i//3)*363
        d.rounded_rectangle((x,y,x+575,y+346),12,fill='white',outline='#d0d8e4',width=2)
        d.text((x+13,y+10),f"{r['candidate']}   UID {r['frame_uid']}",font=font(26,True),fill='#12164c')
        im=Image.open(ROOT/r['folder']/'wide_map.png');im.thumbnail((549,295))
        board.paste(im,(x+13,y+47))
    board.save(candidates/'01_view_candidates.png')
    # A single sheet holds all matching modalities with stable candidate IDs.
    board=Image.new('RGB',(1800,1980),'#f4f6fb');d=ImageDraw.Draw(board)
    d.text((24,16),'Matching modalities | all 12 candidates',font=font(33,True),fill='#12164c')
    d.text((24,61),'Input RGB / Rendered RGB / Rendered depth / Depth-derived normal. Depth: 0.5–7.0 m for all views.',font=font(20),fill='#505c70')
    for i,r in enumerate(meta['candidates']):
        x=20+(i%2)*890;y=104+(i//2)*308
        d.rounded_rectangle((x,y,x+865,y+294),12,fill='white',outline='#d0d8e4',width=2)
        d.text((x+13,y+8),f"{r['candidate']}  |  UID {r['frame_uid']}"+('  (previous)' if r['frame_uid']==284 else ''),font=font(24,True),fill='#12164c')
        for j,(name,label) in enumerate([('input','Input RGB'),('rgb','Rendered RGB'),('depth','Rendered depth'),('normal','Depth-derived normal')]):
            xx=x+13+j*211
            d.text((xx,y+43),label,font=font(18),fill='#505c70')
            im=Image.open(ROOT/r['folder']/f'{name}.png').resize((200,200),Image.Resampling.LANCZOS)
            board.paste(im,(xx,y+73))
    board.save(candidates/'02_modalities_all.png')


def trajectory_views():
    """True pose frusta, not generic camera icons on a hand-drawn curve."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection, PolyCollection
    from plyfile import PlyData
    archive,records=keyframe_records()
    vals=list(records.values());centers=np.stack([r['pose'][:3,3] for r in vals])
    origin=centers.mean(0);_,_,basis=np.linalg.svd(centers-origin,full_matrices=False)
    # Common orthographic pose-plane projection for BOTH map points and cameras.
    U,V,N=basis
    if np.linalg.det(basis)<0:N=-N
    points=PlyData.read(RUN/'3dgs_before_final.ply')['vertex']
    xyz=np.stack([points[a] for a in ['x','y','z']],1)
    dc=np.stack([points[f'f_dc_{i}'] for i in range(3)],1)
    rgb=np.clip(.5+.28209479177387814*dc,0,1)
    intr=np.load(RUN/'intrinsics.npy');fx,fy,cx,cy=intr;w,h=archive['preprocessing']['output_image_size_hw'][::-1]
    selected=np.unique(np.rint(np.linspace(0,len(vals)-1,11)).astype(int))
    out=ROOT/'assets/trajectory';out.mkdir(parents=True,exist_ok=True)
    edges=[(0,i) for i in range(1,5)]+[(1,2),(2,3),(3,4),(4,1)]
    frusta=[];frustum_depth=.45
    for i in selected:
        c=vals[i]['pose'];z=frustum_depth
        corners=np.array([[0,0,0],[-cx/fx*z,-cy/fy*z,z],[(w-cx)/fx*z,-cy/fy*z,z],[(w-cx)/fx*z,(h-cy)/fy*z,z],[-cx/fx*z,(h-cy)/fy*z,z]])
        frusta.append((int(i),corners@c[:3,:3].T+c[:3,3]))
    for name,axes in [('pose_plane',np.stack([U,V])),('oblique',np.stack([U,.65*V+np.sqrt(1-.65**2)*N]))]:
        xy=(centers-origin)@axes.T;cloud=(xyz-origin)@axes.T
        fig,ax=plt.subplots(figsize=(10,5),dpi=180)
        ax.set_facecolor('#f0faff');fig.patch.set_facecolor('#f0faff')
        ax.scatter(cloud[:,0],cloud[:,1],s=.85,c=rgb,alpha=.34,rasterized=True,linewidths=0)
        ax.plot(xy[:,0],xy[:,1],color='#116dc3',lw=2.4,zorder=3)
        ax.scatter(xy[:,0],xy[:,1],s=7,color='#116dc3',zorder=4)
        for i,frustum in frusta:
            f=(frustum-origin)@axes.T
            color='#02a69b' if i==selected[-1] else '#122659'
            ax.add_collection(PolyCollection([f[[1,2,3,4]]],facecolors=color,alpha=.08,zorder=5))
            ax.add_collection(LineCollection([(f[a],f[b]) for a,b in edges],colors=color,linewidths=1.1,zorder=6))
        ax.scatter(*xy[0],color='#f04b36',s=32,zorder=7)
        ax.scatter(*xy[-1],color='#02a69b',s=32,zorder=7)
        # Common display viewport: trajectory plus frustum margins, never map pruning.
        low=xy.min(0)-1.0;high=xy.max(0)+1.0
        ax.set_xlim(low[0],high[0]);ax.set_ylim(low[1],high[1]);ax.set_aspect('equal');ax.axis('off')
        fig.subplots_adjust(0,0,1,1)
        fig.savefig(out/f'{name}.png',dpi=180,bbox_inches='tight',pad_inches=.04)
        fig.savefig(out/f'{name}.svg',bbox_inches='tight',pad_inches=.04);plt.close(fig)
    metadata={'pose_source':str(RUN/'traj_kf_beforeBA.txt'),'pose_source_sha256':sha(RUN/'traj_kf_beforeBA.txt'),
        'map_source':str(RUN/'3dgs_before_final.ply'),'map_sha256':sha(RUN/'3dgs_before_final.ply'),
        'pose_convention':'camera-to-world, TUM xyz qx qy qz qw','keyframes':len(vals),
        'projection':'PCA pose plane / oblique orthographic. Same transform for points, trajectory and frusta. Not a gravity-aligned floor plan.',
        'camera_frustum_depth_m':frustum_depth,'frustum_size':'display glyph only; positions and orientations are measured',
        'frustum_uids':[list(records)[int(i)] for i in selected],'origin':origin.tolist(),'pca_basis':basis.tolist(),
        'background':'actual Gaussian centers with DC colors; not mesh or occupancy; plot viewport cropping only',
        'background_scatter_alpha':.34,'background_scatter_size_pt2':.85,
        'temporal_state':'prefinal endpoint keyframe estimates, not post-EOS dense filled trajectory; not a time-resolved causal replay',
        'files':{p.name:sha(p) for p in sorted(out.glob('*.png'))}}
    (out/'provenance.json').write_text(json.dumps(metadata,indent=2)+'\n')
    board=Image.new('RGB',(1840,1080),'white');d=ImageDraw.Draw(board)
    d.text((25,15),'Actual estimated poses + camera frusta',font=font(32,True),fill='#12164c')
    d.text((25,59),'115 saved keyframes; 11 camera glyphs. Red dot: start. Teal dot: end. Same run as the Gaussian map.',font=font(21),fill='#506075')
    for j,(name,title) in enumerate([('pose_plane','A | Pose-plane projection'),('oblique','B | Oblique projection')]):
        y=105+j*480;d.text((25,y),title,font=font(25,True),fill='#12164c')
        im=Image.open(out/f'{name}.png');im.thumbnail((1760,415));board.paste(im,((1840-im.width)//2,y+38))
    (ROOT/'candidates').mkdir(exist_ok=True);board.save(ROOT/'candidates/03_trajectory_options.png')
    # Relocate old paths without re-rendering or touching source experiment data.
    p=ROOT/'assets/aria1253/provenance.json';prov=json.loads(p.read_text())
    for rec in prov['assets'].values():rec['path']=rec['path'].replace('assets_v02/','assets/aria1253/')
    prov['assets']['trajectory']={'path':'assets/trajectory/pose_plane.png','sha256':sha(out/'pose_plane.png'),'modality':'actual_keyframe_pose_projection'}
    prov['schematics']='growth stages, counts/probabilities and ray diagram; pose trajectory now derives from saved keyframe estimates'
    p.write_text(json.dumps(prov,indent=2)+'\n')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save_image(name, value, rotate=True):
    value=np.nan_to_num(value)
    if value.dtype != np.uint8:
        value=(np.clip(value,0,1)*255).round().astype(np.uint8)
    if rotate:
        value=np.rot90(value,k=-1)
    p=OUT/(name+'.png')
    Image.fromarray(value).save(p)
    return {'path':str(p.relative_to(ROOT)), 'sha256':sha(p),
            'display_rotation_clockwise_degrees':90 if rotate else 0,
            'crop':None, 'brightness_adjustment':None}


def depth_rgb(d):
    v=np.clip((d-0.5)/(7.0-0.5),0,1)
    rgb=cv2.applyColorMap((v*255).astype(np.uint8),cv2.COLORMAP_TURBO)[:,:,::-1]
    rgb[(~np.isfinite(d))|(d<=0)]=[240,242,245]
    return rgb


def normal_rgb(n):
    n=n/np.maximum(np.linalg.norm(n,axis=-1,keepdims=True),1e-8)
    return (n+1)/2


def apply_selection():
    """Apply the user's separate choices: map reference C07, modalities C10, pose A."""
    archive,records=keyframe_records()
    p=OUT/'provenance.json';prov=json.loads(p.read_text())
    cm=ROOT/'candidates/manifest.json';meta=json.loads(cm.read_text())
    source=next(c for c in meta['candidates'] if c['candidate']=='C10')
    map_source=next(c for c in meta['candidates'] if c['candidate']=='C07')
    folder=ROOT/source['folder']
    for key,name in [('render_rgb','rgb'),('render_depth','depth'),('render_normal','normal'),('prior_depth','prior_depth'),('prior_normal','prior_normal')]:
        src=folder/(name+'.png')
        prov['assets'][key]={'path':str(src.relative_to(ROOT)),'sha256':sha(src),
            'frame_uid':1091,'candidate':'C10','modality':key,
            'depth_range_m':[.5,7.] if 'depth' in key else None,
            'display_rotation_clockwise_degrees':90,
            'candidate_manifest':'candidates/manifest.json','brightness_adjustment':None,
            'map_clip_applied':False,
            'normal_convention':'unit camera-space xyz to RGB; pixels rotated only' if 'normal' in key else None}
    src=ROOT/map_source['folder']/'wide_map.png'
    prov['assets']['map_interior']={'path':str(src.relative_to(ROOT)),'sha256':sha(src),
        'frame_uid':786,'candidate':'C07','modality':'uncut_map_reference_view','map_clip_applied':False}
    # Keep the K/I identities and chronological ordering consistent with selected K3.
    selected={'K1':1073,'I2':1079,'K3':1091,'I4':1104,'K5':1123}
    arrivals={a['frame_uid']:a for a in map(json.loads,(ARCHIVE/'arrivals.jsonl').read_text().splitlines())}
    kfs={u for e in archive['events'] for u in e.get('frame_uids',[])}
    mapped=set(json.loads((RUN/'mapped_uids.json').read_text()))
    calib=np.loadtxt(archive['input_calibration'])
    for alias,uid in selected.items():
        a=arrivals[uid];assert uid in mapped and not a['held_out']
        assert (uid in kfs)==alias.startswith('K')
        src=Path(archive['input_image_directory'])/a['source_name']
        rgb,_=preprocess_image(src,calib,False)
        prov['assets'][alias]={**save_image(alias,rgb.permute(1,2,0).numpy()),
            'frame_uid':uid,'source':str(src),'source_sha256':sha(src),
            'keyframe':uid in kfs,'mapped':True,'held_out':False,'timestamp':a['sensor_timestamp']}
    assert prov['assets']['K3']['sha256']==source['files']['input.png']
    prov['aliases']=selected
    prov['selection']={'shared_map_reference':{'candidate':'C07','uid':786},
                       'rendered_modalities':{'candidate':'C10','uid':1091},'trajectory':'A'}
    prov['map_vs_render_note']='Shared-map inspection camera differs from the C10 render camera; same saved Gaussian model.'
    p.write_text(json.dumps(prov,indent=2)+'\n')
    meta['selected_candidate']={'shared_map_reference':'C07','rendered_modalities':'C10'}
    meta['selected_trajectory']='A';cm.write_text(json.dumps(meta,indent=2)+'\n')


def cutaway_views():
    """Section planes for illustration only; keep PLY and uncut C10 renders unchanged."""
    archive,records=keyframe_records()
    pose=records[786]['pose'];reference_origin=pose[:3,3]
    right=-pose[:3,1];up=-pose[:3,0];forward=pose[:3,2]
    reference_basis=np.stack([right,up,forward],axis=1)
    model=load_gaussians(RUN/'3dgs_before_final.ply')
    original_hash=sha(RUN/'3dgs_before_final.ply')
    xyz=model.get_xyz.detach().cpu().numpy();reference_local=(xyz-reference_origin)@reference_basis
    # Robust dominant wall-plane estimate in the upper rear-wall band.
    # This fit orients the illustration only; it never regularizes the source map.
    a=reference_local
    band=(abs(a[:,0])<4.5)&(a[:,1]>-.3)&(a[:,1]<.7)&(a[:,2]>.5)&(a[:,2]<4.6)
    a=a[band];rng=np.random.default_rng(123)
    a=a[rng.choice(len(a),min(len(a),6000),replace=False)]
    best=(0,None,None)
    for _ in range(600):
        triplet=a[rng.choice(len(a),3,False)]
        n=np.cross(triplet[1]-triplet[0],triplet[2]-triplet[0]);n/=max(np.linalg.norm(n),1e-10)
        if abs(n[1])>.3 or abs(n[2])<.65:continue
        d=triplet[0]@n;count=np.count_nonzero(abs(a@n-d)<.04)
        if count>best[0]:best=(count,n,d)
    count,n,d=best
    assert count>500, 'No supported wall plane; review instead of inventing alignment'
    inliers=a[abs(a@n-d)<.04];center=inliers.mean(0)
    _,_,v=np.linalg.svd(inliers-center,full_matrices=False);n=v[-1]
    if n[2]<0:n=-n
    forward=reference_basis@n
    right=np.cross(forward,up);right/=np.linalg.norm(right)
    up=np.cross(right,forward);up/=np.linalg.norm(up)
    basis=np.stack([right,up,forward],axis=1)
    origin=reference_origin+reference_basis@center
    local=(xyz-origin)@basis
    wall_fit={'method':'600 seeded RANSAC trials, 4cm support, SVD refinement; upper wall-band Gaussian centers',
        'sample_count':len(a),'support_count':int(count),'reference_local_normal':n.tolist(),
        'reference_local_center':center.tolist(),'world_normal':forward.tolist(),
        'rms_m':float(np.sqrt(np.mean(((inliers-center)@n)**2))),
        'interpretation':'dominant wall-plane estimate for display, not ground-truth surface normals'}
    out=ROOT/'assets/cutaway';out.mkdir(parents=True,exist_ok=True)
    params=[850.,850.,600.,360.,1200,720]
    def camera(eye,target):
        f=target-eye;f/=np.linalg.norm(f)
        r=np.cross(f,up);r/=np.linalg.norm(r);d=np.cross(f,r)
        ext=np.eye(4);ext[:3,:3]=np.stack([r,d,f]);ext[:3,3]=-ext[:3,:3]@eye
        fx,fy,cx,cy,w,h=params
        pr=getProjectionMatrix2(znear=.01,zfar=100.,fx=fx,fy=fy,cx=cx,cy=cy,W=w,H=h).T.cuda()
        cam=Camera.init_from_tracking(None,None,None,torch.tensor(ext,dtype=torch.float32,device='cuda'),786,pr,params)
        return cam,ext
    # One shared spatial section; vary ONLY the external camera for design review.
    low=np.array([-4.0,-1.80,-1.90]);high=np.array([4.0,.60,.48])
    keep=np.all((local>=low)&(local<=high),axis=1)
    # filter_mask in this renderer only masks gradients, so use a temporary view model.
    # No optimizer, in-place modification, or writing any Gaussian model to disk.
    section=copy.copy(model);mask=torch.tensor(keep,device='cuda')
    for attr in ['_xyz','_opacity','_scaling','_rotation','_features_dc','_features_rest']:
        setattr(section,attr,getattr(model,attr)[mask].detach())
    variants=[('S1',-6,15),('S2',0,15),('S3',6,15),
              ('S4',-6,24),('S5',0,24),('S6',6,24)]
    report=[]
    for name,yaw,pitch in variants:
        y,p=np.deg2rad([yaw,pitch]);target_local=np.array([0,-.65,-.8])
        offset=target_local+10*np.array([np.sin(y)*np.cos(p),np.sin(p),-np.cos(y)*np.cos(p)])
        eye=origin+basis@offset;target=origin+basis@target_local
        cam,ext=camera(eye,target)
        with torch.no_grad():rr=render(cam,section,torch.ones(3,device='cuda'))
        rgb=rr['render'].clamp(0,1).permute(1,2,0).cpu().numpy()
        alpha=(1-rr['transmittance']).squeeze().clamp(0,1).cpu().numpy()
        # White-background output; alpha retained separately, not used to clean geometry.
        path=out/f'{name}.png';Image.fromarray((rgb*255).round().astype(np.uint8)).save(path)
        ap=out/f'{name}_alpha.png';Image.fromarray((alpha*255).round().astype(np.uint8)).save(ap)
        report.append({'id':name,'path':str(path.relative_to(ROOT)),'sha256':sha(path),
            'camera_world_to_view':ext.tolist(),'inspection_camera_offset_local':offset.tolist(),
            'wall_relative_yaw_deg':yaw,'wall_relative_elevation_deg':pitch})
    metadata={'reference_uid':786,'reference_candidate':'C07','run':str(RUN),
        'map_sha256':original_hash,'source_gaussians':len(xyz),'displayed_gaussians':int(keep.sum()),
        'operation':'Display-only spatial cutaway. Original map unchanged; no floater pruning or quality/opacity filter.',
        'section_coordinate_origin':origin.tolist(),'section_coordinate_basis_columns_right_up_forward':basis.tolist(),
        'section_low_m':low.tolist(),'section_high_m':high.tolist(),
        'section_rule':'Keep Gaussian centers inside this box; primitives can extend slightly across the planes.',
        'parameters_unchanged':['position','rotation','scale','opacity','SH color'],
        'wall_plane_fit':wall_fit,
        'camera_intrinsics':params,'variants':report,'selected_variant':None}
    (out/'provenance.json').write_text(json.dumps(metadata,indent=2)+'\n')
    board=Image.new('RGB',(1840,870),'#f4f6fb');d=ImageDraw.Draw(board)
    d.text((20,15),'Wall-aligned Gaussian map cutaway | C07 region',font=font(29,True),fill='#12164c')
    d.text((20,58),'Wall-plane-aligned spatial section; six near-frontal cameras. Display only; original map and C10 renders unchanged.',font=font(19),fill='#526078')
    for i,item in enumerate(report):
        x=20+(i%3)*608;y=104+(i//3)*377
        d.rounded_rectangle((x,y,x+591,y+357),12,fill='white',outline='#cbd6e5',width=2)
        title=f"{item['id']} | yaw {item['wall_relative_yaw_deg']:+d} / elevation {item['wall_relative_elevation_deg']} deg"
        d.text((x+13,y+7),title,font=font(22,True),fill='#12164c')
        im=Image.open(ROOT/item['path']);im.thumbnail((567,310));board.paste(im,(x+12,y+39))
    board.save(ROOT/'candidates/04_cutaway_cameras.png')
    assert sha(RUN/'3dgs_before_final.ply')==original_hash


def select_cutaway(variant):
    """Trim empty canvas only; keep every pixel with nonzero saved alpha."""
    out=ROOT/'assets/cutaway';meta=json.loads((out/'provenance.json').read_text())
    chosen=next(v for v in meta['variants'] if v['id']==variant)
    im=Image.open(ROOT/chosen['path']);alpha=np.asarray(Image.open(out/f'{variant}_alpha.png'))
    ys,xs=np.nonzero(alpha>0)
    bbox=[max(0,int(xs.min())-22),max(0,int(ys.min())-22),min(im.width,int(xs.max())+23),min(im.height,int(ys.max())+23)]
    path=out/'selected.png';im.crop(bbox).save(path)
    meta['selected_variant']=variant;meta['empty_canvas_crop_xyxy']=bbox
    meta['selected_path']=str(path.relative_to(ROOT));meta['selected_sha256']=sha(path)
    (out/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
    p=OUT/'provenance.json';prov=json.loads(p.read_text())
    prov['assets']['map_cutaway']={'path':str(path.relative_to(ROOT)),'sha256':sha(path),
        'reference_frame_uid':786,'reference_candidate':'C07','camera_variant':variant,
        'modality':'display_only_gaussian_map_cutaway','details':'assets/cutaway/provenance.json',
        'map_source_modified':False,'clip_applied':True,'crop':bbox}
    prov['selection']['cutaway_variant']=variant;p.write_text(json.dumps(prov,indent=2)+'\n')


def main():
    OUT.mkdir(exist_ok=True)
    archive=json.loads((ARCHIVE/'archive_manifest.json').read_text())
    arrivals={a['frame_uid']:a for a in map(json.loads,(ARCHIVE/'arrivals.jsonl').read_text().splitlines())}
    runtime=json.loads((RUN/'mapping_replay_runtime.json').read_text())
    kfs={u for e in archive['events'] for u in e.get('frame_uids',[])}
    mapped=set(runtime['mapped_frame_uids'])
    selected={'K1':229,'I2':251,'K3':284,'I4':323,'K5':353}
    images=Path(archive['input_image_directory'])
    calib=np.loadtxt(archive['input_calibration'])
    assets={}
    for alias,uid in selected.items():
        a=arrivals[uid]
        assert uid in mapped and not a['held_out']
        assert (uid in kfs)==alias.startswith('K')
        source=images/a['source_name']
        rgb,params=preprocess_image(source,calib,False)
        assets[alias]={**save_image(alias,rgb.permute(1,2,0).numpy()),
                       'frame_uid':uid,'timestamp':a['sensor_timestamp'],
                       'source':str(source),'source_sha256':sha(source),
                       'modality':'input_rgb','keyframe':uid in kfs,'held_out':False,
                       'mapped':True}
    uid=selected['K3']
    # Latest causally captured version of this keyframe, not the post-EOS trajectory archive.
    event=[e for e in archive['events'] if uid in e.get('frame_uids',[])][-1]
    ref=event['geometry_refs'][event['frame_uids'].index(uid)]
    for kind in ['depth','normal']:
        path=ARCHIVE/ref[kind]
        t=torch.load(path,map_location='cpu',weights_only=False)['tensor'].numpy()
        rgb=depth_rgb(t) if kind=='depth' else normal_rgb(t.transpose(1,2,0))
        assets['prior_'+kind]={**save_image('prior_'+kind,rgb),'frame_uid':uid,
            'modality':'frontend_'+kind,'source':str(path),'source_sha256':sha(path),
            'event_id':event['event_id'],'emitted_at_frame_uid':event['emitted_at_frame_uid'],
            'normal_convention':'unit camera-space xyz mapped to RGB; display pixels rotated only' if kind=='normal' else None,
            'depth_range_m':[0.5,7.0] if kind=='depth' else None}
    trajectory=np.loadtxt(RUN/'traj_full_beforeBA.txt')
    model=load_gaussians(RUN/'3dgs_before_final.ply')
    pose=np.eye(4)
    pose[:3,:3]=Rotation.from_quat(trajectory[uid,4:8]).as_matrix()
    pose[:3,3]=trajectory[uid,1:4]
    w2c=torch.tensor(np.linalg.inv(pose),dtype=torch.float32,device='cuda')
    rgb,params=preprocess_image(images/arrivals[uid]['source_name'],calib,False)
    def camera(w2c,params):
        fx,fy,cx,cy,w,h=params
        projection=getProjectionMatrix2(znear=.01,zfar=100.,fx=fx,fy=fy,cx=cx,cy=cy,W=w,H=h).T.cuda()
        return Camera.init_from_tracking(rgb.float()/255,None,None,w2c,uid,projection,params)
    cam=camera(w2c,params)
    with torch.no_grad():
        result=render(cam,model,torch.ones(3,device='cuda'))
        rendered=result['render'].clamp(0,1).permute(1,2,0).cpu().numpy()
        depth=result['depth'].squeeze().cpu().numpy()
        normal,_=depth_to_normal(cam,result['depth'],world_frame=False)
        normal=normal.cpu().numpy()
    for key,data in [('render_rgb',rendered),('render_depth',depth_rgb(depth)),('render_normal',normal_rgb(normal))]:
        assets[key]={**save_image(key,data),'frame_uid':uid,
            'modality':key,'map_source':str(RUN/'3dgs_before_final.ply'),
            'trajectory_source':str(RUN/'traj_full_beforeBA.txt'),
            'state':'prefinal_before_global_ba_and_color_refinement',
            'renderer':'VIGS gaussian.renderer.render',
            'normal_convention':'VIGS depth_to_normal camera frame, unit vectors mapped to RGB; pixels rotated only' if key=='render_normal' else None,
            'depth_range_m':[0.5,7.0] if key=='render_depth' else None}
    # Real full-map overview from a virtual inspection camera. No Gaussian deletion,
    # opacity modification, or scale modification. White background, normal frustum culling.
    xyz=model.get_xyz.detach().cpu().numpy()
    center=np.median(xyz,axis=0)
    display_rotation=np.eye(4)
    display_rotation[:3,:3]=[[0,-1,0],[1,0,0],[0,0,1]]
    ext=display_rotation@np.linalg.inv(pose)
    cp=[450.,450.,500.,300.,1000,600]
    mc=camera(torch.tensor(ext,dtype=torch.float32,device='cuda'),cp)
    with torch.no_grad():
        rr=render(mc,model,torch.ones(3,device='cuda'))
    assets['map_interior']={**save_image('map_interior',rr['render'].clamp(0,1).permute(1,2,0).cpu().numpy(),False),
        'modality':'gaussian_map_wide_fov_inspection','camera_center_frame_uid':uid,
        'camera_world_to_view':ext.tolist(),'intrinsics':cp,
        'all_gaussians_retained':True,'opacity_or_scale_modified':False}
    for name,position in [('map_a',[-8,-5,10]),('map_b',[-10,-7,3]),('map_c',[-4,4,12])]:
        eye=np.asarray(position,dtype=float)
        forward=(center-eye);forward/=np.linalg.norm(forward)
        # Aria scene vertical is approximately world X; use -X as camera up.
        up=np.array([-1.,0,0])
        right=np.cross(forward,up);right/=np.linalg.norm(right)
        down=np.cross(forward,right)
        rotation=np.stack([right,down,forward])
        ext=np.eye(4);ext[:3,:3]=rotation;ext[:3,3]=-rotation@eye
        cp=[600.,600.,500.,300.,1000,600]
        mc=camera(torch.tensor(ext,dtype=torch.float32,device='cuda'),cp)
        with torch.no_grad():
            rr=render(mc,model,torch.ones(3,device='cuda'))
        assets[name]={**save_image(name,rr['render'].clamp(0,1).permute(1,2,0).cpu().numpy(),False),
            'modality':'gaussian_map_virtual_camera','camera_world_to_view':ext.tolist(),
            'intrinsics':cp,'all_gaussians_retained':True,'opacity_or_scale_modified':False}
    report={'run':str(RUN),'run_approved_for':'overview illustration, not complete-method efficacy claim',
            'map_sha256':sha(RUN/'3dgs_before_final.ply'),'archive':str(ARCHIVE),
            'causal_carve_enabled':runtime['causal_carve_enabled'],
            'no_training_performed':True,'display_rotation':'all frame images 90 degrees clockwise, no recoloring RGB',
            'aliases':selected,'assets':assets,
            'schematics':'trajectory icons, growth stages, counts/probabilities and ray diagram are explanatory, not measured history'}
    trajectory_file=ROOT/'assets/trajectory/pose_plane.png'
    if trajectory_file.exists():
        report['assets']['trajectory']={'path':str(trajectory_file.relative_to(ROOT)),
            'sha256':sha(trajectory_file),'modality':'actual_keyframe_pose_projection'}
        report['schematics']='growth stages, counts/probabilities and ray diagram; poses use actual saved keyframe estimates'
    (OUT/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    print(OUT/'provenance.json')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidates',action='store_true')
    parser.add_argument('--trajectory',action='store_true')
    parser.add_argument('--apply-selection',action='store_true')
    parser.add_argument('--cutaway',action='store_true')
    parser.add_argument('--select-cutaway',choices=['S1','S2','S3','S4','S5','S6'])
    args=parser.parse_args()
    if not any(vars(args).values()):
        p=OUT/'provenance.json'
        if p.exists() and json.loads(p.read_text()).get('selection'):
            parser.error('Selections already exist. Use explicit action flags; run build_overview_v02.py to rebuild only the overview.')
    if args.candidates:candidate_views()
    if args.trajectory:trajectory_views()
    if args.apply_selection:apply_selection()
    if args.cutaway:cutaway_views()
    if args.select_cutaway:select_cutaway(args.select_cutaway)
    if not (args.candidates or args.trajectory or args.apply_selection or args.cutaway or args.select_cutaway):main()
