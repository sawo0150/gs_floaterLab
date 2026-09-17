#!/usr/bin/env python3
"""Headline table: KF-only vs KF+dense at a fixed per-keyframe iteration budget.

One row per scene. Each keyframe interval is granted the same number of
optimizer iterations (60) in both arms, so the total iteration count is a
consequence of how long the trajectory is, not a knob -- which is what an
online incremental mapper actually experiences. The two arms share dataset,
initial point cloud, poses, causal arrival schedule, selector, seed,
resolution, loss, densification policy, total iterations and the llffhold-8
held-out split; only the candidate pool differs.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH_B = HERE.parent / "benchmark-B"
MANIFEST = HERE / "evidence/manifest.json"


def final_psnr(output: str, total: int) -> float | None:
    path = Path(output) / "evaluation_curve.jsonl"
    if not path.is_file():
        return None
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    match = [r for r in rows if r.get("split") == "test" and r["iteration"] == total]
    return float(match[0]["psnr"]) if match else None


def gaussians(output: str, total: int) -> int | None:
    path = Path(output) / "gaussian_metrics" / f"iteration_{total}.json"
    return json.loads(path.read_text())["gaussian/count"] if path.is_file() else None


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    inventory = {(r["family"], r["scene"]): r for r in
                 json.loads((BENCH_B / "evidence/dataset_inventory.json").read_text())["records"]}
    runs: dict[tuple, dict] = {}
    for job in manifest["jobs"]:
        if job.get("state") != "complete":
            continue
        runs[(job["family"], job["scene"], job["arm"])] = {
            "psnr": final_psnr(job["output"], job["total_iterations"]),
            "gaussians": gaussians(job["output"], job["total_iterations"]),
            "total": job["total_iterations"],
            "budget": job["budget"],
        }

    scenes, seen = [], set()
    for job in manifest["jobs"]:
        key = (job["family"], job["scene"])
        if key not in seen:
            seen.add(key)
            scenes.append(key)

    budget = manifest["jobs"][0]["budget"]
    rows, deltas = [], []
    for family, scene in sorted(scenes):
        kf = runs.get((family, scene, "kf_only"))
        dense = runs.get((family, scene, "kf_dense"))
        if not kf or not dense or kf["psnr"] is None or dense["psnr"] is None:
            continue
        record = inventory[(family, scene)]
        delta = dense["psnr"] - kf["psnr"]
        deltas.append(delta)
        rows.append({
            "scene": f"{family}/{scene}", "events": record["events"],
            "keyframes": None, "train_frames": record["train_frames"],
            "total": kf["total"], "kf_psnr": kf["psnr"], "dense_psnr": dense["psnr"],
            "delta": delta,
            "gs_ratio": dense["gaussians"] / kf["gaussians"] if kf["gaussians"] else None,
        })

    table = ["| scene | keyframe intervals | frames | total iters | KF-only | KF+dense | Δ | GS ratio |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        ratio = f"{r['gs_ratio']:.2f}×" if r["gs_ratio"] else "—"
        mark = "**" if r["delta"] > 0 else ""
        table.append(
            f"| {r['scene']} | {r['events']} | {r['train_frames']} | {r['total']:,} | "
            f"{r['kf_psnr']:.2f} | {mark}{r['dense_psnr']:.2f}{mark} | "
            f"{mark}{r['delta']:+.2f}{mark} | {ratio} |")
    if deltas:
        wins = sum(1 for d in deltas if d > 0)
        table.append(f"| **평균 ({len(deltas)} scenes)** | | | | | | "
                     f"**{statistics.fmean(deltas):+.2f}** ({wins}/{len(deltas)}) | |")

    report = f"""# Table X — KF-only vs KF+dense supervision (online incremental)

상태: **{manifest['state']}**

## 설정

각 VIGS keyframe interval에 **{budget} optimizer iteration을 동일하게 배정**한다. 따라서 총
iteration 수는 궤적 길이(=keyframe interval 수)의 결과이지 조절 대상이 아니며, 이는 online
incremental mapper가 실제로 겪는 조건이다. 두 arm은 dataset·초기 point cloud·pose·causal
arrival schedule·selector(`causal_rr`)·seed·해상도·loss·densification 정책·**총 iteration 수**·
llffhold-8 held-out(두 arm 모두 미학습)을 전부 공유하며 **후보 pool만 다르다**.

- `KF-only`: VIGS keyframe만 supervision으로 사용
- `KF+dense`: keyframe 사이에 도착한 frame까지 함께 사용

## 결과 — held-out PSNR (dB)

{chr(10).join(table)}

`GS ratio`는 최종 Gaussian 수의 KF+dense / KF-only 비다. 1에 가까우면 품질 차이를 용량
차이로 설명할 수 없다는 뜻이다.

## 해석 제한

- pose와 초기 point cloud는 사전 VIGS run을 고정 replay한 값이다. strict online
  localization 결과가 아니며, 도착 순서(causality)와 zero-tail만 유지된다.
- 단일 seed다. 이 프로젝트의 run-to-run PSNR 분산은 과거 ±0.33dB로 실측된 바 있어,
  그보다 작은 개별 장면 차이는 단독으로 해석하지 않는다.
- held-out은 llffhold-8이라 held-out frame이 중간 frame과 시간적으로 인접하다. 두 arm이
  동일 held-out을 쓰지만 이 인접성은 KF+dense에 유리하게 작용할 수 있다.
"""
    (HERE / "TABLE_X.md").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
