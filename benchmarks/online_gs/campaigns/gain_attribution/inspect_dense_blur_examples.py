#!/usr/bin/env python3
"""Read-only visual diagnostics of decisions; never supplies training inputs."""
import argparse
from pathlib import Path
import json
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import run_cumulative_ervs_panel as common
sys.path.insert(0,str(common.trial.BASE.WORKSPACE/'benchmarks/online_gs'))
from exp78b_frozen_archive import FrozenTrackerArchive


def main():
    p=argparse.ArgumentParser();p.add_argument('--result',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    x=common.read(args.result/'render_result.json');gate=x['dense_blur_filter']
    archive=FrozenTrackerArchive(common.trial.BASE.sequence_paths(x['dataset'],x['scene'])['archive'])
    rejected=[d for d in gate['decisions'] if not d['accepted']]
    fallback = not rejected
    if fallback:
        rejected=sorted(gate['decisions'],key=lambda d:d['score']['high_frequency_ratio']/max(d['reference']['high_frequency_ratio'],1e-12))[:4]
    # Distributed temporal examples, not cherry-picked by PSNR/render quality.
    chosen=[rejected[i] for i in sorted(set(np.linspace(0,len(rejected)-1,min(4,len(rejected)),dtype=int)))]
    fig,axes=plt.subplots(len(chosen),3,figsize=(12,3.3*len(chosen)),squeeze=False)
    for row,d in zip(axes,chosen):
        for ax,u,title in zip(row,[d['left'],d['uid'],d['right']],['Arrived left KF','Low sharpness dense' if fallback else 'Rejected dense','Arrived right KF']):
            img=archive.load_rgb(u).permute(1,2,0).numpy()
            ax.imshow(img);ax.set_title(f'{title}: {u}');ax.axis('off')
    fig.tight_layout();args.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(args.output,dpi=130);plt.close(fig)
    common.write(args.output.with_suffix('.json'),{'dataset':x['dataset'],'examples':chosen,
        'selection_rule':'four lowest relative frequency ratio' if fallback else 'four evenly spaced rejected UID indices; training input RGB'})
    print(args.output)

if __name__=='__main__':main()
