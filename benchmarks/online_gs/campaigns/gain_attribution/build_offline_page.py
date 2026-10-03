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


def lorenz(d):
    """Cumulative share of final-generation services over views in arrival order (offline = diagonal)."""
    r = json.loads((d / 'render_result.json').read_text())
    gen = max(x['generation'] for x in r['training']['loss_routes'])
    n = {}
    for x in r['training']['loss_routes']:
        if x['generation'] == gen:
            n[x['uid']] = n.get(x['uid'], 0) + 1
    v = np.array([n[u] for u in sorted(n)], float)
    xs = np.concatenate([[0], np.arange(1, len(v) + 1) / len(v)])
    ys = np.concatenate([[0], np.cumsum(v) / v.sum()])
    y = np.interp(S.GRID, xs, ys)
    return y, float(2 * np.trapezoid(y - S.GRID, S.GRID))


def main():
    pinned = [(k, n, ds, k) for k, n, ds in SCENES]
    extra = [(sc, sc, {'aria': 'Aria', 'rpng': 'RPNG', 'utmm': 'UTMM'}[ds], None) for sc, ds in S.NEW]
    scenes = []
    for key, name, ds, pin in pinned + extra:
        if pin:
            off_dirs = {s: OUT / f'offline/{key}/render25/offline_s{s}' for s in SEEDS}
            on_dir = lambda a, s: S.pinned_dir(key, a, s)
        else:
            off_dirs = {0: OUT / f'offline/{key}/render25/offline_s0'}
            on_dir = lambda a, s: S.OUT / f'scenes/{key}/render25/{a}_s{s}'
        if not all((d / f'../{d.name}.row.json').resolve().exists() for d in off_dirs.values()):
            continue
        off = {s: S.views(d) for s, d in off_dirs.items()}
        on = {(a, s): S.views(on_dir(a, s)) for a in ARMS for s in SEEDS}
        f = off[0][0]
        pair = (lambda s: s) if pin else (lambda s: 0)
        rec = dict(key=key, scene=name, dataset=ds, pinned=bool(pin), offline_seeds=len(off), n_views=int(len(f)),
                   abs={}, gap={}, gap_lo={}, gap_hi={}, bins={}, mean={}, counts={}, lorenz={}, gini={}, mad={})
        rec['abs']['offline'] = np.mean([curve(f, off[s][1]) for s in off], 0).round(3).tolist()
        rec['mean']['offline'] = float(np.mean([off[s][1].mean() for s in off]))
        for a in ARMS:
            assert all(np.array_equal(on[(a, s)][0], f) for s in SEEDS)
            ds_ = [on[(a, s)][1] - off[pair(s)][1] for s in SEEDS]
            cs = np.array([curve(f, d) for d in ds_])
            m = cs.mean(0)
            rec['abs'][a] = np.mean([curve(f, on[(a, s)][1]) for s in SEEDS], 0).round(3).tolist()
            rec['gap'][a] = m.round(3).tolist()
            rec['gap_lo'][a] = cs.min(0).round(3).tolist(); rec['gap_hi'][a] = cs.max(0).round(3).tolist()
            rec['bins'][a] = np.mean([b5(d) for d in ds_], 0).round(3).tolist()
            rec['mean'][a] = float(np.mean([on[(a, s)][1].mean() for s in SEEDS]))
            head = m[:91]
            rec['mad'][a] = float(np.abs(head - head.mean()).mean())
        for a, dirs in [(a, [on_dir(a, s) for s in SEEDS]) for a in ARMS] + [('offline', list(off_dirs.values()))]:
            cc = [counts(d) for d in dirs]
            rec['counts'][a] = {k: [None if not np.isfinite(v) else round(float(v), 3)
                                    for v in np.nanmean([c[k]['mean'] / c[k]['overall'] for c in cc], 0)]
                                for k in ('kf', 'dense')}
            rec['counts'][a]['cv'] = {k: float(np.mean([c[k]['cv'] for c in cc])) for k in ('kf', 'dense')}
            lz = [lorenz(d) for d in dirs]
            rec['lorenz'][a] = np.mean([x[0] for x in lz], 0).round(4).tolist()
            rec['gini'][a] = float(np.mean([x[1] for x in lz]))
        scenes.append(rec)
    pairs = {}
    for metric in ('mad', 'gini'):
        for a, b in (('ervs_k16', 'uniform_iid'), ('ervs_k16', 'uniform_k16'), ('uniform_k16', 'uniform_iid')):
            diff = [s[metric][a] - s[metric][b] for s in scenes]
            pairs[f'{metric}:{a}-{b}'] = dict(ci=boot(diff), wins=int(sum(d < 0 for d in diff)), n=len(diff))
    data = dict(grid=np.round(S.GRID, 3).tolist(), count_bins=S.NB, scenes=scenes, pairs=pairs)
    html = (HERE / 'offline_page.html').read_text().replace('__DATA__', json.dumps(data, separators=(',', ':')))
    (OUT / 'offline_compare.html').write_text(html)
    print('scenes', len(scenes), {k: [round(x, 3) for x in v['ci']] + [v['wins'], v['n']] for k, v in pairs.items()})


if __name__ == '__main__':
    main()
