#!/usr/bin/env python3
"""ERVS K16 / uniform with replacement / uniform K16 on extra scenes, run on colin's RTX 5090
(PREREG: context/experiments/campaigns/06_gain_attribution/ervs_vs_iid_colin5090/PREREG.md).

Runs from a clean worktree pair (VIGS-SLAM-custom 6d200f0f, gs_floaterLab) with a machine profile that relocates
only those two code roots; data and frozen tracker archives stay at their colin paths. Scenes are added to SCENES with
their archive, held-out manifest and setup; sequence_paths is extended for them only.

  python run_ervs_colin5090.py --scenes aria301_12F --seeds 0 1 2
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
from run_ervs_vs_iid_scenes import ARMS  # noqa: E402
import oxford_paths  # noqa: E402

base.OUT = base.ROOT / 'results/campaigns/gain_attribution/ervs_vs_iid_colin5090/v1'
PREREG = base.ROOT / 'context/experiments/campaigns/06_gain_attribution/ervs_vs_iid_colin5090/PREREG.md'
CVPR = Path('/home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets')
SCENES = {
    'aria301_12F': dict(dataset='aria', archive=CVPR / 'inputs/aria301_12F/archive',
                        manifest=CVPR / 'inputs/aria301_12F/heldout.json',
                        setup=CVPR / 'fixed_work_12f_v1/inputs/aria/aria301_12F/setup'),
}
for _seq in oxford_paths.SEQUENCES:   # Amendment 1: Oxford Spires (prepare_oxford_vigs.py + prepare_oxford_capture.py)
    _x = oxford_paths.paths(_seq)
    SCENES[_seq] = dict(dataset='oxford', archive=_x['archive'], manifest=_x['fixed_manifest'],
                        setup=oxford_paths.PREP / _seq / 'setup')
BUDGET = 25


def install_paths(trial):
    old = trial.BASE.sequence_paths

    def paths(dataset, scene):
        if scene not in SCENES:
            return old(dataset, scene)
        if dataset == 'oxford':
            return oxford_paths.paths(scene)
        s = SCENES[scene]
        m = json.loads((s['archive'] / 'archive_manifest.json').read_text())
        return {'archive': s['archive'], 'fixed_manifest': s['manifest'],
                'custom_config': base.ROOT / f'benchmarks/online_gs/config/vigs_final_v7_{dataset}.yaml',
                'vanilla_config': Path(m['input_config']), 'image_dir': Path(m['input_image_directory']),
                'calibration': Path(m['input_calibration'])}
    trial.BASE.sequence_paths = paths


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
        s = SCENES.get(prov['scene'])
        if s is None or s['dataset'] != prov['dataset'] or setup != s['setup']:
            raise RuntimeError(f'unexpected setup {setup}')
        archive = prov['command'][prov['command'].index('--archive') + 1]
        if Path(archive) != s['archive']:
            raise RuntimeError(f'setup archive {archive} != {s["archive"]}')
        sp = trial.BASE.sequence_paths(prov['dataset'], prov['scene'])
        for p in (s['archive'] / 'archive_manifest.json', s['manifest'], sp['image_dir'], sp['calibration'],
                  setup / 'native_setup.pt'):
            if not Path(p).exists():
                raise RuntimeError('Missing input: ' + str(p))
        return prov
    return preflight


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--scenes', nargs='+', default=list(SCENES))
    p.add_argument('--seeds', nargs='+', type=int, default=[0, 1, 2])
    p.add_argument('--arms', nargs='+', default=['ervs_k16', 'uniform_iid', 'uniform_k16'], choices=list(ARMS))
    p.add_argument('--pool-cap', type=int, default=0, help='FIFO cap on KF and dense pools (0 = off)')
    a = p.parse_args()
    assert os.environ.get('ROGO_MACHINE_PROFILE'), 'machine profile required'
    sys.path.insert(0, str(base.SEL))
    from selected_mapping_check import load_lock, gpu_idle, verify_files
    lock = load_lock()
    sys.path.insert(0, lock['benchmark_helpers'])
    import run_online_dense_training as trial
    from selected_recipe import recipe_environment, install_scene_adapter
    install_scene_adapter()
    install_paths(trial)
    for scene, s in SCENES.items():
        lock['datasets'][scene] = dict(dataset=s['dataset'], scene=scene, setup=str(s['setup']))
    base.OUT.mkdir(parents=True, exist_ok=True)
    if not (base.OUT / 'protocol.json').exists():
        base.write(base.OUT / 'protocol.json', dict(
            prereg=str(PREREG), prereg_sha256=base.sha(PREREG), main_head=base.head(base.MAIN),
            lab_head=base.head(base.ROOT), recipe=base.read(base.RECIPE), scenes={k: {x: str(y) for x, y in v.items()}
                                                                                  for k, v in SCENES.items()},
            runner_sha256=base.sha(Path(__file__)), machine_profile=os.environ['ROGO_MACHINE_PROFILE'],
            gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version',
                                         '--format=csv,noheader'], text=True).strip()))
    base.write(base.OUT / f'invocation_{int(time.time())}.json', vars(a))
    ctx = (lock, trial, make_preflight(trial, verify_files, load_lock), gpu_idle, recipe_environment)
    rows = []
    for seed in a.seeds:
        for scene in a.scenes:
            for arm in a.arms:
                extra, patch, env = ARMS[arm]
                name = f'{arm}_s{seed}'
                print('START', scene, BUDGET, name, flush=True)
                try:
                    sp = trial.BASE.sequence_paths(SCENES[scene]['dataset'], scene)
                    extra_scenes = {scene: dict(dataset=SCENES[scene]['dataset'], **{k: str(v) for k, v in sp.items()})}
                    env_extra = dict(env, B_SELECTED_WORKER=str(base.SEL / 'run_selected_worker.py'),
                                     B_PATCH_WORKER=str(HERE / patch), B_EXTRA_SCENES=json.dumps(extra_scenes))
                    if a.pool_cap:
                        env_extra['B_POOL_CAP'] = str(a.pool_cap)
                    phase = f'scenes_cap{a.pool_cap}' if a.pool_cap else 'scenes'
                    row = base.run_one(phase, scene, BUDGET, name, [*extra, '--seed', str(seed)], ctx,
                                       worker=HERE / 'extra_scene_launcher.py', env_extra=env_extra)
                    out = Path(row['output'])
                    argv = base.read(out.parent / f'{name}.command.json')['cmd']
                    assert argv[len(argv) - argv[::-1].index('--seed')] == str(seed), 'seed not applied'
                    pol_tau = float(base.read(out / 'render_result.json')['training']['generations'][-1]['policy']['tau'])
                    if arm in ('ervs_k16', 'uniform_k16'):
                        g = base.read(out / 'group_k.json')
                        assert g['stats'].get('groups/keyframe') and g['stats'].get('groups/dense'), g
                        row['group_k'] = g
                    if arm.startswith('uniform'):
                        assert pol_tau >= 1e11, pol_tau
                    if arm == 'uniform_iid':
                        st = base.read(out / 'sampling_mode.json')['stats']
                        assert st.get('repeat_in_batch/keyframe', 0) + st.get('repeat_in_batch/dense', 0), st
                        row['sampling_mode'] = st
                    if a.pool_cap:
                        pc = base.read(out / 'pool_cap.json')
                        assert pc['cap'] == a.pool_cap and pc['reserve_calls'] > 0, pc
                        row['pool_cap'] = pc
                    row['seed'] = seed; row['base_arm'] = arm
                    base.write(out.parent / f'{name}.row.json', row)
                except Exception:
                    base.write(base.OUT / 'failure.json', dict(scene=scene, arm=name, traceback=traceback.format_exc(),
                                                               time=time.time()))
                    raise
                rows.append(row)
                base.summarize(rows)
                print('DONE', scene, BUDGET, name, f"psnr={row['psnr']:.4f}", flush=True)
    print('ABLATION_PASS_COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
