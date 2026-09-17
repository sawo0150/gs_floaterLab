#!/usr/bin/env python3
"""exp87 paper table: incremental KF-only vs KF+dense convergence.

Emits summary.md (paper-ready) and evidence/summary.json. Reports the whole
PSNR-vs-update curve, not just the endpoint, because the claim under test is
about convergence SPEED, and reports final Gaussian counts next to every PSNR
because densification is active and the arms end at different capacities.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "evidence/manifest.json"
ARMS = ("kf_only", "dense_all")


def curve(output: Path) -> dict[int, float]:
    path = output / "evaluation_curve.jsonl"
    if not path.is_file():
        return {}
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    return {r["iteration"]: float(r["psnr"]) for r in rows if r.get("split") == "test"}


def gaussians(output: Path, total: int) -> int | None:
    path = output / "gaussian_metrics" / f"iteration_{total}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text())["gaussian/count"]


def fmt(value, signed: bool = False, digits: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    runs: dict[tuple, dict] = {}
    for job in manifest["jobs"]:
        if job.get("state") != "complete":
            continue
        output = Path(job["output"])
        runs[(job["family"], job["scene"], job["arm"])] = {
            "curve": curve(output), "total": job["total_iterations"],
            "gaussians": gaussians(output, job["total_iterations"]),
            "pool_frames": job["pool_frames"],
            "updates_per_pool_frame": job["updates_per_pool_frame"],
            "wall_seconds": job.get("wall_seconds"),
            "curve_iterations": job["curve_iterations"],
        }

    scenes = []
    for job in manifest["jobs"]:
        key = (job["family"], job["scene"])
        if key not in scenes:
            scenes.append(key)

    milestones = [1000, 3000, 7000, 15000, 25000, "final"]

    def at(entry: dict, milestone):
        if not entry or not entry["curve"]:
            return None
        if milestone == "final":
            return entry["curve"].get(entry["total"])
        available = sorted(entry["curve"])
        if milestone >= entry["total"]:
            return entry["curve"].get(entry["total"])
        if milestone in entry["curve"]:
            return entry["curve"][milestone]
        below = [i for i in available if i <= milestone]
        return entry["curve"][below[-1]] if below else None

    rows, deltas_by_milestone = [], {m: [] for m in milestones}
    for family, scene in scenes:
        kf = runs.get((family, scene, "kf_only"))
        dense = runs.get((family, scene, "dense_all"))
        row = {"family": family, "scene": scene,
               "kf": {m: at(kf, m) for m in milestones} if kf else {},
               "dense": {m: at(dense, m) for m in milestones} if dense else {},
               "kf_gaussians": kf["gaussians"] if kf else None,
               "dense_gaussians": dense["gaussians"] if dense else None,
               "kf_pool": kf["pool_frames"] if kf else None,
               "dense_pool": dense["pool_frames"] if dense else None,
               "kf_wall_s": kf["wall_seconds"] if kf else None,
               "dense_wall_s": dense["wall_seconds"] if dense else None}
        row["delta"] = {}
        for m in milestones:
            a, b = row["kf"].get(m), row["dense"].get(m)
            if a is not None and b is not None:
                row["delta"][m] = b - a
                deltas_by_milestone[m].append(b - a)
        rows.append(row)

    aggregate = {
        str(m): {
            "count": len(v),
            "mean": statistics.fmean(v) if v else None,
            "wins": sum(1 for x in v if x > 0),
        } for m, v in deltas_by_milestone.items()
    }

    # Crispest evidence for "converges faster under the same number of iterations":
    # how many updates does KF+dense need to reach the quality KF-only reaches at
    # the very end of its identical budget? Linear interpolation between the two
    # bracketing curve points; reported as a speed-up factor.
    for row in rows:
        family, scene = row["family"], row["scene"]
        kf, dense = runs.get((family, scene, "kf_only")), runs.get((family, scene, "dense_all"))
        row["speedup"] = None
        if not (kf and dense and kf["curve"] and dense["curve"]):
            continue
        target = kf["curve"].get(kf["total"])
        if target is None:
            continue
        points = sorted(dense["curve"].items())
        reached = None
        previous = None
        for iteration, psnr in points:
            if psnr >= target:
                if previous and previous[1] < target:
                    span = psnr - previous[1]
                    frac = (target - previous[1]) / span if span > 0 else 0.0
                    reached = previous[0] + frac * (iteration - previous[0])
                else:
                    reached = float(iteration)
                break
            previous = (iteration, psnr)
        row["speedup"] = {
            "kf_final_psnr": target, "kf_updates": kf["total"],
            "dense_updates_to_match": reached,
            "factor": (kf["total"] / reached) if reached else None,
            "dense_final_psnr": dense["curve"].get(dense["total"]),
        }

    (HERE / "evidence/summary.json").write_text(json.dumps({
        "state": manifest["state"], "milestones": milestones,
        "rows": rows, "aggregate_delta_dense_minus_kf": aggregate,
    }, indent=2) + "\n")

    speed_rows = ["| scene | KF-only final | KF-only updates | KF+dense updates to match | speed-up | KF+dense final |",
                  "|---|---:|---:|---:|---:|---:|"]
    for row in rows:
        s = row.get("speedup")
        if not s:
            continue
        match = f"{s['dense_updates_to_match']:,.0f}" if s["dense_updates_to_match"] else "미달"
        factor = f"**{s['factor']:.2f}×**" if s["factor"] else "—"
        speed_rows.append(
            f"| {row['family']}/{row['scene']} | {fmt(s['kf_final_psnr'])} | {s['kf_updates']:,} | "
            f"{match} | {factor} | {fmt(s['dense_final_psnr'])} |")

    header = " | ".join("final" if m == "final" else f"@{m//1000}k" for m in milestones)
    table = [f"| scene | arm | pool | {header} | final GS |",
             "|---|---|---:|" + "---:|" * len(milestones) + "---:|"]
    for row in rows:
        for arm, key, gskey, poolkey in (("KF-only", "kf", "kf_gaussians", "kf_pool"),
                                         ("KF+dense", "dense", "dense_gaussians", "dense_pool")):
            cells = " | ".join(fmt(row[key].get(m)) for m in milestones)
            gs = row[gskey]
            table.append(f"| {row['family']}/{row['scene']} | {arm} | "
                         f"{row[poolkey] if row[poolkey] else '—'} | {cells} | "
                         f"{gs if gs else '—'} |")
        cells = " | ".join(fmt(row["delta"].get(m), signed=True) for m in milestones)
        table.append(f"| {row['family']}/{row['scene']} | **Δ (dense−KF)** | | {cells} | |")

    agg_line = " | ".join(
        f"{fmt(aggregate[str(m)]['mean'], signed=True)} ({aggregate[str(m)]['wins']}/{aggregate[str(m)]['count']})"
        for m in milestones)

    summary = f"""# exp87 — incremental KF-only vs KF+dense supervision

상태: **{manifest['state']}**

## 질문

배치 학습에서 관측된 "dense supervision이 keyframe-only보다 빠르게 수렴한다"(exp66,
aria1253, 26k iteration에서 31.68 vs 28.38dB)를 **causal/incremental 도착 조건에서도**
관측할 수 있는가.

## 계약

두 arm이 공유: dataset, init point cloud, causal arrival schedule, `causal_rr` selector,
seed, 해상도 `-r 4`, RGB-only loss, 표준 3DGS densification(500–15,000, interval 100),
총 optimizer update 수, 그리고 두 arm 모두 한 번도 학습하지 않는 llffhold-8 held-out.
**다른 것은 후보 pool 하나뿐**이다 — `kf_only`는 VIGS keyframe만, `dense_all`은 도착한
모든 train frame.

benchmark-A/B와 달리 `--fixed_topology_step_before_report` / `--densify_until_iter 0`을
쓰지 않는다. 즉 dense view가 필요한 Gaussian을 실제로 만들 수 있다(exp66이 배치에서
"dense frame에 keyframe과 동일한 geometry 편집 권한"을 줬을 때의 조건).

## 결과 — held-out PSNR(dB) vs optimizer update

{chr(10).join(table)}

## Scene-unweighted 평균 Δ(dense − KF-only)

| {header} |
|{'---:|' * len(milestones)}
| {agg_line} |

## 수렴 속도 — "같은 iteration 수에서 더 빨리 수렴한다"의 직접 근거

KF-only가 **전체 예산을 다 쓰고** 도달한 품질에, KF+dense는 몇 번의 update만에 도달하는가.

{chr(10).join(speed_rows)}

## 해석 제한

- densification이 켜져 있으므로 두 arm의 최종 Gaussian 수가 다르다. 위 표에 최종
  Gaussian 수를 함께 싣는다. "dense가 단지 Gaussian을 더 많이 만들어서 이긴 것"이라는
  반론을 배제하려면 capacity-matched 후속 통제가 필요하다.
- pose와 init은 사전 VIGS run을 고정 replay한 것이므로 strict online localization
  결과가 아니다. 도착 순서(causality)와 zero-tail은 유지된다.
- held-out은 llffhold-8이라 held-out frame이 dense train frame과 시간적으로 인접한다.
  이 인접성은 dense arm에 유리하게 작용할 수 있으며 두 arm 모두 동일 held-out을 쓴다.
"""
    (HERE / "summary.md").write_text(summary)
    print(summary)


if __name__ == "__main__":
    main()
