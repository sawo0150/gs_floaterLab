#!/usr/bin/env python3
"""Summarize the remeasured controls and image traffic without claiming acceptance."""
import json
from pathlib import Path
import run_online_dense_training as trial


def summarize():
    root = trial.ROOT / 'v15_image_residency'
    rows = []
    for dataset, scene in trial.SCENES:
        arms = {}
        for arm in ('growth_ervs', 'kf_only', 'production'):
            run = root / dataset / scene / arm / 'seed0'
            if not (run / 'result.json').exists():
                continue
            result = trial.common.read(run / 'result.json')
            report = trial.common.read(run / 'online_training.json')
            item = {'result': result}
            if arm != 'production':
                training = report['training']
                item.update(native_steps=report['native_commits'],
                            photo_steps=report['photometric_commits'],
                            photo_seconds=training['photometric_seconds'],
                            image_audit=training['image_audit'])
                old_tag = 'v14_photo_counts' if arm == 'growth_ervs' else 'v10_setup_clock'
                old = trial.ROOT / old_tag / dataset / scene / arm / 'seed0'
                previous = trial.common.read(old / 'result.json')
                old_report = trial.common.read(old / 'online_training.json')
                item['previous'] = {
                    'tag': old_tag,
                    'heldout_psnr': previous['heldout_psnr'],
                    'photo_steps': old_report['photometric_commits'],
                    'delta_psnr': result['heldout_psnr'] - previous['heldout_psnr'],
                    'delta_photo_steps': report['photometric_commits'] - old_report['photometric_commits']}
            arms[arm] = item
        row = {'dataset': dataset, 'scene': scene, 'arms': arms}
        if len(arms) == 3:
            candidate = arms['growth_ervs']['result']['heldout_psnr']
            row['delta_vs_kf'] = candidate - arms['kf_only']['result']['heldout_psnr']
            row['delta_vs_production'] = candidate - arms['production']['result']['heldout_psnr']
        rows.append(row)
    complete = all(len(row['arms']) == 3 for row in rows)
    output = {'complete': complete, 'scenes': rows,
              'all_completed_contracts_pass': all(a['result']['valid'] for r in rows for a in r['arms'].values()),
              'final_acceptance': False,
              'limitations': 'Seed0 exploration; repeated seeds, component ablations, stream curves and live worker integration remain pending.'}
    if complete:
        output['mean_delta_vs_kf'] = sum(r['delta_vs_kf'] for r in rows) / len(rows)
        output['mean_delta_vs_production'] = sum(r['delta_vs_production'] for r in rows) / len(rows)
    trial.common.write(root / 'summary.json', output)
    return output


if __name__ == '__main__':
    print(json.dumps(summarize(), indent=2))
