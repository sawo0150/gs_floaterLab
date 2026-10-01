#!/usr/bin/env python3
"""Render real PLY covariances as opaque, clipped 2-sigma ellipsoids on CPU.

This is an orthographic geometry display, not a photometric Gaussian splat.
The same camera, cut plane and opacity cutoff apply to both unmodified maps.
The manual empty-space mask determines the view; no quality scores select it.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from plyfile import PlyData

PAPER = Path(__file__).resolve().parents[1]
ROOT = PAPER.parent
sys.path.insert(0, str(ROOT / 'benchmarks/online_gs/campaigns/gain_attribution'))
from evaluate_cvpr_regions import EVALUATOR, MASK, POSES, EXPECTED


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def original_metric():
    spec = importlib.util.spec_from_file_location('unaltered_region_evaluator', EVALUATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rotation_matrices(q):
    q = q / np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-12)
    w, x, y, z = q.T
    r = np.empty((len(q), 3, 3))
    r[:, 0, :] = np.stack([1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)], 1)
    r[:, 1, :] = np.stack([2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)], 1)
    r[:, 2, :] = np.stack([2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)], 1)
    return r


def solid_ellipsoids(xyz, covariance, colors, bounds, cut_z, width=500):
    """Analytic ray/quadric intersection with a z buffer, including cut caps."""
    extent = bounds[1] - bounds[0]
    height = int(round(width * extent[1] / extent[0]))
    xs = np.linspace(bounds[0, 0], bounds[1, 0], width)
    ys = np.linspace(bounds[1, 1], bounds[0, 1], height)
    raster = np.full((height, width, 3), .975)
    zbuffer = np.full((height, width), -np.inf)
    radii = 2 * np.sqrt(np.maximum(np.diagonal(covariance, axis1=1, axis2=2), 0))
    visible = ((xyz[:, :2] + radii[:, :2] >= bounds[0, :2]) &
               (xyz[:, :2] - radii[:, :2] <= bounds[1, :2])).all(1)
    visible &= xyz[:, 2] - radii[:, 2] <= cut_z
    visible &= np.isfinite(covariance).all((1, 2))
    ids = np.flatnonzero(visible)
    light = np.array([-.4, -.25, 1.]); light /= np.linalg.norm(light)
    for i in ids:
        cx, cy, cz = xyz[i]
        x0 = max(0, np.searchsorted(xs, cx-radii[i, 0])-1)
        x1 = min(width, np.searchsorted(xs, cx+radii[i, 0])+1)
        # y rows decrease, whereas searchsorted needs an increasing axis.
        y0 = max(0, height-np.searchsorted(ys[::-1], cy+radii[i, 1])-1)
        y1 = min(height, height-np.searchsorted(ys[::-1], cy-radii[i, 1])+1)
        if x0 >= x1 or y0 >= y1:
            continue
        precision = np.linalg.inv(covariance[i])
        qzz = precision[2, 2]
        if not np.isfinite(qzz) or qzz <= 0:
            continue
        dx, dy = np.meshgrid(xs[x0:x1]-cx, ys[y0:y1]-cy)
        xy_cross = precision[2, 0]*dx + precision[2, 1]*dy
        schur = precision[:2, :2] - np.outer(precision[:2, 2], precision[2, :2]) / qzz
        remain = 4 - (schur[0, 0]*dx*dx + 2*schur[0, 1]*dx*dy + schur[1, 1]*dy*dy)
        root = np.sqrt(np.maximum(remain, 0) / qzz)
        middle = cz - xy_cross/qzz
        front, back = middle+root, middle-root
        depth = np.minimum(front, cut_z)
        hit = (remain >= 0) & (back <= cut_z)
        old = zbuffer[y0:y1, x0:x1]
        write = hit & (depth > old)
        if not write.any():
            continue
        dz = depth-cz
        normal = np.stack([precision[0, 0]*dx + precision[0, 1]*dy + precision[0, 2]*dz,
                           precision[1, 0]*dx + precision[1, 1]*dy + precision[1, 2]*dz,
                           xy_cross+qzz*dz], -1)
        cap = front > cut_z
        normal[cap] = [0, 0, 1]
        normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-12)
        shade = .38 + .62*np.maximum(normal @ light, 0)
        rgb = colors[i][None, None, :] * shade[:, :, None]
        raster[y0:y1, x0:x1][write] = rgb[write]
        old[write] = depth[write]
    return np.rint(np.clip(raster, 0, 1)*255).astype(np.uint8), len(ids)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--region-result', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--install', action='store_true')
    a = p.parse_args()
    for path, expected in EXPECTED.items():
        assert sha(path) == expected
    source = json.loads(a.region_result.read_text())
    module = original_metric()
    region = np.load(MASK)
    mask, voxel, lo = region['mask'].astype(bool), float(region['voxel']), region['lo']
    cells = np.argwhere(mask)
    centers = (cells+.5)*voxel+lo
    bounds = np.array([centers.min(0)-3*voxel, centers.max(0)+3*voxel])
    # A single mask-derived horizontal cut exposes the same interior for all maps.
    cut_z = float(centers[:, 2].min() + .75*np.ptp(centers[:, 2]))
    times, orb_centers = module.load_orb_centres(POSES)
    a.output.mkdir(parents=True, exist_ok=False)
    images, provenance = {}, []
    for label in ['vanilla', 'd3']:
        row = next(r for r in source['runs'] if r['label'] == label)
        run = Path(row['run_dir']); ply = run / '3dgs_before_final.ply'
        assert sha(ply) == row['map_sha256']
        xyz, opacity, scales, quaternions = module.load_gaussians(ply)
        scale, rotation, translation, residual = module.align_run(run, times, orb_centers)
        xyz = scale*(xyz @ rotation.T)+translation
        axes = rotation[None] @ rotation_matrices(quaternions)
        axes = axes * (scale*scales)[:, None, :]
        covariance = axes @ axes.transpose(0, 2, 1)
        inside = module.region_membership(xyz, mask, lo, voxel)
        colors = np.broadcast_to(np.array([.26, .47, .57]), xyz.shape).copy()
        colors[inside] = [.93, .34, .15]
        admitted = opacity > .3
        image, displayed = solid_ellipsoids(xyz[admitted], covariance[admitted], colors[admitted], bounds, cut_z)
        images[label] = image
        Image.fromarray(image).save(a.output / f'{label}_solid_ellipsoids.png')
        provenance.append({'arm': label, 'run': str(run), 'ply_sha256': sha(ply),
            'map_gaussians': len(xyz), 'opacity_filter_pass': int(admitted.sum()), 'displayed_candidates': displayed,
            'mask_centers_alpha_gt_0p3': int((inside & admitted).sum()),
            'registration_median_m': float(np.median(residual)), 'registration_p90_m': float(np.percentile(residual, 90))})
        assert provenance[-1]['mask_centers_alpha_gt_0p3'] == row['counts']['nominal']['opacity_gt_0_3']
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.5, 'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(1, 3, figsize=(3.35, 3.1), gridspec_kw={'width_ratios': [1, 1, 1]})
    for ax, label, title in zip(axes[:2], ['vanilla', 'd3'], ['VIGS-SLAM', 'Ours (D3)']):
        ax.imshow(images[label], extent=[bounds[0, 0], bounds[1, 0], bounds[0, 1], bounds[1, 1]])
        ax.set_title(title, fontsize=7.5, pad=4)
    mask_xy = mask.any(2).T
    axes[2].imshow(mask_xy[::-1], extent=[lo[0], lo[0]+mask.shape[0]*voxel, lo[1], lo[1]+mask.shape[1]*voxel],
                   cmap=matplotlib.colors.ListedColormap(['#fafafa', '#f6d2c4']), vmin=0, vmax=1, interpolation='nearest')
    axes[2].set_title('Manual empty space', fontsize=7.0, pad=4)
    for ax in axes:
        ax.set_xlim(bounds[:, 0]); ax.set_ylim(bounds[:, 1]); ax.set_aspect('equal')
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values(): spine.set_color('#dce3e8'); spine.set_linewidth(.5)
    fig.text(.5, .025, 'Solid 2σ ellipsoids · opacity > 0.3 · shared horizontal cut', ha='center', fontsize=6.5)
    fig.subplots_adjust(left=.015, right=.985, bottom=.075, top=.93, wspace=.08)
    for suffix in ['pdf', 'svg', 'png']:
        fig.savefig(a.output / f'figure.{suffix}', dpi=220)
    plt.close(fig)
    caption = ('Actual Gaussian maps on Aria1253 at 40 training renders/KF, displayed as opaque 2-sigma covariance ellipsoids. '
        'Both maps use the same orthographic view, mask-derived horizontal cut and opacity cutoff. '
        'Orange indicates centers in independently annotated empty space; blue indicates other centers. '
        'The right panel shows the empty-space annotation, not a surface reconstruction. '
        'This is a whole-system comparison; D3 uses additional proxy renders.')
    (a.output / 'caption.md').write_text(caption+'\n')
    (a.output / 'provenance.json').write_text(json.dumps({'kind': 'actual_covariance_solid_ellipsoids',
        'experimental_evidence': True, 'renderer': str(Path(__file__)), 'renderer_sha256': sha(__file__),
        'source_region_result': str(a.region_result), 'source_region_result_sha256': sha(a.region_result),
        'reference': {str(path): sha(path) for path in EXPECTED}, 'reference_used_by_mapper': False,
        'bounds_m': bounds.tolist(), 'cut_z_m': cut_z, 'sigma': 2, 'opacity_cutoff': .3,
        'camera': 'orthographic +ORB-world-z looking downward, +x right, +y up',
        'display_colors': 'region membership, not RGB reconstruction', 'maps_modified': False,
        'scene_selection': 'only scene with independent manual free-space reference; no PSNR-based selection',
        'geometry_loss_isolated': False, 'runs': provenance}, indent=2)+'\n')
    if a.install:
        asset = PAPER / 'figures/figure06_geometry_comparison'
        current = asset / 'current'
        archive = asset / 'output/mockup_before_measured_2026-10-01'
        if not archive.exists(): shutil.copytree(current, archive)
        for name in ['figure.pdf', 'figure.svg', 'figure.png', 'caption.md', 'provenance.json']:
            shutil.copy2(a.output / name, current / name)
        shutil.copy2(current / 'figure.pdf', PAPER / 'latex/figs/draft/f6.pdf')
        (PAPER / 'latex/fig/f6_draft.tex').write_text('\\begin{figure}[tbp]\n  \\centering\n  \\includegraphics[width=\\linewidth]{figs/draft/f6.pdf}\n'
            '  \\caption{Actual Aria1253 maps at 40 training renders/KF as solid $2\\sigma$ covariance ellipsoids. '
            'The view, horizontal cut and opacity cutoff ($>0.3$) are shared. Orange centers lie in the independent manual empty-space mask; blue centers lie outside. '
            'Right: the annotation, not a surface reference. This compares complete systems; D3 adds proxy renders.}\n'
            '  \\label{fig:carve}\n\\end{figure}\n')
    print('SOLID_ELLIPSOIDS', a.output, json.dumps(provenance))


if __name__ == '__main__': main()
