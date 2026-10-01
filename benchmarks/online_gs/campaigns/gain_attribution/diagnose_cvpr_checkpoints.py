#!/usr/bin/env python3
"""CPU-only audit of actual snapshot pose gauges and held-out exclusion."""
import argparse
from pathlib import Path
import sys
import traceback
import numpy as np
from scipy.spatial.transform import Rotation
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from collect_cvpr_assets import OUT, RESULTS, read, write, sha
from snapshot_camera_alignment import align_camera_worlds


def main():
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); torch.set_num_threads(4)
    inventory = {(r['dataset'], r['scene']): r for r in read(OUT / 'scene_inventory.json')}
    rows = []
    panels = [RESULTS / 'cvpr_assets/fixed_work_v1/summary.json', RESULTS / 'cvpr_assets/pilot_v1/summary.json']
    for panel in panels:
        for run in read(panel):
            if run['status'] != 'passed': continue
            directory = Path(run['output'])
            manifest = directory / 'snapshots/manifest.json'
            if not manifest.exists(): continue
            reference = np.atleast_2d(np.loadtxt(directory / 'traj_full_beforeBA.txt'))
            c2w = np.repeat(np.eye(4)[None], len(reference), axis=0)
            c2w[:, :3, :3] = Rotation.from_quat(reference[:, 4:8]).as_matrix()
            c2w[:, :3, 3] = reference[:, 1:4]
            poses = np.linalg.inv(c2w)
            source = inventory[(run['dataset'], run['scene'])]
            heldout = {v['frame_index'] for v in read(Path(source['fixed_manifest']))['views']}
            for checkpoint in read(manifest)['snapshots']:
                path = directory / 'snapshots' / checkpoint['file']
                row = {'dataset': run['dataset'], 'scene': run['scene'], 'arm': run['arm'],
                       'budget': run['budget'], 'checkpoint': checkpoint, 'file': str(path),
                       'file_sha256': sha(path), 'status': 'failed'}
                try:
                    state = torch.load(path, map_location='cpu', weights_only=True)
                    keys = sorted(state['keyframe_w2c'])
                    origins = {int(x) for x in state['origin_uids'].tolist() if x >= 0}
                    used = origins | set(keys) | set(state['training_uids'])
                    assert not used & heldout, sorted(used & heldout)
                    alignment = align_camera_worlds(poses[keys], np.stack([state['keyframe_w2c'][k].numpy() for k in keys]))
                    relative = alignment['center_rmse'] / max(alignment['reference_center_rms_radius'], 1e-8)
                    accepted = relative <= .03 and alignment['orientation_max_error_degrees'] <= 5
                    row.update(status='diagnosed', mapping_disjoint=True, accepted=accepted,
                               relative_center_rmse=relative,
                               alignment={k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in alignment.items()})
                except Exception:
                    row['error'] = traceback.format_exc()
                rows.append(row)
    write(a.output, {'rows': rows, 'evaluation_only': True, 'cuda_used': False,
                    'source': str(Path(__file__)), 'source_sha256': sha(Path(__file__))})
    print('SNAPSHOT_AUDIT',len(rows),'states;',sum(r.get('accepted',False) for r in rows),'accepted;',
          sum(r['status']=='failed' for r in rows),'failed')
    for r in rows[:12]:
        print(r['scene'],r['arm'],r['checkpoint']['file'],r['status'],r.get('accepted'),r.get('relative_center_rmse'))


if __name__ == '__main__': main()
