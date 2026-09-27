#!/usr/bin/env python3
"""Offline KF/mixed x depth-normal factorial, with identical RGB work per pair.

This deliberately performs post-EOS optimization on an immutable checkpoint.
No result from this script is evidence of strict-online quality or convergence.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import run_online_dense_training as trial

ROOT = trial.ROOT / 'geometry_interaction/v2'
PARENTS = {
    ('aria', 'aria1253'): 'causal_visual_dense_pose_fixed_map/aria/aria1253',
    ('rpng', 'table_06'): 'visual_pose_transfer/fixed_visual/rpng/table_06',
    ('utmm', 'square-1'): 'visual_pose_transfer/fixed_visual/utmm/square-1'}
ARMS = ('kf_rgb', 'mixed_rgb', 'kf_rgbdn', 'mixed_rgbdn')
PHOTO_STEPS, NATIVE_PERIOD, NATIVE_BATCH = 5000, 16, 17


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def schedules(kf, pool):
    rng = random.Random(0)
    photo = []
    while len(photo) < PHOTO_STEPS:
        block = sorted(pool); rng.shuffle(block); photo.extend(block)
    rng = random.Random(31)
    native = [rng.sample(sorted(kf), min(NATIVE_BATCH, len(kf)))
              for _ in range(PHOTO_STEPS // NATIVE_PERIOD)]
    return photo[:PHOTO_STEPS], native


def native_loss(packages, views, config, lambda_normal, geometry):
    import torch
    from gaussian.utils.slam_utils import get_loss_mapping_rgb, get_loss_normal
    alpha = config['Training'].get('alpha', .95)
    loss = 0
    for view, pkg in zip(views, packages):
        depth = pkg['depth']
        gt = view.depth_gpu if view.depth_gpu is not None else view.depth.to(depth.device)[None]
        valid = (gt > .01) & (depth > .01)
        # Preserve the original all-pixel mean and validity threshold, but
        # exclude invalid values before reciprocal: inf*0 is not a mask.
        inv_depth = torch.where(valid, depth, torch.ones_like(depth)).reciprocal()
        inv_gt = torch.where(valid, gt, torch.ones_like(gt)).reciprocal()
        depth_loss = (inv_depth - inv_gt).abs().mean()
        loss = loss + alpha * get_loss_mapping_rgb(config, pkg['render'], depth, view)
        loss = loss + float(geometry) * ((1-alpha) * 5 * depth_loss
                    + lambda_normal / 10 * get_loss_normal(depth, view))
    return loss


def worker(dataset, scene, arm):
    import numpy as np
    import torch
    import lietorch
    from gaussian.renderer import render, render_kernel_batch
    from gaussian.scene.gaussian_model import GaussianModel
    from gaussian.utils.camera_utils import Camera
    from gaussian.utils.graphics_utils import getProjectionMatrix2
    from gaussian.utils.loss_utils import dense_rgb_l1_ssim_loss, psnr
    import exp78_evaluate_vigs_ply as evaluator

    random.seed(0); np.random.seed(0); torch.manual_seed(0); torch.cuda.manual_seed_all(0)
    parent = trial.BASE.WORKSPACE / 'results/campaigns/gain_attribution' / PARENTS[dataset, scene]
    checkpoint = torch.load(parent / 'checkpoint.pt', map_location='cpu', weights_only=False)
    p = checkpoint['gaussians']
    model = GaussianModel(p['max_sh_degree'], config=checkpoint['config'])
    model.active_sh_degree = p['active_sh_degree']; model.init_lr(p['spatial_lr_scale'])
    for name in ('xyz', 'features_dc', 'features_rest', 'opacity', 'scaling', 'rotation'):
        setattr(model, '_' + name, torch.nn.Parameter(p[name].cuda()))
    model.training_setup(SimpleNamespace(**checkpoint['opt_params']))
    model.optimizer.load_state_dict(copy.deepcopy(p['optimizer']))
    for name in ('max_radii2D', 'xyz_gradient_accum', 'denom'):
        setattr(model, name, p[name].cuda())
    model.unique_kfIDs, model.n_obs = p['unique_kfIDs'], p['n_obs']
    paths = trial.BASE.sequence_paths(dataset, scene)
    manifest = trial.common.read(paths['fixed_manifest'])
    names = evaluator.numeric_names(paths['image_dir'])
    uid_by_name = {name: i for i, name in enumerate(names)}
    heldout = {uid_by_name[r['uid']] for r in manifest['views']}
    k = [float(x) for x in checkpoint['K']]
    proj = getProjectionMatrix2(znear=.01, zfar=100., fx=k[0], fy=k[1], cx=k[2], cy=k[3],
                                W=int(k[-2]), H=int(k[-1])).T.cuda()
    cameras, kf = {}, []
    for row in checkpoint['cameras']:
        uid = int(row['uid'])
        if uid in heldout or row.get('mapping_eval_excluded', False):
            raise ValueError('Held-out RGB in training snapshot')
        pose = torch.eye(4, device='cuda'); pose[:3, :3] = row['R'].cuda(); pose[:3, 3] = row['T'].cuda()
        view = Camera.init_from_tracking(row['image'], row['depth'], row['normal'], pose, uid, proj, k)
        for parameter in view.parameters():
            parameter.requires_grad_(False)
        view.sensor_type = row['sensor_type']
        cameras[uid] = view
        if row['sensor_type'] != 'rgb_dense':
            if row['depth'] is None or row['normal'] is None:
                raise ValueError('Missing native geometry carrier')
            kf.append(uid)
        else:
            view.original_image_gpu = None
    pool = sorted(kf if arm.startswith('kf_') else cameras)
    photo, native = schedules(kf, pool)
    out = ROOT / dataset / scene / arm
    out.mkdir(parents=True, exist_ok=False)
    trial.common.write(out / 'selection.json', {'photo': photo, 'native': native})

    # Evaluator-only cameras are constructed separately and never returned to
    # any training selector, loss, pose solver, or optimization routine.
    trajectory = np.loadtxt(parent / 'base/traj_full_beforeBA.txt')
    eval_poses = lietorch.SE3(torch.tensor(trajectory[:, 1:], dtype=torch.float32, device='cuda')).inv().matrix()
    calibration = np.loadtxt(paths['calibration'])
    eval_views = []
    for uid in sorted(heldout):
        image, params = evaluator.preprocess_image(paths['image_dir'] / names[uid], calibration, dataset != 'aria')
        evproj = getProjectionMatrix2(znear=.01, zfar=100., fx=params[0], fy=params[1], cx=params[2], cy=params[3],
                                     W=params[-2], H=params[-1]).T.cuda()
        view = Camera.init_from_tracking(image.float()/255., None, None, eval_poses[uid], uid, evproj, params)
        view.original_image_gpu = None
        eval_views.append(view)
    background = torch.ones(3, device='cuda')

    @torch.no_grad()
    def evaluate(target):
        scores = []
        for view in eval_views:
            gt = view.original_image.cuda()
            pred = render(view, target, background)['render'].clamp(0, 1)
            mask = gt > 0
            scores.append(float(psnr(pred[mask][None], gt[mask][None]).item()))
        return scores

    initial = evaluate(model)
    curves = [{'photo_steps': 0, 'adam_steps': 0, 'psnr': float(np.mean(initial))}]
    geometry = arm.endswith('rgbdn')
    adam_steps, renders, native_index = 0, 0, 0
    lambda_normal = float(checkpoint['config']['Training'].get('lambda_dnormal', .5))
    config = checkpoint['config']
    torch.cuda.synchronize(); started = time.monotonic()
    for index, uid in enumerate(photo, 1):
        view = cameras[uid]
        model.update_learning_rate(adam_steps + 1)
        prediction = render(view, model, background)['render']
        loss = dense_rgb_l1_ssim_loss(prediction, view.original_image.cuda(),
                                      checkpoint['opt_params']['lambda_dssim'], compiled=False)
        if not torch.isfinite(loss):
            raise RuntimeError('Nonfinite photometric loss')
        loss.backward(); model.optimizer.step(); model.optimizer.zero_grad(set_to_none=True)
        adam_steps += 1; renders += 1
        if index % NATIVE_PERIOD == 0:
            views = [cameras[u] for u in native[native_index]]
            packages = render_kernel_batch(views, model, background)
            if native_index == 0:
                from gaussian.utils.slam_utils import get_loss_mapping_rgbd, get_loss_normal
                with torch.no_grad():
                    validity = [{'uid': v.uid,
                        'render_depth_nonfinite': int((~torch.isfinite(pkg['depth'])).sum()),
                        'render_depth_zero': int((pkg['depth'] == 0).sum()),
                        'gt_depth_zero': int((v.depth_gpu == 0).sum()),
                        'legacy_rgbd_finite': bool(torch.isfinite(get_loss_mapping_rgbd(
                            config, pkg['render'], pkg['depth'], v, geometry_scale=float(geometry)))),
                        'normal_loss_finite': bool(torch.isfinite(get_loss_normal(pkg['depth'], v)))}
                        for v, pkg in zip(views, packages)]
                trial.common.write(out / 'first_native_validity.json', validity)
            loss = native_loss(packages, views, config, lambda_normal, geometry)
            if not torch.isfinite(loss):
                raise RuntimeError('Nonfinite native loss')
            model.update_learning_rate(adam_steps + 1)
            loss.backward(); model.optimizer.step(); model.optimizer.zero_grad(set_to_none=True)
            adam_steps += 1; renders += len(views); native_index += 1
            del packages
        if index in (250, 1000, PHOTO_STEPS):
            scores = evaluate(model)
            curves.append({'photo_steps': index, 'adam_steps': adam_steps, 'psnr': float(np.mean(scores))})
            print(arm, curves[-1], flush=True)
    torch.cuda.synchronize()
    elapsed = time.monotonic() - started
    model.save_ply(out / 'map.ply')
    saved = evaluator.load_gaussians(out / 'map.ply')
    repeat = evaluate(saved)
    reload_difference = float(np.max(np.abs(np.asarray(scores) - np.asarray(repeat))))
    if reload_difference > .01:
        raise RuntimeError('Saved-map evaluation mismatch')
    trial.common.write(out / 'result.json', {
        'protocol': 'offline_geometry_interaction_v1', 'strict_online': False,
        'dataset': dataset, 'scene': scene, 'arm': arm, 'depth_normal': geometry,
        'checkpoint_sha256': digest(parent / 'checkpoint.pt'), 'training_pose_source': checkpoint['training_pose_source'],
        'training_views': len(pool), 'keyframes': len(kf), 'heldout_views': len(heldout), 'heldout_overlap': 0,
        'selection_sha256': digest(out / 'selection.json'), 'native_steps': native_index,
        'native_view_batch': min(NATIVE_BATCH, len(kf)), 'photo_steps': PHOTO_STEPS,
        'post_eos_optimizer_updates': adam_steps, 'training_renders': renders,
        'initial_psnr': curves[0]['psnr'], 'final_psnr': curves[-1]['psnr'], 'curves': curves,
        'saved_reload_max_psnr_difference': reload_difference,
        'same_gaussian_count': len(model.get_xyz) == len(p['xyz']),
        'optimizer_state': 'restored_identical_snapshot', 'wall_seconds_including_evaluation': elapsed,
        'limitations': 'Frozen post-EOS diagnostic; fixed topology and common synthetic service schedule. Not actual live scheduling or a time-matched quality claim. Native RGB term remains present with geometry off.'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', default='aria'); parser.add_argument('--scene', default='aria1253')
    parser.add_argument('--worker', action='store_true'); parser.add_argument('--arm', choices=ARMS)
    args = parser.parse_args()
    if (args.dataset, args.scene) not in PARENTS:
        raise ValueError('Not a goal scene')
    if args.worker:
        return worker(args.dataset, args.scene, args.arm)
    parent = trial.BASE.WORKSPACE / 'results/campaigns/gain_attribution' / PARENTS[args.dataset, args.scene]
    paths = trial.BASE.sequence_paths(args.dataset, args.scene)
    output = ROOT / args.dataset / args.scene; output.mkdir(parents=True, exist_ok=False)
    sources = [Path(__file__).resolve(), parent / 'checkpoint.pt', parent / 'base/traj_full_beforeBA.txt',
        paths['fixed_manifest'], paths['calibration'], trial.BASE.EVALUATOR,
        trial.BACKEND / 'vigs/gaussian/renderer/__init__.py',
        trial.BACKEND / 'vigs/gaussian/scene/gaussian_model.py',
        trial.BACKEND / 'vigs/gaussian/utils/slam_utils.py',
        trial.BACKEND / 'vigs/gaussian/utils/loss_utils.py']
    hashes = {str(p): digest(p) for p in sources}
    trial.common.write(output / 'source_lock.json', hashes)
    (output / 'runner_source.py').write_bytes(Path(__file__).read_bytes())
    trial.common.write(output / 'contract.json', {'arms': ARMS, 'photo_steps': PHOTO_STEPS,
        'native_every_photo_steps': NATIVE_PERIOD, 'native_batch': NATIVE_BATCH,
        'fixed_topology': True, 'strict_online': False, 'source_pose_is_post_eos_training_only': True,
        'only_geometry_weights_change_within_pool': True, 'seed': 0})
    dependency_command = [str(trial.BASE.PYTHON_ENV / 'bin/python'), str(Path(__file__).with_name('online_runtime_dependencies.py'))]
    dependencies = json.loads(subprocess.check_output(dependency_command, env=trial.environment(), text=True))
    trial.common.write(output / 'native_dependencies.json', dependencies)
    for arm in ARMS:
        trial.common.evaluation.panel.v2.gpu_idle()
        command = [str(trial.BASE.PYTHON_ENV / 'bin/python'), str(Path(__file__).resolve()),
            '--worker', '--dataset', args.dataset, '--scene', args.scene, '--arm', arm]
        trial.common.write(output / (arm + '.command.json'), command)
        print('START', args.dataset, args.scene, arm, flush=True)
        with (output / (arm + '.log')).open('x') as log:
            subprocess.run(command, env=trial.environment(), stdout=log, stderr=subprocess.STDOUT, check=True)
        if any(digest(p) != h for p, h in hashes.items()):
            raise RuntimeError('Source/checkpoint changed during diagnostic')
        if json.loads(subprocess.check_output(dependency_command, env=trial.environment(), text=True)) != dependencies:
            raise RuntimeError('Native dependencies changed during diagnostic')
    rows = {arm: trial.common.read(output / arm / 'result.json') for arm in ARMS}
    for key in ('checkpoint_sha256', 'initial_psnr', 'photo_steps', 'native_steps', 'training_renders',
                'post_eos_optimizer_updates', 'heldout_views', 'heldout_overlap', 'same_gaussian_count'):
        if len({r[key] for r in rows.values()}) != 1:
            raise RuntimeError('Factorial mismatch: ' + key)
    for pool in ('kf', 'mixed'):
        if rows[pool + '_rgb']['selection_sha256'] != rows[pool + '_rgbdn']['selection_sha256']:
            raise RuntimeError('Geometry flag changed selection')
    schedules_read = [trial.common.read(output / arm / 'selection.json') for arm in ARMS]
    if any(s['native'] != schedules_read[0]['native'] for s in schedules_read):
        raise RuntimeError('Native RGB/geometry carrier schedules differ')
    gains = {kind: rows['mixed_' + kind]['final_psnr'] - rows['kf_' + kind]['final_psnr'] for kind in ('rgb', 'rgbdn')}
    result = {'valid': True, 'psnr': {a: r['final_psnr'] for a, r in rows.items()},
        'mixed_minus_kf': gains, 'geometry_interaction_db': gains['rgbdn'] - gains['rgb'],
        'strict_online': False, 'online_quality_claim': False}
    trial.common.write(output / 'comparison.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
