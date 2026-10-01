#!/usr/bin/env python3
"""Restore original T4 PSNR from archived paired measurements, not a new run.

The historical dirty source and saved maps are unavailable on this machine.
Matching JSON/CSV and job manifests support reported PSNR, but cannot establish
a fresh reproduction, SSIM/LPIPS, or equivalence to the current online mapper.
"""
import csv
import json
from pathlib import Path
import statistics
import sys

PAPER = Path(__file__).resolve().parents[1]
ROOT = PAPER.parent
sys.path.insert(0, str(PAPER / 'scripts'))
from build_measured_tables import read, sha, CANDIDATES

SOURCE = ROOT / 'context/experiments/ERCB_ablation/benchmark-B/evidence'
ANALYSIS = PAPER / 'tables/table04_sampling_budget/analysis'


def main():
    summary = read(SOURCE / 'summary.json'); manifest = read(SOURCE / 'manifest.json')
    assert summary['protocol'] == manifest['protocol']
    assert summary['requested_scenes'] == 20 and summary['available_scenes'] == 19
    contract = manifest['contract']
    assert contract['primary_budgets'] == [15, 30, 60] and contract['fixed_topology']
    assert contract['loss'] == 'RGB-only' and contract['heldout'] == 'llffhold-8'
    assert contract['tail_updates'] == 0 and contract['seed'] == 0
    key = lambda x: (x['family'], x['scene'], int(x['stride']), int(x['budget']), x['arm'], int(x['seed']))
    with (SOURCE / 'summary.csv').open(newline='') as f:
        csv_rows = {key(r): r for r in csv.DictReader(f)}
    jobs = {key(r): r for r in manifest['jobs']}
    assert len(jobs) == len(manifest['jobs']) == len(summary['runs']) == len(csv_rows) == 152
    rows = []
    for row in summary['runs']:
        csv_row, job = csv_rows[key(row)], jobs[key(row)]
        assert job['state'] == 'complete' and job['returncode'] == 0
        assert row['updates'] == int(csv_row['updates']) == job['total_iterations']
        assert row['gaussians'] == int(csv_row['gaussians'])
        assert abs(row['heldout_psnr_db'] - float(csv_row['heldout_psnr_db'])) < 1e-10
        assert row['output'] == csv_row['output'] == job['output']
        argv = job['argv']
        assert argv[argv.index('--densify_until_iter') + 1] == '0'
        assert '--fixed_topology_step_before_report' in argv
        if row['stride'] != 20: continue
        rows.append(dict(dataset=row['family'], scene=row['scene'], budget=row['budget'], sampler=row['arm'],
            psnr_db=row['heldout_psnr_db'], gaussians=row['gaussians'], optimizer_steps=row['updates'],
            train_frames=job['train_frames'], heldout_frames=job['heldout_frames'], source_run=row['output'],
            metric_status='archived_report; raw map/per-view scores unavailable locally'))
    assert len(rows) == 114
    measured = {(r['dataset'], r['scene']) for r in rows}
    declared = {(d, s) for d, scenes in CANDIDATES.items() for s in scenes}
    assert measured == declared - {('utmm', 'slow-straight-1')}
    for dataset, scene in measured:
        pair = [r for r in rows if (r['dataset'], r['scene']) == (dataset, scene)]
        assert len(pair) == 6 and len({r['gaussians'] for r in pair}) == 1
        for budget in [15, 30, 60]:
            arms = [r for r in pair if r['budget'] == budget]
            assert {r['sampler'] for r in arms} == {'rr', 'ercb'}
            assert len({r['optimizer_steps'] for r in arms}) == 1
            assert len({r['heldout_frames'] for r in arms}) == 1
    ANALYSIS.mkdir(exist_ok=True)
    data = ANALYSIS / 'archived_original_sampling_measurements.csv'
    with data.open('w', newline='') as f:
        writer = csv.DictWriter(f, list(rows[0])); writer.writeheader(); writer.writerows(rows)
    averages = {arm: [statistics.mean(r['psnr_db'] for r in rows if r['budget'] == budget and r['sampler'] == arm)
                     for budget in [15, 30, 60]] for arm in ['rr', 'ercb']}
    body = []
    for metric in ['PSNR', 'SSIM', 'LPIPS']:
        for arm, label in [('rr', 'RR'), ('ercb', 'Interval ERCB')]:
            values = [f'{x:.2f}' for x in averages[arm]] if metric == 'PSNR' else [r'\textemdash'] * 3
            body.append(' & '.join([metric + (r' $\downarrow$' if metric == 'LPIPS' else r' $\uparrow$'), label, *values]) + r' \\')
        if metric != 'LPIPS': body.append(r'\midrule')
    tex = '\n'.join([r'% Archived benchmark-B measurements, not current-code reruns.',
        r'\begin{table}[tbp]', r'\centering',
        r'\caption{Original interval-sampling comparison: archived fixed-topology 3DGS replay measurements. Equal scene-weighted PSNR over 19 available scenes.}',
        r'\label{tab:order}', r'\begingroup', r'\footnotesize', r'\setlength{\tabcolsep}{3pt}',
        r'\resizebox{\linewidth}{!}{%', r'\begin{tabular}{@{}llccc@{}}', r'\toprule',
        r'Metric & Sampling policy & \shortstack{15 updates\\per interval} & \shortstack{30 updates\\per interval} & \shortstack{60 updates\\per interval} \\',
        r'\midrule', *body, r'\bottomrule', r'\end{tabular}}', r'\endgroup', r'\par\vspace{3pt}',
        r'\begin{minipage}{\linewidth}', r'\scriptsize\raggedright '
        r'Historical scheduler-isolation replay with fixed final poses/initialization, RGB-only loss, seed0, resolution4, llffhold-8 and zero tail; this is not an online-system comparison. '
        r'Both samplers use the same map (mean91.3k Gaussians). UTMM \texttt{slow-straight-1} was unavailable (19/20 scenes). '
        r'SSIM/LPIPS are absent from the archived report. JSON/CSV values and completed-job manifests agree, but the original dirty source and raw maps are not restored; these are not fresh reproductions. '
        r'Current per-view ERVS at 15/40 renders/KF is reported separately.', r'\end{minipage}', r'\end{table}', ''])
    (ANALYSIS / 'archived_original_sampling.tex').write_text(tex)
    local_source = ROOT / 'repos/main/3dgs-custom'
    original_hashes = manifest['implementation_sha256']
    current_hashes = {name: sha(local_source / name) for name in ['train.py', 'runtime/scheduler.py']}
    provenance = dict(kind='archived_original_interval_sampling_measurements', archived_metrics=True,
        experimental_evidence=True, fresh_reproduction=False, raw_maps_available_here=False,
        original_source_restored=all(current_hashes[k] == original_hashes[k] for k in current_hashes),
        sources={str(SOURCE / name): sha(SOURCE / name) for name in ['summary.json', 'summary.csv', 'manifest.json']},
        original_source_hashes=original_hashes, currently_available_source_hashes=current_hashes,
        paired_runs=114, available_scenes=19, requested_scenes=20, unavailable=manifest['unavailable'],
        averages=averages, missing_metrics=['SSIM', 'LPIPS'], manuscript_width='one_column',
        generator_sha256=sha(Path(__file__)), data=str(data), data_sha256=sha(data),
        table_sha256=sha(ANALYSIS / 'archived_original_sampling.tex'))
    (ANALYSIS / 'archived_original_sampling_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print('ARCHIVED_T4', averages, 'original_source_restored', provenance['original_source_restored'])


if __name__ == '__main__': main()
