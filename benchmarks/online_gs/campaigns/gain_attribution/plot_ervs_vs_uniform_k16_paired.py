#!/usr/bin/env python3
"""Paired per-view difference vs uniform K16 along stream time (ervs_vs_uniform_k16 v1).

Scene difficulty is shared by all arms on the same held-out view, so d_i = PSNR_arm(i) - PSNR_uniformK16(i) removes it.
Top: per-cell difference curves (moving average, 20% of views) and their mean on a 0..1 grid.
Bottom: five equal time bins, mean difference per cell (dots) and across cells (bar).
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[4]
V = ROOT / 'results/campaigns/gain_attribution/ervs_vs_uniform_k16/v1'
CELLS = [('aria1253', 15), ('aria1253', 25), ('table_06', 15), ('table_06', 25)]
MARK = {'aria1253': 'o', 'table_06': 's'}
GRID = np.linspace(0, 1, 201)
COMP = [('ervs_k16', 'ERVS K16 − Uniform K16', '#2a6fdb'), ('uniform_iid', 'Uniform w/ repl. − Uniform K16', '#2e9e6b')]


def views(output):
    pv = [x for x in json.loads((Path(output) / 'psnr/strict_fixed_manifest/final_result.json').read_text())['per_view']
          if x.get('predeclared_fixed_manifest_split')]
    pv.sort(key=lambda x: x['frame_index'])
    return np.array([x['frame_index'] for x in pv]), np.array([x['psnr'] for x in pv])


def smooth(y, frac=0.20):
    k = np.ones(max(3, int(round(frac * len(y)))))
    return np.convolve(y, k, 'same') / np.convolve(np.ones_like(y), k, 'same')


rows = {(r['scene'], r['budget'], r['arm']): r for r in json.loads((V / 'summary.json').read_text())}
fig, axes = plt.subplots(2, 2, figsize=(14, 8))
out = {}
for col, (arm, title, color) in enumerate(COMP):
    ax, bx = axes[0, col], axes[1, col]
    curves, bins = [], []
    for scene, budget in CELLS:
        f, ref = views(rows[(scene, budget, 'uniform_k16')]['output'])
        f2, p = views(rows[(scene, budget, arm)]['output'])
        assert (f == f2).all(), 'held-out views differ between arms'
        d = p - ref; t = (f - f[0]) / (f[-1] - f[0])
        s = smooth(d); curves.append(np.interp(GRID, t, s))
        ax.plot(t, s, color=color, lw=1, alpha=0.35)
        b = [d[i * len(d) // 5:(i + 1) * len(d) // 5].mean() for i in range(5)]
        bins.append(b)
        bx.scatter(np.arange(5) + 0.18, b, marker=MARK[scene], s=30, color='#555555', zorder=3,
                   facecolors='none' if budget == 15 else '#555555')
    m = np.mean(curves, axis=0)
    ax.plot(GRID, m, color=color, lw=2.5, label='mean of 4 cells')
    ax.axhline(0, color='#999999', lw=1)
    ax.set_title(title); ax.set_ylabel('Δ held-out PSNR (dB), moving avg 20% views')
    ax.set_xlabel('stream time (0 = start, 1 = end)'); ax.legend(frameon=False, fontsize=9)
    bm = np.mean(bins, axis=0)
    bx.bar(np.arange(5), bm, width=0.5, color=color)
    for i, v in enumerate(bm):
        bx.text(i, v + (0.02 if v >= 0 else -0.02), f'{v:+.2f}', ha='center', va='bottom' if v >= 0 else 'top', fontsize=9)
    bx.axhline(0, color='#999999', lw=1)
    bx.set_xticks(range(5), ['0–20%', '20–40%', '40–60%', '60–80%', '80–100%'])
    bx.set_ylabel('Δ mean PSNR per time bin (dB)'); bx.set_xlabel('stream time bin')
    bx.set_title('bar = mean of 4 cells; ○ budget 15, ● budget 25; circle aria, square table_06', fontsize=9)
    out[arm] = dict(bin_mean=bm.tolist(), bin_cells=bins)
    for a in (ax, bx):
        a.grid(alpha=0.25, lw=0.6); a.spines[['top', 'right']].set_visible(False)
fig.suptitle('Paired difference vs Uniform K16 along the stream (same held-out views) — B, seed 0', y=1.0)
fig.tight_layout()
fig.savefig(V / 'temporal_paired_diff.png', dpi=140, bbox_inches='tight')
(V / 'temporal_paired_diff.json').write_text(json.dumps(out, indent=1))
print(json.dumps({k: [round(x, 3) for x in v['bin_mean']] for k, v in out.items()}))
for k, v in out.items():
    print(k, [[round(x, 2) for x in c] for c in v['bin_cells']])
