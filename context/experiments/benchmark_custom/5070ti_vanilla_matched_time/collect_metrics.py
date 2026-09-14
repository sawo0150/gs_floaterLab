#!/usr/bin/env python3
"""Collect common-UID quality and physical B1 service for matched-time runs."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
HERE = LAB / "context/experiments/benchmark_custom/5070ti_vanilla_matched_time"
RESULTS = LAB / "results/benchmarks/benchmark_custom/5070ti_vanilla_matched_time"
BUDGETS = HERE / "evidence/budget_manifest.json"
ARMS = (
    ("rr", "rr_unified_pool_seed0"),
    ("ercb_relative_floor", "ercb_relative_floor_unified_pool_seed0"),
    ("rr_workcredit_r4", "rr_unified_pool_workcredit_r4_seed0"),
    (
        "ercb_relative_floor_workcredit_r4",
        "ercb_relative_floor_unified_pool_workcredit_r4_seed0",
    ),
    ("rr_workcredit_cycle_r4", "rr_unified_pool_workcredit_cycle_r4_seed0"),
    (
        "ercb_relative_floor_workcredit_cycle_r4",
        "ercb_relative_floor_unified_pool_workcredit_cycle_r4_seed0",
    ),
    (
        "view_uniform_k128_workcredit_cycle_r4",
        "view_uniform_k128_unified_pool_workcredit_cycle_r4_seed0",
    ),
    (
        "ercb_view_count_b002_k128_workcredit_cycle_r4",
        "ercb_view_count_b002_k128_unified_pool_workcredit_cycle_r4_seed0",
    ),
    (
        "ercb_view_count_b002_k32_workcredit_cycle_r4",
        "ercb_view_count_b002_k32_unified_pool_workcredit_cycle_r4_seed0",
    ),
    (
        "ercb_view_count_b002_k8_workcredit_cycle_r4",
        "ercb_view_count_b002_k8_unified_pool_workcredit_cycle_r4_seed0",
    ),
    (
        "ercb_base_workcredit_cycle_r4",
        "ercb_base_unified_pool_workcredit_cycle_r4_seed0",
    ),
    (
        "ercb_coverage1_workcredit_cycle_r4",
        "ercb_coverage1_unified_pool_workcredit_cycle_r4_seed0",
    ),
    ("rr_workcredit_cycle_r2", "rr_unified_pool_workcredit_cycle_r2_seed0"),
    (
        "ercb_relative_floor_workcredit_cycle_r2",
        "ercb_relative_floor_unified_pool_workcredit_cycle_r2_seed0",
    ),
)
PANEL = (
    ("rpng", "table_01"),
    ("utmm", "fast-straight"),
    ("utmm", "ego-drive"),
    ("utmm", "ego-centric-1"),
    ("rpng", "table_04"),
)
METRICS = ("psnr", "ssim", "lpips")


def non_keyframes(path: Path) -> dict[int, dict[str, float]]:
    payload = json.loads(path.read_text())
    return {
        int(row["frame_idx"]): {key: float(row[key]) for key in METRICS}
        for row in payload["per_view"]
        if not bool(row.get("is_keyframe", False))
    }


def means(rows: dict[int, dict[str, float]], uids: list[int]) -> dict[str, float]:
    return {
        key: sum(rows[uid][key] for uid in uids) / len(uids)
        for key in METRICS
    }


def mapping_summary(log_text: str) -> dict[str, str]:
    matches = re.findall(r"^MAP_ONLINE_SUMMARY (.+)$", log_text, re.MULTILINE)
    if not matches:
        return {}
    return dict(token.split("=", 1) for token in matches[-1].split() if "=" in token)


def stream_times(log_text: str) -> tuple[float | None, float | None]:
    first = re.findall(r"ONLINE_STREAM_FIRST_FRAME_EPOCH ([0-9.]+)", log_text)
    done = re.findall(r"ONLINE_LOOP_DONE_EPOCH ([0-9.]+)", log_text)
    if not first or not done:
        return None, None
    return float(first[-1]), float(done[-1])


def collect() -> list[dict]:
    budget_rows = {
        (row["family"], row["scene"]): row
        for row in json.loads(BUDGETS.read_text())["records"]
    }
    records = []
    for family, scene in PANEL:
        budget = budget_rows[(family, scene)]
        vanilla_path = Path(budget["vanilla_result_file"])
        for selector, output_name in ARMS:
            output = RESULTS / family / scene / output_name
            # Custom pure-online evaluation is intentionally written under
            # online_final; after_opt is the legacy vanilla artifact location.
            result_path = output / "psnr/online_final/final_result.json"
            audit_path = output / "sensor_eos_audit.json"
            log_path = output / "run.log"
            record = {
                "family": family,
                "scene": scene,
                "selector": selector,
                "status": "missing",
                "matched_replay_scale": budget["matched_replay_scale"],
                "matched_budget_s": budget["vanilla_mapping_elapsed_s"],
                "output_dir": str(output),
            }
            if result_path.is_file() and audit_path.is_file() and log_path.is_file():
                candidate = non_keyframes(result_path)
                vanilla = non_keyframes(vanilla_path)
                uids = sorted(set(candidate).intersection(vanilla))
                if not uids:
                    record["status"] = "metric_contract_fail"
                    records.append(record)
                    continue
                candidate_mean = means(candidate, uids)
                vanilla_mean = means(vanilla, uids)
                audit = json.loads(audit_path.read_text())
                log_text = log_path.read_text(errors="replace").replace("\r", "\n")
                service = mapping_summary(log_text)
                first, done = stream_times(log_text)
                elapsed = None if first is None or done is None else done - first
                zero_tail = (
                    int(audit.get("updates_completed_after_deadline", -1)) == 0
                    and int(
                        audit.get(
                            "topology_actions_completed_after_deadline", -1
                        )
                    )
                    == 0
                )
                expected_budget = float(budget["vanilla_mapping_elapsed_s"])
                budget_match = abs(float(audit.get("budget_seconds", -1.0)) - expected_budget) <= 1e-3
                counter_match = int(audit["completed_adam_steps"]) == int(
                    service.get("physical_adam_steps_total", -1)
                )
                record.update(
                    {
                        "status": (
                            "matched_pass"
                            if zero_tail and budget_match and counter_match
                            else "contract_fail"
                        ),
                        "common_uid_count": len(uids),
                        "custom_psnr": candidate_mean["psnr"],
                        "custom_ssim": candidate_mean["ssim"],
                        "custom_lpips": candidate_mean["lpips"],
                        "vanilla_psnr_common": vanilla_mean["psnr"],
                        "vanilla_ssim_common": vanilla_mean["ssim"],
                        "vanilla_lpips_common": vanilla_mean["lpips"],
                        "delta_psnr": candidate_mean["psnr"] - vanilla_mean["psnr"],
                        "delta_ssim": candidate_mean["ssim"] - vanilla_mean["ssim"],
                        "delta_lpips": candidate_mean["lpips"] - vanilla_mean["lpips"],
                        "online_loop_elapsed_s": elapsed,
                        "zero_tail": zero_tail,
                        "budget_match": budget_match,
                        "counter_match": counter_match,
                        "physical_adam_steps": int(audit["completed_adam_steps"]),
                        "summary_physical_adam_steps": int(
                            service.get("physical_adam_steps_total", 0)
                        ),
                        "keyframe_updates": int(service.get("keyframe_updates", 0)),
                        "dense_updates": int(service.get("dense_updates", 0)),
                        "dense_candidate_count": int(
                            service.get("dense_candidate_count", 0)
                        ),
                        "dense_selection_count_min": int(
                            service.get("dense_selection_count_min", 0)
                        ),
                        "dense_selection_count_p10": float(
                            service.get("dense_selection_count_p10", 0.0)
                        ),
                        "dense_selection_count_mean": float(
                            service.get("dense_selection_count_mean", 0.0)
                        ),
                        "dense_under_required": int(
                            service.get("dense_under_required", 0)
                        ),
                        "pending_keyframe_births": int(service.get("pending_keyframe_births", 0)),
                    }
                )
            elif log_path.is_file() and "Traceback (most recent call last):" in log_path.read_text(errors="replace"):
                record["status"] = "failed_incomplete"
            records.append(record)
    return records


def fmt(value: object, digits: int = 4) -> str:
    return "—" if value is None else f"{float(value):.{digits}f}"


def main() -> None:
    records = collect()
    evidence = HERE / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "summary.json").write_text(json.dumps({"records": records}, indent=2) + "\n")
    fields = sorted({key for row in records for key in row})
    with (evidence / "summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    lines = [
        "# 5070ti vanilla-matched-time 결과", "",
        "동일 UID는 양쪽 run에서 tracking keyframe이 아닌 frame의 교집합이다.",
        "`physical Adam`은 MAP_ONLINE_SUMMARY의 실제 B1 optimizer 완료 횟수다.", "",
        "| family | scene | selector | status | scale | budget(s) | common | PSNR | vanilla | delta | SSIM delta | LPIPS delta | physical Adam | KF upd | dense upd | loop(s) |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in records:
        lines.append(
            f"| {row['family']} | {row['scene']} | {row['selector']} | {row['status']} | "
            f"{fmt(row.get('matched_replay_scale'), 3)} | {fmt(row.get('matched_budget_s'), 2)} | "
            f"{row.get('common_uid_count', '—')} | {fmt(row.get('custom_psnr'))} | "
            f"{fmt(row.get('vanilla_psnr_common'))} | {fmt(row.get('delta_psnr'))} | "
            f"{fmt(row.get('delta_ssim'), 5)} | {fmt(row.get('delta_lpips'), 5)} | "
            f"{row.get('physical_adam_steps', '—')} | {row.get('keyframe_updates', '—')} | "
            f"{row.get('dense_updates', '—')} | {fmt(row.get('online_loop_elapsed_s'), 2)} |"
        )
    (HERE / "summary.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
