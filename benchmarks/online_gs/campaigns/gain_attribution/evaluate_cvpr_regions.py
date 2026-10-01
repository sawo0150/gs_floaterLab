#!/usr/bin/env python3
"""Evaluate immutable maps against the existing independent manual region.

These diagnostics measure opacity in annotated empty space, not dense surface
accuracy. The reference and ORB trajectory are never supplied to the mapper.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from collect_cvpr_assets import ROOT, RESULTS, read, write, sha

ASSETS = Path('/home/intern/VIGS-SLAM-paper-full/exp70_axes/region_gt')
EVALUATOR = ASSETS.parent / 'evaluate_manual_floater_regions.py'
MASK = ASSETS / '1253_region_gt.npz'
POSES = ASSETS / 'aria1253_orb_keyframes.jsonl'
EXPECTED = {
    MASK: '2caae887350ba59aa1d80486a8f370dfcc119b58931af07afbe08e30e508359c',
    POSES: '814bdf340efcac85d01f4e4c3ccc6e0f1d83f5367a9814fc71ceebc891678abe',
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('runs', nargs='+', help='LABEL=RUN_DIRECTORY')
    a = p.parse_args()
    for path, expected in EXPECTED.items():
        assert sha(path) == expected, path
    labelled = [(label, Path(path).resolve()) for label, path in (r.split('=', 1) for r in a.runs)]
    spec = importlib.util.spec_from_file_location('original_manual_region', EVALUATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.evaluate('aria1253', labelled, POSES, MASK)
    for row in result['runs']:
        run = Path(row['run_dir'])
        mpath = run / 'psnr/strict_fixed_manifest/final_result.json'
        metrics = read(mpath)
        q = metrics['predeclared_fixed_manifest_posthoc']
        assert q['mapping_disjoint'] and q['mapping_view_overlap_count'] == 0
        assert row['alignment_pairs'] >= 3
        row.update(heldout_quality=q, metric_path=str(mpath), metric_sha256=sha(mpath),
                   map_sha256=sha(run / '3dgs_before_final.ply'),
                   pose_sha256=sha(run / 'traj_kf_beforeBA.txt'),
                   registration_p90_in_voxels=row['alignment_p90_m'] / result['mask_voxel_m'])
    result.update(provenance={
        'evaluator': str(EVALUATOR), 'evaluator_sha256': sha(EVALUATOR),
        'script': str(Path(__file__)), 'script_sha256': sha(Path(__file__)),
        'assets': {str(path): sha(path) for path in EXPECTED},
        'evaluation_only': True, 'reference_used_by_mapper': False,
        'independent_reference': 'pre-existing manually annotated empty-space voxel mask',
        'dense_surface_accuracy_completeness_fscore': 'NA; this mask contains no dense surface reference',
        'selection_uses_quality_scores': False,
    })
    if a.output.exists():
        raise FileExistsError(a.output)
    write(a.output, result)
    from run_cvpr_measurements import journal
    for row in result['runs']:
        journal({'dataset': 'aria', 'scene': 'aria1253', 'budget': 'region',
                 'arm': row['label'], 'status': 'evaluated',
                 'psnr': row['heldout_quality']['mean_psnr'], 'output': str(a.output)})
    print(json.dumps([{ 'arm': r['label'], 'nominal_count_alpha_gt_0p3': r['counts']['nominal']['opacity_gt_0_3'],
                       'nominal_opacity_support': r['counts']['nominal']['opacity_support_mass'],
                       'registration_median_m': r['alignment_median_m'], 'registration_p90_m': r['alignment_p90_m']}
                      for r in result['runs']], indent=2))


if __name__ == '__main__':
    main()
