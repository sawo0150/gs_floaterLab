#!/usr/bin/env python3
"""Build the frozen R4 all-local-scene result tables from verifier artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from statistics import mean


WORKSPACE = Path(__file__).resolve().parents[4]
RAW = WORKSPACE / "results/experiments/exp78/paper_full_staged_v1"
OUTPUT = Path(__file__).resolve().parent

# dataset, scene, role, verifier path relative to RAW
REPORTS = (
    ("rpng", "table_01", "development", "stage6r_r4_native_global_keyframe/rpng/table_01/verification/r4_render_match.json"),
    ("rpng", "table_02", "previously_exposed_validation", "stage6r_all_scenes_fixed_work/rpng/table_02/verification/stage6rx4_render_match_s0.json"),
    ("rpng", "table_03", "confirmation", "stage6rx4_cross_sequence_confirmation/rpng/table_03/verification/stage6rx4_render_match_s0.json"),
    ("rpng", "table_04", "confirmation", "stage6rx4_cross_sequence_confirmation/rpng/table_04/verification/stage6rx4_render_match_s0.json"),
    ("rpng", "table_05", "confirmation", "stage6rx4_cross_sequence_confirmation/rpng/table_05/verification/stage6rx4_render_match_s0.json"),
    ("rpng", "table_06", "development", "stage6r_all_scenes_fixed_work/rpng/table_06/verification/stage6rx4_render_match_s0.json"),
    ("rpng", "table_07", "confirmation", "stage6rx4_cross_sequence_confirmation/rpng/table_07/verification/stage6rx4_render_match_s0_v2.json"),
    ("rpng", "table_08", "confirmation", "stage6rx4_cross_sequence_confirmation/rpng/table_08/verification/stage6rx4_render_match_s0.json"),
    ("utmm", "ego-centric-1", "confirmation", "stage6rx4_cross_sequence_confirmation/utmm/ego-centric-1/verification/stage6rx4_render_match_s0.json"),
    ("utmm", "ego-centric-2", "confirmation", "stage6rx4_cross_sequence_confirmation/utmm/ego-centric-2/verification/stage6rx4_render_match_s0.json"),
    ("utmm", "ego-drive", "development", "stage6r_all_scenes_fixed_work/utmm/ego-drive/verification/stage6rx4_render_match_s0.json"),
    ("utmm", "fast-straight", "confirmation", "stage6rx4_cross_sequence_confirmation/utmm/fast-straight/verification/stage6rx4_render_match_s0_v2.json"),
    ("utmm", "slow-straight-2", "confirmation", "stage6rx4_cross_sequence_confirmation/utmm/slow-straight-2/verification/stage6rx4_render_match_s0.json"),
    ("utmm", "square-1", "confirmation", "stage6rx4_cross_sequence_confirmation/utmm/square-1/verification/stage6rx4_render_match_s0.json"),
    ("utmm", "square-2", "development", "stage6r_all_scenes_fixed_work/utmm/square-2/verification/stage6rx4_render_match_s0.json"),
    ("aria", "aria1253", "development", "stage6r_all_scenes_fixed_work/aria/aria1253/verification/stage6rx4_render_match_s0.json"),
    ("aria", "aria301_305", "transfer", "stage6r_all_scenes_fixed_work/aria/aria301_305/verification/stage6rx4_render_match_s0.json"),
)

CSV_FIELDS = (
    "dataset",
    "scene",
    "role",
    "status",
    "views",
    "candidate_psnr",
    "vanilla_psnr",
    "delta_psnr",
    "candidate_ssim",
    "vanilla_ssim",
    "delta_ssim",
    "candidate_lpips",
    "vanilla_lpips",
    "delta_lpips",
    "renders_each",
    "candidate_optimizer_steps",
    "vanilla_optimizer_steps",
    "candidate_gaussians",
    "vanilla_gaussians",
    "mapping_services_each",
    "verifier_checks_passed",
    "verifier_checks_total",
    "report",
    "note",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_manifest(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def aggregate(rows: list[dict]) -> dict:
    total_views = sum(int(row["views"]) for row in rows)
    return {
        "valid_scenes": len(rows),
        "positive_scenes": sum(float(row["delta_psnr"]) > 0.0 for row in rows),
        "views": total_views,
        "candidate_psnr_scene_mean": mean(float(row["candidate_psnr"]) for row in rows),
        "vanilla_psnr_scene_mean": mean(float(row["vanilla_psnr"]) for row in rows),
        "delta_psnr_scene_mean": mean(float(row["delta_psnr"]) for row in rows),
        "delta_psnr_view_weighted": sum(
            float(row["delta_psnr"]) * int(row["views"]) for row in rows
        ) / total_views,
        "delta_ssim_scene_mean": mean(float(row["delta_ssim"]) for row in rows),
        "delta_lpips_scene_mean": mean(float(row["delta_lpips"]) for row in rows),
    }


def aggregate_timing(rows: list[dict]) -> dict:
    candidate_wall = sum(float(row["candidate_wall_seconds"]) for row in rows)
    vanilla_wall = sum(float(row["vanilla_wall_seconds"]) for row in rows)
    candidate_adam = sum(int(row["candidate_optimizer_steps"]) for row in rows)
    vanilla_adam = sum(int(row["vanilla_optimizer_steps"]) for row in rows)
    renders = sum(int(row["renders_each"]) for row in rows)
    return {
        "valid_scenes": len(rows),
        "candidate_faster_scenes": sum(
            float(row["candidate_wall_seconds"])
            < float(row["vanilla_wall_seconds"])
            for row in rows
        ),
        "mean_final_gaussian_ratio": mean(
            float(row["candidate_gaussians"]) / float(row["vanilla_gaussians"])
            for row in rows
        ),
        "candidate_wall_seconds": candidate_wall,
        "vanilla_wall_seconds": vanilla_wall,
        "wall_ratio": candidate_wall / vanilla_wall,
        "candidate_ms_per_adam": 1000.0 * candidate_wall / candidate_adam,
        "vanilla_ms_per_adam": 1000.0 * vanilla_wall / vanilla_adam,
        "candidate_ms_per_render": 1000.0 * candidate_wall / renders,
        "vanilla_ms_per_render": 1000.0 * vanilla_wall / renders,
        "candidate_map_calls": sum(int(row["candidate_map_calls"]) for row in rows),
        "vanilla_map_calls": sum(int(row["vanilla_map_calls"]) for row in rows),
    }


def fmt(value: float, digits: int = 4) -> str:
    return f"{float(value):.{digits}f}"


def signed(value: float, digits: int = 4) -> str:
    return f"{float(value):+.{digits}f}"


def render_summary_markdown(summary: dict) -> str:
    overall = summary["aggregates"]["overall"]
    acceptance = summary["acceptance"]
    rows = summary["rows"]
    na = summary["n_a"][0]
    timing = summary["timing"]
    lines = [
        "# R4 all-scene fixed-work 요약",
        "",
        f"날짜: {summary['date']}",
        "",
        f"범위: {summary['scope']}",
        "",
        "## 결론",
        "",
        f"- 계획 {summary['planned_scenes']}개 중 유효 {summary['valid_scenes']}개, "
        f"N/A {summary['n_a_scenes']}개",
        f"- 유효 장면 PSNR 승리: {overall['positive_scenes']}/{overall['valid_scenes']}",
        f"- scene-mean PSNR: R4 **{fmt(overall['candidate_psnr_scene_mean'])} dB**, "
        f"vanilla **{fmt(overall['vanilla_psnr_scene_mean'])} dB**, "
        f"delta **{signed(overall['delta_psnr_scene_mean'])} dB**",
        f"- view-weighted PSNR delta: **{signed(overall['delta_psnr_view_weighted'])} dB** "
        f"({overall['views']:,} views)",
        f"- scene-mean SSIM/LPIPS delta: "
        f"**{signed(overall['delta_ssim_scene_mean'], 5)} / "
        f"{signed(overall['delta_lpips_scene_mean'], 5)}**",
        f"- prospective all-scene acceptance: **{'PASS' if acceptance['passed'] else 'HOLD'}**",
        "",
        "## 데이터셋별 집계",
        "",
        "| Dataset | 유효 | 승리 | Views | R4 PSNR | Vanilla PSNR | ΔPSNR | View-weighted ΔPSNR | ΔSSIM | ΔLPIPS |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for dataset in ("rpng", "utmm", "aria"):
        item = summary["aggregates"]["by_dataset"][dataset]
        lines.append(
            f"| {dataset.upper()} | {item['valid_scenes']} | {item['positive_scenes']} | "
            f"{item['views']:,} | {fmt(item['candidate_psnr_scene_mean'])} | "
            f"{fmt(item['vanilla_psnr_scene_mean'])} | "
            f"**{signed(item['delta_psnr_scene_mean'])}** | "
            f"{signed(item['delta_psnr_view_weighted'])} | "
            f"{signed(item['delta_ssim_scene_mean'], 5)} | "
            f"{signed(item['delta_lpips_scene_mean'], 5)} |"
        )

    lines.extend(
        [
            "",
            "## Role별 집계",
            "",
            "| Role | 유효 | 승리 | Views | R4 PSNR | Vanilla PSNR | ΔPSNR |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for role, item in summary["aggregates"]["by_role"].items():
        lines.append(
            f"| `{role}` | {item['valid_scenes']} | {item['positive_scenes']} | "
            f"{item['views']:,} | {fmt(item['candidate_psnr_scene_mean'])} | "
            f"{fmt(item['vanilla_psnr_scene_mean'])} | "
            f"**{signed(item['delta_psnr_scene_mean'])}** |"
        )

    lines.extend(
        [
            "",
            "## 장면별 품질",
            "",
            "LPIPS는 낮을수록 좋다.",
            "",
            "| Dataset | Scene | Role | Views | R4 PSNR | Vanilla PSNR | ΔPSNR | ΔSSIM | ΔLPIPS |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['dataset'].upper()} | `{row['scene']}` | `{row['role']}` | "
            f"{int(row['views']):,} | {fmt(row['candidate_psnr'])} | "
            f"{fmt(row['vanilla_psnr'])} | **{signed(row['delta_psnr'])}** | "
            f"{signed(row['delta_ssim'], 5)} | {signed(row['delta_lpips'], 5)} |"
        )
    lines.append(
        f"| {na['dataset'].upper()} | `{na['scene']}` | `{na['role']}` | "
        f"{int(na['views']):,} | N/A | N/A | N/A | N/A | N/A |"
    )

    lines.extend(
        [
            "",
            "## 장면별 work와 모델 규모",
            "",
            "| Dataset | Scene | Renders/arm | Adam R4/vanilla | GS R4/vanilla | Mapping services | Verifier |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['dataset'].upper()} | `{row['scene']}` | "
            f"{int(row['renders_each']):,} | "
            f"{int(row['candidate_optimizer_steps']):,}/{int(row['vanilla_optimizer_steps']):,} | "
            f"{int(row['candidate_gaussians']):,}/{int(row['vanilla_gaussians']):,} | "
            f"{int(row['mapping_services_each']):,} | "
            f"{int(row['verifier_checks_passed'])}/{int(row['verifier_checks_total'])} |"
        )

    lines.extend(
        [
            "",
            "## Acceptance와 예외",
            "",
            f"적용한 사전 기준은 `{acceptance['prospective_rule']}`이다.",
            "",
            f"- 평균 ΔPSNR ≥ {acceptance['mean_delta_threshold_db']:.1f} dB: "
            f"**{'PASS' if acceptance['mean_delta_pass'] else 'HOLD'}**",
            f"- strict majority positive: "
            f"**{'PASS' if acceptance['strict_majority_pass'] else 'HOLD'}**",
            f"- 모든 포함 pair fairness valid: "
            f"**{'PASS' if acceptance['fairness_pass'] else 'HOLD'}**",
            f"- UTMM `{na['scene']}` N/A: {na['note']}.",
            "",
            "원래 X4 gate는 사후 변경하지 않았다. 유효 confirmation 10개 평균은 "
            "+0.951601 dB였지만 UTMM confirmation 5개 평균은 +0.468676 dB였고, "
            "`slow-straight-1`은 N/A였으므로 원래 gate는 HOLD다.",
            "",
            "## 범위와 원본",
            "",
            "이 결과는 B-track mapping-only fixed-work 결과다. C-track strict live-time, "
            "27 dB milestone, region-GT/floater 개선을 증명하지 않는다.",
            "",
            "- 장면별 정규화 행: [`summary.csv`](summary.csv)",
            "- verifier, source manifest, 실행 경로와 SHA: [`provenance.json`](provenance.json)",
            "- 해석과 프로토콜 상세: [`README.md`](README.md)",
            "",
            "이 파일은 `build_summary.py`가 원시 verifier artifact에서 생성한다.",
            "",
            "## Gaussian 수와 mapping 시간 감사",
            "",
            "아래 시간은 기존 unbounded B-track 로그의 `mapping_wall_seconds`를 집계한 "
            "것이다. 각 pair는 physical training render 수가 정확히 같지만, R4와 "
            "vanilla의 Adam step 및 gradient scope는 같지 않다. 따라서 `ms/Adam`과 "
            "`ms/render`는 CUDA kernel 자체의 순수 시간이 아니라 mapping 전체 wall-time "
            "proxy다.",
            "",
            "| Dataset | Scenes | Mean final GS R4/vanilla | Mapping wall R4/vanilla (s) | Wall ratio | ms/Adam R4/vanilla | ms/render R4/vanilla | map() calls R4/vanilla |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for dataset in ("rpng", "utmm", "aria"):
        item = timing["by_dataset"][dataset]
        lines.append(
            f"| {dataset.upper()} | {item['valid_scenes']} | "
            f"{item['mean_final_gaussian_ratio']:.3f}× | "
            f"{item['candidate_wall_seconds']:.3f}/{item['vanilla_wall_seconds']:.3f} | "
            f"{item['wall_ratio']:.3f}× | "
            f"{item['candidate_ms_per_adam']:.3f}/{item['vanilla_ms_per_adam']:.3f} | "
            f"{item['candidate_ms_per_render']:.3f}/{item['vanilla_ms_per_render']:.3f} | "
            f"{item['candidate_map_calls']:,}/{item['vanilla_map_calls']:,} |"
        )
    timing_all = timing["overall"]
    lines.append(
        f"| **전체** | **{timing_all['valid_scenes']}** | "
        f"**{timing_all['mean_final_gaussian_ratio']:.3f}×** | "
        f"**{timing_all['candidate_wall_seconds']:.3f}/"
        f"{timing_all['vanilla_wall_seconds']:.3f}** | "
        f"**{timing_all['wall_ratio']:.3f}×** | "
        f"**{timing_all['candidate_ms_per_adam']:.3f}/"
        f"{timing_all['vanilla_ms_per_adam']:.3f}** | "
        f"**{timing_all['candidate_ms_per_render']:.3f}/"
        f"{timing_all['vanilla_ms_per_render']:.3f}** | "
        f"**{timing_all['candidate_map_calls']:,}/"
        f"{timing_all['vanilla_map_calls']:,}** |"
    )
    table01 = next(
        row for row in timing["rows"]
        if row["dataset"] == "rpng" and row["scene"] == "table_01"
    )
    lines.extend(
        [
            "",
            f"전체적으로 R4의 scene별 최종 Gaussian 비율 평균은 "
            f"**{timing_all['mean_final_gaussian_ratio']:.3f}×**였지만, mapping wall은 "
            f"**{timing_all['wall_ratio']:.3f}×**, 즉 "
            f"**{(timing_all['wall_ratio'] - 1.0) * 100:+.1f}%**에 그쳤다. "
            f"R4가 빠른 장면은 {timing_all['candidate_faster_scenes']}/"
            f"{timing_all['valid_scenes']}개, 느린 장면은 "
            f"{timing_all['valid_scenes'] - timing_all['candidate_faster_scenes']}/"
            f"{timing_all['valid_scenes']}개였다.",
            "",
            "최종 Gaussian 수만으로 시간 차이를 설명할 수 없다. RPNG는 최종 GS가 "
            f"{timing['by_dataset']['rpng']['mean_final_gaussian_ratio']:.3f}×인데 wall은 "
            f"{timing['by_dataset']['rpng']['wall_ratio']:.3f}×였고, UTMM은 GS가 "
            f"{timing['by_dataset']['utmm']['mean_final_gaussian_ratio']:.3f}×로 더 적은데 "
            f"wall은 {timing['by_dataset']['utmm']['wall_ratio']:.3f}×였다. Aria는 GS가 "
            f"{timing['by_dataset']['aria']['mean_final_gaussian_ratio']:.3f}×로 비슷하지만 "
            f"wall은 {timing['by_dataset']['aria']['wall_ratio']:.3f}×였다.",
            "",
            "이유는 (1) 최종 GS 수는 실행 중 평균이나 view별 visible/touched splat 수가 "
            "아니고, (2) R4의 dense/KF 보조 update는 appearance-only인 반면 vanilla는 "
            "native full-gradient update이며, (3) R4는 frontier/dense/KF service를 분리해 "
            f"전체 `map()` 호출이 {timing_all['candidate_map_calls']:,}회로 vanilla "
            f"{timing_all['vanilla_map_calls']:,}회의 약 "
            f"{timing_all['candidate_map_calls'] / timing_all['vanilla_map_calls']:.2f}배이고, "
            "(4) PGBA pose refresh, C1/ERCB 장부, densify/prune 및 topology overhead도 "
            "wall-time에 포함되기 때문이다.",
            "",
            f"메모리 영향은 명확하다. RPNG `table_01`은 최종 GS "
            f"{int(table01['candidate_gaussians']):,}/{int(table01['vanilla_gaussians']):,} "
            f"({float(table01['candidate_gaussians']) / float(table01['vanilla_gaussians']):.3f}×), "
            f"peak CUDA allocated "
            f"{float(table01['candidate_peak_cuda_bytes']) / 1e9:.2f}/"
            f"{float(table01['vanilla_peak_cuda_bytes']) / 1e9:.2f} GB였지만, mapping wall은 "
            f"{float(table01['candidate_wall_seconds']):.3f}/"
            f"{float(table01['vanilla_wall_seconds']):.3f}초로 오히려 R4가 "
            f"{(1.0 - float(table01['candidate_wall_seconds']) / float(table01['vanilla_wall_seconds'])) * 100:.1f}% "
            "빨랐다. 현재 증거에서 Gaussian 증가는 속도보다 메모리 압력에 더 직접적으로 "
            "나타난다.",
            "",
            "이 감사만으로 C-track에서 tracking과 GPU를 경쟁할 때의 deadline 영향이나 "
            "Gaussian 수의 순수 인과 효과를 증명하지 않는다. 후자를 분리하려면 동일 R4 "
            "경로에서 Gaussian capacity만 바꾼 profiler pair가 필요하다.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    rows: list[dict] = []
    timing_rows: list[dict] = []
    provenance: list[dict] = []
    for dataset, scene, role, relative_report in REPORTS:
        report_path = RAW / relative_report
        report = read_json(report_path)
        checks = report["checks"]
        passed = sum(value.get("passed") is True for value in checks.values())
        if report.get("valid") is not True or passed != len(checks):
            raise RuntimeError(f"invalid verifier report: {report_path}")
        result = report["result"]
        candidate = result["d1"]
        vanilla = result["vanilla"]
        delta = result["d1_minus_vanilla"]
        candidate_run = Path(report["d1_run"])
        vanilla_run = Path(report["vanilla_run"])
        candidate_runtime = read_json(candidate_run / "mapping_replay_runtime.json")
        vanilla_runtime = read_json(vanilla_run / "mapping_replay_runtime.json")
        if (
            int(candidate_runtime["rasterized_view_updates"]) != int(candidate["renders"])
            or int(vanilla_runtime["rasterized_view_updates"]) != int(vanilla["renders"])
            or int(candidate_runtime["rasterized_view_updates"])
            != int(vanilla_runtime["rasterized_view_updates"])
        ):
            raise RuntimeError(f"runtime render mismatch: {report_path}")
        evaluation = read_json(
            candidate_run / "psnr/strict_fixed_manifest/final_result.json"
        )["predeclared_fixed_manifest_posthoc"]
        if evaluation.get("mapping_disjoint") is not True:
            raise RuntimeError(f"mapping-held-out overlap: {candidate_run}")
        row = {
            "dataset": dataset,
            "scene": scene,
            "role": role,
            "status": "valid",
            "views": int(evaluation["view_count"]),
            "candidate_psnr": candidate["psnr"],
            "vanilla_psnr": vanilla["psnr"],
            "delta_psnr": delta["psnr"],
            "candidate_ssim": candidate["ssim"],
            "vanilla_ssim": vanilla["ssim"],
            "delta_ssim": delta["ssim"],
            "candidate_lpips": candidate["lpips"],
            "vanilla_lpips": vanilla["lpips"],
            "delta_lpips": delta["lpips"],
            "renders_each": candidate["renders"],
            "candidate_optimizer_steps": candidate["optimizer_steps"],
            "vanilla_optimizer_steps": vanilla["optimizer_steps"],
            "candidate_gaussians": candidate["gaussians"],
            "vanilla_gaussians": vanilla["gaussians"],
            "mapping_services_each": checks["same_d1_mapping_service_trace"]["detail"]["d1_count"],
            "verifier_checks_passed": passed,
            "verifier_checks_total": len(checks),
            "report": str(report_path.relative_to(WORKSPACE)),
            "note": "table_01 exact R4 result reused" if scene == "table_01" else "",
        }
        rows.append(row)
        timing_rows.append(
            {
                "dataset": dataset,
                "scene": scene,
                "renders_each": int(candidate_runtime["rasterized_view_updates"]),
                "candidate_gaussians": int(candidate_runtime["gaussians"]),
                "vanilla_gaussians": int(vanilla_runtime["gaussians"]),
                "candidate_wall_seconds": float(candidate_runtime["mapping_wall_seconds"]),
                "vanilla_wall_seconds": float(vanilla_runtime["mapping_wall_seconds"]),
                "candidate_optimizer_steps": int(candidate_runtime["optimizer_steps_completed"]),
                "vanilla_optimizer_steps": int(vanilla_runtime["optimizer_steps_completed"]),
                "candidate_map_calls": int(candidate_runtime["map_calls"]),
                "vanilla_map_calls": int(vanilla_runtime["map_calls"]),
                "candidate_peak_cuda_bytes": int(candidate_runtime["peak_cuda_allocated_bytes"]),
                "vanilla_peak_cuda_bytes": int(vanilla_runtime["peak_cuda_allocated_bytes"]),
            }
        )
        candidate_manifest = candidate_run / "source_manifest.txt"
        vanilla_manifest = vanilla_run / "source_manifest.txt"
        provenance.append(
            {
                "dataset": dataset,
                "scene": scene,
                "verifier": str(report_path.relative_to(WORKSPACE)),
                "verifier_sha256": sha256(report_path),
                "candidate_run": str(candidate_run.relative_to(WORKSPACE)),
                "candidate_source_manifest_sha256": sha256(candidate_manifest),
                "candidate_source": parse_manifest(candidate_manifest),
                "vanilla_run": str(vanilla_run.relative_to(WORKSPACE)),
                "vanilla_source_manifest_sha256": sha256(vanilla_manifest),
                "vanilla_source": parse_manifest(vanilla_manifest),
            }
        )

    na_row = {field: "" for field in CSV_FIELDS}
    na_row.update(
        {
            "dataset": "utmm",
            "scene": "slow-straight-1",
            "role": "confirmation",
            "status": "N/A",
            "views": 80,
            "note": (
                "tracker-ineligible: 0 metric_rescale events and no IMU metric "
                "initialization, so mapping-after-metric-init admits no map for either arm"
            ),
            "report": (
                "results/experiments/exp78/b_strict_fair_comparison/frozen_tracker/"
                "official_22ffe24_trt/utmm/slow-straight-1/seed0/capture_runtime.json"
            ),
        }
    )
    csv_rows = rows + [na_row]
    with (OUTPUT / "summary.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(csv_rows)

    by_dataset = {
        dataset: aggregate([row for row in rows if row["dataset"] == dataset])
        for dataset in ("rpng", "utmm", "aria")
    }
    by_role = {
        role: aggregate([row for row in rows if row["role"] == role])
        for role in sorted({row["role"] for row in rows})
    }
    overall = aggregate(rows)
    timing_by_dataset = {
        dataset: aggregate_timing(
            [row for row in timing_rows if row["dataset"] == dataset]
        )
        for dataset in ("rpng", "utmm", "aria")
    }
    acceptance = {
        "prospective_rule": (
            "valid-scene arithmetic mean delta PSNR >= +0.5 dB, strict majority "
            "positive, and every included pair passes all fairness checks"
        ),
        "mean_delta_threshold_db": 0.5,
        "mean_delta_pass": overall["delta_psnr_scene_mean"] >= 0.5,
        "strict_majority_pass": overall["positive_scenes"] > len(rows) / 2,
        "fairness_pass": True,
    }
    acceptance["passed"] = all(
        acceptance[key]
        for key in ("mean_delta_pass", "strict_majority_pass", "fairness_pass")
    )
    summary = {
        "protocol": "exp78_r4_all_local_scenes_fixed_work_summary_v1",
        "date": "2026-09-15",
        "scope": "B-track mapping-only fixed-work; not C-track strict live-time",
        "planned_scenes": 18,
        "valid_scenes": len(rows),
        "n_a_scenes": 1,
        "n_a": [na_row],
        "rows": rows,
        "aggregates": {
            "overall": overall,
            "by_dataset": by_dataset,
            "by_role": by_role,
        },
        "timing": {
            "overall": aggregate_timing(timing_rows),
            "by_dataset": timing_by_dataset,
            "rows": timing_rows,
        },
        "acceptance": acceptance,
        "original_x4_gate_note": (
            "The earlier X4 gate is not retroactively changed: 10 valid confirmation "
            "scenes averaged +0.9516012797 dB, while slow-straight-1 was N/A and "
            "the five-scene UTMM confirmation mean was +0.4686755789 dB."
        ),
    }
    (OUTPUT / "summary.md").write_text(
        render_summary_markdown(summary), encoding="utf-8"
    )
    (OUTPUT / "provenance.json").write_text(
        json.dumps(
            {
                "protocol": "exp78_r4_all_local_scenes_provenance_v1",
                "execution_lab_commits": {
                    "rpng_utmm_extension": "d9a5dc9",
                    "aria": "a883104a7f71e531edc18b5b6b5d1bc0629c7cbf",
                },
                "paper_commit": "07a09aa7d3a1461f9d67106e45dc094f6c9724ee",
                "official_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996",
                "pairs": provenance,
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT / 'summary.md'}")
    print(f"acceptance={'PASS' if acceptance['passed'] else 'HOLD'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
