#!/usr/bin/env python3
"""Real tracking/work measurements; no dummy curves or inferred GPU limits."""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PAPER = Path(__file__).resolve().parents[1]
ROOT = PAPER.parent
SOURCE = ROOT / "results/campaigns/gain_attribution/fifo_live/v1"
ASSET = PAPER / "figures/figure12_tracking_mapping_capacity"
KEYS = [("aria", "Aria1253"), ("rot", "Aria rot"), ("rpng", "table_06"), ("utmm", "square-1")]


def main():
    rows = []
    for scale, allowance in [("scale1", 1), ("scale1p5", 1.5)]:
        for key, label in KEYS:
            for arm in ["vanilla", "ours"]:
                p = SOURCE / scale / key / arm / "result.json"
                x = json.loads(p.read_text())
                assert not x["error"] and x["zero_tail_observed"]
                rows.append({"scene": key, "label": label, "arm": arm, "allowance": allowance,
                             "tracking_call_p95_ms": x["track_call_ms"]["95"],
                             "training_renders_per_final_tracking_kf": x["committed_renders"] / x["tracking_kfs_final"],
                             "training_renders_per_mapper_admission": x["committed_renders"] / x["kf_admissions"],
                             "overflow_drops": x["worker"]["backlog"]["dropped_mapping_packets"],
                             "training_renders": x["committed_renders"], "tracking_kfs": x["tracking_kfs_final"],
                             "mapper_kf_admissions": x["kf_admissions"], "allowed_seconds": x["duration_seconds"],
                             "tracking_seconds": x["tracking_elapsed_seconds"], "source": str(p),
                             "source_sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    analysis = ASSET / "analysis"
    analysis.mkdir(exist_ok=True)
    with (analysis / "measured_tracking_work.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    current = ASSET / "current"
    archive = ASSET / "output/dummy_before_measurements_2026-10-01"
    if not archive.exists():
        shutil.copytree(current, archive)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.2, "axes.labelsize": 7.4,
                         "axes.titlesize": 8, "pdf.fonttype": 42, "svg.fonttype": "none"})
    fig, axes = plt.subplots(3, 1, figsize=(3.35, 4.25), sharex=True)
    settings = [("tracking_call_p95_ms", "Tracking call p95 (ms)", "(a) Tracking load"),
                ("training_renders_per_final_tracking_kf", "Renders / tracking KF", "(b) Achieved mapping work"),
                ("overflow_drops", "Pending packets dropped", "(c) FIFO overflow")]
    colors = {"vanilla": "#72787f", "ours": "#087e8b"}
    for ax, (field, ylabel, title) in zip(axes, settings):
        for j, (arm, allowance) in enumerate([("vanilla", 1), ("ours", 1), ("vanilla", 1.5), ("ours", 1.5)]):
            values = [next(r[field] for r in rows if r["scene"] == key and r["arm"] == arm and r["allowance"] == allowance) for key, _ in KEYS]
            ax.bar(np.arange(4) + (j-1.5)*.18, values, width=.17, color=colors[arm], edgecolor="white", linewidth=.35,
                   hatch="//" if allowance == 1.5 else None, label=f"{'VIGS' if arm == 'vanilla' else 'Ours'} {allowance:g}x")
        ax.set_ylabel(ylabel); ax.set_title(title, loc="left", pad=4)
        ax.grid(axis="y", color="#e4e8eb", linewidth=.5); ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="both", labelsize=6.8)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=2, fontsize=6.7, frameon=False, loc="upper center", bbox_to_anchor=(.55, 1.005))
    axes[-1].set_xticks(np.arange(4), [label for _, label in KEYS])
    fig.tight_layout(pad=.6, h_pad=.8, rect=(0, 0, 1, .91))
    fig.savefig(current / "figure.pdf")
    fig.savefig(current / "figure.svg")
    fig.savefig(current / "figure.png", dpi=220)
    plt.close(fig)
    shutil.copy2(current / "figure.pdf", PAPER / "latex/figs/draft/f12.pdf")
    caption = "Measured tracking load and mapping work with concurrent tracking at 1x and 1.5x sensor-duration allowances. (a) Per-frame tracking-call p95. (b) Committed training renders divided by final tracking keyframes, including keyframes that did not enter mapping. (c) Pending FIFO packet drops. The mapper cap is 40 renders per mapper admission, which differs from the denominator in (b). RPNG/UTMM retain different tracker settings between systems; these are end-to-end measurements, not isolated tracking-cost effects or hardware capacity limits."
    (current / "caption.md").write_text(caption + "\n")
    (current / "provenance.json").write_text(json.dumps({"kind": "actual_live_measurements", "experimental_evidence": True,
        "complete_candidate_cohort": False, "measured_scenes": 4, "candidate_scenes": 20, "data": str(analysis / "measured_tracking_work.csv"),
        "rows": rows, "generator": str(Path(__file__).resolve()), "manuscript_width": "one_column"}, indent=2) + "\n")
    (PAPER / "latex/fig/f12_draft.tex").write_text("\\begin{figure}[tbp]\n  \\centering\n  \\includegraphics[width=\\linewidth]{figs/draft/f12.pdf}\n  \\caption{Tracking load and achieved mapping work at 1$\\times$ and 1.5$\\times$ time allowances on four measured sequences. (a) Tracking-call p95. (b) Committed training renders per final tracking KF. (c) Pending FIFO drops. RPNG/UTMM tracker settings differ between systems; these measurements do not establish an isolated tracking-cost effect.}\n  \\label{fig:tracking_capacity}\n\\end{figure}\n")
    print("Installed real F12, four scenes / sixteen live runs.")


if __name__ == "__main__":
    main()
