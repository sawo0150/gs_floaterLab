#!/usr/bin/env python3
"""Offline reference page: online − offline per-view PSNR gap over stream time, training counts, flatness.

  python build_offline_page.py   ->  results/campaigns/gain_attribution/offline_reference/v1/offline_compare.html
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_ervs_scenes_page as S  # noqa: E402

OUT = S.R / 'offline_reference/v1'
SCENES = [('aria', 'aria1253', 'Aria'), ('rpng', 'table_06', 'RPNG'), ('rot', 'aria1253rot', 'Aria'),
          ('utmm', 'square-1', 'UTMM')]
ARMS = ('uniform_iid', 'uniform_k16', 'ervs_k16')
SEEDS = (0, 1, 2)


def curve(f, p):
    t = (f - f[0]) / (f[-1] - f[0])
    return np.interp(S.GRID, t, S.smooth(p, 0.10))


def b5(d):
    n = len(d); return [float(d[i * n // 5:(i + 1) * n // 5].mean()) for i in range(5)]


def dec(d):
    n = len(d); return np.array([d[i * n // 10:(i + 1) * n // 10].mean() for i in range(10)])


def boot(x, n=5000):
    rng = np.random.default_rng(0); x = np.asarray(x)
    m = [rng.choice(x, len(x)).mean() for _ in range(n)]
    return [float(x.mean()), *map(float, np.percentile(m, [2.5, 97.5]))]


def counts(d):
    """Final-generation services per view by stream position (frame order, so offline's post-stream training time
    does not stretch the axis)."""
    r = json.loads((d / 'render_result.json').read_text())
    uids = [a['uid'] for a in r['arrivals']]
    u0, u1 = min(uids), max(uids)
    gen = max(x['generation'] for x in r['training']['loss_routes'])
    n, kind = {}, {}
    for x in r['training']['loss_routes']:
        if x['generation'] != gen:
            continue
        n[x['uid']] = n.get(x['uid'], 0) + 1
        kind[x['uid']] = 'dense' if x['role'] == 'dense' else 'kf'
    out = {}
    for k in ('kf', 'dense'):
        vals = [n[u] for u in n if kind[u] == k]
        sums, cnt = np.zeros(S.NB), np.zeros(S.NB)
        for u, c in n.items():
            if kind[u] != k:
                continue
            b = min(S.NB - 1, int((u - u0) / (u1 - u0) * S.NB))
            sums[b] += c; cnt[b] += 1
        out[k] = dict(mean=np.where(cnt > 0, sums / np.maximum(cnt, 1), np.nan), overall=float(np.mean(vals)),
                      cv=float(np.std(vals) / np.mean(vals)))
    return out


def main():
    scenes, flat = [], {a: [] for a in ARMS}
    for key, name, ds in SCENES:
        off = {s: S.views(OUT / f'offline/{key}/render25/offline_s{s}') for s in SEEDS}
        on = {(a, s): S.views(S.pinned_dir(key, a, s)) for a in ARMS for s in SEEDS}
        f = off[0][0]
        rec = dict(key=key, scene=name, dataset=ds, n_views=int(len(f)), abs={}, gap={}, gap_lo={}, gap_hi={},
                   bins={}, mean={}, counts={}, seed_gap={})
        rec['abs']['offline'] = np.mean([curve(f, off[s][1]) for s in SEEDS], 0).round(3).tolist()
        rec['mean']['offline'] = float(np.mean([off[s][1].mean() for s in SEEDS]))
        for a in ARMS:
            assert all(np.array_equal(on[(a, s)][0], f) for s in SEEDS)
            ds_ = [on[(a, s)][1] - off[s][1] for s in SEEDS]
            cs = np.array([curve(f, d) for d in ds_])
            rec['abs'][a] = np.mean([curve(f, on[(a, s)][1]) for s in SEEDS], 0).round(3).tolist()
            rec['gap'][a] = cs.mean(0).round(3).tolist()
            rec['gap_lo'][a] = cs.min(0).round(3).tolist(); rec['gap_hi'][a] = cs.max(0).round(3).tolist()
            rec['bins'][a] = np.mean([b5(d) for d in ds_], 0).round(3).tolist()
            rec['mean'][a] = float(np.mean([on[(a, s)][1].mean() for s in SEEDS]))
            rec['seed_gap'][a] = [float(d.mean()) for d in ds_]
            for s, d in zip(SEEDS, ds_):
                flat[a].append(dict(scene=name, seed=s, sd=float(dec(d)[:9].std())))
        for a, dirs in [(a, [S.pinned_dir(key, a, s) for s in SEEDS]) for a in ARMS] + \
                       [('offline', [OUT / f'offline/{key}/render25/offline_s{s}' for s in SEEDS])]:
            cc = [counts(d) for d in dirs]
            rec['counts'][a] = {k: [None if not np.isfinite(v) else round(float(v), 3) for v in np.nanmean([c[k]['mean'] / c[k]['overall'] for c in cc], 0)]
                                for k in ('kf', 'dense')}
            rec['counts'][a]['cv'] = {k: float(np.mean([c[k]['cv'] for c in cc])) for k in ('kf', 'dense')}
        scenes.append(rec)
    pairs = {}
    for a, b in (('ervs_k16', 'uniform_iid'), ('ervs_k16', 'uniform_k16'), ('uniform_k16', 'uniform_iid')):
        diff = [x['sd'] - y['sd'] for x, y in zip(flat[a], flat[b])]
        pairs[f'{a}-{b}'] = dict(ci=boot(diff), wins=int(sum(d < 0 for d in diff)), n=len(diff))
    data = dict(grid=np.round(S.GRID, 3).tolist(), count_bins=S.NB, scenes=scenes, flat=flat, pairs=pairs,
                flat_mean={a: float(np.mean([x['sd'] for x in flat[a]])) for a in ARMS})
    html = (HERE / 'offline_page.html').read_text().replace('__DATA__', json.dumps(data, separators=(',', ':')))
    (OUT / 'offline_compare.html').write_text(html)
    print('scenes', len(scenes), 'flat', data['flat_mean'], {k: v['ci'] for k, v in pairs.items()})


if __name__ == '__main__':
    main()
