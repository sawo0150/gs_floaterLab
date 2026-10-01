#!/usr/bin/env python3
"""Serialize loss-off controls and checkpoint evaluations after the live panel.

Existing source, renderer, input trace and sampler remain unchanged. The clean
geometry control uses the existing D3 weights set to zero, retaining its proxy
forward/backward work. This is distinct from switching to native RGBD losses.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import run_cvpr_measurements as fixed
from collect_cvpr_assets import ROOT, RESULTS, OUT, MAIN, read, write, sha
from run_cvpr_asset_pipeline import process_identity
from run_cvpr_full_asset_panel import curves_ok


def wait_gpu():
    from selected_mapping_check import gpu_idle
    while True:
        try:
            gpu_idle(); return
        except RuntimeError:
            time.sleep(30)


def command_run(command, log, env):
    wait_gpu()
    write(log.with_suffix('.command.json'), command)
    with log.open('x') as f:
        subprocess.run(command, cwd=ROOT, env=env, stdout=f,
                       stderr=subprocess.STDOUT, check=True)


def geometry_control(item, output, py, source):
    dataset, scene = item['dataset'], item['scene']
    panel = RESULTS / ('cvpr_assets/fixed_work_12f_v1' if scene == 'aria301_12F' else 'cvpr_assets/fixed_work_v1')
    reference = panel / 'render40' / dataset / scene / 'd3'
    setup = panel / 'inputs' / dataset / scene / 'setup'
    out = output / 'render40' / dataset / scene / 'geometry_zero_weights'
    row = dict(dataset=dataset, scene=scene, budget=40, arm='geometry_zero_weights',
               output=str(out), reference=str(reference), status='failed')
    if out.exists(): raise RuntimeError(f'Unexpected existing output: {out}')
    command = [py, str(Path(fixed.__file__)), '--stage', 'worker', '--dataset', dataset,
        '--scene', scene, '--budget', '40', '--arm', 'd3', '--selector', 'ervs',
        '--auxiliary-mode', 'dense_rgb', '--setup', str(setup), '--output', str(out), '--snapshots']
    env = fixed.environment('d3')
    env.update(FIXED40_D3_HARD='0', FIXED40_D3_MAIN='0')
    command_run(command, out.parent / 'geometry_zero_weights.log', env)
    actual, target = read(out / 'render_result.json'), read(reference / 'render_result.json')
    assert actual['valid_execution'] and all(actual['checks'].values())
    prefix = lambda x: [(r['uid'], r['training_renders']) for r in x['render_prefixes']]
    assert prefix(actual) == prefix(target)
    assert actual['main_optimizer_steps'] == target['main_optimizer_steps']
    for name in ['traj_full_beforeBA.txt', 'traj_kf_beforeBA.txt']:
        assert sha(out / name) == sha(reference / name)
    geometry = read(out / 'geometry_runtime.json')
    assert geometry['config']['mode'] == 'd3'
    assert geometry['config']['w_hard'] == geometry['config']['w_main'] == 0
    reference_geometry = read(reference / 'geometry_runtime.json')
    assert geometry['stats']['aux_renders'] == reference_geometry['stats']['aux_renders']
    evaluation = fixed.trial.common.evaluation.panel.run_evaluation_twice(
        out, dataset, scene, Path(item['fixed_manifest']))
    assert evaluation['pass'], evaluation
    cohort = lambda path: [r['uid'] for r in read(path / 'psnr/strict_fixed_manifest/final_result.json')['per_view']
                           if r['predeclared_fixed_manifest_split']]
    assert cohort(out) == cohort(reference)
    assert all(sha(Path(path)) == digest for path, digest in source.items())
    audit = dict(geometry_switch='D3 hard/main weights .0315/.25 -> 0/0',
        same_prefix_renders_poses_cohort=True, proxy_render_work_preserved=True,
        training_renders=actual['render_counts']['training'], auxiliary_renders=geometry['stats']['aux_renders'],
        optimizer_steps=actual['main_optimizer_steps'], geometry=geometry,
        expected_geometry_pruning_feedback='Map/opacity differences can change the same protected-pruning decisions')
    write(out / 'comparison_audit.json', audit)
    row.update(status='passed', psnr=evaluation['fixed_psnr_first'], audit=audit,
               mapping_seconds=actual['mapping_seconds'], evaluation=evaluation)
    return row


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--wait-pid', type=int, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    identity = process_identity(a.wait_pid)
    assert identity is not None and any(name in identity['cmd'] for name in
        ['run_cvpr_full_asset_panel.py', 'run_cvpr_ablations.py']), identity
    a.output.mkdir(parents=True, exist_ok=False)
    write(a.output / 'protocol.json', dict(wait_for_verified_process=identity,
        script_sha256=sha(Path(__file__)), candidate_selection='all declared scenes, no metric-based filtering',
        production_source_changes=False, geometry_control='existing D3 weights zero, proxy work retained',
        checkpoint_scopes=['RR/source controls', 'D3 zero-weight geometry', 'shared-tracking elapsed-time runs']))
    print('FOLLOWUP_WAIT', a.wait_pid, flush=True)
    while True:
        now = process_identity(a.wait_pid)
        if now is None or now['state'] == 'Z' or now['start'] != identity['start']: break
        write(a.output / 'waiting.json', dict(pid=a.wait_pid, verified_live=True, checked_at=time.time()))
        time.sleep(30)
    fixed.install_paths()
    sys.path.insert(0, str(MAIN / 'scripts/selected_mapping'))
    source = {str(path): sha(path) for path in [*MAIN.glob('vigs/**/*.py'), *fixed.GEOM.glob('*.py'),
                                              Path(fixed.__file__), Path(__file__)]}
    write(a.output / 'source_lock.json', source)
    inventory = read(OUT / 'scene_inventory.json')
    assert len(inventory) == 20 and all(r['ready'] for r in inventory)
    py = str(fixed.trial.BASE.PYTHON_ENV / 'bin/python')
    teaser = RESULTS / 'cvpr_assets/current_teaser_capture_v1'
    teaser_stage = dict(stage='current_teaser_capture', output=str(teaser), status='failed')
    try:
        command_run([py, str(HERE / 'capture_cvpr_teaser.py'), '--output', str(teaser)],
                    a.output / 'current_teaser_capture.log', fixed.environment('vanilla'))
        capture = read(teaser / 'provenance.json')
        assert capture['source_maps_unchanged'] and capture['optimizer_updates'] == 0
        teaser_stage['status'] = 'passed'
    except Exception:
        teaser_stage['error'] = traceback.format_exc()
    write(a.output / 'teaser_capture_stage.json', teaser_stage)
    fixed.journal(dict(dataset='rpng', scene='table_06_teaser_capture', budget=40,
                       arm='saved_map_no_training', status=teaser_stage['status'], output=str(teaser)))
    # The former parent coordinator can disappear while its control child keeps
    # running. Reconnect to that verified child, then resume the same live panel;
    # completed pilot runs are skipped by its existing source-locked runner.
    live = RESULTS / 'cvpr_assets/live_shared_tracking_v1'
    live_stage = dict(stage='shared_tracker_full_cohort', output=str(live), status='failed')
    try:
        existing = read(live / 'summary.json') if (live / 'summary.json').exists() else []
        if len(existing) != len(inventory) * 4:
            command_run([py, str(HERE / 'run_cvpr_live_measurements.py'), '--output', str(live), '--snapshots'],
                        a.output / 'shared_tracker_full_cohort.log', fixed.environment('vanilla'))
        states = read(live / 'summary.json')
        assert len(states) == len(inventory) * 4 and all(r['status'] == 'passed' for r in states)
        live_stage['status'] = 'passed'
    except Exception:
        live_stage['error'] = traceback.format_exc()
    write(a.output / 'live_stage.json', live_stage)
    fixed.journal(dict(dataset='cvpr', scene='shared_tracker_full_cohort', budget='1x_1p5x',
                       arm='same_tracking_config', status=live_stage['status'], output=str(live)))
    geometry = RESULTS / 'cvpr_assets/geometry_zero_weights_v1'
    geometry.mkdir(parents=True, exist_ok=False)
    write(geometry / 'protocol.json', dict(seed=0, budget=40, candidates=[r['scene'] for r in inventory],
        weights_off=dict(hard=0, main=0), weights_on=dict(hard=.0315, main=.25),
        proxy_forward_work_retained=True, optimizer_batch_size=1,
        kappa=16, tau0=4, quotas=[3, 3, 6], scene_specific_tuning=False, source_lock=source))
    measured = []
    for item in inventory:
        print('GEOMETRY_ZERO_START', item['dataset'], item['scene'], flush=True)
        try:
            row = geometry_control(item, geometry, py, source)
        except Exception:
            row = dict(dataset=item['dataset'], scene=item['scene'], budget=40,
                arm='geometry_zero_weights', status='failed', error=traceback.format_exc(),
                output=str(geometry / 'render40' / item['dataset'] / item['scene'] / 'geometry_zero_weights'))
        measured.append(row); write(geometry / 'summary.json', measured); fixed.journal(row)
        print('GEOMETRY_ZERO_DONE', row['scene'], row['status'], row.get('psnr'), flush=True)
    jobs = []
    for panel in [RESULTS / 'cvpr_assets/current_controls_v1', geometry, RESULTS / 'cvpr_assets/live_shared_tracking_v1']:
        if not (panel / 'summary.json').exists(): continue
        for item in read(panel / 'summary.json'):
            if item['status'] != 'passed': continue
            run = Path(item['output'])
            name = run.relative_to(RESULTS / 'cvpr_assets').as_posix().replace('/', '__')
            jobs.append((name, run, item['dataset'], item['scene']))
    rows = []
    for name, run, dataset, scene in jobs:
        row = dict(stage=name, run=str(run), status='failed')
        print('FOLLOWUP_CURVE_START', name, flush=True)
        try:
            command = [py, str(HERE / 'evaluate_cvpr_checkpoints.py'), '--run', str(run),
                       '--dataset', dataset, '--scene', scene]
            command_run(command, a.output / f'{name}.log', fixed.environment('vanilla'))
            row['artifact_check_passed'] = curves_ok(run)
            row['status'] = 'passed' if row['artifact_check_passed'] else 'failed'
        except Exception:
            row['error'] = traceback.format_exc()
        rows.append(row); write(a.output / 'summary.json', rows)
        fixed.journal(dict(dataset=dataset, scene=scene, budget='checkpoint_curve',
                           arm=name, status=row['status'], output=str(run / 'curve_evaluation')))
    write(a.output / 'completion.json', dict(geometry_control_count=len(measured),
        geometry_passed=sum(r['status'] == 'passed' for r in measured),
        checkpoint_jobs=len(jobs), checkpoints_passed=sum(r['status'] == 'passed' for r in rows),
        source_unchanged=all(sha(Path(path)) == digest for path, digest in source.items())))
    print('FOLLOWUP_FINISHED', flush=True)


if __name__ == '__main__': main()
