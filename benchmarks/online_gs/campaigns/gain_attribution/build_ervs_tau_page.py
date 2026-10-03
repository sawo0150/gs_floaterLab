#!/usr/bin/env python3
"""Collect ERVS K16 τ ∈ {4, 1, 0.25} vs uniform with replacement (four B scenes, budget 25, seed 0) and render the page.

τ = 4 and uniform_iid are the seed-0 runs used in ervs_vs_iid_seeds; τ = 1 and 0.25 come from ervs_tau_strength.
Writes tau_page_data.json and ervs_tau.html into results/.../ervs_tau_strength/v1/.
"""
import json
from pathlib import Path
import numpy as np

import build_ervs_scenes_page as S

R = S.R
OUT = R / 'ervs_tau_strength/v1'
ARMS = [('uniform_iid', None), ('ervs_tau4', 4.0), ('ervs_tau1', 1.0), ('ervs_tau0.25', 0.25)]


def run_dir(key, arm):
    if arm == 'uniform_iid':
        return S.pinned_dir(key, 'uniform_iid', 0)
    if arm == 'ervs_tau4':
        return S.pinned_dir(key, 'ervs_k16', 0)
    return OUT / f'tau/{key}/render{S.BUDGET}/{arm}'


def main():
    scenes = []
    for key, scene, ds in S.PINNED:
        runs = {a: run_dir(key, a) for a, _ in ARMS}
        runs = {a: d for a, d in runs.items() if (d / 'psnr/strict_fixed_manifest/final_result.json').exists()}
        if 'uniform_iid' not in runs:
            continue
        rec = dict(scene=scene, dataset=ds, arms=list(runs), curve={}, bins={}, metrics={}, diff={}, count={},
                   cv={}, scale={})
        f0, p0, *_ = S.views(runs['uniform_iid'])
        cnt = {a: S.counts(d) for a, d in runs.items()}
        for k in ('kf', 'dense'):
            rec['scale'][k] = round(float(np.mean([c[k]['overall'] for c in cnt.values()])), 3)
        for a, d in runs.items():
            f, p, ssim, lpips = S.views(d)
            assert (f == f0).all(), (scene, a)
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
    data = dict(grid=np.round(S.GRID, 3).tolist(), count_bins=S.NB, budget=S.BUDGET,
                arms=[dict(id=a, tau=t) for a, t in ARMS], scenes=scenes,
                replay=json.loads((OUT / 'replay_analysis.json').read_text()) if (OUT / 'replay_analysis.json').exists() else None)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'tau_page_data.json').write_text(json.dumps(data))
    tmpl = (S.HERE / 'ervs_tau_page.html').read_text()
    (OUT / 'ervs_tau.html').write_text(tmpl.replace('/*__DATA__*/null', json.dumps(data)))
    print('scenes', len(scenes), {s['scene']: s['arms'] for s in scenes})


if __name__ == '__main__':
    main()
