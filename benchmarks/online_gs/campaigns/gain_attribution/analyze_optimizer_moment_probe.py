#!/usr/bin/env python3
"""Summarize sampled training gradients; never use these as quality metrics."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics


def summarize(report):
    if not report['ledger_matches'] or report['heldout_overlap']:
        raise ValueError('Invalid training provenance')
    generation = max(r['generation'] for r in report['records'])
    records = [r for r in report['records'] if r['generation'] == generation]
    bins = defaultdict(list)
    source_rows = defaultdict(list)
    for row in records:
        source_rows[row['source']].append(row)
        for group in row['groups']:
            bins[row['source'], group['name']].append(group)
    groups = []
    for (source, name), values in sorted(bins.items()):
        nonzero = [v for v in values if v['gradient_rms'] > 0]
        ratios = [v['history_delta_rms'] / v['current_delta_rms']
                  for v in nonzero if v['current_delta_rms'] > 0]
        groups.append({'source': source, 'group': name, 'records': len(values),
            'nonzero_records': len(nonzero),
            'median_gradient_rms': statistics.median(v['gradient_rms'] for v in values),
            'median_previous_moment_rms': statistics.median(v['previous_first_moment_rms'] for v in values),
            'median_history_to_current_delta_rms': statistics.median(ratios) if ratios else None,
            'median_gradient_descent_cosine': statistics.median(v['gradient_descent_direction_cosine'] for v in nonzero) if nonzero else None,
            'sampled_group_ascent_fraction': sum(v['gradient_dot_parameter_delta'] > 0 for v in nonzero) / len(nonzero) if nonzero else None,
            'max_adam_prediction_error': max(v['max_adam_prediction_error'] for v in values)})
    sources = {}
    for source, rows in source_rows.items():
        dots = [sum(g['gradient_dot_parameter_delta'] * g['parameter_coordinates'] / g['sample_coordinates']
                    for g in row['groups']) for row in rows]
        sources[source] = {'records': len(rows),
            'median_batch_views': statistics.median(r['batch_views'] for r in rows),
            'median_service_step': statistics.median(r['next_service_step'] for r in rows),
            'estimated_whole_model_ascent_fraction': sum(d > 0 for d in dots) / len(dots)}
    return {'generation': generation, 'sources': sources, 'groups': groups,
        'limitations': 'Different sampled training steps, not paired gradients at one model. Strided-coordinate RMS/directional estimates, not held-out quality or causal attribution. Group ascent does not imply whole-model loss increase.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    sources, rows = {}, []
    for path in sorted(args.root.glob('*/*/optimizer_probe.json')):
        sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        summary = summarize(json.loads(path.read_text()))
        summary.update(dataset=path.parent.parent.name, scene=path.parent.name)
        rows.append(summary)
    result = {'scenes': rows, 'source_lock': sources, 'quality_claim': False}
    (args.root / 'gradient_summary.json').write_text(json.dumps(result, indent=2) + '\n')
    for row in rows:
        print(row['dataset'], row['sources'])
        for g in row['groups']:
            if g['group'] in ('xyz', 'f_dc', 'opacity'):
                print(g)


if __name__ == '__main__':
    main()
