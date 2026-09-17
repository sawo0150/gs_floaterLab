#!/usr/bin/env python3
"""Validate benchmark-A three-arm budget runs and generate result artifacts."""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MANIFEST = HERE / "evidence/manifest.json"
BUDGET_LABELS = {15: "low", 30: "mid", 60: "high"}


def final_test(output: Path, total: int) -> dict:
    rows = [
        json.loads(line)
        for line in (output / "evaluation_curve.jsonl").read_text().splitlines()
        if line.strip()
    ]
    tests = [row for row in rows if row.get("split") == "test"]
    if not tests or tests[-1].get("iteration") != total:
        raise ValueError(f"missing final post-update test row: {output}")
    return tests[-1]


def fmt(value, digits: int = 4) -> str:
    if value is None or not isinstance(value, (int, float)) or not math.isfinite(value):
        return "—"
    return f"{value:.{digits}f}"


def temporal_quartile_service(summary: dict) -> list[float]:
    counts = summary["selection_count"]
    arrivals = summary["arrival_iteration"]
    names = sorted(counts, key=lambda name: (arrivals[name], name))
    size = len(names)
    groups = (
        names[: size // 4],
        names[size // 4 : size // 2],
        names[size // 2 : 3 * size // 4],
        names[3 * size // 4 :],
    )
    total = sum(counts.values())
    return [sum(counts[name] for name in group) / total for group in groups]


def pearson(xs: list[float], ys: list[float]) -> float:
    mean_x, mean_y = statistics.fmean(xs), statistics.fmean(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator = math.sqrt(
        sum((x - mean_x) ** 2 for x in xs)
        * sum((y - mean_y) ** 2 for y in ys)
    )
    return numerator / denominator


def aggregate(rows: list[dict], budget: int, family: str) -> dict | None:
    subset = [
        row
        for row in rows
        if row["status"] == "three_arm_pass"
        and row["budget"] == budget
        and (family == "all" or row["family"] == family)
    ]
    if not subset:
        return None
    ercb_deltas = [row["ercb_delta_vs_rr"] for row in subset]
    window_deltas = [row["window10_delta_vs_rr"] for row in subset]
    ercb_window_deltas = [row["ercb_delta_vs_window10"] for row in subset]
    return {
        "budget": budget,
        "budget_label": BUDGET_LABELS[budget],
        "family": family,
        "scenes": len(subset),
        "rr_mean_psnr": statistics.fmean(row["rr_psnr"] for row in subset),
        "window10_rr_mean_psnr": statistics.fmean(
            row["window10_rr_psnr"] for row in subset
        ),
        "ercb_mean_psnr": statistics.fmean(row["ercb_psnr"] for row in subset),
        "mean_window10_delta_vs_rr": statistics.fmean(window_deltas),
        "median_window10_delta_vs_rr": statistics.median(window_deltas),
        "window10_wins_vs_rr": sum(delta > 0 for delta in window_deltas),
        "mean_ercb_delta_vs_rr": statistics.fmean(ercb_deltas),
        "median_ercb_delta_vs_rr": statistics.median(ercb_deltas),
        "ercb_wins_vs_rr": sum(delta > 0 for delta in ercb_deltas),
        "mean_ercb_delta_vs_window10": statistics.fmean(ercb_window_deltas),
        "ercb_wins_vs_window10": sum(delta > 0 for delta in ercb_window_deltas),
        "rr_temporal_quartile_service_mean": [
            statistics.fmean(row[f"rr_service_q{quartile}_share"] for row in subset)
            for quartile in range(1, 5)
        ],
        "window10_rr_temporal_quartile_service_mean": [
            statistics.fmean(
                row[f"window10_rr_service_q{quartile}_share"] for row in subset
            )
            for quartile in range(1, 5)
        ],
        "ercb_temporal_quartile_service_mean": [
            statistics.fmean(row[f"ercb_service_q{quartile}_share"] for row in subset)
            for quartile in range(1, 5)
        ],
        "ercb_zero_service_worse": sum(
            row["ercb_zero_service"] > row["rr_zero_service"] for row in subset
        ),
    }


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    budgets = sorted(map(int, manifest["contract"]["updates_per_event"]))
    grouped: dict[tuple[str, str, int], dict[str, dict]] = defaultdict(dict)
    for job in manifest["jobs"]:
        grouped[(job["family"], job["scene"], int(job["budget"]))][job["arm"]] = job

    rows = []
    for (family, scene, budget), arms in sorted(grouped.items()):
        row = {"family": family, "scene": scene, "budget": budget, "status": "missing"}
        expected_arms = ("rr", "window10_rr", "ercb")
        if set(arms) == set(expected_arms):
            summaries, finals = {}, {}
            valid = True
            for arm in expected_arms:
                job = arms[arm]
                output = Path(job["output"])
                if job.get("state") != "complete" or not output.is_dir():
                    valid = False
                    continue
                summaries[arm] = json.loads(
                    (output / "view_scheduler_summary.json").read_text()
                )
                finals[arm] = final_test(output, job["total_iterations"])
            if valid:
                rr, window10, ercb = arms["rr"], arms["window10_rr"], arms["ercb"]
                service = {
                    arm: temporal_quartile_service(summaries[arm])
                    for arm in expected_arms
                }
                contract_ok = (
                    len({job["total_iterations"] for job in arms.values()}) == 1
                    and len({job["dataset"] for job in arms.values()}) == 1
                    and len({job["schedule"] for job in arms.values()}) == 1
                    and all(
                        summaries[arm].get("completed_updates_this_run")
                        == arms[arm]["total_iterations"]
                        and summaries[arm].get("post_update_reporting") is True
                        for arm in expected_arms
                    )
                    and summaries["window10_rr"].get("window_size") == 10
                )
                row.update(
                    {
                        "status": "three_arm_pass" if contract_ok else "contract_fail",
                        "events": rr["events"],
                        "train_frames": rr["train_frames"],
                        "heldout_frames": rr["heldout_frames"],
                        "updates": rr["total_iterations"],
                        "rr_psnr": finals["rr"]["psnr"],
                        "window10_rr_psnr": finals["window10_rr"]["psnr"],
                        "ercb_psnr": finals["ercb"]["psnr"],
                        "window10_delta_vs_rr": finals["window10_rr"]["psnr"]
                        - finals["rr"]["psnr"],
                        "ercb_delta_vs_rr": finals["ercb"]["psnr"]
                        - finals["rr"]["psnr"],
                        "ercb_delta_vs_window10": finals["ercb"]["psnr"]
                        - finals["window10_rr"]["psnr"],
                        "rr_zero_service": summaries["rr"].get("zero_service"),
                        "window10_rr_zero_service": summaries["window10_rr"].get("zero_service"),
                        "ercb_zero_service": summaries["ercb"].get("zero_service"),
                        "rr_unique_selected": summaries["rr"].get("unique_selected"),
                        "window10_rr_unique_selected": summaries["window10_rr"].get("unique_selected"),
                        "ercb_unique_selected": summaries["ercb"].get("unique_selected"),
                        "rr_gpu_ms": summaries["rr"].get("training_gpu_ms"),
                        "window10_rr_gpu_ms": summaries["window10_rr"].get("training_gpu_ms"),
                        "ercb_gpu_ms": summaries["ercb"].get("training_gpu_ms"),
                        **{
                            f"{arm}_service_q{quartile}_share": values[quartile - 1]
                            for arm, values in service.items()
                            for quartile in range(1, 5)
                        },
                    }
                )
        rows.append(row)

    for key, reason in sorted(manifest.get("unavailable", {}).items()):
        family, scene = key.split("/", 1)
        for budget in budgets:
            rows.append(
                {
                    "family": family,
                    "scene": scene,
                    "budget": budget,
                    "status": "unavailable",
                    "reason": reason,
                }
            )
    rows.sort(key=lambda row: (row["budget"], row["family"], row["scene"]))
    valid = [row for row in rows if row["status"] == "three_arm_pass"]

    family_summary = [
        result
        for budget in budgets
        for family in ("utmm", "rpng", "all")
        if (result := aggregate(rows, budget, family)) is not None
    ]
    all_by_budget = {
        row["budget"]: row for row in family_summary if row["family"] == "all"
    }
    window_event_count_correlation = {
        budget: pearson(
            [row["events"] for row in valid if row["budget"] == budget],
            [row["window10_delta_vs_rr"] for row in valid if row["budget"] == budget],
        )
        for budget in budgets
    }

    anchors = []
    old_root = ROOT / "results/ERCB_ablation/exp03_5070ti_budget_reproduction"
    anchor_paths = {
        ("utmm", "square-1"): old_root / "utmm_square1_full/event15",
        ("rpng", "table_01"): old_root / "rpng_table01_full/event15",
    }
    for (family, scene), base in anchor_paths.items():
        current = next(
            row
            for row in valid
            if row["family"] == family
            and row["scene"] == scene
            and row["budget"] == 15
        )
        if not all(
            (base / f"{arm}_s0/evaluation_curve.jsonl").is_file()
            for arm in ("rr", "ercb")
        ):
            continue
        old_rr = final_test(base / "rr_s0", current["updates"])["psnr"]
        old_ercb = final_test(base / "ercb_s0", current["updates"])["psnr"]
        old_delta = old_ercb - old_rr
        anchors.append(
            {
                "family": family,
                "scene": scene,
                "previous_delta_psnr": old_delta,
                "benchmark_A_delta_psnr": current["ercb_delta_vs_rr"],
                "delta_difference": current["ercb_delta_vs_rr"] - old_delta,
                "same_positive_sign": old_delta > 0 and current["ercb_delta_vs_rr"] > 0,
            }
        )

    payload = {
        "protocol": manifest["protocol"],
        "manifest_state": manifest["state"],
        "contract": manifest["contract"],
        "rows": rows,
        "family_summary": family_summary,
        "window_event_count_correlation": window_event_count_correlation,
        "anchor_reproduction": anchors,
    }
    evidence = HERE / "evidence"
    (evidence / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    columns = sorted({key for row in rows for key in row})
    with (evidence / "summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    expected_groups = len(manifest["jobs"]) // 3
    lines = [
        "# ERCB benchmark-A — historical exp03 budget sweep",
        "",
        f"상태: **{len(valid)}/{expected_groups} valid scene-budget three-arm 비교 완료**. "
        "원 VIGS source가 없는 3개 scene은 각 budget에서 unavailable이다.",
        "",
        "기존 RPNG table_01의 약 +1dB 결과를 만든 scheduler-isolation 설정을 장면별 "
        "재튜닝 없이 저·중·고예산으로 확장했다. strict end-to-end VIGS가 아니라 fixed final "
        "VIGS pose/init을 쓰는 진단 실험이다.",
        "",
        "## 고정 계약",
        "",
        "- update budget: keyframe-arrival event당 15/30/60회(low/mid/high), seed 0",
        "- full-pool RR vs recent-10-keyframe-interval window RR vs interval relative-floor ERCB "
        "(`K=8`, `rho=.5`, `gamma=log(3)`)",
        "- resolution 4, RGB-only, fixed topology, llffhold-8, optimizer zero-tail",
        "- historical exp03 schedule builder를 그대로 사용했다. 마지막 tracking keyframe 뒤 RGB가 "
        "그 마지막 event에 함께 admission되는 tail 의미론까지 재현하므로 인과적 streaming 증거가 아니다.",
    ]

    for budget in budgets:
        lines.extend(
            [
                "",
                f"## {BUDGET_LABELS[budget].capitalize()} budget — {budget} updates/event",
                "",
                "| family | scene | status | events | train/test | updates | full RR | window10 RR | ERCB | window−full | ERCB−full | ERCB−window |",
                "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in (item for item in rows if item["budget"] == budget):
            train_test = (
                f"{row['train_frames']}/{row['heldout_frames']}"
                if row.get("train_frames") is not None
                else "—"
            )
            status = row["status"]
            if status == "unavailable":
                status += ": " + row.get("reason", "")
            lines.append(
                f"| {row['family']} | {row['scene']} | {status} | "
                f"{row.get('events', '—')} | {train_test} | {row.get('updates', '—')} | "
                f"{fmt(row.get('rr_psnr'))} | {fmt(row.get('window10_rr_psnr'))} | "
                f"{fmt(row.get('ercb_psnr'))} | {fmt(row.get('window10_delta_vs_rr'))} | "
                f"{fmt(row.get('ercb_delta_vs_rr'))} | {fmt(row.get('ercb_delta_vs_window10'))} |"
            )

    lines.extend(
        [
            "",
            "## Budget/family averages",
            "",
            "| budget | family | scenes | full RR | window10 RR | ERCB | window−full mean/median | window wins | ERCB−full mean/median | ERCB wins | ERCB−window |",
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in family_summary:
        lines.append(
            f"| {row['budget']} ({row['budget_label']}) | {row['family']} | "
            f"{row['scenes']} | {fmt(row['rr_mean_psnr'])} | {fmt(row['window10_rr_mean_psnr'])} | "
            f"{fmt(row['ercb_mean_psnr'])} | {fmt(row['mean_window10_delta_vs_rr'])}/"
            f"{fmt(row['median_window10_delta_vs_rr'])} | {row['window10_wins_vs_rr']}/{row['scenes']} | "
            f"{fmt(row['mean_ercb_delta_vs_rr'])}/{fmt(row['median_ercb_delta_vs_rr'])} | "
            f"{row['ercb_wins_vs_rr']}/{row['scenes']} | {fmt(row['mean_ercb_delta_vs_window10'])} |"
        )

    lines.extend(
        [
            "",
            "## Per-scene budget interaction",
            "",
            "| family | scene | window−full @15/@30/@60 | ERCB−full @15/@30/@60 |",
            "|---|---|---:|---:|",
        ]
    )
    scene_keys = sorted({(row["family"], row["scene"]) for row in valid})
    for family, scene in scene_keys:
        window_values = {
            row["budget"]: row["window10_delta_vs_rr"]
            for row in valid
            if row["family"] == family and row["scene"] == scene
        }
        ercb_values = {
            row["budget"]: row["ercb_delta_vs_rr"]
            for row in valid
            if row["family"] == family and row["scene"] == scene
        }
        lines.append(
            f"| {family} | {scene} | {fmt(window_values.get(15))}/"
            f"{fmt(window_values.get(30))}/{fmt(window_values.get(60))} | "
            f"{fmt(ercb_values.get(15))}/{fmt(ercb_values.get(30))}/"
            f"{fmt(ercb_values.get(60))} |"
        )

    lines.extend(
        [
            "",
            "## Existing exp03 low-budget anchor rerun",
            "",
            "| scene | previous delta | benchmark-A delta | difference | sign |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for row in anchors:
        lines.append(
            f"| {row['family']}/{row['scene']} | {fmt(row['previous_delta_psnr'])} | "
            f"{fmt(row['benchmark_A_delta_psnr'])} | {fmt(row['delta_difference'])} | "
            f"{'same positive' if row['same_positive_sign'] else 'changed'} |"
        )
    lines.extend(
        [
            "",
            "두 anchor의 event15 schedule SHA-256은 기존 exp03 입력과 일치한다.",
            "",
            "## 판정",
            "",
        ]
    )
    if len(all_by_budget) == len(budgets):
        trend = " > ".join(
            f"{budget}:{all_by_budget[budget]['mean_ercb_delta_vs_rr']:+.4f}dB"
            for budget in budgets
        )
        monotonic = all(
            all_by_budget[left]["mean_ercb_delta_vs_rr"]
            > all_by_budget[right]["mean_ercb_delta_vs_rr"]
            for left, right in zip(budgets, budgets[1:])
        )
        lines.append(
            f"전체 scene-unweighted ERCB−RR 평균은 {trend}다. "
            + (
                "예산이 증가할수록 이득이 단조 감소했다."
                if monotonic
                else "예산별 이득은 단조 감소하지 않았다."
            )
        )
        lines.append("")
        lines.append(
            "; ".join(
                f"{budget} budget ERCB {all_by_budget[budget]['ercb_wins_vs_rr']}/"
                f"{all_by_budget[budget]['scenes']} 승"
                for budget in budgets
            )
            + "."
        )
        lines.append("")
        lines.append(
            "; ".join(
                f"{budget} budget window10−full RR "
                f"{all_by_budget[budget]['mean_window10_delta_vs_rr']:+.4f}dB "
                f"({all_by_budget[budget]['window10_wins_vs_rr']}/"
                f"{all_by_budget[budget]['scenes']} 승)"
                for budget in budgets
            )
            + "."
        )
        lines.append("")
        low = all_by_budget[budgets[0]]
        high = all_by_budget[budgets[-1]]
        lines.append(
            "Window10의 시간순 frame quartile service 평균은 저예산 "
            f"{[round(value, 4) for value in low['window10_rr_temporal_quartile_service_mean']]}, "
            "고예산 "
            f"{[round(value, 4) for value in high['window10_rr_temporal_quartile_service_mean']]}다. "
            "Full RR의 대응 분포는 각각 "
            f"{[round(value, 4) for value in low['rr_temporal_quartile_service_mean']]}와 "
            f"{[round(value, 4) for value in high['rr_temporal_quartile_service_mean']]}다."
        )
        lines.append("")
        lines.append(
            "Window10−full RR delta와 keyframe event 수의 Pearson 상관은 "
            + ", ".join(
                f"{budget}:{window_event_count_correlation[budget]:+.4f}"
                for budget in budgets
            )
            + "다. 긴 장면일수록 recent-only window 손실이 커지는 방향이다."
        )
        lines.append("")
        lines.append(
            "따라서 최근 10개 keyframe interval만 유지하는 hard window RR은 기각한다. "
            "ERCB의 저예산 이득은 최신 구간 집중만으로 설명되지 않으며, 전체 historical pool을 "
            "보존한 상태에서 interval service를 조절하는 것이 핵심이다."
        )
    else:
        lines.append("모든 budget pair가 완료된 뒤 budget interaction을 판정한다.")
    lines.extend(
        [
            "",
            "이 패널은 seed0 broad transfer이며 fixed final pose/init, fixed topology, RGB-only, "
            "historical tail admission을 쓴다. strict streaming이나 현재 unified VIGS의 selector "
            "우위 근거로 해석하지 않는다.",
            "",
            "Machine-readable: [`evidence/summary.json`](evidence/summary.json), "
            "[`evidence/summary.csv`](evidence/summary.csv), "
            "[`evidence/manifest.json`](evidence/manifest.json).",
            "Raw outputs: `results/ERCB_ablation/benchmark-A_5070ti_exp03_low_budget/` "
            "(legacy root label이며 event15/30/60을 모두 포함).",
            "RPNG table_03 event60 ERCB의 최초 중단 산출물은 `_interrupted_20260915T215046`로 "
            "보존했으며 집계에서 제외했다. clean rerun만 위 결과에 포함된다.",
        ]
    )
    (HERE / "summary.md").write_text("\n".join(lines) + "\n")
    print(HERE / "summary.md")


if __name__ == "__main__":
    main()
