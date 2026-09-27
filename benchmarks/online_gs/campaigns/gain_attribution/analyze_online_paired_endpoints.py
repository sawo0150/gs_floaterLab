#!/usr/bin/env python3
"""Describe fixed-cohort endpoint differences; never infer a convergence curve."""
import argparse
import hashlib
import json
from pathlib import Path
import run_online_dense_training as trial


def read_views(run):
    result_path = run / 'result.json'
    result = trial.common.read(result_path)
    if not result['valid']:
        raise ValueError('Invalid mapping run: ' + str(run))
    path = run / 'psnr/strict_fixed_manifest/final_result.json'
    rows = [r for r in trial.common.read(path)['per_view'] if r['predeclared_fixed_manifest_split']]
    views = {str(r['uid']): float(r['psnr']) for r in rows}
    if not views or len(views) != len(rows):
        raise ValueError('Missing or duplicate evaluation images')
    if abs(sum(views.values()) / len(views) - result['heldout_psnr']) > 1e-8:
        raise ValueError('Reported endpoint disagrees with the fixed cohort')
    return views, {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (path, result_path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', default='v15_image_residency')
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--scene', required=True)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()
    root = trial.ROOT / args.tag / args.dataset / args.scene
    candidate, lock_a = read_views(root / 'growth_ervs' / f'seed{args.seed}')
    baseline, lock_b = read_views(root / 'kf_only' / f'seed{args.seed}')
    if candidate.keys() != baseline.keys():
        raise ValueError('Candidate and KF-only evaluation cohorts differ')
    keys = sorted(candidate)
    deltas = [candidate[k] - baseline[k] for k in keys]
    output = {'kind': 'post-run held-out endpoint diagnostic; never training input or a policy rule',
              'view_count': len(keys), 'improved_views': sum(d > 0 for d in deltas),
              'mean_delta': sum(deltas) / len(deltas), 'filename_order_quarters': [],
              'source_lock': {**lock_a, **lock_b,
                  str(Path(__file__).resolve()): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              'stream_convergence_claim': False}
    for q in range(4):
        subset = keys[q * len(keys) // 4:(q + 1) * len(keys) // 4]
        if subset:
            output['filename_order_quarters'].append({
                'first_filename': subset[0], 'last_filename': subset[-1],
                'mean_delta': sum(candidate[k] - baseline[k] for k in subset) / len(subset)})
    trial.common.write(root / f'paired_endpoint_seed{args.seed}.json', output)
    print(json.dumps({k: v for k, v in output.items() if k != 'source_lock'}, indent=2))


if __name__ == '__main__':
    main()
