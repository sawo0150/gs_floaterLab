#!/usr/bin/env python3
"""Export a saved CPU map and post-run gauge-aligned evaluation trajectory.

Alignment residuals must be reviewed before interpreting snapshot PSNR. A good
least-squares fit is not proof that nonrigid trajectory changes are negligible.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from plyfile import PlyData, PlyElement
from scipy.spatial.transform import Rotation
import torch
from snapshot_camera_alignment import align_camera_worlds, transform_evaluation_cameras


def write_map(state, path):
    p = {key: value.numpy() for key, value in state['parameters'].items()}
    n = len(p['xyz'])
    degree = state['active_sh_degree']
    dc = p['features_dc'].transpose(0, 2, 1).reshape(n, -1)
    # The existing PLY evaluator infers active SH degree from stored fields.
    # Truncate inactive coefficients so it evaluates the captured model exactly.
    rest = p['features_rest'][:, :(degree + 1) ** 2 - 1, :].transpose(0, 2, 1)
    rest = rest.reshape(n, -1)
    names = ['x', 'y', 'z', 'nx', 'ny', 'nz']
    names += [f'f_dc_{i}' for i in range(dc.shape[1])]
    names += [f'f_rest_{i}' for i in range(rest.shape[1])]
    names += ['opacity'] + [f'scale_{i}' for i in range(p['scaling'].shape[1])]
    names += [f'rot_{i}' for i in range(p['rotation'].shape[1])]
    values = np.concatenate([p['xyz'], np.zeros_like(p['xyz']), dc, rest,
                             p['opacity'], p['scaling'], p['rotation']], axis=1)
    vertices = np.empty(n, dtype=[(key, 'f4') for key in names])
    for i, key in enumerate(names):
        vertices[key] = values[:, i]
    PlyData([PlyElement.describe(vertices, 'vertex')]).write(path)


def export(state, trajectory, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    trajectory = np.asarray(trajectory, dtype=np.float64)
    c2w = np.repeat(np.eye(4)[None], len(trajectory), axis=0)
    c2w[:, :3, :3] = Rotation.from_quat(trajectory[:, 4:8]).as_matrix()
    c2w[:, :3, 3] = trajectory[:, 1:4]
    reference = np.linalg.inv(c2w)
    keys = sorted(state['keyframe_w2c'])
    if not keys or min(keys) < 0 or max(keys) >= len(reference):
        raise ValueError('Snapshot UID does not index the reference trajectory')
    alignment = align_camera_worlds(reference[keys],
        np.stack([state['keyframe_w2c'][key].numpy() for key in keys]))
    aligned = np.linalg.inv(transform_evaluation_cameras(reference, alignment))
    rows = np.concatenate([trajectory[:, :1], aligned[:, :3, 3],
                           Rotation.from_matrix(aligned[:, :3, :3]).as_quat()], axis=1)
    write_map(state, output / '3dgs_before_final.ply')
    np.savetxt(output / 'traj_full_beforeBA.txt', rows, fmt='%.12f')
    np.savetxt(output / 'traj_kf_beforeBA.txt', rows[keys], fmt='%.12f')
    (output / 'mapped_uids.json').write_text(json.dumps(state['training_uids']) + '\n')
    report = {key: value.tolist() if isinstance(value, np.ndarray) else value
              for key, value in alignment.items()}
    report.update(snapshot=state['metadata'], evaluation_only=True,
                  alignment_quality_accepted=False)
    (output / 'snapshot_alignment.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--reference-trajectory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    state = torch.load(args.snapshot, map_location='cpu', weights_only=True)
    print(json.dumps(export(state, np.loadtxt(args.reference_trajectory), args.output), indent=2))
