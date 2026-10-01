#!/usr/bin/env python3
"""Actual F5: shared held-out views and GT-only enlargements for three datasets."""
import argparse
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
from build_measured_tables import read,sha
ASSET=PAPER/'figures/figure05_rendering_comparison'
CATALOG=ASSET/'analysis/rendering_catalog.json'


def main():
    p=argparse.ArgumentParser();p.add_argument('--sequences',nargs=3,required=True,help='dataset:scene')
    p.add_argument('--selection-reason',required=True)
    p.add_argument('--rpng-gt-crop',nargs=4,type=int,help='Shared RPNG crop chosen from GT, e.g. readable poster text')
    a=p.parse_args()
    catalog=read(CATALOG);assert catalog['complete_candidate_render_review'], 'Review all20 scenes before choosing examples'
    pairs=[s.split(':',1) for s in a.sequences]
    assert {d for d,s in pairs}=={'rpng','utmm','aria'}
    selected=[next(r for r in catalog['rows'] if (r['dataset'],r['scene'])==(d,s)) for d,s in pairs]
    if a.rpng_gt_crop is not None:
        row=next(r for r in selected if r['dataset']=='rpng')
        row['proposed_view']['crop']=a.rpng_gt_crop
        row['proposed_view']['crop_selection']='manual GT-only poster text, applied identically to both methods'
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig=plt.figure(figsize=(3.35,3.9))
    grid=fig.add_gridspec(6,3,height_ratios=[1,.6,1,.6,1,.6],hspace=.22,wspace=.035)
    for i,row in enumerate(selected):
        view=row['proposed_view'];crop=tuple(view['crop'])
        for j,(arm,label) in enumerate([('vanilla','VIGS-SLAM'),('d3','Ours (D3)'),('gt','Ground truth')]):
            path=Path(view[arm]);assert sha(path)==view[arm+'_sha256']
            image=Image.open(path).convert('RGB')
            ax=fig.add_subplot(grid[i*2,j]);ax.imshow(image);ax.axis('off')
            x0,y0,x1,y1=crop
            ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,edgecolor='#e18b36',linewidth=.7))
            if i==0:ax.set_title(label,fontsize=7,pad=2)
            if j==0:ax.text(-.055,.5,row['dataset'].upper(),rotation=90,ha='center',va='center',
                            transform=ax.transAxes,fontsize=6.5)
            ax=fig.add_subplot(grid[i*2+1,j]);ax.imshow(image.crop(crop));ax.axis('off')
    fig.subplots_adjust(left=.045,right=.995,bottom=.005,top=.95)
    current=ASSET/'current';archive=ASSET/'output/mockup_before_actual_renderings_2026-10-01'
    if not archive.exists():shutil.copytree(current,archive)
    for suffix in ['pdf','svg','png']:fig.savefig(current/f'figure.{suffix}',dpi=240)
    plt.close(fig)
    shutil.copy2(current/'figure.pdf',PAPER/'latex/figs/draft/f5.pdf')
    ids='; '.join(f"{r['dataset'].upper()} {r['scene']} / held-out frame {r['proposed_view']['frame_index']}" for r in selected)
    caption=('Final held-out RGB renderings at 40 training renders/KF. Columns show VIGS-SLAM, ours and ground truth. '
        'The view and enlargement are shared within each row; crop proposals use GT structure only. '+ids+'. '
        'All20 candidates were evaluated and reviewed before selecting these examples. D3 uses additional proxy renders; this is a complete-system comparison.')
    (current/'caption.md').write_text(caption+'\n')
    (current/'README.md').write_text('# 실제 최종 RGB 비교\n\n'+caption+'\n')
    (current/'provenance.json').write_text(json.dumps({'kind':'actual_final_heldout_renderings','experimental_evidence':True,
        'generator':str(Path(__file__)),'generator_sha256':sha(Path(__file__)),
        'catalog':str(CATALOG),'catalog_sha256':sha(CATALOG),'all_candidate_renderings_reviewed':True,
        'selection_reason':a.selection_reason,'examples':selected,'crop_selection_uses_prediction_scores':False,
        'manuscript_width':'one_column','loss_isolated':False,'image_content_modified':False},indent=2)+'\n')
    tex_ids='; '.join(r['dataset'].upper()+r' \texttt{'+r['scene'].replace('_',r'\_')+'}' for r in selected)
    (PAPER/'latex/fig/f5_draft.tex').write_text('\\begin{figure}[tbp]\n  \\centering\n  \\includegraphics[width=\\linewidth]{figs/draft/f5.pdf}\n'
        '  \\caption{Actual final held-out renderings at 40 training renders/KF. Columns: VIGS-SLAM, ours and GT. Rows: '+tex_ids+'. '
        'Shared enlarged regions are selected from GT structure. All 20 candidates were evaluated before selection. D3 adds proxy renders.}\n'
        '  \\label{fig:rgb_comparison}\n\\end{figure}\n')
    print('INSTALLED_ACTUAL_F5',ids)


if __name__=='__main__':main()
