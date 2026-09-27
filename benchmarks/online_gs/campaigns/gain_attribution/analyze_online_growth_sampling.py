#!/usr/bin/env python3
"""Compare v15 membership and sampling policies on identical held-out cohorts."""
import hashlib
import json
from pathlib import Path
from analyze_online_paired_endpoints import read_views
from analyze_online_service_age import analyze as service_age
import run_online_dense_training as trial


def comparison(left, right):
    if left.keys() != right.keys():
        raise ValueError('Ablation cohorts differ')
    keys = sorted(left)
    return {'mean_delta': sum(left[k] - right[k] for k in keys) / len(keys),
            'filename_order_quarter_deltas': [
                sum(left[k] - right[k] for k in keys[q * len(keys) // 4:(q + 1) * len(keys) // 4])
                / len(keys[q * len(keys) // 4:(q + 1) * len(keys) // 4]) for q in range(4)]}


def main():
    rows, all_locks = [], {}
    for dataset, scene in trial.SCENES:
        arms, views = {}, {}
        for arm in ('kf_only', 'growth_ervs', 'growth_rr', 'immediate_rr'):
            tag = 'v15_image_residency' if arm in ('kf_only', 'growth_ervs') else 'v15_growth_sampling'
            run = trial.ROOT / tag / dataset / scene / arm / 'seed0'
            if not (run / 'result.json').exists():
                continue
            result = trial.common.read(run / 'result.json')
            arms[arm] = {'result': result}
            if not result['valid']:
                continue
            views[arm], locks = read_views(run)
            all_locks.update(locks)
            age = service_age(run)
            report = trial.common.read(run / 'online_training.json')
            arms[arm].update(photo_steps=report['photometric_commits'], native_steps=report['native_commits'],
                            photo_seconds=report['training']['photometric_seconds'],
                            last_time_quarter_photo_shares=age['last_time_quarter_photo_shares'])
        row = {'dataset': dataset, 'scene': scene, 'arms': arms, 'comparisons': {}}
        for left, right, label in [('growth_ervs', 'growth_rr', 'ERVS_minus_RR'),
                                    ('growth_rr', 'immediate_rr', 'Growth_minus_immediate'),
                                    ('growth_rr', 'kf_only', 'Growth_RR_minus_KF'),
                                    ('immediate_rr', 'kf_only', 'Immediate_RR_minus_KF')]:
            if left in views and right in views:
                row['comparisons'][label] = comparison(views[left], views[right])
        rows.append(row)
    output = {'complete': all(len(r['arms']) == 4 for r in rows), 'scenes': rows,
              'all_completed_contracts_pass': all(a['result']['valid'] for r in rows for a in r['arms'].values()),
              'source_lock': {**all_locks, str(Path(__file__).resolve()): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              'final_acceptance': False,
              'limitations': 'Seed0 whole-clock ablation; endpoint quarters are not a stream quality curve or causal proof of forgetting.'}
    trial.common.write(trial.ROOT / 'v15_growth_sampling/analysis.json', output)
    print(json.dumps({r['dataset']: r['comparisons'] for r in rows}, indent=2))


if __name__ == '__main__':
    main()
