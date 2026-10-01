#!/usr/bin/env python3
"""Scene-centered teaser A from the current merged system's verified assets."""
import argparse
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
from build_measured_tables import read, sha, RESULTS
from build_measured_photometric_figure import evaluated_curve
ASSET = PAPER / 'figures/figure01_teaser'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--capture', type=Path, default=RESULTS / 'cvpr_assets/current_teaser_capture_v1')
    p.add_argument('--output', type=Path, default=ASSET / 'output/current_measured_scene_centered_v1')
    p.add_argument('--install', action='store_true')
    a = p.parse_args()
    source = a.capture / 'provenance.json'; meta = read(source)
    assert meta['source_maps_unchanged'] and meta['optimizer_updates'] == 0
    assert meta['all_candidate_scenes_evaluated_before_selection']
    for name, digest in meta['files'].items(): assert sha(a.capture / name) == digest
    for arm, row in meta['source_runs'].items():
        assert sha(Path(row['map'])) == row['map_sha256']
        assert sha(Path(row['metric'])) == row['metric_sha256']
    curves = {arm: evaluated_curve(Path(row['run'])) for arm, row in meta['source_runs'].items()}
    assert len({r['training_renders'] for r in meta['source_runs'].values()}) == 1
    renders = meta['source_runs']['d3']['training_renders']
    a.output.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.5,
                         'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    fig = plt.figure(figsize=(6.9, 2.5))
    grid = fig.add_gridspec(1, 3, width_ratios=[1.5, 1.05, 1.35], wspace=.36)
    variant = next(r for r in meta['map_variants'] if r['id'] == 'V2')
    ax = fig.add_subplot(grid[0, 0])
    ax.imshow(Image.open(a.capture / variant['image']).convert('RGB'))
    transform = np.array(variant['world_to_camera'])
    fx, fy, cx, cy, width, height = variant['intrinsics']
    def project(points):
        points = np.atleast_2d(points)
        q = points @ transform[:3, :3].T + transform[:3, 3]
        assert (q[:, 2] > 0).all()
        return np.stack([fx * q[:, 0] / q[:, 2] + cx, fy * q[:, 1] / q[:, 2] + cy], axis=1)
    route = project(meta['trajectory_world'])
    ax.plot(route[:, 0], route[:, 1], color='white', linewidth=1.9)
    ax.plot(route[:, 0], route[:, 1], color='#087e8b', linewidth=.85)
    for frustum in meta['camera_frusta']:
        f = project(frustum['corners_world'])
        edge = f[[1, 2, 3, 4, 1]]
        ax.plot(edge[:, 0], edge[:, 1], color='#087e8b', linewidth=.45)
        for corner in f[1:]:
            ax.plot([f[0, 0], corner[0]], [f[0, 1], corner[1]], color='#087e8b', linewidth=.45)
    point = project(meta['roi_center_world'])[0]
    ax.scatter([point[0]], [point[1]], s=95, facecolors='none', edgecolors='#d88729', linewidths=.8)
    ax.set_xlim(100, 1300); ax.set_ylim(980, 250); ax.axis('off')
    ax.set_title('(a) Gaussian map and camera trajectory', fontsize=7.6, pad=6)
    ax.text(.5, -.12, 'Display-only spatial cutaway', transform=ax.transAxes,
            ha='center', va='top', color='#646b71', fontsize=6.8)
    sub = grid[0, 1].subgridspec(2, 2, height_ratios=[1, 1], hspace=.36, wspace=.07)
    for j, (arm, label) in enumerate([('vanilla', 'VIGS-SLAM'), ('d3', 'Ours (D3)')]):
        rgb = Image.open(a.capture / f'{arm}_rgb.png').convert('RGB').crop(tuple(meta['roi']))
        ax = fig.add_subplot(sub[0, j]); ax.imshow(rgb); ax.axis('off'); ax.set_title(label, fontsize=7, pad=4)
        ax = fig.add_subplot(sub[1, j]); ax.imshow(Image.open(a.capture / f'{arm}_depth.png')); ax.axis('off')
    fig.text(.516, .975, '(b) Same-view RGB / rendered depth', ha='center', fontsize=7.6)
    fig.text(.516, .115, 'Depth range: 0.5--4.0 m (shared)', ha='center', fontsize=6.5, color='#646b71')
    ax = fig.add_subplot(grid[0, 2])
    for arm, color, label in [('vanilla', '#737a81', 'VIGS-SLAM'), ('d3', '#087e8b', 'Ours (D3)')]:
        points = curves[arm]
        ax.plot([r['renders'] / 1000 for r in points], [r['psnr'] for r in points],
                color=color, marker='o', markersize=2.4, linewidth=1.3, label=label)
    ax.set_title('(c) Measured photometric convergence', fontsize=7.6, pad=6)
    ax.set_xlabel('Training image-renders (k)', fontsize=7, labelpad=3)
    ax.set_ylabel('Held-out PSNR (dB)', fontsize=7, labelpad=3)
    ax.grid(color='#e4e8eb', linewidth=.5); ax.spines[['top', 'right']].set_visible(False)
    ax.legend(frameon=False, fontsize=6.5, loc='upper left')
    fig.text(.5, .025, f'RPNG {meta["scene"]} / held-out frame {meta["frame"]} / {renders:,} training renders per method',
             ha='center', fontsize=7, color='#646b71')
    fig.subplots_adjust(left=.007, right=.987, top=.88, bottom=.235)
    for suffix in ['pdf', 'svg', 'png']: fig.savefig(a.output / f'figure.{suffix}', dpi=260)
    plt.close(fig)
    caption = ('The proposed mapping system on RPNG ' + meta['scene'] + '. '
        '(a) Actual Gaussian map with estimated camera trajectory; the spatial cutaway is for display only. '
        '(b) Shared held-out RGB details and expected rendered depths from the complete saved maps. '
        '(c) Actual checkpoint PSNR on a fixed uniform held-out subset. '
        f'Both final maps use {renders:,} training image-renders; D3 adds proxy renders. '
        'Rendered depth is qualitative and does not measure independent surface accuracy.')
    (a.output / 'caption.md').write_text(caption + '\n')
    (a.output / 'README.md').write_text('# 실제 현재 구현 기반 A형 teaser\n\n' + caption + '\n')
    (a.output / 'provenance.json').write_text(json.dumps(dict(kind='actual_current_scene_centered_teaser',
        experimental_evidence=True, source=str(source), source_sha256=sha(source),
        scene=meta['scene'], frame=meta['frame'], roi=meta['roi'], curves=curves,
        curve_quality_scope='same uniform64 held-out subset as F3, not full-cohort T1 means',
        all_scenes_evaluated_before_selection=True, budget=40, width='two_columns_user_exception',
        source_map_modified=False, image_content_edited=False, independent_depth_ground_truth=False,
        map_variant=variant, script=str(Path(__file__)), script_sha256=sha(Path(__file__))), indent=2) + '\n')
    if a.install:
        current = ASSET / 'current'; archive = ASSET / 'output/ai_mockup_before_actual_current_teaser_2026-10-01'
        if not archive.exists(): shutil.copytree(current, archive)
        for name in ['figure.pdf', 'figure.svg', 'figure.png', 'caption.md', 'README.md', 'provenance.json']:
            shutil.copy2(a.output / name, current / name)
        shutil.copy2(current / 'figure.pdf', PAPER / 'latex/figs/draft/f1.pdf')
        (PAPER / 'latex/fig/f1_draft.tex').write_text('\\begin{figure*}[tbp]\n  \\centering\n'
            '  \\includegraphics[width=\\linewidth]{figs/draft/f1.pdf}\n'
            '  \\caption{'+caption.replace('_', r'\_')+'}\n  \\label{fig:teaser}\n\\end{figure*}\n')
    print('ACTUAL_TEASER_BUILT', a.output)


if __name__ == '__main__': main()
