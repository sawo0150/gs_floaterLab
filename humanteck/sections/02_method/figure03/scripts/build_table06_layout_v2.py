#!/usr/bin/env python3
"""Fig3 v2: bottom-centered legend, no scene title or threshold annotation."""
import base64
import hashlib
import json
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parent.parent
SOURCE=Path('/home/intern/gs_floaterLab/results/figure03_scene_search_20260921/rpng/table_06/evaluation/curves.json')
OUT=ROOT/'output';STEM='fig3_table06_compact_v2_frame355'
W,H=1500,800
WIDTH_MM=(180-20*25.4/72.27)/2
XL,XR,YT,YB=125,1470,25,625
YMIN,YMAX=14.,25.5
COLORS={'baseline':'#d86236','ours':'#008f93'}


def main():
    data=json.loads(SOURCE.read_text())
    curves={a:sorted([r for r in data['curves'] if r['arm']==a],key=lambda r:r['iteration']) for a in COLORS}
    def px(k):return XL+(XR-XL)*k/2800
    def py(q):return YB-(YB-YT)*(q-YMIN)/(YMAX-YMIN)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="{WIDTH_MM:.6f}mm" height="{WIDTH_MM*H/W:.6f}mm" viewBox="0 0 {W} {H}">',
           '<title>RPNG table_06; compact Fig3 with held-out frame 355</title>',
           '<desc>Original 555-view mean PSNR, unchanged values, shared linear y-axis 14 to 25.5 dB. All 28 checkpoints shown. Insets use a different poster face from Fig2, frame355 at 800/1400/2600 steps. No threshold or crossing annotation: native streaming curves fluctuate.</desc>',
           f'<rect width="{W}" height="{H}" fill="white"/>']
    def text(x,y,value,size=38,anchor='start',color='#222',extra=''):
        parts.append(f'<text x="{x:.3f}" y="{y:.3f}" font-family="Times New Roman" font-size="{size}" text-anchor="{anchor}" fill="{color}" {extra}>{escape(value)}</text>')
    def line(x1,y1,x2,y2,color='#333',width=1.8,dash='',extra=''):
        parts.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+f' {extra}/>')
    # Offset from Inkscape's measured Times New Roman text bounds, centered on page.
    parts.append('<g id="legend" transform="translate(18.76 0)">')
    line(425,765,490,765,COLORS['baseline'],4.6,'14 9')
    text(620,779,'VIGS-SLAM',40,'middle')
    line(845,765,910,765,COLORS['ours'],4.6)
    text(1000,779,'Ours',40,'middle')
    parts.append('</g>')
    for q in [15,17,19,21,23,25]:
        y=py(q);line(XL,y,XR,y,'#dddddd',1.25,'4 7');line(XL-8,y,XL,y)
        text(XL-17,y+12,str(q),37,'end')
    for k in [0,800,1600,2400,2800]:
        x=px(k);line(x,YT,x,YB,'#e7e7e7',1.1,'4 7');line(x,YB,x,YB+8)
        text(x,YB+43,f'{k/1000:g}',38,'middle')
    parts.append(f'<rect x="{XL}" y="{YT}" width="{XR-XL}" height="{YB-YT}" fill="none" stroke="#333" stroke-width="1.9"/>')
    text(795,710,'Mapping iterations (×10³)',42,'middle')
    text(40,(YT+YB)/2,'Evaluation PSNR (dB) ↑',39,'middle',extra=f'transform="rotate(-90 40 {(YT+YB)/2})"')
    for arm,rows in curves.items():
        assert all(YMIN<r['mean_psnr']<YMAX for r in rows)
        points=' '.join(f'{px(r["iteration"]):.3f},{py(r["mean_psnr"]):.3f}' for r in rows)
        dash=' stroke-dasharray="14 9"' if arm=='baseline' else ''
        parts.append(f'<polyline id="curve-{arm}" points="{points}" fill="none" stroke="{COLORS[arm]}" stroke-width="4.6" stroke-linejoin="round"{dash}/>')
        for r in rows:parts.append(f'<circle cx="{px(r["iteration"]):.3f}" cy="{py(r["mean_psnr"]):.3f}" r="3.2" fill="{COLORS[arm]}"/>')
    crop=(230,100,390,180);images=[]
    for k,x in zip([800,1400,2600],[510,825,1140]):
        y=279;iw=280;ih=140
        text(x+iw/2,y+22,f'{k:,} iter.',35,'middle')
        for j,arm in enumerate(['baseline','ours']):
            iy=y+39+j*(ih+9)
            src=ROOT/f'candidates/table06_revision/frame_0355/{arm}_{k:05d}.png'
            uri='data:image/png;base64,'+base64.b64encode(src.read_bytes()).decode();scale=iw/160;clip=f'crop-{arm}-{k}'
            parts.append(f'<defs><clipPath id="{clip}"><rect x="{x}" y="{iy}" width="{iw}" height="{ih}"/></clipPath></defs>')
            parts.append(f'<g clip-path="url(#{clip})"><image x="{x-230*scale}" y="{iy-100*scale}" width="{616*scale}" height="{344*scale}" href="{uri}"/></g>')
            parts.append(f'<rect x="{x}" y="{iy}" width="{iw}" height="{ih}" fill="none" stroke="{COLORS[arm]}" stroke-width="2.5"/>')
            row=next(r for r in curves[arm] if r['iteration']==k);tx,ty=px(k),py(row['mean_psnr'])
            line(x+iw/2+(-7 if arm=='baseline' else 7),y-11,tx,ty,COLORS[arm],1.3,'5 6',extra='opacity="0.65"')
            parts.append(f'<circle cx="{tx}" cy="{ty}" r="5.8" fill="white" stroke="{COLORS[arm]}" stroke-width="2.8"/>')
            images.append({'arm':arm,'iteration':k,'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'crop':crop})
    parts.append('</svg>')
    svg=OUT/f'{STEM}.svg';pdf=OUT/'pdf'/f'{STEM}.pdf';svg.write_text('\n'.join(parts))
    subprocess.run(['inkscape',str(svg),'--export-type=pdf',f'--export-filename={pdf}'],check=True,capture_output=True)
    subprocess.run(['pdftoppm','-png','-singlefile','-scale-to','2000',str(pdf),str(OUT/STEM)],check=True)
    subprocess.run(['pdftoppm','-png','-singlefile','-r','200',str(pdf),str(OUT/'qa'/f'{STEM}_column_200dpi')],check=True)
    provenance={'curve_source':str(SOURCE),'curve_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'curve_points':28,'width_mm':WIDTH_MM,'height_mm':WIDTH_MM*H/W,'old_height_mm':WIDTH_MM*1100/1500,'height_reduction_fraction':1-H/1100,'y_axis':[YMIN,YMAX],'frame':355,'images':images,'legend':'bottom centered','annotation':'none','interpretation':'All 28 raw means retained. Baseline-final crossing removed because first attainment is not convergence for fluctuating streaming curves. Frame355 is provisional pending candidate review.'}
    (OUT/f'{STEM}_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps({k:v for k,v in provenance.items() if k not in ['images']},indent=2))


if __name__=='__main__':main()
