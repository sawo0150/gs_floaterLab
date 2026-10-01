#!/usr/bin/env python3
"""A teaser: immutable saved-map renders and measured historical curves.

No training, no generated pixels, no changes to source experiments or manuscript.
Use --assets to render saved maps (VIGS environment), then --build for SVG/PDF.
"""
import argparse
import base64
import hashlib
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parents[2]
RUN = WORK / 'results/figure03_scene_search_20260921/rpng/table_06'
CURVE = RUN / 'evaluation/curves.json'
ASSETS = ROOT / 'candidates/real_A_2026-10-01'
OUT = ROOT / 'output/scene_centered_A_2026-10-01'
FRAME = 1420
ROI = [440, 40, 564, 164]
BLUE = '#0057FF'
AMBER = '#C77D17'


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(p, value):
    Path(p).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def assets():
    active = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name', '--format=csv,noheader'], text=True).strip()
    assert not active, f'GPU occupied; do not terminate: {active}'
    sys.path.insert(0, str(WORK / 'humanteck/sections/02_method/figure03/scripts'))
    from evaluate_convergence import np, torch, lietorch, Image, load_gaussians, render, preprocess_image, Camera, getProjectionMatrix2, psnr
    import copy
    import cv2
    ASSETS.mkdir(parents=True, exist_ok=True)
    data = read(CURVE)
    finals = {a: next(r for r in data['curves'] if r['arm'] == a and r['final']) for a in ['ours', 'baseline']}
    assert finals['ours']['training_renders'] == finals['baseline']['training_renders']
    cmd = read(RUN / 'ours/mapping_command.json')
    archive = Path(cmd[cmd.index('--archive') + 1])
    manifest = read(archive / 'archive_manifest.json')
    pose_rows = np.loadtxt(RUN / 'ours/traj_full_beforeBA.txt')
    np.testing.assert_allclose(pose_rows, np.loadtxt(RUN / 'baseline/traj_full_beforeBA.txt'), atol=1e-6, rtol=0)
    pose = lietorch.SE3(torch.tensor(pose_rows[FRAME, 1:], dtype=torch.float32, device='cuda')).matrix().cpu().numpy()
    expected = read(RUN / 'evaluation/ours_02714_final.json')
    view = next(v for v in expected['per_view'] if v['frame_index'] == FRAME)
    rgb, params = preprocess_image(Path(manifest['input_image_directory']) / view['uid'], np.loadtxt(manifest['input_calibration']), manifest['preprocessing']['undistort'])

    def camera(ext, K=params, color=None):
        fx, fy, cx, cy, w, h = K
        pr = getProjectionMatrix2(znear=.01, zfar=100., fx=fx, fy=fy, cx=cx, cy=cy, W=w, H=h).T.cuda()
        return Camera.init_from_tracking(color, None, None, torch.tensor(ext, dtype=torch.float32, device='cuda'), FRAME, pr, K)

    def save(path, a):
        if hasattr(a, 'detach'):
            a = a.detach().cpu().numpy()
        if a.ndim == 3 and a.shape[0] == 3:
            a = a.transpose(1, 2, 0)
        Image.fromarray((np.clip(a, 0, 1) * 255).round().astype('uint8')).save(path)

    cam = camera(np.linalg.inv(pose), color=rgb.float()/255)
    save(ASSETS / 'gt.png', rgb.float()/255)
    info = {'scene': 'RPNG table_06', 'frame_index': FRAME, 'uid': view['uid'], 'source_curve': str(CURVE), 'curve_sha256': sha(CURVE), 'archive': str(archive), 'training_renders_each': finals['ours']['training_renders'], 'heldout_count': data['heldout_count'], 'camera_to_world': pose.tolist(), 'image_intrinsics': params, 'depth_range_m': [0.5, 4.0], 'models': {}, 'no_training': True, 'carve_enabled': False, 'geometry_interpretation': 'Rendered depth only. Not independent geometry ground truth, Carve ablation or evidence of improved geometry accuracy.'}
    models = {}
    for arm, row in finals.items():
        model = load_gaussians(Path(row['map']))
        models[arm] = model
        with torch.no_grad():
            rr = render(cam, model, torch.ones(3, device='cuda'))
        pred = rr['render'].clamp(0, 1)
        gt = cam.original_image.cuda()
        val = float(psnr(pred[gt > 0][None], gt[gt > 0][None]).item())
        ev = read(RUN / f'evaluation/{arm}_{row["iteration"]:05d}_final.json')
        old = next(v['psnr'] for v in ev['per_view'] if v['frame_index'] == FRAME)
        assert abs(val - old) < .005, (arm, val, old)
        save(ASSETS / f'{arm}_rgb.png', pred)
        d = rr['depth'].squeeze().cpu().numpy()
        np.save(ASSETS / f'{arm}_depth.npy', d)
        v = np.clip((d - .5) / 3.5, 0, 1)
        colored = cv2.applyColorMap((v * 255).round().astype('uint8'), cv2.COLORMAP_VIRIDIS)[:, :, ::-1]
        colored[(~np.isfinite(d)) | (d <= 0)] = 255
        Image.fromarray(colored).save(ASSETS / f'{arm}_depth.png')
        info['models'][arm] = {'map': row['map'], 'map_sha256': sha(row['map']), 'iteration': row['iteration'], 'training_renders': row['training_renders'], 'frame_psnr': val, 'expected_frame_psnr': old, 'mean_heldout_psnr': row['mean_psnr']}

    # Display-only cutaway in the reference camera coordinate system, no quality filtering.
    model = models['ours']
    xyz = model.get_xyz.detach().cpu().numpy()
    local = (xyz - pose[:3, 3]) @ pose[:3, :3]
    low = np.array([-2.7, -.65, .05]); high = np.array([2.7, 2.0, 2.4])
    keep = np.all((local >= low) & (local <= high), axis=1)
    section = copy.copy(model)
    mask = torch.tensor(keep, device='cuda')
    for attr in ['_xyz', '_opacity', '_scaling', '_rotation', '_features_dc', '_features_rest']:
        setattr(section, attr, getattr(model, attr)[mask].detach())
    info['display_section'] = {'low_camera_xyz': low.tolist(), 'high_camera_xyz': high.tolist(), 'source_gaussians': len(xyz), 'displayed_gaussians': int(keep.sum()), 'purpose': 'Spatial cutaway for scene context only. No opacity/quality pruning; source PLY and detail renders unchanged.'}
    up = -pose[:3, 1]
    kfs = np.loadtxt(RUN / 'ours/traj_kf_beforeBA.txt')
    mid=int(np.argmin(abs(kfs[:,0]-pose_rows[FRAME,0])))
    start,end=max(0,mid-7),min(len(kfs),mid+8)
    selected = np.linspace(start, end-1, 4).round().astype(int)
    frusta = []
    fx, fy, cx, cy, w, h = params
    for idx in selected:
        p = lietorch.SE3(torch.tensor(kfs[idx, 1:], dtype=torch.float32, device='cuda')).matrix().cpu().numpy()
        z = .14
        corners = np.array([[0, 0, 0], [-cx/fx*z, -cy/fy*z, z], [(w-cx)/fx*z, -cy/fy*z, z], [(w-cx)/fx*z, (h-cy)/fy*z, z], [-cx/fx*z, (h-cy)/fy*z, z]])
        frusta.append({'keyframe_index': int(idx), 'corners_world': (corners @ p[:3, :3].T + p[:3, 3]).tolist()})
    # RGB ROI is projected using this same map's rendered depth, not a hand-placed correspondence.
    depth = np.load(ASSETS / 'ours_depth.npy')
    x0, y0, x1, y1 = ROI
    xyz_roi = []
    for u, v in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        z = float(np.median(depth[max(0,v-2):v+3, max(0,u-2):u+3]))
        xyz_roi.append((pose[:3,:3] @ np.array([(u-cx)/fx*z, (v-cy)/fy*z, z]) + pose[:3,3]).tolist())
    info['rgb_roi_xyxy'] = ROI
    info['roi_corners_world'] = xyz_roi
    u,v=(x0+x1)//2,(y0+y1)//2
    z=float(np.median(depth[v-2:v+3,u-2:u+3]))
    info['roi_center_world']=(pose[:3,:3] @ np.array([(u-cx)/fx*z,(v-cy)/fy*z,z])+pose[:3,3]).tolist()
    info['trajectory_source'] = str(RUN / 'ours/traj_kf_beforeBA.txt')
    info['trajectory_world'] = kfs[start:end,1:4].tolist()
    info['trajectory_segment_indices'] = [start,end]
    info['camera_frusta'] = frusta
    variants = []
    K = [980., 980., 700., 490., 1400, 980]
    for name, eye_local, target_local in [
        ('V1', [-2.0, -1.5, -3.2], [0, .4, 1.8]),
        ('V2', [-1.0, -1.2, -3.4], [0, .4, 1.8]),
        ('V3', [1.2, -1.4, -3.4], [0, .4, 1.8]),
        ('V4', [-2.0, -2.4, -2.0], [0, .5, 1.8]),
    ]:
        eye = pose[:3,3] + pose[:3,:3] @ np.array(eye_local)
        target = pose[:3,3] + pose[:3,:3] @ np.array(target_local)
        f = target-eye; f /= np.linalg.norm(f)
        right = np.cross(f, up); right /= np.linalg.norm(right)
        down = np.cross(f, right)
        ext = np.eye(4); ext[:3,:3] = np.stack([right,down,f]); ext[:3,3] = -ext[:3,:3] @ eye
        with torch.no_grad():
            rr = render(camera(ext, K), section, torch.ones(3,device='cuda'))
        save(ASSETS / f'map_{name}.png', rr['render'].clamp(0,1))
        variants.append({'id':name, 'image':f'map_{name}.png', 'world_to_camera':ext.tolist(), 'intrinsics':K})
    info['map_variants'] = variants
    info['source_map_unchanged'] = all(sha(v['map']) == v['map_sha256'] for v in info['models'].values())
    info['files'] = {p.name:sha(p) for p in ASSETS.glob('*.png')}
    write_json(ASSETS / 'provenance.json', info)
    print(json.dumps({'rendered': str(ASSETS), 'rgb_verification': info['models'], 'section':info['display_section']}, indent=2))


def build():
    import math
    meta = read(ASSETS / 'provenance.json')
    data = read(CURVE)
    OUT.mkdir(parents=True, exist_ok=True)
    assert len(data['curves']) == 28
    assert all(sum(r['arm']==a for r in data['curves']) == 14 for a in ['ours','baseline'])
    W,H = 1800,610
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="180mm" height="61mm" viewBox="0 0 {W} {H}">', '<title>ROGO-SLAM teaser A: historical RPNG table_06 results</title>', '<desc>Actual saved-map render and trajectory, held-out RGB details, qualitative rendered depth and 28 measured held-out PSNR checkpoints. Carve disabled. Spatial cutaway only on the context image. No generative image content.</desc>', '<rect width="1800" height="610" fill="white"/>', '<g font-family="Times New Roman" fill="#202329">']
    def text(x,y,t,size=24,color='#202329',anchor='start',bold=False,extra=''):
        s.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{700 if bold else 400}" {extra}>{html.escape(t)}</text>')
    def line(x1,y1,x2,y2,color='#ADB3BC',sw=1.2,dash=''):
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
    def poly(points,color,sw=1.6,fill='none',close=False,dash=''):
        tag='polygon' if close else 'polyline'
        s.append(f'<{tag} points="'+ ' '.join(f'{x:.3f},{y:.3f}' for x,y in points)+f'" fill="{fill}" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
    def rect(x,y,w,h,color='#CCD0D7',sw=1.1):
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{color}" stroke-width="{sw}"/>')
    def image(path,x,y,w,h,crop=None,source_wh=None):
        uri='data:image/png;base64,'+base64.b64encode(Path(path).read_bytes()).decode()
        if crop:
            a,b,c,d=crop; scale=w/(c-a); assert abs(h/(d-b)-scale)<1e-5
            clip=f'clip{len(s)}'; s.append(f'<defs><clipPath id="{clip}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath></defs><g clip-path="url(#{clip})">')
            iw,ih=source_wh; s.append(f'<image x="{x-a*scale}" y="{y-b*scale}" width="{iw*scale}" height="{ih*scale}" xlink:href="{uri}"/>');s.append('</g>')
        else:s.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" xlink:href="{uri}"/>')
    text(16,32,'(a) Reconstructed scene',29,bold=True)
    text(742,32,'(b) Same-view comparison',29,bold=True)
    text(1265,32,'(c) Online refinement',29,bold=True)
    s.append('<g id="scene" inkscape:groupmode="layer" inkscape:label="01 Actual map and camera poses">')
    text(17,62,'RPNG table_06',23,color='#606672')
    variant = next(v for v in meta['map_variants'] if v['id']=='V2')
    # Same 1400x980 perspective for the map and all projected annotations.
    map_crop=[100,250,1300,980]
    mx,my,mw=0,95,712
    mh=(map_crop[3]-map_crop[1])*mw/(map_crop[2]-map_crop[0])
    image(ASSETS/variant['image'],mx,my,mw,mh,map_crop,(1400,980))
    E=variant['world_to_camera'];fx,fy,cx,cy,_,_=variant['intrinsics']
    def project(p):
        q=[sum(E[i][j]*p[j] for j in range(3))+E[i][3] for i in range(3)]
        scale=mw/(map_crop[2]-map_crop[0])
        return mx+(fx*q[0]/q[2]+cx-map_crop[0])*scale, my+(fy*q[1]/q[2]+cy-map_crop[1])*scale
    s.append('<defs><clipPath id="map-clip"><rect x="0" y="64" width="712" height="498.4"/></clipPath></defs><g clip-path="url(#map-clip)">')
    path=[project(p) for p in meta['trajectory_world']]
    poly(path,'white',3.8);poly(path,BLUE,1.8)
    for f in meta['camera_frusta']:
        p=[project(v) for v in f['corners_world']]
        poly(p[1:],BLUE,.9,close=True)
        for j in range(1,5):line(*p[0],*p[j],BLUE,.9)
    target=project(meta['roi_center_world'])
    s.append(f'<circle cx="{target[0]}" cy="{target[1]}" r="15" fill="none" stroke="{AMBER}" stroke-width="2.5"/>')
    s.append('</g>')
    # One accurate spatial connection to the appearance ROI; depth is full-view.
    right=(target[0]+15,target[1]); poly([right,(692,right[1]),(730,129),(752,129)],AMBER,1.5,dash='6 5')
    text(22,548,'Gaussian map + local camera trajectory',23)
    text(22,576,'Spatial cutaway for display only',21,color='#686D75')
    s.append('</g><g id="comparisons" inkscape:groupmode="layer" inkscape:label="02 Paired held-out RGB and rendered depth">')
    line(730,61,730,560,'#D8DCE2')
    text(861,75,'VIGS-SLAM',25,anchor='middle',bold=True)
    text(1099,75,'Ours',25,BLUE,'middle',True)
    text(750,110,'Appearance detail',23,bold=True)
    for arm,x,c in [('baseline',752,'#4C525C'),('ours',990,BLUE)]:
        image(ASSETS/f'{arm}_rgb.png',x,123,218,218,ROI,(616,344));rect(x,123,218,218,c,1.5)
    text(750,378,'Rendered depth',23,bold=True)
    text(1208,378,'geometry term off',20,anchor='end',color='#686D75')
    for arm,x,c in [('baseline',752,'#4C525C'),('ours',990,BLUE)]:
        image(ASSETS/f'{arm}_depth.png',x,394,218,121.74);rect(x,394,218,121.74,c,1.2)
    # Compact shared viridis colorbar, deterministic standard palette anchors.
    stops=['#440154','#414487','#2A788E','#22A884','#7AD151','#FDE725']
    s.append('<defs><linearGradient id="depthbar">'+''.join(f'<stop offset="{i/(len(stops)-1)}" stop-color="{c}"/>' for i,c in enumerate(stops))+'</linearGradient></defs>')
    s.append('<rect x="921" y="537" width="128" height="10" fill="url(#depthbar)"/>')
    text(910,552,'0.5',20,anchor='end');text(1060,552,'4.0 m',20)
    text(980,579,'34,437 training renders per method',21,anchor='middle',color='#606672')
    line(1233,61,1233,560,'#D8DCE2')
    s.append('</g><g id="measured-curves" inkscape:groupmode="layer" inkscape:label="03 Measured held-out curves">')
    # All 28 measured points, linear axes; not a fitted or smoothed convergence curve.
    xl,xr,yt,yb=1311,1763,108,471
    px=lambda k:xl+(xr-xl)*k/36000
    py=lambda v:yb-(yb-yt)*(v-14)/12
    for v in [14,18,22,26]:
        y=py(v);line(xl,y,xr,y,'#E1E4E9',1,'3 5');text(xl-12,y+7,str(v),23,anchor='end')
    for k in [0,10000,20000,30000]:
        x=px(k);line(x,yb,x,yb+5,'#555');text(x,yb+30,str(k//1000),23,anchor='middle')
    line(xl,yt,xl,yb,'#4C525C',1.5);line(xl,yb,xr,yb,'#4C525C',1.5)
    line(px(meta['training_renders_each']),yt,px(meta['training_renders_each']),yb,'#ABB2BF',1.2,'4 5')
    text(1264,290,'Held-out PSNR (dB)',23,anchor='middle',extra='transform="rotate(-90 1264 290)"')
    text((xl+xr)/2,535,'Training renders (×10³)',24,anchor='middle')
    text((xl+xr)/2,576,'555 held-out views · measured checkpoints',21,anchor='middle',color='#606672')
    for a,c in [('baseline','#52565E'),('ours',BLUE)]:
        rows=sorted([r for r in data['curves'] if r['arm']==a],key=lambda r:r['training_renders'])
        poly([(px(r['training_renders']),py(r['mean_psnr'])) for r in rows],c,3.0,dash='8 5' if a=='baseline' else '')
        for r in rows:s.append(f'<circle cx="{px(r["training_renders"])}" cy="{py(r["mean_psnr"])}" r="2.5" fill="{c}"/>')
        end=rows[-1];x=px(end['training_renders']);y=py(end['mean_psnr'])
        s.append(f'<circle cx="{x}" cy="{y}" r="5.5" fill="white" stroke="{c}" stroke-width="2.3"/>')
    line(1314,76,1348,76,BLUE,3);text(1358,83,'Ours',24,BLUE)
    line(1460,76,1494,76,'#52565E',3,'7 4');text(1504,83,'VIGS-SLAM',24)
    s.append('</g></g></svg>')
    svg=OUT/'figure.svg';svg.write_text('\n'.join(s))
    subprocess.run(['inkscape',str(svg),'--export-type=pdf',f'--export-filename={OUT/"figure.pdf"}'],check=True,capture_output=True)
    subprocess.run(['pdftoppm','-png','-singlefile','-r','300',str(OUT/'figure.pdf'),str(OUT/'figure')],check=True)
    provenance={'kind':'real_data_historical_draft','experimental_evidence':True,'full_method_evidence':False,'source_assets':str(ASSETS/'provenance.json'),'source_assets_sha256':sha(ASSETS/'provenance.json'),'source_curve':str(CURVE),'source_curve_sha256':sha(CURVE),'all_28_points_preserved':True,'curve_x':'logged cumulative training renders; not optimizer steps or elapsed time','checkpoint_comparison':'final same 34437 training renders; intermediate input prefixes are not equalized','map_variant':variant,'appearance_roi':ROI,'geometry':'Full-view expected-depth render, same camera, common 0.5-4m color range. No accuracy or Carve claim.','font':'Times New Roman, embedded in PDF','width_mm':180,'height_mm':61,'raster_postprocessing':'Shared crop/scaling only. No sharpening, cleanup, denoising, generative editing.','renderer':'Inkscape SVG -> PDF -> Poppler PNG','manuscript_modified':False,'files':{p.name:sha(p) for p in [svg,OUT/'figure.pdf',OUT/'figure.png']}}
    provenance['map_canvas_crop_xyxy']=map_crop
    provenance['correspondence']='Projected actual ROI center using local median rendered depth; leader is not a pipeline arrow.'
    provenance['trajectory_segment_indices']=meta['trajectory_segment_indices']
    write_json(OUT/'provenance.json',provenance)
    print(json.dumps({'output':str(OUT),'provenance':provenance},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--assets',action='store_true');p.add_argument('--build',action='store_true');args=p.parse_args()
    if args.assets:assets()
    if args.build:build()
