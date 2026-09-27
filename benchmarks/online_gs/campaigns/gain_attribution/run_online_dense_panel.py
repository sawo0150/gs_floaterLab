#!/usr/bin/env python3
"""Continue the preregistered seed-0 transfer and record every completed arm."""
import json
from pathlib import Path
import subprocess
import sys

import run_online_dense_training as trial


def record(dataset, scene, arm, result=None, failure=None):
    key = f'v4_k64/{dataset}/{scene}/{arm}/seed0'
    root = trial.ROOT / key
    marker = root / 'panel_recorded.json'
    if marker.exists():
        return
    if result is not None:
        detail = (f'held-out {result["heldout_psnr"]:.6f}dB, '
                  f'{result["mapping_seconds"]:.3f}/{result["budget_seconds"]:.3f}초, '
                  f'{result["optimizer_steps"]} Adam/{result["render_count"]} renders, '
                  f'실행 계약 {"PASS" if result["valid"] else "FAIL"}.')
    else:
        detail = f'실행 실패: {failure}. 기존 산출물과 로그 보존; 품질 성공으로 해석하지 않음.'
    message = f'**2026-09-25 (online dense goal / {dataset} {scene} {arm}):** {detail} 공통 κ64 seed0 전이 실험, 전체 목표 판정은 대조군·3seed·수렴곡선 확인 후.'
    card = trial.BASE.WORKSPACE / 'context/experiments/campaigns/06_gain_attribution/online_dense_training/README.md'
    with card.open('a') as f:
        f.write(f'\n### Panel {key}\n\n{detail}\nArtifact: `online_dense_training/{key}/`.\n')
    status = trial.BASE.WORKSPACE / 'context/STATUS.md'
    text = status.read_text(); heading = '## 최근 흐름 (최신순)\n'
    if heading not in text:
        raise RuntimeError('Missing STATUS insertion heading')
    status.write_text(text.replace(heading, heading + '\n- ' + message +
        ' → [카드](experiments/campaigns/06_gain_attribution/online_dense_training/README.md)\n', 1))
    index = trial.BASE.WORKSPACE / 'context/experiments/INDEX.md'
    text = index.read_text(); heading = '# Experiment Index\n'
    if heading not in text:
        raise RuntimeError('Missing INDEX insertion heading')
    index.write_text(text.replace(heading, heading + '\n- ' + message +
        ' [카드](campaigns/06_gain_attribution/online_dense_training/README.md)\n', 1))
    trial.common.write(marker, {'key': key, 'result': result, 'failure': failure})


def main():
    records = []
    for dataset, scene in [('rpng', 'table_06'), ('utmm', 'square-1')]:
        for arm in ['production', 'kf_only', 'growth_ervs']:
            print('START', dataset, scene, arm, flush=True)
            cmd = [sys.executable, str(Path(trial.__file__).resolve()), '--dataset', dataset,
                   '--scene', scene, '--arm', arm, '--tag', 'v4_k64', '--kappa', '64']
            completed = subprocess.run(cmd)
            root = trial.ROOT / 'v4_k64' / dataset / scene / arm / 'seed0'
            if completed.returncode:
                record(dataset, scene, arm, failure=f'worker/validation exit {completed.returncode}')
                records.append({'dataset': dataset, 'scene': scene, 'arm': arm, 'failed': True})
            else:
                result = trial.common.read(root / 'result.json')
                record(dataset, scene, arm, result=result)
                records.append({'dataset': dataset, 'scene': scene, 'arm': arm, **result})
            trial.common.write(trial.ROOT / 'v4_k64/panel_progress.json', records)
    print('PANEL_COMPLETE', json.dumps(records), flush=True)


if __name__ == '__main__':
    main()
