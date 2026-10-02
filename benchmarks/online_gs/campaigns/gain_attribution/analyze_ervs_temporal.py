#!/usr/bin/env python3
"""Temporal and tail metrics for ERVS/ERCB vs RR on two systems (post-hoc analysis of existing runs; no training).

System B (VIGS-SLAM-custom main 6d200f0f, fixed-work frozen-tracker replay): ERVS vs RR, budgets 5/10/15/25 (4 scenes)
and 40 (rot, rpng); per-view PSNR from the fixed held-out manifest evaluation.
System 3dgs-custom benchmark-B (offline replay, RGB-only, stride20 init): original interval ERCB vs RR, budgets 15/30/60
updates/event, 19 scenes; per-view test PSNR from evaluation_curve.jsonl (final iteration).

Metrics per (system, scene, budget, arm), definitions follow ERCB_ablation/summarize_ercb_benchmark.py where they exist:
  mean        mean per-view PSNR
  worst_q1    mean of the arm's lowest ceil(n/4) per-view PSNRs
  rr_hard_q1  mean PSNR on the views in RR's lowest ceil(n/4) (same views for both arms)
  early, late mean PSNR over the first / last 25% of held-out views in time order
  drop        late - early
  std         standard deviation of per-view PSNR
Curves: per-view PSNR in time order, centred moving average over 15% of the views, x = normalized time (0..1).
"""
import csv
import json
import math
from pathlib import Path
import statistics as st

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
RES = ROOT / 'results/campaigns/gain_attribution'
OUT = RES / 'ervs_temporal_analysis/v1'
B_SCENES = ('aria1253', 'aria1253rot', 'table_06', 'square-1')
RR_C, ERVS_C, INK, INK2, GRID, SURF = '#2a78d6', '#eb6834', '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'


def load(p):
    return json.loads(Path(p).read_text())


def b_runs():
    """{(scene, budget): {'ervs': output, 'rr': output}} for system B (seed 0)."""
    cells = {}
    for r in load(RES / 'b_ablation_chain/v1/summary.json'):
        if r['phase'] == 'chain' and r['arm'] in ('R4', 'R4rr'):
            cells.setdefault((r['scene'], r['budget']), {})['ervs' if r['arm'] == 'R4' else 'rr'] = r['output']
    for name in ('b_ablation_v2', 'ervs_low_budget'):
        for r in load(RES / name / 'v1/summary.json'):
            cells.setdefault((r['scene'], r['budget']), {})[r['arm']] = r['output']
    return {k: v for k, v in cells.items() if {'ervs', 'rr'} <= set(v)}


def b_views(output):
    rows = [r for r in load(Path(output) / 'psnr/strict_fixed_manifest/final_result.json')['per_view']
            if r.get('predeclared_fixed_manifest_split')]
    rows.sort(key=lambda r: r['frame_index'])
    return [r['frame_index'] for r in rows], [r['psnr'] for r in rows]


def ercb_runs():
    rows = load(ROOT / 'context/experiments/ERCB_ablation/benchmark-B/evidence/summary.json')['runs']
    cells = {}
    for r in rows:
        if r['stride'] == 20 and r['seed'] == 0:
            cells.setdefault((f"{r['family']}/{r['scene']}", r['budget']), {})[r['arm']] = r['output']
    return {k: v for k, v in cells.items() if {'ercb', 'rr'} <= set(v)}


def ercb_views(output):
    last = None
    for line in (Path(output) / 'evaluation_curve.jsonl').read_text().splitlines():
        d = json.loads(line)
        if d['split'] == 'test':
            last = d
    names = sorted(last['per_view_psnr'], key=lambda n: (float(Path(n).stem) if Path(n).stem.replace('.', '').isdigit()
                                                          else math.inf, n))
    return list(range(len(names))), [last['per_view_psnr'][n] for n in names], names


def metrics(psnr, rr_hard_idx):
    n = len(psnr)
    q = max(1, math.ceil(n / 4))
    return dict(n=n, mean=st.fmean(psnr), worst_q1=st.fmean(sorted(psnr)[:q]),
                rr_hard_q1=st.fmean(psnr[i] for i in rr_hard_idx), early=st.fmean(psnr[:q]),
                late=st.fmean(psnr[-q:]), drop=st.fmean(psnr[-q:]) - st.fmean(psnr[:q]), std=st.pstdev(psnr))


def moving(psnr, frac=0.15):
    w = max(3, int(round(len(psnr) * frac)) | 1)
    x = np.asarray(psnr, float)
    pad = w // 2
    xp = np.pad(x, pad, mode='edge')
    return np.convolve(xp, np.ones(w) / w, mode='valid')


def analyse(system, cells, reader, arm_names):
    table, curves = [], {}
    for (scene, budget), arms in sorted(cells.items()):
        views = {a: reader(arms[a]) for a in arm_names}
        p_rr = views['rr'][1]
        p_new = views[arm_names[0]][1]
        if len(p_rr) != len(p_new) or (system == 'B' and views['rr'][0] != views[arm_names[0]][0]):
            raise RuntimeError(f'view mismatch {system} {scene} {budget}')
        q = max(1, math.ceil(len(p_rr) / 4))
        hard = sorted(range(len(p_rr)), key=p_rr.__getitem__)[:q]
        for arm in arm_names:
            m = metrics(views[arm][1], hard)
            table.append(dict(system=system, scene=scene, budget=budget, arm=arm, **m))
        curves[(scene, budget)] = {a: moving(views[a][1]) for a in arm_names}
    return table, curves


def deltas(table, new_arm):
    by = {(r['system'], r['scene'], r['budget'], r['arm']): r for r in table}
    out = []
    for (sy, sc, bu, arm), r in by.items():
        if arm != new_arm:
            continue
        rr = by[(sy, sc, bu, 'rr')]
        out.append(dict(system=sy, scene=sc, budget=bu, **{k: r[k] - rr[k] for k in
                   ('mean', 'worst_q1', 'rr_hard_q1', 'early', 'late', 'drop', 'std')}))
    return out


def aggregate(dl):
    agg = {}
    for d in dl:
        agg.setdefault((d['system'], d['budget']), []).append(d)
    rows = []
    for (sy, bu), L in sorted(agg.items()):
        row = dict(system=sy, budget=bu, scenes=len(L))
        for k in ('mean', 'worst_q1', 'rr_hard_q1', 'early', 'late', 'drop', 'std'):
            v = [d[k] for d in L]
            row[k] = st.fmean(v)
            row[k + '_wins'] = sum(x < 0 for x in v) if k == 'std' else sum(x > 0 for x in v)
        rows.append(row)
    return rows


def style(ax):
    ax.set_facecolor(SURF)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=7)
    ax.grid(axis='y', color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def plot_curves(curves, scenes, budgets, new_arm, new_label, path, title):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(len(scenes), len(budgets), figsize=(2.6 * len(budgets), 1.9 * len(scenes)),
                             sharex=True, squeeze=False, facecolor=SURF)
    for i, sc in enumerate(scenes):
        for j, bu in enumerate(budgets):
            ax = axes[i][j]
            style(ax)
            c = curves.get((sc, bu))
            if c is None:
                ax.set_visible(False)
                continue
            x = np.linspace(0, 1, len(c['rr']))
            ax.plot(x, c['rr'], color=RR_C, linewidth=1.6, label='RR')
            ax.plot(x, c[new_arm], color=ERVS_C, linewidth=1.6, label=new_label)
            if i == 0:
                ax.set_title(f'budget {bu}', fontsize=8, color=INK)
            if j == 0:
                ax.set_ylabel(f'{sc}\nPSNR (dB)', fontsize=7, color=INK2)
            if i == len(scenes) - 1:
                ax.set_xlabel('normalized time', fontsize=7, color=INK2)
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper right', ncol=2, fontsize=8, frameon=False, labelcolor=INK)
    fig.suptitle(title, fontsize=9, color=INK, x=0.01, ha='left')
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(path, dpi=160, facecolor=SURF)
    plt.close(fig)


def plot_delta(curve_sets, path):
    """Scene-averaged ERVS/ERCB − RR moving-average difference vs normalized time, one panel per system."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    grid = np.linspace(0, 1, 101)
    fig, axes = plt.subplots(1, len(curve_sets), figsize=(4.2 * len(curve_sets), 2.8), squeeze=False, facecolor=SURF)
    ramp = ['#86b6ef', '#5598e7', '#2a78d6', '#1c5cab', '#0d366b']
    for ax, (name, curves, new_arm, budgets) in zip(axes[0], curve_sets):
        style(ax)
        ax.axhline(0, color=INK2, linewidth=0.8)
        for k, bu in enumerate(budgets):
            diffs = []
            for (sc, b), c in curves.items():
                if b != bu:
                    continue
                d = c[new_arm] - c['rr']
                diffs.append(np.interp(grid, np.linspace(0, 1, len(d)), d))
            if diffs:
                ax.plot(grid, np.mean(diffs, axis=0), color=ramp[k * (len(ramp) - 1) // max(1, len(budgets) - 1)],
                        linewidth=1.8, label=f'budget {bu} ({len(diffs)} scenes)')
        ax.set_title(name, fontsize=8, color=INK, loc='left')
        ax.set_xlabel('normalized time', fontsize=7, color=INK2)
        ax.set_ylabel('PSNR difference vs RR (dB)', fontsize=7, color=INK2)
        ax.legend(fontsize=7, frameon=False, labelcolor=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=160, facecolor=SURF)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tb, cb = analyse('B', b_runs(), b_views, ('ervs', 'rr'))
    te, ce = analyse('3dgs-custom', ercb_runs(), lambda o: ercb_views(o)[:2], ('ercb', 'rr'))
    dl = deltas(tb, 'ervs') + deltas(te, 'ercb')
    agg = aggregate(dl)
    (OUT / 'per_arm_metrics.json').write_text(json.dumps(tb + te, indent=2) + '\n')
    (OUT / 'per_scene_deltas.json').write_text(json.dumps(dl, indent=2) + '\n')
    (OUT / 'aggregate.json').write_text(json.dumps(agg, indent=2) + '\n')
    with (OUT / 'aggregate.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(agg[0]))
        w.writeheader()
        w.writerows(agg)
    plot_curves(cb, B_SCENES, (5, 15, 25, 40), 'ervs', 'ERVS', OUT / 'B_temporal_curves.png',
                'System B: held-out PSNR along the sequence (moving average, 15% window)')
    e_scenes = sorted({sc for sc, _ in ce})
    plot_curves(ce, e_scenes, (15, 30, 60), 'ercb', 'ERCB', OUT / 'ercb_temporal_curves.png',
                '3dgs-custom benchmark-B: held-out PSNR along the sequence (moving average, 15% window)')
    plot_delta([('System B: ERVS − RR', cb, 'ervs', (5, 10, 15, 25, 40)),
                ('3dgs-custom: ERCB − RR', ce, 'ercb', (15, 30, 60))], OUT / 'delta_vs_time.png')
    for r in agg:
        print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}))


if __name__ == '__main__':
    main()
