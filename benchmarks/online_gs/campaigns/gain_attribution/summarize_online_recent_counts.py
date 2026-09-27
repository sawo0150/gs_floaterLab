#!/usr/bin/env python3
"""Compare recent-count ERVS with lifetime ERVS, RR and both v15 controls."""
import json
from pathlib import Path
from analyze_online_paired_endpoints import read_views
from analyze_online_growth_sampling import comparison
from analyze_online_service_age import analyze as service_age
import run_online_dense_training as trial


def main():
    rows = []
    root = trial.ROOT / 'v16_recent_counts'
    for dataset, scene in trial.SCENES:
        run = root / dataset / scene / 'growth_ervs/seed0'
        if not (run / 'result.json').exists():
            continue
        result = trial.common.read(run / 'result.json')
        row = {'dataset': dataset, 'scene': scene, 'result': result, 'comparisons': {}}
        if result['valid']:
            candidate, locks = read_views(run)
            report = trial.common.read(run / 'online_training.json')
            age = service_age(run)
            row.update(photo_steps=report['photometric_commits'], native_steps=report['native_commits'],
                       recent_count_audit=report['recent_count_history_matches_services'],
                       last_time_quarter_photo_shares=age['last_time_quarter_photo_shares'])
            for tag, arm, label in [('v15_image_residency', 'growth_ervs', 'versus_lifetime_ERVS'),
                                    ('v15_growth_sampling', 'growth_rr', 'versus_RR'),
                                    ('v15_image_residency', 'kf_only', 'versus_KF'),
                                    ('v15_image_residency', 'production', 'versus_production')]:
                other = trial.ROOT / tag / dataset / scene / arm / 'seed0'
                baseline, more_locks = read_views(other)
                locks.update(more_locks)
                row['comparisons'][label] = comparison(candidate, baseline)
            row['source_lock'] = locks
        rows.append(row)
    output = {'complete': len(rows) == 3, 'scenes': rows,
              'all_completed_contracts_pass': all(r['result']['valid'] for r in rows),
              'final_acceptance': False,
              'limitations': 'Exploratory seed0; paired endpoints do not establish fast convergence or repeatability. Final controls require the final source.'}
    if len(rows) == 3 and output['all_completed_contracts_pass']:
        output['mean_deltas'] = {k: sum(r['comparisons'][k]['mean_delta'] for r in rows) / 3
                                for k in rows[0]['comparisons']}
    trial.common.write(root / 'summary.json', output)
    print(json.dumps({r['dataset']: {'psnr': r['result']['heldout_psnr'],
                     'comparisons': r['comparisons'], 'valid': r['result']['valid']} for r in rows}, indent=2))


if __name__ == '__main__':
    main()
