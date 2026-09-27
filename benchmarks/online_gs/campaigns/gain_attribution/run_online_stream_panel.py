#!/usr/bin/env python3
"""Post-run, fixed-cohort comparison of v6 dense/KF online map snapshots."""
import json
from pathlib import Path
import subprocess

import run_online_dense_training as trial


def record(dataset, scene, arm, root, curve):
    marker = root / 'stream_quality_shared_recorded.json'
    if marker.exists():
        return
    points = [{'seconds': p['seconds'], 'psnr': p['mean_heldout_psnr']}
              for p in curve['points']]
    brief = ', '.join(f'{p["seconds"]:.2f}s:{p["psnr"]:.4f}dB' for p in points)
    detail = (f'{dataset}/{scene}/{arm}: {brief}. Fixed held-out cohort '
              f'{curve["view_count"]}; common evaluation coordinates; '
              'post-run rendering only. Alignment residuals remain unaccepted; '
              'no exact first-attainment claim.')
    card = trial.BASE.WORKSPACE / 'context/experiments/campaigns/06_gain_attribution/online_dense_training/README.md'
    with card.open('a') as stream:
        stream.write('\n### v6 saved-state quality curve\n\n' + detail + '\n')
    for name, heading, link in (
        ('context/STATUS.md', '## 최근 흐름 (최신순)\n', 'experiments/campaigns/06_gain_attribution/online_dense_training/README.md'),
        ('context/experiments/INDEX.md', '# Experiment Index\n', 'campaigns/06_gain_attribution/online_dense_training/README.md')):
        path = trial.BASE.WORKSPACE / name
        text = path.read_text()
        if heading not in text:
            raise RuntimeError('Missing ledger heading')
        entry = f'\n- **2026-09-25 (v6 stream quality):** {detail} → [카드]({link})\n'
        path.write_text(text.replace(heading, heading + entry, 1))
    trial.common.write(marker, {'points': points, 'cohort_sha256': curve['cohort_sha256']})


def main():
    rows = []
    for dataset, scene in [('rpng', 'table_06'), ('aria', 'aria1253'), ('utmm', 'square-1')]:
        for arm in ['growth_ervs', 'kf_only']:
            root = trial.ROOT / 'v6_deferred' / dataset / scene / arm / 'seed0'
            command = [str(trial.BASE.PYTHON_ENV / 'bin/python'),
                str(Path(__file__).with_name('evaluate_online_stream.py').resolve()),
                '--run-dir', str(root), '--dataset', dataset, '--scene', scene,
                '--shared-coordinates']
            trial.common.evaluation.panel.v2.gpu_idle()
            print('EVALUATE_STREAM', dataset, scene, arm, flush=True)
            with (root / 'stream_quality_shared.log').open('a') as log:
                subprocess.run(command, env=trial.environment(), stdout=log,
                               stderr=subprocess.STDOUT, check=True)
            curve = trial.common.read(root / 'stream_quality_shared.json')
            record(dataset, scene, arm, root, curve)
            summary = {'dataset': dataset, 'scene': scene, 'arm': arm,
                'points': [{k: p[k] for k in ('seconds', 'mean_heldout_psnr')}
                           for p in curve['points']]}
            rows.append(summary)
            trial.common.write(trial.ROOT / 'v6_deferred/stream_panel_progress.json', rows)
            print(json.dumps(summary), flush=True)
    print('STREAM_PANEL_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
