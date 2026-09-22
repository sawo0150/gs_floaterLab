#!/usr/bin/env python3
"""Review actual saved renders with identical crops and a full GT locator."""
import base64,json,subprocess,hashlib
from pathlib import Path
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parent.parent
SRC=ROOT/'candidates/scene_search/table_06'; OUT=ROOT/'candidates/table06_review_v2';OUT.mkdir(exist_ok=True)
CROPS={1420:(440,40,564,164)}
EVAL=Path('/home/intern/gs_floaterLab/results/figure03_scene_search_20260921/rpng/table_06/evaluation')
CHECKS=[]
for k in [800,1400,2600]:
 for arm in ['baseline','ours']:
  result=json.loads((EVAL/f'{arm}_{k:05d}.json').read_text())
  row=next(v for v in result['per_view'] if v['frame_index']==1420)
  CHECKS.append({'frame':1420,'arm':arm,'iteration':k,'psnr':row['psnr']})
COLORS={'baseline':'#d86236','ours':'#008f93','gt':'#777777'}

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
 p=start(1290,1515);text(p,25,32,f'Frame {f}: same crop as Fig. 2, at three checkpoints',28)
 locator(p,f,25,58);text(p,370,94,'Magenta box: crop location in GT')
 text(p,370,133,'PSNR labels: full frame, not crop. Same pixels, no enhancement.',21)
 for x,a in zip([150,530,910],['baseline','ours','gt']):text(p,x,256,{'baseline':'VIGS-SLAM','ours':'Ours','gt':'GT'}[a])
 for j,k in enumerate([800,1400,2600]):
  y=275+j*415;text(p,20,y+85,f'{k:,}',22);text(p,20,y+112,'iter.',20)
  for x,a in zip([150,530,910],['baseline','ours','gt']):
   name='gt.png' if a=='gt' else f'{a}_{k:05d}.png';draw(p,SRC/f'frame_{f:04d}'/name,x,y,360,360,c,COLORS[a])
   if a!='gt':text(p,x,y+387,f'{val(f,a,k):.2f} dB',20)
  text(p,910,y+387,f'Ours - baseline: {val(f,"ours",k)-val(f,"baseline",k):+.2f} dB',20)
 export(p,f'frame_{f:04d}_three_stages')

old=json.loads((ROOT/'output/fig3_search_table_06_frame1420_provenance.json').read_text())
for im in old['images']:
 assert hashlib.sha256(Path(im['source']).read_bytes()).hexdigest()==im['sha256']
provenance={'frame':1420,'crop':CROPS[1420],'crop_matches_figure02':True,'steps':[800,1400,2600],'metrics':CHECKS,'source_images':[{k:v for k,v in im.items() if k!='crop'} for im in old['images']],'processing':'Original checkpoint renders. SVG crop and uniform scale only. All three rows use identical GT. PSNR labels are full-frame values.'}
(OUT/'frame_1420_three_stages_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(OUT/'frame_1420_three_stages.png')
