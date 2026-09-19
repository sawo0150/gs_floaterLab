#!/usr/bin/env python3
"""Emit the two paper tables as LaTeX.

Table A -- supervision source: keyframes only vs keyframes + in-between frames.
Table B -- view ordering over the same pool: random reshuffling vs ERCB.

Both share one seal: same stream, same causal arrival schedule, the same number
of optimizer iterations per keyframe interval, the same initial point cloud and
poses, the same seed, the same densification policy, and a held-out split
neither arm ever trains on. Only the row label's policy differs.

Values are averaged over the scenes of each dataset, and a scene contributes
only if every arm in that table completed for it.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILIES = ("rpng", "utmm", "aria")
BUDGET = 120   # optimizer iterations granted to each keyframe interval


def psnr(output: str, total: int) -> float | None:
    path = Path(output) / "evaluation_curve.jsonl"
    if not path.is_file():
        return None
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    match = [r for r in rows if r.get("split") == "test" and r["iteration"] == total]
    return float(match[0]["psnr"]) if match else None


def extra(output: str) -> tuple[float | None, float | None]:
    path = Path(output) / "results.json"
    if not path.is_file():
        return None, None
    payload = json.loads(path.read_text())
    for value in payload.values():
        if "SSIM" in value:
            return float(value["SSIM"]), float(value["LPIPS"])
    return None, None


def gaussians(output: str, total: int) -> int | None:
    path = Path(output) / "gaussian_metrics" / f"iteration_{total}.json"
    return json.loads(path.read_text())["gaussian/count"] if path.is_file() else None


BENCH_B = HERE.parent / "benchmark-B"
ORDER_BUDGETS = (15, 30, 60)   # updates per keyframe interval


def collect() -> dict:
    """Table A runs (densify on, budget 60) plus the ordering runs from benchmark-B."""
    runs = {}
    for name in ("evidence/manifest_budget.json",):
        path = HERE / name
        if not path.is_file():
            continue
        for job in json.loads(path.read_text())["jobs"]:
            if job.get("state") != "complete" or job["budget"] != BUDGET:
                continue
            ssim, lpips = extra(job["output"])
            runs[(job["family"], job["scene"], job["arm"])] = {
                "psnr": psnr(job["output"], job["total_iterations"]),
                "ssim": ssim, "lpips": lpips,
                "updates": job["total_iterations"],
                "gaussians": gaussians(job["output"], job["total_iterations"]),
            }
    # ordering axis: benchmark-B's own RR/ERCB pair across its update budgets
    path = BENCH_B / "evidence/manifest.json"
    if path.is_file():
        for job in json.loads(path.read_text())["jobs"]:
            if job.get("state") != "complete":
                continue
            if job.get("stride") != 20 or job.get("budget") not in ORDER_BUDGETS:
                continue
            if job["arm"] not in ("rr", "ercb"):
                continue
            ssim, lpips = extra(job["output"])
            runs[(job["family"], job["scene"], f"order_{job['arm']}_{job['budget']}")] = {
                "psnr": psnr(job["output"], job["total_iterations"]),
                "ssim": ssim, "lpips": lpips,
                "updates": job["total_iterations"],
                "gaussians": gaussians(job["output"], job["total_iterations"]),
            }
    return runs


def table(runs: dict, arms: list[tuple[str, str]], caption: str, label: str) -> str:
    scenes = sorted({(f, s) for f, s, _ in runs})
    paired = [(f, s) for f, s in scenes
              if all((f, s, arm) in runs and runs[(f, s, arm)]["psnr"] is not None
                     for arm, _ in arms)]
    counts = {fam: sum(1 for f, _ in paired if f == fam) for fam in FAMILIES}

    def cell(arm: str, fam: str | None, key: str) -> str:
        values = [runs[(f, s, arm)][key] for f, s in paired
                  if (fam is None or f == fam) and runs[(f, s, arm)][key] is not None]
        if not values:
            return "--"
        mean = statistics.fmean(values)
        if key == "psnr":
            return f"{mean:.2f}"
        if key == "ssim":
            return f"{mean:.4f}"
        if key == "lpips":
            return f"{mean:.4f}"
        return f"{mean:,.0f}"

    lines = [
        r"\begin{table}[t]", r"\centering",
        rf"\caption{{{caption}}}", rf"\label{{{label}}}",
        r"\setlength{\tabcolsep}{5pt}", r"\renewcommand{\arraystretch}{1.05}",
        r"\resizebox{\linewidth}{!}{%",
        r"\begin{tabular}{clcccc}", r"\toprule",
        r"Metric & Policy & " + " & ".join(
            f"{fam.upper()} ({counts[fam]})" for fam in FAMILIES) + r" & All \\",
        r"\midrule",
    ]
    metric_rows = [("PSNR $\\uparrow$", "psnr"), ("SSIM $\\uparrow$", "ssim"),
                   ("LPIPS $\\downarrow$", "lpips"), ("final \\#G", "gaussians")]
    for title, key in metric_rows:
        lines.append(rf"\multirow{{{len(arms)}}}{{*}}{{{title}}}")
        for arm, name in arms:
            bold = name.startswith("*")
            display = name.lstrip("*")
            label_cell = rf"\textbf{{{display}}}" if bold else display
            cells = [cell(arm, fam, key) for fam in FAMILIES] + [cell(arm, None, key)]
            if bold:
                cells = [rf"\textbf{{{c}}}" for c in cells]
            lines.append(rf"& {label_cell} & " + " & ".join(cells) + r" \\")
        lines.append(r"\midrule" if key != metric_rows[-1][1] else r"\bottomrule")
    lines += [r"\end{tabular}%", r"}", r"\end{table}"]
    return "\n".join(lines), paired


def budget_table(runs: dict, caption: str, label: str) -> tuple[str, list]:
    """Ordering axis with the update budget on the columns, so the crossover shows."""
    arms = [("order_rr", "Random reshuffling"), ("order_ercb", "ERCB")]
    scenes = sorted({(f, s) for f, s, _ in runs})
    paired = [(f, s) for f, s in scenes
              if all((f, s, f"{arm}_{b}") in runs
                     and runs[(f, s, f"{arm}_{b}")]["psnr"] is not None
                     for arm, _ in arms for b in ORDER_BUDGETS)]

    def mean(arm: str, budget: int, key: str):
        values = [runs[(f, s, f"{arm}_{budget}")][key] for f, s in paired
                  if runs[(f, s, f"{arm}_{budget}")][key] is not None]
        return statistics.fmean(values) if values else None

    def wins(budget: int) -> str:
        count = sum(1 for f, s in paired
                    if runs[(f, s, f"order_ercb_{budget}")]["psnr"]
                    > runs[(f, s, f"order_rr_{budget}")]["psnr"])
        return f"{count}/{len(paired)}"

    def fmt(value, key):
        if value is None:
            return "--"
        if key == "psnr":
            return f"{value:.2f}"
        if key in ("ssim", "lpips"):
            return f"{value:.4f}"
        return f"{value:,.0f}"

    lines = [
        r"\begin{table}[t]", r"\centering",
        rf"\caption{{{caption}}}", rf"\label{{{label}}}",
        r"\setlength{\tabcolsep}{5pt}", r"\renewcommand{\arraystretch}{1.05}",
        r"\resizebox{\linewidth}{!}{%",
        r"\begin{tabular}{clccc}", r"\toprule",
        r"Metric & Policy & " + " & ".join(
            f"{b} upd./interval" for b in ORDER_BUDGETS) + r" \\",
        r"\midrule",
    ]
    for title, key in (("PSNR $\\uparrow$", "psnr"), ("SSIM $\\uparrow$", "ssim"),
                       ("LPIPS $\\downarrow$", "lpips")):
        lines.append(rf"\multirow{{2}}{{*}}{{{title}}}")
        for arm, name in arms:
            cells = []
            for b in ORDER_BUDGETS:
                value = fmt(mean(arm, b, key), key)
                better = mean("order_ercb", b, key) is not None and mean("order_rr", b, key) is not None
                if better and key != "gaussians":
                    e, r = mean("order_ercb", b, key), mean("order_rr", b, key)
                    win = (e > r) if key in ("psnr", "ssim") else (e < r)
                    if (arm == "order_ercb") == win:
                        value = rf"\textbf{{{value}}}"
                cells.append(value)
            lines.append(rf"& {name} & " + " & ".join(cells) + r" \\")
        lines.append(r"\midrule")
    lines = lines[:-1]
    lines += [r"\bottomrule", r"\end{tabular}%", r"}", r"\end{table}"]
    return "\n".join(lines), paired


def main() -> None:
    runs = collect()
    table_a, paired_a = table(
        runs, [("kf_only", "Keyframes only"), ("kf_dense", "*+ in-between frames")],
        "Supervision source. Both rows receive the identical stream, the same number of "
        "optimizer iterations per keyframe interval, the same initial point cloud, poses, "
        "seed and densification policy; only which arrived frames may be drawn differs. "
        "Averaged over the scenes of each dataset; scene counts in parentheses.",
        "tab:supervision")
    table_b, paired_b = budget_table(
        runs,
        "View ordering over the same pool, as a function of how many optimizer iterations each "
        "keyframe interval receives. Both rows see the identical causal stream with the same "
        "seed, initialisation and iteration count; only the draw order differs. The advantage "
        "belongs to ERCB exactly where the selector must choose what not to serve, and "
        "disappears once every view can be served anyway.",
        "tab:ordering")

    out = HERE / "TABLES.tex"
    out.write_text(table_a + "\n\n" + table_b + "\n")
    print(f"Table A scenes: {len(paired_a)}   Table B scenes: {len(paired_b)}")
    print(out)
    print()
    print(table_a)
    print()
    print(table_b)


if __name__ == "__main__":
    main()
