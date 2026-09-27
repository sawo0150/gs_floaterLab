#!/usr/bin/env python3
"""Complete the membership/sampling ablation for the fixed v15 implementation.

Compare immediate+RR and growth+RR against v15 growth+ERVS and KF-only.
The candidate, geometry, pose preparation, clocks and input cohort stay fixed.
"""
import hashlib
from pathlib import Path
import subprocess
import sys
import run_online_dense_training as trial

TAG = 'v15_growth_sampling'


def record(dataset, scene, arm, run, result, returncode):
    marker = run / 'panel_recorded.json'
    if marker.exists():
        return
    detail = (f'실행/평가 실패(exit {returncode}); 로그 보존.' if result is None else
              f'held-out {result["heldout_psnr"]:.6f}dB, '
              f'{result["mapping_seconds"]:.3f}/{result["budget_seconds"]:.3f}초, '
              f'전체시간 계약 {"PASS" if result["valid"] else "FAIL"}.')
    key = f'{TAG}/{dataset}/{scene}/{arm}/seed0'
    card = trial.BASE.WORKSPACE / 'context/experiments/campaigns/06_gain_attribution/online_dense_training/README.md'
    with card.open('a') as stream:
        stream.write(f'\n### Growth/sampling ablation {key}\n\n{detail}\nArtifact: `online_dense_training/{key}/`.\n')
    for name, heading, link in (
        ('context/STATUS.md', '## 최근 흐름 (최신순)\n', 'experiments/campaigns/06_gain_attribution/online_dense_training/README.md'),
        ('context/experiments/INDEX.md', '# Experiment Index\n', 'campaigns/06_gain_attribution/online_dense_training/README.md')):
        path = trial.BASE.WORKSPACE / name
        text = path.read_text()
        if heading not in text:
            raise RuntimeError('Missing ledger heading')
        entry = (f'\n- **2026-09-25 (v15 Growth/sampling / {dataset} {scene} {arm}):** '
                 f'{detail} 동일 v15 소스·seed0 기여분리; 목표미완. → [카드]({link})\n')
        path.write_text(text.replace(heading, heading + entry, 1))
    trial.common.write(marker, {'key': key, 'result': result, 'returncode': returncode})


def main():
    # Do not silently compare this ablation against another implementation.
    frozen = trial.common.read(trial.ROOT / 'source_v15/index.json')
    for current, archived in frozen.items():
        if Path(current).read_bytes() != (trial.BASE.WORKSPACE / archived).read_bytes():
            raise RuntimeError('v15 implementation changed: ' + current)
    for dataset, scene in trial.SCENES:
        for arm in ('growth_ervs', 'kf_only', 'production'):
            source = trial.ROOT / 'v15_image_residency' / dataset / scene / arm / 'seed0/result.json'
            if not source.exists() or not trial.common.read(source)['valid']:
                raise RuntimeError('Complete valid v15 controls before ablation: ' + str(source))
    rows = []
    for dataset, scene in [('rpng', 'table_06'), ('aria', 'aria1253'), ('utmm', 'square-1')]:
        for arm in ('growth_rr', 'immediate_rr'):
            run = trial.ROOT / TAG / dataset / scene / arm / 'seed0'
            if (run / 'result.json').exists():
                contract = trial.common.read(run / 'contract.json')
                expected_contract = dict(arm=arm, dataset=dataset, scene=scene, seed=0,
                    kappa=64, tau=1.0, entropy_weight_policy='per_view',
                    selection_count_scope='photometric', snapshots=True,
                    deadline_reserve_ms=100, include_mapper_setup_in_clock=True,
                    lazy_dense_refresh=True, defer_dense_preparation=True,
                    reuse_dense_correspondences=True, audit_dense_pose_fit=True)
                if any(contract.get(k) != v for k, v in expected_contract.items()):
                    raise RuntimeError('Existing ablation has a different contract')
                for name, expected in trial.common.read(run / 'source_lock.json').items():
                    if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
                        raise RuntimeError('Source changed after existing ablation: ' + name)
                result = trial.common.read(run / 'result.json')
                returncode = 0 if result['valid'] else 1
            else:
                cmd = [sys.executable, str(Path(trial.__file__).resolve()),
                       '--dataset', dataset, '--scene', scene, '--arm', arm, '--tag', TAG,
                       '--seed', '0', '--kappa', '64', '--tau', '1.0',
                       '--entropy-weight-policy', 'per_view', '--selection-count-scope', 'photometric',
                       '--snapshots', '--deadline-reserve-ms', '100', '--include-mapper-setup-in-clock',
                       '--lazy-dense-refresh', '--defer-dense-preparation',
                       '--reuse-dense-correspondences', '--audit-dense-pose-fit']
                print('START', dataset, scene, arm, flush=True)
                returncode = subprocess.run(cmd).returncode
                result = trial.common.read(run / 'result.json') if (run / 'result.json').exists() else None
            record(dataset, scene, arm, run, result, returncode)
            rows.append({'dataset': dataset, 'scene': scene, 'arm': arm,
                         'returncode': returncode, 'result': result})
            trial.common.write(trial.ROOT / TAG / 'panel_progress.json', rows)
    print('ABLATION_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
