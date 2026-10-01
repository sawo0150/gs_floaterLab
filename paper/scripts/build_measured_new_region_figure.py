#!/usr/bin/env python3
"""F4: real RGB-patch refinement after its first supported observation.

Feature correspondences, reprojection and parallax identify physical patches.
All candidate scenes are examined before GT-structure-only example selection.
This measures quantized PNG ROI appearance in a frozen causal replay, not
independent surface geometry or elapsed-time performance.
"""
import csv
import json
from pathlib import Path
import shutil
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

PAPER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER / 'scripts'))
from build_measured_tables import CANDIDATES, RESULTS, read, sha

ASSET = PAPER / 'figures/figure04_new_region_convergence'
REGIONS = RESULTS / 'cvpr_assets/region_observations_v1'
CATALOG = PAPER / 'figures/figure05_rendering_comparison/analysis/rendering_catalog.json'


def measured_regions():
    summary = read(REGIONS / 'summary.json')
    declared = {(d, s) for d, scenes in CANDIDATES.items() for s in scenes}
    assert {(r['dataset'], r['scene']) for r in summary} == declared
    assert all(r['status'] == 'measured' for r in summary)
    assert read(CATALOG)['complete_candidate_render_review']
    records, candidates = [], []
    for item in summary:
        dataset, scene = item['dataset'], item['scene']
        source = Path(item['output']) / 'regions.json'
        evidence = read(source)
        assert sha(Path(evidence['trajectory'])) == evidence['trajectory_sha256']
        trajectory = np.atleast_2d(np.loadtxt(evidence['trajectory']))
        panel = RESULTS / ('cvpr_assets/fixed_work_12f_v1' if scene == 'aria301_12F' else 'cvpr_assets/fixed_work_v1')
        base = panel / 'render40' / dataset / scene
        states = {arm: read(base / arm / 'curve_evaluation/summary.json') for arm in ['vanilla', 'd3']}
        assert all(any(r['name'] == 'final' and r['status'] == 'evaluated' for r in rows) for rows in states.values())
        for region in evidence['regions']:
            match = region.get('match')
            candidate = dict(dataset=dataset, scene=scene, target_frame=region['target_frame'],
                             crop_rank=region['crop_rank'], gt_structure_score=region['gt_structure_score'],
                             crop=region['crop'], status='unsupported_patch', source=str(source), source_sha256=sha(source))
            candidates.append(candidate)
            if not match or not match['qualifies_as_new_region']:
                if match: candidate['status'] = 'observed_before_new_region_threshold'
                continue
            candidate.update(match=match, status='too_few_later_checkpoints')
            target = region['target_frame']
            box = tuple(region['crop'])
            points = []
            for arm, rows in states.items():
                end = read(base / arm / 'render_result.json')
                for row in rows:
                    if row['status'] != 'evaluated' or not row.get('usable_for_convergence_claim'):
                        continue
                    checkpoint = row['checkpoint']
                    uid = len(trajectory) - 1 if checkpoint.get('final') else checkpoint['arrival_uid']
                    if uid < match['first_observed_frame']: continue
                    q = row['quality']
                    assert q['mapping_disjoint'] and q['mapping_view_overlap_count'] == 0
                    directory = Path(row['output']) / 'images'
                    prediction = directory / f'{target:06d}_render.png'
                    gt = directory / f'{target:06d}_gt.png'
                    assert prediction.exists() and gt.exists()
                    a = np.asarray(Image.open(prediction).convert('RGB').crop(box), dtype=np.float64) / 255
                    b = np.asarray(Image.open(gt).convert('RGB').crop(box), dtype=np.float64) / 255
                    assert a.shape == b.shape and a.size
                    mse = float(np.mean((a - b) ** 2))
                    point = dict(dataset=dataset, scene=scene, target_frame=target, crop_rank=region['crop_rank'],
                        arm=arm, checkpoint=row['name'], prefix_frame=uid,
                        first_supported_frame=match['first_observed_frame'],
                        first_supported_sensor_time=match['first_observed_sensor_time'],
                        prefix_sensor_time=float(trajectory[uid, 0]),
                        sensor_seconds_since_supported_observation=float(trajectory[uid, 0] - match['first_observed_sensor_time']),
                        training_renders=end['render_counts']['training'] if checkpoint.get('final') else checkpoint['training_renders'],
                        png_roi_psnr_db=float(-10 * np.log10(max(mse, 1e-12))),
                        crop=region['crop'], prediction=str(prediction), prediction_sha256=sha(prediction),
                        gt=str(gt), gt_sha256=sha(gt), checkpoint_summary_sha256=sha(base / arm / 'curve_evaluation/summary.json'))
                    assert point['sensor_seconds_since_supported_observation'] >= 0
                    points.append(point)
            counts = {arm: sum(p['arm'] == arm for p in points) for arm in states}
            # At least two real post-observation states for each method, no interpolation.
            if min(counts.values()) < 2: continue
            assert len({p['gt_sha256'] for p in points}) == 1
            candidate.update(status='eligible', point_counts=counts, points=points)
            records.extend(points)
    return records, candidates


def main():
    rows, candidates = measured_regions()
    analysis = ASSET / 'analysis'
    analysis.mkdir(exist_ok=True)
    data = analysis / 'measured_region_psnr.csv'
    assert rows
    with data.open('w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    (analysis / 'region_candidates.json').write_text(json.dumps(candidates, indent=2) + '\n')
    chosen = [max((r for r in candidates if r['dataset'] == dataset and r['status'] == 'eligible'),
                  key=lambda r: r['gt_structure_score']) for dataset in CANDIDATES]
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7, 'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    fig = plt.figure(figsize=(3.35, 3.35))
    grid = fig.add_gridspec(3, 2, width_ratios=[.72, 1.85], hspace=.68, wspace=.35)
    for i, region in enumerate(chosen):
        image = Image.open(region['points'][0]['gt']).convert('RGB').crop(tuple(region['crop']))
        ax = fig.add_subplot(grid[i, 0]); ax.imshow(image); ax.axis('off')
        ax.set_title('GT region', fontsize=6.3, pad=3)
        ax = fig.add_subplot(grid[i, 1])
        for arm, color, label in [('vanilla', '#737a81', 'VIGS-SLAM'), ('d3', '#087e8b', 'Ours (D3)')]:
            points = sorted((p for p in region['points'] if p['arm'] == arm),
                            key=lambda p: p['sensor_seconds_since_supported_observation'])
            ax.plot([p['sensor_seconds_since_supported_observation'] for p in points],
                    [p['png_roi_psnr_db'] for p in points], color=color, label=label,
                    marker='o', markersize=2.5, linewidth=1.2)
        ax.set_title(region['dataset'].upper() + ' / ' + region['scene'], fontsize=6.7, pad=3)
        ax.set_ylabel('ROI PSNR (dB)', fontsize=6.5, labelpad=2)
        ax.grid(color='#e4e8eb', linewidth=.5); ax.spines[['top', 'right']].set_visible(False)
        ax.tick_params(labelsize=6.4, pad=1)
        if i == 0: ax.legend(frameon=False, fontsize=6.1, loc='upper left')
    fig.supxlabel('Sensor seconds after first supported observation', fontsize=7, y=.018)
    fig.subplots_adjust(left=.01, right=.98, top=.94, bottom=.13)
    current = ASSET / 'current'
    archive = ASSET / 'output/mockup_before_actual_region_measurements_2026-10-01'
    if not archive.exists(): shutil.copytree(current, archive)
    for suffix in ['pdf', 'svg', 'png']: fig.savefig(current / f'figure.{suffix}', dpi=240)
    plt.close(fig)
    shutil.copy2(current / 'figure.pdf', PAPER / 'latex/figs/draft/f4.pdf')
    caption = ('Refinement of matched held-out RGB regions at 40 training renders/KF. '
        'The horizontal axis is sensor time after the first supported training-image match, '
        'not wall-clock time. SIFT matches, parallax and reprojection establish physical patch correspondence; '
        'this is not proof that the patch was never visible earlier. Points are actual 8-bit PNG ROI evaluations '
        'at accepted map checkpoints. The three examples are selected by GT structure after reviewing all 20 scenes; '
        'no map-quality score selects a region. D3 adds proxy rendering work. No independent surface-error claim is made.')
    (current / 'caption.md').write_text(caption + '\n')
    (current / 'README.md').write_text('# 실제 새 관측 영역의 RGB 수렴\n\n' + caption + '\n')
    provenance = dict(kind='actual_matched_region_refinement', experimental_evidence=True,
        generator=str(Path(__file__)), generator_sha256=sha(Path(__file__)),
        all_candidate_scenes_reviewed=True, region_source=str(REGIONS),
        region_protocol_sha256=sha(REGIONS / 'protocol.json'),
        catalog_sha256=sha(CATALOG), data=str(data), data_sha256=sha(data),
        inspected_candidate_regions=len(candidates), eligible_regions=sum(r['status'] == 'eligible' for r in candidates),
        selected=chosen, selection='highest GT-structure score among eligible regions per dataset',
        selection_uses_prediction_scores=False, quality='PSNR of quantized RGB PNG ROI, not raw full-frame T1 PSNR',
        time_axis='sensor time in fixed causal replay, not elapsed wall time',
        depth_surface_reference_available=False, manuscript_width='one_column', image_content_modified=False)
    (current / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    (PAPER / 'latex/fig/f4_draft.tex').write_text('\\begin{figure}[tbp]\n  \\centering\n'
        '  \\includegraphics[width=\\linewidth]{figs/draft/f4.pdf}\n'
        '  \\caption{Measured refinement of matched held-out RGB regions. Points show PNG ROI PSNR at actual map checkpoints; '
        'the horizontal axis is sensor time after the first feature-supported observation, not wall-clock time. '
        'GT structure selects examples from all 20 scenes. D3 adds proxy renders.}\n'
        '  \\label{fig:new_region}\n\\end{figure}\n')
    print('INSTALLED_ACTUAL_F4', len(rows), 'points', len(candidates), 'regions',
          [(r['dataset'], r['scene'], r['target_frame'], r['crop_rank']) for r in chosen])


if __name__ == '__main__': main()
