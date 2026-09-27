#!/usr/bin/env python3
"""Clocked 1.5x online photometric ablation, with explicit goal evidence."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time

import run_dense_scope_online as common

BASE = common.BASE
BACKEND = Path('/home/intern/VIGS-SLAM-online-view-training')
ROOT = BASE.WORKSPACE / 'results/campaigns/gain_attribution/online_dense_training'
SCENES = [('aria', 'aria1253'), ('rpng', 'table_06'), ('utmm', 'square-1')]
ARMS = ['production', 'kf_only', 'immediate_rr', 'growth_rr', 'growth_ervs']


def base_command(args, output):
    if args.arm == 'production':
        cmd = BASE.mapping_command('candidate', args.dataset, args.scene, ROOT)
        cmd[cmd.index('--output')+1] = str(output)
        cmd[cmd.index('--seed')+1] = str(args.seed)
        return cmd + ['--ercb-selection-potential', 'normalized_variance']
    paths = BASE.sequence_paths(args.dataset, args.scene)
    return [str(BASE.PYTHON_ENV / 'bin/python'), str(BASE.CUSTOM_HARNESS),
        '--archive', str(paths['archive']), '--output', str(output),
        '--config', str(paths['custom_config']), '--seed', str(args.seed),
        '--time-scale', 'unbounded', '--deadline-reserve-ms', '20',
        '--profile', 'dense_rr_imu',
        '--density-policy', 'online_rank', '--online-density-mean-multiplier', '2.5',
        '--online-density-span', '2.0', '--observation-topology-gate',
        '--dense-replay-scope', 'full']


def command(args, output):
    cmd = base_command(args, output)
    flag = '--deadline-reserve-ms'
    if flag in cmd:
        cmd[cmd.index(flag) + 1] = str(args.deadline_reserve_ms)
    else:
        cmd += [flag, str(args.deadline_reserve_ms)]
    return cmd


def environment():
    env = BASE.mapping_environment(True)
    env['EXP78B_CUSTOM_ROOT'] = str(BACKEND)
    env['PYTHONPATH'] = str(BACKEND / 'vigs') + ':' + str(BACKEND) + ':' + env.get('PYTHONPATH', '')
    return env


def worker(args, output):
    import exp78b_replay_gsslam_mapping as replay
    io_audit = {'calls': 0, 'cache_misses': 0, 'wall_seconds': 0.}
    snapshots = None
    if args.arm != 'production':
        from dense_pose_refresh_repair import install as repair
        replay.install_dense_imu_pose_refresh = repair

    def configure(mapper, archive, parsed, guard):
        nonlocal snapshots
        original_rgb = archive.load_rgb
        def load_rgb(uid):
            io_audit['calls'] += 1
            io_audit['cache_misses'] += int(int(uid) not in archive._rgb_cache)
            started = time.monotonic()
            try:
                return original_rgb(uid)
            finally:
                io_audit['wall_seconds'] += time.monotonic() - started
        archive.load_rgb = load_rgb
        if args.snapshots:
            from online_map_snapshots import StreamSnapshots, install as install_observer
            duration = 1.5 * (float(archive.arrivals[-1]['sensor_timestamp']) - float(archive.arrivals[0]['sensor_timestamp']))
            snapshots = StreamSnapshots(start=guard.deadline - duration, deadline=guard.deadline,
                                        heldout=archive.heldout_uids)
            install_observer(mapper, snapshots, guard)
        if args.arm == 'production':
            return
        from online_photometric import OnlinePhotometricTrainer
        membership = 'kf_only' if args.arm == 'kf_only' else 'immediate' if args.arm == 'immediate_rr' else 'growth'
        selector = 'ervs' if args.arm == 'growth_ervs' else 'rr'
        mapper.online_view_trainer = OnlinePhotometricTrainer(mapper,
            heldout=set(archive.heldout_uids), membership=membership, selector=selector,
            seed=args.seed, guard=guard, kappa=args.kappa, tau=args.tau,
            entropy_weight_policy=args.entropy_weight_policy,
            selection_count_scope=args.selection_count_scope,
            growth_budget_scope=args.growth_budget_scope)
        if membership != 'kf_only':
            from dense_visual_pose import install
            options = {}
            if args.reuse_dense_correspondences:
                from dense_visual_pose_reuse import CorrespondenceRefiner
                options['engine_class'] = CorrespondenceRefiner
            if args.audit_dense_pose_fit:
                from dense_pose_quality_refiner import QualityAuditedRefiner
                options['engine_class'] = QualityAuditedRefiner
            install(mapper, BASE.PAPER_ROOT / 'pretrained_models/droid.pth',
                    set(archive.heldout_uids), **options)
            if args.lazy_dense_refresh:
                from dense_pose_lazy_refresh import install as install_lazy
                install_lazy(mapper)
            if args.defer_dense_preparation:
                from deferred_dense_observations import DeferredDenseObservations
                mapper.deferred_dense_observations = DeferredDenseObservations(mapper, archive, guard)

    def dense_input(mapper, metadata, shaper):
        store = mapper.deferred_dense_observations
        before = len(store.records)
        store.ingest(metadata, shaper)
        return len(store.records) - before

    def idle(mapper, next_arrival, deadline, guard):
        if not mapper.initialized or not mapper.current_window:
            return False
        mapper.online_view_trainer.next_arrival = next_arrival
        return bool(mapper.map(mapper.current_window, iters=1, photometric_only=True))

    def complete(mapper, archive, parsed, guard, stats):
        common.write(output / 'archive_rgb_audit.json', io_audit)
        if snapshots is not None:
            snapshots.write(output / 'stream_snapshots')
        report = {'protocol': 'clocked_online_view_training_v1', 'time_scale': 1.5,
            'arm': args.arm, 'seed': args.seed, 'deadline': guard.deadline,
            'optimizer_completion_times': guard.optimizer_completion_times,
            'optimizer_completions_after_deadline': sum(t > guard.deadline for t in guard.optimizer_completion_times),
            'strict_tracking_claim': False}
        if args.arm != 'production':
            trainer = mapper.online_view_trainer
            report['training'] = trainer.report()
            native = sum(sum(r['source'] == 'native' for r in g['services']) for g in trainer.report()['generations'])
            photo = trainer.photometric_steps
            report['shared_count_matches_optimizer'] = native + photo == guard.main_gaussian_steps_completed
            report['native_commits'] = native
            report['photometric_commits'] = photo
            report['photometric_count_matches_optimizer'] = sum(
                sum(g['policy']['photometric_counts'].values())
                for g in report['training']['generations']) == photo
            if not report['shared_count_matches_optimizer']:
                raise RuntimeError('Actual Gaussian optimizer/count history disagree')
            if not report['photometric_count_matches_optimizer']:
                raise RuntimeError('Dedicated photometric counts disagree with completed optimizer steps')
            report['growth_capacity_valid'] = all(
                g['policy']['growth_budget_scope'] == args.growth_budget_scope
                and all(a['growth_budget_scope'] == args.growth_budget_scope
                        and (args.growth_budget_scope != 'whole_pool'
                             or g['policy']['membership'] != 'growth'
                             or a['pool_size_after'] <= a['rgb_steps'] // args.kappa)
                        for a in g['admissions'])
                for g in report['training']['generations'])
            if not report['growth_capacity_valid']:
                raise RuntimeError('Dense admission exceeded declared growth capacity')
            report['recent_count_history_matches_services'] = True
            if args.selection_count_scope == 'recent_photometric':
                from collections import Counter
                for generation in report['training']['generations']:
                    policy = generation['policy']
                    history = [uid for service in generation['services']
                               if service['source'] == 'photometric' for uid in service['uids']]
                    uids = sorted(set(policy['keyframes']) | set(policy['admitted_dense']))
                    # Reconstruct independently from actual committed service
                    # records, including empty map generations and cancellation.
                    retained = max(0, len(uids) - 1)
                    expected = Counter(history[-retained:]) if retained else Counter()
                    valid = (policy['recent_history_length'] == len(history)
                             and policy['recent_window_size'] == len(uids)
                             and policy['next_draw_counts'] == {uid: expected[uid] for uid in uids})
                    report['recent_count_history_matches_services'] &= valid
                if not report['recent_count_history_matches_services']:
                    raise RuntimeError('Recent selection counts disagree with committed service history')
            if hasattr(mapper, '_visual_pose_audit'):
                common.write(output / 'visual_pose.json', mapper._visual_pose_audit)
            if hasattr(mapper, '_dense_pose_refresh_repair_audit'):
                common.write(output / 'refresh_repair.json', mapper._dense_pose_refresh_repair_audit)
            if hasattr(mapper, '_lazy_dense_refresh_audit'):
                common.write(output / 'lazy_refresh.json', mapper._lazy_dense_refresh_audit)
            if hasattr(mapper, '_sparse_dense_refresh_audit'):
                common.write(output / 'sparse_refresh.json', mapper._sparse_dense_refresh_audit)
            if hasattr(mapper, 'deferred_dense_observations'):
                common.write(output / 'deferred_dense.json', mapper.deferred_dense_observations.audit)
        common.write(output / 'online_training.json', report)
        if report['optimizer_completions_after_deadline']:
            raise RuntimeError('Optimizer completed after stream deadline')
        if args.arm != 'production':
            return [uid for uid, count in mapper.online_view_trainer.policy.counts.items() if count > 0]

    sys.argv = command(args, output)[1:]
    replay.main(clocked_time_scale=1.5, configure_mapper=configure,
                idle_callback=None if args.arm == 'production' else idle,
                completion_callback=complete, skip_dense_input=args.arm == 'kf_only',
                dense_callback=dense_input if args.defer_dense_preparation else None,
                include_mapper_setup_in_clock=args.include_mapper_setup_in_clock)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', required=True); p.add_argument('--scene', required=True)
    p.add_argument('--arm', choices=ARMS, required=True)
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--kappa', type=int, default=16)
    p.add_argument('--tau', type=float, default=.01)
    p.add_argument('--entropy-weight-policy', choices=['fixed', 'per_view'], default='fixed')
    p.add_argument('--selection-count-scope', choices=['all_rgb', 'photometric', 'recent_photometric'], default='all_rgb')
    p.add_argument('--growth-budget-scope', choices=['dense_only', 'whole_pool'], default='dense_only')
    p.add_argument('--lazy-dense-refresh', action='store_true')
    p.add_argument('--defer-dense-preparation', action='store_true')
    p.add_argument('--reuse-dense-correspondences', action='store_true')
    p.add_argument('--audit-dense-pose-fit', action='store_true')
    p.add_argument('--snapshots', action='store_true')
    p.add_argument('--include-mapper-setup-in-clock', action='store_true')
    p.add_argument('--deadline-reserve-ms', type=float, default=20.)
    p.add_argument('--tag', default='v1')
    p.add_argument('--worker', action='store_true')
    args = p.parse_args()
    if (args.dataset, args.scene) not in SCENES:
        raise ValueError('Scene outside preregistered goal')
    if args.kappa <= 0:
        raise ValueError('kappa must be positive')
    if not math.isfinite(args.tau) or args.tau <= 0:
        raise ValueError('tau must be finite and positive')
    if args.lazy_dense_refresh and args.arm in ('production', 'kf_only'):
        raise ValueError('Lazy dense refresh requires a dense training arm')
    if args.defer_dense_preparation and not args.lazy_dense_refresh:
        raise ValueError('Deferred image preparation requires current-anchor refresh')
    if args.reuse_dense_correspondences and not args.defer_dense_preparation:
        raise ValueError('Correspondence-reuse comparison requires deferred preparation')
    if args.audit_dense_pose_fit and not args.reuse_dense_correspondences:
        raise ValueError('Pose-fit audit requires the correspondence-reuse refiner')
    if args.deadline_reserve_ms <= 0:
        raise ValueError('Deadline reserve must be positive')
    output = ROOT / args.tag / args.dataset / args.scene / args.arm / f'seed{args.seed}'
    if args.worker:
        return worker(args, output)
    dependency_probe = Path(__file__).with_name('online_runtime_dependencies.py')
    dependencies = json.loads(subprocess.check_output(
        [str(BASE.PYTHON_ENV / 'bin/python'), str(dependency_probe)],
        env=environment(), text=True))
    dependency_lock = output / 'native_dependencies.json'
    if dependency_lock.exists() and common.read(dependency_lock) != dependencies:
        raise RuntimeError('Runtime dependencies changed: preserve attempt and use a new tag')
    common.write(dependency_lock, dependencies)
    sources = [Path(__file__), BASE.CUSTOM_HARNESS,
        BACKEND / 'vigs/gs_backend.py', BACKEND / 'vigs/online_view_training.py',
        BACKEND / 'vigs/online_photometric.py', BACKEND / 'vigs/dense_visual_pose.py',
        BACKEND / 'vigs/dense_pose_inputs.py', BACKEND / 'vigs/dense_pose_lazy_refresh.py',
        BACKEND / 'vigs/deferred_dense_observations.py', BACKEND / 'vigs/online_map_snapshots.py',
        BACKEND / 'vigs/dense_visual_pose_reuse.py',
        BACKEND / 'vigs/dense_pose_quality.py', BACKEND / 'vigs/dense_pose_quality_refiner.py',
        BACKEND / 'vigs/dense_pose_sparse_refresh.py',
        BACKEND / 'vigs/recent_selection_counts.py',
        Path(__file__).with_name('dense_pose_refresh_repair.py'), BASE.EVALUATOR,
        BASE.PAPER_ROOT / 'pretrained_models/droid.pth',
        BASE.WORKSPACE / 'benchmarks/online_gs/exp78b_timeline_scheduler.py']
    sources += [dependency_probe] + [Path(v['path']) for v in dependencies['files'].values()]
    paths = BASE.sequence_paths(args.dataset, args.scene)
    sources += [paths['custom_config'], paths['fixed_manifest'], paths['archive'] / 'archive_manifest.json']
    hashes = {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}
    lock = output / 'source_lock.json'
    if lock.exists() and common.read(lock) != hashes:
        raise RuntimeError('Source changed: preserve attempt and use a new tag')
    common.write(lock, hashes)

    def check_source_lock():
        changed = [name for name, digest in hashes.items()
                   if not Path(name).is_file() or hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest]
        if changed:
            common.write(output / 'source_change_failure.json', {'changed_files': changed})
            raise RuntimeError('Sources or native libraries changed during the run: ' + ', '.join(changed))

    contract = {'dataset': args.dataset, 'scene': args.scene, 'arm': args.arm,
                'seed': args.seed, 'kappa': args.kappa, 'tau': args.tau, 'time_scale': 1.5,
                'entropy_weight_policy': args.entropy_weight_policy,
                'selection_count_scope': args.selection_count_scope,
                'growth_budget_scope': args.growth_budget_scope,
                'lazy_dense_refresh': args.lazy_dense_refresh, 'pose_measurement_cache': True,
                'defer_dense_preparation': args.defer_dense_preparation, 'snapshots': args.snapshots,
                'reuse_dense_correspondences': args.reuse_dense_correspondences,
                'audit_dense_pose_fit': args.audit_dense_pose_fit,
                'include_mapper_setup_in_clock': args.include_mapper_setup_in_clock,
                'input_boundary_guards': True,
                'deadline_reserve_ms': args.deadline_reserve_ms}
    contract_path = output / 'contract.json'
    if contract_path.exists() and common.read(contract_path) != contract:
        raise RuntimeError('Changed policy parameters: use a new tag')
    common.write(contract_path, contract)
    common.write(output / 'base_mapping_command.json', command(args, output))
    if not (output / 'mapping_replay_runtime.json').exists():
        common.evaluation.panel.v2.gpu_idle()
        cmd = [str(BASE.PYTHON_ENV / 'bin/python'), str(Path(__file__).resolve()),
            '--worker', '--dataset', args.dataset, '--scene', args.scene,
            '--arm', args.arm, '--seed', str(args.seed), '--tag', args.tag,
            '--kappa', str(args.kappa), '--tau', str(args.tau),
            '--entropy-weight-policy', args.entropy_weight_policy,
            '--selection-count-scope', args.selection_count_scope,
            '--growth-budget-scope', args.growth_budget_scope]
        cmd += ['--deadline-reserve-ms', str(args.deadline_reserve_ms)]
        if args.lazy_dense_refresh:
            cmd.append('--lazy-dense-refresh')
        if args.defer_dense_preparation:
            cmd.append('--defer-dense-preparation')
        if args.reuse_dense_correspondences:
            cmd.append('--reuse-dense-correspondences')
        if args.audit_dense_pose_fit:
            cmd.append('--audit-dense-pose-fit')
        if args.snapshots:
            cmd.append('--snapshots')
        if args.include_mapper_setup_in_clock:
            cmd.append('--include-mapper-setup-in-clock')
        common.write(output / 'command.json', cmd)
        with (output / 'mapping.log').open('x') as log:
            subprocess.run(cmd, env=environment(), stdout=log, stderr=subprocess.STDOUT, check=True)
    check_source_lock()
    common.evaluation.panel.run_evaluation_twice(output, args.dataset, args.scene, paths['fixed_manifest'])
    check_source_lock()
    metrics = common.read(output / 'psnr/strict_fixed_manifest/final_result.json')
    runtime = common.read(output / 'mapping_replay_runtime.json')
    audit = common.read(output / 'online_training.json')
    result = {'heldout_psnr': metrics['predeclared_fixed_manifest_posthoc']['mean_psnr'],
        'checks': {'finite_clock': runtime['time_scale'] == '1.5',
            'zero_tail': runtime['post_eos_optimizer_updates'] == 0,
            'no_deadline_overrun': audit['optimizer_completions_after_deadline'] == 0,
            'total_mapping_within_budget': runtime['mapping_wall_seconds'] <= runtime['budget_seconds'],
            'declared_setup_clock_matches': runtime['mapper_setup_in_mapping_clock'] == args.include_mapper_setup_in_clock,
            'input_boundary_guards': runtime['input_boundary_guards'],
            'photometric_count_history': args.arm == 'production' or audit['photometric_count_matches_optimizer'],
            'recent_count_history': args.arm == 'production' or audit['recent_count_history_matches_services'],
            'growth_capacity': args.arm == 'production' or audit['growth_capacity_valid'],
            'heldout_disjoint': runtime['heldout_mapping_overlap_count'] == runtime['heldout_gaussian_origin_overlap_count'] == 0},
        'mapping_seconds': runtime['mapping_wall_seconds'], 'budget_seconds': runtime['budget_seconds'],
        'mapping_overrun_seconds': max(0., runtime['mapping_wall_seconds'] - runtime['budget_seconds']),
        'render_count': runtime['rasterized_view_updates'], 'optimizer_steps': runtime['optimizer_steps_completed']}
    result['valid'] = all(result['checks'].values())
    common.write(output / 'result.json', result)
    print(json.dumps(result), flush=True)
    if not result['valid']:
        raise RuntimeError('Clocked online contract failed')


if __name__ == '__main__':
    main()
