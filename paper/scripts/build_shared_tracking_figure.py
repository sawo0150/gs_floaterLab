#!/usr/bin/env python3
"""Measured F12 with the shared tracker recipe, without capacity extrapolation."""
import csv
import hashlib
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

PAPER = Path(__file__).resolve().parents[1]
ASSET = PAPER / 'figures/figure12_tracking_mapping_capacity'
DATA = PAPER / 'results/tables/cvpr_endpoint_measurements.csv'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    with DATA.open(newline='') as f:
        candidates = [r for r in csv.DictReader(f) if r['protocol']=='live_fifo_shared_tracking']
    scenes = sorted({(r['dataset'],r['scene']) for r in candidates})
    complete = [(d,s) for d,s in scenes if len({(r['arm'],r['time_scale']) for r in candidates if (r['dataset'],r['scene'])==(d,s)})==4]
    assert complete, 'Wait for one full 1x/1.5x shared-tracker quartet'
    rows = []
    for d,s in complete:
        quartet = [r for r in candidates if (r['dataset'],r['scene'])==(d,s)]
        assert len({r['cohort_uid_sha256'] for r in quartet})==1
        for r in quartet:
            p = Path(r['output']) / 'result.json'
            x = json.loads(p.read_text())
            assert not x['error'] and x['zero_tail_observed'] and x['source_unchanged']
            assert x['tracked_frames']==x['input_frames'] and x['tracking_kfs_final']>0
            assert sha(p)==r['result_sha256']
            rows.append({'dataset':d,'scene':s,'arm':r['arm'],'allowance':float(r['time_scale']),
                'tracking_call_p95_ms':x['track_call_ms']['95'],
                'committed_renders_per_tracking_kf':x['committed_renders']/x['tracking_kfs_final'],
                'tracking_time_ratio':x['tracking_elapsed_seconds']/x['duration_seconds'],
                'tracking_seconds':x['tracking_elapsed_seconds'],'allowed_seconds':x['duration_seconds'],
                'committed_renders':x['committed_renders'],'tracking_keyframes':x['tracking_kfs_final'],
                'mapper_admissions':x['kf_admissions'],'pending_packet_drops':x['worker']['backlog']['dropped_mapping_packets'],
                'source':str(p),'source_sha256':sha(p)})
    analysis = ASSET / 'analysis'; analysis.mkdir(exist_ok=True)
    out = analysis / 'measured_shared_tracking_work.csv'
    with out.open('w',newline='') as f:
        writer=csv.DictWriter(f,list(rows[0]));writer.writeheader();writer.writerows(rows)
    current = ASSET / 'current'
    archive = ASSET / 'output/previous_tracker_recipe_2026-10-01'
    if not archive.exists(): shutil.copytree(current,archive)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7.2,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig,axes=plt.subplots(2,1,figsize=(3.35,3.15))
    settings=[('vanilla',1),('ours',1),('vanilla',1.5),('ours',1.5)]
    colors={'vanilla':'#72787f','ours':'#087e8b'}
    for arm,allowance in settings:
        points=[r for r in rows if r['arm']==arm and r['allowance']==allowance]
        axes[0].scatter([r['tracking_call_p95_ms'] for r in points],
            [r['committed_renders_per_tracking_kf'] for r in points],s=19,
            marker='o' if allowance==1 else '^',c=colors[arm],alpha=.8,
            label=f"{'VIGS' if arm=='vanilla' else 'Ours'} {allowance:g}x")
    axes[0].set_xlabel('Tracking call p95 (ms)')
    axes[0].set_ylabel('Renders / tracking KF')
    datasets=[d for d in ['rpng','utmm','aria'] if any(r['dataset']==d for r in rows)]
    for j,(arm,allowance) in enumerate(settings):
        values=[np.mean([r['tracking_time_ratio'] for r in rows if r['dataset']==d and r['arm']==arm and r['allowance']==allowance]) for d in datasets]
        axes[1].bar(np.arange(len(datasets))+(j-1.5)*.18,values,width=.17,color=colors[arm],
                    edgecolor='white',linewidth=.3,hatch='//' if allowance==1.5 else None)
    axes[1].axhline(1,color='#ab503b',linewidth=.8,linestyle='--')
    axes[1].set_ylabel('Tracking time /\nallowance')
    names={'rpng':'RPNG','utmm':'UTMM','aria':'Aria'}
    axes[1].set_xticks(np.arange(len(datasets)),[f"{names[d]} (n={sum(x==d for x,_ in complete)})" for d in datasets])
    for ax in axes:
        ax.grid(color='#e4e8eb',linewidth=.5);ax.set_axisbelow(True)
        ax.spines[['top','right']].set_visible(False)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,ncol=2,frameon=False,fontsize=6.8,loc='upper center',bbox_to_anchor=(.57,1))
    fig.tight_layout(pad=.7,h_pad=1.1,rect=(0,0,1,.9))
    for suffix in ['pdf','svg','png']:fig.savefig(current/f'figure.{suffix}',dpi=220)
    plt.close(fig)
    shutil.copy2(current/'figure.pdf',PAPER/'latex/figs/draft/f12.pdf')
    caption=(f'Shared-tracker measurements on {len(complete)} paired candidate sequences. '
        'Top: each point relates observed tracking-call p95 to committed training renders per final tracking keyframe. '
        'The denominator includes keyframes not admitted to mapping; the mapper cap is 40 renders per admission. '
        'Bottom: equal-weight scene means of tracking completion time divided by its allowance; values above one exceed the mapper deadline. '
        'Both systems use the same dataset Tracking configuration. This is an observed association, not an isolated tracking-cost intervention or a hardware capacity bound.')
    (current/'caption.md').write_text(caption+'\n')
    (current/'README.md').write_text('# 공통 tracking 설정의 실제 측정\n\n'+caption+'\n')
    (current/'provenance.json').write_text(json.dumps({'kind':'actual_shared_tracking_work',
        'experimental_evidence':True,'complete_candidate_cohort':len(complete)==20,'paired_scenes':complete,
        'data':str(out),'data_sha256':sha(out),'rows':rows,'manuscript_width':'one_column',
        'claims_hardware_limit':False,'claims_isolated_tracking_cost_effect':False},indent=2)+'\n')
    (PAPER/'latex/fig/f12_draft.tex').write_text('\\begin{figure}[tbp]\n  \\centering\n  \\includegraphics[width=\\linewidth]{figs/draft/f12.pdf}\n'
        f'  \\caption{{Shared-tracker measurements on {len(complete)} paired sequences at 1$\\times$/1.5$\\times$ allowances. '
        'Top: observed tracking-call p95 versus committed training renders per final tracking KF, including KFs not admitted to mapping. '
        'Bottom: tracking completion time divided by allowance (dataset scene means); values above one exceed the mapper deadline. '
        'The mapper cap is 40 renders/admission. These measurements do not establish a causal tracking-cost effect or a hardware limit.}\n'
        '  \\label{fig:tracking_capacity}\n\\end{figure}\n')
    print('F12_SHARED_TRACKING',len(complete),'scenes',len(rows),'actual runs')


if __name__=='__main__':main()
