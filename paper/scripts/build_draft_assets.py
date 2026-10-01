#!/usr/bin/env python3
"""Build explicitly marked layout drafts; never load or fabricate experiment results.

Run with a Python environment containing numpy, matplotlib, pillow, reportlab.
AI images were made with built-in image_gen; prompts are kept in figures/.
Copies and PDF wrappers preserve the original generated and HumanTech images.
"""
from pathlib import Path
import json, shutil, hashlib, csv, re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

P=Path(__file__).resolve().parents[1]; R=P.parent
LAT=P/'latex'; (LAT/'figs/draft').mkdir(parents=True,exist_ok=True)
(LAT/'fig').mkdir(exist_ok=True); (LAT/'tab').mkdir(exist_ok=True)
BLUE='#0057FF'; BLACK='#252525'; ORANGE='#D57C2B'; GRAY='#6B7280'
plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','DejaVu Serif'],'font.size':8,'axes.titlesize':8.5,'axes.labelsize':8,'legend.fontsize':7,'xtick.labelsize':7,'ytick.labelsize':7,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':0.2,'lines.linewidth':1.5})
FIGS={
 'F1':('figure01_teaser','fig:teaser'), 'F2':('figure02_system_overview','fig:overview'),
 'F3':('figure03_photometric_convergence','fig:photometric_convergence'),
 'F4':('figure04_new_region_convergence','fig:new_region'),
 'F5':('figure05_rendering_comparison','fig:rgb_comparison'),
 'F6':('figure06_geometry_comparison','fig:carve'),
 'F7':('figure07_geometry_convergence','fig:geometry_convergence'),
 'F9':('figure09_sampling_convergence','fig:sampling_convergence'),
 'F11':('figure11_equal_time_online','fig:equal_time'),
 'F12':('figure12_tracking_mapping_capacity','fig:tracking_capacity')}
CAP={
 'F1':r'\textbf{AI-generated teaser mockup.} Fictional appearance and solid-ellipsoid comparisons for online Gaussian mapping.',
 'F2':r'Overview reused from HumanTech. View-set growth, image selection, and depth-based supervision refine a shared Gaussian map. \textbf{Draft reuse:} reconcile labels with the final implementation.',
 'F3':r"Historical HumanTech photometric convergence on RPNG \texttt{table\_06}. $^{*}$First saved checkpoints reaching the baseline's peak: 1,400 iterations (ours) versus 2,400 (baseline). Pending replacement with latest measurements.",
 'F4':r'\textbf{Dummy data.} New-region appearance (top) and depth error (bottom) from the first observation of a region.',
 'F5':r'\textbf{AI-generated mockup.} RGB comparison layout with full views and enlarged regions. All images and method differences are fictional.',
 'F6':r'\textbf{AI-generated mockup.} Depth-like images and solid ellipsoid cutaways for geometry off/on/reference. Not measured results.',
 'F7':r'\textbf{Dummy data.} Free-space error (top) and surface completeness (bottom) against completed training renders.',
 'F9':r'\textbf{Dummy data.} Sampling convergence at 15/30/60 updates per keyframe interval. Sampler labels await reconciliation with the measured replay implementation.',
 'F11':r'\textbf{Dummy data.} Held-out quality (top) and completed renders (bottom) with concurrent tracking under 1$\times$/1.5$\times$ input-time allowances.',
 'F12':r'\textbf{Dummy data.} Tracking load and keyframe arrivals (a), mapping renders per keyframe (b), and their relationship (c). Not measured hardware capacity.'}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def current_note(cur,id,kind):
 (cur/'README.md').write_text(f'# {id} current — 레이아웃 초안\n\n유형: **{kind}**. 최종 논문 결과가 아닙니다. `figure.pdf`, `figure.png`, `caption.md`, `provenance.json`을 함께 확인합니다. 생성: `paper/scripts/build_draft_assets.py`.\n')

def finish(id,meta):
 folder,label=FIGS[id];cur=P/'figures'/folder/'current'
 (cur/'caption.md').write_text(CAP[id]+'\n')
 meta.update({'asset_id':id,'stage':'layout_draft','caption':CAP[id],'pdf_sha256':sha(cur/'figure.pdf')})
 (cur/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
 current_note(cur,id,meta['kind'])
 shutil.copy2(cur/'figure.pdf',LAT/'figs/draft'/f'{id.lower()}.pdf')
 # Only the teaser and system overview may span both manuscript columns.
 env='figure*' if id in ['F1','F2'] else 'figure'
 meta['manuscript_width']='two_columns' if env=='figure*' else 'one_column'
 (cur/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
 tex='\\begin{'+env+'}[tbp]\n  \\centering\n  \\includegraphics[width=\\linewidth]{figs/draft/'+id.lower()+'.pdf}\n  \\caption{'+CAP[id]+'}\n  \\label{'+label+'}\n\\end{'+env+'}\n'
 (LAT/'fig'/f'{id.lower()}_draft.tex').write_text(tex)

def raster_pdf(src,dst):
 im=Image.open(src);w,h=im.size;width=510;height=width*h/w
 c=canvas.Canvas(str(dst),pagesize=(width,height));c.drawImage(ImageReader(im),0,0,width=width,height=height);c.save()

# The generated images already carry draft markers. Copy without editing.
prompts=json.loads((P/'figures/imagegen_prompts_2026-10-01.json').read_text())
for row in prompts:
 id=row['id'];cur=P/'figures'/FIGS[id][0]/'current'
 src=Path(re.search(r'as (/[^\s]+\.png)',row['output_hint']).group(1))
 local=P/'figures'/FIGS[id][0]/'candidates/ai_mockup_2026-10-01.png'
 if not local.exists():shutil.copy2(src,local)
 shutil.copy2(local,cur/'figure.png');raster_pdf(local,cur/'figure.pdf')
 finish(id,{'kind':'ai_generated_mockup','experimental_evidence':False,'generator':'built-in image_gen','prompt':row['prompt'],'original_file':str(src),'local_source':str(local.relative_to(R)),'image_sha256':sha(local)})
# HumanTech native vector figures are copied without altering source values.
for id,srcbase in [('F2',R/'humanteck/sections/02_method/figure01/production/current/overview'),('F3',R/'humanteck/sections/02_method/figure03/current/fig3')]:
 cur=P/'figures'/FIGS[id][0]/'current'
 for ext in ['pdf','png','svg']:
  src=srcbase.with_suffix('.'+ext)
  if src.exists():shutil.copy2(src,cur/f'figure.{ext}')
 finish(id,{'kind':'humanteck_reused_overview' if id=='F2' else 'humanteck_historical_convergence','new_experiment':False,'source':str(srcbase.relative_to(R)),'source_pdf_sha256':sha(srcbase.with_suffix('.pdf'))})

def graph_finish(id,fig,data):
 cur=P/'figures'/FIGS[id][0]/'current'
 fig.suptitle('DRAFT - DUMMY DATA\nNot experimental results',fontsize=8,color='#A5382D',fontweight='bold',y=1.0)
 fig.tight_layout(rect=(0,0.015,1,0.90));
 for ext in ['pdf','png','svg']:
  fig.savefig(cur/f'figure.{ext}',dpi=190,bbox_inches='tight',facecolor='white')
 plt.close(fig)
 dfile=P/'figures'/FIGS[id][0]/'analysis/dummy_data.json'
 dfile.write_text(json.dumps({'synthetic':True,'experimental_evidence':False,'data':data},indent=2)+'\n')
 finish(id,{'kind':'dummy_graph','synthetic':True,'experimental_evidence':False,'data_file':str(dfile.relative_to(R)),'builder':'paper/scripts/build_draft_assets.py'})
def pair(ax,x,b,o,xlabel,ylabel,title):
 ax.plot(x,b,color=BLACK,label='VIGS-SLAM');ax.plot(x,o,color=BLUE,label='Ours')
 ax.set(xlabel=xlabel,ylabel=ylabel,title=title);ax.legend(frameon=False,loc='best')
def serial(x):return np.asarray(x).tolist()
# New-region appearance and geometry example.
x=np.linspace(0,4,21);b=17+8*(1-np.exp(-x/1.9));o=17+9*(1-np.exp(-x/1.15));bd=9*np.exp(-x/1.8)+2;od=9*np.exp(-x/0.85)+1.7
fig,axes=plt.subplots(2,1,figsize=(3.35,3.35),sharex=True);pair(axes[0],x,b,o,'','ROI PSNR (dB)','(a) Appearance');pair(axes[1],x,bd,od,'Seconds after first observation','Depth error (cm)','(b) Geometry')
graph_finish('F4',fig,{'seconds':serial(x),'baseline_psnr':serial(b),'ours_psnr':serial(o),'baseline_depth_error':serial(bd),'ours_depth_error':serial(od)})
# Geometry convergence, both error and coverage.
x=np.arange(0,6001,300);b=30*np.exp(-x/2200)+7;o=30*np.exp(-x/1200)+4;bc=45+40*(1-np.exp(-x/2200));oc=45+44*(1-np.exp(-x/1700))
fig,axes=plt.subplots(2,1,figsize=(3.35,3.35),sharex=True);pair(axes[0],x,b,o,'','Free-space error (%)','(a) Free-space consistency');pair(axes[1],x,bc,oc,'Completed training renders','Completeness (%)','(b) Surface preservation')
graph_finish('F7',fig,{'renders':serial(x),'baseline_free_error':serial(b),'ours_free_error':serial(o),'baseline_completeness':serial(bc),'ours_completeness':serial(oc)})
# Same scene, three independent synthetic budget arms.
fig,axes=plt.subplots(3,1,figsize=(3.35,4.0));data={}
for ax,budget in zip(axes,[15,30,60]):
 x=np.linspace(0,budget*100,25);b=16+(7+budget/40)*(1-np.exp(-x/(budget*43)));o=16+(7.3+budget/40)*(1-np.exp(-x/(budget*36)))
 ax.plot(x,b,color=BLACK,label='RR');ax.plot(x,o,color=BLUE,label='ERCB/ERVS (draft)')
 ax.set(xlabel='' if budget!=60 else 'Completed optimizer steps',ylabel='PSNR (dB)',title=f'{budget} updates / KF interval')
 ax.ticklabel_format(axis='x',style='sci',scilimits=(3,3));data[str(budget)]={'steps':serial(x),'rr':serial(b),'sampling':serial(o)}
axes[0].legend(frameon=False,fontsize=7,loc='lower right');graph_finish('F9',fig,data)
# Equal wall-clock with sensor playback allowance.
fig,axes=plt.subplots(2,2,figsize=(3.35,3.35));data={}
for c,allowance in enumerate([1,1.5]):
 x=np.linspace(0,60*allowance,31);b=16+7.8*(1-np.exp(-x/30));o=16+10.0*(1-np.exp(-x/24))
 pair(axes[0,c],x,b,o,'','PSNR (dB)' if c==0 else '',f'{allowance:g}x allowance')
 br=np.floor(x*60);orr=np.floor(x*48)
 pair(axes[1,c],x,br,orr,'Elapsed time (s)','Training renders' if c==0 else '','')
 data[str(allowance)]={'seconds':serial(x),'baseline_psnr':serial(b),'ours_psnr':serial(o),'baseline_renders':serial(br),'ours_renders':serial(orr)}
graph_finish('F11',fig,data)
# Timed local load and achieved (not theoretical maximum) throughput.
x=np.arange(0,61,2);load=0.35+0.12*np.sin(x/6)+0.2*np.exp(-((x-26)/5)**2);kf=1.5+0.4*np.sin(x/8+1);work=np.clip(40*(1-load)/(kf/1.5),8,40)
fig,axes=plt.subplots(3,1,figsize=(3.35,4.15));ax=axes[0];line1=ax.plot(x,load*100,color=ORANGE,label='Tracking load');ax.set(xlabel='',ylabel='Tracking load (%)',title='(a) Tracking and arrivals');ay=ax.twinx();line2=ay.plot(x,kf,color=GRAY,linestyle='--',label='KF arrivals');ay.set_ylabel('KF arrivals / s',fontsize=8);ay.spines['top'].set_visible(False)
ax.legend(line1+line2,[l.get_label() for l in line1+line2],frameon=False,fontsize=7,loc='upper right');ax.set_ylim(0,90)
ay.set_ylim(0,2.7)
axes[1].plot(x,work,color=BLUE,label='Achieved work');axes[1].axhline(40,color=GRAY,linestyle='--',label='Configured cap');axes[1].set(xlabel='Sensor time (s)',ylabel='Training renders / KF',title='(b) Mapping throughput',ylim=(0,44));axes[1].legend(frameon=False,fontsize=7,loc='lower right')
axes[2].scatter(load*100,work,color=BLUE,s=17);axes[2].set(xlabel='Tracking load (%)',ylabel='Training renders / KF',title='(c) Load versus work')
graph_finish('F12',fig,{'sensor_seconds':serial(x),'tracking_load_fraction':serial(load),'kf_per_second':serial(kf),'renders_per_kf':serial(work)})
print('Built 10 figure assets: 3 generated images, 2 reused HumanTech figures, 5 dummy graphs.')
