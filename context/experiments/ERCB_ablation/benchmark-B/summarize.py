#!/usr/bin/env python3
"""Summarize benchmark-B density and ERCB budget interactions."""

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "evidence/manifest.json"


def final_psnr(output: Path, total: int) -> float:
    rows = [
        json.loads(line)
        for line in (output / "evaluation_curve.jsonl").read_text().splitlines()
        if line
    ]
    match = [row for row in rows if row.get("split") == "test" and row.get("iteration") == total]
    if len(match) != 1:
        raise RuntimeError(f"missing unique final test row: {output}")
    return float(match[0]["psnr"])


def aggregate(values: list[float]) -> dict:
    return {
        "count": len(values),
        "mean": statistics.fmean(values) if values else None,
        "median": statistics.median(values) if values else None,
        "wins": sum(value > 0 for value in values),
    }


def fmt(value: float | None, signed: bool = False) -> str:
    if value is None:
        return "—"
    return f"{value:+.4f}" if signed else f"{value:.4f}"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    dataset_inventory = json.loads((HERE / "evidence/dataset_inventory.json").read_text())
    dataset_by_scene = {
        (row["family"], row["scene"]): row for row in dataset_inventory["records"]
    }
    runs = []
    for job in manifest["jobs"]:
        if job.get("state") != "complete":
            continue
        output = Path(job["output"])
        scheduler = json.loads((output / "view_scheduler_summary.json").read_text())
        metric = json.loads((
            output / "gaussian_metrics" / f"iteration_{job['total_iterations']}.json"
        ).read_text())
        runs.append({
            "family": job["family"], "scene": job["scene"],
            "stride": job["stride"], "budget": job["budget"], "arm": job["arm"],
            "seed": job["seed"], "updates": job["total_iterations"],
            "heldout_psnr_db": final_psnr(output, job["total_iterations"]),
            "gaussians": metric["gaussian/count"],
            "training_gpu_seconds": scheduler["training_gpu_ms"] / 1000,
            "wall_seconds": job.get("wall_seconds"),
            "unique_selected": scheduler["unique_selected"],
            "zero_service_views": scheduler["zero_service"],
            "output": str(output),
        })
    lookup = {
        (row["family"], row["scene"], row["stride"], row["budget"], row["arm"]): row
        for row in runs
    }
    density = []
    ercb = []
    scenes = sorted(dataset_by_scene)
    for family, scene in scenes:
        for arm in ("rr", "ercb"):
            control = lookup.get((family, scene, 40, 15, arm))
            dense = lookup.get((family, scene, 20, 15, arm))
            if control and dense:
                density.append({
                    "family": family, "scene": scene, "arm": arm,
                    "stride40_psnr": control["heldout_psnr_db"],
                    "stride20_psnr": dense["heldout_psnr_db"],
                    "dense_delta_db": dense["heldout_psnr_db"] - control["heldout_psnr_db"],
                    "gpu_ratio": dense["training_gpu_seconds"] / control["training_gpu_seconds"],
                    "wall_ratio": dense["wall_seconds"] / control["wall_seconds"],
                })
        for budget in (15, 30, 60):
            rr = lookup.get((family, scene, 20, budget, "rr"))
            selected = lookup.get((family, scene, 20, budget, "ercb"))
            if rr and selected:
                ercb.append({
                    "family": family, "scene": scene, "budget": budget,
                    "rr_psnr": rr["heldout_psnr_db"],
                    "ercb_psnr": selected["heldout_psnr_db"],
                    "ercb_delta_db": selected["heldout_psnr_db"] - rr["heldout_psnr_db"],
                })

    aggregate_density = {}
    for family in ("utmm", "rpng", "aria", "overall"):
        aggregate_density[family] = {}
        for arm in ("rr", "ercb"):
            values = [
                row["dense_delta_db"] for row in density
                if row["arm"] == arm and (family == "overall" or row["family"] == family)
            ]
            aggregate_density[family][arm] = aggregate(values)
    aggregate_ercb = {}
    for family in ("utmm", "rpng", "aria", "overall"):
        aggregate_ercb[family] = {}
        for budget in (15, 30, 60):
            values = [
                row["ercb_delta_db"] for row in ercb
                if row["budget"] == budget and (family == "overall" or row["family"] == family)
            ]
            aggregate_ercb[family][str(budget)] = aggregate(values)

    payload = {
        "protocol": manifest["protocol"], "manifest_state": manifest["state"],
        "requested_scenes": (
            len(dataset_inventory["records"]) + len(dataset_inventory["unavailable"])
        ),
        "available_scenes": len(dataset_inventory["records"]),
        "unavailable": dataset_inventory["unavailable"],
        "runs": runs, "density_pairs": density, "ercb_pairs": ercb,
        "aggregate_density": aggregate_density, "aggregate_ercb": aggregate_ercb,
    }
    evidence = HERE / "evidence"
    (evidence / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    if runs:
        with (evidence / "summary.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(runs[0]))
            writer.writeheader()
            writer.writerows(runs)

    table_rows = []
    for family, scene in scenes:
        ds = dataset_by_scene[(family, scene)]
        d_rr = next((row["dense_delta_db"] for row in density if row["family"] == family and row["scene"] == scene and row["arm"] == "rr"), None)
        d_er = next((row["dense_delta_db"] for row in density if row["family"] == family and row["scene"] == scene and row["arm"] == "ercb"), None)
        low_rr = lookup.get((family, scene, 20, 15, "rr"))
        low_er = lookup.get((family, scene, 20, 15, "ercb"))
        deltas = {
            budget: next((row["ercb_delta_db"] for row in ercb if row["family"] == family and row["scene"] == scene and row["budget"] == budget), None)
            for budget in (15, 30, 60)
        }
        table_rows.append(
            f"| {family}/{scene} | {ds['density_ratio']:.2f}× | {fmt(d_rr, True)} | "
            f"{fmt(d_er, True)} | {fmt(low_rr['heldout_psnr_db'] if low_rr else None)} | "
            f"{fmt(low_er['heldout_psnr_db'] if low_er else None)} | "
            f"{fmt(deltas[15], True)} | {fmt(deltas[30], True)} | {fmt(deltas[60], True)} |"
        )
    agg_rows = []
    for family in ("utmm", "rpng", "aria", "overall"):
        dd = aggregate_density[family]
        ee = aggregate_ercb[family]
        agg_rows.append(
            f"| {family} | {fmt(dd['rr']['mean'], True)} ({dd['rr']['wins']}/{dd['rr']['count']}) | "
            f"{fmt(dd['ercb']['mean'], True)} ({dd['ercb']['wins']}/{dd['ercb']['count']}) | "
            f"{fmt(ee['15']['mean'], True)} ({ee['15']['wins']}/{ee['15']['count']}) | "
            f"{fmt(ee['30']['mean'], True)} ({ee['30']['wins']}/{ee['30']['count']}) | "
            f"{fmt(ee['60']['mean'], True)} ({ee['60']['wins']}/{ee['60']['count']}) |"
        )
    unavailable = "\n".join(
        f"- `{label}`: {reason}" for label, reason in dataset_inventory["unavailable"].items()
    ) or "- 없음"
    result = f"""# benchmark-B result — stride20 full-family panel

상태: **{manifest['state']}**
가용 scene: **{len(dataset_inventory['records'])}/20**, 완료 run: **{len(runs)}/{len(manifest['jobs'])}**

## Scene 결과

`init Δ`는 동일 VIGS source/pose에서 event15 stride20−stride40이다. `ERCB Δ`는 stride20에서
ERCB−RR이다. 모든 PSNR은 llffhold-8 held-out이다.

| scene | point ratio | init Δ RR | init Δ ERCB | low RR | low ERCB | ERCB Δ low | mid | high |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(table_rows)}

## Family scene-unweighted 평균

괄호는 양수 scene/유효 scene이다.

| family | init Δ RR | init Δ ERCB | ERCB Δ low | ERCB Δ mid | ERCB Δ high |
|---|---:|---:|---:|---:|---:|
{chr(10).join(agg_rows)}

## Unavailable

{unavailable}

## 해석 제한

- stride20은 Gaussian 수가 약 4배라 fixed-update와 동일 wall-time을 뜻하지 않는다. GPU와
  wall-time ratio는 `evidence/summary.json`의 density pair에 함께 기록했다.
- 이것은 final VIGS pose/init를 고정한 offline scheduler-isolation replay이며 strict
  end-to-end mapping 결과가 아니다.
- 실패와 불완전 pair는 평균에서 제외하며 위 unavailable 목록에 남긴다.
"""
    (HERE / "summary.md").write_text(result)
    print(json.dumps({
        "state": manifest["state"], "runs": len(runs),
        "aggregate_density": aggregate_density,
        "aggregate_ercb": aggregate_ercb,
    }, indent=2))


if __name__ == "__main__":
    main()
