#!/usr/bin/env python3
"""Paired online cost ablation after fixing depth-aware pose cache validity."""
import json
import subprocess
import sys
from pathlib import Path
import run_online_dense_training as trial


def record(tag, dataset, scene, result, returncode):
    key = f'{tag}/{dataset}/{scene}/growth_ervs/seed0'
    root = trial.ROOT / key
    marker = root / 'panel_recorded.json'
    if marker.exists():
        return
    if result is None:
        detail = f'실행/평가 실패(exit {returncode}); 로그 보존, 품질 미판정.'
    else:
        detail = (f'held-out {result["heldout_psnr"]:.6f}dB, '
            f'{result["mapping_seconds"]:.3f}/{result["budget_seconds"]:.3f}초, '
            f'{result["optimizer_steps"]} Adam; 전체시간 포함 계약 '
            f'{"PASS" if result["valid"] else "FAIL"}.')
    card = trial.BASE.WORKSPACE / 'context/experiments/campaigns/06_gain_attribution/online_dense_training/README.md'
    with card.open('a') as f:
        f.write(f'\n### Pose preparation panel {key}\n\n{detail}\nArtifact: `online_dense_training/{key}/`.\n')
    message = f'**2026-09-25 (online pose 준비 / {tag} {dataset} {scene}):** {detail} seed0 진단이며 최종 목표 판정은 미완.'
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
    records = []
    for dataset, scene in [('rpng', 'table_06'), ('aria', 'aria1253'), ('utmm', 'square-1')]:
        for tag, lazy in [('v5_depth', False), ('v5_depth_lazy', True)]:
            cmd = [sys.executable, str(Path(trial.__file__).resolve()), '--dataset', dataset,
                   '--scene', scene, '--arm', 'growth_ervs', '--tag', tag, '--kappa', '64']
            if lazy:
                cmd.append('--lazy-dense-refresh')
            print('START', tag, dataset, scene, flush=True)
            completed = subprocess.run(cmd)
            root = trial.ROOT / tag / dataset / scene / 'growth_ervs/seed0'
            path = root / 'result.json'
            result = trial.common.read(path) if path.exists() else None
            record(tag, dataset, scene, result, completed.returncode)
            records.append({'tag': tag, 'dataset': dataset, 'scene': scene,
                            'returncode': completed.returncode, 'result': result})
            trial.common.write(trial.ROOT / 'v5_pose_panel_progress.json', records)
    print('PANEL_COMPLETE', json.dumps(records), flush=True)


if __name__ == '__main__':
    main()
