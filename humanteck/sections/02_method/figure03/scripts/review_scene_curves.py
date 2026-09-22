#!/usr/bin/env python3
"""Plot all screened candidates together and preserve numerical selection evidence."""
import json
import shutil
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

WORK=Path('/home/intern/gs_floaterLab')
ROOT=Path(__file__).resolve().parent.parent
SOURCE=WORK/'results/figure03_scene_search_20260921'
DEST=ROOT/'analysis/scene_search'


def main():
    panel=[('Aria 301_305 (previous)',WORK/'results/figure03_convergence_20260921/aria301_305/evaluation/curves.json'),
           ('UTMM square-1',SOURCE/'utmm/square-1/evaluation/curves.json'),
           ('RPNG table_01',SOURCE/'rpng/table_01/evaluation/curves.json'),
           ('RPNG table_06',SOURCE/'rpng/table_06/evaluation/curves.json')]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none'})
    fig,axs=plt.subplots(2,2,figsize=(12,8),sharey=True)
    summary=[]
    for ax,(name,path) in zip(axs.flat,panel):
        if not path.exists():ax.set_title(name+' — pending');continue
        d=json.loads(path.read_text());cs={a:sorted([r for r in d['curves'] if r['arm']==a],key=lambda r:r['iteration']) for a in ['baseline','ours']}
        ends={a:rr[-1]['iteration'] for a,rr in cs.items()};end=min(ends.values())
        x=np.linspace(.3*end,.8*end,101)
        q={a:np.interp(x,[r['iteration'] for r in rr],[r['mean_psnr'] for r in rr]) for a,rr in cs.items()}
        gap=float(np.mean(q['ours']-q['baseline']))
        up={};maxjump={}
        for a,color,ls in [('baseline','#d86236','--'),('ours','#008f93','-')]:
            rr=cs[a];xx=np.array([r['iteration'] for r in rr]);yy=np.array([r['mean_psnr'] for r in rr])
            ax.plot(xx,yy,color=color,ls=ls,marker='o',ms=3,lw=2,label='VIGS-SLAM' if a=='baseline' else 'Ours')
            deltas=np.diff(yy)[xx[1:]>=.3*end]
            up[a]=float(np.mean(deltas>=0));maxjump[a]=float(max(deltas))
        final_gap=cs['ours'][-1]['mean_psnr']-cs['baseline'][-1]['mean_psnr']
        ax.set_title(name+f"\nMidstream gap {gap:+.2f} dB | final {final_gap:+.2f} dB",fontsize=12)
        ax.set_xlabel('Mapping iterations');ax.set_ylabel('Evaluation PSNR (dB)')
        ax.set_ylim(4,29);ax.grid(alpha=.22);ax.legend(loc='lower right',fontsize=9)
        summary.append({'scene':name,'source':str(path),'heldout_count':d['heldout_count'],'final_gap':final_gap,'mean_gap_30_to_80_percent_common_iteration_span':gap,'nondecreasing_interval_fraction_after_30pct':up,'max_upward_checkpoint_jump_after_30pct':maxjump,'checkpoint_counts':{a:len(v) for a,v in cs.items()},'endpoint_checks':d.get('endpoint_checks')})
        if 'previous' not in name:shutil.copy2(path,DEST/(d['scene']+'_curves.json'))
    fig.suptitle('Native system curves on fixed full-trajectory held-out views',fontsize=15)
    fig.text(.5,.01,'Raw measured checkpoints; no smoothing. Midstream gaps use linear interpolation only for the summary statistic.',ha='center',fontsize=10)
    fig.tight_layout(rect=[0,.04,1,.95])
    fig.savefig(DEST/'curve_comparison.png',dpi=180)
    fig.savefig(DEST/'curve_comparison.svg')
    (DEST/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
