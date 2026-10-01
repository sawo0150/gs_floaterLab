#!/usr/bin/env python3
"""F11/F12 from actual shared-tracker checkpoint clocks and event records.

Catalog mode is usable while measurement runs. Figure selection requires all
declared live candidates to be considered. Rendering and installation are
separate: inspect the output first, then use --install.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

PAPER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER / 'scripts'))
from collect_measured_live_curves import collect, ANALYSIS
from build_measured_tables import sha

COLORS = {'vanilla': '#737a81', 'ours': '#087e8b'}
LABELS = {'vanilla': 'VIGS-SLAM', 'ours': 'Ours'}


def selected_quartet(catalog, dataset, scene, curves):
    assert catalog['all_candidate_runs_evaluated'] if curves else catalog['all_candidate_live_runs_considered'], \
        'Consider all 20 scenes at both allowances before selecting an example'
    rows = [r for r in catalog['runs'] if (r['dataset'], r['scene']) == (dataset, scene)]
    assert len(rows) == 4 and all('run' in r for r in rows)
    if curves: assert all(r['status'] == 'measured' for r in rows)
    return {(r['allowance'], r['arm']): r for r in rows}


def style_axes(axes):
    for ax in axes.flat:
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(color='#e4e8eb', linewidth=.5)
        ax.tick_params(labelsize=6.3, pad=2)


def plot_quality(rows):
    fig, axes = plt.subplots(2, 2, figsize=(3.35, 3.12))
    for col, scale in enumerate([1., 1.5]):
        for arm in ['vanilla', 'ours']:
            run = rows[(scale, arm)]
            for row, x_key, divisor in [(0, 'elapsed_seconds', 1), (1, 'training_renders', 1000)]:
                points = run['points']
                axes[row, col].plot([p[x_key] / divisor for p in points], [p['psnr_db'] for p in points],
                    color=COLORS[arm], marker='o' if arm == 'ours' else 's', markersize=2.4,
                    linewidth=1.1, label=LABELS[arm])
        duration = rows[(scale, 'ours')]['elapsed_allowance_seconds']
        assert abs(duration - rows[(scale, 'vanilla')]['elapsed_allowance_seconds']) < 1e-6
        axes[0, col].set_title(f"({'a' if col == 0 else 'b'}) {scale:g}x allowance", fontsize=7, pad=4)
        axes[0, col].set_xlim(0, duration * 1.025)
        axes[0, col].set_xlabel('Stream elapsed time (s)', fontsize=6.5, labelpad=2)
        axes[1, col].set_xlabel('Training image-renders (k)', fontsize=6.5, labelpad=2)
        axes[1, col].set_title(f"({'c' if col == 0 else 'd'}) Same runs, render axis", fontsize=6.6, pad=4)
    for row in [0, 1]:
        axes[row, 0].set_ylabel('Held-out PSNR (dB)', fontsize=6.6, labelpad=3)
        lo = min(ax.get_ylim()[0] for ax in axes[row]); hi = max(ax.get_ylim()[1] for ax in axes[row])
        for ax in axes[row]: ax.set_ylim(lo, hi)
    style_axes(axes)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, ncol=2, fontsize=6.5, loc='upper center', bbox_to_anchor=(.56, 1.005))
    fig.subplots_adjust(left=.17, right=.985, top=.865, bottom=.12, hspace=.88, wspace=.42)
    return fig


def plot_work(rows):
    fig, axes = plt.subplots(2, 2, figsize=(3.35, 3.12), sharex='col')
    for col, scale in enumerate([1., 1.5]):
        for arm in ['vanilla', 'ours']:
            bins = rows[(scale, arm)]['bins']
            seconds = [(x['start_seconds'] + x['end_seconds']) / 2 for x in bins]
            fraction = [x['tracking_call_wall_fraction'] for x in bins]
            per_kf = [float(x['renders_per_frame_observed_admission']) if x['renders_per_frame_observed_admission'] != '' else np.nan for x in bins]
            axes[0, col].plot(seconds, fraction, color=COLORS[arm], linewidth=1,
                marker='o' if arm == 'ours' else 's', markersize=2, label=LABELS[arm])
            axes[1, col].plot(seconds, per_kf, color=COLORS[arm], linewidth=1,
                marker='o' if arm == 'ours' else 's', markersize=2)
        axes[0, col].set_title(f"({'a' if col == 0 else 'b'}) {scale:g}x allowance", fontsize=7, pad=4)
        axes[0, col].set_ylim(-.03, 1.05)
        axes[1, col].axhline(40, color='#ab503b', linewidth=.6, linestyle='--')
        axes[1, col].set_xlabel('Stream elapsed time (s)', fontsize=6.6, labelpad=3)
        axes[1, col].set_xlim(0, rows[(scale, 'ours')]['elapsed_allowance_seconds'])
    axes[0, 0].set_ylabel('Tracking call wall fraction', fontsize=6.5, labelpad=3)
    axes[1, 0].set_ylabel('Renders / observed admission', fontsize=6.4, labelpad=3)
    lo, hi = 0, max(ax.get_ylim()[1] for ax in axes[1])
    for ax in axes[1]: ax.set_ylim(lo, hi)
    style_axes(axes)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, ncol=2, fontsize=6.5, loc='upper center', bbox_to_anchor=(.56, 1.005))
    fig.subplots_adjust(left=.17, right=.985, top=.865, bottom=.12, hspace=.32, wspace=.42)
    return fig


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog-only', action='store_true')
    p.add_argument('--kind', choices=['quality', 'work'], default='quality')
    p.add_argument('--dataset'); p.add_argument('--scene'); p.add_argument('--selection-reason')
    p.add_argument('--output', type=Path); p.add_argument('--install', action='store_true')
    a = p.parse_args(); catalog = collect()
    print('LIVE_CANDIDATES', catalog['live_runs_measured'], '/80 runs;', catalog['curves_measured'], '/80 curves')
    if a.catalog_only: return
    assert a.dataset and a.scene and a.selection_reason and a.output
    quality = a.kind == 'quality'
    rows = selected_quartet(catalog, a.dataset, a.scene, quality)
    asset = PAPER / ('figures/figure11_equal_time_online' if quality else 'figures/figure12_tracking_mapping_capacity')
    number = 11 if quality else 12
    a.output.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7, 'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    fig = plot_quality(rows) if quality else plot_work(rows)
    for suffix in ['pdf', 'svg', 'png']: fig.savefig(a.output / f'figure.{suffix}', dpi=240)
    plt.close(fig)
    if quality:
        caption = (f'Shared-tracker online refinement on {a.dataset.upper()} {a.scene} at 1x/1.5x sensor-duration allowances. '
            '(a,b) Actual saved-state held-out PSNR versus elapsed stream time. (c,d) The same measured states versus training image-renders. '
            'Markers are evaluated checkpoints; rejected pose alignments are excluded and retained in the catalog. The uniform held-out subset '
            'and dataset Tracking configuration are shared. Model warm load is outside the clock; map optimization has zero tail. '
            'Final states are held at the deadline; tracking may finish later. Extra D3 proxy work is included in elapsed time, but not in the training-image-render axis.')
    else:
        caption = (f'Tracking and mapping work on {a.dataset.upper()} {a.scene} in fixed five-second elapsed-time bins at 1x/1.5x allowances. '
            '(a,b) Fraction of each bin covered by tracking calls, including CPU/GPU waiting; this is not GPU occupancy. '
            'Bottom: committed training renders divided by mapper admissions first observed at frame-end queries in that bin. '
            'Bins without observed admissions are NA and are not interpolated. Admissions include reset generations; backlog can carry work '
            'across bins, so the ratio need not equal the 40-render/admission cap (dashed). This is observed allocation, not a hardware capacity bound.')
    scene_tex = a.scene.replace('_', r'\_')
    text = ('Measured online refinement with concurrent tracking on ' + a.dataset.upper() + r' \texttt{' + scene_tex +
        r'} at 1$\times$/1.5$\times$ allowances. Top: held-out PSNR versus elapsed time. Bottom: the same saved states versus training image-renders. '
        r'Tracking settings and held-out images are shared. Warm load is excluded; optimizer tail is zero; tracking may finish late. D3 proxy work is included in time.' if quality else
        'Measured tracking and mapping allocation on ' + a.dataset.upper() + r' \texttt{' + scene_tex +
        r'} in five-second bins at 1$\times$/1.5$\times$ allowances. Top: tracking-call wall fraction, including waiting. '
        r'Bottom: committed training renders per frame-observed mapper admission; gaps mean no admission. The dashed line is the 40-render/admission cap. '
        r'Backlog crosses bins. These are observed workloads, not GPU occupancy or maximum capacity.')
    tex = ('\\begin{figure}[tbp]\n  \\centering\n' +
        f'  \\includegraphics[width=\\linewidth]{{figs/draft/f{number}.pdf}}\n' +
        '  \\caption{' + text + '}\n  \\label{' + ('fig:equal_time' if quality else 'fig:tracking_capacity') + '}\n\\end{figure}\n')
    (a.output / 'caption.md').write_text(caption + '\n')
    (a.output / 'figure.tex').write_text(tex)
    provenance = dict(kind='actual_shared_tracking_clock_curves' if quality else 'actual_shared_tracking_binned_work',
        experimental_evidence=True, all_live_candidates_considered=True, dataset=a.dataset, scene=a.scene,
        selection_reason=a.selection_reason, runs=list(rows.values()), manuscript_width='one_column',
        generator=str(Path(__file__)), generator_sha256=sha(Path(__file__)),
        catalog=str(ANALYSIS / 'measured_live_curve_catalog.json'), catalog_sha256=sha(ANALYSIS / 'measured_live_curve_catalog.json'),
        claims_isolated_tracking_cost=False, claims_hardware_capacity=False)
    (a.output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    if a.install:
        current = asset / 'current'; archive = asset / 'output/before_actual_clock_curves_2026-10-01'
        if not archive.exists(): shutil.copytree(current, archive)
        for name in ['figure.pdf', 'figure.svg', 'figure.png', 'caption.md', 'provenance.json']:
            shutil.copy2(a.output / name, current / name)
        (current / 'README.md').write_text('# 실제 공통 tracking 시간/학습량 측정\n\n' + caption + '\n')
        shutil.copy2(a.output / 'figure.pdf', PAPER / f'latex/figs/draft/f{number}.pdf')
        shutil.copy2(a.output / 'figure.tex', PAPER / f'latex/fig/f{number}_draft.tex')
    print('MEASURED_LIVE_FIGURE', a.kind, a.output, 'installed', a.install)


if __name__ == '__main__': main()
