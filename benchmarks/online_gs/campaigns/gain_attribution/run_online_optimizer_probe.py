#!/usr/bin/env python3
"""Instrument actual native/photo Adam work without changing mapper policy."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import run_online_dense_training as trial


ROOT = trial.ROOT / 'optimizer_scale_audit/v2_online_probe'


def worker(dataset, scene, output):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    import exp78b_replay_gsslam_mapping as replay
    from optimizer_moment_probe import install
    original_main = replay.main
    report = None

    def observed_main(**kwargs):
        original_configure = kwargs['configure_mapper']
        original_complete = kwargs['completion_callback']

        def configure(mapper, archive, parsed, guard):
            nonlocal report
            original_configure(mapper, archive, parsed, guard)
            report = install(mapper, guard, set(archive.heldout_uids))

        def complete(mapper, archive, parsed, guard, stats):
            result = original_complete(mapper, archive, parsed, guard, stats)
            services = {(g['policy']['generation'], row['step']): row
                for g in mapper.online_view_trainer.report()['generations'] for row in g['services']}
            errors = []
            for row in report['records']:
                expected = services.get((row['generation'], row['next_service_step']))
                source = 'native' if row['source'] == 'native' else 'photometric'
                if (expected is None or expected['source'] != source
                        or list(expected['uids']) != row['uids']):
                    errors.append({'record': row, 'actual_service': expected})
            report['ledger_errors'] = errors
            report['ledger_matches'] = not errors
            report['heldout_overlap'] = sorted({uid for row in report['records'] for uid in row['uids']} & archive.heldout_uids)
            report['notes'] = 'Sampled-coordinate diagnostics include observer time in the clock; not a quality comparison. wall_seconds includes measured optimizer time.'
            trial.common.write(output / 'optimizer_probe.json', report)
            if errors or report['heldout_overlap']:
                raise RuntimeError('Optimizer diagnostic/service ledger mismatch')
            return result

        kwargs['configure_mapper'], kwargs['completion_callback'] = configure, complete
        return original_main(**kwargs)

    replay.main = observed_main
    args = SimpleNamespace(dataset=dataset, scene=scene, arm='growth_ervs', seed=0,
        kappa=64, tau=1., entropy_weight_policy='per_view', selection_count_scope='recent_photometric',
        lazy_dense_refresh=True, defer_dense_preparation=True, reuse_dense_correspondences=True,
        audit_dense_pose_fit=False, snapshots=True, include_mapper_setup_in_clock=True,
        deadline_reserve_ms=100.)
    trial.worker(args, output)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker', action='store_true')
    p.add_argument('--dataset'); p.add_argument('--scene')
    args = p.parse_args()
    if args.worker:
        return worker(args.dataset, args.scene, ROOT / args.dataset / args.scene)
    ROOT.mkdir(parents=True, exist_ok=False)
    source_paths = list(trial.common.read(trial.ROOT / 'source_v17/index.json'))
    source_paths += [str(Path(__file__).resolve()), str(Path(__file__).with_name('optimizer_moment_probe.py').resolve()),
                     str(Path(__file__).with_name('test_optimizer_moment_probe.py').resolve())]
    hashes = {}
    source_dir = ROOT / 'sources'; source_dir.mkdir()
    for name in source_paths:
        path = Path(name); data = path.read_bytes(); digest = hashlib.sha256(data).hexdigest()
        hashes[str(path)] = digest
        (source_dir / (digest[:12] + '_' + path.name)).write_bytes(data)
    trial.common.write(ROOT / 'source_lock.json', hashes)
    dependency_probe = Path(__file__).with_name('online_runtime_dependencies.py')
    dependency_command = [str(trial.BASE.PYTHON_ENV / 'bin/python'), str(dependency_probe)]
    dependencies = json.loads(subprocess.check_output(dependency_command, env=trial.environment(), text=True))
    trial.common.write(ROOT / 'native_dependencies.json', dependencies)
    results = []
    for dataset, scene in [('rpng', 'table_06'), ('aria', 'aria1253'), ('utmm', 'square-1')]:
        trial.common.evaluation.panel.v2.gpu_idle()
        output = ROOT / dataset / scene; output.mkdir(parents=True)
        command = [str(trial.BASE.PYTHON_ENV / 'bin/python'), str(Path(__file__).resolve()),
                   '--worker', '--dataset', dataset, '--scene', scene]
        trial.common.write(output / 'command.json', command)
        print('START', dataset, scene, flush=True)
        with (output / 'run.log').open('x') as log:
            returncode = subprocess.run(command, env=trial.environment(), stdout=log, stderr=subprocess.STDOUT).returncode
        for name, digest in hashes.items():
            if hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest:
                raise RuntimeError('Source changed during diagnostic: ' + name)
        if json.loads(subprocess.check_output(dependency_command, env=trial.environment(), text=True)) != dependencies:
            raise RuntimeError('Native dependencies changed during diagnostic')
        row = {'dataset': dataset, 'scene': scene, 'returncode': returncode}
        if returncode == 0:
            report = trial.common.read(output / 'optimizer_probe.json')
            runtime = trial.common.read(output / 'mapping_replay_runtime.json')
            audit = trial.common.read(output / 'online_training.json')
            checks = {'ledger': report['ledger_matches'], 'heldout': not report['heldout_overlap'],
                'zero_tail': runtime['post_eos_optimizer_updates'] == 0,
                'budget': runtime['mapping_wall_seconds'] <= runtime['budget_seconds'],
                'deadline': audit['optimizer_completions_after_deadline'] == 0}
            row.update(checks=checks, valid=all(checks.values()), records=len(report['records']))
        results.append(row)
        trial.common.write(ROOT / 'progress.json', results)
        print(json.dumps(row), flush=True)
        if returncode:
            raise RuntimeError('Diagnostic failed; preserve log and use a new tag')


if __name__ == '__main__':
    main()
