#!/usr/bin/env python3
"""Export candidate and controls in one common evaluation gauge per state.

Post-run evaluation only. This does not certify that a similarity transform
fully removes nonrigid online trajectory drift; residuals stay in every export.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import torch
from export_online_snapshot import export
from export_paired_online_snapshots import sha


def export_group(roots, *, identical_anchor_subset=False):
    roots = [Path(root).resolve() for root in roots]
    if len(roots) < 2 or len(set(roots)) != len(roots):
        raise ValueError('Need at least two distinct runs')
    references = [np.loadtxt(root / 'traj_full_beforeBA.txt') for root in roots]
    if any(not np.array_equal(references[0], ref) for ref in references[1:]):
        raise ValueError('Final reference trajectories differ')
    rows = [json.loads((root / 'stream_snapshots/manifest.json').read_text())['snapshots']
            for root in roots]
    names = [row['file'] for row in rows[0]]
    if not names or any([row['file'] for row in group] != names for group in rows[1:]):
        raise ValueError('Captured snapshot schedules differ or are empty')
    reports = []
    for group in zip(*rows):
        paths = [root / 'stream_snapshots' / row['file'] for root, row in zip(roots, group)]
        states = [torch.load(path, map_location='cpu', weights_only=True) for path in paths]
        common = sorted(set.intersection(*(set(state['keyframe_w2c']) for state in states)))
        differences = {key:max(float((states[0]['keyframe_w2c'][key]-state['keyframe_w2c'][key]).abs().max())
                              for state in states[1:]) for key in common}
        keys = [key for key in common if differences[key] == 0.] if identical_anchor_subset else common
        if len(keys) < 3 or any(differences[key] != 0. for key in keys):
            raise ValueError('Common online keyframe poses are insufficient or differ')
        outputs = [root / 'stream_evaluation_shared' / path.stem for root, path in zip(roots, paths)]
        if any(output.exists() for output in outputs):
            raise FileExistsError('Preserve existing exports; do not overwrite a different gauge')
        provenance = {'protocol': 'identical_common_keyframe_group_gauge_v1',
            'common_keyframe_uids': keys, 'evaluation_only': True,
            'identical_anchor_subset': identical_anchor_subset,
            'all_common_keyframe_uids': common,
            'excluded_pose_differences': {key:value for key,value in differences.items() if key not in keys},
            'sources': {str(path): sha(path) for path in paths},
            'reference_sha256': sha(roots[0] / 'traj_full_beforeBA.txt'),
            'exporter_path': str(Path(__file__).resolve()), 'exporter_sha256': sha(Path(__file__)),
            'state_times_seconds': [row['copy_finished_seconds'] for row in group]}
        alignments = []
        for state, output in zip(states, outputs):
            fit = {**state, 'keyframe_w2c': {key: state['keyframe_w2c'][key] for key in keys}}
            alignments.append(export(fit, references[0], output))
            (output / 'paired_coordinate_provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
        first = (outputs[0] / 'traj_full_beforeBA.txt').read_bytes()
        if any((output / 'traj_full_beforeBA.txt').read_bytes() != first for output in outputs[1:]):
            raise RuntimeError('Exported evaluation coordinates differ')
        reports.append({'snapshot': paths[0].name, 'run_count': len(roots),
                        'common_keyframes': len(keys), 'identical_evaluation_trajectory': True,
                        'actual_times_seconds': provenance['state_times_seconds'],
                        'alignment': alignments[0], 'alignment_quality_accepted': False})
        reports[-1]['excluded_pose_differences'] = provenance['excluded_pose_differences']
    return reports


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dirs', type=Path, nargs='+', required=True)
    parser.add_argument('--identical-anchor-subset', action='store_true')
    args = parser.parse_args()
    print(json.dumps(export_group(args.run_dirs, identical_anchor_subset=args.identical_anchor_subset), indent=2))
