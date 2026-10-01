#!/usr/bin/env python3
"""CPU-only independent free-space diagnostics for immutable map snapshots.

Final trajectories/ORB registration are post-run evaluation inputs. The mapper
never sees them. Frustum coverage is reported as context, not surface coverage
or proof of visibility: this manual mask contains no occlusion/surface GT.
"""
import argparse
import importlib.util
from pathlib import Path
import sys
import traceback

import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from collect_cvpr_assets import OUT, read, write, sha
from evaluate_cvpr_regions import EVALUATOR, MASK, POSES, EXPECTED
from snapshot_camera_alignment import align_camera_worlds


def region_metrics(module, xyz, opacity, scales, quaternions, transform, mask, lower, voxel):
    s, r, t = transform
    centers = s*(xyz @ r.T)+t
    member = module.region_membership(centers, mask, lower, voxel)
    support = module.sigma_points(xyz, scales, quaternions)
    support = s*(support.reshape(-1, 3) @ r.T)+t
    overlap = module.region_membership(support, mask, lower, voxel).reshape(len(xyz), 7) @ module.SIGMA_WEIGHTS
    return {'gaussians': len(xyz), 'centers_alpha_gt_0p3': int((member & (opacity > .3)).sum()),
            'opacity_support_mass': float((opacity*overlap).sum())}


def frustum_membership(points, cameras, intrinsics, size):
    # No method's predicted depths or reconstruction are used to pick voxels.
    seen = np.zeros(len(points), dtype=bool)
    fx, fy, cx, cy = intrinsics
    width, height = size
    for camera in cameras:
        ids = np.flatnonzero(~seen)
        if not len(ids): break
        local = (points[ids]-camera[:3, 3]) @ camera[:3, :3]
        z = local[:, 2]
        good = (z > .1) & (z < 10)
        xx = fx*local[:, 0]/np.maximum(z, 1e-8)+cx
        yy = fy*local[:, 1]/np.maximum(z, 1e-8)+cy
        good &= (xx >= 0) & (xx < width) & (yy >= 0) & (yy < height)
        seen[ids[good]] = True
    return seen


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('runs', nargs='+', help='LABEL=RUN_DIRECTORY')
    a = p.parse_args(); torch.set_num_threads(4)
    assert not a.output.exists(), a.output
    for path, expected in EXPECTED.items(): assert sha(path) == expected
    spec = importlib.util.spec_from_file_location('unchanged_manual_region', EVALUATOR)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    source = next(r for r in read(OUT / 'scene_inventory.json') if r['scene'] == 'aria1253')
    region = np.load(MASK)
    mask, lower, voxel = region['mask'].astype(bool), region['lo'], float(region['voxel'])
    points = (np.argwhere(mask)+.5)*voxel+lower
    intrinsics = np.loadtxt(source['calibration'])[:4]
    image = next(p for p in sorted(Path(source['image_dir']).iterdir()) if p.suffix.lower() in {'.png', '.jpg', '.jpeg'})
    size = Image.open(image).size
    heldout = {int(v['frame_index']) for v in read(Path(source['fixed_manifest']))['views']}
    orb_times, orb_centers = module.load_orb_centres(POSES)
    labelled = [(label, Path(path).resolve()) for label, path in (s.split('=', 1) for s in a.runs)]
    first_keys = []
    for _, run in labelled:
        first = read(run / 'snapshots/manifest.json')['snapshots'][0]
        state = torch.load(run / 'snapshots' / first['file'], map_location='cpu', weights_only=True)
        first_keys.append(set(state['keyframe_w2c']))
        del state
    common_keys = sorted(set.intersection(*first_keys))
    common_run = labelled[0][1]
    common_ref = np.atleast_2d(np.loadtxt(common_run / 'traj_full_beforeBA.txt'))
    cs, cr, ct, _ = module.align_run(common_run, orb_times, orb_centers)
    common_cameras = np.repeat(np.eye(4)[None], len(common_ref), axis=0)
    common_cameras[:, :3, :3] = cr[None] @ Rotation.from_quat(common_ref[:, 4:8]).as_matrix()
    common_cameras[:, :3, 3] = cs*(common_ref[:, 1:4] @ cr.T)+ct
    initial_seen = frustum_membership(points, common_cameras[common_keys], intrinsics, size)
    common_mask = np.zeros_like(mask)
    initial_cells = np.argwhere(mask)[initial_seen]
    common_mask[tuple(initial_cells.T)] = True
    common_path = a.output.with_suffix('.npz')
    np.savez_compressed(common_path, mask=common_mask, lo=lower, voxel=voxel)
    common_declaration = {'shared_first_checkpoint_keyframe_uids': common_keys,
        'mask_path': str(common_path), 'mask_sha256': sha(common_path),
        'mask_voxels': int(initial_seen.sum()), 'fraction_of_full_annotation': float(initial_seen.mean()),
        'selection': 'manual voxels in shared first-checkpoint camera frusta; no quality scores, predicted depths or reconstruction used'}
    rows = []
    for label, run in labelled:
        reference = np.atleast_2d(np.loadtxt(run / 'traj_full_beforeBA.txt'))
        c2w = np.repeat(np.eye(4)[None], len(reference), axis=0)
        c2w[:, :3, :3] = Rotation.from_quat(reference[:, 4:8]).as_matrix()
        c2w[:, :3, 3] = reference[:, 1:4]
        sb, rb, tb, residual = module.align_run(run, orb_times, orb_centers)
        orb_cameras = c2w.copy()
        orb_cameras[:, :3, :3] = rb[None] @ c2w[:, :3, :3]
        orb_cameras[:, :3, 3] = sb*(c2w[:, :3, 3] @ rb.T)+tb
        manifest = read(run / 'snapshots/manifest.json')['snapshots']
        for checkpoint in manifest + [{'file': 'final', 'final': True}]:
            row = {'arm': label, 'run': str(run), 'name': Path(checkpoint['file']).stem,
                   'checkpoint': checkpoint, 'status': 'failed'}
            try:
                if checkpoint.get('final'):
                    xyz, opacity, scales, quaternions = module.load_gaussians(run / '3dgs_before_final.ply')
                    transform = sb, rb, tb
                    result = read(run / 'render_result.json')
                    keys = np.flatnonzero(np.isin(reference[:, 0], np.loadtxt(run / 'traj_kf_beforeBA.txt')[:, 0])).tolist()
                    row.update(training_renders=result['render_counts']['training'], arrival_uid=len(reference)-1,
                               source_sha256=sha(run / '3dgs_before_final.ply'), alignment_accepted=True)
                else:
                    path = run / 'snapshots' / checkpoint['file']
                    state = torch.load(path, map_location='cpu', weights_only=True)
                    keys = sorted(state['keyframe_w2c'])
                    used = set(keys) | set(state['training_uids']) | {int(v) for v in state['origin_uids'].tolist() if v >= 0}
                    assert not used & heldout
                    align = align_camera_worlds(np.linalg.inv(c2w[keys]), np.stack([state['keyframe_w2c'][k].numpy() for k in keys]))
                    relative = align['center_rmse']/max(align['reference_center_rms_radius'], 1e-8)
                    accepted = relative <= .03 and align['orientation_max_error_degrees'] <= 5
                    rc = rb @ align['rotation'].T
                    sc = sb/align['scale']
                    tc = tb-sc*rc @ align['translation']
                    transform = sc, rc, tc
                    params = {k: v.numpy().astype(np.float64) for k, v in state['parameters'].items()}
                    xyz, scales, quaternions = params['xyz'], np.exp(params['scaling']), params['rotation']
                    opacity = 1/(1+np.exp(-params['opacity'].reshape(-1)))
                    row.update(training_renders=checkpoint['training_renders'], arrival_uid=checkpoint['arrival_uid'],
                               source_sha256=sha(path), alignment_accepted=accepted, relative_center_rmse=relative,
                               orientation_max_error_degrees=align['orientation_max_error_degrees'])
                    del state
                common_metrics = region_metrics(module, xyz, opacity, scales, quaternions, transform, common_mask, lower, voxel)
                row.update(**region_metrics(module, xyz, opacity, scales, quaternions, transform, mask, lower, voxel),
                    initial_shared_region=common_metrics,
                    frustum_covered_mask_fraction=float(frustum_membership(points, orb_cameras[keys], intrinsics, size).mean()),
                    registration_median_m=float(np.median(residual)), registration_p90_m=float(np.percentile(residual, 90)),
                    status='evaluated')
            except Exception:
                row['error'] = traceback.format_exc()
            rows.append(row)
            write(a.output, {'rows': rows, 'evaluation_only': True, 'reference_used_by_mapper': False,
                'script_sha256': sha(Path(__file__)), 'metric_source_sha256': sha(EVALUATOR),
                'reference': {str(p): sha(p) for p in EXPECTED}, 'full_mask_voxels': len(points),
                'initial_shared_region': common_declaration,
                'frustum_coverage': 'camera frusta with 0.1–10 m range; no occlusion test; not surface completeness',
                'dense_surface_reference_available': False})
            print('REGION_CHECKPOINT', label, row['name'], row['status'], row.get('opacity_support_mass'), flush=True)
    from run_cvpr_measurements import journal
    journal({'dataset': 'aria', 'scene': 'aria1253_region_checkpoints', 'budget': 40,
             'arm': 'd3_vs_vanilla', 'status': 'evaluated' if all(r['status']=='evaluated' for r in rows) else 'failed',
             'output': str(a.output)})


if __name__ == '__main__': main()
