#!/usr/bin/env python3
"""ERVS K16 vs uniform with replacement on the 15 extra scenes (cvpr_assets fixed_work_v1 setups), B recipe
(PREREG: context/experiments/campaigns/06_gain_attribution/ervs_vs_iid_scenes/PREREG.md).

The official preflight accepts only the four pinned scenes. This runner keeps every source/extension/rasterizer hash
check and replaces only the scene lookup: setups are the cvpr fixed_work_v1 captures (same exp78b command flags and
frozen tracker archive as the pinned setups; native_setup differs only in recorded output/weights paths).

  python run_ervs_vs_iid_scenes.py --budgets 25 --seeds 0 1 2 [--scenes table_01 ...]
"""
import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_b_ablation_chain as base  # noqa: E402

base.OUT = base.ROOT / 'results/campaigns/gain_attribution/ervs_vs_iid_scenes/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/ervs_vs_iid_scenes/PREREG.md'
SETUPS = Path('/home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/inputs')
SCENES = {'aria301_305': 'aria', **{f'table_0{i}': 'rpng' for i in (1, 2, 3, 4, 5, 7, 8)},
          **{s: 'utmm' for s in ('ego-centric-1', 'ego-centric-2', 'ego-drive', 'fast-straight', 'slow-straight-1',
                                 'slow-straight-2', 'square-2')}}
ARMS = {'ervs_k16': ([], 'group_k_patch.py', dict(B_GROUP_K='16')),
        'uniform_iid': (['--tau', '1e12'], 'sampling_mode_patch.py', dict(B_WITH_REPLACEMENT='1'))}


def make_preflight(trial, verify_files, load_lock):
    def preflight(setup, extensions, output):
        lock = load_lock()
        if Path(sys.prefix).resolve() != Path(lock['python_prefix']).resolve():
            raise RuntimeError('Use ' + lock['python_prefix'] + '/bin/python')
        if output.exists():
            raise RuntimeError('Output must be a new directory: ' + str(output))
        verify_files(lock['sources'])
        if extensions.resolve() != Path(lock['extensions']).resolve():
            raise RuntimeError('Use the pinned CUDA extensions')
        verify_files(lock['extension_files'])
        verify_files(lock['rasterizer']['files'])
        prov = json.loads((setup / 'provenance.json').read_text())
        dataset, scene = prov['dataset'], prov['scene']
        if SCENES.get(scene) != dataset or setup != SETUPS / dataset / scene / 'setup':
            raise RuntimeError(f'unexpected setup {setup}: {dataset}/{scene}')
        sp = trial.BASE.sequence_paths(dataset, scene)
        archive = prov['command'][prov['command'].index('--archive') + 1]
        if Path(archive).parts[-4:] != Path(sp['archive']).parts[-4:]:
            raise RuntimeError(f'setup archive {archive} != {sp["archive"]}')
        for p in (Path(sp['archive']) / 'archive_manifest.json', Path(sp['fixed_manifest']), Path(sp['image_dir']),
                  setup / 'native_setup.pt', setup / 'native_setup.json'):
            if not p.exists():
                raise RuntimeError('Missing input: ' + str(p))
        return prov
    return preflight


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--budgets', nargs='+', type=int, required=True)
    p.add_argument('--seeds', nargs='+', type=int, required=True)
    p.add_argument('--scenes', nargs='+', default=list(SCENES))
    a = p.parse_args()
    assert os.environ.get('ROGO_MACHINE_PROFILE'), 'machine profile required'
    sys.path.insert(0, str(base.SEL))
    from selected_mapping_check import load_lock, gpu_idle, verify_files
    lock = load_lock()
    sys.path.insert(0, lock['benchmark_helpers'])
    import run_online_dense_training as trial
    from selected_recipe import recipe_environment, install_scene_adapter
    install_scene_adapter()
    for scene, dataset in SCENES.items():
        lock['datasets'][scene] = dict(dataset=dataset, scene=scene, setup=str(SETUPS / dataset / scene / 'setup'))
    base.OUT.mkdir(parents=True, exist_ok=True)
    if not (base.OUT / 'protocol.json').exists():
        base.write(base.OUT / 'protocol.json', dict(
            prereg=str(PREREG), prereg_sha256=base.sha(PREREG), main_head=base.head(base.MAIN),
            lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE), scenes=SCENES, setups=str(SETUPS),
            patch_sha256={x: base.sha(HERE / x) for x in ('group_k_patch.py', 'sampling_mode_patch.py')},
            runner_sha256=base.sha(Path(__file__)), machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                         '--format=csv,noheader'], text=True).strip()))
    base.write(base.OUT / f'invocation_{int(time.time())}.json', vars(a))
    ctx = (lock, trial, make_preflight(trial, verify_files, load_lock), gpu_idle, recipe_environment)
    rows = []
    for seed in a.seeds:
        for budget in a.budgets:
            for scene in a.scenes:
                for arm, (extra, patch, env) in ARMS.items():
                    name = f'{arm}_s{seed}'
                    print('START', scene, budget, name, flush=True)
                    try:
                        env_extra = dict(env, B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'),
                                         B_PATCH_WORKER=str(HERE / patch))
                        # Legacy-IMU launcher only fills a missing manifest key (fast-straight); see its docstring.
                        row = base.run_one('scenes', scene, budget, name, [*extra, '--seed', str(seed)], ctx,
                                           worker=HERE / 'legacy_imu_launcher.py', env_extra=env_extra)
                        out = Path(row['output'])
                        argv = base.read(out.parent / f'{name}.command.json')['cmd']
                        assert argv[len(argv) - argv[::-1].index('--seed')] == str(seed), 'seed not applied'
                        if arm == 'ervs_k16':
                            g = base.read(out / 'group_k.json')
                            assert g['stats'].get('groups/keyframe') and g['stats'].get('groups/dense'), g
                            row['group_k'] = g
                        else:
                            tau = base.read(out / 'render_result.json')['training']['generations'][-1]['policy']['tau']
                            assert float(tau) >= 1e11, tau
                            st = base.read(out / 'sampling_mode.json')['stats']
                            assert st.get('repeat_in_batch/keyframe', 0) + st.get('repeat_in_batch/dense', 0), st
                            row['sampling_mode'] = st
                        row['seed'] = seed; row['base_arm'] = arm
                        base.write(out.parent / f'{name}.row.json', row)
                    except Exception:
                        base.write(base.OUT / 'failure.json', dict(scene=scene, budget=budget, arm=name,
                                                                   traceback=traceback.format_exc(), time=time.time()))
                        raise
                    rows.append(row)
                    base.summarize(rows)
                    print('DONE', scene, budget, name, f"psnr={row['psnr']:.4f}", flush=True)
    print('ABLATION_PASS_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
