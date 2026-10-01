"""Handoff follow-up: clean D3 controls, then historical sampler reproduction.

No FIFO or wall-time panel is launched. Never write into the original dirty
3dgs worktree, archived runs, or the immutable prepared sampler manifest.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_cvpr_measurements as fixed
from collect_cvpr_assets import ROOT, MAIN, OUT, read, write, sha
from run_cvpr_asset_pipeline import process_identity
from run_cvpr_followup_panel import geometry_control, wait_gpu
from resume_cvpr_5070ti import evaluate_curves, inputs_ready, wait_for


def reproduce(manifest_path, output, status):
    manifest = read(manifest_path)
    repo = Path(manifest['isolated_repo'])
    expected = manifest['implementation_sha256']
    checks = {str(repo / k): v for k, v in expected.items() if not k.startswith('exp77/')}
    checks[str(ROOT / 'context/experiments/exp77/run_training.py')] = expected['exp77/run_training.py']
    assert all(sha(Path(k)) == v for k, v in checks.items())
    assert all(sha(Path(k)) == v for k, v in manifest['input_file_hashes'].items())
    spec = importlib.util.spec_from_file_location('historical_b_completion', ROOT / 'context/experiments/ERCB_ablation/benchmark-B/run_panel.py')
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    rows = []
    env = dict(os.environ)
    env.pop('ROGO_MACHINE_PROFILE', None)
    env.pop('PYTHONPATH', None)
    for j in manifest['jobs']:
        target = Path(j['output'])
        assert not target.exists(), f'Existing output requires inspection: {target}'
        target.parent.mkdir(parents=True, exist_ok=True)
        write(status, {'stage': 'original_sampler', 'scene': j['scene'], 'budget': j['budget'], 'arm': j['arm'], 'updated': time.time()})
        wait_gpu()
        with target.with_suffix('.train.log').open('x') as log:
            subprocess.run(j['argv'], cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        assert legacy.completed(target, j['total_iterations']), target
        assert all(sha(Path(k)) == v for k, v in checks.items())
        historical = Path(j['historical_output'])
        assert sha(target / 'input.ply') == sha(historical / 'input.ply')
        assert sha(target / 'cameras.json') == sha(historical / 'cameras.json')
        old_sampler = read(historical / 'view_scheduler_summary.json')
        new_sampler = read(target / 'view_scheduler_summary.json')
        semantic = lambda x: {k: v for k, v in x.items() if k not in ('scheduler_cpu_ns', 'training_gpu_ms')}
        assert semantic(old_sampler) == semantic(new_sampler), 'Historical sampling trace mismatch'
        curve = [json.loads(s) for s in (target / 'evaluation_curve.jsonl').read_text().splitlines() if s]
        final = [r for r in curve if r.get('split') == 'test' and r['iteration'] == j['total_iterations']]
        assert len(final) == 1
        results = []
        for repeat in (1, 2):
            commands = [
                [j['argv'][0], str(repo / 'render.py'), '-m', str(target), '--eval', '--skip_train', '--iteration', str(j['total_iterations']), '--quiet'],
                [j['argv'][0], str(repo / 'metrics.py'), '-m', str(target)]]
            for index, command in enumerate(commands):
                wait_gpu()
                with (target / f'eval_{repeat}_{index}.log').open('x') as log:
                    subprocess.run(command, cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            key = f"ours_{j['total_iterations']}"
            metric = read(target / 'results.json')[key]
            views = read(target / 'per_view.json')[key]
            assert all(len(views[k]) == j['heldout_frames'] for k in ('PSNR', 'SSIM', 'LPIPS'))
            results.append({'metrics': metric, 'per_view': views})
            write(target / f'saved_map_evaluation_{repeat}.json', results[-1])
        assert results[0] == results[1], 'Saved-map double evaluation mismatch'
        row = {**{k: j[k] for k in ('family', 'scene', 'budget', 'arm', 'seed', 'total_iterations')},
               'output': str(target), 'status': 'passed', 'training_curve_psnr': final[0]['psnr'],
               'saved_map_metrics': results[0]['metrics'], 'saved_map_double_eval_match': True,
               'historical_initial_cloud_camera_cohort_sampler_match': True,
               'source_hashes': checks, 'historical_output': j['historical_output']}
        rows.append(row)
        write(output / 'original_sampler_summary.json', rows)
        fixed.journal(dict(dataset=j['family'], scene=j['scene'], budget=j['budget'], arm='original_sampler_'+j['arm'],
                           status='passed', psnr=row['saved_map_metrics']['PSNR'], output=str(target)))
    assert len(rows) == 114
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--wait-pid', type=int, required=True)
    p.add_argument('--controls', type=Path, required=True)
    p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--original-manifest', type=Path, required=True)
    p.add_argument('--archived-controls', type=Path, required=True)
    p.add_argument('--archived-transfer-pid', type=int, required=True)
    a = p.parse_args()
    identity = process_identity(a.wait_pid)
    assert identity is not None and 'resume_cvpr_5070ti.py' in identity['cmd'], identity
    a.output.mkdir(parents=True, exist_ok=False)
    status = a.output / 'queue_status.json'
    try:
        write(a.output / 'protocol.json', {'wait_identity': identity, 'script_sha256': sha(Path(__file__)),
            'reference': str(a.reference), 'original_manifest_sha256': sha(a.original_manifest),
            'geometry': '40 training renders/KF; existing D3 weights zero; proxy work retained',
            'original_sampler': '19 scenes x 15/30/60 x RR/interval ERCB; exact historical train/scheduler hashes',
            'realtime_panels': 'deferred', 'time_comparison': False})
        while True:
            now = process_identity(a.wait_pid)
            if now is None or now['state'] == 'Z' or now['start'] != identity['start']: break
            write(status, {'stage': 'waiting_controls_and_curves', 'verified_process': now, 'updated': time.time()})
            time.sleep(30)
        assert read(a.controls / 'queue_status.json')['stage'] == 'fixed_work_controls_and_curves_complete'
        rows = read(a.controls / 'summary.json')
        assert len(rows) == 121 and all(r['status'] == 'passed' for r in rows)
        fixed.install_paths()
        sys.path.insert(0, str(MAIN / 'scripts/selected_mapping'))
        from selected_mapping_check import verify_files
        lock = read(MAIN / 'scripts/selected_mapping/source_lock.json')
        verify_files(lock['sources']); verify_files(lock['extension_files'])
        inventory = read(OUT / 'scene_inventory.json')
        assert len(inventory) == 20
        inputs_ready(inventory)
        fixed.journal(dict(dataset='all20', scene='local_controls_121_curves', budget='checkpoint_curve',
                           arm='checkpoint_evaluation', status='passed', output=str(a.controls)))
        wait_for([a.archived_transfer_pid], status, 'waiting_archived_controls_transfer')
        archived = [r for r in read(a.archived_controls / 'summary.json') if r['status'] == 'passed']
        declared = read(ROOT / 'context/experiments/campaigns/06_gain_attribution/handoff_5070ti/completed_controls.json')
        identity_key = lambda r: (r['dataset'], r['scene'], r['budget'], r['arm'])
        assert len(archived) == 19 and {identity_key(r) for r in archived} == {identity_key(r) for r in declared}
        evaluate_curves(archived, a.output, status, 'archived_control_curves')
        fixed.journal(dict(dataset='archived19', scene='controls_5090_maps_evaluated_on_5070ti', budget='checkpoint_curve',
                           arm='checkpoint_evaluation', status='passed', output=str(a.archived_controls)))
        table_command = [sys.executable, str(ROOT / 'paper/scripts/build_measured_control_tables.py'),
                         '--panels', str(a.archived_controls / 'summary.json'), str(a.controls / 'summary.json'),
                         '--output-dir', str(a.output / 'control_table_review'), '--require-complete']
        with (a.output / 'control_table_review.log').open('x') as log:
            subprocess.run(table_command, stdout=log, stderr=subprocess.STDOUT, check=True)
        source = {str(f): sha(f) for f in [*MAIN.glob('vigs/**/*.py'), *fixed.GEOM.glob('*.py'),
                  Path(fixed.__file__), HERE / 'run_cvpr_followup_panel.py', Path(__file__)]}
        write(a.output / 'source_lock.json', source)
        geometry = a.output / 'geometry_zero_weights'
        geometry.mkdir()
        measured = []
        for item in inventory:
            write(status, {'stage': 'geometry_zero_weights', 'scene': item['scene'], 'updated': time.time()})
            row = geometry_control(item, geometry, sys.executable, source, a.reference)
            measured.append(row); write(geometry / 'summary.json', measured); fixed.journal(row)
        assert len(measured) == 20 and all(r['status'] == 'passed' for r in measured)
        evaluate_curves(measured, a.output, status, 'geometry_curves')
        fixed.journal(dict(dataset='all20', scene='geometry_zero_weights_curves', budget=40,
                           arm='checkpoint_evaluation', status='passed', output=str(geometry)))
        original = reproduce(a.original_manifest, a.output, status)
        write(status, {'stage': 'complete', 'geometry_passed': len(measured), 'original_sampler_passed': len(original),
                       'table_aggregation': 'pending', 'updated': time.time()})
    except BaseException:
        write(status, {'stage': 'failed', 'traceback': traceback.format_exc(), 'updated': time.time()})
        raise


if __name__ == '__main__': main()
