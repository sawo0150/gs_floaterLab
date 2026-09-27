#!/usr/bin/env python3
"""Fresh three-scene controls and deferred-input candidate with stream snapshots."""
import subprocess
import hashlib
import sys
from pathlib import Path
import run_online_dense_training as trial


def record(dataset, scene, arm, result, returncode):
    key = f'v6_deferred/{dataset}/{scene}/{arm}/seed0'
    root = trial.ROOT / key
    marker = root / 'panel_recorded.json'
    if marker.exists():
        return
    detail = f'실행/평가 실패(exit {returncode}), 로그 보존.' if result is None else (
        f'held-out {result["heldout_psnr"]:.6f}dB, '
        f'{result["mapping_seconds"]:.3f}/{result["budget_seconds"]:.3f}초, '
        f'{result["optimizer_steps"]} Adam; 전체시간 계약 {"PASS" if result["valid"] else "FAIL"}.')
    card = trial.BASE.WORKSPACE / 'context/experiments/campaigns/06_gain_attribution/online_dense_training/README.md'
    with card.open('a') as f:
        f.write(f'\n### Deferred panel {key}\n\n{detail}\nArtifact: `online_dense_training/{key}/`.\n')
    message = f'**2026-09-25 (online deferred / {dataset} {scene} {arm}):** {detail} 공통100ms여유·중간지도계측 seed0이며 전체목표미완.'
    for name, heading, link in (
        ('context/STATUS.md', '## 최근 흐름 (최신순)\n', 'experiments/campaigns/06_gain_attribution/online_dense_training/README.md'),
        ('context/experiments/INDEX.md', '# Experiment Index\n', 'campaigns/06_gain_attribution/online_dense_training/README.md')):
        p = trial.BASE.WORKSPACE / name
        text = p.read_text()
        if heading not in text:
            raise RuntimeError('Missing ledger heading')
        p.write_text(text.replace(heading, heading + '\n- ' + message + f' → [카드]({link})\n', 1))
    trial.common.write(marker, {'key': key, 'result': result, 'returncode': returncode})


def main():
    rows = []
    for dataset, scene in [('rpng', 'table_06'), ('aria', 'aria1253'), ('utmm', 'square-1')]:
        for arm in ('growth_ervs', 'kf_only', 'production'):
            root = trial.ROOT / 'v6_deferred' / dataset / scene / arm / 'seed0'
            if (root / 'result.json').exists():
                for name, expected in trial.common.read(root / 'source_lock.json').items():
                    if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
                        raise RuntimeError('Source changed; existing trial cannot be reused: ' + name)
                contract = trial.common.read(root / 'contract.json')
                if (contract['deadline_reserve_ms'] != 100 or not contract['snapshots']
                        or contract['defer_dense_preparation'] != (arm == 'growth_ervs')):
                    raise RuntimeError('Existing trial has a different execution contract')
                result = trial.common.read(root / 'result.json')
                returncode = 0 if result['valid'] else 1
            else:
                cmd = [sys.executable, str(Path(trial.__file__).resolve()), '--dataset', dataset,
                    '--scene', scene, '--arm', arm, '--tag', 'v6_deferred', '--kappa', '64',
                    '--snapshots', '--deadline-reserve-ms', '100']
                if arm == 'growth_ervs':
                    cmd += ['--lazy-dense-refresh', '--defer-dense-preparation']
                print('START', dataset, scene, arm, flush=True)
                returncode = subprocess.run(cmd).returncode
                result = trial.common.read(root / 'result.json') if (root / 'result.json').exists() else None
            record(dataset, scene, arm, result, returncode)
            rows.append({'dataset': dataset, 'scene': scene, 'arm': arm,
                         'returncode': returncode, 'result': result})
            trial.common.write(trial.ROOT / 'v6_deferred/panel_progress.json', rows)
    print('PANEL_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
