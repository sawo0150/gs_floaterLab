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


def main() -> int:
    rows: list[dict] = []
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
        "acceptance": acceptance,
        "original_x4_gate_note": (
            "The earlier X4 gate is not retroactively changed: 10 valid confirmation "
            "scenes averaged +0.9516012797 dB, while slow-straight-1 was N/A and "
            "the five-scene UTMM confirmation mean was +0.4686755789 dB."
        ),
    }
    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
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
    print(json.dumps(summary["aggregates"], indent=2, sort_keys=True))
    print(json.dumps(acceptance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
