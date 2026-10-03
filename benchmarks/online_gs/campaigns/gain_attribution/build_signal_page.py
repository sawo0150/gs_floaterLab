#!/usr/bin/env python3
"""Build the training-signal artifact page (ervs_train_signal v1): stage-1 diagnostics + stage-2 sampler comparison.

Per scene and arm: PSNR curves, five-bin means, paired Δ vs uniform, service counts by arrival time, CV (same
quantities as the τ page). Arms appear as soon as their runs exist. Writes signal_page_data.json and signal.html.
"""
import json
import subprocess
import sys
from pathlib import Path
import numpy as np

import build_ervs_scenes_page as S

R = S.R
OUT = R / 'ervs_train_signal/v1'
ARMS = [
    dict(id='uniform_iid', label='균등 복원', color='--iid', dash='6 4', dir='stage1/{k}/render25/uniform_iid_log',
         desc='모든 view 같은 확률, 매번 독립 추출 (기준)'),
    dict(id='ervs_tau4', label='ERVS τ=4', color='--t4', dir='stage1/{k}/render25/ervs_tau4_log',
         desc='학습 횟수 n이 많을수록 낮게: exp(−(n−n_min)/(4×평균 n))'),
    dict(id='sig_forget_stale', label='망각량+staleness', color='--c1', dir='stage2/{k}/render25/sig_forget_stale',
         desc='망각량(최고 − 마지막 training PSNR) 순위 0.7 + 마지막 학습 후 경과 step 0.3'),
    dict(id='sig_progress_stale', label='진척도+staleness', color='--c2', dir='stage2/{k}/render25/sig_progress_stale',
         desc='학습 진척도(마지막 − 직전 training PSNR) 순위 0.7 + staleness 0.3'),
    dict(id='sig_loss_stale', label='loss+staleness', color='--c3', dir='stage2/{k}/render25/sig_loss_stale',
         desc='마지막 training loss 순위(큰 것 먼저) 0.7 + staleness 0.3'),
    dict(id='sig_catchup', label='catch-up', color='--c4', dir='stage2/{k}/render25/sig_catchup',
         desc='30·0.7ⁿ + 1: 몇 번 학습될 때까지만 강하게 우선, 이후 균등'),
    dict(id='sig_age_norm', label='나이 정규화 성숙도', color='--c5', dir='stage2/{k}/render25/sig_age_norm',
         desc='m = n ÷ (첫 학습 후 step × pool 평균 비율), exp(−(m−1))'),
]
OLD = {'uniform_iid': lambda k: S.pinned_dir(k, 'uniform_iid', 0), 'ervs_tau4': lambda k: S.pinned_dir(k, 'ervs_k16', 0)}


def done(d):
    return (d / 'psnr/strict_fixed_manifest/final_result.json').exists() and any(d.parent.glob(d.name + '.row.json'))


def main():
    sys.path.insert(0, str(S.HERE))
    import analyze_train_signal as A
    if any((OUT / f'stage1/{k}/render25/{a}').exists() for k, *_ in S.PINNED for a in ('uniform_iid_log', 'ervs_tau4_log')):
        A.main()
    stage1 = json.loads((OUT / 'stage1_analysis.json').read_text()) if (OUT / 'stage1_analysis.json').exists() else None
    if stage1 is not None:
        ren = {'uniform_iid_log': 'uniform_iid', 'ervs_tau4_log': 'ervs_tau4'}
        stage1['revisit'] = {ren.get(k, k): v for k, v in stage1['revisit'].items()}
        stage1['scenes'] = {sc: {ren.get(k, k): v for k, v in x.items()} for sc, x in stage1['scenes'].items()}
    repro = []
    scenes = []
    for key, scene, ds in S.PINNED:
        dirs = {a['id']: OUT / a['dir'].format(k=key) for a in ARMS}
        dirs = {a: d for a, d in dirs.items() if done(d)}
        for a in ('uniform_iid', 'ervs_tau4'):
            if a in dirs:
                before = S.views(OLD[a](key))[1].mean(); after = S.views(dirs[a])[1].mean()
                repro.append(dict(scene=scene, arm=a, before=float(before), after=float(after)))
        if 'uniform_iid' not in dirs:
            continue
        rec = dict(scene=scene, dataset=ds, arms=list(dirs), curve={}, bins={}, metrics={}, diff={}, count={},
                   cv={}, scale={})
        f0, p0, *_ = S.views(dirs['uniform_iid'])
        cnt = {a: S.counts(d) for a, d in dirs.items()}
        for k in ('kf', 'dense'):
            rec['scale'][k] = round(float(np.mean([c[k]['overall'] for c in cnt.values()])), 3)
        for a, d in dirs.items():
            f, p, ssim, lpips = S.views(d)
            t = (f - f[0]) / (f[-1] - f[0])
            rec['curve'][a] = np.round(np.interp(S.GRID, t, S.smooth(p, 0.10)), 3).tolist()
            rec['bins'][a] = np.round(S.bins5(p), 3).tolist()
            q = max(1, -(-len(p) // 4))
            rec['metrics'][a] = dict(psnr=float(p.mean()), minbin=min(S.bins5(p)), wq1=float(np.sort(p)[:q].mean()),
                                     ssim=ssim, lpips=lpips)
            rec['diff'][a] = np.round(np.interp(S.GRID, t, S.smooth(p - p0, 0.20)), 3).tolist()
            rec['count'][a] = {k: [None if np.isnan(v) else round(float(v), 3) for v in cnt[a][k]['mean']]
                               for k in ('kf', 'dense')}
            rec['cv'][a] = {k: round(cnt[a][k]['cv'], 4) for k in ('kf', 'dense')}
        scenes.append(rec)
    n1 = sum(done(OUT / a['dir'].format(k=k)) for k, *_ in S.PINNED for a in ARMS[:2])
    n2 = sum(done(OUT / a['dir'].format(k=k)) for k, *_ in S.PINNED for a in ARMS[2:])
    if stage1 is not None:
        stage1['repro'] = repro
    data = dict(grid=np.round(S.GRID, 3).tolist(), count_bins=S.NB, budget=S.BUDGET,
                arms=[{k: v for k, v in a.items() if k != 'dir'} for a in ARMS], scenes=scenes, stage1=stage1,
                progress=f'1단계 {n1} / 8 run · 2단계 {n2} / 20 run 반영' + (' (완료)' if n1 == 8 and n2 == 20 else ' (진행 중)'))
    (OUT / 'signal_page_data.json').write_text(json.dumps(data))
    tmpl = (S.HERE / 'ervs_signal_page.html').read_text()
    (OUT / 'signal.html').write_text(tmpl.replace('/*__DATA__*/null', json.dumps(data)))
    print(data['progress'], {s['scene']: s['arms'] for s in scenes})


if __name__ == '__main__':
    main()
