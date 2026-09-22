#!/usr/bin/env python3
"""Review actual saved renders with identical crops and a full GT locator."""
import base64,json,subprocess,hashlib
from pathlib import Path
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parent.parent
SRC=ROOT/'candidates/table06_revision'; OUT=ROOT/'candidates/table06_review_v2';OUT.mkdir(exist_ok=True)
CROPS={1110:(340,65,500,145),685:(140,90,300,170),950:(40,160,200,240),2370:(415,140,575,220),905:(190,130,350,210),1630:(160,90,320,170),355:(230,100,390,180),205:(260,110,420,190)}
CHECKS=json.loads((SRC/'render_checks.json').read_text());COLORS={'baseline':'#d86236','ours':'#008f93','gt':'#777777'}
def start(w,h):return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/>']
def text(p,x,y,s,size=23):p.append(f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="{size}" fill="#222">{escape(s)}</text>')
def draw(p,path,x,y,w,h,crop=None,color='#777'):
 b64=base64.b64encode(path.read_bytes()).decode(); cid=f'c{len(p)}'
 if crop is None:crop=(0,0,616,344)
 l,t,r,b=crop;scale=w/(r-l);assert abs(h/(b-t)-scale)<1e-8
 p.append(f'<defs><clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath></defs><g clip-path="url(#{cid})"><image x="{x-l*scale}" y="{y-t*scale}" width="{616*scale}" height="{344*scale}" href="data:image/png;base64,{b64}"/></g><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{color}" stroke-width="2"/>')
def locator(p,f,x,y):
 draw(p,SRC/f'frame_{f:04d}/gt.png',x,y,308,172)
 l,t,r,b=CROPS[f];p.append(f'<rect x="{x+l/2}" y="{y+t/2}" width="{(r-l)/2}" height="{(b-t)/2}" fill="none" stroke="#dc2690" stroke-width="2"/>')
def val(f,a,k):return next(d['psnr'] for d in CHECKS if d['frame']==f and d['arm']==a and d['iteration']==k)
def export(p,name):
 path=OUT/f'{name}.svg';path.write_text('\n'.join(p+['</svg>']))
 subprocess.run(['inkscape',str(path),'--export-type=png',f'--export-filename={OUT/name}.png'],check=True,capture_output=True)
for f,c in CROPS.items():
 p=start(1290,985);text(p,25,32,f'Frame {f}: identical crop at three mapping checkpoints',28)
 locator(p,f,25,58);text(p,370,94,'Magenta box: crop location in GT')
 text(p,370,133,'PSNR labels: full frame, not crop. Same pixels, no enhancement.',21)
 for x,a in zip([150,530,910],['baseline','ours','gt']):text(p,x,256,{'baseline':'VIGS-SLAM','ours':'Ours','gt':'GT'}[a])
 for j,k in enumerate([800,1400,2600]):
  y=275+j*235;text(p,20,y+85,f'{k:,}',22);text(p,20,y+112,'iter.',20)
  for x,a in zip([150,530,910],['baseline','ours','gt']):
   name='gt.png' if a=='gt' else f'{a}_{k:05d}.png';draw(p,SRC/f'frame_{f:04d}'/name,x,y,360,180,c,COLORS[a])
   if a!='gt':text(p,x,y+207,f'{val(f,a,k):.2f} dB',20)
  text(p,910,y+207,f'Ours - baseline: {val(f,"ours",k)-val(f,"baseline",k):+.2f} dB',20)
 export(p,f'frame_{f:04d}_three_stages')
for page,frames in enumerate([list(CROPS)[:4],list(CROPS)[4:]],1):
 p=start(1300,1080);text(p,20,32,f'Candidate review {page}: 2,600 iterations',28)
 text(p,20,63,'GT context (box = crop)');text(p,345,63,'VIGS-SLAM');text(p,660,63,'Ours');text(p,975,63,'GT crop')
 for j,f in enumerate(frames):
  y=106+j*242;text(p,20,y-12,f'Frame {f}  |  full-frame PSNR gap: {val(f,"ours",2600)-val(f,"baseline",2600):+.2f} dB',21)
  locator(p,f,20,y)
  for x,a in zip([345,660,975],['baseline','ours','gt']):
   name='gt.png' if a=='gt' else f'{a}_02600.png';draw(p,SRC/f'frame_{f:04d}'/name,x,y,300,150,CROPS[f],COLORS[a])
 export(p,f'candidate_board_{page}')
(OUT/'provenance.json').write_text(json.dumps({'crops':CROPS,'steps':[800,1400,2600],'source_checks':str(SRC/'render_checks.json'),'source_checks_sha256':hashlib.sha256((SRC/'render_checks.json').read_bytes()).hexdigest(),'processing':'SVG crop and uniform scale only; same crop for both arms and all stages; all GT columns are identical.'},indent=2)+'\n')
print(OUT)
