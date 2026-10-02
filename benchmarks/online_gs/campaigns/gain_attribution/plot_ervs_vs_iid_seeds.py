#!/usr/bin/env python3
"""ERVS K16 vs uniform with replacement over 3 seeds × 4 scenes × 2 budgets (ervs_vs_iid_seeds v1).

Fig 1: absolute held-out PSNR along stream time (moving average 10% of views), seed-mean per cell and the 8-cell mean.
Fig 2: paired per-view difference ERVS − iid (same held-out views), moving average 20% of views; per-cell seed-mean
curves and the 8-cell mean with a ±1 s.e. band over cells; five-bin means with per-cell points.
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[4]
R = ROOT / 'results/campaigns/gain_attribution'
OUT = R / 'ervs_vs_iid_seeds/v1'
SCENES = [('aria', 'aria1253'), ('rpng', 'table_06'), ('rot', 'aria1253rot'), ('utmm', 'square-1')]
BUDGETS, SEEDS = (15, 25), (0, 1, 2)
GRID = np.linspace(0, 1, 201)
ARMS = [('ervs_k16', 'ERVS K16', '#2a6fdb', '-'), ('uniform_iid', 'Uniform w/ replacement (K=1)', '#2e9e6b', '--')]


def run_dir(key, budget, arm, seed):
    if seed:
        return OUT / f'seeds/{key}/render{budget}/{arm}_s{seed}'
    if arm == 'ervs_k16':
        return (R / f'ervs_vs_uniform_k16/v1/cmp/{key}/render{budget}/ervs_k16' if key in ('aria', 'rpng')
                else R / f'ervs_group_k/v1/groupk/{key}/render{budget}/K16')
    if key in ('aria', 'rpng'):
        return R / f'ervs_vs_uniform_k16/v1/cmp/{key}/render{budget}/uniform_iid'
    if key == 'rot':
        return R / f'ervs_vs_uniform/v1/uniform/rot/render{budget}/uniform_iid'
    return OUT / f'seeds/{key}/render{budget}/uniform_iid_s0'


def views(d):
    pv = [x for x in json.loads((d / 'psnr/strict_fixed_manifest/final_result.json').read_text())['per_view']
          if x.get('predeclared_fixed_manifest_split')]
    pv.sort(key=lambda x: x['frame_index'])
    f = np.array([x['frame_index'] for x in pv], float)
    return (f - f[0]) / (f[-1] - f[0]), np.array([x['psnr'] for x in pv]), f


def smooth(y, frac):
    k = np.ones(max(3, int(round(frac * len(y)))))
    return np.convolve(y, k, 'same') / np.convolve(np.ones_like(y), k, 'same')


def bins5(y):
    return [y[i * len(y) // 5:(i + 1) * len(y) // 5].mean() for i in range(5)]


data, missing = {}, []
for key, scene in SCENES:
    for b in BUDGETS:
        for arm, *_ in ARMS:
            for s in SEEDS:
                d = run_dir(key, b, arm, s)
                if (d / 'psnr/strict_fixed_manifest/final_result.json').exists():
                    data[(scene, b, arm, s)] = views(d)
                else:
                    missing.append(str(d))
print('runs', len(data), 'missing', len(missing))

cells = [(sc, b) for _, sc in SCENES for b in BUDGETS]
fig, axes = plt.subplots(3, 3, figsize=(17, 12))
abs_mean = {a: [] for a, *_ in ARMS}
for ax, (sc, b) in zip(axes.flat[:8], cells):
    for arm, label, color, ls in ARMS:
        cs = [np.interp(GRID, t, smooth(p, 0.10)) for s in SEEDS if (k := (sc, b, arm, s)) in data
              for t, p, _ in [data[k]]]
        if not cs: continue
        m = np.mean(cs, axis=0); abs_mean[arm].append(m)
        means = [data[(sc, b, arm, s)][1].mean() for s in SEEDS if (sc, b, arm, s) in data]
        ax.plot(GRID, m, color=color, ls=ls, lw=2, label=f'{label}: {np.mean(means):.2f} (n={len(cs)})')
    ax.set_title(f'{sc} · {b} renders/KF', fontsize=10); ax.legend(fontsize=7.5, frameon=False, loc='lower left')
ax = axes.flat[8]
for arm, label, color, ls in ARMS:
    if abs_mean[arm]:
        m = np.mean(abs_mean[arm], axis=0); ax.plot(GRID, m, color=color, ls=ls, lw=2.5, label=label)
ax.set_title('Mean over cells and seeds', fontsize=10); ax.legend(fontsize=8, frameon=False, loc='lower left')
for ax in axes.flat:
    ax.grid(alpha=0.25, lw=0.6); ax.spines[['top', 'right']].set_visible(False)
    ax.set_xlabel('stream time (0 = start, 1 = end)', fontsize=8); ax.set_ylabel('held-out PSNR (dB)', fontsize=8)
fig.suptitle('Held-out PSNR along the stream — B, seed-mean (moving avg 10% views; legend: mean PSNR)')
fig.tight_layout(); fig.savefig(OUT / 'temporal_abs_seedmean.png', dpi=130, bbox_inches='tight')

fig, (ax, bx) = plt.subplots(1, 2, figsize=(15, 5))
curves, cellbins, report = [], [], {}
for sc, b in cells:
    cs, bs = [], []
    for s in SEEDS:
        ke, ku = (sc, b, 'ervs_k16', s), (sc, b, 'uniform_iid', s)
        if ke not in data or ku not in data: continue
        (t, pe, fe), (_, pu, fu) = data[ke], data[ku]
        assert (fe == fu).all()
        d = pe - pu
        cs.append(np.interp(GRID, t, smooth(d, 0.20))); bs.append(bins5(d))
    if not cs: continue
    c = np.mean(cs, axis=0); curves.append(c); cellbins.append(np.mean(bs, axis=0))
    ax.plot(GRID, c, color='#2a6fdb', lw=1, alpha=0.3)
    report[f'{sc}|{b}'] = dict(n_seeds=len(cs), bins=np.mean(bs, axis=0).round(3).tolist())
C = np.array(curves); m = C.mean(0); se = C.std(0, ddof=1) / np.sqrt(len(C)) if len(C) > 1 else 0 * m
ax.fill_between(GRID, m - se, m + se, color='#2a6fdb', alpha=0.18, lw=0)
ax.plot(GRID, m, color='#2a6fdb', lw=2.5, label=f'mean of {len(C)} cells (±1 s.e.)')
ax.axhline(0, color='#999999', lw=1); ax.legend(frameon=False)
ax.set_title('ERVS K16 − Uniform w/ replacement, paired per view (seed-mean per cell)', fontsize=10)
ax.set_xlabel('stream time (0 = start, 1 = end)'); ax.set_ylabel('Δ held-out PSNR (dB), moving avg 20% views')
B = np.array(cellbins); bm = B.mean(0); bse = B.std(0, ddof=1) / np.sqrt(len(B))
bx.bar(range(5), bm, yerr=bse, width=0.5, color='#2a6fdb', capsize=4)
mk = {'aria1253': 'o', 'table_06': 's', 'aria1253rot': '^', 'square-1': 'D'}
for (sc, b), row in zip([c for c in cells if f'{c[0]}|{c[1]}' in report], B):
    bx.scatter(np.arange(5) + 0.3, row, marker=mk[sc], s=26, color='#555555',
               facecolors='none' if b == 15 else '#555555', zorder=3)
for i, v in enumerate(bm):
    bx.text(i - 0.32, v, f'{v:+.2f}', ha='right', va='center', fontsize=9)
bx.axhline(0, color='#999999', lw=1)
bx.set_xticks(range(5), ['0–20%', '20–40%', '40–60%', '60–80%', '80–100%'])
bx.set_ylabel('Δ mean PSNR per time bin (dB)'); bx.set_xlabel('stream time bin')
bx.set_title('bar = mean of cells ±1 s.e.; ○ budget 15 ● budget 25; ○aria □table_06 △rot ◇square-1', fontsize=9)
for a in (ax, bx):
    a.grid(alpha=0.25, lw=0.6); a.spines[['top', 'right']].set_visible(False)
fig.tight_layout(); fig.savefig(OUT / 'temporal_paired_seedmean.png', dpi=130, bbox_inches='tight')
report['bin_mean'] = bm.round(3).tolist(); report['bin_se'] = bse.round(3).tolist(); report['missing'] = missing
(OUT / 'temporal_seedmean.json').write_text(json.dumps(report, indent=1))
print(json.dumps({k: v for k, v in report.items() if k != 'missing'}, indent=0))

# Fig 3: the two arms' mean held-out PSNR curves alone (8 cells × 3 seeds), plus five-bin means.
fig, (ax, bx) = plt.subplots(1, 2, figsize=(15, 5), gridspec_kw=dict(width_ratios=[1.6, 1]))
binmeans = {}
for arm, label, color, ls in ARMS:
    cs = [np.interp(GRID, data[k][0], smooth(data[k][1], 0.10)) for k in data if k[2] == arm]
    bs = [bins5(data[k][1]) for k in data if k[2] == arm]
    m = np.mean(cs, axis=0); se = np.std(cs, axis=0, ddof=1) / np.sqrt(len(cs))
    allmean = np.mean([data[k][1].mean() for k in data if k[2] == arm])
    ax.fill_between(GRID, m - se, m + se, color=color, alpha=0.12, lw=0)
    ax.plot(GRID, m, color=color, ls=ls, lw=2.5, label=f'{label} — mean {allmean:.2f} dB')
    binmeans[arm] = np.mean(bs, axis=0)
ax.set_title(f'Mean held-out PSNR along the stream ({len(cells)} cells × {len(SEEDS)} seeds; band ±1 s.e.)', fontsize=10)
ax.set_xlabel('stream time (0 = start, 1 = end)'); ax.set_ylabel('held-out PSNR (dB), moving avg 10% views')
ax.legend(frameon=False, loc='lower center')
for j, (arm, label, color, ls) in enumerate(ARMS):
    x = np.arange(5) + (j - 0.5) * 0.18
    bx.plot(x, binmeans[arm], color=color, ls=ls, lw=1.5, marker='o', ms=9, label=label)
    for xi, v in zip(x, binmeans[arm]):
        bx.text(xi + (-0.08 if j == 0 else 0.08), v, f'{v:.2f}', ha='right' if j == 0 else 'left', va='center', fontsize=8)
bx.set_xticks(range(5), ['0–20%', '20–40%', '40–60%', '60–80%', '80–100%'])
lo = min(v.min() for v in binmeans.values()); hi = max(v.max() for v in binmeans.values())
bx.set_ylim(lo - 0.2, hi + 0.15); bx.set_xlim(-0.6, 4.6)
bx.set_ylabel('mean held-out PSNR per time bin (dB)'); bx.set_xlabel('stream time bin')
bx.set_title('Five-bin means (all cells and seeds; axis not from zero)', fontsize=10); bx.legend(frameon=False, fontsize=8, loc='upper right')
for a in (ax, bx):
    a.grid(alpha=0.25, lw=0.6); a.spines[['top', 'right']].set_visible(False)
fig.tight_layout(); fig.savefig(OUT / 'temporal_mean_curves.png', dpi=130, bbox_inches='tight')
print({a: np.round(v, 2).tolist() for a, v in binmeans.items()})
