#!/usr/bin/env python3
"""Summarize measurement fit only; no true-pose-error or mapping-quality claim."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics


def summarize(rows):
    fits = [r['correspondence_fit_after_refinement'] for r in rows]
    values = sorted(f['weighted_rms_grid'] for f in fits if f['weighted_rms_grid'] is not None)
    quantiles = {str(q): values[int((len(values)-1)*q)] for q in (.5, .9, .99, 1.)} if values else {}
    return {'calls': len(rows), 'supported_calls': len(values), 'rms_grid_quantiles': quantiles,
            'rms_full_resolution_pixel_quantiles': {q: 8*v for q,v in quantiles.items()},
            'support_fraction_mean': statistics.mean(f['supported_pixel_fraction'] for f in fits) if fits else None,
            'support_fraction_min': min((f['supported_pixel_fraction'] for f in fits), default=None)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', default='v12_pose_fit')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4] / 'results/campaigns/gain_attribution/online_dense_training' / args.tag
    scenes = {}
    for dataset, scene in [('rpng', 'table_06'), ('aria', 'aria1253'), ('utmm', 'square-1')]:
        run = root / dataset / scene / 'growth_ervs/seed0'
        path = run / 'visual_pose.json'
        if not path.exists():
            continue
        audit = json.loads(path.read_text())
        contract = json.loads((run / 'contract.json').read_text())
        assert contract['audit_dense_pose_fit'] and audit['refiner'] == 'QualityAuditedRefiner'
        rows = audit['calls']
        result = {'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'all': summarize(rows),
                  'cold': summarize([r for r in rows if not r['correspondences_reused']]),
                  'warm': summarize([r for r in rows if r['correspondences_reused']]),
                  'preparation_seconds': audit['wall_seconds'], 'pose_cache_hits': audit['cache_hits']}
        (run / 'pose_fit_summary.json').write_text(json.dumps(result, indent=2) + '\n')
        scenes[dataset] = result
    report = {'scenes': scenes, 'complete_three_scene_measurements': len(scenes) == 3,
              'quantile_method': 'sorted observed value at floor((n-1)*q)',
              'interpretation': 'Fit to current depth anchors and learned image correspondences; not true pose error. Repeated warm calls are not independent views.',
              'mapping_quality_claim': False}
    (root / 'pose_fit_summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({d: s['all'] for d,s in scenes.items()}, indent=2))


if __name__ == '__main__':
    main()
