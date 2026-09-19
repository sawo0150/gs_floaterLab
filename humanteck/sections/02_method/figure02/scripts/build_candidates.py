#!/usr/bin/env python3
"""Rank existing paired metrics and render saved maps. No training or source writes."""
from pathlib import Path
import argparse, csv, hashlib, json, math, subprocess, sys

WORK=Path('/home/intern/gs_floaterLab')
ROOT=Path(__file__).resolve().parent.parent
RUNS=WORK/'results/experiments/exp94_normalized_metric_v2_fixed_eval'

def read(p):return json.loads(Path(p).read_text())
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def csv_file(path,rows,keys):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(rows)

def scan():
    scenes=[];allviews=[];first=[];seconds=[]
    for path in sorted(RUNS.glob('*/*/pair_result.json')):
        pair=read(path);v=read(path.parent/'pair_verification.json')
        assert v['valid'] and pair['fairness_pass']
        n=Path(v['d1_run']);b=Path(v['vanilla_run'])
        nm=read(n/'psnr/strict_fixed_manifest/final_result.json')
        bm=read(b/'psnr/strict_fixed_manifest/final_result.json')
        assert nm['mapping_disjoint_filter_enforced'] and bm['mapping_disjoint_filter_enforced']
        nb={x['uid']:x for x in nm['per_view'] if x['predeclared_fixed_manifest_split']}
        bb={x['uid']:x for x in bm['per_view'] if x['predeclared_fixed_manifest_split']}
        assert nb.keys()==bb.keys()
        rows=[];carve_enabled=read(n/'mapping_replay_runtime.json').get('causal_carve_enabled',False)
        for uid,a in nb.items():
            z=bb[uid];assert not a['is_mapping_view'] and not z['is_mapping_view']
            assert a['frame_index']==z['frame_index']
            rows.append({'dataset':pair['dataset'],'scene':pair['scene'],'uid':uid,'frame_index':a['frame_index'],
                'baseline_psnr':z['psnr'],'ours_psnr':a['psnr'],'delta_psnr':a['psnr']-z['psnr'],
                'scene_delta_psnr':pair['delta_psnr'],'scene_baseline_psnr':pair['vanilla_psnr'],
                'scene_ours_psnr':pair['normalized_psnr'],'baseline_run':str(b),'ours_run':str(n),
                'physical_renders':pair['normalized_renders'],'baseline_adam':pair['vanilla_adam'],'ours_adam':pair['normalized_adam'],
                'held_out':True,'carve_enabled':carve_enabled})
        rows.sort(key=lambda x:x['delta_psnr'],reverse=True)
        span=max(x['frame_index'] for x in rows)-min(x['frame_index'] for x in rows)
        first.append(rows[0])
        second=next((x for x in rows[1:] if abs(x['frame_index']-rows[0]['frame_index'])>=max(20,.1*span)),None)
        if second:seconds.append(second)
        allviews.extend(rows)
        scenes.append({**pair,'held_out_count':len(rows),'max_view_delta_psnr':rows[0]['delta_psnr'],'top_frame_index':rows[0]['frame_index']})
    chosen=first+sorted(seconds,key=lambda x:x['delta_psnr'],reverse=True)[:7]
    chosen.sort(key=lambda x:x['delta_psnr'],reverse=True)
    for i,c in enumerate(chosen,1):c['candidate']=f'F{i:02d}'
    scenes.sort(key=lambda x:x['delta_psnr'],reverse=True);allviews.sort(key=lambda x:x['delta_psnr'],reverse=True)
    a=ROOT/'analysis';a.mkdir(exist_ok=True)
    write(a/'scene_ranking.json',scenes);write(a/'view_ranking.json',allviews);write(a/'selected_candidates.json',chosen)
    csv_file(a/'scene_ranking.csv',scenes,['dataset','scene','normalized_psnr','vanilla_psnr','delta_psnr','held_out_count','max_view_delta_psnr'])
    csv_file(a/'view_ranking.csv',allviews,['dataset','scene','frame_index','uid','baseline_psnr','ours_psnr','delta_psnr','scene_delta_psnr'])
    write(a/'scan_summary.json',{'pairs':len(scenes),'held_out_views':len(allviews),'candidates':len(chosen),
        'selection':'One maximum-delta held-out view per scene, plus seven high-delta second views separated by >=10% of frame span (minimum 20 frames). Deliberately favorable examples, not typical or unbiased samples.',
        'source_protocol':'exp94 corrected evaluator, exact paired physical-render budget, no end-to-end runtime claim'})
    print(json.dumps({'pairs':len(scenes),'held_out_views':len(allviews),'chosen':[(x['candidate'],x['scene'],x['frame_index'],round(x['delta_psnr'],2)) for x in chosen]},indent=2))

def render_candidates():
    import numpy as np
    import torch, lietorch
    from PIL import Image,ImageDraw,ImageFont
    sys.path.insert(0,str(WORK/'benchmarks/online_gs'))
    from exp78_evaluate_vigs_ply import load_gaussians,preprocess_image
    from gaussian.renderer import render
    from gaussian.utils.camera_utils import Camera
    from gaussian.utils.graphics_utils import getProjectionMatrix2
    from gaussian.utils.loss_utils import psnr
    choices=read(ROOT/'analysis/selected_candidates.json');done=[]
    out=ROOT/'candidates';out.mkdir(exist_ok=True)
    fp=subprocess.check_output(['fc-match','-f','%{file}','Times New Roman'],text=True)
    def font(size):return ImageFont.truetype(fp,size)
    def put(canvas,im,box):
        x,y,w,h=box;scale=min(w/im.width,h/im.height)
        copy=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.BILINEAR)
        canvas.paste(copy,(x+(w-copy.width)//2,y+(h-copy.height)//2))
    # Load each map once even when several viewpoints were selected from its scene.
    for scene_key in sorted({(c['dataset'],c['scene']) for c in choices}):
        batch=[c for c in choices if (c['dataset'],c['scene'])==scene_key]
        example=batch[0];n=Path(example['ours_run']);b=Path(example['baseline_run'])
        cmd=read(n/'mapping_command.json');archive=Path(cmd[cmd.index('--archive')+1]);am=read(archive/'archive_manifest.json')
        images=Path(am['input_image_directory']);calib=np.loadtxt(am['input_calibration']);undistort=am['preprocessing']['undistort']
        nt=np.atleast_2d(np.loadtxt(n/'traj_full_beforeBA.txt'));bt=np.atleast_2d(np.loadtxt(b/'traj_full_beforeBA.txt'))
        assert nt.shape==bt.shape
        model_hashes={name:sha(run/'3dgs_before_final.ply') for name,run in [('baseline',b),('ours',n)]}
        models={name:load_gaussians(run/'3dgs_before_final.ply') for name,run in [('baseline',b),('ours',n)]}
        for c in batch:
            idx=c['frame_index'];assert np.allclose(nt[idx],bt[idx],atol=1e-6,rtol=0),f'Pose mismatch: {c}'
            rgb,params=preprocess_image(images/c['uid'],calib,undistort)
            fx,fy,cx,cy,w,h=params
            projection=getProjectionMatrix2(znear=.01,zfar=100.,fx=fx,fy=fy,cx=cx,cy=cy,W=w,H=h).T.cuda()
            pose=lietorch.SE3(torch.tensor(nt[idx,1:],dtype=torch.float32,device='cuda')).inv().matrix().data
            frame=Camera.init_from_tracking(rgb.float()/255,None,None,pose,idx,projection,params)
            gt=frame.original_image.cuda();mask=gt>0
            arrays={'gt':gt.permute(1,2,0).cpu().numpy()};recomputed={}
            for name,model in models.items():
                with torch.no_grad():pred=render(frame,model,torch.ones(3,device='cuda'))['render'].clamp(0,1)
                measured=float(psnr(pred[mask][None],gt[mask][None]).item())
                expected=c[f'{name}_psnr'];assert abs(measured-expected)<.005,(c['candidate'],name,measured,expected)
                recomputed[name]=measured;arrays[name]=pred.permute(1,2,0).cpu().numpy()
            rotate=c['dataset']=='aria'
            if rotate:arrays={k:np.rot90(v,k=-1).copy() for k,v in arrays.items()}
            hh,ww=arrays['gt'].shape[:2];side=round(min(hh,ww)*.36)
            # Candidate ROI: largest mean pixel-MSE reduction, avoiding an empty GT patch.
            gain=((arrays['baseline']-arrays['gt'])**2-(arrays['ours']-arrays['gt'])**2).mean(2)
            gray=arrays['gt'].mean(2);score=(-1e9,None)
            for y in range(0,hh-side+1,8):
                for x in range(0,ww-side+1,8):
                    patch=gray[y:y+side,x:x+side]
                    if patch.std()<.035:continue
                    val=float(gain[y:y+side,x:x+side].mean())
                    if val>score[0]:score=(val,[x,y,x+side,y+side])
            bbox=score[1] or [(ww-side)//2,(hh-side)//2,(ww+side)//2,(hh+side)//2]
            folder=out/'frames'/c['candidate'];folder.mkdir(parents=True,exist_ok=True)
            ims={k:Image.fromarray((v*255).round().clip(0,255).astype('uint8')) for k,v in arrays.items()}
            for key,im in ims.items():im.save(folder/f'{key}.png');im.crop(bbox).save(folder/f'{key}_crop.png')
            card=Image.new('RGB',(1536,1020),'white');d=ImageDraw.Draw(card)
            title=f"{c['candidate']} | {c['dataset'].upper()} {c['scene']} | frame {idx} | view gain +{c['delta_psnr']:.2f} dB"
            d.text((20,12),title,font=font(31),fill='#17223b')
            for j,key in enumerate(['baseline','ours','gt']):
                x=18+j*506;label={'baseline':'VIGS-SLAM','ours':'Ours (Carve off)','gt':'Ground truth'}[key]
                d.text((x+10,55),label,font=font(28),fill='black')
                annotated=ims[key].copy();ImageDraw.Draw(annotated).rectangle(bbox,outline='#eca800',width=3)
                put(card,annotated,(x,98,488,345));put(card,ims[key].crop(bbox),(x,470,488,430))
                if key!='gt':d.text((x+10,923),f"Full-view PSNR: {c[key+'_psnr']:.2f} dB",font=font(25),fill='#17223b')
            d.text((20,964),'Actual saved-map renders | high-gain selection | identical crop | no sharpening or color enhancement',font=font(23),fill='#666666')
            card.save(out/f"{c['candidate']}_comparison.png")
            rec={**c,'source_rgb':str(images/c['uid']),'source_rgb_sha256':sha(images/c['uid']),
                'source_map_sha256':model_hashes,'archive':str(archive),'same_pose_checked':True,
                'rendered_psnr_check':recomputed,'display_rotation_clockwise_degrees':90 if rotate else 0,
                'crop_xyxy_display_pixels':bbox,'crop_rule':'maximum mean pixel-MSE improvement on 8px grid, 36% min-side square, GT std >=0.035; candidate only, not semantic hand selection',
                'files':{p.name:sha(p) for p in folder.glob('*.png')}}
            write(folder/'provenance.json',rec);done.append(rec);print(c['candidate'],c['scene'],idx,'PASS',flush=True)
            frame.clean()
        del models;torch.cuda.empty_cache()
        for name,run in [('baseline',b),('ours',n)]:assert sha(run/'3dgs_before_final.ply')==model_hashes[name]
    done.sort(key=lambda x:x['candidate']);write(out/'manifest.json',done)
    # Six compact full-view comparison pages; per-candidate cards provide larger crops.
    for page in range(math.ceil(len(done)/4)):
        group=done[page*4:(page+1)*4];board=Image.new('RGB',(1650,1420),'white');d=ImageDraw.Draw(board)
        d.text((20,12),f'Fig. 2 actual candidates | page {page+1} | ranked by held-out PSNR gain',font=font(29),fill='#17223b')
        for j,label in enumerate(['VIGS-SLAM','Ours (Carve off)','Ground truth']):d.text((30+j*545,55),label,font=font(27),fill='black')
        for i,c in enumerate(group):
            y=100+i*320
            d.text((20,y),f"{c['candidate']}  {c['dataset'].upper()} / {c['scene']}  frame {c['frame_index']} | {c['baseline_psnr']:.2f} -> {c['ours_psnr']:.2f} dB (+{c['delta_psnr']:.2f})",font=font(25),fill='#17223b')
            for j,key in enumerate(['baseline','ours','gt']):
                im=Image.open(out/'frames'/c['candidate']/f'{key}.png');put(board,im,(15+j*545,y+40,530,265))
        d.text((20,1380),'Selected high-gain examples, not average views. See individual cards for identical-region enlargements.',font=font(23),fill='#666666')
        board.save(out/f'contact_sheet_{page+1:02d}.png')

def build_figure():
    """CPU-only publication layout from verified F04 PNGs; no generated pixels."""
    import base64
    from io import BytesIO
    from PIL import Image
    from xml.sax.saxutils import escape
    source=ROOT/'candidates/frames/F04'
    provenance=read(source/'provenance.json')
    assert provenance['held_out'] and provenance['same_pose_checked']
    assert provenance['carve_enabled'] is False
    output=ROOT/'output';pdf_dir=output/'pdf';pdf_dir.mkdir(parents=True,exist_ok=True)
    # Match the actual Humantech single-column width: (180 mm - 20 TeX pt)/2.
    width_mm=(180-20*25.4/72.27)/2
    W,H=1800,640;panel_w=576;gap=24;outer=12;image_y=76
    crop=(440,40,564,164)  # exact existing F04 ROI: logo and printed pattern below it
    inset_y=310;inset_w=320;amber='#dc9700'
    font_path=subprocess.check_output(['fc-match','-f','%{file}','Times New Roman'],text=True)
    assert 'Times_New_Roman' in font_path or 'times' in font_path.lower(),font_path
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width_mm:.6f}mm" height="{width_mm*H/W:.6f}mm" viewBox="0 0 {W} {H}">',
        '<title>Held-out RGB comparison: RPNG table_06, frame 1420</title>',
        '<desc>Actual F04 saved-map renders. Carve disabled. Same evaluation camera, matched physical training-render count. Identical unaltered crops; vector labels and connectors.</desc>',
        f'<rect width="{W}" height="{H}" fill="white"/>']
    sources={};layout=[]
    def embedded(im):
        stream=BytesIO();im.save(stream,format='PNG')
        return 'data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode()
    def img(uri,x,y,w,h):
        return f'<image x="{x:.4f}" y="{y:.4f}" width="{w:.4f}" height="{h:.4f}" preserveAspectRatio="xMidYMid meet" xlink:href="{uri}"/>'
    for j,(key,label) in enumerate([('baseline','VIGS-SLAM'),('ours','Ours'),('gt','Ground truth')]):
        path=source/f'{key}.png';sources[key]=sha(path)
        assert sources[key]==provenance['files'][path.name]
        im=Image.open(path).convert('RGB');assert im.size==(616,344)
        detail=im.crop(crop)
        # Verify exact correspondence to the previously inspected candidate crop.
        assert detail.tobytes()==Image.open(source/f'{key}_crop.png').convert('RGB').tobytes()
        x=outer+j*(panel_w+gap);scale=panel_w/im.width;image_h=im.height*scale
        rx=x+crop[0]*scale;ry=image_y+crop[1]*scale;rw=(crop[2]-crop[0])*scale;rh=(crop[3]-crop[1])*scale
        ix=x+2;iy=inset_y;ih=inset_w*detail.height/detail.width
        assert rx>ix+inset_w and ry+rh<iy
        parts.append(f'<text x="{x+panel_w/2}" y="55" text-anchor="middle" font-family="Times New Roman" font-size="52" fill="#111111">{escape(label)}</text>')
        parts.append(img(embedded(im),x,image_y,panel_w,image_h))
        # Source bottom corners -> inset top corners: two non-crossing leaders.
        # White under-stroke keeps thin amber lines visible on black print.
        path_d=f'M {rx:.4f},{ry+rh:.4f} L {ix:.4f},{iy:.4f} M {rx+rw:.4f},{ry+rh:.4f} L {ix+inset_w:.4f},{iy:.4f}'
        parts.append(f'<path d="{path_d}" fill="none" stroke="white" stroke-width="5" stroke-opacity="0.85" stroke-dasharray="10 7"/>')
        parts.append(f'<path d="{path_d}" fill="none" stroke="{amber}" stroke-width="3.1" stroke-dasharray="10 7"/>')
        parts.append(f'<rect x="{rx:.4f}" y="{ry:.4f}" width="{rw:.4f}" height="{rh:.4f}" fill="none" stroke="white" stroke-width="5" stroke-dasharray="10 7"/>')
        parts.append(f'<rect x="{rx:.4f}" y="{ry:.4f}" width="{rw:.4f}" height="{rh:.4f}" fill="none" stroke="{amber}" stroke-width="3.1" stroke-dasharray="10 7"/>')
        parts.append(f'<rect x="{ix-4}" y="{iy-4}" width="{inset_w+8}" height="{ih+8}" fill="white"/>')
        parts.append(img(embedded(detail),ix,iy,inset_w,ih))
        parts.append(f'<rect x="{ix}" y="{iy}" width="{inset_w}" height="{ih}" fill="none" stroke="{amber}" stroke-width="3.5"/>')
        layout.append({'method':key,'main_box':[x,image_y,panel_w,image_h],
            'roi_box':[rx,ry,rw,rh],'inset_box':[ix,iy,inset_w,ih]})
    parts.append('</svg>')
    svg=output/'rgb_comparison.svg';svg.write_text('\n'.join(parts)+'\n')
    pdf=pdf_dir/'rgb_comparison.pdf'
    subprocess.run(['inkscape',str(svg),'--export-type=pdf',f'--export-filename={pdf}'],check=True)
    # Preview the PDF, not a separate rendering path.
    subprocess.run(['pdftoppm','-singlefile','-scale-to','2400','-png',str(pdf),str(output/'rgb_comparison')],check=True)
    subprocess.run(['pdftoppm','-singlefile','-r','150','-png',str(pdf),str(output/'rgb_comparison_column_150dpi')],check=True)
    for key,digest in sources.items():assert sha(source/f'{key}.png')==digest
    write(output/'provenance.json',{'candidate':'F04','dataset':'rpng','scene':'table_06','frame_index':1420,
        'source_provenance':str(source/'provenance.json'),'source_png_sha256':sources,
        'crop_xyxy':crop,'crop_matches_candidate_exactly':True,'layout':layout,
        'width_mm':width_mm,'height_mm':width_mm*H/W,'font':font_path,
        'label_size_pt':52/W*width_mm/25.4*72,
        'physical_training_renders_each':provenance['physical_renders'],
        'baseline_psnr_full_image':provenance['baseline_psnr'],'ours_psnr_full_image':provenance['ours_psnr'],
        'carve_enabled':False,'postprocessing':'No sharpening, recoloring, denoising or generative edits. Identical display scaling only.',
        'pdf_sha256':sha(pdf),'svg_sha256':sha(svg)})
    # This is the asset path already consumed by the manuscript's Fig. 2 block.
    import shutil
    installed=WORK/'humanteck/HumanTeck_Song_s_intern/figure/rgb_comparison.pdf'
    shutil.copy2(pdf,installed)
    assert sha(installed)==sha(pdf)
    print('Publication figure:',pdf)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--scan',action='store_true');p.add_argument('--render',action='store_true');p.add_argument('--figure',action='store_true');a=p.parse_args()
    if a.scan:scan()
    if a.render:render_candidates()
    if a.figure:build_figure()
