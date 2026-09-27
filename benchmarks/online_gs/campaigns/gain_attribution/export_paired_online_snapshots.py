#!/usr/bin/env python3
"""Export two saved runs with identical evaluation coordinates per snapshot.

Requires identical reference trajectories and identical common online KF poses.
This is evaluation-only; no trajectory or held-out data reaches the mapper.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from export_online_snapshot import export


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def export_pair(left, right):
    roots = [Path(left), Path(right)]
    references = [np.loadtxt(p / 'traj_full_beforeBA.txt') for p in roots]
    if not np.array_equal(*references):
        raise ValueError('Different final reference trajectories require separate analysis')
    manifests = [json.loads((p / 'stream_snapshots/manifest.json').read_text()) for p in roots]
    rows = [m['snapshots'] for m in manifests]
    if [r['file'] for r in rows[0]] != [r['file'] for r in rows[1]]:
        raise ValueError('Captured snapshot schedules differ')
    reports = []
    for pair in zip(*rows):
        paths = [root / 'stream_snapshots' / row['file'] for root, row in zip(roots, pair)]
        states = [torch.load(p, map_location='cpu', weights_only=True) for p in paths]
        keys = sorted(set(states[0]['keyframe_w2c']) & set(states[1]['keyframe_w2c']))
        if len(keys) < 3 or any(not torch.equal(states[0]['keyframe_w2c'][k],
                                               states[1]['keyframe_w2c'][k]) for k in keys):
            raise ValueError('Common online keyframe poses are not identical')
        provenance = {'protocol': 'identical_common_keyframe_gauge_v1',
            'common_keyframe_uids': keys, 'evaluation_only': True,
            'sources': {str(p.resolve()): sha(p) for p in paths},
            'reference_sha256': sha(roots[0] / 'traj_full_beforeBA.txt'),
            'exporter_sha256': sha(Path(__file__)),
            'state_times_seconds': [row['copy_finished_seconds'] for row in pair]}
        outputs = []
        for root, source, state in zip(roots, paths, states):
            output = root / 'stream_evaluation_shared' / source.stem
            # Only the fitting anchors change; Gaussian parameters, training
            # membership, and actual state timestamps stay exactly as captured.
            fit_state = {**state, 'keyframe_w2c': {k: state['keyframe_w2c'][k] for k in keys}}
            export(fit_state, references[0], output)
            (output / 'paired_coordinate_provenance.json').write_text(
                json.dumps(provenance, indent=2) + '\n')
            outputs.append(output)
        if (outputs[0] / 'traj_full_beforeBA.txt').read_bytes() != (
                outputs[1] / 'traj_full_beforeBA.txt').read_bytes():
            raise RuntimeError('Paired exports did not yield identical evaluation coordinates')
        reports.append({'snapshot': paths[0].name, 'common_keyframes': len(keys),
                        'identical_evaluation_trajectory': True,
                        'actual_times_seconds': provenance['state_times_seconds']})
    return reports


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--left', type=Path, required=True)
    parser.add_argument('--right', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_pair(args.left, args.right), indent=2))
