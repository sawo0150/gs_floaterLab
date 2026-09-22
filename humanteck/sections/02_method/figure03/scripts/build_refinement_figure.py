#!/usr/bin/env python3
"""Editable single-column figure from measured five-event refinement curves."""
import base64
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parent.parent
RUNS=Path('/home/intern/gs_floaterLab/results/figure03_refinement_20260921/aria301_305')
OUT=ROOT/'output';QA=OUT/'qa';PDF=OUT/'pdf'
STEM='fig3_refinement_frame1180'


def main():
    data=json.loads((RUNS/'evaluation/curves.json').read_text())
    curves={a:[r for r in data['mean_curves'] if r['arm']==a] for a in ['baseline','ours']}
    colors={'baseline':'#d86236','ours':'#008f93'}
    w,h=1500,1130;mm=(180-20*25.4/72.27)/2
    xl,xr,yt,yb=140,1450,175,980
    qs=[r['mean_psnr'] for r in data['mean_curves']]
    ymin=max(0,math.floor(min(qs))-1);ymax=math.ceil(max(qs))
    def px(k):return xl+(xr-xl)*k/120
    def py(q):return yb-(yb-yt)*(q-ymin)/(ymax-ymin)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{mm:.6f}mm" height="{mm*h/w:.6f}mm" viewBox="0 0 {w} {h}">',
           '<title>Aria 301_305: controlled refinement; representative frame 1180</title>',
           '<desc>Measured PSNR, equal mean over five fixed event cohorts. Each diagnostic iteration renders one view and makes one Gaussian Adam update. Current causal evaluation poses held fixed, no incoming observations. Own initial online maps. This is not a native end-to-end runtime benchmark.</desc>',
           f'<rect width="{w}" height="{h}" fill="white"/>']
    def text(x,y,s,size=40,anchor='start',color='#222',extra=''):
        parts.append(f'<text x="{x:.3f}" y="{y:.3f}" font-family="Times New Roman" font-size="{size}" text-anchor="{anchor}" fill="{color}" {extra}>{escape(s)}</text>')
    def line(x1,y1,x2,y2,color='#333',width=2,dash=''):
        parts.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
    text(140,51,'Aria 301_305',43)
    line(615,38,680,38,colors['baseline'],5,'15 10');text(698,51,'VIGS-SLAM*',41)
    line(1100,38,1165,38,colors['ours'],5);text(1183,51,'Ours',41)
    text(795,104,'Controlled refinement: fixed input and poses',38,'middle')
    text(795,150,'5 event cohorts; 1 rendered view per iteration',35,'middle','#555')
    tick=.5
    for n in range(int(math.ceil(ymin/tick)),int(ymax/tick)+1):
        q=n*tick
        y=py(q);line(xl,y,xr,y,'#dddddd',1.4,'4 7');line(xl-8,y,xl,y)
        text(xl-20,y+13,f'{q:g}',39,'end')
    for k in [0,30,60,90,120]:
        x=px(k);line(x,yt,x,yb,'#e7e7e7',1.2,'4 7');line(x,yb,x,yb+8)
        text(x,yb+47,str(k),40,'middle')
    parts.append(f'<rect x="{xl}" y="{yt}" width="{xr-xl}" height="{yb-yt}" fill="none" stroke="#222" stroke-width="2.2"/>')
    text(795,1083,'Additional mapping iterations',45,'middle')
    text(42,578,'Mean held-out PSNR (dB)',43,'middle',extra='transform="rotate(-90 42 578)"')
    for arm,rows in curves.items():
        points=' '.join(f'{px(r["additional_iteration"]):.3f},{py(r["mean_psnr"]):.3f}' for r in rows)
        dash=' stroke-dasharray="15 10"' if arm=='baseline' else ''
        parts.append(f'<polyline id="curve-{arm}" points="{points}" fill="none" stroke="{colors[arm]}" stroke-width="5.2" stroke-linejoin="round"{dash}/>')
        for row in rows:
            parts.append(f'<circle cx="{px(row["additional_iteration"]):.3f}" cy="{py(row["mean_psnr"]):.3f}" r="4.5" fill="{colors[arm]}"/>')
    text(795,548,'Frame 1180: upper VIGS-SLAM* / lower Ours',35,'middle','#555')
    crop=(0,195,464,445);iw=310;ih=iw*250/464;images=[]
    for k,x in [(0,170),(30,640),(120,1110)]:
        y=577
        text(x+iw/2,y+25,f'+{k} iter.',40,'middle')
        for j,arm in enumerate(['baseline','ours']):
            iy=y+43+j*(ih+12)
            src=ROOT/f'candidates/refinement_insets/frame_1180/{arm}_additional_{k:03d}.png'
            uri='data:image/png;base64,'+base64.b64encode(src.read_bytes()).decode()
            x0,y0,x1,y1=crop;s=iw/(x1-x0);clip=f'clip-{arm}-{k}'
            parts.append(f'<defs><clipPath id="{clip}"><rect x="{x}" y="{iy}" width="{iw}" height="{ih}"/></clipPath></defs>')
            parts.append(f'<g clip-path="url(#{clip})"><image x="{x-x0*s}" y="{iy-y0*s}" width="{464*s}" height="{464*s}" href="{uri}"/></g>')
            parts.append(f'<rect x="{x}" y="{iy}" width="{iw}" height="{ih}" fill="none" stroke="{colors[arm]}" stroke-width="3"/>')
            images.append({'arm':arm,'additional_iteration':k,'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'crop':crop})
    parts.append('</svg>')
    svg=OUT/f'{STEM}.svg';pdf=PDF/f'{STEM}.pdf'
    svg.write_text('\n'.join(parts))
    subprocess.run(['inkscape',str(svg),'--export-type=pdf',f'--export-filename={pdf}'],check=True,capture_output=True)
    subprocess.run(['pdftoppm','-png','-singlefile','-scale-to','1800',str(pdf),str(OUT/STEM)],check=True)
    subprocess.run(['pdftoppm','-png','-singlefile','-r','200',str(pdf),str(QA/(STEM+'_column_200dpi'))],check=True)
    provenance={'curve_source':str(RUNS/'evaluation/curves.json'),'curve_sha256':hashlib.sha256((RUNS/'evaluation/curves.json').read_bytes()).hexdigest(),
                'images':images,'axis_range':[ymin,ymax],'width_mm':mm,'height_mm':mm*h/w,
                'smoothing':False,'aggregation':data['aggregation'],'baseline_asterisk':'Native vanilla map normalized with max_viewpoints=1; controlled diagnostic, not the original native end-to-end run.'}
    (OUT/f'{STEM}_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    dest=ROOT/'analysis/refinement_curves';dest.mkdir(exist_ok=True)
    for name in ['curves.json','per_event_curves.csv','mean_curves.csv']:
        shutil.copy2(RUNS/'evaluation'/name,dest/name)
    print(svg,flush=True)


if __name__=='__main__':
    main()
