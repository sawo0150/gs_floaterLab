#!/usr/bin/env python3
"""Compact one-column T6 from actual evaluated checkpoints, without interpolation."""
import csv
import json
from pathlib import Path
import shutil
import sys

PAPER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER / 'scripts'))
from build_measured_tables import CANDIDATES, DISPLAY, RESULTS, read, sha, EMPTY
from build_draft_tables import escape


def curve(run):
    summary = run / 'curve_evaluation/summary.json'
    if not summary.exists(): return []
    endpoint = read(run / 'render_result.json')
    rows = []
    for r in read(summary):
        if r['status'] != 'evaluated' or not r['usable_for_convergence_claim']: continue
        renders = endpoint['render_counts']['training'] if r['checkpoint'].get('final') else r['checkpoint']['training_renders']
        rows.append({'renders': renders, 'psnr': r['quality']['mean_psnr'], 'final':bool(r['checkpoint'].get('final')),
                     'source': str(summary), 'source_sha256': sha(summary)})
    return sorted(rows, key=lambda r: r['renders'])


def main():
    rows, body = [], []
    for dataset, scenes in CANDIDATES.items():
        body += [r'\multicolumn{7}{@{}l}{\textit{' + DISPLAY[dataset] + r'}} \\']
        for scene in scenes:
            panel = RESULTS / ('cvpr_assets/fixed_work_12f_v1' if scene == 'aria301_12F' else 'cvpr_assets/fixed_work_v1')
            base = panel / 'render40' / dataset / scene
            a, b = curve(base / 'vanilla'), curve(base / 'd3')
            r = {'dataset': dataset, 'scene': scene, 'status': 'unmeasured'}
            values = [EMPTY] * 6
            if len(a) >= 2 and len(b) >= 2 and any(x['final'] for x in a) and any(x['final'] for x in b):
                peak = max(x['psnr'] for x in a)
                baseline = next(x for x in a if x['psnr'] >= peak - 1e-10)
                proposed = next((x for x in b if x['psnr'] >= peak), None)
                r.update(status='reached' if proposed else 'NR', baseline_peak=peak,
                         baseline_renders=baseline['renders'], ours_renders=proposed['renders'] if proposed else None,
                         final_baseline_psnr=a[-1]['psnr'], final_ours_psnr=b[-1]['psnr'],
                         baseline_curve=baseline['source'], baseline_curve_sha256=baseline['source_sha256'],
                         ours_curve=b[-1]['source'], ours_curve_sha256=b[-1]['source_sha256'])
                saved = baseline['renders'] - proposed['renders'] if proposed else None
                reduction = 100 * saved / baseline['renders'] if saved is not None and baseline['renders'] > 0 else None
                r.update(saved_renders=saved, reduction_percent=reduction)
                values = [f'{peak:.2f}', str(baseline['renders']), str(proposed['renders']) if proposed else 'NR',
                          str(saved) if saved is not None else 'NR', f'{reduction:.1f}' if reduction is not None else 'NA',
                          r'\shortstack{' + f"{a[-1]['psnr']:.2f}" + r'\\' + f"{b[-1]['psnr']:.2f}" + '}']
            rows.append(r)
            body.append(' & '.join([escape(scene), *values]) + r' \\')
        body.append(r'\midrule')
    body.pop()
    fields = list(dict.fromkeys(k for r in rows for k in r))
    data = PAPER / 'results/tables/cvpr_baseline_peak.csv'
    with data.open('w', newline='') as f:
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(rows)
    count = sum(r['status']!='unmeasured' for r in rows)
    tex = '\n'.join([r'\begin{table}[tbp]', r'\centering',
        r'\caption{Per-sequence cost of reaching the highest observed VIGS-SLAM PSNR on a shared checkpoint schedule at 40 training renders/KF. '
        + f'{count}/{len(rows)} candidate scenes evaluated.' + '}',
        r'\label{tab:baseline_peak}', r'\begingroup', r'\footnotesize',
        r'\setlength{\tabcolsep}{2pt}', r'\renewcommand{\arraystretch}{1.04}',
        r'\resizebox{\linewidth}{!}{%', r'\begin{tabular}{@{}lrrrrrr@{}}', r'\toprule',
        r'Sequence & \shortstack{Peak\\(dB)} & \shortstack{VIGS\\renders} & \shortstack{Ours\\renders} & \shortstack{Saved\\renders} & \shortstack{Saved\\(\%)} & \shortstack{Final PSNR\\VIGS / Ours} \\',
        r'\midrule', *body, r'\bottomrule', r'\end{tabular}}', r'\endgroup',
        r'\par\vspace{3pt}', r'\begin{minipage}{\linewidth}',
        r'\scriptsize\raggedright Dashes mean unmeasured; NR means not reached on the measured grid; NA means undefined. '
        r'Costs count training image renders, with D3 proxy work additional. Peak and final scores use the same fixed uniform subset of up to 64 held-out views, rather than the full cohort in Table~\ref{tab:rendering_comparison}. '
        r'Only measured states with acceptable pose alignment enter the comparison. Costs locate the first sampled crossing, not the exact continuous crossing. No interpolation is used; negative savings are retained.',
        r'\end{minipage}', r'\end{table}', ''])
    current = PAPER / 'tables/table06_baseline_peak/current'
    archive = current.parent / 'output/before_compact_measured_layout_2026-10-01'
    if not archive.exists(): shutil.copytree(current, archive)
    (current / 'table.tex').write_text(tex)
    (current / 'caption.md').write_text(f'실제 checkpoint 평가 {count}/{len(rows)} scenes. 두 방법의 최종 checkpoint가 평가된 scene만 포함한다. Baseline의 최고 관측 PSNR에 처음 도달한 sampled training-render 비용을 보고하고 interpolation은 하지 않는다.\n')
    (PAPER / 'latex/tab/t6_peak_draft.tex').write_text(tex)
    (current / 'provenance.json').write_text(json.dumps({'kind': 'curve_measurement_table',
        'experimental_evidence': any(r['status'] != 'unmeasured' for r in rows), 'rows': rows,
        'data': str(data), 'data_sha256': sha(data), 'manuscript_width': 'one_column'}, indent=2) + '\n')
    print('T6 compact layout; measured scenes',sum(r['status'] != 'unmeasured' for r in rows),'/',len(rows))


if __name__ == '__main__': main()
