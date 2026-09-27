#!/usr/bin/env python3
"""Evaluation PSNR against map optimization step, in the HAMMER Fig. 5 idiom.

A fixed held-out set spanning the whole trajectory (llffhold-8, never trained
by any arm) is re-rendered from the map as it stands at each checkpoint, and
its mean PSNR is plotted against cumulative optimizer steps. The last point of
each curve is exactly the number that arm contributes to the table.

One panel per dataset, stacked; the scene shown is the one whose final Delta is
the median of that dataset, so the choice cannot be read as cherry-picking.
Both arms receive the identical causal stream, identical arrival times and the
identical number of optimizer steps; only the candidate pool differs.

Usage: plot_convergence.py [evidence/manifest_curve.json]
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
ARMS = (("kf_only", "Keyframes only", "#c0392b"),
        ("kf_dense", "+ in-between frames", "#7d5bbe"))


def series(job: dict) -> tuple[np.ndarray, np.ndarray]:
    path = Path(job["output"]) / "evaluation_curve.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    test = sorted((r for r in rows if r.get("split") == "test"), key=lambda r: r["iteration"])
    return (np.array([r["iteration"] for r in test], dtype=float),
            np.array([statistics.fmean(r["per_view_psnr"].values()) for r in test]))


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "evidence/manifest_curve.json"
    manifest = json.loads((HERE / name).read_text())
    jobs = {(j["family"], j["scene"], j["arm"]): j
            for j in manifest["jobs"] if j.get("state") == "complete"}
    scenes = sorted({(f, s) for f, s, _ in jobs
                     if (f, s, "kf_only") in jobs and (f, s, "kf_dense") in jobs})
    delta = {(f, s): series(jobs[(f, s, "kf_dense")])[1][-1] - series(jobs[(f, s, "kf_only")])[1][-1]
             for f, s in scenes}
    chosen = []
    for family in FAMILIES:
        pool = sorted((s for f, s in scenes if f == family), key=lambda s: delta[(family, s)])
        chosen.append((family, pool[len(pool) // 2]))

    plt.rcParams.update({"font.size": 15, "axes.linewidth": 1.4})
    fig, axes = plt.subplots(len(chosen), 1, figsize=(8.0, 3.1 * len(chosen)))
    for ax, (family, scene) in zip(np.atleast_1d(axes), chosen):
        for arm, _, color in ARMS:
            ax.plot(*series(jobs[(family, scene, arm)]), color=color, lw=3.6,
                    solid_capstyle="round")
        ax.set_xlabel("Map Optimization Step")
        ax.set_ylabel("Evaluation PSNR")
        ax.set_xlim(0, series(jobs[(family, scene, "kf_only")])[0][-1])
        ax.text(0.975, 0.07, f"{family.upper()} / {scene}", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=16, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.45", facecolor="#c8c8c8",
                          edgecolor="#e8e8e8", linewidth=3))
        ax.tick_params(width=1.4, length=5)
    handles = [plt.Line2D([], [], color=color, lw=5, solid_capstyle="round")
               for _, _, color in ARMS]
    fig.legend(handles, [label for _, label, _ in ARMS], loc="lower center",
               ncol=len(ARMS), frameon=False, fontsize=16,
               bbox_to_anchor=(0.5, -0.004), handlelength=1.6, columnspacing=2.4)
    fig.tight_layout(rect=(0, 0.055, 1, 1))
    for suffix in ("pdf", "png"):
        fig.savefig(HERE / f"figure_convergence.{suffix}", dpi=220)
    print("panels:", ", ".join(f"{f}/{s} (d={delta[(f,s)]:+.2f})" for f, s in chosen))
    print(HERE / "figure_convergence.pdf")


if __name__ == "__main__":
    main()
