#!/usr/bin/env python3
"""Build T3 from independent manual free-space diagnostics and RGB metrics."""
import csv
import json
from pathlib import Path
import shutil
import sys

PAPER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER / 'scripts'))
from build_measured_tables import table, fmt, sha, install, OUT, read


def main():
    rows, sources = [], []
    for budget in [15, 40]:
        # Fresh maps from the full candidate panel supersede the pilot maps.
        # Keep the earlier source files intact for provenance.
        source = OUT / f'aria_manual_region{budget}_v2.json'
        result = read(source)
        sources.append({'path': str(source), 'sha256': sha(source), 'provenance': result['provenance']})
        for r in result['runs']:
            row = {'scene': 'aria1253', 'budget': budget, 'arm': r['label'],
                   'gaussians': r['gaussians'], 'psnr': r['heldout_quality']['mean_psnr'],
                   'eroded': r['counts']['eroded_1']['opacity_gt_0_3'],
                   'nominal': r['counts']['nominal']['opacity_gt_0_3'],
                   'dilated': r['counts']['dilated_1']['opacity_gt_0_3'],
                   'opacity_support': r['counts']['nominal']['opacity_support_mass'],
                   'registration_median_m': r['alignment_median_m'],
                   'registration_p90_m': r['alignment_p90_m'],
                   'metric_path': r['metric_path'], 'metric_sha256': r['metric_sha256'],
                   'region_result_path': str(source), 'region_result_sha256': sha(source)}
            assert sha(Path(r['metric_path'])) == r['metric_sha256']
            rows.append(row)
    csv_path = PAPER / 'results/tables/cvpr_manual_region_measurements.csv'
    with csv_path.open('w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    body = []
    for budget in [15, 40]:
        for i, arm in enumerate(['vanilla', 'd3']):
            r = next(r for r in rows if r['budget'] == budget and r['arm'] == arm)
            body.append(' & '.join([str(budget) if i == 0 else '',
                'VIGS-SLAM' if arm == 'vanilla' else r'\textbf{Ours}',
                str(r['nominal']), f"{r['opacity_support']:.1f}",
                fmt(r['psnr'], 'psnr'), fmt(r['gaussians'], 'gaussians')]) + r' \\')
        if budget == 15: body.append(r'\midrule')
    sensitivity = '; '.join(f"{r['budget']}, {'VIGS' if r['arm'] == 'vanilla' else 'ours'}: {r['eroded']}/{r['nominal']}/{r['dilated']}" for r in rows)
    note = (r'$N_{.3}$ counts Gaussian centers with opacity $>0.3$ in the manual empty-space mask. '
            r'$M_\alpha$ sums opacity times region overlap using seven covariance support points. '
            'One-voxel eroded/nominal/dilated counts: ' + sensitivity + '. '
            'Voxel size 7.5 cm; shared trajectory-registration median/p90 error 2.42/3.84 cm. '
            'The reference is evaluation-only. Surface accuracy, completeness and F-score are NA because no independent dense surface reference is available. '
            'This compares complete systems; it does not isolate the D3 loss, which incurs extra proxy renders.')
    tex = table('Independent manual free-space diagnostics on Aria1253 at 15 and 40 training renders/KF. '
                'Held-out RGB quality is reported alongside opacity in the annotated empty space.',
                ['tab:geometry'], 'llcccc', ['Renders/KF', 'Method', r'$N_{.3}\downarrow$', r'$M_\alpha\downarrow$', r'PSNR $\uparrow$', r'\#G (k)'], body, note)
    asset = PAPER / 'tables/table03_geometry/current'
    archive = asset.parent / 'output/blank_before_measurements_2026-10-01'
    if not archive.exists(): shutil.copytree(asset, archive)
    (asset / 'table.tex').write_text(tex)
    (PAPER / 'latex/tab/t3_geometry_draft.tex').write_text(tex)
    (asset / 'caption.md').write_text('Aria1253 수작업 빈 공간 region의 opacity 진단. 15/40 학습 렌더 예산. 원본 map을 수정하지 않으며 GT/ORB pose는 사후 평가에만 사용한다. 표면 정확도·completeness·F-score는 NA. D3 단독 ablation은 아직 아니다.\n')
    (asset / 'provenance.json').write_text(json.dumps({'kind': 'measured_manual_free_space_diagnostics',
        'experimental_evidence': True, 'complete_candidate_cohort': False, 'independent_reference_scenes': ['aria1253'],
        'data': str(csv_path), 'data_sha256': sha(csv_path), 'source_results': sources,
        'manuscript_width': 'one_column', 'geometry_loss_isolated': False}, indent=2) + '\n')
    print('Installed measured T3; four real records, independent manual region, dense surface metrics NA.')


if __name__ == '__main__': main()
