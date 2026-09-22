#!/usr/bin/env python3
"""Build three editable SVG figures, export PDFs, render PDFs for visual QA."""
import base64
import hashlib
import json
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

WORK=Path('/home/intern/gs_floaterLab')
ROOT=Path(__file__).resolve().parent.parent
EVAL=WORK/'results/figure03_convergence_20260921/aria301_305/evaluation'
DATA=json.loads((EVAL/'curves.json').read_text())
OUT=ROOT/'output'
PDF=OUT/'pdf'
QA=OUT/'qa'
for p in (OUT,PDF,QA): p.mkdir(parents=True,exist_ok=True)
COLORS={'baseline':'#d86236','ours':'#008f93'}
CURVES={a:sorted([r for r in DATA['curves'] if r['arm']==a],key=lambda r:r['iteration']) for a in COLORS}
W,H=1500,1100
WIDTH_MM=(180-20*25.4/72.27)/2
XL,XR,YT,YB=130,1460,140,960
XMAX,YMAX=1400,28
def px(k): return XL+(XR-XL)*k/XMAX
def py(q): return YB-(YB-YT)*q/YMAX
def cross(rows,q):
    for i,r in enumerate(rows):
        if r['mean_psnr']>=q:
            if i==0: return {'estimate':r['iteration'],'interval':[None,r['iteration']]}
            a=rows[i-1]
            k=a['iteration']+(r['iteration']-a['iteration'])*(q-a['mean_psnr'])/(r['mean_psnr']-a['mean_psnr'])
            return {'estimate':k,'interval':[a['iteration'],r['iteration']]}
    return None
TARGET=next(r['mean_psnr'] for r in CURVES['baseline'] if r['final'])
CROSS={a:cross(rows,TARGET) for a,rows in CURVES.items()}
VARIANTS=[('A',1180,(0,195,464,445)),('B',1220,(0,205,464,455)),('C',980,(0,205,464,455))]


def build(version,frame,crop):
    stem=f'fig3_{version}_frame{frame}'
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="{WIDTH_MM:.6f}mm" height="{WIDTH_MM*H/W:.6f}mm" viewBox="0 0 {W} {H}">',
           f'<title>Aria 301_305 convergence; inset frame {frame}</title>',
           '<desc>Measured mean PSNR on 539 fixed held-out views. Unsmoothened checkpoint curves. Insets show real intermediate maps at 600, 1000, 1300 Gaussian optimizer steps. Upper orange: VIGS-SLAM. Lower teal: Ours. Frozen causal tracker mapping-only comparison; late pose correction contributes to the jump.</desc>',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#333"/></marker></defs>',
           '<rect width="1500" height="1100" fill="white"/>']
    def line(x1,y1,x2,y2,color='#333',width=2,dash=None,extra=''):
        parts.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+f' {extra}/>')
    def text(x,y,value,size=42,anchor='start',color='#222',extra=''):
        parts.append(f'<text x="{x:.3f}" y="{y:.3f}" font-family="Times New Roman" font-size="{size}" text-anchor="{anchor}" fill="{color}" {extra}>{escape(value)}</text>')
    text(130,53,'Aria 301_305',44)
    line(485,43,555,43,COLORS['baseline'],5,'15 10');text(570,56,'VIGS-SLAM',42)
    line(850,43,920,43,COLORS['ours'],5);text(935,56,'Ours',42)
    parts.append('<rect x="1110" y="26" width="35" height="32" fill="#e8e8e8"/>')
    text(1160,56,'Pose correction',38)
    text(795,108,'Insets: upper VIGS-SLAM / lower Ours',36,'middle','#555')

    # The final pose-correction event is reached at different native step counts.
    parts.append(f'<rect x="{px(1295):.3f}" y="{YT}" width="{px(1347)-px(1295):.3f}" height="{YB-YT}" fill="#ededed"/>')
    for q in [0,5,10,15,20,25]:
        y=py(q);line(XL,y,XR,y,'#dddddd',1.4,'4 7');line(XL-9,y,XL,y,width=2)
        text(XL-20,y+14,str(q),40,'end')
    for k in [0,400,800,1200,1400]:
        x=px(k);line(x,YT,x,YB,'#e4e4e4',1.4,'4 7');line(x,YB,x,YB+10,width=2)
        text(x,YB+50,f'{k/1000:g}',40,'middle')
    parts.append(f'<rect x="{XL}" y="{YT}" width="{XR-XL}" height="{YB-YT}" fill="none" stroke="#222" stroke-width="2.3"/>')
    text((XL+XR)/2,1060,'Mapping iterations (×10³)',45,'middle')
    text(42,(YT+YB)/2,'Evaluation PSNR (dB) ↑',44,'middle',extra=f'transform="rotate(-90 42 {(YT+YB)/2})"')
    for arm,rows in CURVES.items():
        points=' '.join(f'{px(r["iteration"]):.3f},{py(r["mean_psnr"]):.3f}' for r in rows)
        dash=' stroke-dasharray="15 10"' if arm=='baseline' else ''
        parts.append(f'<polyline id="curve-{arm}" points="{points}" fill="none" stroke="{COLORS[arm]}" stroke-width="5.2" stroke-linejoin="round"{dash}/>')
        for r in rows:
            parts.append(f'<circle cx="{px(r["iteration"]):.3f}" cy="{py(r["mean_psnr"]):.3f}" r="3.5" fill="{COLORS[arm]}"/>')

    # Descriptive endpoint matching, without turning the event-related jump into a speedup claim.
    qy=py(TARGET)
    line(px(560),qy,XR,qy,'#888',2,'12 9')
    text(px(570),qy-14,f'Baseline final: {TARGET:.2f} dB',36,color='#555')
    xa,xb=(px(CROSS[a]['estimate']) for a in ['ours','baseline'])
    ay=py(26.2)
    line(xa,qy,xa,ay,'#777',1.5,'5 6');line(xb,qy,xb,ay,'#777',1.5,'5 6')
    line(xa,ay,xb,ay,'#333',2.2,extra='marker-start="url(#arrow)" marker-end="url(#arrow)"')
    text((xa+xb)/2-85,ay-18,'Same PSNR',36,'end')

    images=[]
    placements=[(600,155,150),(1000,650,555),(1300,1120,555)]
    # Crop width 320; each shared ROI is 464x250, matching the reviewed aspect ratio.
    iw=320;ih=iw*(crop[3]-crop[1])/(crop[2]-crop[0])
    for step,x,y in placements:
        text(x+iw/2,y+27,f'{step:,} iter.',42,'middle')
        for j,arm in enumerate(['baseline','ours']):
            iy=y+45+j*(ih+12)
            path=ROOT/f'candidates/convergence_insets/frame_{frame:04d}/{arm}_iter_{step:05d}.png'
            uri='data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
            x0,y0,x1,y1=crop;s=iw/(x1-x0)
            clip=f'crop-{step}-{arm}'
            parts.append(f'<defs><clipPath id="{clip}" clipPathUnits="userSpaceOnUse"><rect x="{x}" y="{iy}" width="{iw}" height="{ih}"/></clipPath></defs>')
            parts.append(f'<g clip-path="url(#{clip})"><image x="{x-x0*s}" y="{iy-y0*s}" width="{464*s}" height="{464*s}" href="{uri}"/></g>')
            parts.append(f'<rect x="{x}" y="{iy}" width="{iw}" height="{ih}" fill="none" stroke="{COLORS[arm]}" stroke-width="3"/>')
            row=next(r for r in CURVES[arm] if r['iteration']==step)
            tx,ty=px(step),py(row['mean_psnr'])
            if step==600:
                sx,sy=x+iw+6,iy+ih/2
                d=f'M {sx} {sy} L {tx-55} {sy} L {tx} {ty}'
            else:
                # Connections terminate outside the header; colors identify upper/lower crops.
                sx,sy=x+iw/2+(-12 if arm=='baseline' else 12),y-7
                d=f'M {sx} {sy} L {tx} {ty}'
            parts.append(f'<path d="{d}" fill="none" stroke="{COLORS[arm]}" stroke-width="2" stroke-dasharray="7 6" opacity="0.75"/>')
            parts.append(f'<circle cx="{tx}" cy="{ty}" r="8" fill="white" stroke="{COLORS[arm]}" stroke-width="4"/>')
            images.append({'arm':arm,'iteration':step,'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'crop':crop})
    parts.append('</svg>')
    svg=OUT/f'{stem}.svg';pdf=PDF/f'{stem}.pdf'
    svg.write_text('\n'.join(parts))
    subprocess.run(['inkscape',str(svg),'--export-type=pdf',f'--export-filename={pdf}'],check=True,capture_output=True)
    subprocess.run(['pdftoppm','-png','-singlefile','-scale-to','1800',str(pdf),str(OUT/stem)],check=True)
    subprocess.run(['pdftoppm','-png','-singlefile','-r','200',str(pdf),str(QA/(stem+'_column_200dpi'))],check=True)
    record={'version':version,'frame_index':frame,'curve_source':str(EVAL/'curves.json'),
            'curve_sha256':hashlib.sha256((EVAL/'curves.json').read_bytes()).hexdigest(),
            'inset_iterations':[600,1000,1300],'images':images,'width_mm':WIDTH_MM,'height_mm':WIDTH_MM*H/W,
            'target_psnr':TARGET,'crossings_linear_interpolation':CROSS,
            'pose_correction_bands':{'ours':[1295,1317],'baseline':[1327,1347]},
            'postprocessing':'Unmodified measured polylines; identical actual-image crops; no enhancement or generated content'}
    (OUT/f'{stem}_provenance.json').write_text(json.dumps(record,indent=2)+'\n')
    print(stem,'complete',flush=True)


if __name__=='__main__':
    for version,frame,crop in VARIANTS:
        build(version,frame,crop)
