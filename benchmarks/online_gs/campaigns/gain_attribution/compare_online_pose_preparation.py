#!/usr/bin/env python3
"""Compare measured preparation work under identical declared online policies."""
import argparse
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def measures(run):
    training = read(run / 'online_training.json')
    visual = read(run / 'visual_pose.json')
    lazy = read(run / 'lazy_refresh.json')
    result = read(run / 'result.json')
    report = {'psnr': result['heldout_psnr'], 'valid': result['valid'],
        'mapping_seconds': result['mapping_seconds'],
        'native_steps': training['native_commits'], 'photo_steps': training['photometric_commits'],
        'photo_seconds_including_preparation': training['training']['photometric_seconds'],
        'refresh_seconds': lazy['refresh_seconds'], 'refreshed_views': lazy['prepared_views'],
        'visual_refinement_seconds': visual['wall_seconds'], 'visual_refinement_calls': len(visual['calls'])}
    if (run / 'sparse_refresh.json').exists():
        report['sparse_refresh'] = read(run / 'sparse_refresh.json')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', default='v12_pose_fit')
    parser.add_argument('--candidate', default='v13_sparse_refresh')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4] / 'results/campaigns/gain_attribution/online_dense_training'
    rows = {}
    for dataset, scene in [('rpng', 'table_06'), ('aria', 'aria1253'), ('utmm', 'square-1')]:
        suffix = Path(dataset) / scene / 'growth_ervs/seed0'
        before, after = root / args.baseline / suffix, root / args.candidate / suffix
        if not (after / 'result.json').exists():
            continue
        if read(before / 'contract.json') != read(after / 'contract.json'):
            raise RuntimeError('Declared online policies differ: ' + dataset)
        a, b = measures(before), measures(after)
        rows[dataset] = {'baseline': a, 'candidate': b,
                         'psnr_delta': b['psnr'] - a['psnr'],
                         'photo_steps_delta': b['photo_steps'] - a['photo_steps'],
                         'refresh_seconds_delta': b['refresh_seconds'] - a['refresh_seconds']}
    report = {'baseline': args.baseline, 'candidate': args.candidate,
              'scenes': rows, 'complete': len(rows) == 3,
              'interpretation': 'Seed0 total-runtime comparison. Stage times/counts are observations, not a proof of the cause of PSNR changes; final repeated-seed quality acceptance remains separate.'}
    (root / args.candidate / 'preparation_comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
