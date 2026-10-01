#!/usr/bin/env python3
"""Read-only catalog of the declared shared-tracker live experiments.

Clock curves use saved maps and their actual monotonic capture times. Tracking
call durations are CPU wall time, including waiting; they are not GPU occupancy.
No production mapper or currently running experiment script is modified.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import sys

PAPER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER / 'scripts'))
from build_measured_tables import CANDIDATES, RESULTS, read, sha

PANEL = RESULTS / 'cvpr_assets/live_shared_tracking_v1'
ANALYSIS = PAPER / 'figures/figure11_equal_time_online/analysis'


def write_rows(path, rows):
    if not rows:
        return
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, list(dict.fromkeys(k for row in rows for k in row)))
        writer.writeheader(); writer.writerows(rows)


def runtime_events(run, result, origin, deadline):
    """Return successful optimizer times and associated training render counts."""
    if (run / 'runtime.json').exists():
        runtime = read(run / 'runtime.json')
        boundary = runtime['boundaries']
        assert abs(boundary['deadline'] - deadline) < 1e-6
        assert all(x['seconds'] <= deadline for x in boundary['mutation_completions'])
        steps = [x for x in boundary['optimizer_completions'] if x['role'] == 'main']
        services = [x for generation in runtime['training']['generations'] for x in generation['services']]
        assert len(steps) == len(services)
        events = [(step['seconds'] - origin, len(service['uids'])) for step, service in zip(steps, services)]
        assert sum(count for _, count in events) == result['committed_renders']
        source = run / 'runtime.json'
    else:
        services = read(run / 'services.json')
        events, previous = [], 0
        for service in services:
            assert service['renders'] >= previous
            events.append((service['time'] - origin, service['renders'] - previous))
            previous = service['renders']
        assert previous == result['committed_renders']
        source = run / 'services.json'
    assert all(0 <= t <= result['duration_seconds'] for t, _ in events)
    assert result['worker']['closed'] and result['worker']['error'] is None
    assert result['worker']['stopped_at'] <= deadline + .05
    return events, source


def work_bins(run, result, events, bin_seconds=5.):
    """Fixed five-second bins, with explicit NA when no admission is observed."""
    frames = read(run / 'frames.json')
    assert len(frames) == result['tracked_frames'] == result['input_frames']
    assert all(a['end_seconds'] <= b['end_seconds'] for a, b in zip(frames, frames[1:]))
    duration = result['duration_seconds']
    records = []
    for index in range(math.ceil(duration / bin_seconds)):
        start, end = index * bin_seconds, min((index + 1) * bin_seconds, duration)
        tracking_seconds = sum(max(0., min(end, f['end_seconds']) - max(start, f['start_seconds'])) for f in frames)
        renders = sum(count for time, count in events if start <= time < end or time == end == duration)
        # Admissions are queried after each tracking call. Their timestamp is an
        # observation bound, not an exact mapper-thread admission event time.
        prior = max((f['kf_admissions'] for f in frames if f['end_seconds'] < start), default=0)
        now = max((f['kf_admissions'] for f in frames if f['end_seconds'] < end), default=prior)
        admissions = now - prior
        assert admissions >= 0 and tracking_seconds <= end - start + 1e-6
        records.append(dict(bin_index=index, start_seconds=start, end_seconds=end,
            tracking_call_wall_seconds=tracking_seconds, tracking_call_wall_fraction=tracking_seconds/(end-start),
            committed_training_renders=renders, frame_observed_mapper_admissions=admissions,
            renders_per_frame_observed_admission=renders/admissions if admissions else '',
            admission_timestamp_rule='first frame-end query reporting cumulative admission count',
            no_admission_status='NA' if admissions == 0 else 'measured'))
    assert sum(r['committed_training_renders'] for r in records) == result['committed_renders']
    return records


def collect():
    summaries = read(PANEL / 'summary.json') if (PANEL / 'summary.json').exists() else []
    lookup = {(r['dataset'], r['scene'], float(r['time_scale']), r['arm']): r for r in summaries}
    assert len(lookup) == len(summaries), 'Duplicate live condition'
    declared = {(d, s) for d, scenes in CANDIDATES.items() for s in scenes}
    assert {(r['dataset'], r['scene']) for r in summaries} <= declared
    runs, points, bins = [], [], []
    for dataset, scenes in CANDIDATES.items():
        for scene in scenes:
            for scale in [1., 1.5]:
                for arm in ['vanilla', 'ours']:
                    condition = dict(dataset=dataset, scene=scene, allowance=scale, arm=arm)
                    entry = {**condition, 'status': 'awaiting_live_run', 'points': []}
                    runs.append(entry)
                    state = lookup.get((dataset, scene, scale, arm))
                    if state is None: continue
                    if state['status'] != 'passed':
                        entry.update(status='failed_live_run', error=state.get('error')); continue
                    run = Path(state['output']); result = read(run / 'result.json')
                    assert not result['error'] and result['source_unchanged'] and result['zero_tail_observed']
                    assert result['time_scale'] == scale
                    origin = result['stream_start_monotonic_time']
                    deadline = origin + result['duration_seconds']
                    assert math.isfinite(origin) and result['duration_seconds'] > 0
                    effective = read(run / 'effective_config.json')
                    assert read(run / 'adapter_provenance.json')['tracking_recipe'] == 'shared_official_dataset_config'
                    events, event_source = runtime_events(run, result, origin, deadline)
                    bin_rows = work_bins(run, result, events)
                    for row in bin_rows: bins.append({**condition, **row, 'event_source': str(event_source),
                        'event_source_sha256': sha(event_source), 'frames_source_sha256': sha(run / 'frames.json')})
                    entry.update(status='awaiting_checkpoint_evaluation', run=str(run),
                        elapsed_allowance_seconds=result['duration_seconds'],
                        tracking_elapsed_seconds=result['tracking_elapsed_seconds'],
                        tracking_exceeds_allowance=result['tracking_elapsed_seconds'] > result['duration_seconds'],
                        training_renders=result['training_renders'], committed_training_renders=result['committed_renders'],
                        additional_proxy_renders=result.get('geometry', {}).get('stats', {}).get('aux_renders', 0),
                        snapshot_copy_seconds=read(run / 'snapshots/manifest.json')['copy_seconds'],
                        tracking_config=effective['config']['Tracking'], frontend_iterations=result['frontend_iterations'],
                        result_source_sha256=sha(run / 'result.json'), bins=bin_rows)
                    summary = run / 'curve_evaluation/summary.json'
                    if not summary.exists(): continue
                    subset = read(run / 'curve_evaluation/fixed_subset_manifest.json')
                    entry['subset_views'] = subset['views']
                    rejected = []
                    for row in read(summary):
                        if row['status'] != 'evaluated' or not row.get('usable_for_convergence_claim'):
                            rejected.append(row); continue
                        checkpoint = row['checkpoint']; final = bool(checkpoint.get('final'))
                        elapsed = result['duration_seconds'] if final else checkpoint['capture_monotonic_time'] - origin
                        assert 0 <= elapsed <= result['duration_seconds'] + .05
                        metric_path = Path(row['output']) / 'psnr/curve_fixed_subset/final_result.json'
                        metric = read(metric_path)['predeclared_fixed_manifest_posthoc']
                        assert metric['mapping_disjoint'] and metric['mapping_view_overlap_count'] == 0
                        assert metric['view_count'] == len(subset['views'])
                        assert abs(metric['mean_psnr'] - row['quality']['mean_psnr']) < 1e-8
                        point = {**condition, 'checkpoint': row['name'], 'final': final,
                            'elapsed_seconds': elapsed, 'training_renders': result['training_renders'] if final else checkpoint['training_renders'],
                            'psnr_db': metric['mean_psnr'], 'view_count': metric['view_count'],
                            'metric': str(metric_path), 'metric_sha256': sha(metric_path), 'summary_sha256': sha(summary)}
                        points.append(point); entry['points'].append(point)
                    entry['points'].sort(key=lambda x: x['elapsed_seconds'])
                    assert all(a['training_renders'] <= b['training_renders'] for a, b in zip(entry['points'], entry['points'][1:]))
                    entry.update(status='measured' if len(entry['points']) >= 2 and any(p['final'] for p in entry['points']) else 'insufficient_accepted_checkpoints',
                        rejected_checkpoints=rejected)
    for dataset, scene in declared:
        quartet = [r for r in runs if (r['dataset'], r['scene']) == (dataset, scene) and 'tracking_config' in r]
        if quartet:
            assert len({json.dumps(r['tracking_config'], sort_keys=True) for r in quartet}) == 1
            assert len({tuple(r['frontend_iterations']) for r in quartet}) == 1
        evaluated = [r for r in quartet if 'subset_views' in r]
        if evaluated: assert all(r['subset_views'] == evaluated[0]['subset_views'] for r in evaluated)
    payload = dict(kind='actual_shared_tracking_live_curve_catalog', expected_runs=80,
        live_runs_measured=sum('run' in r for r in runs), curves_measured=sum(r['status'] == 'measured' for r in runs),
        all_candidate_live_runs_considered=all('run' in r or r['status'] == 'failed_live_run' for r in runs),
        all_candidate_runs_evaluated=all(r['status'] in ['measured', 'insufficient_accepted_checkpoints', 'failed_live_run'] for r in runs),
        clock='actual time.monotonic capture minus recorded stream origin; warm load outside clock',
        final_state_rule='deadline-held map; successful optimizers and recorded mutations end before allowance',
        bins_rule='fixed5seconds; CPU tracking call wall time; frame-sampled admission counts; no capacity extrapolation',
        generator=str(Path(__file__)), generator_sha256=sha(Path(__file__)), runs=runs)
    ANALYSIS.mkdir(exist_ok=True)
    write_rows(ANALYSIS / 'measured_live_curve_points.csv', points)
    write_rows(ANALYSIS / 'measured_live_work_bins.csv', bins)
    (ANALYSIS / 'measured_live_curve_catalog.json').write_text(json.dumps(payload, indent=2) + '\n')
    return payload


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    result = collect()
    print('SHARED_LIVE_CURVE_CATALOG', result['live_runs_measured'], 'live runs;', result['curves_measured'], '/80 accepted curves')
