#!/usr/bin/env python3
"""Offline reference page: online − offline per-view PSNR gap over stream time, training counts, flatness.

  python build_offline_page.py   ->  results/campaigns/gain_attribution/offline_reference/v1/offline_compare.html
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_ervs_scenes_page as S  # noqa: E402

OUT = S.R / 'offline_reference/v1'
SCENES = [('aria', 'aria1253', 'Aria'), ('rpng', 'table_06', 'RPNG'), ('rot', 'aria1253rot', 'Aria'),
          ('utmm', 'square-1', 'UTMM')]
ARMS = ('uniform_iid', 'uniform_k16', 'ervs_k16')
SEEDS = (0, 1, 2)


def smooth_sym(y, frac):
    """Centred moving average whose window shrinks symmetrically at the edges (the first point is itself)."""
    h = max(1, int(round(frac * len(y))) // 2)
    n = len(y)
    return np.array([y[i - min(h, i, n - 1 - i):i + min(h, i, n - 1 - i) + 1].mean() for i in range(n)])


def curve(f, p, sym=False):
    t = (f - f[0]) / (f[-1] - f[0])
    return np.interp(S.GRID, t, smooth_sym(p, 0.10) if sym else S.smooth(p, 0.10))


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


def first_trained(d):
    lr = json.loads((d / 'render_result.json').read_text())['training']['loss_routes']
    g = max(x['generation'] for x in lr)
    return min(x['uid'] for x in lr if x['generation'] == g)


FIRST = {}


def V(d, key):
    """Held-out views from the final map's first trained view on: earlier views have no trained view of the final
    map generation near them (the tracker reset the map), identically in every arm and in offline."""
    f, p = S.views(d)[:2]
    m = f >= FIRST[key]
    return f[m], p[m]


SEL_THR = -0.3   # baseline-only selection: uniform_iid seed-0 gap slope over the first 90%
EXTRA_LOCAL = S.R / 'extra_local_5070ti/v1'   # FAST-LIVO2 etc. run on the RTX 5070 Ti (online + offline, seed 0)
TAU_OUT = S.R / 'ervs_tau_scale/v1'            # ERVS K16 with tau 8 / 16
TAUS = (8, 16)
FASTLIVO = ('Retail_Street', 'HKU_Campus', 'CBD_Building_01', 'SYSU_01', 'CBD_Building_02')


def scene_list():
    out = [dict(key=k, name=n, ds=ds, kind='pinned') for k, n, ds in SCENES]
    out += [dict(key=sc, name=sc, ds={'aria': 'Aria', 'rpng': 'RPNG', 'utmm': 'UTMM'}[ds], kind='extra') for sc, ds in S.NEW]
    out += [dict(key=sc, name=sc, ds='FAST-LIVO2', kind='local') for sc in FASTLIVO]
    return out


def online_dir(sc, arm, seed):
    if arm.startswith('ervs_t'):
        return TAU_OUT / f'scenes/{sc["key"]}/render25/{arm}_s{seed}'
    if sc['kind'] == 'pinned':
        return S.pinned_dir(sc['key'], arm, seed)
    if sc['kind'] == 'extra':
        return S.OUT / f'scenes/{sc["key"]}/render25/{arm}_s{seed}'
    return EXTRA_LOCAL / f'scenes/{sc["key"]}/render25/{arm}_s{seed}'


def offline_dir(sc, seed):
    if sc['kind'] == 'local':
        return EXTRA_LOCAL / f'scenes/{sc["key"]}/render25/offline_s0'
    return OUT / f'offline/{sc["key"]}/render25/offline_s{seed if sc["kind"] == "pinned" else 0}'


def done(d):
    return d is not None and (d.parent / f'{d.name}.row.json').exists()


def main():
    arms = list(ARMS) + [f'ervs_t{t}' for t in TAUS]
    scenes = []
    for sc in scene_list():
        if not done(offline_dir(sc, 0)):
            continue
        key = sc['key']
        FIRST[key] = first_trained(offline_dir(sc, 0))
        n_all = len(S.views(offline_dir(sc, 0))[0])
        rec = dict(key=key, scene=sc['name'], dataset=sc['ds'], excluded=0, runs={}, offline={}, counts={}, lorenz={},
                   gini={})
        f0 = None
        for seed in SEEDS:
            od = offline_dir(sc, seed)
            if not done(od) or (sc['kind'] != 'pinned' and seed and False):
                continue
            fo, po = V(od, key)
            f0 = fo if f0 is None else f0
            rec['offline'][seed] = dict(abs=curve(fo, po).round(3).tolist(), psnr=float(po.mean()), psnr90=float(po[(fo - fo[0]) / (fo[-1] - fo[0]) < .9].mean()))
        rec['excluded'] = int(n_all - len(f0)); rec['n_views'] = int(len(f0))
        for a in arms:
            for seed in SEEDS:
                d = online_dir(sc, a, seed)
                if not done(d):
                    continue
                f, p = V(d, key)
                assert np.array_equal(f, f0), (key, a, seed)
                oseed = seed if seed in rec['offline'] and sc['kind'] == 'pinned' else 0
                fo, po = V(offline_dir(sc, oseed), key)
                g = p - po
                t = (f - f[0]) / (f[-1] - f[0])
                rec['runs'].setdefault(a, {})[seed] = dict(
                    gap=curve(f, g).round(3).tolist(), gap_sym=curve(f, g, True).round(3).tolist(),
                    abs=curve(f, p).round(3).tolist(), bins=[round(x, 3) for x in b5(g)],
                    psnr=float(p.mean()), psnr90=float(p[t < .9].mean()))
            if a not in rec['runs']:
                continue
            dirs = [online_dir(sc, a, s) for s in rec['runs'][a]]
            cc = [counts(d) for d in dirs]
            rec['counts'][a] = {k: [None if not np.isfinite(v) else round(float(v), 3)
                                    for v in np.nanmean([c[k]['mean'] / c[k]['overall'] for c in cc], 0)] for k in ('kf', 'dense')}
            rec['counts'][a]['cv'] = {k: float(np.mean([c[k]['cv'] for c in cc])) for k in ('kf', 'dense')}
            lz = [lorenz(d) for d in dirs]
            rec['lorenz'][a] = np.mean([x[0] for x in lz], 0).round(4).tolist(); rec['gini'][a] = float(np.mean([x[1] for x in lz]))
        od = [offline_dir(sc, s) for s in rec['offline']]
        cc = [counts(d) for d in od]
        rec['counts']['offline'] = {k: [None if not np.isfinite(v) else round(float(v), 3)
                                        for v in np.nanmean([c[k]['mean'] / c[k]['overall'] for c in cc], 0)] for k in ('kf', 'dense')}
        rec['counts']['offline']['cv'] = {k: float(np.mean([c[k]['cv'] for c in cc])) for k in ('kf', 'dense')}
        lz = [lorenz(d) for d in od]
        rec['lorenz']['offline'] = np.mean([x[0] for x in lz], 0).round(4).tolist(); rec['gini']['offline'] = float(np.mean([x[1] for x in lz]))
        if not all(a in rec['runs'] for a in ARMS):
            continue
        scenes.append(rec)
    data = dict(sel_thr=SEL_THR, grid=np.round(S.GRID, 3).tolist(), count_bins=S.NB, scenes=scenes, taus=[4, *TAUS])
    html = (HERE / 'offline_page.html').read_text().replace('__DATA__', json.dumps(data, separators=(',', ':')))
    (OUT / 'offline_compare.html').write_text(html)
    print('scenes', len(scenes), {d: sum(s['dataset'] == d for s in scenes) for d in sorted({s['dataset'] for s in scenes})},
          'tau arms', {a: sum(a in s['runs'] for s in scenes) for a in arms})


if __name__ == '__main__':
    main()
