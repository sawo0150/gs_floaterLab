#!/usr/bin/env python3
"""Scope-only online diagnostic preserving every native RGB-D service slot.

An explicit process-local adapter widens only the existing single-view dense
replay gradient mask. The historical appearance-only CLI contract stays intact;
effective scope is asserted in telemetry and recorded separately in the result.
No production source, topology schedule, pose, admission or selector is changed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ONLINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ONLINE))
import run_exp94_normalized_metric_v2_fixed_eval as evaluation

BASE = evaluation.base
evaluation.panel.v2.install_inventory()
ROOT = BASE.WORKSPACE / 'results/campaigns/gain_attribution/dense_gain_recovery_online'
OLD = BASE.WORKSPACE / 'results/campaigns/gain_attribution/role_aware_dense_service_v3'


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def command(dataset, scene, output):
    cmd = read(OLD / dataset / scene / 'r4_backbone/mapping_command.json')
    cmd[cmd.index('--output') + 1] = str(output)
    cmd += ['--stage6r-aux-kf-to-dense-repeat']
    return cmd


def worker(args):
    import exp78b_replay_gsslam_mapping as replay
    original = replay.install_adam_guard
    def install(mapper, guard):
        if mapper._exp78b_replay_gradient_scope != 'appearance':
            raise RuntimeError('Unexpected input replay scope')
        mapper._exp78b_replay_gradient_scope = args.scope
        return original(mapper, guard)
    replay.install_adam_guard = install
    output = ROOT / args.dataset / args.scene / args.scope
    cmd = command(args.dataset, args.scene, output)
    sys.argv = cmd[1:]
    replay.main()
    runtime = read(output / 'mapping_replay_runtime.json')
    scopes = runtime['effective_replay_source_scope_optimizer_steps']
    if set(scopes) != {'dense:' + args.scope} or scopes['dense:' + args.scope] <= 0:
        raise RuntimeError('Effective scope mismatch: ' + repr(scopes))
    write(output / 'scope_override.json', {
        'protocol': 'dense_replay_scope_override_v1',
        'base_cli_scope': 'appearance', 'effective_scope': args.scope,
        'effective_optimizer_steps': scopes,
        'native_rgbd_scope_changed': False, 'topology_schedule_changed': False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', choices=['aria', 'utmm', 'rpng'], required=True)
    parser.add_argument('--scene', required=True)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--scope', choices=['appearance', 'full'], default='appearance')
    args = parser.parse_args()
    if args.worker:
        return worker(args)
    root = ROOT / args.dataset / args.scene
    source_paths = [Path(__file__), BASE.CUSTOM_HARNESS,
                    BASE.PAPER_ROOT / 'vigs/gs_backend.py', BASE.PAPER_ROOT / 'vigs/map_scheduler.py',
                    BASE.EVALUATOR]
    source = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    lock = root / 'source_lock.json'
    if lock.exists() and read(lock) != source:
        raise RuntimeError('Source lock changed')
    write(lock, source)
    runtimes, metrics = {}, {}
    for scope in ('appearance', 'full'):
        output = root / scope
        if not (output / 'scope_override.json').exists():
            if output.exists():
                raise FileExistsError('Incomplete output preserved: ' + str(output))
            evaluation.panel.v2.gpu_idle()
            cmd = [str(BASE.PYTHON_ENV / 'bin/python'), str(Path(__file__).resolve()),
                   '--worker', '--dataset', args.dataset, '--scene', args.scene, '--scope', scope]
            write(output / 'mapping_command.json', cmd)
            write(output / 'base_mapping_command.json', command(args.dataset, args.scene, output))
            with (output / 'mapping.log').open('x') as stream:
                subprocess.run(cmd, env=BASE.mapping_environment(True), stdout=stream,
                               stderr=subprocess.STDOUT, check=True)
        evaluation.panel.run_evaluation_twice(output, args.dataset, args.scene,
                                              BASE.sequence_paths(args.dataset, args.scene)['fixed_manifest'])
        runtimes[scope] = read(output / 'mapping_replay_runtime.json')
        metrics[scope] = read(output / 'psnr/strict_fixed_manifest/final_result.json')[
            'predeclared_fixed_manifest_posthoc']['mean_psnr']
        print(scope, metrics[scope], flush=True)
    a, b = runtimes['appearance'], runtimes['full']
    checks = {key: a[key] == b[key] for key in (
        'rasterized_view_updates', 'optimizer_steps_completed',
        'dense_registered_frame_uids', 'dense_selected_frame_uids',
        'archive_manifest_sha256', 'event_ids_fully_processed')}
    for scope, r in runtimes.items():
        for key in ('post_eos_optimizer_updates', 'heldout_mapping_overlap_count',
                    'heldout_gaussian_origin_overlap_count'):
            checks[scope + '_' + key] = r[key] == 0
    for key in ('fixed_event_dense_opportunity_ledger', 'fixed_event_dense_repeat_opportunity_ledger'):
        def trace(r):
            return [(row['event_id'], row['map_generation'], row['selected_keys']) for row in r[key]]
        checks[key + '_same_order'] = bool(a[key]) and trace(a) == trace(b)
    # Historical native selection may diverge if geometry changes maturation;
    # record that rather than pretending to freeze a downstream consequence.
    def native_trace(r):
        return [row['selected_uids'] for row in r['stage6r_native_global_keyframe_selection_ledger']]
    report = {'protocol': 'online_auxiliary_dense_scope_pair_v1', 'checks': checks,
              'valid': all(checks.values()), 'heldout_psnr': metrics,
              'full_minus_appearance': metrics['full'] - metrics['appearance'],
              'same_native_history_selection': native_trace(a) == native_trace(b),
              'mapping_only_unbounded': True, 'strict_live_claim': False}
    write(root / 'pair.json', report)
    if not report['valid']:
        raise RuntimeError('Scope pair work/admission/order contract failed; inspect pair.json')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
