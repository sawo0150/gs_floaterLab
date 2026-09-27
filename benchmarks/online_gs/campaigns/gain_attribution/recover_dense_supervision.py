#!/usr/bin/env python3
"""Recover dense RGB gains with an immutable checkpoint and scope-only branches.

The checkpoint diagnostic intentionally performs post-stream optimization. It is
not a streaming benchmark. Training cameras come from the mapper, never from
the evaluation-only full trajectory. The online pair retains all native work.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import time

ONLINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ONLINE))
import run_exp94_normalized_metric_v2_fixed_eval as evaluation

BASE = evaluation.base
evaluation.panel.v2.install_inventory()
ROOT = BASE.WORKSPACE / 'results/campaigns/gain_attribution/dense_gain_recovery'
OLD = BASE.WORKSPACE / 'results/campaigns/gain_attribution/role_aware_dense_service_v3'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_gpu():
    active = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name',
                                      '--format=csv,noheader'], text=True).strip()
    if active:
        raise RuntimeError('GPU compute processes active; wait: ' + active)


def command(dataset, scene, output):
    cmd = json.loads((OLD / dataset / scene / 'r4_backbone/mapping_command.json').read_text())
    cmd[cmd.index('--output') + 1] = str(output)
    return cmd


def launch(args):
    if args.mode == 'online':
        subprocess.run([sys.executable, str(Path(__file__).with_name('run_dense_scope_online.py')),
                        '--dataset', args.dataset, '--scene', args.scene], check=True)
        return
    root = ROOT / args.dataset / args.scene
    sources = [Path(__file__), BASE.CUSTOM_HARNESS, BASE.PAPER_ROOT / 'vigs/gs_backend.py',
               BASE.PAPER_ROOT / 'vigs/map_scheduler.py', BASE.EVALUATOR,
               BASE.PAPER_ROOT / 'vigs/gaussian/scene/gaussian_model.py',
               BASE.PAPER_ROOT / 'vigs/gaussian/utils/loss_utils.py']
    lock = {str(p): digest(p) for p in sources}
    lockpath = root / 'source_lock.json'
    if lockpath.exists() and json.loads(lockpath.read_text()) != lock:
        raise RuntimeError('Source changed: use a new result root')
    write(lockpath, lock)
    contract = {'steps': args.steps, 'pose_align_steps': args.pose_align_steps,
                'dataset': args.dataset, 'scene': args.scene}
    contract_path = root / 'contract.json'
    if contract_path.exists() and json.loads(contract_path.read_text()) != contract:
        raise RuntimeError('Changed diagnostic budget: use a new result root')
    write(contract_path, contract)
    frozen_runner = root / 'runner_source.py'
    if not frozen_runner.exists():
        frozen_runner.write_bytes(Path(__file__).read_bytes())
    actions = (['mixed_full'] if args.pose_align_steps else
               ['capture', 'kf_sh', 'mixed_sh', 'kf_full', 'mixed_full'])
    for action in actions:
        target = root / ('checkpoint.pt' if action == 'capture' else action + '/result.json')
        if target.exists():
            continue
        check_gpu()
        logpath = root / (action + '.log')
        if logpath.exists():
            raise FileExistsError('Incomplete worker log preserved: ' + str(logpath))
        cmd = [str(BASE.PYTHON_ENV / 'bin/python'), str(Path(__file__).resolve()),
               'worker', '--dataset', args.dataset, '--scene', args.scene,
               '--action', action, '--steps', str(args.steps),
               '--result-root', str(ROOT), '--pose-align-steps', str(args.pose_align_steps)]
        with logpath.open('x') as log:
            subprocess.run(cmd, env=BASE.mapping_environment(True), stdout=log,
                           stderr=subprocess.STDOUT, check=True)
        print('COMPLETED', args.dataset, args.scene, action, flush=True)


def worker(args):
    import numpy as np
    import torch
    import lietorch
    from gaussian.renderer import render
    from gaussian.scene.gaussian_model import GaussianModel
    from gaussian.utils.camera_utils import Camera
    from gaussian.utils.graphics_utils import getProjectionMatrix2
    from gaussian.utils.loss_utils import dense_rgb_l1_ssim_loss, psnr
    import exp78b_replay_gsslam_mapping as replay
    import exp78_evaluate_vigs_ply as evaluator
    root = ROOT / args.dataset / args.scene
    if args.action == 'capture':
        instances = []
        original = replay.GSBackEnd.__init__
        def capture(self, *a, **kw):
            original(self, *a, **kw)
            instances.append(self)
        replay.GSBackEnd.__init__ = capture
        output = root / 'base'
        if output.exists():
            raise FileExistsError(output)
        cmd = command(args.dataset, args.scene, output)
        sys.argv = cmd[1:]
        replay.main()
        mapper = instances[-1]
        cameras = []
        for view in [*mapper.viewpoints.values(), *mapper.polish_viewpoints.values()]:
            if getattr(view, 'mapping_eval_excluded', False):
                continue
            row = mapper._capture_polish_camera(view)
            row['image'] = view.original_image.detach().cpu().clone()
            cameras.append(row)
        torch.save({'gaussians': mapper._capture_polish_gaussians(), 'cameras': cameras,
                    'K': mapper.K, 'opt_params': dict(mapper.opt_params),
                    'config': mapper.config,
                    'training_pose_source': 'mapper cameras at end of causal replay; no evaluation poses'},
                   root / 'checkpoint.pt')
        return
    random.seed(0); np.random.seed(0); torch.manual_seed(0); torch.cuda.manual_seed_all(0)
    checkpoint = torch.load(root / 'checkpoint.pt', map_location='cpu', weights_only=False)
    p = checkpoint['gaussians']
    model = GaussianModel(p['max_sh_degree'], config=checkpoint['config'])
    model.active_sh_degree = p['active_sh_degree']
    model.init_lr(p['spatial_lr_scale'])
    for name in ('xyz', 'features_dc', 'features_rest', 'opacity', 'scaling', 'rotation'):
        setattr(model, '_' + name, torch.nn.Parameter(p[name].cuda()))
    from types import SimpleNamespace
    model.training_setup(SimpleNamespace(**checkpoint['opt_params']))
    model.optimizer.load_state_dict(copy.deepcopy(p['optimizer']))
    for name in ('max_radii2D', 'xyz_gradient_accum', 'denom'):
        setattr(model, name, p[name].cuda())
    model.unique_kfIDs = p['unique_kfIDs']
    model.n_obs = p['n_obs']
    k = [float(x) for x in checkpoint['K']]
    proj = getProjectionMatrix2(znear=.01, zfar=100., fx=k[0], fy=k[1], cx=k[2], cy=k[3],
                               W=int(k[-2]), H=int(k[-1])).T.cuda()
    base = root / 'base'
    archive_meta = json.loads((Path(json.loads((base / 'mapping_replay_runtime.json').read_text())['archive']) /
                               'archive_manifest.json').read_text())
    paths = BASE.sequence_paths(args.dataset, args.scene)
    manifest = json.loads(paths['fixed_manifest'].read_text())
    names = evaluator.numeric_names(paths['image_dir'])
    uid_by_name = {n: i for i, n in enumerate(names)}
    heldout = {uid_by_name[row['uid']] for row in manifest['views']}
    cameras = {}
    for row in checkpoint['cameras']:
        uid = row['uid']
        if uid in heldout:
            raise RuntimeError('Held-out image in training snapshot')
        if args.action.startswith('kf_') and row['sensor_type'] == 'rgb_dense':
            continue
        pose = torch.eye(4, device='cuda')
        pose[:3, :3] = row['R'].cuda(); pose[:3, 3] = row['T'].cuda()
        view = Camera.init_from_tracking(row['image'], None, None, pose, uid, proj, k)
        view.original_image_gpu = None
        view.sensor_type = row['sensor_type']
        cameras[uid] = view
    # Evaluation poses are isolated from all training camera construction above.
    trajectory = np.loadtxt(base / 'traj_full_beforeBA.txt')
    eval_poses = lietorch.SE3(torch.tensor(trajectory[:, 1:], dtype=torch.float32, device='cuda')).inv().matrix()
    calib = np.loadtxt(paths['calibration'])
    eval_views = []
    for uid in sorted(heldout):
        image, params = evaluator.preprocess_image(paths['image_dir'] / names[uid], calib, args.dataset != 'aria')
        evproj = getProjectionMatrix2(znear=.01, zfar=100., fx=params[0], fy=params[1],
                                     cx=params[2], cy=params[3], W=params[-2], H=params[-1]).T.cuda()
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
    output = root / args.action
    output.mkdir(exist_ok=False)
    initial_scores = evaluate(model)
    pose_updates = 0
    if args.pose_align_steps:
        # Frozen-map diagnostic: align training cameras only, with no evaluation
        # trajectory access. Additional renders/Adam steps are reported explicitly.
        from gaussian.utils.slam_utils import update_pose
        for view in cameras.values():
            if view.sensor_type != 'rgb_dense':
                continue
            params = (view.cam_rot_delta, view.cam_trans_delta)
            pose_optimizer = torch.optim.Adam(params, lr=checkpoint['opt_params']['pose_lr'])
            for _ in range(args.pose_align_steps):
                loss = dense_rgb_l1_ssim_loss(render(view, model, background)['render'],
                    view.original_image.cuda(), checkpoint['opt_params']['lambda_dssim'], compiled=False)
                grads = torch.autograd.grad(loss, params)
                for param, grad in zip(params, grads):
                    param.grad = grad
                pose_optimizer.step(); pose_optimizer.zero_grad(set_to_none=True)
                with torch.no_grad():
                    view.cam_rot_delta.clamp_(-1e-3, 1e-3)
                    view.cam_trans_delta.clamp_(-1e-3, 1e-3)
                    update_pose(view)
                pose_updates += 1
        if any(g['params'][0].grad is not None for g in model.optimizer.param_groups):
            raise RuntimeError('Pose-only alignment leaked map gradients')
    rng = random.Random(0)
    sequence = []
    while len(sequence) < args.steps:
        block = sorted(cameras); rng.shuffle(block); sequence.extend(block)
    sequence = sequence[:args.steps]
    write(output / 'selection.json', sequence)
    checkpoints = {min(250, args.steps), args.steps}
    curves = [{'steps': 0, 'mean_psnr': float(np.mean(initial_scores))}]
    torch.cuda.synchronize(); start = time.monotonic()
    for step, uid in enumerate(sequence, 1):
        view = cameras[uid]
        model.update_learning_rate(step)
        prediction = render(view, model, background)['render']
        loss = dense_rgb_l1_ssim_loss(prediction, view.original_image.cuda(),
                                      checkpoint['opt_params']['lambda_dssim'], compiled=False)
        loss.backward()
        if args.action.endswith('_sh'):
            for group in model.optimizer.param_groups:
                if group['name'] not in ('f_dc', 'f_rest'):
                    for param in group['params']:
                        param.grad = None
        model.optimizer.step(); model.optimizer.zero_grad(set_to_none=True)
        if step in checkpoints:
            scores = evaluate(model)
            curves.append({'steps': step, 'mean_psnr': float(np.mean(scores))})
            print(args.action, curves[-1], flush=True)
    torch.cuda.synchronize()
    elapsed = time.monotonic() - start
    model.save_ply(output / 'map.ply')
    saved = evaluator.load_gaussians(output / 'map.ply')
    repeat_scores = evaluate(saved)
    max_difference = float(np.max(np.abs(np.array(scores) - np.array(repeat_scores))))
    frozen_checks = {name: bool(torch.equal(getattr(model, '_' + name).detach().cpu(), p[name]))
                     for name in ('xyz', 'opacity', 'scaling', 'rotation')}
    result = {'protocol': 'offline_scope_diagnostic_v1', 'strict_online': False,
              'post_eos_optimizer_updates': args.steps, 'optimizer_state': 'restored_identical_snapshot',
              'training_pose_source': checkpoint['training_pose_source'],
              'checkpoint_sha256': digest(root / 'checkpoint.pt'),
              'selection_sha256': digest(output / 'selection.json'),
              'arm': args.action, 'training_views': len(cameras), 'heldout_views': len(heldout),
              'heldout_overlap': len(set(cameras) & heldout), 'curves': curves,
              'initial_psnr': curves[0]['mean_psnr'], 'final_psnr': curves[-1]['mean_psnr'],
              'gain_db': curves[-1]['mean_psnr'] - curves[0]['mean_psnr'],
              'same_gaussian_count': len(model.get_xyz) == len(p['xyz']),
              'additional_pose_optimizer_steps': pose_updates,
              'additional_pose_training_renders': pose_updates,
              'parameter_unchanged': frozen_checks, 'saved_reload_max_psnr_difference': max_difference,
              'wall_seconds_including_evaluation': elapsed}
    if max_difference > .01 or (args.action.endswith('_sh') and not all(frozen_checks.values())):
        raise RuntimeError('Scope or saved-map evaluation gate failed')
    write(output / 'result.json', result)


def main():
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['diagnostic', 'online', 'worker'])
    parser.add_argument('--dataset', required=True, choices=['aria', 'rpng', 'utmm'])
    parser.add_argument('--scene', required=True)
    parser.add_argument('--steps', type=int, default=1000)
    parser.add_argument('--action', default='capture')
    parser.add_argument('--result-root', type=Path, default=ROOT)
    parser.add_argument('--pose-align-steps', type=int, default=0)
    args = parser.parse_args()
    if args.steps <= 0:
        parser.error('steps must be positive')
    if args.pose_align_steps < 0:
        parser.error('pose-align-steps must be nonnegative')
    ROOT = args.result_root
    worker(args) if args.mode == 'worker' else launch(args)


if __name__ == '__main__':
    main()
