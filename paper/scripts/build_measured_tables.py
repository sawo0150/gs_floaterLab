#!/usr/bin/env python3
"""Build one-column tables from audited held-out records, never invented cells."""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import sys

PAPER = Path(__file__).resolve().parents[1]
ROOT = PAPER.parent
sys.path.insert(0, str(ROOT / "benchmarks/online_gs/campaigns/gain_attribution"))
from collect_cvpr_assets import CANDIDATES, OUT, RESULTS, endpoint, read, sha
import build_draft_tables as registry

EMPTY = r"\textemdash"
SHARED_LIVE = "live_fifo_shared_tracking"
FAILURES = {}
DISPLAY = {"rpng": "RPNG", "utmm": "UTMM", "aria": "Aria"}
METRICS = [("psnr", r"PSNR $\uparrow$"), ("ssim", r"SSIM $\uparrow$"), ("lpips", r"LPIPS $\downarrow$"), ("gaussians", r"\#G (k)")]


def fmt(value, metric):
    if value is None:
        return EMPTY
    return f"{value/1000:.1f}" if metric == "gaussians" else f"{value:.2f}" if metric == "psnr" else f"{value:.3f}"


def records():
    rows = read(OUT / "measured_endpoints.json")
    selected = [r for r in rows if r["protocol"] in ["fixed_training40_d3", "live_fifo"]]
    # Install a fresh pair atomically, never average different cohorts or a lone arm.
    for panel in [RESULTS / "cvpr_assets/pilot_v1/summary.json", RESULTS / "cvpr_assets/fixed_work_v1/summary.json", RESULTS / "cvpr_assets/fixed_work_12f_v1/summary.json"]:
      if panel.exists():
        states = read(panel)
        done = [r for r in states if r["status"] == "passed"]
        for r in states:
            if r['status'] == 'failed' and r.get('budget') is not None and r.get('arm') in {'d3', 'vanilla'}:
                key = (f"fixed_training{r['budget']}_d3", r['dataset'], r['scene'], None, r['arm'])
                FAILURES[key] = {'status': r['status'], 'output': r['output'], 'summary': str(panel), 'error': r.get('error')}
        for dataset, scene, budget in {(r["dataset"], r["scene"], r["budget"]) for r in done}:
            arms = [r for r in done if (r["dataset"], r["scene"], r["budget"]) == (dataset, scene, budget)]
            if {r["arm"] for r in arms} != {"d3", "vanilla"}:
                continue
            protocol = f"fixed_training{budget}_d3"
            pair = [endpoint(protocol, Path(r["output"]), dataset, scene, r["arm"], budget) for r in arms]
            assert len({r["cohort_uid_sha256"] for r in pair}) == 1
            selected = [r for r in selected if not (r["protocol"] == protocol and (r["dataset"], r["scene"]) == (dataset, scene))]
            selected += pair
        # A failed fresh run must not be silently replaced by a prior release.
        for protocol, dataset, scene, scale, arm in FAILURES:
            selected = [r for r in selected if (r['protocol'], r['dataset'], r['scene'], r['time_scale'], r['arm']) != (protocol, dataset, scene, scale, arm)]
    live_panel = RESULTS / 'cvpr_assets/live_shared_tracking_v1/summary.json'
    if live_panel.exists():
        done = [r for r in read(live_panel) if r['status']=='passed']
        for d,s,scale in {(r['dataset'],r['scene'],r['time_scale']) for r in done}:
            group = [r for r in done if (r['dataset'],r['scene'],r['time_scale'])==(d,s,scale)]
            if {r['arm'] for r in group} != {'ours','vanilla'}: continue
            configs = [read(Path(r['output']) / 'effective_config.json')['config']['Tracking'] for r in group]
            assert configs[0] == configs[1]
            pair = [endpoint('live_fifo', Path(r['output']), d,s,r['arm'],40,scale) for r in group]
            assert len({r['cohort_uid_sha256'] for r in pair})==1
            for r in pair:
                runtime = read(Path(r['output']) / 'result.json')
                assert not runtime['error'] and runtime['source_unchanged'] and runtime['zero_tail_observed']
                assert runtime['tracked_frames']==runtime['input_frames']
                r.update(protocol=SHARED_LIVE, tracking_config_scope='shared_official_dataset_Tracking_config')
            selected += pair
    for r in selected:
        if r["protocol"].startswith("live_fifo"):
            x = read(Path(r["output"]) / "result.json")
            r["lag_p95_seconds"] = x["start_lag_ms"]["95"] / 1000
            r["dropped_packets"] = x["worker"]["backlog"]["dropped_mapping_packets"]
    # Repository convention: lightweight table CSV is the canonical input to TeX.
    canonical = PAPER / "results/tables/cvpr_endpoint_measurements.csv"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    fields = ["protocol", "dataset", "scene", "arm", "renders_per_kf_cap", "time_scale", "psnr", "ssim", "lpips", "gaussians", "eval_views", "training_renders", "proxy_renders", "mapping_seconds", "allowed_seconds", "tracking_seconds", "lag_p95_seconds", "dropped_packets", "tracking_config_scope", "peak_cuda_allocated_bytes", "result_sha256", "output", "metric_path", "metric_sha256", "cohort_uid_sha256"]
    with canonical.open("w", newline="") as f:
        w = csv.DictWriter(f, fields, extrasaction="ignore")
        w.writeheader(); w.writerows(selected)
    numeric = {"renders_per_kf_cap", "time_scale", "psnr", "ssim", "lpips", "gaussians", "eval_views", "training_renders", "proxy_renders", "mapping_seconds", "allowed_seconds", "tracking_seconds", "lag_p95_seconds", "dropped_packets", "peak_cuda_allocated_bytes"}
    with canonical.open(newline="") as f:
        result = [{k: (float(v) if v else None) if k in numeric else v for k, v in r.items()} for r in csv.DictReader(f)]
    (canonical.parent / 'cvpr_failed_runs.json').write_text(json.dumps(list(FAILURES.values()), indent=2) + '\n')
    return result


def paired(rows, dataset, protocol, scale=None):
    arm_ours = "ours" if protocol.startswith("live_fifo") else "d3"
    arms = {arm: {r["scene"]: r for r in rows if r["dataset"] == dataset and r["protocol"] == protocol and r["time_scale"] == scale and r["arm"] == arm} for arm in ["vanilla", arm_ours]}
    common = set(arms["vanilla"]) & set(arms[arm_ours])
    for scene in common:
        assert arms["vanilla"][scene]["cohort_uid_sha256"] == arms[arm_ours][scene]["cohort_uid_sha256"]
    return {arm: {s: a[s] for s in CANDIDATES[dataset] if s in common} for arm, a in arms.items()}


def time_protocol(rows):
    # Never mix the old unmatched tracker recipe with the new shared recipe.
    return SHARED_LIVE if any(r['protocol']==SHARED_LIVE for r in rows) else 'live_fifo'


def line(cells):
    return " & ".join(cells) + r" \\"


def table(caption, labels, columns, headers, body, note):
    return "\n".join(["% Generated from audited experiment JSON by build_measured_tables.py.", r"\begin{table}[tbp]", r"\centering", "\\caption{" + caption + "}", *["\\label{"+s+"}" for s in labels], r"\begingroup", r"\footnotesize", r"\setlength{\tabcolsep}{2.8pt}", r"\renewcommand{\arraystretch}{1.02}", r"\resizebox{\linewidth}{!}{%", "\\begin{tabular}{@{}"+columns+"@{}}", r"\toprule", line(headers), r"\midrule", *body, r"\bottomrule", r"\end{tabular}}", r"\endgroup", r"\par\vspace{3pt}", r"\begin{minipage}{\linewidth}", r"\scriptsize\raggedright " + note, r"\end{minipage}", r"\end{table}", ""])


def legend():
    return r"\textsuperscript{VI}: RGB+IMU; \textsuperscript{R}: RGB only; \textsuperscript{C}: conditional adapter. Dashes denote unmeasured cells; F denotes a failed run."


def main_table(rows, timed=False, scale=None):
    protocol = time_protocol(rows) if timed else "fixed_training40_d3"
    body, ns = [], []
    for dataset in DISPLAY:
        pairs = paired(rows, dataset, protocol, scale)
        ours = "ours" if timed else "d3"
        ns.append(f"{DISPLAY[dataset]} {len(pairs['vanilla'])}/{len(CANDIDATES[dataset])}")
        for idx, method in enumerate(registry.METHODS):
            arm = "vanilla" if method["name"] == "VIGS-SLAM" else ours if method["name"] == "Ours" else None
            samples = list(pairs.get(arm, {}).values())
            values = [fmt(statistics.mean(x[k] for x in samples), k) if samples else EMPTY for k, _ in METRICS]
            if timed:
                values.append(f"{statistics.mean(x['lag_p95_seconds'] for x in samples):.2f}" if samples else EMPTY)
            body.append(line([DISPLAY[dataset] if idx == 0 else "", registry.method_tex(method), *values]))
        body.append(r"\midrule")
    body.pop()
    complete = all(len(paired(rows, d, protocol, scale)['vanilla']) == len(CANDIDATES[d]) for d in DISPLAY)
    note = legend() + " Paired coverage: " + "; ".join(ns) + ". Scene means have equal weight."
    note += (" All declared candidate scenes are measured for VIGS-SLAM and ours." if complete else
             " These partial means are not full-dataset results.")
    if timed:
        note += (" Both systems use the same dataset Tracking configuration." if protocol==SHARED_LIVE else
                 " Tracker settings match on Aria; RPNG/UTMM retain different motion thresholds, windows, and radii.")
        note += " The mapper stops at its deadline; tracking may finish later, so this is not proof of real-time end-to-end completion."
        caption = f"Measured end-to-end held-out quality with {scale:g}$\\times$ sensor-duration allowance, concurrent tracking, FIFO capacity two, and zero optimizer tail. Only completed paired scenes contribute to means; other methods await measurement."
        labels = ["tab:time_comparison", "tab:time_comparison_1x"] if scale == 1 else ["tab:time_comparison_1p5x"]
    else:
        note += " Ours uses D3 plus the fixed raster/warp implementation. Its proxy forwards are additional to 40 training renders/KF; this is not equal total computation."
        caption = "Measured held-out rendering quality at 40 training renders per admitted keyframe, using a shared causal tracking trace and evaluation cohort. Ours includes the merged D3 geometry objective. Unmeasured baseline rows remain reserved."
        labels = ["tab:rendering_comparison", "tab:main"]
    return table(caption, labels, "ll"+"c"*(5 if timed else 4), ["Dataset", "Method", *[v for _, v in METRICS], *([r"\shortstack{Lag p95\\(s)}"] if timed else [])], body, note)


def supplementary(rows, timed=False):
    pieces = []
    for dataset in DISPLAY:
        for budget_or_scale in [1, 1.5] if timed else [15, 40]:
            scale = budget_or_scale if timed else None
            budget = None if timed else budget_or_scale
            protocol = time_protocol(rows) if timed else f"fixed_training{budget}_d3"
            pairs = paired(rows, dataset, protocol, scale)
            ours = "ours" if timed else "d3"
            body = []
            for scene in CANDIDATES[dataset]:
                for idx, (arm, label) in enumerate([("vanilla", "VIGS-SLAM"), (ours, r"\textbf{Ours}")]):
                    record = pairs[arm].get(scene)
                    failed = (protocol, dataset, scene, scale, arm) in FAILURES
                    values = ["F" if failed else fmt(record[k] if record else None, k) for k, _ in METRICS]
                    body.append(line([registry.escape(scene) if idx == 0 else "", label, *values]))
                body.append(r"\addlinespace[2pt]")
            body.append(r"\midrule")
            for idx, (arm, label) in enumerate([("vanilla", "VIGS-SLAM"), (ours, r"\textbf{Ours}")]):
                samples = list(pairs[arm].values())
                values = [fmt(statistics.mean(x[k] for x in samples), k) if samples else EMPTY for k, _ in METRICS]
                body.append(line(["Avg." if idx == 0 else "", label, *values]))
            ident = f"tab:t{'2' if timed else '1'}_supp_{dataset}" + ("_1x" if scale == 1 else "_1p5x" if scale == 1.5 else f"_render{budget}")
            labels = [ident]
            if not timed and dataset == "rpng" and budget == 40:
                labels.append("tab:scene")
            allowance = f" at {scale:g}$\\times$ sensor-duration allowance" if timed else f" at {budget} training renders/KF"
            caption = f"{DISPLAY[dataset]} sequence-level held-out results{allowance}. All candidate scenes remain listed, including unmeasured scenes."
            note = f"Paired coverage {len(pairs['vanilla'])}/{len(CANDIDATES[dataset])}. Avg. gives equal weight to the paired scene means at this budget. Dashes mean unmeasured or unpaired; F means failed. " + ("Both systems use RGB+IMU. D3 proxy renders are additional work. The 40-render rows also generate the main table; additional candidate baselines remain unmeasured." if not timed else "These records also generate the main table. Concurrent tracking, FIFO capacity two, zero mapper optimizer tail. " + ("Shared dataset Tracking configuration; tracking completion may exceed the mapper deadline." if protocol==SHARED_LIVE else "See the main table for tracking configuration differences."))
            pieces.append(table(caption, labels, "llcccc", ["Sequence", "Method", *[v for _, v in METRICS]], body, note))
    return "\n".join(pieces)


def install(name, fragment, tex, rows):
    directory = PAPER / "tables" / name
    current = directory / "current"
    archive = directory / "output/blank_before_measurements_2026-10-01"
    if not archive.exists():
        shutil.copytree(current, archive)
    current.mkdir(exist_ok=True)
    (current / "table.tex").write_text(tex)
    (PAPER / "latex/tab" / fragment).write_text(tex)
    data = PAPER / "results/tables/cvpr_endpoint_measurements.csv"
    timed = name.startswith('table02')
    protocols = [(time_protocol(rows), s) for s in [1, 1.5]] if timed else [(f'fixed_training{b}_d3', None) for b in ([15,40] if 'supp' in name else [40])]
    coverage = [{'protocol': p, 'time_scale': s, 'dataset': d, 'paired': len(paired(rows,d,p,s)['vanilla']),
                 'candidates': len(CANDIDATES[d])} for p,s in protocols for d in DISPLAY]
    complete = all(c['paired']==c['candidates'] for c in coverage)
    provenance = {"kind": "measured_results", "experimental_evidence": True, "complete_cohort": complete,
                  "coverage": coverage, "other_method_rows_measured": False,
                  "manuscript_width": "one_column", "data": str(data), "data_sha256": sha(data), "records": [{"protocol": r["protocol"], "scene": r["scene"], "arm": r["arm"], "metric_path": r["metric_path"], "metric_sha256": r["metric_sha256"]} for r in rows], "failed_runs": list(FAILURES.values()), "table_sha256": sha(current / "table.tex")}
    (current / "provenance.json").write_text(json.dumps(provenance, indent=2)+"\n")
    (current / "caption.md").write_text("# 실제 측정 표 (전체 cohort 진행 중)\n\n한 단 너비. 숫자는 strict fixed held-out 평가에서 수집한다. 미측정 scene/방법은 대시로 남긴다. 본문 평균과 appendix는 같은 paired cohort를 쓴다. 최신 D3의 보조 렌더와 live tracker 설정 차이는 TeX 각주에 명시한다.\n")


def main():
    rows = records()
    install("table01_rendering_main", "t1_main_draft.tex", main_table(rows), rows)
    install("table01_rendering_supp", "t1_supp_draft.tex", supplementary(rows), rows)
    install("table02_time_main", "t2_main_draft.tex", main_table(rows, True, 1)+"\n"+main_table(rows, True, 1.5), rows)
    install("table02_time_supp", "t2_supp_draft.tex", supplementary(rows, True), rows)
    print("Installed measured T1/T2 main + supplementary; other baseline cells remain unmeasured.")


if __name__ == "__main__":
    main()
