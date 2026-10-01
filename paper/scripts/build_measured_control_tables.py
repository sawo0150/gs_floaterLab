#!/usr/bin/env python3
"""Current-code sampling and RGB-source tables from audited completed pairs.

The original offline15/30/60 ERCB template remains a separate unmeasured panel.
No current15/40 result is relabeled as an original-replay measurement.
"""
import argparse
import csv
import json
from pathlib import Path
import shutil
import statistics
import sys

PAPER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER / 'scripts'))
from build_measured_tables import CANDIDATES, DISPLAY, RESULTS, read, sha, fmt, EMPTY
from collect_cvpr_assets import endpoint
from build_draft_tables import escape

METRICS = ['psnr', 'ssim', 'lpips', 'gaussians']
CASES = ['rr_dense', 'ervs_kf_rgb', 'rr_kf_rgb']


def collect(panels=None):
    panels = panels or [RESULTS / 'cvpr_assets/current_controls_v1/summary.json']
    states = [{**r, 'source_summary': str(panel)} for panel in panels if panel.exists() for r in read(panel)]
    rows = []
    for item in states:
        if item['status'] != 'passed' or item['arm'] not in CASES: continue
        run, reference = Path(item['output']), Path(item['reference'])
        assert read(run / 'evaluation_consistency.json')['pass']
        audit = read(run / 'comparison_audit.json')
        assert audit['same_prefix_renders_poses_cohort']
        a, b = read(run / 'render_result.json'), read(reference / 'render_result.json')
        assert a['valid_execution'] and all(a['checks'].values())
        assert b['valid_execution'] and all(b['checks'].values())
        assert read(reference / 'evaluation_consistency.json')['pass']
        prefix = lambda x: [(r['uid'], r['training_renders']) for r in x['render_prefixes']]
        assert prefix(a) == prefix(b)
        for name in ['traj_full_beforeBA.txt', 'traj_kf_beforeBA.txt']:
            assert sha(run / name) == sha(reference / name)
        for case, path in [(item['arm'], run), ('ervs_dense', reference)]:
            row = endpoint('current_control', path, item['dataset'], item['scene'], case, item['budget'])
            assert row is not None
            row.update(case=case, budget=item['budget'], audit_path=str(run / 'comparison_audit.json'),
                       audit_sha256=sha(run / 'comparison_audit.json'), source_summary=item['source_summary'])
            duplicate = next((r for r in rows if (r['dataset'], r['scene'], r['budget'], r['case']) ==
                             (row['dataset'], row['scene'], row['budget'], row['case'])), None)
            if duplicate is None: rows.append(row)
            else: assert duplicate['metric_sha256'] == row['metric_sha256'], 'Conflicting records for the same table cell'
        pair = [r for r in rows if (r['dataset'], r['scene'], r['budget']) ==
                (item['dataset'], item['scene'], item['budget']) and r['case'] in [item['arm'], 'ervs_dense']]
        assert len({r['cohort_uid_sha256'] for r in pair}) == 1
    return rows, [r for r in states if r['status'] != 'passed']


def table(kind, rows):
    sampling = kind == 'sampling'
    cases = ['rr_dense', 'ervs_dense'] if sampling else ['ervs_kf_rgb', 'ervs_dense']
    labels = ['RR', 'ERVS'] if sampling else ['KF RGB only', '+ in-between RGB']
    body, groups = [], []
    for budget in [15, 40]:
        body.append(r'\multicolumn{8}{@{}l}{\textit{' + str(budget) + r' training renders/KF}} \\')
        for dataset, scenes in CANDIDATES.items():
            selected = [r for r in rows if r['budget'] == budget and r['dataset'] == dataset and r['case'] in cases]
            paired = [s for s in scenes if {r['case'] for r in selected if r['scene'] == s} == set(cases)]
            group = dict(dataset=dataset, budget=budget, scenes=paired, count=len(paired), expected=len(scenes), cases=cases)
            groups.append(group)
            for i, (case, label) in enumerate(zip(cases, labels)):
                measurements = [r for r in selected if r['scene'] in paired and r['case'] == case]
                values = [fmt(statistics.mean(r[m] for r in measurements), m) if measurements else EMPTY for m in METRICS]
                cells = [DISPLAY[dataset] if i == 0 else '', str(budget) if i == 0 else '',
                         label, f'{len(paired)}/{len(scenes)}', *values]
                body.append(' & '.join(cells) + r' \\')
        body.append(r'\midrule')
    body.pop()
    caption = ('Current merged mapper: RR versus cumulative-count ERVS with in-between RGB supervision.' if sampling else
        'Current merged mapper: replace the extra RGB slots with keyframe RGB-only supervision or use in-between RGB images; both use ERVS.')
    label = 'tab:current_sampling' if sampling else 'tab:abl'
    return '\n'.join([r'\begin{table}[tbp]', r'\centering', r'\caption{' + caption + '}',
        r'\label{' + label + '}', r'\begingroup', r'\footnotesize',
        r'\setlength{\tabcolsep}{2.5pt}', r'\renewcommand{\arraystretch}{1.04}',
        r'\resizebox{\linewidth}{!}{%', r'\begin{tabular}{@{}llrlrrrr@{}}',
        r'\toprule', r'Dataset & Budget & ' + ('Sampler' if sampling else 'RGB supervision') +
        r' & $n/N$ & PSNR $\uparrow$ & SSIM $\uparrow$ & LPIPS $\downarrow$ & \#G (k) \\',
        r'\midrule', *body, r'\bottomrule', r'\end{tabular}}', r'\endgroup',
        r'\par\vspace{3pt}', r'\begin{minipage}{\linewidth}',
        r'\scriptsize\raggedright Equal scene-weighted means over completed pairs only; $n/N$ gives coverage of the declared dataset. '
        r'Dashes mean unmeasured. The paired sensor trace, poses, render prefixes and held-out cohort are verified. '
        r'The current D3 objective and protected opacity pruning are common; D3 proxy renders are additional work. '
        + (r'This is the current per-view ERVS implementation, distinct from the original offline interval ERCB 15/30/60 replay.' if sampling else
           r'This is a whole-system supervision-source replacement, not a comparison to vanilla. Realized role counts and learning-rate positions may differ.'),
        r'\end{minipage}', r'\end{table}', '']), groups


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--panels', type=Path, nargs='+', help='Explicit summary.json files to combine')
    p.add_argument('--output-dir', type=Path, help='Write a review bundle instead of replacing current manuscript assets')
    p.add_argument('--require-complete', action='store_true', help='Require every declared paired scene at both budgets')
    a = p.parse_args()
    if a.panels: assert all(panel.is_file() for panel in a.panels), 'Missing requested panel'
    rows, failures = collect(a.panels)
    if not rows:
        if a.require_complete: raise RuntimeError('No audited pairs: complete tables cannot be produced')
        print('No audited control pair completed yet'); return
    rendered = {kind: table(kind, rows) for kind in ('sampling', 'source')}
    if a.require_complete:
        assert all(g['count'] == g['expected'] for _, groups in rendered.values() for g in groups), 'Incomplete paired cohort'
    if a.output_dir:
        a.output_dir.mkdir(parents=True, exist_ok=False)
        data = a.output_dir / 'measurements.csv'
        with data.open('w', newline='') as f:
            w = csv.DictWriter(f, list(dict.fromkeys(k for r in rows for k in r))); w.writeheader(); w.writerows(rows)
        for kind, (tex, groups) in rendered.items():
            (a.output_dir / f'{kind}.tex').write_text(tex)
        write = lambda p, x: p.write_text(json.dumps(x, indent=2) + '\n')
        write(a.output_dir / 'provenance.json', dict(rows=rows, failures=failures,
            groups={kind: groups for kind, (_, groups) in rendered.items()},
            panels={str(p): sha(p) for p in (a.panels or [RESULTS / 'cvpr_assets/current_controls_v1/summary.json'])},
            complete_required=a.require_complete, cross_gpu_time_comparison=False,
            scope='Held-out quality only; each control retains its explicit paired reference',
            generator_sha256=sha(Path(__file__)), data_sha256=sha(data)))
        print('CONTROL_TABLE_REVIEW_BUNDLE', a.output_dir)
        return
    data = PAPER / 'results/tables/cvpr_control_measurements.csv'
    with data.open('w', newline='') as f:
        w = csv.DictWriter(f, list(dict.fromkeys(k for r in rows for k in r))); w.writeheader(); w.writerows(rows)
    for kind, asset, portable in [('sampling', 'table04_sampling_budget', 't4_sampling_draft.tex'),
                                  ('source', 'table05_dense_supervision', 't5_dense_draft.tex')]:
        folder = PAPER / 'tables' / asset
        current = folder / 'current'
        archive = folder / 'output/blank_before_current_controls_2026-10-01'
        if not archive.exists(): shutil.copytree(current, archive)
        tex, groups = table(kind, rows)
        if kind == 'sampling':
            # Archived original-code metrics are explicitly a historical replay;
            # they cannot be relabeled as current online measurements.
            restored = folder / 'analysis/archived_original_sampling.tex'
            original = restored if restored.exists() else archive / 'table.tex'
            tex = original.read_text() + '\n' + tex
        (current / 'table.tex').write_text(tex)
        (PAPER / 'latex/tab' / portable).write_text(tex)
        caption = ('현재 merged-code의 실제 paired control 결과. original replay 15/30/60은 보존된 실측 요약의 PSNR이며 새 재현이 아니다; current ERVS 15/40과 구분한다. 미완료 cohort와 실패는 provenance에 남긴다.' if kind == 'sampling' else '현재 merged-code에서 dense RGB와 KF RGB를 대체한 실제 paired control 결과. 미완료 cohort와 실패는 provenance에 남긴다.')
        (current / 'caption.md').write_text(caption + '\n')
        original_provenance = folder / 'analysis/archived_original_sampling_provenance.json'
        original = read(original_provenance) if kind == 'sampling' and original_provenance.exists() else None
        (current / 'provenance.json').write_text(json.dumps(dict(kind='actual_current_control_table',
            experimental_evidence=True, original_replay_measurements_available=bool(original),
            original_replay_fresh_reproduction=False, original_replay=original,
            data=str(data), data_sha256=sha(data), rows=rows, paired_groups=groups, failures=failures,
            manuscript_width='one_column', generator=str(Path(__file__)), generator_sha256=sha(Path(__file__)),
            table_sha256=sha(current / 'table.tex')), indent=2) + '\n')
        print('CURRENT_CONTROL_TABLE', kind, [(r['dataset'], r['budget'], r['count'], r['expected']) for r in groups])


if __name__ == '__main__': main()
