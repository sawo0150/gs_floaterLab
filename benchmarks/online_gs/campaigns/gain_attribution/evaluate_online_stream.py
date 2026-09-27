#!/usr/bin/env python3
"""Evaluate saved online states on one fixed held-out cohort after mapping.

No model refinement is performed. Alignment residuals remain in the output;
earliest sampled threshold attainment must not be called exact first attainment.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import run_online_dense_training as trial


def fixed_rows(result):
    rows = [row for row in result['per_view'] if row['predeclared_fixed_manifest_split']]
    if not rows or len({row['uid'] for row in rows}) != len(rows):
        raise ValueError('Missing or duplicate fixed evaluation views')
    return sorted(rows, key=lambda row: row['uid'])


def point(result, seconds, *, alignment=None, steps=None):
    rows = fixed_rows(result)
    values = [float(row['psnr']) for row in rows]
    if not all(math.isfinite(v) for v in values):
        raise ValueError('Nonfinite fixed-view quality')
    return {'seconds': float(seconds), 'optimizer_steps': steps,
            'mean_heldout_psnr': sum(values) / len(values),
            'view_uids': [row['uid'] for row in rows], 'per_view_psnr': values,
            'alignment': alignment}


def assemble_curve(points):
    points = sorted(points, key=lambda row: row['seconds'])
    if len(points) < 2:
        raise ValueError('A final result alone is not a stream-quality curve')
    uids = points[0]['view_uids']
    for i, row in enumerate(points):
        if not math.isfinite(row['seconds']) or row['seconds'] < 0:
            raise ValueError('Invalid state availability time')
        if row['view_uids'] != uids:
            raise ValueError('Evaluation cohort changed across online states')
        if i and row['seconds'] <= points[i - 1]['seconds']:
            raise ValueError('Duplicate or invalid state times')
    return {'protocol': 'fixed_cohort_online_quality_v1', 'view_count': len(uids),
            'cohort_sha256': hashlib.sha256(json.dumps(uids).encode()).hexdigest(),
            'points': points, 'mapping_received_evaluator_inputs': False,
            'exact_first_attainment_claim': False,
            'coordinate_alignment_quality_accepted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--scene', required=True)
    parser.add_argument('--shared-coordinates', action='store_true')
    args = parser.parse_args()
    root = args.run_dir.resolve()
    if not (root / 'result.json').exists():
        raise ValueError('Mapping and final evaluation must finish first')
    import torch
    import numpy as np
    from export_online_snapshot import export
    snapshot_manifest = trial.common.read(root / 'stream_snapshots/manifest.json')
    fixed_manifest = trial.BASE.sequence_paths(args.dataset, args.scene)['fixed_manifest']
    records = []
    for row in snapshot_manifest['snapshots']:
        source = root / 'stream_snapshots' / row['file']
        subdir = 'stream_evaluation_shared' if args.shared_coordinates else 'stream_evaluation'
        output = root / subdir / source.stem
        if not output.exists():
            if args.shared_coordinates:
                raise ValueError('Export the pair in common coordinates before evaluation')
            state = torch.load(source, map_location='cpu', weights_only=True)
            export(state, np.loadtxt(root / 'traj_full_beforeBA.txt'), output)
        # Lock both original state and generated evaluation artifacts before
        # running the existing independently repeated dataset-specific evaluator.
        sources = [source, root / 'traj_full_beforeBA.txt', Path(__file__),
                   Path(__file__).with_name('export_online_snapshot.py'),
                   Path(__file__).with_name('snapshot_camera_alignment.py'),
                   output / 'snapshot_alignment.json']
        sources += [output / name for name in ('3dgs_before_final.ply',
                    'traj_full_beforeBA.txt', 'mapped_uids.json')]
        if args.shared_coordinates:
            sources += [output / 'paired_coordinate_provenance.json',
                        Path(__file__).with_name('export_paired_online_snapshots.py')]
            provenance = trial.common.read(output / 'paired_coordinate_provenance.json')
            if provenance.get('protocol') == 'identical_common_keyframe_group_gauge_v1':
                exporter = Path(__file__).with_name('export_group_online_snapshots.py').resolve()
                if (provenance.get('exporter_path') != str(exporter)
                        or hashlib.sha256(exporter.read_bytes()).hexdigest() != provenance['exporter_sha256']):
                    raise RuntimeError('Group exporter changed after shared export')
                sources.append(exporter)
            if str(source.resolve()) not in provenance['sources']:
                raise RuntimeError('Shared export does not name this snapshot')
            for name, expected in provenance['sources'].items():
                if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
                    raise RuntimeError('Original paired snapshot changed after export')
            if hashlib.sha256((root / 'traj_full_beforeBA.txt').read_bytes()).hexdigest() != provenance['reference_sha256']:
                raise RuntimeError('Reference trajectory changed after shared export')
        lock = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
        path = output / 'stream_source_lock.json'
        if path.exists() and trial.common.read(path) != lock:
            raise RuntimeError('Snapshot/evaluation source changed')
        trial.common.write(path, lock)
        trial.common.evaluation.panel.run_evaluation_twice(output, args.dataset, args.scene, fixed_manifest)
        result = trial.common.read(output / 'psnr/strict_fixed_manifest/final_result.json')
        alignment = trial.common.read(output / 'snapshot_alignment.json')
        records.append(point(result, row['copy_finished_seconds'], alignment=alignment,
                             steps=row['completed_optimizer_steps']))
    final = trial.common.read(root / 'psnr/strict_fixed_manifest/final_result.json')
    runtime = trial.common.read(root / 'mapping_replay_runtime.json')
    records.append(point(final, runtime['mapping_wall_seconds'],
                         steps=runtime['optimizer_steps_completed']))
    curve = assemble_curve(records)
    curve['shared_evaluation_coordinates'] = args.shared_coordinates
    filename = 'stream_quality_shared.json' if args.shared_coordinates else 'stream_quality.json'
    trial.common.write(root / filename, curve)
    print(json.dumps({**{k: v for k, v in curve.items() if k != 'points'},
        'points': [{k: v for k, v in row.items() if k not in ('view_uids', 'per_view_psnr', 'alignment')}
                   for row in records]}, indent=2))


if __name__ == '__main__':
    main()
