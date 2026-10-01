#!/usr/bin/env python3
"""Current merged mapper: sampler/source controls with unchanged production code.

The existing fresh D3+ERVS+dense arm is the reference. Controls use the same
input prefix, training render budget, pose trace and fixed evaluation cohort.
Native is a separate geometry-recipe comparison, not an isolated D3 switch.
"""
import argparse
from collections import Counter
from pathlib import Path
import sys
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import run_cvpr_measurements as fixed
from collect_cvpr_assets import ROOT, MAIN, RESULTS, OUT, read, write, sha

CASES = {'rr_dense': ('d3', 'rr', 'dense_rgb'),
         'ervs_kf_rgb': ('d3', 'ervs', 'kf_rgb'),
         'rr_kf_rgb': ('d3', 'rr', 'kf_rgb'),
         'native_geometry': ('native', 'ervs', 'dense_rgb')}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--scenes', nargs='+')
    p.add_argument('--budgets', nargs='+', type=int, default=[15, 40])
    p.add_argument('--cases', nargs='+', choices=list(CASES), default=list(CASES))
    p.add_argument('--snapshots', action='store_true')
    a = p.parse_args()
    fixed.install_paths()
    sys.path.insert(0, str(MAIN / 'scripts/selected_mapping'))
    from selected_mapping_check import verify_files
    lock = read(MAIN / 'scripts/selected_mapping/source_lock.json')
    verify_files(lock['sources']); verify_files(lock['extension_files'])
    source = {str(p): sha(p) for p in [*MAIN.glob('vigs/**/*.py'), *fixed.GEOM.glob('*.py'),
                                     Path(__file__), Path(fixed.__file__)]}
    a.output.mkdir(parents=True, exist_ok=True)
    spath = a.output / 'source_lock.json'
    if spath.exists(): assert read(spath) == source
    write(spath, source)
    inventory = [r for r in read(OUT / 'scene_inventory.json') if not a.scenes or r['scene'] in a.scenes]
    write(a.output / 'protocol.json', {'cases': CASES, 'candidate_scenes': [r['scene'] for r in inventory],
        'budgets': a.budgets, 'seed': 0, 'kappa': 16, 'tau0': 4, 'birth_multiplier': .8,
        'pruning': 'opacity .1, every 300 renders, protect 10 births', 'quotas': [3, 3, 6],
        'optimizer_batch_size': 1, 'reference': 'fresh D3+ERVS+dense at same budget',
        'dense_vs_kf_claim': 'system-level source replacement; realized RGB/native counts and LR positions may differ',
        'geometry_claim': 'native RGBD/normal vs D3; not an isolated add/remove term', 'snapshots': a.snapshots})
    rows = read(a.output / 'summary.json') if (a.output / 'summary.json').exists() else []
    py = str(fixed.trial.BASE.PYTHON_ENV / 'bin/python')
    for r in inventory:
        d, s = r['dataset'], r['scene']
        panel = RESULTS / ('cvpr_assets/fixed_work_12f_v1' if s == 'aria301_12F' else 'cvpr_assets/fixed_work_v1')
        setup = panel / 'inputs' / d / s / 'setup'
        for budget in a.budgets:
            reference = panel / f'render{budget}' / d / s / 'd3'
            for case in a.cases:
                if case == 'native_geometry' and budget != 40: continue
                out = a.output / f'render{budget}' / d / s / case
                if any(row['output'] == str(out) for row in rows): continue
                arm, selector, auxiliary = CASES[case]
                row = {'dataset': d, 'scene': s, 'budget': budget, 'arm': case,
                       'output': str(out), 'reference': str(reference), 'status': 'failed'}
                print('ABLATION_START', d, s, budget, case, flush=True)
                try:
                    xref = read(reference / 'render_result.json')
                    assert xref['valid_execution'] and all(xref['checks'].values())
                    cmd = [py, str(Path(fixed.__file__)), '--stage', 'worker', '--dataset', d,
                           '--scene', s, '--budget', str(budget), '--arm', arm, '--selector', selector,
                           '--auxiliary-mode', auxiliary, '--setup', str(setup), '--output', str(out)]
                    if a.snapshots: cmd += ['--snapshots']
                    fixed.run(cmd, out.parent / f'{case}.log', arm)
                    x = read(out / 'render_result.json')
                    assert x['valid_execution'] and all(x['checks'].values())
                    prefix = lambda z: [(v['uid'], v['training_renders']) for v in z['render_prefixes']]
                    assert prefix(x) == prefix(xref)
                    for name in ['traj_full_beforeBA.txt', 'traj_kf_beforeBA.txt']:
                        assert sha(out / name) == sha(reference / name)
                    ev = fixed.trial.common.evaluation.panel.run_evaluation_twice(out, d, s, Path(r['fixed_manifest']))
                    assert ev['pass'], ev
                    metric = lambda p: [v['uid'] for v in read(p / 'psnr/strict_fixed_manifest/final_result.json')['per_view'] if v['predeclared_fixed_manifest_split']]
                    assert metric(out) == metric(reference)
                    assert all(sha(Path(p)) == h for p, h in source.items())
                    audit = {'same_prefix_renders_poses_cohort': True,
                             'training_renders': x['render_counts']['training'],
                             'optimizer_steps': x['main_optimizer_steps'],
                             'gaussians': x['gaussians'],
                             'loss_routes': dict(Counter(v['loss'] for v in x['training']['loss_routes'])),
                             'roles': dict(Counter(role for g in x['training']['generations'] for v in g['services'] for role in v['roles']))}
                    write(out / 'comparison_audit.json', audit)
                    row.update(status='passed', psnr=ev['fixed_psnr_first'], audit=audit,
                               mapping_seconds=x['mapping_seconds'], evaluation=ev)
                except Exception:
                    row['error'] = traceback.format_exc()
                rows.append(row); write(a.output / 'summary.json', rows); fixed.journal(row)
                print('ABLATION_DONE', d, s, budget, case, row['status'], row.get('psnr'), flush=True)


if __name__ == '__main__': main()
