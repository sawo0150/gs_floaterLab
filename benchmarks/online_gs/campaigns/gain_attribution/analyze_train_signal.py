#!/usr/bin/env python3
"""Stage-1 analysis of per-render training signals (ervs_train_signal v1, four B scenes, budget 25, seed 0).

For each run (uniform_iid_log, ervs_tau4_log) and each training view of the final generation:
  - visit trajectory of training PSNR (measured on the forward pass before that visit's update);
  - revisit change Δ = PSNR at visit k − PSNR at visit k−1 (learning from visit k−1 minus interference since then),
    by revisit gap (steps) and by view age;
  - end-of-run state: count n, last PSNR, best PSNR, forgetting = best − last, staleness (steps since last visit),
    age-normalized maturity m = n / (age × pool rate), learning progress = last − previous.
Held-out link: for each held-out frame, the mean of each state over training views within ±1.5% of the stream;
Spearman ρ with held-out PSNR per scene, and ρ after removing the local best training PSNR (difficulty proxy).
Writes stage1_analysis.json next to the runs and prints a summary.
"""
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
V = ROOT / 'results/campaigns/gain_attribution/ervs_train_signal/v1'
SCENES = [('aria', 'aria1253'), ('rpng', 'table_06'), ('rot', 'aria1253rot'), ('utmm', 'square-1')]
ARMS = ('uniform_iid_log', 'ervs_tau4_log')
W = 0.015
GAP_BINS = [0, 50, 100, 200, 400, 800, 1600, 1e9]
SIGNALS = ('n', 'last', 'best', 'forget', 'stale', 'maturity', 'progress')


def rankdata(x):
    o = np.argsort(x, kind='mergesort'); r = np.empty(len(x)); r[o] = np.arange(len(x)); return r


def spearman(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 5:
        return np.nan
    return float(np.corrcoef(rankdata(a[ok]), rankdata(b[ok]))[0, 1])


def residual(y, x):
    ok = np.isfinite(y) & np.isfinite(x); r = np.full(len(y), np.nan)
    if ok.sum() > 2:
        c = np.polyfit(x[ok], y[ok], 1); r[ok] = y[ok] - np.polyval(c, x[ok])
    return r


def gap_stats(gap, dv, lo, hi):
    m = (gap >= lo) & (gap < hi)
    return dict(lo=lo, hi=hi, n=int(m.sum()), mean_delta=float(dv[m].mean()) if m.any() else None,
                frac_drop=float((dv[m] < 0).mean()) if m.any() else None)


def analyse(d):
    sig = json.loads((d / 'train_signal.json').read_text())
    rows = sig['rows']
    gen = max(r[1] for r in rows)
    rows = [r for r in rows if r[1] == gen]
    s0 = rows[0][0]; end = rows[-1][0] + 1
    visits = {}
    for s, g, u, role, p, l1, loss in rows:
        visits.setdefault(u, dict(kind='dense' if role == 'dense' else 'kf', steps=[], psnr=[]))
        visits[u]['steps'].append(s); visits[u]['psnr'].append(p)
    rate = sum(len(v['steps']) for v in visits.values()) / sum(end - v['steps'][0] for v in visits.values())
    # revisit changes
    deltas = []
    for u, v in visits.items():
        for k in range(1, len(v['steps'])):
            deltas.append((v['kind'], v['steps'][k] - v['steps'][k - 1], v['steps'][k] - v['steps'][0],
                           v['psnr'][k] - v['psnr'][k - 1]))
    state = {}
    for u, v in visits.items():
        ps = v['psnr']
        state[u] = dict(n=len(ps), last=ps[-1], best=max(ps), forget=max(ps) - ps[-1], stale=end - v['steps'][-1],
                        maturity=len(ps) / max(1.0, (end - v['steps'][0]) * rate),
                        progress=(ps[-1] - ps[-2]) if len(ps) > 1 else np.nan, kind=v['kind'])
    final = json.loads((d / 'psnr/strict_fixed_manifest/final_result.json').read_text())
    held = sorted((x for x in final['per_view'] if x.get('predeclared_fixed_manifest_split')), key=lambda x: x['frame_index'])
    hf = np.array([x['frame_index'] for x in held]); hp = np.array([x['psnr'] for x in held])
    span = max(1, int(W * (max(max(state), hf.max()) + 1)))
    uids = np.array(sorted(state))
    local = {k: np.full(len(hf), np.nan) for k in SIGNALS}
    for i, f in enumerate(hf):
        near = uids[np.abs(uids - f) <= span]
        if len(near):
            for k in SIGNALS:
                vals = np.array([state[u][k] for u in near], float)
                if np.isfinite(vals).any():
                    local[k][i] = np.nanmean(vals)
    return dict(deltas=deltas, state=state, hp=hp, hf=hf, local=local, end=end, s0=s0)


def main():
    out = dict(window=W, gap_bins=GAP_BINS, scenes={})
    pooled = {a: [] for a in ARMS}
    for key, scene in SCENES:
        sc = {}
        for arm in ARMS:
            d = V / f'stage1/{key}/render25/{arm}'
            if not (d / 'train_signal.json').exists():
                continue
            A = analyse(d); pooled[arm].extend(A['deltas'])
            corr = {k: spearman(A['local'][k], A['hp']) for k in SIGNALS}
            diff = A['local']['best']
            corr_resid = {k: spearman(residual(A['local'][k], diff), residual(A['hp'], diff)) for k in SIGNALS if k != 'best'}
            st = list(A['state'].values())
            sc[arm] = dict(
                heldout_psnr=float(A['hp'].mean()), spearman_heldout=corr, spearman_heldout_given_best=corr_resid,
                end_forget_mean={k: float(np.mean([s['forget'] for s in st if s['kind'] == k])) for k in ('kf', 'dense')},
                end_stale_mean={k: float(np.mean([s['stale'] for s in st if s['kind'] == k])) for k in ('kf', 'dense')},
                maturity_cv={k: float(np.std([s['maturity'] for s in st if s['kind'] == k]) /
                                      np.mean([s['maturity'] for s in st if s['kind'] == k])) for k in ('kf', 'dense')})
        out['scenes'][scene] = sc
    out['revisit'] = {}
    for arm, D in pooled.items():
        if not D:
            continue
        res = {}
        for kind in ('kf', 'dense'):
            dd = [x for x in D if x[0] == kind]
            gap = np.array([x[1] for x in dd]); dv = np.array([x[3] for x in dd])
            res[kind] = dict(n=len(dd), mean_delta=float(dv.mean()), frac_drop=float((dv < 0).mean()),
                             by_gap=[gap_stats(gap, dv, GAP_BINS[i], GAP_BINS[i + 1]) for i in range(len(GAP_BINS) - 1)])
        out['revisit'][arm] = res
    (V / 'stage1_analysis.json').write_text(json.dumps(out, indent=1))
    for arm, r in out['revisit'].items():
        for kind, x in r.items():
            print(arm, kind, 'n', x['n'], 'meanΔ', round(x['mean_delta'], 3), 'drop%', round(100 * x['frac_drop'], 1),
                  'by gap', [(b['lo'], None if b['mean_delta'] is None else round(b['mean_delta'], 2), b['n']) for b in x['by_gap']])
    for scene, sc in out['scenes'].items():
        for arm, x in sc.items():
            print(scene, arm, 'held', round(x['heldout_psnr'], 3),
                  'ρ', {k: round(v, 2) for k, v in x['spearman_heldout'].items()},
                  '| ρ|best', {k: round(v, 2) for k, v in x['spearman_heldout_given_best'].items()},
                  '| endForget', {k: round(v, 2) for k, v in x['end_forget_mean'].items()},
                  '| maturityCV', {k: round(v, 2) for k, v in x['maturity_cv'].items()})


if __name__ == '__main__':
    main()
