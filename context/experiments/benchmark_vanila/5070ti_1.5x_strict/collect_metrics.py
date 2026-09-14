#!/usr/bin/env python3
"""Collect strict vanilla quality, timing, and physical-update evidence."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
HERE = LAB / "context/experiments/benchmark_vanila/5070ti_1.5x_strict"
RESULTS = LAB / "results/benchmarks/benchmark_vanila/5070ti_1.5x_strict"
EVIDENCE = HERE / "evidence"
PAPER = LAB / "context/experiments/benchmark_vanila/paper_reference/vigs_before_color_refinement.csv"

SCENES = {
    "aria": ["aria1253", "aria1253rot", "aria301_12F", "aria301_305"],
    "utmm": [
        "ego-centric-1", "ego-centric-2", "ego-drive", "fast-straight",
        "slow-straight-1", "slow-straight-2", "square-1", "square-2",
    ],
    "rpng": [f"table_{index:02d}" for index in range(1, 9)],
}


def average(rows: list[dict], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return sum(values) / len(values) if values else None


def elapsed_seconds(path: Path) -> float | None:
    if not path.is_file():
        return None
    matches = re.findall(
        r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*([^\s]+)",
        path.read_text(errors="replace").replace("\r", "\n"),
    )
    if not matches:
        return None
    parts = [float(value) for value in matches[-1].split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return None


def ply_vertices(path: Path) -> int | None:
    if not path.is_file():
        return None
    with path.open("rb") as handle:
        for raw in handle:
            line = raw.decode("ascii", errors="replace").strip()
            match = re.fullmatch(r"element vertex (\d+)", line)
            if match:
                return int(match.group(1))
            if line == "end_header":
                break
    return None


def paper_lookup() -> dict[tuple[str, str], dict]:
    if not PAPER.is_file():
        return {}
    with PAPER.open(newline="") as handle:
        return {
            (row["family"], row["scene"]): row
            for row in csv.DictReader(handle)
        }


def collect() -> list[dict]:
    references = paper_lookup()
    records: list[dict] = []
    for family, scenes in SCENES.items():
        for scene in scenes:
            output = RESULTS / family / scene / "origin22ffe24_pure_online_strict15x"
            result_path = output / "psnr/after_opt/final_result.json"
            contract_path = output / "stream_contract.json"
            audit_path = output / "sensor_eos_audit.json"
            record: dict = {
                "family": family,
                "scene": scene,
                "status": "missing",
                "output_dir": str(output),
            }
            reference = references.get((family, scene))
            if reference:
                record.update({
                    "paper_psnr_before_refinement": float(reference["psnr"]),
                    "paper_ssim_before_refinement": float(reference["ssim"]),
                    "paper_lpips_before_refinement": float(reference["lpips"]),
                })
            if result_path.is_file() and contract_path.is_file() and audit_path.is_file():
                result = json.loads(result_path.read_text())
                contract = json.loads(contract_path.read_text())
                audit = json.loads(audit_path.read_text())
                per_view = result.get("per_view", [])
                heldout = [row for row in per_view if not row.get("is_keyframe", False)]
                map_strict_pass = bool(audit.get("strict_zero_tail_proven"))
                ingress_pass = bool(contract.get("producer_deadline_pass"))
                tracking_pass = bool(contract.get("tracking_deadline_pass"))
                end_to_end_pass = map_strict_pass and ingress_pass and tracking_pass
                record.update({
                    "status": (
                        "strict_pass"
                        if heldout and end_to_end_pass
                        else "map_strict_tracking_late"
                        if heldout and map_strict_pass and ingress_pass
                        else "contract_fail"
                    ),
                    "input_frame_count": contract.get("frame_count"),
                    "processed_frame_count": contract.get("processed_frame_count"),
                    "producer_dropped_frame_count": contract.get("producer_dropped_frame_count"),
                    "processed_frame_fraction": contract.get("processed_frame_fraction"),
                    "heldout_count": len(heldout),
                    "keyframe_count": sum(bool(row.get("is_keyframe")) for row in per_view),
                    "heldout_psnr": average(heldout, "psnr"),
                    "heldout_ssim": average(heldout, "ssim"),
                    "heldout_lpips": average(heldout, "lpips"),
                    "physical_adam_steps": audit.get("completed_adam_steps"),
                    "updates_after_deadline": audit.get("updates_completed_after_deadline"),
                    "map_mutations_after_deadline": audit.get("map_mutations_completed_after_deadline"),
                    "mapping_packets_started": audit.get("mapping_packets_started"),
                    "mapping_packets_completed": audit.get("mapping_packets_completed"),
                    "mapping_packets_interrupted": audit.get("mapping_packets_interrupted"),
                    "mapping_packets_rejected": audit.get("mapping_packets_rejected"),
                    "strict_zero_tail_proven": map_strict_pass,
                    "producer_deadline_pass": ingress_pass,
                    "tracking_deadline_pass": tracking_pass,
                    "end_to_end_strict_pass": end_to_end_pass,
                    "source_duration_s": contract.get("source_duration_s"),
                    "budget_duration_s": contract.get("budget_duration_s"),
                    "tracking_lateness_s": contract.get("track_done_lateness_s"),
                    "pending_packets_at_eos": contract.get("pending_gs_packets_at_sensor_eos"),
                    "discarded_pending_at_eos": contract.get("discarded_pending_gs_packets_at_sensor_eos"),
                    "gaussian_count": ply_vertices(output / "3dgs_before_final.ply"),
                    "wall_seconds_including_eval": elapsed_seconds(output / "run.log"),
                })
                if reference and record["heldout_psnr"] is not None:
                    record["psnr_minus_paper_reference"] = (
                        record["heldout_psnr"] - float(reference["psnr"])
                    )
            elif (output / "run.log").is_file():
                log_text = (output / "run.log").read_text(errors="replace")
                if (
                    "Traceback (most recent call last):" in log_text
                    or "Command terminated by signal" in log_text
                    or re.search(r"Exit status:\s*[1-9]", log_text)
                ):
                    record["status"] = "failed_incomplete"
                    if "CUDA error: invalid configuration argument" in log_text:
                        record["failure"] = "cuda_invalid_configuration"
            records.append(record)
    return records


def fmt(value: object, digits: int = 4) -> str:
    return "—" if value is None else f"{float(value):.{digits}f}"


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    records = collect()
    payload = {
        "experiment": "benchmark_vanila/5070ti_1.5x_strict",
        "vanilla_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996",
        "gpu": "NVIDIA GeForce RTX 5070 Ti",
        "protocol": "fixed1p5x_sensor_eos_zero_tail_pending_queue_discard",
        "physical_step_definition": "completed torch.optim.Adam.step on Gaussian optimizer",
        "records": records,
    }
    (EVIDENCE / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    fields = sorted({key for row in records for key in row})
    with (EVIDENCE / "summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    lines = [
        "# 5070ti_1.5x_strict 결과", "",
        "Local held-out은 evaluator의 `idx % 5 == 0 + keyframe + last` 중 실제 vanilla keyframe을 제외한 view다.",
        "`physical Adam`은 batch나 render 수가 아니라 완료된 Gaussian optimizer step의 실제 횟수다.", "",
        "| family | scene | status | processed | drop | held-out PSNR | SSIM | LPIPS | physical Adam | updates late | mutations late | track late(s) | GS |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in records:
        lines.append(
            f"| {row['family']} | {row['scene']} | {row['status']} | "
            f"{row.get('processed_frame_count', '—')}/{row.get('input_frame_count', '—')} | "
            f"{row.get('producer_dropped_frame_count', '—')} | "
            f"{fmt(row.get('heldout_psnr'))} | {fmt(row.get('heldout_ssim'), 5)} | "
            f"{fmt(row.get('heldout_lpips'), 5)} | {row.get('physical_adam_steps', '—')} | "
            f"{row.get('updates_after_deadline', '—')} | {row.get('map_mutations_after_deadline', '—')} | "
            f"{fmt(row.get('tracking_lateness_s'), 3)} | {row.get('gaussian_count', '—')} |"
        )
    complete = [row for row in records if row.get("strict_zero_tail_proven")]
    end_to_end = [row for row in records if row.get("end_to_end_strict_pass")]
    lines.extend([
        "",
        f"고정 deadline map/zero-tail 완료: **{len(complete)}/{len(records)}**; end-to-end strict 통과: **{len(end_to_end)}/{len(records)}**",
        "",
    ])
    if complete:
        lines.extend([
            "## Family averages", "",
            "| family | scenes | PSNR | SSIM | LPIPS | physical Adam |",
            "|---|---:|---:|---:|---:|---:|",
        ])
        for family in SCENES:
            group = [row for row in complete if row["family"] == family]
            if group:
                lines.append(
                    f"| {family} | {len(group)} | {fmt(average(group, 'heldout_psnr'))} | "
                    f"{fmt(average(group, 'heldout_ssim'), 5)} | {fmt(average(group, 'heldout_lpips'), 5)} | "
                    f"{fmt(average(group, 'physical_adam_steps'), 1)} |"
                )
        lines.append("")
    (HERE / "summary.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
