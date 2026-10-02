#!/usr/bin/env python3
"""Held-out PSNR along stream time for ERVS K16 / uniform K16 / uniform with replacement (ervs_vs_uniform_k16 v1).

x = held-out view position in the stream (frame index normalized to 0..1 per scene); y = centered moving average of
per-view held-out PSNR (window = 10% of views). The mean panel averages the four cell curves on a common 0..1 grid.
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[4]
V = ROOT / 'results/campaigns/gain_attribution/ervs_vs_uniform_k16/v1'
ARMS = [('ervs_k16', 'ERVS K16', '#2a6fdb', '-'), ('uniform_k16', 'Uniform K16', '#d9622b', '--'),
        ('uniform_iid', 'Uniform w/ replacement', '#2e9e6b', ':')]
CELLS = [('aria1253', 15), ('aria1253', 25), ('table_06', 15), ('table_06', 25)]
GRID = np.linspace(0, 1, 201)


def curve(output):
    pv = [x for x in json.loads((Path(output) / 'psnr/strict_fixed_manifest/final_result.json').read_text())['per_view']
          if x.get('predeclared_fixed_manifest_split')]
    pv.sort(key=lambda x: x['frame_index'])
    f = np.array([x['frame_index'] for x in pv], float); p = np.array([x['psnr'] for x in pv])
    t = (f - f[0]) / (f[-1] - f[0])
    w = max(3, int(round(0.10 * len(p))))
    kernel = np.ones(w)
    smooth = np.convolve(p, kernel, 'same') / np.convolve(np.ones_like(p), kernel, 'same')
    return t, smooth, p.mean()


rows = {(r['scene'], r['budget'], r['arm']): r for r in json.loads((V / 'summary.json').read_text())}
fig, axes = plt.subplots(1, 5, figsize=(22, 4.2), sharey=False)
mean_curves = {a: [] for a, *_ in ARMS}
for ax, (scene, budget) in zip(axes, CELLS):
    for arm, label, color, ls in ARMS:
        t, y, m = curve(rows[(scene, budget, arm)]['output'])
        ax.plot(t, y, color=color, ls=ls, lw=2, label=f'{label} ({m:.2f})')
        mean_curves[arm].append(np.interp(GRID, t, y))
    ax.set_title(f'{scene} · {budget} renders/KF')
    ax.legend(fontsize=8, frameon=False, loc='lower right')
ax = axes[-1]
for arm, label, color, ls in ARMS:
    y = np.mean(mean_curves[arm], axis=0)
    ax.plot(GRID, y, color=color, ls=ls, lw=2, label=f'{label} ({y.mean():.2f})')
ax.set_title('Mean of 4 cells')
ax.legend(fontsize=8, frameon=False, loc='lower right')
for ax in axes:
    ax.set_xlabel('stream time (held-out view position, 0 = start, 1 = end)')
    ax.grid(alpha=0.25, lw=0.6); ax.spines[['top', 'right']].set_visible(False)
axes[0].set_ylabel('held-out PSNR (dB), moving avg 10% views')
fig.suptitle('Held-out PSNR along the stream — B, seed 0 (legend: mean PSNR)', y=1.02)
fig.tight_layout()
out = V / 'temporal_psnr.png'
fig.savefig(out, dpi=140, bbox_inches='tight')
print(out)
