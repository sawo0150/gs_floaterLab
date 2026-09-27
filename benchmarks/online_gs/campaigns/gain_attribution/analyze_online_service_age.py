#!/usr/bin/env python3
"""Post-run service allocation by observation age, never a mapping phase rule.

Rows are wall-clock quarters; columns are sensor-time quarters of input images.
Native RGB services count each image in the batch, not equal-cost Adam steps.
"""
import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def analyze(root):
    runtime_path = root / 'mapping_replay_runtime.json'
    training_path = root / 'online_training.json'
    runtime, report = read(runtime_path), read(training_path)
    if report.get('auxiliary_adam_steps_completed', runtime['auxiliary_adam_steps_completed']) != 0:
        raise ValueError('The service timeline requires Gaussian-only Adam completion records')
    services = [s for g in report['training']['generations'] for s in g['services']]
    times = report['optimizer_completion_times']
    if len(services) != len(times) or len(services) != runtime['main_gaussian_optimizer_steps_completed']:
        raise ValueError('Service records do not match actual optimizer completions')
    archive = Path(runtime['archive'])
    manifest_path = archive / 'archive_manifest.json'
    manifest = read(manifest_path)
    arrivals_path = archive / manifest['arrivals']
    arrivals = [json.loads(line) for line in arrivals_path.read_text().splitlines() if line.strip()]
    inputs = {int(row['frame_uid']): row for row in arrivals}
    first, last = float(arrivals[0]['sensor_timestamp']), float(arrivals[-1]['sensor_timestamp'])
    duration = runtime['budget_seconds']
    started = report['deadline'] - duration
    matrices = {source: [[0] * 4 for _ in range(4)] for source in ('native', 'photometric')}
    native_steps = [0] * 4
    photo_steps = [0] * 4
    for service, completed in zip(services, times):
        q = min(3, max(0, int(4 * (completed - started) / duration)))
        source = service['source']
        (native_steps if source == 'native' else photo_steps)[q] += 1
        for uid in service['uids']:
            row = inputs[int(uid)]
            if row['held_out']:
                raise ValueError('Held-out image in actual service ledger')
            observation_q = min(3, max(0, int(4 * (float(row['sensor_timestamp']) - first) / (last - first))))
            matrices[source][q][observation_q] += 1
    photo_last = matrices['photometric'][-1]
    sources = [runtime_path, training_path, manifest_path, arrivals_path, Path(__file__).resolve()]
    output = {'kind': 'post-run nominal RGB service allocation, not quality or a phase policy',
              'rows': 'elapsed mapping-time quarters', 'columns': 'input sensor-time quarters',
              'native_image_services': matrices['native'], 'photo_image_services': matrices['photometric'],
              'native_steps_by_time_quarter': native_steps, 'photo_steps_by_time_quarter': photo_steps,
              'last_time_quarter_photo_shares': [n / sum(photo_last) for n in photo_last] if sum(photo_last) else None,
              'source_lock': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    (root / 'service_age_diagnostic.json').write_text(json.dumps(output, indent=2) + '\n')
    return {k: v for k, v in output.items() if k != 'source_lock'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.run_dir.resolve()), indent=2))
