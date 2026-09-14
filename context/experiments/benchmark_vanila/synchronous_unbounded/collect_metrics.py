#!/usr/bin/env python3
"""Collect vanilla union and keyframe-excluded held-out image metrics."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


LAB = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
HERE = LAB / "context/experiments/benchmark_vanila/synchronous_unbounded"
EVIDENCE = HERE / "evidence"
NEW = LAB / "results/benchmarks/benchmark_vanila/synchronous_unbounded"
PAPER_CSV = LAB / "context/experiments/benchmark_vanila/paper_reference/vigs_before_color_refinement.csv"

SCENES = {
    "utmm": [
        "ego-centric-1", "ego-centric-2", "ego-drive", "fast-straight",
        "slow-straight-1", "slow-straight-2", "square-1", "square-2",
    ],
    "rpng": [f"table_{index:02d}" for index in range(1, 9)],
    "aria": ["aria1253", "aria301_305"],
}

REUSED = {
    ("utmm", scene): LAB / f"results/benchmarks/exp81_vigs_vanilla5070/utmm/{scene}/origin22ffe24_pytorch_transfer_seed0"
    for scene in [
        "ego-centric-1", "ego-centric-2", "fast-straight", "slow-straight-1",
        "slow-straight-2", "square-1",
    ]
}
REUSED.update({
    ("aria", "aria1253"): LAB / "results/benchmarks/exp82_vigs_vanilla5070/aria1253/origin22ffe24_pytorch_seed0",
    ("aria", "aria301_305"): LAB / "results/benchmarks/exp82_vigs_vanilla5070/aria301_305/origin22ffe24_pytorch_seed0",
})


def selected_output(family: str, scene: str) -> tuple[Path, str]:
    new = NEW / family / scene / "origin22ffe24_pure_online_seed0"
    if (new / "psnr/after_opt/final_result.json").is_file():
        return new, "benchmark_vanila"
    reused = REUSED.get((family, scene))
    if reused and (reused / "psnr/after_opt/final_result.json").is_file():
        return reused, "reused_exp81_82"
    return new, "missing"


def mean(rows: list[dict], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return sum(values) / len(values) if values else None


def elapsed_seconds(log_path: Path) -> float | None:
    if not log_path.is_file():
        return None
    text = log_path.read_text(errors="replace").replace("\r", "\n")
    matches = re.findall(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*([^\s]+)", text)
    if not matches:
        return None
    parts = [float(part) for part in matches[-1].split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return None


def ply_vertex_count(ply_path: Path) -> int | None:
    if not ply_path.is_file():
        return None
    with ply_path.open("rb") as handle:
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
    records = []
    for family, scenes in SCENES.items():
        for scene in scenes:
            output, provenance = selected_output(family, scene)
            result_path = output / "psnr/after_opt/final_result.json"
            record = {
                "family": family,
                "scene": scene,
                "status": "missing",
                "provenance": provenance,
                "output_dir": str(output),
                "result_file": str(result_path),
            }
            paper_row = paper.get((family, scene))
            if paper_row is not None:
                record.update({
                    "paper_psnr_before_refinement": float(paper_row["psnr"]),
                    "paper_ssim_before_refinement": float(paper_row["ssim"]),
                    "paper_lpips_before_refinement": float(paper_row["lpips"]),
                })
            if result_path.is_file():
                result = json.loads(result_path.read_text())
                per_view = result.get("per_view", [])
                heldout = [row for row in per_view if not row.get("is_keyframe", False)]
                keyframes = [row for row in per_view if row.get("is_keyframe", False)]
                record.update({
                    "status": "complete" if heldout else "no_per_view",
                    "input_frame_count": max((int(row["frame_idx"]) for row in per_view), default=-1) + 1,
                    "union_count": len(per_view),
                    "heldout_count": len(heldout),
                    "keyframe_count": len(keyframes),
                    "union_psnr": result.get("mean_psnr"),
                    "union_ssim": result.get("mean_ssim"),
                    "union_lpips": result.get("mean_lpips"),
                    "heldout_psnr": mean(heldout, "psnr"),
                    "heldout_ssim": mean(heldout, "ssim"),
                    "heldout_lpips": mean(heldout, "lpips"),
                    "wall_seconds_including_eval": elapsed_seconds(output / "run.log"),
                    "gaussian_count": ply_vertex_count(output / "3dgs_before_final.ply"),
                })
                if paper_row is not None and record["heldout_psnr"] is not None:
                    record["psnr_minus_paper_reference"] = (
                        record["heldout_psnr"]
                        - record["paper_psnr_before_refinement"]
                    )
            records.append(record)
    return records


def fmt(value: object, digits: int = 4) -> str:
    return "—" if value is None else f"{float(value):.{digits}f}"


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    records = collect()
    payload = {
        "experiment": "benchmark_vanila/synchronous_unbounded",
        "vanilla_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996",
        "random_seed_explicitly_set": False,
        "legacy_output_suffix_note": (
            "directory suffix seed0 is a preserved naming error; upstream "
            "safe_state() is not called by this execution path"
        ),
        "offline_polish": False,
        "metric_contract": "standalone idx%5 evaluator views excluding vanilla keyframes; not the paper multi-method shared split",
        "records": records,
    }
    (EVIDENCE / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")

    fields = sorted({key for record in records for key in record})
    with (EVIDENCE / "summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    lines = [
        "# synchronous_unbounded 결과", "",
        "표는 vanilla keyframe을 제외한 `idx % 5 == 0` standalone held-out 평균이다. 논문 multi-method shared split이나 matched-runtime custom 비교가 아니다.", "",
        "논문 열은 Table 18/19의 final color refinement 전 참고값이며 평가 split이 달라 엄밀한 재현 오차가 아니다.", "",
        "| family | scene | status | frames | held-out | local PSNR | paper PSNR | local-paper | SSIM | paper SSIM | LPIPS | paper LPIPS | union PSNR | GS | wall(s) | source |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for record in records:
        lines.append(
            f"| {record['family']} | {record['scene']} | {record['status']} | "
            f"{record.get('input_frame_count', 0)} | {record.get('heldout_count', 0)} | {fmt(record.get('heldout_psnr'))} | "
            f"{fmt(record.get('paper_psnr_before_refinement'), 2)} | {fmt(record.get('psnr_minus_paper_reference'))} | "
            f"{fmt(record.get('heldout_ssim'), 5)} | {fmt(record.get('paper_ssim_before_refinement'), 3)} | "
            f"{fmt(record.get('heldout_lpips'), 5)} | {fmt(record.get('paper_lpips_before_refinement'), 3)} | "
            f"{fmt(record.get('union_psnr'))} | {record.get('gaussian_count') or '—'} | "
            f"{fmt(record.get('wall_seconds_including_eval'), 2)} | "
            f"{record['provenance']} |"
        )
    complete = sum(record["status"] == "complete" for record in records)
    lines.extend(["", f"완료: **{complete}/{len(records)}**", ""])
    (HERE / "summary.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
