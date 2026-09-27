#!/usr/bin/env python3
"""Plot measured online states; never infer continuous first-attainment times."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


ROOT = Path('/home/intern/gs_floaterLab/results/campaigns/gain_attribution/online_dense_training/v6_deferred')


def main():
    scenes = [('rpng', 'table_06'), ('aria', 'aria1253'), ('utmm', 'square-1')]
    fig, axes = plt.subplots(2, 3, figsize=(11.8, 6.3), gridspec_kw={'height_ratios': [2, 1]})
    report = {'protocol': 'paired_observed_states_v1', 'exact_first_attainment_claim': False,
              'coordinate_alignment_accepted': False, 'scenes': []}
    for column, (dataset, scene) in enumerate(scenes):
        ax = axes[0, column]
        curves = {arm: json.loads((ROOT / dataset / scene / arm / 'seed0/stream_quality_shared.json').read_text())
                  for arm in ('growth_ervs', 'kf_only')}
        dense, kf = [curves[arm] for arm in ('growth_ervs', 'kf_only')]
        if dense['cohort_sha256'] != kf['cohort_sha256']:
            raise ValueError('Paired evaluation cohorts differ')
        threshold = kf['points'][-1]['mean_heldout_psnr']
        summary = {'dataset': dataset, 'scene': scene, 'view_count': dense['view_count'],
                   'kf_endpoint_quality': threshold, 'points': []}
        for a, b in zip(dense['points'], kf['points']):
            summary['points'].append({'dense_seconds': a['seconds'], 'kf_seconds': b['seconds'],
                'dense_psnr': a['mean_heldout_psnr'], 'kf_psnr': b['mean_heldout_psnr'],
                'delta_psnr': a['mean_heldout_psnr'] - b['mean_heldout_psnr']})
        for arm, label, color in [('growth_ervs', 'Dense + Growth + ERVS', '#0072B2'),
                                  ('kf_only', 'KF-only', '#D55E00')]:
            points = curves[arm]['points']
            ax.plot([p['seconds'] for p in points], [p['mean_heldout_psnr'] for p in points],
                    'o--', color=color, label=label, markersize=4, linewidth=1.3)
            above = [p['seconds'] for p in points if p['mean_heldout_psnr'] >= threshold]
            summary[arm + '_earliest_observed_at_kf_endpoint_quality'] = min(above) if above else None
        ax.set_title(f'{dataset.upper()} {scene}')
        ax.set_xlabel('Elapsed mapping time (s)')
        ax.set_ylabel('Mean held-out PSNR (dB)')
        ax.grid(alpha=.2)
        ax.spines[['top', 'right']].set_visible(False)
        delta_ax = axes[1, column]
        delta_ax.plot([25, 50, 75, 100], [p['delta_psnr'] for p in summary['points']],
                      'o--', color='#333333', markersize=4, linewidth=1.2)
        delta_ax.axhline(0, color='#777777', linewidth=.8)
        delta_ax.set_ylim(-.85, .85)
        delta_ax.set_xticks([25, 50, 75, 100])
        delta_ax.set_xlabel('Matched stream checkpoint (%)')
        delta_ax.set_ylabel('Dense minus KF (dB)')
        delta_ax.grid(alpha=.2)
        delta_ax.spines[['top', 'right']].set_visible(False)
        report['scenes'].append(summary)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle('Online map quality at saved states (v6, seed 0)', fontsize=13)
    fig.text(.5, .025, 'Markers are measurements; dashed segments are guides only. '
             'Shared evaluation coordinates; alignment residuals remain under review.',
             ha='center', fontsize=8)
    fig.tight_layout(rect=(0, .075, 1, .94))
    fig.savefig(ROOT / 'paired_stream_quality.png', dpi=180)
    fig.savefig(ROOT / 'paired_stream_quality.svg')
    (ROOT / 'paired_stream_summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
