#!/usr/bin/env python3
"""Preregistered three-scene transfer; production and previous runners unchanged."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import run_dense_scope_online as common

BASE = common.BASE
ROOT = BASE.WORKSPACE / 'results/campaigns/gain_attribution/visual_pose_transfer'
SCENES = [('rpng', 'table_06'), ('utmm', 'square-1'), ('utmm', 'ego-centric-1')]
WEIGHTS = BASE.PAPER_ROOT / 'pretrained_models/droid.pth'


def command(dataset, scene, output, online=False):
    cmd = BASE.mapping_command('candidate', dataset, scene, ROOT)
    cmd[cmd.index('--output') + 1] = str(output)
    cmd += ['--ercb-selection-potential', 'normalized_variance',
            '--dense-topology-first-persistence-ticket']
    if online:
        cmd += ['--stage6r-aux-kf-to-dense-repeat']
    return cmd


def equal(a, b):
    import torch
    if isinstance(a, torch.Tensor):
        return torch.equal(a, b)
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def refine_snapshot(dataset, scene):
    import torch
    from causal_visual_dense_pose import VisualRefiner
    from dense_pose_refresh_repair import bracket
    source = ROOT / 'fixed_original' / dataset / scene
    output = ROOT / 'fixed_visual' / dataset / scene
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = torch.load(source / 'checkpoint.pt', map_location='cpu', weights_only=False)
    k = checkpoint['K']
    views = {r['uid']: SimpleNamespace(uid=r['uid'], original_image=r['image'], depth=r['depth'],
             R=r['R'].cuda(), T=r['T'].cuda(), image_height=int(k[-1]), image_width=int(k[-2]),
             fx=k[0], fy=k[1], cx=k[2], cy=k[3]) for r in checkpoint['cameras']}
    kf = sorted(r['uid'] for r in checkpoint['cameras'] if r['sensor_type'] != 'rgb_dense')
    refiner = VisualRefiner(WEIGHTS)
    audit = {'calls': [], 'skipped': [], 'strict_online': False,
             'post_eos_pose_refinement': True, 'network_load_seconds': refiner.load_seconds}
    torch.cuda.synchronize()
    start = time.perf_counter()
    for row in checkpoint['cameras']:
        if row['sensor_type'] != 'rgb_dense':
            continue
        pair = bracket(kf, row['uid'])
        if pair is None:
            audit['skipped'].append(row['uid'])
            continue
        value, stats = refiner.refine(views[pair[0]], views[pair[1]], views[row['uid']])
        row['R'], row['T'] = value[:3, :3].cpu().clone(), value[:3, 3].cpu().clone()
        audit['calls'].append({'uid': row['uid'], 'left': pair[0], 'right': pair[1], **stats})
    torch.cuda.synchronize()
    audit['pose_wall_seconds'] = time.perf_counter() - start
    parent = torch.load(source / 'checkpoint.pt', map_location='cpu', weights_only=False)
    checks = {'gaussians_adam_unchanged': equal(checkpoint['gaussians'], parent['gaussians']),
              'same_camera_count': len(checkpoint['cameras']) == len(parent['cameras']),
              'noncamera_fields_unchanged': all(equal(checkpoint[k], parent[k])
                  for k in checkpoint if k != 'cameras'),
              'only_dense_pose_changed': all(equal(row[k], old[k])
                  for row, old in zip(checkpoint['cameras'], parent['cameras'])
                  for k in row if k not in ({'R', 'T'} if row['sensor_type'] == 'rgb_dense' else set())),
              'anchors_depth_fixed': all(r['anchor_pose_unchanged'] and r['depth_unchanged']
                                        for r in audit['calls']),
              'pose_refinement_exercised': bool(audit['calls'])}
    audit['checks'] = checks
    if not all(checks.values()):
        raise RuntimeError('Pose-only snapshot contract failed')
    checkpoint['training_pose_source'] = 'snapshot training KF anchors; dense visual6 at EOS; no evaluation poses'
    torch.save(checkpoint, output / 'checkpoint.pt')
    (output / 'base').symlink_to(source / 'base', target_is_directory=True)
    common.write(output / 'pose_refinement.json', audit)


def worker(args):
    if args.action == 'refine':
        return refine_snapshot(args.dataset, args.scene)
    if args.action in ('capture', 'kf_full', 'mixed_full', 'visual_full'):
        import recover_dense_supervision as diagnostic
        diagnostic.command = command
        diagnostic.ROOT = ROOT / ('fixed_visual' if args.action == 'visual_full' else 'fixed_original')
        diagnostic.worker(SimpleNamespace(dataset=args.dataset, scene=args.scene,
            action='mixed_full' if args.action == 'visual_full' else args.action,
            steps=5000, pose_align_steps=0))
        return
    import torch
    import exp78b_replay_gsslam_mapping as replay
    from dense_pose_refresh_repair import install as repair
    from causal_visual_dense_pose import install as visual
    instances = []
    def install(mapper, shaper):
        repair(mapper, shaper)
        if args.action == 'online_visual':
            visual(mapper, WEIGHTS, set(shaper.archive.heldout_uids))
        instances.append(mapper)
    replay.install_dense_imu_pose_refresh = install
    common.ROOT = ROOT / args.action
    common.command = lambda d, s, o: command(d, s, o, online=True)
    common.worker(SimpleNamespace(dataset=args.dataset, scene=args.scene, scope='full'))
    mapper = instances[-1]
    out = ROOT / args.action / args.dataset / args.scene / 'full'
    audit = mapper._dense_pose_refresh_repair_audit
    if audit['future_imu_used'] or not audit['refreshed_views']:
        raise RuntimeError('Repair causal/execution check failed')
    common.write(out / 'refresh_repair.json', audit)
    if args.action == 'online_visual':
        common.write(out / 'visual_pose.json', mapper._visual_pose_audit)
        torch.save(mapper._visual_pose_latest, out / 'causal_refined_poses.pt')


def run_action(dataset, scene, action):
    if action.startswith('online_'):
        out = ROOT / action / dataset / scene / 'full'
        target = out / ('visual_pose.json' if action == 'online_visual' else 'refresh_repair.json')
    else:
        root = ROOT / ('fixed_visual' if action in ('refine', 'visual_full') else 'fixed_original') / dataset / scene
        target = (root / 'checkpoint.pt' if action == 'capture' else
                  root / 'pose_refinement.json' if action == 'refine' else
                  root / ('mixed_full' if action == 'visual_full' else action) / 'result.json')
    if target.exists():
        return
    common.evaluation.panel.v2.gpu_idle()
    log = ROOT / 'logs' / dataset / scene / (action + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(BASE.PYTHON_ENV / 'bin/python'), str(Path(__file__).resolve()),
           '--worker', '--dataset', dataset, '--scene', scene, '--action', action]
    common.write(log.with_suffix('.command.json'), cmd)
    with log.open('x') as stream:
        subprocess.run(cmd, env=BASE.mapping_environment(True), stdout=stream,
                       stderr=subprocess.STDOUT, check=True)
    if not target.exists():
        raise RuntimeError('Missing completion artifact: ' + str(target))
    print('COMPLETED', dataset, scene, action, flush=True)


def compare_fixed(dataset, scene):
    original = ROOT / 'fixed_original' / dataset / scene
    visual = ROOT / 'fixed_visual' / dataset / scene
    kf = common.read(original / 'kf_full/result.json')
    old = common.read(original / 'mixed_full/result.json')
    new = common.read(visual / 'mixed_full/result.json')
    audit = common.read(visual / 'pose_refinement.json')
    checks = {k: old[k] == new[k] for k in ['initial_psnr', 'selection_sha256', 'training_views',
               'heldout_views', 'heldout_overlap', 'post_eos_optimizer_updates']}
    checks.update({'kf_initial_same': kf['initial_psnr'] == old['initial_psnr'],
                   'kf_checkpoint_same': kf['checkpoint_sha256'] == old['checkpoint_sha256'],
                   'snapshot_pose_only': all(audit['checks'].values()),
                   'all_disjoint_fixed_topology_reload': all(r['heldout_overlap'] == 0 and
                       r['same_gaussian_count'] and r['saved_reload_max_psnr_difference'] <= .01
                       for r in [kf, old, new])})
    report = {'valid': all(checks.values()), 'checks': checks,
              'psnr': {'kf_only': kf['final_psnr'], 'original_dense': old['final_psnr'],
                       'visual_dense': new['final_psnr']},
              'visual_minus_original': new['final_psnr'] - old['final_psnr'],
              'visual_minus_kf': new['final_psnr'] - kf['final_psnr'],
              'curves': {key: row['curves'] for key, row in [('kf_only', kf), ('original_dense', old), ('visual_dense', new)]},
              'extra_pose_seconds': audit['pose_wall_seconds'], 'pose_calls': len(audit['calls']),
              'strict_online': False, 'total_compute_matched': False}
    common.write(ROOT / 'comparisons' / dataset / scene / 'fixed.json', report)
    print('FIXED_RESULT', dataset, scene, json.dumps(report), flush=True)
    if not report['valid']:
        raise RuntimeError('Fixed comparison invalid')


def compare_online(dataset, scene):
    paths = [ROOT / a / dataset / scene / 'full' for a in ['online_control', 'online_visual']]
    for path in paths:
        common.evaluation.panel.run_evaluation_twice(path, dataset, scene,
            BASE.sequence_paths(dataset, scene)['fixed_manifest'])
    a, b = [common.read(p / 'mapping_replay_runtime.json') for p in paths]
    checks = {k: a[k] == b[k] for k in ['rasterized_view_updates', 'optimizer_steps_completed',
              'dense_registered_frame_uids', 'archive_manifest_sha256', 'event_ids_fully_processed']}
    for key in ['fixed_event_dense_opportunity_ledger', 'fixed_event_dense_repeat_opportunity_ledger']:
        checks[key] = [(r['event_id'], r['map_generation'], r['selected_keys']) for r in a[key]] == [
            (r['event_id'], r['map_generation'], r['selected_keys']) for r in b[key]]
    for key in ['post_eos_optimizer_updates', 'heldout_mapping_overlap_count', 'heldout_gaussian_origin_overlap_count']:
        checks[key] = a[key] == b[key] == 0
    audit = common.read(paths[1] / 'visual_pose.json')
    checks['causal_brackets'] = bool(audit['calls']) and all(
        r['left'] < r['uid'] < r['right'] <= r['latest_mapper_kf'] for r in audit['calls'])
    checks['anchors_depth_fixed'] = all(r['anchor_pose_unchanged'] and r['depth_unchanged'] for r in audit['calls'])
    scores = [common.read(p / 'psnr/strict_fixed_manifest/final_result.json')[
        'predeclared_fixed_manifest_posthoc']['mean_psnr'] for p in paths]
    native_key = 'stage6r_native_global_keyframe_selection_ledger'
    report = {'valid': all(checks.values()), 'checks': checks,
              'psnr': dict(zip(['control', 'visual'], scores)), 'visual_minus_control': scores[1] - scores[0],
              'same_native_history_selection': [r['selected_uids'] for r in a[native_key]] ==
                  [r['selected_uids'] for r in b[native_key]],
              'mapping_seconds': {'control': a['mapping_wall_seconds'], 'visual': b['mapping_wall_seconds']},
              'extra_pose_seconds': audit['wall_seconds'], 'network_load_seconds': audit['network_load_seconds'],
              'pose_calls': len(audit['calls']), 'mapping_renders': b['rasterized_view_updates'],
              'mapping_adam_steps': b['optimizer_steps_completed'],
              'strict_live_claim': False, 'total_compute_matched': False}
    common.write(ROOT / 'comparisons' / dataset / scene / 'online.json', report)
    print('ONLINE_RESULT', dataset, scene, json.dumps(report), flush=True)
    if not report['valid']:
        raise RuntimeError('Online comparison invalid')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker', action='store_true')
    p.add_argument('--dataset'); p.add_argument('--scene'); p.add_argument('--action')
    p.add_argument('--phase', choices=['fixed', 'online', 'all'], default='all')
    args = p.parse_args()
    if args.worker:
        return worker(args)
    sources = [Path(__file__), Path(common.__file__), BASE.CUSTOM_HARNESS, BASE.EVALUATOR,
        WEIGHTS, BASE.PAPER_ROOT / 'vigs/gs_backend.py', BASE.PAPER_ROOT / 'vigs/map_scheduler.py',
        BASE.PAPER_ROOT / 'vigs/factor_graph.py', BASE.PAPER_ROOT / 'vigs/depth_video.py']
    sources += [Path(__file__).with_name(f) for f in ['recover_dense_supervision.py',
                'causal_visual_dense_pose.py', 'dense_pose_refresh_repair.py']]
    for dataset, scene in SCENES:
        paths = BASE.sequence_paths(dataset, scene)
        sources += [paths['custom_config'], paths['fixed_manifest'], paths['archive'] / 'archive_manifest.json']
        if not paths['image_dir'].is_dir():
            raise FileNotFoundError(paths['image_dir'])
    hashes = {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}
    lock = ROOT / 'source_lock.json'
    if lock.exists() and common.read(lock) != hashes:
        raise RuntimeError('Source lock changed; preserve results and use a new root')
    common.write(lock, hashes)
    common.write(ROOT / 'contract.json', {'scenes': SCENES, 'seed': 0, 'steps': 5000,
        'visual_motion_updates': 6, 'selection': 'RR in fixed-map', 'no_scene_tuning': True})
    scenes = [(args.dataset, args.scene)] if args.dataset else SCENES
    if any(s not in SCENES for s in scenes):
        raise ValueError('Not a preregistered scene')
    for dataset, scene in scenes:
        if args.phase in ('fixed', 'all'):
            for action in ['capture', 'kf_full', 'mixed_full', 'refine', 'visual_full']:
                run_action(dataset, scene, action)
            compare_fixed(dataset, scene)
        if args.phase in ('online', 'all'):
            for action in ['online_control', 'online_visual']:
                run_action(dataset, scene, action)
            compare_online(dataset, scene)


if __name__ == '__main__':
    main()
