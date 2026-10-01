#!/usr/bin/env python3
"""F9 current15/40 RR vs ERVS, gated on all candidate checkpoint pairs.

Original offline15/30/60 interval-ERCB results are a separate regime. A partial
catalog can be generated while GPU work runs; it cannot install a figure.
"""
import argparse
import csv
import json
from pathlib import Path
import shutil
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PAPER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER / 'scripts'))
from build_measured_tables import CANDIDATES, RESULTS, read, sha
from build_measured_photometric_figure import evaluated_curve
ASSET = PAPER / 'figures/figure09_sampling_convergence'


def catalog():
    pairs, points = [], []
    for dataset, scenes in CANDIDATES.items():
        for scene in scenes:
            panel = RESULTS / ('cvpr_assets/fixed_work_12f_v1' if scene == 'aria301_12F' else 'cvpr_assets/fixed_work_v1')
            for budget in [15, 40]:
                paths = {'RR': RESULTS / 'cvpr_assets/current_controls_v1' / f'render{budget}' / dataset / scene / 'rr_dense',
                         'ERVS': panel / f'render{budget}' / dataset / scene / 'd3'}
                pair = dict(dataset=dataset, scene=scene, budget=budget, status='awaiting_checkpoint_pair')
                curves = {}
                for label, run in paths.items():
                    source = run / 'curve_evaluation/summary.json'
                    if not source.exists(): continue
                    states = read(source)
                    usable = [r for r in states if r['status'] == 'evaluated' and r.get('usable_for_convergence_claim')]
                    if len(usable) < 2 or not any(r['checkpoint'].get('final') for r in usable): continue
                    curves[label] = evaluated_curve(run)
                    for point in curves[label]:
                        points.append(dict(dataset=dataset, scene=scene, budget=budget, sampler=label,
                            checkpoint=point['name'], training_renders=point['renders'], psnr_db=point['psnr'],
                            arrival_uid=point['arrival_uid'], final=point['final'],
                            source=str(source), source_sha256=sha(source)))
                if set(curves) == {'RR', 'ERVS'}:
                    manifests = [read(path / 'curve_evaluation/fixed_subset_manifest.json')['views'] for path in paths.values()]
                    assert manifests[0] == manifests[1]
                    for run in paths.values():
                        assert read(run / 'render_result.json')['valid_execution']
                        assert all(r['quality']['mapping_disjoint'] for r in read(run / 'curve_evaluation/summary.json') if r['status'] == 'evaluated')
                    for name in ['traj_full_beforeBA.txt', 'traj_kf_beforeBA.txt']:
                        assert len({sha(path / name) for path in paths.values()}) == 1
                    pair.update(status='measured', curves=curves,
                        final_ervs_minus_rr_db=curves['ERVS'][-1]['psnr'] - curves['RR'][-1]['psnr'])
                pairs.append(pair)
    directory = ASSET / 'analysis'; directory.mkdir(exist_ok=True)
    data = directory / 'current_sampler_curves.csv'
    if points:
        with data.open('w', newline='') as f:
            writer = csv.DictWriter(f, list(points[0])); writer.writeheader(); writer.writerows(points)
    payload = dict(kind='actual_current_sampler_curve_catalog', expected_pairs=40,
        measured_pairs=sum(r['status'] == 'measured' for r in pairs), pairs=pairs,
        complete_candidate_curve_review=all(r['status'] == 'measured' for r in pairs),
        script_sha256=sha(Path(__file__)))
    (directory / 'current_sampler_catalog.json').write_text(json.dumps(payload, indent=2) + '\n')
    return payload, data


def main():
    p = argparse.ArgumentParser(); p.add_argument('--catalog-only', action='store_true')
    p.add_argument('--dataset'); p.add_argument('--scene'); p.add_argument('--selection-reason')
    a = p.parse_args(); source, data = catalog()
    print('CURRENT_SAMPLER_CURVES', source['measured_pairs'], '/', source['expected_pairs'])
    if a.catalog_only: return
    assert source['complete_candidate_curve_review'], 'Evaluate every scene before selecting a sampler example'
    assert a.dataset and a.scene and a.selection_reason
    pairs = [next(r for r in source['pairs'] if (r['dataset'], r['scene'], r['budget']) ==
                  (a.dataset, a.scene, budget)) for budget in [15, 40]]
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7,
                         'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(2, 1, figsize=(3.35, 2.65), sharex=False)
    for ax, pair in zip(axes, pairs):
        for label, color in [('RR', '#737a81'), ('ERVS', '#087e8b')]:
            curve = pair['curves'][label]
            ax.plot([r['renders'] / 1000 for r in curve], [r['psnr'] for r in curve],
                    marker='o', markersize=2.5, linewidth=1.2, color=color, label=label)
        ax.set_title(f"{pair['budget']} training renders/KF", fontsize=7.3, pad=3)
        ax.set_ylabel('Held-out PSNR (dB)', fontsize=7, labelpad=3)
        ax.set_xlabel('Training image-renders (k)', fontsize=6.7, labelpad=2)
        ax.grid(color='#e4e8eb', linewidth=.5); ax.spines[['top', 'right']].set_visible(False)
    axes[0].legend(frameon=False, ncol=2, fontsize=6.5, loc='upper left')
    fig.subplots_adjust(left=.155, right=.985, top=.93, bottom=.14, hspace=.9)
    current = ASSET / 'current'; archive = ASSET / 'output/dummy_before_current_sampler_measurements_2026-10-01'
    if not archive.exists(): shutil.copytree(current, archive)
    for suffix in ['pdf', 'svg', 'png']: fig.savefig(current / f'figure.{suffix}', dpi=240)
    plt.close(fig)
    shutil.copy2(current / 'figure.pdf', PAPER / 'latex/figs/draft/f9.pdf')
    caption = (f'Actual RR versus cumulative-count ERVS convergence on {a.dataset.upper()} {a.scene} '
        'in the current merged mapper at 15 and 40 training renders/KF. All 20 scenes are evaluated before '
        'example selection; dataset means appear in the current-code sampling table. The fixed uniform held-out '
        'subset and input trace are shared. D3 proxy renders are additional work. '
        'This is separate from the original offline15/30/60 interval-ERCB replay.')
    (current / 'caption.md').write_text(caption + '\n')
    (current / 'README.md').write_text('# 실제 현재 sampler 수렴 비교\n\n' + caption + '\n')
    (current / 'provenance.json').write_text(json.dumps(dict(kind='actual_current_sampler_convergence',
        experimental_evidence=True, all_candidates_evaluated=True, selection_reason=a.selection_reason,
        dataset=a.dataset, scene=a.scene, curves=pairs, data=str(data), data_sha256=sha(data),
        original_replay_regime=False, manuscript_width='one_column', script_sha256=sha(Path(__file__))), indent=2) + '\n')
    scene = a.scene.replace('_', r'\_')
    (PAPER / 'latex/fig/f9_draft.tex').write_text('\\begin{figure}[tbp]\n  \\centering\n'
        '  \\includegraphics[width=\\linewidth]{figs/draft/f9.pdf}\n'
        f'  \\caption{{Measured RR/ERVS convergence on {a.dataset.upper()} \\texttt{{{scene}}} at 15/40 training renders/KF '
        'in the current merged mapper. The fixed uniform held-out subset and input trace are shared; D3 adds proxy renders. '
        'Original offline interval ERCB is a separate regime.}\n'
        '  \\label{fig:sampling_convergence}\n\\end{figure}\n')
    print('INSTALLED_ACTUAL_F9', a.dataset, a.scene)


if __name__ == '__main__': main()
