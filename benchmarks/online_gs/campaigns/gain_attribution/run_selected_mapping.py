"""Run the user-adopted mapper replay recipe without changing legacy defaults."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def recipe_args(quotas=None):
    recipe = json.loads((HERE / 'selected_mapping_recipe.json').read_text())
    args = list(recipe['worker_args'])
    if quotas is not None:
        i = args.index('--batch-quotas') + 1
        args[i:i + 3] = [str(n) for n in quotas]
    return args


def main():
    p = argparse.ArgumentParser()
    inputs = p.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--dataset', choices=['aria', 'rpng', 'utmm'])
    inputs.add_argument('--setup', type=Path)
    p.add_argument('--extensions', type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--reference', type=Path)
    p.add_argument('--print-command', action='store_true')
    p.add_argument('--check-only', action='store_true', help='Verify pinned sources and replay inputs without using GPU')
    p.add_argument('--evaluate', action='store_true', help='Run the fixed held-out evaluator twice after mapping')
    args = p.parse_args()
    from selected_mapping_check import load_lock, preflight, gpu_idle
    lock = load_lock()
    if args.dataset:
        args.setup = Path(lock['datasets'][args.dataset]['setup'])
    args.extensions = args.extensions or Path(lock['extensions'])
    args.output = args.output.resolve()
    cmd = [sys.executable, str(HERE / 'run_kf15_render_worker.py'), *recipe_args()]
    for name in ('setup', 'extensions', 'output', 'reference'):
        value = getattr(args, name)
        if value is not None:
            cmd += ['--' + name, str(value)]
    if args.print_command:
        print(json.dumps(cmd))
    else:
        provenance = preflight(args.setup, args.extensions, args.output)
        if args.check_only:
            print('Preflight PASS: pinned recipe, source, setup, extensions and input manifests')
            print(json.dumps(cmd))
            return
        gpu_idle()
        import run_online_dense_training as trial
        backend = Path('/home/intern/VIGS-SLAM-online-worker-integration')
        env = trial.environment()
        env['EXP78B_CUSTOM_ROOT'] = str(backend)
        env['PYTHONPATH'] = str(backend / 'vigs') + ':' + str(backend) + ':' + env['PYTHONPATH']
        subprocess.run(cmd, env=env, check=True)
        (args.output / 'selected_recipe.json').write_text((HERE / 'selected_mapping_recipe.json').read_text())
        (args.output / 'selected_source_lock.json').write_text(json.dumps(lock, indent=2) + '\n')
        (args.output / 'selected_command.json').write_text(json.dumps(cmd, indent=2) + '\n')
        if args.evaluate:
            dataset, scene = provenance['dataset'], provenance['scene']
            result = trial.common.evaluation.panel.run_evaluation_twice(
                args.output, dataset, scene, trial.BASE.sequence_paths(dataset, scene)['fixed_manifest'])
            if not result['pass']:
                raise RuntimeError('Held-out evaluation consistency failed')
            print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
