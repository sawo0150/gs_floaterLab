#!/usr/bin/env python3
"""Validate benchmark-A budget pairs and generate JSON, CSV, and summary.md."""

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


def aggregate(rows: list[dict], budget: int, family: str) -> dict | None:
    subset = [
        row
        for row in rows
        if row["status"] == "paired_pass"
        and row["budget"] == budget
        and (family == "all" or row["family"] == family)
    ]
    if not subset:
        return None
    deltas = [row["delta_psnr"] for row in subset]
    return {
        "budget": budget,
        "budget_label": BUDGET_LABELS[budget],
        "family": family,
        "scenes": len(subset),
        "rr_mean_psnr": statistics.fmean(row["rr_psnr"] for row in subset),
        "ercb_mean_psnr": statistics.fmean(row["ercb_psnr"] for row in subset),
        "mean_delta_psnr": statistics.fmean(deltas),
        "median_delta_psnr": statistics.median(deltas),
        "ercb_wins": sum(delta > 0 for delta in deltas),
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
        if set(arms) == {"rr", "ercb"}:
            summaries, finals = {}, {}
            valid = True
            for arm in ("rr", "ercb"):
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
                rr, ercb = arms["rr"], arms["ercb"]
                contract_ok = (
                    rr["total_iterations"] == ercb["total_iterations"]
                    and rr["dataset"] == ercb["dataset"]
                    and rr["schedule"] == ercb["schedule"]
                    and summaries["rr"].get("completed_updates_this_run")
                    == rr["total_iterations"]
                    and summaries["ercb"].get("completed_updates_this_run")
                    == ercb["total_iterations"]
                    and summaries["rr"].get("post_update_reporting") is True
                    and summaries["ercb"].get("post_update_reporting") is True
                )
                row.update(
                    {
                        "status": "paired_pass" if contract_ok else "contract_fail",
                        "events": rr["events"],
                        "train_frames": rr["train_frames"],
                        "heldout_frames": rr["heldout_frames"],
                        "updates": rr["total_iterations"],
                        "rr_psnr": finals["rr"]["psnr"],
                        "ercb_psnr": finals["ercb"]["psnr"],
                        "delta_psnr": finals["ercb"]["psnr"]
                        - finals["rr"]["psnr"],
                        "rr_zero_service": summaries["rr"].get("zero_service"),
                        "ercb_zero_service": summaries["ercb"].get("zero_service"),
                        "rr_unique_selected": summaries["rr"].get("unique_selected"),
                        "ercb_unique_selected": summaries["ercb"].get("unique_selected"),
                        "rr_gpu_ms": summaries["rr"].get("training_gpu_ms"),
                        "ercb_gpu_ms": summaries["ercb"].get("training_gpu_ms"),
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
    valid = [row for row in rows if row["status"] == "paired_pass"]

    family_summary = [
        result
        for budget in budgets
        for family in ("utmm", "rpng", "all")
        if (result := aggregate(rows, budget, family)) is not None
    ]
    all_by_budget = {
        row["budget"]: row for row in family_summary if row["family"] == "all"
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
                "benchmark_A_delta_psnr": current["delta_psnr"],
                "delta_difference": current["delta_psnr"] - old_delta,
                "same_positive_sign": old_delta > 0 and current["delta_psnr"] > 0,
            }
        )

    payload = {
        "protocol": manifest["protocol"],
        "manifest_state": manifest["state"],
        "contract": manifest["contract"],
        "rows": rows,
        "family_summary": family_summary,
        "anchor_reproduction": anchors,
    }
    evidence = HERE / "evidence"
    (evidence / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    columns = sorted({key for row in rows for key in row})
    with (evidence / "summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    expected_pairs = len(manifest["jobs"]) // 2
    lines = [
        "# ERCB benchmark-A — historical exp03 budget sweep",
        "",
        f"상태: **{len(valid)}/{expected_pairs} valid scene-budget pair 완료**. "
        "원 VIGS source가 없는 3개 scene은 각 budget에서 unavailable이다.",
        "",
        "기존 RPNG table_01의 약 +1dB 결과를 만든 scheduler-isolation 설정을 장면별 "
        "재튜닝 없이 저·중·고예산으로 확장했다. strict end-to-end VIGS가 아니라 fixed final "
        "VIGS pose/init을 쓰는 진단 실험이다.",
        "",
        "## 고정 계약",
        "",
        "- update budget: keyframe-arrival event당 15/30/60회(low/mid/high), seed 0",
        "- RR vs interval relative-floor ERCB (`K=8`, `rho=.5`, `gamma=log(3)`)",
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
                "| family | scene | status | events | train/test | updates | RR PSNR | ERCB PSNR | delta | zero-service RR/ERCB |",
                "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
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
            zero = (
                f"{row['rr_zero_service']}/{row['ercb_zero_service']}"
                if row.get("rr_zero_service") is not None
                else "—"
            )
            lines.append(
                f"| {row['family']} | {row['scene']} | {status} | "
                f"{row.get('events', '—')} | {train_test} | {row.get('updates', '—')} | "
                f"{fmt(row.get('rr_psnr'))} | {fmt(row.get('ercb_psnr'))} | "
                f"{fmt(row.get('delta_psnr'))} | {zero} |"
            )

    lines.extend(
        [
            "",
            "## Budget/family averages",
            "",
            "| budget | family | scenes | RR mean | ERCB mean | mean delta | median delta | ERCB wins |",
            "|---:|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in family_summary:
        lines.append(
            f"| {row['budget']} ({row['budget_label']}) | {row['family']} | "
            f"{row['scenes']} | {fmt(row['rr_mean_psnr'])} | {fmt(row['ercb_mean_psnr'])} | "
            f"{fmt(row['mean_delta_psnr'])} | {fmt(row['median_delta_psnr'])} | "
            f"{row['ercb_wins']}/{row['scenes']} |"
        )

    lines.extend(
        [
            "",
            "## Per-scene budget interaction",
            "",
            "| family | scene | delta@15 | delta@30 | delta@60 |",
            "|---|---|---:|---:|---:|",
        ]
    )
    scene_keys = sorted({(row["family"], row["scene"]) for row in valid})
    for family, scene in scene_keys:
        values = {
            row["budget"]: row["delta_psnr"]
            for row in valid
            if row["family"] == family and row["scene"] == scene
        }
        lines.append(
            f"| {family} | {scene} | {fmt(values.get(15))} | "
            f"{fmt(values.get(30))} | {fmt(values.get(60))} |"
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
            f"{budget}:{all_by_budget[budget]['mean_delta_psnr']:+.4f}dB"
            for budget in budgets
        )
        monotonic = all(
            all_by_budget[left]["mean_delta_psnr"]
            > all_by_budget[right]["mean_delta_psnr"]
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
                f"{budget} budget {all_by_budget[budget]['ercb_wins']}/"
                f"{all_by_budget[budget]['scenes']} 승"
                for budget in budgets
            )
            + "."
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
        ]
    )
    (HERE / "summary.md").write_text("\n".join(lines) + "\n")
    print(HERE / "summary.md")


if __name__ == "__main__":
    main()
