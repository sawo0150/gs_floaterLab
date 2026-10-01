"""Fixed40 replay: no prune vs protected opacity thresholds .7 and .1."""
import argparse
import math
from pathlib import Path
import subprocess
import traceback
import run_init_density_panel as prior

c = prior.common
trial = prior.trial
ROOT, HERE = prior.ROOT, prior.HERE
CARD = 'campaigns/06_gain_attribution/protected_prune/README.md'


def final_map_count_audit(out, x):
    # IMU resets replace the entire GaussianModel, without prune_points.
    archive = trial.BASE.sequence_paths(x['dataset'], x['scene'])['archive']
    manifest = c.read(archive / 'archive_manifest.json')
    last_reset = max((e['emitted_at_frame_uid'] for e in manifest['events']
                      if e['kind'] == 'mapper_reset'), default=-1)
    births = [line.split(',') for line in (out / 'birth_sampling.csv').read_text().splitlines()]
    last_init = max(i for i, r in enumerate(births) if int(r[4]))
    final_births = sum(int(r[3]) for r in births[last_init:])
    final_removed = sum(e['removed'] for e in x['densify_prune_ablation']['events']
                        if e['arrival_uid'] >= last_reset)
    assert final_births - final_removed == x['gaussians']
    return {'last_reset_arrival': last_reset, 'final_map_births': final_births,
            'final_map_removed': final_removed, 'final_map_count_pass': True}


def journal(row):
    message = (f"**2026-09-28 protected prune {row['case']} / {row.get('dataset', 'rpng')}40 "
               f"period={row.get('prune_every_renders')} birth_denominator={row.get('birth_downsample_multiplier')}:** "
               f"PSNR={row.get('psnr')}, GS={row.get('gaussians')}, "
               f"audit={row.get('audit_pass')}, error={row.get('error')}; {row['output']}.")
    p = ROOT / 'context/experiments' / CARD
    with p.open('a') as f:
        f.write('\n' + message + '\n')
    for file, heading, link in [('context/STATUS.md', '## 최근 흐름 (최신순)\n', 'experiments/' + CARD),
                                ('context/experiments/INDEX.md', '# Experiment Index\n', CARD)]:
        p = ROOT / file
        s = p.read_text()
        assert heading in s
        p.write_text(s.replace(heading, heading + '\n- ' + message + ' → [카드](' + link + ')\n', 1))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--dataset', choices=['aria', 'rpng', 'utmm'], default='rpng')
    p.add_argument('--cases', nargs='+', choices=['off', 'opacity07', 'opacity01'], default=['off', 'opacity07', 'opacity01'])
    p.add_argument('--baseline-dir', type=Path)
    p.add_argument('--prune-every-renders', type=int, default=300)
    p.add_argument('--birth-downsample-multiplier', type=float, default=1.)
    args = p.parse_args()
    if args.prune_every_renders <= 0:
        p.error('prune-every-renders must be positive')
    if not math.isfinite(args.birth_downsample_multiplier) or args.birth_downsample_multiplier <= 0:
        p.error('birth-downsample-multiplier must be finite and positive')
    dataset = args.dataset
    scene = c.SCENES[dataset]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    backend = Path('/home/intern/VIGS-SLAM-online-worker-integration')
    protocol = {'scene': dataset + '/' + scene, 'renders_per_kf': 40, 'seed': 0,
                'thresholds': [{'off': None, 'opacity07': .7, 'opacity01': .1}[case] for case in args.cases], 'protect_recent_nonempty_KF_births': 10,
                'prune_every_renders': args.prune_every_renders,
                'cadence': f'every {args.prune_every_renders} completed renders, deferred to packet boundary; no tail pass',
                'birth_downsample_multiplier': args.birth_downsample_multiplier,
                'approximate_birth_count_multiplier': 1. / args.birth_downsample_multiplier,
                'kappa': 16, 'tau': 4., 'batch_quotas': [3, 3, 6],
                'optimizer_batch_size': 1, 'selector': 'ervs', 'dense_rgb': True,
                'densify': False, 'size_prune': False, 'cap_prune': False,
                'carve': False, 'blur': False, 'scale_projection': True,
                'actual_tracking': False, 'no_extra_tuning': True}
    c.write(output / 'protocol.json', protocol)
    source = output / 'source'
    source.mkdir()
    lock = {}
    for path in list((backend / 'vigs').rglob('*.py')) + list(HERE.glob('*.py')):
        digest = c.sha(path)
        dest = source / (digest[:12] + '_' + path.name)
        dest.write_bytes(path.read_bytes())
        lock[str(path)] = {'sha256': digest, 'copy': str(dest)}
    c.write(output / 'source_lock.json', lock)
    env = trial.environment()
    env['EXP78B_CUSTOM_ROOT'] = str(backend)
    env['PYTHONPATH'] = str(backend / 'vigs') + ':' + str(backend) + ':' + env['PYTHONPATH']
    tests = ['test_protected_opacity_prune', 'test_unified_rr', 'test_unified_growth',
             'test_unified_view_training', 'test_paired_cumulative_counts',
             'test_dense_blur_filter', 'test_kf_rgb_control']
    cp = subprocess.run([str(trial.BASE.PYTHON_ENV / 'bin/python'), '-m', 'unittest', *tests],
                        cwd=HERE, env=env, capture_output=True, text=True)
    c.write(output / 'cpu_tests.json', {'returncode': cp.returncode, 'stdout': cp.stdout, 'stderr': cp.stderr})
    assert cp.returncode == 0
    base = trial.ROOT / 'live_worker_integration_audit'
    reference = ROOT / 'results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d1' / dataset / 'render_result.json'
    setup = base / ('v5_packet_identity/aria_setup' if dataset == 'aria' else f'v9_productive_worker/three_scene/{dataset}_setup')
    rows = []
    baseline_dir = args.baseline_dir.resolve() if args.baseline_dir else output / 'off'
    c.write(output / 'execution_scope.json', {'cases': args.cases, 'baseline_dir': str(baseline_dir)})
    for case, threshold in [('off', None), ('opacity07', .7), ('opacity01', .1)]:
        if case not in args.cases:
            continue
        trial.common.evaluation.panel.v2.gpu_idle()
        out = output / case
        cmd = [str(trial.BASE.PYTHON_ENV / 'bin/python'), str(HERE / 'run_kf15_render_worker.py'),
               '--setup', str(setup),
               '--extensions', str(base / 'v6_current_stream_extensions'), '--output', str(out),
               '--renders-per-kf', '40', '--seed', '0', '--membership', 'growth', '--kappa', '16',
               '--tau', '4', '--growth-budget-scope', 'dense_only', '--selector', 'ervs',
               '--schedule', 'unified', '--selection-count-scope', 'all_rgb',
               '--batch-quotas', '3', '3', '6', '--disable-densify-prune',
               '--optimizer-batch-size', '1', '--unified-scale-projection', '--reference', str(reference),
               '--birth-downsample-multiplier', str(args.birth_downsample_multiplier)]
        if threshold is not None:
            cmd += ['--protected-opacity-prune', '--prune-opacity-threshold', str(threshold),
                    '--prune-every-renders', str(args.prune_every_renders)]
        c.write(output / (case + '_command.json'), cmd)
        print('START', dataset, case, flush=True)
        with (output / (case + '_launcher.log')).open('x') as f:
            code = subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.STDOUT).returncode
        row = {'case': case, 'dataset': dataset, 'scene': scene, 'threshold': threshold, 'output': str(out), 'returncode': code,
               'prune_every_renders': args.prune_every_renders,
               'birth_downsample_multiplier': args.birth_downsample_multiplier,
               'audit_pass': False, 'error': None}
        try:
            x = c.read(out / 'render_result.json')
            assert code == 0 and x['valid_execution']
            evaluation = trial.common.evaluation.panel.run_evaluation_twice(
                out, dataset, scene, trial.BASE.sequence_paths(dataset, scene)['fixed_manifest'])
            assert evaluation['pass']
            audit = prior.audit_run(out, dataset, {'kappa': 16, 'tau': 4., 'blur': False,
                                                 'selector': 'ervs', 'renders_per_kf': 40})
            audit.pop('densify_prune_off', None)
            y = c.read(reference if threshold is None else baseline_dir / 'render_result.json')
            assert x['render_counts'] == y['render_counts']
            assert x['main_optimizer_steps'] == y['main_optimizer_steps']
            assert [g['services'] for g in x['training']['generations']] == [g['services'] for g in y['training']['generations']]
            assert [g['admissions'] for g in x['training']['generations']] == [g['admissions'] for g in y['training']['generations']]
            refdir = reference.parent if threshold is None else baseline_dir
            births = [line.split(',') for line in (out / 'birth_sampling.csv').read_text().splitlines()]
            refbirths = [line.split(',') for line in (refdir / 'birth_sampling.csv').read_text().splitlines()]
            assert [r[:3] + r[4:] for r in births] == [r[:3] + r[4:] for r in refbirths]
            factor = args.birth_downsample_multiplier
            reference_factor = y['birth_density']['downsample_multiplier']
            assert x['birth_density']['pcd_downsample_init'] == 64 * factor
            assert x['birth_density']['pcd_downsample'] == 256 * factor
            if factor == reference_factor:
                assert c.sha(out / 'birth_sampling.csv') == c.sha(refdir / 'birth_sampling.csv')
            else:
                assert all(abs(int(r[3]) * factor - int(b[3]) * reference_factor) <= 5 * max(factor, reference_factor)
                           for r, b in zip(births, refbirths)), 'Birth counts do not follow the requested common multiplier'
            topology = x['densify_prune_ablation']
            events = topology.get('events', [])
            if threshold is not None:
                assert topology['mode'] == 'protected_opacity_only'
                assert topology['threshold'] == threshold
                assert topology['period_completed_renders'] == args.prune_every_renders
                assert events and all(e['protected_removed'] == 0 and e['alignment_pass'] for e in events)
                assert all(e['completed_at'] <= x['last_input_at'] for e in events)
                removed = sum(e['removed'] for e in events)
                audit.update(final_map_count_audit(out, x))
            else:
                removed = 0
            changed = [k for k, v in lock.items() if c.sha(Path(k)) != v['sha256']]
            assert not changed
            audit.update(densify_off=True, prune_only=threshold is not None,
                         identical_selection_admission_work=True,
                         identical_birth_inputs=True, identical_birth_counts=factor == reference_factor,
                         requested_birth_multiplier_verified=True, protected_removed=0,
                         all_pruning_before_last_input=True, source_unchanged=True)
            c.write(out / 'independent_audit.json', audit)
            row.update(audit_pass=True, psnr=evaluation['fixed_psnr_first'], gaussians=x['gaussians'],
                       mapping_seconds=x['mapping_seconds'], removed=removed, pruning_passes=len(events),
                       peak_allocated_mib=x['peak_cuda_allocated_bytes'] / 2**20,
                       renders=x['render_counts']['training'], adam=x['main_optimizer_steps'])
            if threshold is not None:
                row.update(final_map_births=audit['final_map_births'],
                           final_map_removed=audit['final_map_removed'])
        except Exception:
            row['error'] = traceback.format_exc()
        rows.append(row)
        c.write(output / 'progress.json', rows)
        journal(row)
        print('DONE', row, flush=True)
        if not row['audit_pass']:
            raise RuntimeError(row['error'])
    c.write(output / 'summary.json', rows)
    print('PROTECTED_PRUNE_COMPARISON_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
