#!/usr/bin/env python3
"""Fig3-style alternatives: real full-scene curves, three embedded inset pairs."""
import base64
import hashlib
import json
import math
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
RUNS=Path('/home/intern/gs_floaterLab/results/figure03_scene_search_20260921/rpng')
OUT=ROOT/'output'
OPTIONS=[('table_01',330,[800,1600,3000],(310,198,570,338)),
         ('table_06',1420,[800,1400,2600],(365,30,610,162))]


def build(scene,frame,steps,crop):
    src=RUNS/scene/'evaluation/curves.json'
    if not src.exists():return
    data=json.loads(src.read_text())
    curves={a:sorted([r for r in data['curves'] if r['arm']==a],key=lambda r:r['iteration']) for a in ['baseline','ours']}
    colors={'baseline':'#d86236','ours':'#008f93'}
    xmax=math.ceil(max(r['iteration'] for r in data['curves'])/200)*200
    xl,xr,yt,yb=130,1460,140,960
    def px(k):return xl+(xr-xl)*k/xmax
    def py(q):return yb-(yb-yt)*q/28
    mm=(180-20*25.4/72.27)/2
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{mm:.6f}mm" height="{mm*1100/1500:.6f}mm" viewBox="0 0 1500 1100">',
           f'<title>RPNG {scene}; fixed held-out full-trajectory PSNR; inset frame {frame}</title>',
           '<desc>Exploratory scene selection. Raw native Gaussian Adam checkpoints, same total render budget. Curves include coverage and pose corrections. Insets contain actual renders; no generated or enhanced pixels.</desc>',
           '<rect width="1500" height="1100" fill="white"/>']
    def text(x,y,s,size=40,anchor='start',color='#222',extra=''):
        parts.append(f'<text x="{x:.3f}" y="{y:.3f}" font-family="Times New Roman" font-size="{size}" text-anchor="{anchor}" fill="{color}" {extra}>{escape(s)}</text>')
    def line(x1,y1,x2,y2,color='#333',width=2,dash=''):
        parts.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
    text(130,52,'RPNG '+scene,43)
    line(665,39,730,39,colors['baseline'],5,'15 10');text(748,53,'VIGS-SLAM',42)
    line(1130,39,1195,39,colors['ours'],5);text(1213,53,'Ours',42)
    text(795,108,f'{data["heldout_count"]} held-out views; insets: upper baseline / lower ours',35,'middle','#555')
    for q in [0,5,10,15,20,25]:
        y=py(q);line(xl,y,xr,y,'#dddddd',1.4,'4 7');line(xl-8,y,xl,y);text(xl-20,y+13,str(q),40,'end')
    ticks=[0,1000,2000,3000] if xmax==3200 else [0,800,1600,2400,2800]
    for k in ticks:
        x=px(k);line(x,yt,x,yb,'#e5e5e5',1.3,'4 7');line(x,yb,x,yb+8);text(x,yb+48,f'{k/1000:g}',40,'middle')
    parts.append(f'<rect x="{xl}" y="{yt}" width="{xr-xl}" height="{yb-yt}" fill="none" stroke="#222" stroke-width="2.2"/>')
    text(795,1060,'Mapping iterations (×10³)',45,'middle')
    text(42,550,'Evaluation PSNR (dB) ↑',44,'middle',extra='transform="rotate(-90 42 550)"')
    for arm,rows in curves.items():
        points=' '.join(f'{px(r["iteration"]):.3f},{py(r["mean_psnr"]):.3f}' for r in rows)
        dash=' stroke-dasharray="15 10"' if arm=='baseline' else ''
        parts.append(f'<polyline points="{points}" fill="none" stroke="{colors[arm]}" stroke-width="5.2" stroke-linejoin="round"{dash}/>')
        for r in rows:parts.append(f'<circle cx="{px(r["iteration"]):.3f}" cy="{py(r["mean_psnr"]):.3f}" r="4" fill="{colors[arm]}"/>')
    target=curves['baseline'][-1]['mean_psnr']
    reached={a:next((r['iteration'] for r in rows if r['mean_psnr']>=target),None) for a,rows in curves.items()}
    if reached['ours'] is not None and reached['ours'] < reached['baseline']:
        xa,xb=px(reached['ours']),px(reached['baseline']);ay=py(26.0)
        line(xa,py(target),xr,py(target),'#999',1.6,'10 9')
        line(xa,py(target),xa,ay,'#777',1.5,'5 6');line(xb,py(target),xb,ay,'#777',1.5,'5 6')
        line(xa,ay,xb,ay,'#444',2)
        parts.append(f'<path d="M {xa} {ay} l 11 -6 v 12 Z M {xb} {ay} l -11 -6 v 12 Z" fill="#444"/>')
        text((xa+xb)/2,ay-14,'Same PSNR*',33,'middle')
    images=[]
    for step,x in zip(steps,[165,650,1135]):
        y=575;iw=300;x0,y0,x1,y1=crop;ih=iw*(y1-y0)/(x1-x0)
        text(x+iw/2,y+26,f'{step:,} iter.',40,'middle')
        for j,arm in enumerate(['baseline','ours']):
            iy=y+43+j*(ih+12)
            path=ROOT/f'candidates/scene_search/{scene}/frame_{frame:04d}/{arm}_{step:05d}.png'
            width,height=Image.open(path).size;s=iw/(x1-x0)
            assert 0<=x0<x1<=width and 0<=y0<y1<=height
            uri='data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode();clip=f'clip-{step}-{arm}'
            parts.append(f'<defs><clipPath id="{clip}"><rect x="{x}" y="{iy}" width="{iw}" height="{ih}"/></clipPath></defs>')
            parts.append(f'<g clip-path="url(#{clip})"><image x="{x-x0*s}" y="{iy-y0*s}" width="{width*s}" height="{height*s}" href="{uri}"/></g>')
            parts.append(f'<rect x="{x}" y="{iy}" width="{iw}" height="{ih}" fill="none" stroke="{colors[arm]}" stroke-width="3"/>')
            r=next(r for r in curves[arm] if r['iteration']==step)
            tx,ty=px(step),py(r['mean_psnr']);sx=x+iw/2+(-10 if arm=='baseline' else 10)
            line(sx,y-8,tx,ty,colors[arm],1.6,'7 7')
            parts.append(f'<circle cx="{tx}" cy="{ty}" r="7" fill="white" stroke="{colors[arm]}" stroke-width="3.5"/>')
            images.append({'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'crop':crop,'iteration':step,'arm':arm})
    parts.append('</svg>')
    stem=f'fig3_search_{scene}_frame{frame}';svg=OUT/f'{stem}.svg'
    svg.write_text('\n'.join(parts))
    subprocess.run(['inkscape',str(svg),'--export-type=png','--export-width=1800',f'--export-filename={OUT/(stem+".png")}'],check=True,capture_output=True)
    (OUT/f'{stem}_provenance.json').write_text(json.dumps({'scene':scene,'frame':frame,'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'images':images,'inset_steps':steps,'native_recipe_preserved':True,'no_curve_smoothing':True,'threshold_psnr':target,'first_sampled_iterations_at_or_above_threshold':reached,'arrow_note':'First saved checkpoint at or above baseline endpoint PSNR; not exact crossing or sustained attainment. No interpolation.','interpretation':'Exploratory full-system map quality, including coverage and pose changes; not a pure optimization-speed benchmark.'},indent=2)+'\n')
    print(svg)


if __name__=='__main__':
    for option in OPTIONS:build(*option)
