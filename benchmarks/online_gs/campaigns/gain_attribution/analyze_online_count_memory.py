#!/usr/bin/env python3
"""Counterfactual next-draw probabilities on v15 final pools, not a quality test."""
from pathlib import Path
import hashlib
import json
import sys
import run_online_dense_training as trial

sys.path.insert(0, str(trial.BACKEND / 'vigs'))
from online_view_training import ervs_probabilities
from recent_selection_counts import prospective_recent_counts


def main():
    base = trial.ROOT / 'v15_image_residency'
    rows, locks = [], {}
    for dataset, scene in trial.SCENES:
        run = base / dataset / scene / 'growth_ervs/seed0'
        report_path, runtime_path = run / 'online_training.json', run / 'mapping_replay_runtime.json'
        report, runtime = trial.common.read(report_path), trial.common.read(runtime_path)
        generation = report['training']['generations'][-1]
        policy = generation['policy']
        uids = sorted(int(k) for k in policy['photometric_counts'])
        photo = [s for s in generation['services'] if s['source'] == 'photometric']
        if any(len(s['uids']) != 1 for s in photo):
            raise ValueError('Counterfactual expects single-image photometric steps')
        history = [int(s['uids'][0]) for s in photo]
        recent = prospective_recent_counts(history, uids)
        archive = Path(runtime['archive'])
        manifest_path = archive / 'archive_manifest.json'
        arrivals_path = archive / trial.common.read(manifest_path)['arrivals']
        arrivals = [json.loads(line) for line in arrivals_path.read_text().splitlines() if line.strip()]
        lookup = {int(r['frame_uid']): r for r in arrivals}
        start, end = arrivals[0]['sensor_timestamp'], arrivals[-1]['sensor_timestamp']
        groups = [min(3, int(4 * (lookup[k]['sensor_timestamp'] - start) / (end - start))) for k in uids]
        row = {'dataset': dataset, 'pool_size': len(uids), 'recent_selection_window_size': len(uids),
               'counterfactual_only': True, 'policy_was_not_run': True,
               'rules': 'Retain the last N-1 committed photo selections before one hypothetical next choice. Training membership remains entire history.'}
        for name, counts in [('lifetime', [policy['photometric_counts'][str(k)] for k in uids]),
                             ('recent_one_pool_pass', [recent[k] for k in uids])]:
            probabilities = ervs_probabilities(counts, policy['effective_tau'])
            row[name] = {'count_range': [min(counts), max(counts)],
                         'probability_by_input_quarter': [sum(p for p, q in zip(probabilities, groups) if q == i) for i in range(4)]}
        rows.append(row)
        for p in (report_path, runtime_path, manifest_path, arrivals_path):
            locks[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (Path(__file__).resolve(), trial.BACKEND / 'vigs/recent_selection_counts.py',
              trial.BACKEND / 'vigs/online_view_training.py'):
        locks[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    output = {'rows': rows, 'quality_claim': False, 'training_modified': False, 'source_lock': locks}
    trial.common.write(base / 'count_memory_counterfactual.json', output)
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
