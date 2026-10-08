"""Offline (no GPU) analysis for settle-triggered consolidation: how often old KFs are 'touched' by later births and
how much replay a settle rule would schedule.

Births are reconstructed from a finished online run: each surviving Gaussian's origin_uid is its birth KF; points are
projected into earlier KFs with the final KF poses (no pose updates in these archives). A KF u is touched by birth b if
u is older than the newest LAG KFs at b and ≥ SHARE of b's surviving points fall in u's image with positive depth.
Rule: u is 'settled' once M KFs have arrived since its last touch; each touched→settled transition schedules one
consolidation of u (+ its anchored admitted dense views). Prunned Gaussians are missing (survivors only).
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch

LAG, SHARE = 6, 0.05


def analyze(run, Ms=(3, 6, 10), budget_frac=0.15, renders_per_kf=25, share=SHARE):
    run = Path(run)
    st = torch.load(run / 'final_map_state.pt', map_location='cpu', weights_only=False)
    xyz = st['parameters']['xyz'].float().numpy(); org = st['origin_uids'].numpy()
    W = {int(u): m.double().numpy() for u, m in st['keyframe_w2c'].items()}
    fx, fy, cx, cy = np.load(run / 'intrinsics.npy')[:4]
    Wd, Hd = 2 * cx, 2 * cy
    pol = json.loads((run / 'render_result.json').read_text())['training']['generations'][-1]['policy']
    kfs = sorted(int(u) for u in pol['keyframes'] if int(u) in W)
    import bisect
    adm = set(int(u) for u in pol['admitted_dense'])
    anchored = {u: 0 for u in kfs}
    for d in adm:                       # dense frames lie between KFs: left anchor = last KF before it
        i = bisect.bisect_right(kfs, d) - 1
        if i >= 0:
            anchored[kfs[i]] += 1
    touches = {u: [] for u in kfs}
    rng = np.random.default_rng(0)
    for bi, b in enumerate(kfs):
        P = xyz[org == b]
        if len(P) == 0 or bi <= LAG:
            continue
        if len(P) > 3000:
            P = P[rng.choice(len(P), 3000, replace=False)]
        Ph = np.c_[P, np.ones(len(P))]
        for u in kfs[:bi - LAG]:
            c = Ph @ W[u].T
            z = c[:, 2]; ok = z > 0.05
            x = fx * c[:, 0] / np.maximum(z, 1e-6) + cx; y = fy * c[:, 1] / np.maximum(z, 1e-6) + cy
            if np.mean(ok & (x >= 0) & (x < Wd) & (y >= 0) & (y < Hd)) >= share:
                touches[u].append(bi)
    n = np.array([len(v) for v in touches.values()])
    out = dict(run=str(run), kfs=len(kfs), touched_kfs=int((n > 0).sum()), touches_median=float(np.median(n[n > 0])) if (n > 0).any() else 0,
               touches_p90=float(np.percentile(n[n > 0], 90)) if (n > 0).any() else 0, dense_admitted=len(adm), share_threshold=share, rules={})
    total = len(kfs) * renders_per_kf; budget = budget_frac * total
    for M in Ms:
        events = []        # (arrival index when settled, uid)
        for u, ts in touches.items():
            if not ts:
                continue
            seq = ts + [10 ** 9]
            for a, nxt in zip(ts, seq[1:]):
                if nxt - a > M and a + M < len(kfs):      # settles before the next touch, within the stream
                    events.append((a + M, u))
        renders = sum(1 + anchored[u] for _, u in events)
        per_third = [sum(1 + anchored[u] for t, u in events if lo <= t / len(kfs) < hi) for lo, hi in ((0, 1/3), (1/3, 2/3), (2/3, 1.01))]
        never = sum(1 for u, ts in touches.items() if ts and ts[-1] + M >= len(kfs))
        out['rules'][M] = dict(consolidations=len(events), renders=round(renders, 1), share_of_15pct_budget=round(renders / budget, 2),
                               renders_by_third=[round(x, 1) for x in per_third], unsettled_at_end=never)
    return out


if __name__ == '__main__':
    for r in sys.argv[1:]:
        print(json.dumps(analyze(r), indent=1))
