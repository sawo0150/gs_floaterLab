#!/usr/bin/env python3
"""Collect 5070 Ti 1.5x streaming metrics and paper reference values."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
HERE = LAB / "context/experiments/benchmark_vanila/5070ti_1.5x_streaming"
EVIDENCE = HERE / "evidence"
RESULTS = LAB / "results/benchmarks/benchmark_vanila/5070ti_1.5x_streaming"
PAPER_CSV = LAB / "context/experiments/benchmark_vanila/paper_reference/vigs_before_color_refinement.csv"
SYNC_JSON = LAB / "context/experiments/benchmark_vanila/synchronous_unbounded/evidence/summary.json"

SCENES = {
    "utmm": [
        "ego-centric-1", "ego-centric-2", "ego-drive", "fast-straight",
        "slow-straight-1", "slow-straight-2", "square-1", "square-2",
    ],
    "rpng": [f"table_{index:02d}" for index in range(1, 9)],
}


def mean(rows: list[dict], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return sum(values) / len(values) if values else None


def elapsed_seconds(log_path: Path) -> float | None:
    if not log_path.is_file():
        return None
    text = log_path.read_text(errors="replace").replace("\r", "\n")
    matches = re.findall(
        r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*([^\s]+)",
        text,
    )
    if not matches:
        return None
    parts = [float(part) for part in matches[-1].split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return None


def ply_vertex_count(path: Path) -> int | None:
    if not path.is_file():
        return None
    with path.open("rb") as handle:
        for raw_line in handle:
            line = raw_line.decode("ascii", errors="replace").strip()
            match = re.fullmatch(r"element vertex (\d+)", line)
            if match:
                return int(match.group(1))
            if line == "end_header":
                break
    return None


def collect() -> list[dict]:
    with PAPER_CSV.open(newline="") as handle:
        paper = {
            (row["family"], row["scene"]): row
            for row in csv.DictReader(handle)
        }
    synchronous = {
        (row["family"], row["scene"]): row
        for row in json.loads(SYNC_JSON.read_text())["records"]
    }

    records = []
    for family, scenes in SCENES.items():
        for scene in scenes:
            output = (
                RESULTS / family / scene
                / "origin22ffe24_pure_online_stream15x_seed0"
            )
            result_path = output / "psnr/after_opt/final_result.json"
            contract_path = output / "stream_contract.json"
            paper_row = paper[(family, scene)]
            record = {
                "family": family,
                "scene": scene,
                "status": "missing",
                "output_dir": str(output),
                "result_file": str(result_path),
                "stream_contract_file": str(contract_path),
                "paper_psnr_before_refinement": float(paper_row["psnr"]),
                "paper_ssim_before_refinement": float(paper_row["ssim"]),
                "paper_lpips_before_refinement": float(paper_row["lpips"]),
            }
            sync_row = synchronous.get((family, scene), {})
            record["synchronous_unbounded_psnr"] = sync_row.get("heldout_psnr")
            if result_path.is_file() and contract_path.is_file():
                result = json.loads(result_path.read_text())
                contract = json.loads(contract_path.read_text())
                per_view = result.get("per_view", [])
                heldout = [row for row in per_view if not row.get("is_keyframe", False)]
                keyframes = [row for row in per_view if row.get("is_keyframe", False)]
                record.update({
                    "status": "complete" if heldout else "no_per_view",
                    "input_frame_count": contract.get("frame_count"),
                    "union_count": len(per_view),
                    "heldout_count": len(heldout),
                    "keyframe_count": len(keyframes),
                    "union_psnr": result.get("mean_psnr"),
                    "union_ssim": result.get("mean_ssim"),
                    "union_lpips": result.get("mean_lpips"),
                    "heldout_psnr": mean(heldout, "psnr"),
                    "heldout_ssim": mean(heldout, "ssim"),
                    "heldout_lpips": mean(heldout, "lpips"),
                    "gaussian_count": ply_vertex_count(output / "3dgs_before_final.ply"),
                    "wall_seconds_including_eval": elapsed_seconds(output / "run.log"),
                    "source_duration_s": contract.get("source_duration_s"),
                    "budget_duration_s": contract.get("budget_duration_s"),
                    "producer_lateness_s": contract.get("last_emit_lateness_s"),
                    "tracking_lateness_s": contract.get("track_done_lateness_s"),
                    "mapping_lateness_s": contract.get("mapping_done_lateness_s"),
                    "mapping_drain_s": contract.get("mapping_drain_after_track_s"),
                    "producer_deadline_pass": contract.get("producer_deadline_pass"),
                    "tracking_deadline_pass": contract.get("tracking_deadline_pass"),
                    "mapping_deadline_pass": contract.get("mapping_deadline_pass"),
                    "strict_zero_tail_proven": contract.get("strict_zero_tail_proven"),
                })
                if record["heldout_psnr"] is not None:
                    record["psnr_minus_paper_reference"] = (
                        record["heldout_psnr"]
                        - record["paper_psnr_before_refinement"]
                    )
                    if record["synchronous_unbounded_psnr"] is not None:
                        record["psnr_minus_synchronous_unbounded"] = (
                            record["heldout_psnr"]
                            - record["synchronous_unbounded_psnr"]
                        )
            records.append(record)
    return records


def fmt(value: object, digits: int = 4) -> str:
    return "—" if value is None else f"{float(value):.{digits}f}"


def timing_mark(value: object) -> str:
    if value is None:
        return "—"
    return "ON TIME" if value else "LATE"


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    records = collect()
    payload = {
        "experiment": "benchmark_vanila/5070ti_1.5x_streaming",
        "vanilla_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996",
        "gpu": "NVIDIA GeForce RTX 5070 Ti",
        "random_seed_explicitly_set": False,
        "legacy_output_suffix_note": (
            "directory suffix seed0 is a preserved naming error; upstream "
            "safe_state() is not called by this execution path"
        ),
        "replay_time_scale": 1.5,
        "offline_polish": False,
        "strict_zero_tail_proven": False,
        "metric_contract": (
            "standalone idx%5 evaluator views excluding each vanilla run's "
            "keyframes; paper values use a different shared non-mapping split"
        ),
        "records": records,
    }
    (EVIDENCE / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")

    fields = sorted({key for record in records for key in record})
    with (EVIDENCE / "summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    lines = [
        "# 5070ti_1.5x_streaming 결과", "",
        "Local metric은 `idx % 5 == 0` 중 해당 vanilla keyframe을 제외한 standalone held-out 평균이다.",
        "논문은 Table 18/19 final color refinement 전 값이며 split이 달라 참고 비교로만 사용한다.", "",
        "`track @1.5x`와 map tail은 실시간성 진단값이며, 늦었다고 품질 결과를 실패 처리하지 않는다.", "",
        "| family | scene | status | local PSNR | sync PSNR | local-sync | paper PSNR | local-paper | SSIM | LPIPS | track @1.5x | track late(s) | map tail(s) | drain(s) | GS |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|",
    ]
    for record in records:
        lines.append(
            f"| {record['family']} | {record['scene']} | {record['status']} | "
            f"{fmt(record.get('heldout_psnr'))} | "
            f"{fmt(record.get('synchronous_unbounded_psnr'))} | "
            f"{fmt(record.get('psnr_minus_synchronous_unbounded'))} | "
            f"{fmt(record.get('paper_psnr_before_refinement'), 2)} | "
            f"{fmt(record.get('psnr_minus_paper_reference'))} | "
            f"{fmt(record.get('heldout_ssim'), 5)} | "
            f"{fmt(record.get('heldout_lpips'), 5)} | "
            f"{timing_mark(record.get('tracking_deadline_pass'))} | "
            f"{fmt(record.get('tracking_lateness_s'), 3)} | "
            f"{fmt(record.get('mapping_lateness_s'), 3)} | "
            f"{fmt(record.get('mapping_drain_s'), 3)} | "
            f"{record.get('gaussian_count') or '—'} |"
        )
    complete = sum(record["status"] == "complete" for record in records)
    tracking_on_time = sum(record.get("tracking_deadline_pass") is True for record in records)
    complete_records = [record for record in records if record["status"] == "complete"]
    lines.extend([
        "",
        f"완료: **{complete}/{len(records)}**, 1.5x 안에 tracking 완료: **{tracking_on_time}/{complete}**",
        "",
        "마지막 입력 뒤 upstream worker의 in-flight/pending packet을 drain한다. 따라서 map tail은 기록하지만",
        "이 표의 품질 판정 cutoff로 쓰지 않으며, `strict_zero_tail_proven=false`이다.",
        "",
    ])
    if complete_records:
        lines.extend([
            "## Family averages", "",
            "장면별 산술평균이며 frame 수로 가중하지 않는다.", "",
            "| family | scenes | local PSNR | sync PSNR | local-sync | paper PSNR | SSIM | LPIPS | mean track late(s) | total wall(s) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ])
        groups = [
            (family, [row for row in complete_records if row["family"] == family])
            for family in SCENES
        ]
        groups.append(("all", complete_records))
        for family, group in groups:
            lines.append(
                f"| {family} | {len(group)} | "
                f"{fmt(mean(group, 'heldout_psnr'))} | "
                f"{fmt(mean(group, 'synchronous_unbounded_psnr'))} | "
                f"{fmt(mean(group, 'psnr_minus_synchronous_unbounded'))} | "
                f"{fmt(mean(group, 'paper_psnr_before_refinement'))} | "
                f"{fmt(mean(group, 'heldout_ssim'), 5)} | "
                f"{fmt(mean(group, 'heldout_lpips'), 5)} | "
                f"{fmt(mean(group, 'tracking_lateness_s'), 3)} | "
                f"{fmt(sum(float(row.get('wall_seconds_including_eval') or 0) for row in group), 2)} |"
            )
        lines.append("")
    (HERE / "summary.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
