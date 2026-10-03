#!/usr/bin/env python3
"""CPU-only analysis of the τ-strength runs (four B scenes, budget 25, seed 0; uniform_iid and ERVS τ 4/1/0.25).

A. Replay rate: per training view, services in the final mapper generation ÷ steps since its first service there.
B. Held-out PSNR vs local training: for each held-out frame, total services of training views within ±W% of the
   stream (by frame index). (1) paired across arms: Δlog(local) vs ΔPSNR on the same view; (2) share of per-view
   PSNR variance explained by view identity (mean over arms) vs arm.
Writes results/.../ervs_tau_strength/v1/replay_analysis.json.
"""
import json
from pathlib import Path
import numpy as np

import build_ervs_tau_page as T
import build_ervs_scenes_page as S

W = 0.015        # local window half-width as a fraction of the stream (frames)
NB = 20
ARMS = [a for a, _ in T.ARMS]


def load(d):
    r = json.loads((d / 'render_result.json').read_text())
    lr = r['training']['loss_routes']
    gen = max(x['generation'] for x in lr)
    steps = [x for x in lr if x['generation'] == gen]
    n, first, kind = {}, {}, {}
    for i, x in enumerate(steps):
        u = x['uid']; n[u] = n.get(u, 0) + 1; first.setdefault(u, i)
        kind[u] = 'dense' if x['role'] == 'dense' else 'kf'
    arr = {a['uid']: a['seconds'] for a in r['arrivals']}
    f, p, *_ = S.views(d)
    return dict(n=n, first=first, kind=kind, total=len(steps), arr=arr, hf=f.astype(int), hp=p, nframes=max(arr) + 1)


def main():
    out = dict(window=W, scenes={})
    rate_bins = {a: {k: [] for k in ('kf', 'dense')} for a in ARMS}
    pairs = {a: [] for a in ARMS if a != 'uniform_iid'}
    for key, scene, ds in S.PINNED:
        runs = {a: load(T.run_dir(key, a)) for a in ARMS}
        u0 = runs['uniform_iid']
        t0, t1 = min(u0['arr'].values()), max(u0['arr'].values())
        sc = {}
        # A. replay rate by arrival bin, relative to the uniform arm's mean rate in the same scene/kind
        for k in ('kf', 'dense'):
            ref = None
            for a in ARMS:
                R = runs[a]; res = {}
                for u, c in R['n'].items():
                    life = R['total'] - R['first'][u]
                    if R['kind'][u] == k and life >= 20:
                        res[u] = c / life
                if a == 'uniform_iid':
                    ref = np.mean(list(res.values()))
                b = [[] for _ in range(NB)]
                for u, v in res.items():
                    b[min(NB - 1, int((R['arr'][u] - t0) / (t1 - t0) * NB))].append(v / ref)
                rate_bins[a][k].append([np.mean(x) if x else np.nan for x in b])
        # B. local services around each held-out frame
        w = max(1, int(W * u0['nframes']))
        local = {}
        for a in ARMS:
            R = runs[a]; c = np.zeros(R['nframes'] + 2 * w + 1)
            for u, v in R['n'].items():
                c[u + w] += v
            cs = np.concatenate([[0], np.cumsum(c)])
            local[a] = np.array([cs[f + 2 * w + 1] - cs[f] for f in R['hf']])
            assert (R['hf'] == u0['hf']).all()
        P = np.array([runs[a]['hp'] for a in ARMS])                      # arms × views
        view_mean = P.mean(0)
        between = view_mean.var(); within = P.var(0).mean()
        sc['variance_share_view'] = float(between / (between + within))
        sc['psnr_sd_across_views'] = float(view_mean.std())
        sc['psnr_sd_across_arms'] = float(np.sqrt(within))
        lu = np.log(local['uniform_iid'] + 1)
        sc['corr_psnr_local_within_uniform'] = float(np.corrcoef(lu, u0['hp'])[0, 1])
        for a in pairs:
            dl = np.log(local[a] + 1) - lu; dp = runs[a]['hp'] - u0['hp']
            ok = (local[a] > 0) & (local['uniform_iid'] > 0)
            pairs[a].append((dl[ok], dp[ok]))
            sc[f'paired_{a}'] = dict(r=float(np.corrcoef(dl[ok], dp[ok])[0, 1]),
                                     slope_db_per_doubling=float(np.polyfit(dl[ok], dp[ok], 1)[0] * np.log(2)))
        out['scenes'][scene] = sc
    out['rate_ratio_by_arrival'] = {a: {k: np.round(np.nanmean(rate_bins[a][k], 0), 3).tolist() for k in rate_bins[a]}
                                    for a in ARMS}
    out['pooled_paired'] = {}
    for a, lst in pairs.items():
        dl = np.concatenate([x for x, _ in lst]); dp = np.concatenate([y for _, y in lst])
        q = np.quantile(dl, [0, .2, .4, .6, .8, 1])
        strata = [dict(dlog_mid=float(np.median(dl[(dl >= q[i]) & (dl <= q[i + 1])])),
                       dpsnr=float(dp[(dl >= q[i]) & (dl <= q[i + 1])].mean())) for i in range(5)]
        out['pooled_paired'][a] = dict(n=int(len(dl)), r=float(np.corrcoef(dl, dp)[0, 1]),
                                       slope_db_per_doubling=float(np.polyfit(dl, dp, 1)[0] * np.log(2)), strata=strata)
    (T.OUT / 'replay_analysis.json').write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != 'rate_ratio_by_arrival'}, indent=1))
    for a in ARMS:
        r = out['rate_ratio_by_arrival'][a]['dense']
        print(a, 'dense rate ratio first20', round(np.nanmean(r[:4]), 2), 'mid', round(np.nanmean(r[8:16]), 2), 'last20', round(np.nanmean(r[16:]), 2))
        r = out['rate_ratio_by_arrival'][a]['kf']
        print(a, 'kf    rate ratio first20', round(np.nanmean(r[:4]), 2), 'mid', round(np.nanmean(r[8:16]), 2), 'last20', round(np.nanmean(r[16:]), 2))


if __name__ == '__main__':
    main()
