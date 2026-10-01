#!/usr/bin/env python3
"""Actual F3: measured convergence plus matching-prefix held-out renderings."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image

PAPER=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PAPER/'scripts'))
from build_measured_tables import RESULTS,read,sha
ASSET=PAPER/'figures/figure03_photometric_convergence'
CATALOG=PAPER/'figures/figure05_rendering_comparison/analysis/rendering_catalog.json'


def evaluated_curve(run):
    summary=run/'curve_evaluation/summary.json'
    end=read(run/'render_result.json')
    rows=[]
    for r in read(summary):
        if r['status']!='evaluated' or not r.get('usable_for_convergence_claim'):continue
        c=r['checkpoint']
        rows.append({'name':r['name'],'renders':end['render_counts']['training'] if c.get('final') else c['training_renders'],
            'psnr':r['quality']['mean_psnr'],'arrival_uid':None if c.get('final') else c['arrival_uid'],
            'final':bool(c.get('final')),'output':r['output']})
    assert len(rows)>=2 and any(r['final'] for r in rows)
    return sorted(rows,key=lambda r:r['renders'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--scene',required=True)
    p.add_argument('--selection-reason',required=True)
    p.add_argument('--frame',type=int,help='Explicit shared saved held-out view chosen after full-cohort review')
    p.add_argument('--gt-crop',nargs=4,type=int,help='Shared enlargement selected by inspecting GT only')
    a=p.parse_args()
    catalog=read(CATALOG);assert catalog['complete_candidate_render_review'], 'Review all candidate renders first'
    panel=RESULTS/('cvpr_assets/fixed_work_12f_v1' if a.scene=='aria301_12F' else 'cvpr_assets/fixed_work_v1')
    base=panel/'render40'/a.dataset/a.scene
    curves={arm:evaluated_curve(base/arm) for arm in ['vanilla','d3']}
    prefixes={arm:{r['arrival_uid']:r for r in rows if not r['final']} for arm,rows in curves.items()}
    common=set(prefixes['vanilla'])&set(prefixes['d3'])
    if common:
        uid=max(common)
        selected={arm:prefixes[arm][uid] for arm in curves}
    else:
        selected={arm:next(r for r in rows if r['final']) for arm,rows in curves.items()}
        uid=None
    dirs={arm:Path(r['output']) for arm,r in selected.items()}
    frames=set.intersection(*[{int(p.name.split('_')[0]) for p in (d/'images').glob('*_render.png')} for d in dirs.values()])
    if uid is not None:frames={i for i in frames if i<=uid}
    all_views=[]
    with (CATALOG.parent/'heldout_view_structure_scores.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            if r['dataset']==a.dataset and r['scene']==a.scene and int(r['frame_index']) in frames:
                r['frame_index']=int(r['frame_index']);r['gt_structure_score']=float(r['gt_structure_score'])
                r['crop']=json.loads(r['crop']);all_views.append(r)
    assert all_views, 'No shared saved past held-out view'
    view=(next(r for r in all_views if r['frame_index']==a.frame) if a.frame is not None
          else max(all_views,key=lambda r:r['gt_structure_score']))
    frame=view['frame_index'];crop=a.gt_crop if a.gt_crop is not None else view['crop']
    paths={arm:dirs[arm]/'images'/f'{frame:06d}_render.png' for arm in dirs}
    gt=dirs['d3']/'images'/f'{frame:06d}_gt.png';paths['gt']=gt
    assert sha(gt)==sha(dirs['vanilla']/'images'/gt.name)
    assert sha(gt)==view['gt_sha256']
    image={arm:Image.open(path).convert('RGB') for arm,path in paths.items()}
    w,h=image['gt'].size
    assert 0<=crop[0]<crop[2]<=w and 0<=crop[1]<crop[3]<=h
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7.2,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig=plt.figure(figsize=(3.35,3.25))
    grid=fig.add_gridspec(3,3,height_ratios=[1.5,1,.72],hspace=.62,wspace=.06)
    ax=fig.add_subplot(grid[0,:])
    for arm,color,label in [('vanilla','#737a81','VIGS-SLAM'),('d3','#087e8b','Ours (D3)')]:
        rows=curves[arm]
        ax.plot([r['renders']/1000 for r in rows],[r['psnr'] for r in rows],color=color,
            marker='o',markersize=2.8,linewidth=1.3,label=label)
    peak=max(r['psnr'] for r in curves['vanilla'])
    baseline=next(r for r in curves['vanilla'] if r['psnr']>=peak-1e-10)
    ours=next((r for r in curves['d3'] if r['psnr']>=peak),None)
    ax.axhline(peak,color='#a3a8ad',linestyle=':',linewidth=.7)
    if ours is not None:
        ax.scatter([ours['renders']/1000],[ours['psnr']],marker='*',s=42,c='#087e8b',zorder=5)
    ax.set_ylabel('Held-out PSNR (dB)');ax.set_xlabel('Training image-renders (k)',labelpad=2)
    ax.grid(color='#e4e8eb',linewidth=.5);ax.spines[['top','right']].set_visible(False)
    ax.legend(frameon=False,ncol=2,loc='upper left',fontsize=6.7)
    ax.margins(y=.18)
    for j,(arm,title) in enumerate([('vanilla','VIGS-SLAM'),('d3','Ours (D3)'),('gt','Ground truth')]):
        ax=fig.add_subplot(grid[1,j]);ax.imshow(image[arm]);ax.axis('off')
        x0,y0,x1,y1=crop
        ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,edgecolor='#e18b36',linewidth=.8))
        ax.set_title(title,fontsize=6.5,pad=2)
        if arm!='gt':ax.text(.5,-.12,f"{selected[arm]['renders']:,} renders",ha='center',va='top',
                            fontsize=6.2,transform=ax.transAxes)
        ax=fig.add_subplot(grid[2,j]);ax.imshow(image[arm].crop(tuple(crop)));ax.axis('off')
    fig.subplots_adjust(left=.14,right=.99,bottom=.018,top=.97)
    current=ASSET/'current';archive=ASSET/'output/humantech_before_current_measurements_2026-10-01'
    if not archive.exists():shutil.copytree(current,archive)
    for suffix in ['pdf','svg','png']:fig.savefig(current/f'figure.{suffix}',dpi=240)
    plt.close(fig)
    shutil.copy2(current/'figure.pdf',PAPER/'latex/figs/draft/f3.pdf')
    schedule='the same streaming prefix' if uid is not None else 'the final checkpoint'
    savings=baseline['renders']-ours['renders'] if ours else None
    star=(f"The starred checkpoint first reaches the baseline's highest observed PSNR with {savings:,} fewer training renders on the sampled grid." if savings is not None and savings>=0 else
          f"The starred checkpoint reaches the baseline's highest observed PSNR after {-savings:,} additional training renders on the sampled grid." if savings is not None else
          "Our sampled checkpoints do not reach the baseline's highest observed PSNR.")
    caption=(f"Photometric convergence on {a.dataset.upper()} {a.scene} at 40 training renders/KF. "
        f"The curve uses a fixed uniform held-out subset; points are actual evaluations. {star} "
        f"Below: VIGS-SLAM, ours and GT for held-out frame {frame} at {schedule}. "
        "The actual per-method render counts are shown; intermediate states are not exactly equal-work snapshots. "
        "Enlarged regions are selected from GT structure and shared. D3 proxy renders are additional work.")
    (current/'caption.md').write_text(caption+'\n')
    rows=[{'arm':arm,**r} for arm,rs in curves.items() for r in rs]
    data=ASSET/'analysis/measured_photometric_curve.csv';data.parent.mkdir(exist_ok=True)
    with data.open('w',newline='') as f:
        writer=csv.DictWriter(f,list(rows[0]));writer.writeheader();writer.writerows(rows)
    (current/'provenance.json').write_text(json.dumps({'kind':'actual_photometric_convergence',
        'generator':str(Path(__file__)),'generator_sha256':sha(Path(__file__)),
        'experimental_evidence':True,'all_candidate_scenes_evaluated_before_selection':True,
        'catalog':str(CATALOG),'catalog_sha256':sha(CATALOG),'dataset':a.dataset,'scene':a.scene,
        'selection_reason':a.selection_reason,'frame':frame,'crop':crop,
        'view_selection':'manual shared held-out view after full-cohort review' if a.frame is not None else 'highest GT structure',
        'crop_selection':'manual GT-only semantic detail box' if a.gt_crop is not None else 'GT structure only',
        'stream_prefix_uid':uid,'selected_checkpoints':selected,'star':{'baseline':baseline,'ours':ours},
        'curves':rows,'data_sha256':sha(data),'images':{arm:{'path':str(p),'sha256':sha(p)} for arm,p in paths.items()},
        'manuscript_width':'one_column','exact_equal_work_intermediate_images':False},indent=2)+'\n')
    scene_tex=a.scene.replace('_',r'\_')
    (PAPER/'latex/fig/f3_draft.tex').write_text('\\begin{figure}[tbp]\n  \\centering\n  \\includegraphics[width=\\linewidth]{figs/draft/f3.pdf}\n'
        f'  \\caption{{Measured photometric convergence on {a.dataset.upper()} \\texttt{{{scene_tex}}} at 40 training renders/KF. '
        f'{star} Below: held-out renderings and shared GT-selected enlargements at {schedule}; actual render counts are shown. '
        'The curve uses a fixed uniform held-out subset. D3 proxy renders are additional work.}\n'
        '  \\label{fig:photometric_convergence}\n\\end{figure}\n')
    print('INSTALLED_ACTUAL_F3',a.dataset,a.scene,frame,selected)


if __name__=='__main__':main()
