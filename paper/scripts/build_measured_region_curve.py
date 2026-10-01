#!/usr/bin/env python3
"""Replace F7 dummy curves with actual independent region diagnostics."""
import csv
import hashlib
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PAPER = Path(__file__).resolve().parents[1]
ROOT = PAPER.parent
SOURCE = ROOT / 'results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region_curve40_v2.json'
ASSET = PAPER / 'figures/figure07_geometry_convergence'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    data = json.loads(SOURCE.read_text())
    assert not data['reference_used_by_mapper']
    rows = []
    for r in data['rows']:
        if r['status'] != 'evaluated' or not r.get('alignment_accepted'): continue
        rows.append({'arm': r['arm'], 'checkpoint': r['name'], 'training_renders': r['training_renders'],
            'gaussians': r['gaussians'], 'region_centers_alpha_gt_0p3': r['initial_shared_region']['centers_alpha_gt_0p3'],
            'region_opacity_support': r['initial_shared_region']['opacity_support_mass'],
            'full_mask_frustum_fraction': r['frustum_covered_mask_fraction'],
            'source_sha256': r['source_sha256']})
    assert len(rows) == 14
    analysis = ASSET / 'analysis'; analysis.mkdir(exist_ok=True)
    csv_path = analysis / 'measured_region_curve.csv'
    with csv_path.open('w', newline='') as f:
        writer = csv.DictWriter(f, list(rows[0])); writer.writeheader(); writer.writerows(rows)
    current = ASSET / 'current'
    archive = ASSET / 'output/dummy_before_measured_2026-10-01'
    if not archive.exists(): shutil.copytree(current, archive)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.5, 'axes.labelsize': 7.5,
                         'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(2, 1, figsize=(3.35, 2.95), sharex=True)
    for arm, color, label in [('vanilla', '#737a81', 'VIGS-SLAM'), ('d3', '#087e8b', 'Ours (D3)')]:
        samples = sorted((r for r in rows if r['arm']==arm), key=lambda r:r['training_renders'])
        x = [r['training_renders']/1000 for r in samples]
        axes[0].plot(x, [r['region_opacity_support'] for r in samples], marker='o', markersize=3,
                     linewidth=1.35, color=color, label=label)
        axes[1].plot(x, [r['gaussians']/1000 for r in samples], marker='o', markersize=3,
                     linewidth=1.35, color=color, label=label)
    axes[0].set_ylabel(r'Free-space support $M_\alpha$')
    axes[0].legend(frameon=False, ncol=2, loc='upper right', fontsize=7)
    axes[0].margins(y=.2)
    axes[1].set_ylabel('Map Gaussians (k)')
    axes[1].set_xlabel('Completed training image-renders (k)')
    for ax in axes:
        ax.grid(color='#e4e8eb', linewidth=.5)
        ax.spines[['top','right']].set_visible(False)
    fig.tight_layout(pad=.7, h_pad=.75)
    for suffix in ['pdf','svg','png']: fig.savefig(current / f'figure.{suffix}', dpi=220)
    plt.close(fig)
    shutil.copy2(current / 'figure.pdf', PAPER / 'latex/figs/draft/f7.pdf')
    caption = ('Independent free-space diagnostics during mapping on Aria1253. '
        'Top: opacity-weighted seven-point covariance support in a fixed manual region within the shared first-checkpoint camera frusta. '
        'Bottom: total map Gaussian count. Markers are actual immutable checkpoints; map growth can increase the error. '
        'The fixed region covers 71.8% of the manual annotation; frustum inclusion does not test occlusion or surface completeness. '
        'This compares complete systems; D3 proxy renders are extra work. No within-run wall-clock curve or isolated-loss comparison is implied.')
    (current / 'caption.md').write_text(caption+'\n')
    (current / 'provenance.json').write_text(json.dumps({'kind':'actual_independent_region_checkpoints',
        'experimental_evidence':True, 'data':str(csv_path), 'data_sha256':sha(csv_path),
        'source':str(SOURCE), 'source_sha256':sha(SOURCE), 'rows':rows,
        'fixed_region':data['initial_shared_region'], 'manuscript_width':'one_column',
        'geometry_loss_isolated':False, 'surface_completeness_available':False,
        'remaining_work':'native geometry recipe control and wall-clock checkpoint axis'}, indent=2)+'\n')
    (PAPER / 'latex/fig/f7_draft.tex').write_text('\\begin{figure}[tbp]\n  \\centering\n  \\includegraphics[width=\\linewidth]{figs/draft/f7.pdf}\n'
        '  \\caption{Independent free-space diagnostics on Aria1253. Top: opacity-weighted covariance support in a fixed manual region within shared first-checkpoint camera frusta (71.8\\% of the annotation). Bottom: map size. '
        'Markers are actual checkpoints; map growth can increase the error. Frustum inclusion does not establish surface visibility or completeness. This compares complete systems; D3 adds proxy renders.}\n'
        '  \\label{fig:geometry_convergence}\n\\end{figure}\n')
    print('Installed F7: fourteen actual states; no dummy data or surface-completeness claim.')


if __name__ == '__main__': main()
