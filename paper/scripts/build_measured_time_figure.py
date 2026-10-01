#!/usr/bin/env python3
"""Actual equal-time endpoints; independent runs, never dummy convergence."""
import csv
import json
from pathlib import Path
import shutil
import hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

PAPER = Path(__file__).resolve().parents[1]
ROOT = PAPER.parent
SOURCE = ROOT / 'results/campaigns/gain_attribution/fifo_live/v1'
ASSET = PAPER / 'figures/figure11_equal_time_online'


def main():
    canonical = PAPER / 'results/tables/cvpr_endpoint_measurements.csv'
    with canonical.open(newline='') as f:
        fresh = [r for r in csv.DictReader(f) if r['protocol']=='live_fifo_shared_tracking']
    measured = sorted({(r['dataset'],r['scene']) for r in fresh})
    complete = [(d,s) for d,s in measured if len({(r['arm'],r['time_scale']) for r in fresh if (r['dataset'],r['scene'])==(d,s)})==4]
    shared = bool(complete)
    lookup = {(r['dataset']+'/'+r['scene'],float(r['time_scale']),r['arm']):Path(r['output']) for r in fresh}
    scenes = [d+'/'+s for d,s in complete] if shared else ['aria','rot','rpng','utmm']
    rows = []
    for scene in scenes:
        for scale in [1, 1.5]:
            for arm in ['vanilla', 'ours']:
                run = lookup[(scene,scale,arm)] if shared else SOURCE / ('scale1' if scale == 1 else 'scale1p5') / scene / arm
                result_path = run / 'result.json'
                result = json.loads(result_path.read_text())
                metric_path = run / 'psnr/strict_fixed_manifest/final_result.json'
                metric = json.loads(metric_path.read_text())
                q = metric['predeclared_fixed_manifest_posthoc']
                assert q['mapping_disjoint'] and q['mapping_view_overlap_count'] == 0
                assert not result['error'] and result['zero_tail_observed']
                assert result['tracked_frames'] == result['input_frames']
                uids = sorted(v['uid'] for v in metric['per_view'] if v['predeclared_fixed_manifest_split'])
                rows.append({'scene': scene, 'scale': scale, 'arm': arm, 'psnr': q['mean_psnr'],
                    'committed_renders': result['committed_renders'], 'allowed_seconds': result['duration_seconds'],
                    'tracking_seconds': result['tracking_elapsed_seconds'],
                    'cohort_sha256': hashlib.sha256(json.dumps(uids).encode()).hexdigest(),
                    'metric_path': str(metric_path), 'metric_sha256': hashlib.sha256(metric_path.read_bytes()).hexdigest(),
                    'result_path': str(result_path), 'result_sha256': hashlib.sha256(result_path.read_bytes()).hexdigest()})
    for scene in scenes:
        assert len({r['cohort_sha256'] for r in rows if r['scene'] == scene}) == 1
    analysis = ASSET / 'analysis'; analysis.mkdir(exist_ok=True)
    data = analysis / 'measured_time_endpoints.csv'
    with data.open('w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    current = ASSET / 'current'
    archive = ASSET / 'output/dummy_before_measurements_2026-10-01'
    if not archive.exists(): shutil.copytree(current, archive)
    previous = ASSET / 'output/previous_tracker_recipe_2026-10-01'
    if shared and not previous.exists(): shutil.copytree(current,previous)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.5,
                         'axes.labelsize': 7.7, 'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(2, 1, figsize=(3.35, 2.95), sharex=True)
    colors = {'vanilla': '#737a81', 'ours': '#087e8b'}
    aggregate = []
    for arm in ['vanilla', 'ours']:
        for ax, metric, divisor in [(axes[0], 'psnr', 1), (axes[1], 'committed_renders', 1000)]:
            means = [np.mean([r[metric] / divisor for r in rows if r['arm'] == arm and r['scale'] == scale]) for scale in [1, 1.5]]
            ax.plot([1, 1.5], means, marker='o' if arm == 'ours' else 's', markersize=4,
                    color=colors[arm], linewidth=1.6, label='VIGS-SLAM' if arm == 'vanilla' else 'Ours')
            for scale, mean in zip([1, 1.5], means):
                aggregate.append({'arm': arm, 'scale': scale, 'metric': metric, 'mean': float(mean), 'scenes': len(scenes)})
                ax.annotate(f'{mean:.2f}' if metric == 'psnr' else f'{mean:.1f}', (scale, mean),
                            xytext=(4, 5 if arm == 'ours' and metric == 'psnr' else -11),
                            textcoords='offset points', fontsize=6.7, color=colors[arm])
    axes[0].set_ylabel('Held-out PSNR (dB)')
    axes[1].set_ylabel('Completed renders (k)')
    axes[1].set_xlabel('Time allowance / sensor duration')
    axes[0].legend(frameon=False, ncol=2, loc='upper left', fontsize=7)
    axes[0].margins(y=.28)
    axes[1].margins(y=.25)
    for ax in axes:
        ax.set_xlim(.92, 1.65); ax.set_xticks([1, 1.5], ['1x', '1.5x'])
        ax.grid(color='#e4e8eb', linewidth=.5); ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout(pad=.6, h_pad=.9)
    fig.savefig(current / 'figure.pdf'); fig.savefig(current / 'figure.svg')
    fig.savefig(current / 'figure.png', dpi=220); plt.close(fig)
    shutil.copy2(current / 'figure.pdf', PAPER / 'latex/figs/draft/f11.pdf')
    caption = ('Final held-out quality and completed training renders with concurrent tracking at 1x and 1.5x sensor-duration allowances. '
               f'Each point is an equal-weight mean over {len(scenes)} completed sequence pairs from separate runs, not a within-run convergence curve. '
               'The mapper stops at the deadline; tracking may finish later. ' +
               ('Both systems use the same dataset Tracking configuration.' if shared else 'RPNG/UTMM tracker configurations differ between systems.'))
    (current / 'caption.md').write_text(caption + '\n')
    (current / 'provenance.json').write_text(json.dumps({'kind': 'actual_equal_time_endpoints', 'experimental_evidence': True,
        'complete_candidate_cohort': len(scenes)==20, 'tracking_recipe': 'shared_official_dataset_Tracking_config' if shared else 'previous_development_recipe',
        'data': str(data), 'rows': rows, 'aggregate': aggregate,
        'within_run_convergence': False, 'manuscript_width': 'one_column',
        'remaining_work': 'shared-tracker full cohort and checkpoint-based wall-clock convergence'}, indent=2) + '\n')
    (PAPER / 'latex/fig/f11_draft.tex').write_text('\\begin{figure}[tbp]\n  \\centering\n  \\includegraphics[width=\\linewidth]{figs/draft/f11.pdf}\n'
        f'  \\caption{{Measured final quality and completed training renders with concurrent tracking. Each point averages {len(scenes)} completed sequence pairs from separate runs at 1$\\times$/1.5$\\times$ time allowances. These are budget-response endpoints. '
        + ('Both systems use the same dataset Tracking configuration; ' if shared else 'RPNG/UTMM tracker settings differ; ')
        + 'tracking can finish after the mapper deadline.}\n'
        '  \\label{fig:equal_time}\n\\end{figure}\n')
    print('Installed F11:',len(rows),'actual endpoints; shared tracker:',shared,'; within-run convergence remains pending.')


if __name__ == '__main__': main()
