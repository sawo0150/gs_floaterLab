#!/usr/bin/env python3
"""Summarize the completed paired initialization-density pilot."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "evidence/manifest.json"


def final_test(output: Path, total: int) -> dict:
    rows = [
        json.loads(line)
        for line in (output / "evaluation_curve.jsonl").read_text().splitlines()
        if line
    ]
    matches = [
        row
        for row in rows
        if row.get("split") == "test" and row.get("iteration") == total
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one final held-out row: {output}")
    return matches[0]


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    if manifest.get("state") != "FINISHED_8_COMPLETE_0_FAILED":
        raise RuntimeError(f"panel is incomplete: {manifest.get('state')}")

    density_by_scene = {
        (row["family"], row["scene"]): row for row in manifest["datasets"]
    }
    rows = []
    for job in manifest["jobs"]:
        output = Path(job["output"])
        evaluation = final_test(output, job["total_iterations"])
        scheduler = json.loads((output / "view_scheduler_summary.json").read_text())
        gaussian = json.loads(
            (
                output
                / "gaussian_metrics"
                / f"iteration_{job['total_iterations']}.json"
            ).read_text()
        )
        if scheduler["completed_updates_this_run"] != job["total_iterations"]:
            raise RuntimeError(f"update count mismatch: {output}")
        if not scheduler.get("post_update_reporting"):
            raise RuntimeError(f"pre-update final report: {output}")
        rows.append(
            {
                "family": job["family"],
                "scene": job["scene"],
                "density": job["density"],
                "arm": job["arm"],
                "seed": job["seed"],
                "updates": job["total_iterations"],
                "initial_gaussians": gaussian["gaussian/count"],
                "heldout_psnr_db": evaluation["psnr"],
                "training_gpu_seconds": scheduler["training_gpu_ms"] / 1000.0,
                "wall_seconds": job["wall_seconds"],
                "unique_selected": scheduler["unique_selected"],
                "zero_service_views": scheduler["zero_service"],
                "output": str(output),
            }
        )

    lookup = {
        (row["family"], row["scene"], row["density"], row["arm"]): row
        for row in rows
    }
    comparisons = []
    for family, scene in density_by_scene:
        for arm in ("rr", "ercb"):
            control = lookup[(family, scene, "stride40", arm)]
            dense = lookup[(family, scene, "stride20", arm)]
            comparisons.append(
                {
                    "family": family,
                    "scene": scene,
                    "arm": arm,
                    "control_psnr_db": control["heldout_psnr_db"],
                    "dense_psnr_db": dense["heldout_psnr_db"],
                    "dense_minus_control_db": (
                        dense["heldout_psnr_db"] - control["heldout_psnr_db"]
                    ),
                    "training_gpu_ratio": (
                        dense["training_gpu_seconds"]
                        / control["training_gpu_seconds"]
                    ),
                    "wall_ratio": dense["wall_seconds"] / control["wall_seconds"],
                }
            )

    scheduler_effect = []
    for family, scene in density_by_scene:
        for density in ("stride40", "stride20"):
            rr = lookup[(family, scene, density, "rr")]
            ercb = lookup[(family, scene, density, "ercb")]
            scheduler_effect.append(
                {
                    "family": family,
                    "scene": scene,
                    "density": density,
                    "ercb_minus_rr_db": (
                        ercb["heldout_psnr_db"] - rr["heldout_psnr_db"]
                    ),
                }
            )

    by_arm = defaultdict(list)
    for row in comparisons:
        by_arm[row["arm"]].append(row["dense_minus_control_db"])
    aggregate = {
        "dense_positive_pairs": sum(
            row["dense_minus_control_db"] > 0 for row in comparisons
        ),
        "dense_total_pairs": len(comparisons),
        "mean_dense_minus_control_db_by_arm": {
            arm: sum(values) / len(values) for arm, values in by_arm.items()
        },
    }
    payload = {
        "protocol": manifest["protocol"],
        "manifest_state": manifest["state"],
        "datasets": list(density_by_scene.values()),
        "runs": rows,
        "density_comparisons": comparisons,
        "scheduler_effect": scheduler_effect,
        "aggregate": aggregate,
        "interpretation": (
            "GO for broader initialization-density validation; this is fixed-replay "
            "diagnostic evidence, not strict end-to-end VIGS evidence."
        ),
    }
    evidence = HERE / "evidence"
    (evidence / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    with (evidence / "summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    table = []
    for row in comparisons:
        table.append(
            "| {family}/{scene} | {arm} | {control_psnr_db:.4f} | "
            "{dense_psnr_db:.4f} | {dense_minus_control_db:+.4f} | "
            "{training_gpu_ratio:.3f}× | {wall_ratio:.3f}× |".format(**row)
        )
    scheduler_table = []
    for row in scheduler_effect:
        scheduler_table.append(
            "| {family}/{scene} | {density} | {ercb_minus_rr_db:+.4f} |".format(
                **row
            )
        )
    dataset_table = []
    for row in density_by_scene.values():
        dataset_table.append(
            f"| {row['family']}/{row['scene']} | {row['control_points']:,} | "
            f"{row['dense_points']:,} | {row['density_ratio']:.3f}× |"
        )

    result = f"""# benchmark-A initialization-density pilot result

## 판정

**두 장면·두 scheduler의 4/4 pair에서 stride20 dense initialization이 held-out
PSNR을 높였다.** RR 장면 평균은 **{aggregate['mean_dense_minus_control_db_by_arm']['rr']:+.4f}dB**,
ERCB 장면 평균은 **{aggregate['mean_dense_minus_control_db_by_arm']['ercb']:+.4f}dB**다.
따라서 sparse fixed initialization이 benchmark-A의 낮은 절대 PSNR에 기여한다는 가설은
pilot gate를 통과했다. 다만 2장면·seed0 fixed replay 결과이므로 전체 benchmark나 strict
VIGS end-to-end의 일반 결론은 아니다.

## 통제

- 한 번의 strict VIGS source run에서 동일 BA-refined depth/pose를 stride40과 stride20으로
  동시에 export했다. 복제·jitter·다른 run point cloud는 쓰지 않았다.
- RGB, camera, full trajectory, keyframe boundary, causal arrival schedule, Adam update 수,
  seed, RGB-only loss, fixed topology, llffhold-8 held-out evaluator가 pair별로 동일하다.
- 저예산은 event당 15 update이며 optimizer tail은 0이다. 모든 run의 최종 평가는 마지막
  update 뒤 기록됐고 manifest는 8/8 complete, 0 failed다.

| scene | stride40 points | stride20 points | density |
|---|---:|---:|---:|
{chr(10).join(dataset_table)}

## Held-out PSNR와 비용

| scene | scheduler | stride40 | stride20 | dense Δ | train GPU ratio | wall ratio |
|---|---|---:|---:|---:|---:|---:|
{chr(10).join(table)}

Gaussian topology는 고정돼 최종 Gaussian 수가 초기점 수와 같다. Dense init의 비용은
square-1에서 training GPU time **1.17×**, table_01에서 **1.69–1.71×**였다. Wall time은
각각 약 **1.01–1.02×**, **1.22×**다. 따라서 이는 같은 update 수에서의 품질 개선이지,
같은 wall-time budget에서 공짜로 얻은 개선은 아니다.

## ERCB 상호작용

| scene | density | ERCB − RR |
|---|---|---:|
{chr(10).join(scheduler_table)}

초기점을 촘촘히 해도 ERCB의 저예산 이득은 4/4 조건에서 양수다. 다만 square-1에서는
ERCB 이득이 +0.6459→+0.1399dB로 줄고 table_01에서는 +0.7919→+1.0708dB로 늘어,
단 두 장면만으로 일관된 interaction을 주장할 수 없다.

## 다음 판정

**GO는 “조금 더 넓게 검증할 가치가 있다”는 뜻이다.** 바로 production 설정으로 채택하지
않는다. 다음 최소 실험은 같은 paired exporter를 몇 개 추가 장면에 적용하고, fixed-update와
matched-wall-time을 함께 보고 dense init이 실제 strict mapping budget에서도 이득인지
확인하는 것이다. 전체 13-scene sweep나 density knob 장면별 튜닝은 아직 하지 않는다.
"""
    (HERE / "RESULT.md").write_text(result)
    print(json.dumps(aggregate, indent=2))


if __name__ == "__main__":
    main()
