#!/usr/bin/env python3
"""Convergence figure on an absolute optimizer-iteration axis.

Follows the idiom these papers use (e.g. 3DGS^2, SIGGRAPH 2025, Fig. 4): a
group of representative per-scene convergence plots with iterations on the x
axis, rather than one curve averaged over scenes. Averaging is what would force
a normalised axis here, because trajectory length sets the iteration count and
it varies 37x across our scenes (901 to 33,901).

Selection rule, stated so it cannot be read as cherry-picking: for each dataset
we show the scene whose final Delta is the median of that dataset, and the
scene whose final Delta is the lowest. All 19 scenes appear in the summary bar.

Both arms of every panel receive the identical causal stream, identical arrival
times and the identical number of optimizer iterations; only the candidate pool
differs. The horizontal arrow is the iteration saving in real iterations.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
FAMILIES = ("aria", "utmm", "rpng")
GREY, BLUE = "#8c8c8c", "#1f6fb4"


def series(job: dict) -> tuple[np.ndarray, np.ndarray]:
    path = Path(job["output"]) / "evaluation_curve.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    test = sorted((r for r in rows if r.get("split") == "test"), key=lambda r: r["iteration"])
    return (np.array([r["iteration"] for r in test], dtype=float),
            np.array([statistics.fmean(r["per_view_psnr"].values()) for r in test]))


def crossing(x: np.ndarray, y: np.ndarray, target: float) -> float | None:
    for i in range(len(y)):
        if y[i] >= target:
            if i == 0:
                return float(x[0])
            x0, y0, x1, y1 = x[i - 1], y[i - 1], x[i], y[i]
            return float(x0 + (x1 - x0) * (target - y0) / (y1 - y0))
    return None


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "evidence/manifest_curve.json"
    manifest = json.loads((HERE / name).read_text())
    jobs = {(j["family"], j["scene"], j["arm"]): j
            for j in manifest["jobs"] if j.get("state") == "complete"}
    scenes = sorted({(f, s) for f, s, _ in jobs
                     if (f, s, "kf_only") in jobs and (f, s, "kf_dense") in jobs})

    record = {}
    for family, scene in scenes:
        xa, ya = series(jobs[(family, scene, "kf_only")])
        xb, yb = series(jobs[(family, scene, "kf_dense")])
        point = crossing(xb, yb, ya[-1])
        record[(family, scene)] = {
            "kf": (xa, ya), "dn": (xb, yb), "total": xa[-1],
            "delta": yb[-1] - ya[-1], "cross": point,
            "saved": None if point is None else xa[-1] - point,
        }

    # selection: per dataset, the median-Delta scene and the lowest-Delta scene
    chosen = []
    for family in FAMILIES:
        pool = sorted((s for f, s in scenes if f == family),
                      key=lambda s: record[(family, s)]["delta"])
        chosen.append((family, pool[len(pool) // 2]))
        chosen.append((family, pool[0]))

    fig, axes = plt.subplots(2, 3, figsize=(10.2, 5.4))
    for index, (family, scene) in enumerate(chosen):
        ax = axes[index % 2][index // 2]
        entry = record[(family, scene)]
        ax.plot(*entry["kf"], color=GREY, lw=1.8)
        ax.plot(*entry["dn"], color=BLUE, lw=1.8)
        target = entry["kf"][1][-1]
        ax.axhline(target, color="#777777", ls=":", lw=0.9)
        if entry["cross"] is not None and entry["saved"] > 0:
            ax.annotate("", xy=(entry["cross"], target), xytext=(entry["total"], target),
                        arrowprops=dict(arrowstyle="<|-", color=BLUE, lw=1.1,
                                        shrinkA=0, shrinkB=0))
        saving = ("" if entry["cross"] is None or entry["saved"] <= 0
                  else f",  $-${entry['saved']:,.0f} it. to match")
        ax.set_title(f"{family}/{scene}   ({entry['total']:,.0f} it.)\n"
                     rf"$\Delta$={entry['delta']:+.2f} dB{saving}", fontsize=8.5)
        ax.tick_params(labelsize=7.5)
        ax.grid(alpha=0.25, lw=0.5)
        if index % 2 == 1:
            ax.set_xlabel("optimizer iterations", fontsize=8.5)
        if index // 2 == 0:
            ax.set_ylabel("held-out PSNR (dB)", fontsize=8.5)
    axes[0][0].plot([], [], color=GREY, lw=1.8, label="Keyframes only")
    axes[0][0].plot([], [], color=BLUE, lw=1.8, label="+ in-between frames")
    axes[0][0].legend(loc="lower right", fontsize=7.5, frameon=False)
    fig.tight_layout()
    for suffix in ("pdf", "png"):
        fig.savefig(HERE / f"figure_convergence.{suffix}", dpi=220)

    print(f"{'scene':24s} {'T':>7} {'cross':>8} {'saved':>8} {'saved %':>8} {'final d':>8}")
    saved_pct = []
    for family, scene in scenes:
        e = record[(family, scene)]
        if e["cross"] is None:
            print(f"{family+'/'+scene:24s} {e['total']:7,.0f} {'never':>8}")
            continue
        pct = 100 * e["saved"] / e["total"]
        saved_pct.append(pct)
        mark = " *" if (family, scene) in chosen else ""
        print(f"{family+'/'+scene:24s} {e['total']:7,.0f} {e['cross']:8,.0f} "
              f"{e['saved']:8,.0f} {pct:7.1f}% {e['delta']:+8.2f}{mark}")
    print(f"\nmedian iteration saving: {statistics.median(saved_pct):.1f}%  "
          f"({len(saved_pct)}/{len(scenes)} scenes reach the keyframe-only endpoint early)")
    print(HERE / "figure_convergence.pdf")


if __name__ == "__main__":
    main()
