"""Two window-quota alternatives on the adopted fixed40 mapper recipe."""
import argparse
from collections import Counter
from pathlib import Path
import subprocess
import traceback
import run_protected_prune_comparison as prune
from run_selected_mapping import recipe_args

c, trial, prior = prune.c, prune.trial, prune.prior
ROOT, HERE = prune.ROOT, prune.HERE
CARD = 'campaigns/06_gain_attribution/window_quota/README.md'


def service_summary(x):
    roles = Counter()
    recent = 0
    native = 0
    for g in x['training']['generations']:
        for s in g['services']:
            roles.update(s['roles'])
            for uid, role in zip(s['uids'], s['roles']):
                if role in ('window', 'keyframe'):
                    native += 1
                    recent += uid in s['window_uids']
    return {'roles': dict(roles), 'kf_renders': native, 'recent_kf_renders': recent,
            'recent_fraction_of_kf': recent / max(native, 1),
            'dense_renders': roles['dense'],
            'loss_renders': dict(Counter(r['loss'] for r in x['training']['loss_routes']))}


def journal(row):
    message = (f"**2026-09-28 window quota {row['case']} / {row['dataset']}40:** "
               f"PSNR={row.get('psnr')}, GS={row.get('gaussians')}, "
               f"audit={row.get('audit_pass')}, error={row.get('error')}; {row['output']}.")
    with (ROOT / 'context/experiments' / CARD).open('a') as f:
        f.write('\n' + message + '\n')
    for file, heading, link in [('context/STATUS.md', '## 최근 흐름 (최신순)\n', 'experiments/' + CARD),
                                ('context/experiments/INDEX.md', '# Experiment Index\n', CARD)]:
        path = ROOT / file
        s = path.read_text()
        assert heading in s
        path.write_text(s.replace(heading, heading + '\n- ' + message + ' → [카드](' + link + ')\n', 1))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    backend = Path('/home/intern/VIGS-SLAM-online-worker-integration')
    cases = {'156': (1, 5, 6), '066': (0, 6, 6)}
    c.write(output / 'protocol.json', {
        'cases': cases, 'control_quotas': [3, 3, 6], 'scenes': c.SCENES,
        'adopted_recipe': c.read(HERE / 'selected_mapping_recipe.json'),
        'baseline': 'protected_prune/init_increase300_v1/{dataset}/increase/opacity01',
        'new_runs': 6, 'pool_retention': 'unchanged; no window quota does not remove recent KFs from full pool',
        'interpretation': 'Sampling-mixture ablation with fixed nominal KF/dense ratio; report actual loss counts and batch/LR schedules',
        'actual_tracking': False})
    source = output / 'source'
    source.mkdir()
    lock = {}
    for path in list((backend / 'vigs').rglob('*.py')) + list(HERE.glob('*.py')) + [HERE / 'selected_mapping_recipe.json']:
        digest = c.sha(path)
        dest = source / (digest[:12] + '_' + path.name)
        dest.write_bytes(path.read_bytes())
        lock[str(path)] = {'sha256': digest, 'copy': str(dest)}
    c.write(output / 'source_lock.json', lock)
    env = trial.environment()
    env['EXP78B_CUSTOM_ROOT'] = str(backend)
    env['PYTHONPATH'] = str(backend / 'vigs') + ':' + str(backend) + ':' + env['PYTHONPATH']
    tests = ['test_window_quota', 'test_protected_opacity_prune', 'test_unified_rr',
             'test_unified_growth', 'test_unified_view_training', 'test_paired_cumulative_counts',
             'test_dense_blur_filter', 'test_kf_rgb_control']
    cp = subprocess.run([str(trial.BASE.PYTHON_ENV / 'bin/python'), '-m', 'unittest', *tests],
                        cwd=HERE, env=env, capture_output=True, text=True)
    c.write(output / 'cpu_tests.json', {'returncode': cp.returncode, 'stdout': cp.stdout, 'stderr': cp.stderr})
    assert cp.returncode == 0
    base = trial.ROOT / 'live_worker_integration_audit'
    rows = []
    for dataset, scene in c.SCENES.items():
        reference = ROOT / 'results/campaigns/gain_attribution/protected_prune/init_increase300_v1' / dataset / 'increase/opacity01'
        old = c.read(reference / 'render_result.json')
        assert old['valid_execution'] and old['birth_density']['downsample_multiplier'] == .8
        assert old['densify_prune_ablation']['threshold'] == .1
        assert old['densify_prune_ablation']['period_completed_renders'] == 300
        setup = base / ('v5_packet_identity/aria_setup' if dataset == 'aria' else f'v9_productive_worker/three_scene/{dataset}_setup')
        for case, quotas in cases.items():
            trial.common.evaluation.panel.v2.gpu_idle()
            out = output / dataset / case
            out.parent.mkdir(parents=True, exist_ok=True)
            cmd = [str(trial.BASE.PYTHON_ENV / 'bin/python'), str(HERE / 'run_kf15_render_worker.py'),
                   *recipe_args(quotas), '--setup', str(setup),
                   '--extensions', str(base / 'v6_current_stream_extensions'), '--output', str(out),
                   '--reference', str(reference / 'render_result.json')]
            c.write(out.parent / (case + '_command.json'), cmd)
            print('START', dataset, case, flush=True)
            with (out.parent / (case + '_launcher.log')).open('x') as f:
                code = subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.STDOUT).returncode
            row = {'case': case, 'dataset': dataset, 'scene': scene, 'output': str(out),
                   'returncode': code, 'audit_pass': False, 'error': None}
            try:
                x = c.read(out / 'render_result.json')
                assert code == 0 and x['valid_execution']
                evaluation = trial.common.evaluation.panel.run_evaluation_twice(
                    out, dataset, scene, trial.BASE.sequence_paths(dataset, scene)['fixed_manifest'])
                assert evaluation['pass']
                audit = prior.audit_run(out, dataset, {'kappa': 16, 'tau': 4., 'blur': False,
                    'selector': 'ervs', 'renders_per_kf': 40, 'batch_quotas': quotas})
                audit.pop('densify_prune_off', None)
                assert x['render_counts'] == old['render_counts']
                assert x['main_optimizer_steps'] == old['main_optimizer_steps']
                assert [g['admissions'] for g in x['training']['generations']] == [g['admissions'] for g in old['training']['generations']]
                assert c.sha(out / 'birth_sampling.csv') == c.sha(reference / 'birth_sampling.csv')
                topology = x['densify_prune_ablation']
                assert topology['threshold'] == .1 and topology['period_completed_renders'] == 300
                assert topology['protect_recent_birth_batches'] == 10
                assert all(e['protected_removed'] == 0 and e['alignment_pass'] and e['completed_at'] <= x['last_input_at'] for e in topology['events'])
                assert [(e['arrival_uid'], e['renders']) for e in topology['events']] == [(e['arrival_uid'], e['renders']) for e in old['densify_prune_ablation']['events']]
                audit.update(prune.final_map_count_audit(out, x))
                inventory = lambda g: (g['policy']['keyframes'], g['policy']['offered_dense'], g['policy']['admitted_dense'])
                assert [inventory(g) for g in x['training']['generations']] == [inventory(g) for g in old['training']['generations']]
                services = service_summary(x)
                if quotas[0] == 0:
                    assert services['roles'].get('window', 0) == 0
                old_services = service_summary(old)
                def lr_positions(result):
                    return [s['lr_render_position'] for g in result['training']['generations'] for s in g['services'] for _ in s['uids']]
                actual_loss_changes = sum(a['loss'] != b['loss'] for a,b in zip(x['training']['loss_routes'], old['training']['loss_routes']))
                assert not [k for k,v in lock.items() if c.sha(Path(k)) != v['sha256']]
                audit.update(densify_off=True, protected_removed=0, same_birth_inputs_counts=True,
                    same_admissions_pool_membership=True, same_pruning_schedule=True,
                    lr_positions_equal=lr_positions(x) == lr_positions(old),
                    loss_type_position_changes=actual_loss_changes, service_summary=services,
                    control_service_summary=old_services, source_unchanged=True)
                c.write(out / 'independent_audit.json', audit)
                row.update(audit_pass=True, psnr=evaluation['fixed_psnr_first'], gaussians=x['gaussians'],
                    mapping_seconds=x['mapping_seconds'], peak_allocated_mib=x['peak_cuda_allocated_bytes']/2**20,
                    services=services, control_services=old_services, loss_type_position_changes=actual_loss_changes,
                    lr_positions_equal=audit['lr_positions_equal'])
            except Exception:
                row['error'] = traceback.format_exc()
            rows.append(row)
            c.write(output / 'progress.json', rows)
            journal(row)
            print('DONE', row, flush=True)
            if not row['audit_pass']:
                raise RuntimeError(row['error'])
    c.write(output / 'summary.json', rows)
    print('WINDOW_QUOTA_COMPARISON_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
