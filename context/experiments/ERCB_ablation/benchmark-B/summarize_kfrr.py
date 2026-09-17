#!/usr/bin/env python3
"""Three-arm benchmark-B summary: full-pool RR vs keyframe-only RR vs ERCB.

Reads the existing evidence/manifest.json (rr/ercb) and the isolated
evidence/manifest_kfrr.json (kf_rr) side by side. Never writes to either
manifest; only produces evidence/summary_kfrr.json and summary_kfrr.md.
Safe to run at any time -- rows with an incomplete arm are simply omitted
from that row's comparison (partial-progress friendly, same philosophy as
summarize.py).
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path


HERE = Path(__file__).resolve().parent


def final_psnr(output: Path, total: int) -> float | None:
    path = output / "evaluation_curve.jsonl"
    if not path.is_file():
        return None
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    match = [row for row in rows if row.get("split") == "test" and row.get("iteration") == total]
    return float(match[0]["psnr"]) if len(match) == 1 else None


def aggregate(values: list[float]) -> dict:
    return {
        "count": len(values),
        "mean": statistics.fmean(values) if values else None,
        "median": statistics.median(values) if values else None,
        "wins": sum(value > 0 for value in values),
    }


def fmt(value, signed: bool = False) -> str:
    if value is None:
        return "—"
    return f"{value:+.4f}" if signed else f"{value:.4f}"


def load_runs(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    lookup = {}
    for job in manifest["jobs"]:
        if job.get("state") != "complete":
            continue
        output = Path(job["output"])
        psnr = final_psnr(output, job["total_iterations"])
        if psnr is None:
            continue
        key = (job["family"], job["scene"], job["stride"], job["budget"], job["arm"], job["seed"])
        lookup[key] = psnr
    return manifest, lookup


def main() -> None:
    main_manifest, main_lookup = load_runs(HERE / "evidence/manifest.json")
    kfrr_manifest, kfrr_lookup = load_runs(HERE / "evidence/manifest_kfrr.json")
    lookup = {**main_lookup, **kfrr_lookup}
    pool_inventory = json.loads((HERE / "evidence/keyframe_pool_inventory.json").read_text())
    pool_by_scene = {(r["family"], r["scene"]): r for r in pool_inventory["records"]}

    scenes = sorted({(j["family"], j["scene"]) for j in main_manifest["jobs"]})
    seed = 0
    rows = []
    for family, scene in scenes:
        for stride, budget in ((40, 15), (20, 15), (20, 30), (20, 60)):
            rr = lookup.get((family, scene, stride, budget, "rr", seed))
            kf = lookup.get((family, scene, stride, budget, "kf_rr", seed))
            er = lookup.get((family, scene, stride, budget, "ercb", seed))
            if rr is None and kf is None and er is None:
                continue
            rows.append({
                "family": family, "scene": scene, "stride": stride, "budget": budget,
                "rr": rr, "kf_rr": kf, "ercb": er,
                "kfrr_minus_rr": (kf - rr) if (kf is not None and rr is not None) else None,
                "ercb_minus_rr": (er - rr) if (er is not None and rr is not None) else None,
                "ercb_minus_kfrr": (er - kf) if (er is not None and kf is not None) else None,
            })

    by_condition = {}
    for stride, budget in ((40, 15), (20, 15), (20, 30), (20, 60)):
        key = f"stride{stride}_event{budget}"
        kfrr_minus_rr = [r["kfrr_minus_rr"] for r in rows if r["stride"] == stride and r["budget"] == budget and r["kfrr_minus_rr"] is not None]
        ercb_minus_rr = [r["ercb_minus_rr"] for r in rows if r["stride"] == stride and r["budget"] == budget and r["ercb_minus_rr"] is not None]
        ercb_minus_kfrr = [r["ercb_minus_kfrr"] for r in rows if r["stride"] == stride and r["budget"] == budget and r["ercb_minus_kfrr"] is not None]
        by_condition[key] = {
            "kfrr_minus_rr": aggregate(kfrr_minus_rr),
            "ercb_minus_rr": aggregate(ercb_minus_rr),
            "ercb_minus_kfrr": aggregate(ercb_minus_kfrr),
        }

    payload = {
        "main_manifest_state": main_manifest["state"],
        "kfrr_manifest_state": kfrr_manifest["state"],
        "rows": rows, "aggregate_by_condition": by_condition,
    }
    (HERE / "evidence/summary_kfrr.json").write_text(json.dumps(payload, indent=2) + "\n")

    table_rows = []
    for r in rows:
        pool = pool_by_scene.get((r["family"], r["scene"]), {})
        ratio = pool.get("conditions", {}).get(f"stride{r['stride']}_event{r['budget']}", {})
        pool_str = f"{ratio.get('keyframe_only_pool_size','?')}/{ratio.get('full_pool_size','?')}"
        table_rows.append(
            f"| {r['family']}/{r['scene']} | stride{r['stride']} e{r['budget']} | {pool_str} | "
            f"{fmt(r['rr'])} | {fmt(r['kf_rr'])} | {fmt(r['ercb'])} | "
            f"{fmt(r['kfrr_minus_rr'], True)} | {fmt(r['ercb_minus_rr'], True)} | {fmt(r['ercb_minus_kfrr'], True)} |"
        )
    agg_rows = []
    for stride, budget in ((40, 15), (20, 15), (20, 30), (20, 60)):
        key = f"stride{stride}_event{budget}"
        a = by_condition[key]
        agg_rows.append(
            f"| {key} | "
            f"{fmt(a['kfrr_minus_rr']['mean'], True)} ({a['kfrr_minus_rr']['wins']}/{a['kfrr_minus_rr']['count']}) | "
            f"{fmt(a['ercb_minus_rr']['mean'], True)} ({a['ercb_minus_rr']['wins']}/{a['ercb_minus_rr']['count']}) | "
            f"{fmt(a['ercb_minus_kfrr']['mean'], True)} ({a['ercb_minus_kfrr']['wins']}/{a['ercb_minus_kfrr']['count']}) |"
        )

    result = f"""# benchmark-B three-arm result — full-pool RR vs keyframe-only RR vs ERCB

main manifest(rr/ercb): **{main_manifest['state']}**
kf_rr manifest: **{kfrr_manifest['state']}**

keyframe-only RR은 같은 total_iterations/event 경계/seed로 causal RR을 도는데, 후보 pool을
VIGS 실제 keyframe(traj_kf_beforeBA 타임스탬프를 최근접 RGB로 매핑, dense 프레임 제외)으로만
제한한 arm이다. pool 열은 `keyframe-only pool / full pool`(둘 다 held-out 제외 학습 프레임 수) 크기다.

## Row 상세

| scene | condition | pool(kf/full) | RR(full) | RR(kf-only) | ERCB | kf_rr−RR(full) | ERCB−RR(full) | ERCB−kf_rr |
|---|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(table_rows)}

## Condition 평균 (scene-unweighted)

| condition | kf_rr−RR(full) | ERCB−RR(full) | ERCB−kf_rr |
|---|---:|---:|---:|
{chr(10).join(agg_rows)}

## 해석 메모

- `kf_rr−RR(full)`: 후보 pool을 dense 프레임 없이 keyframe만으로 좁히면 무슨 일이 생기는지
  (pool 크기 축소 자체의 효과, ERCB 가중치와 무관).
- `ERCB−RR(full)`: 기존 저예산 ERCB 우위(=+0.66~0.77dB, event15).
- `ERCB−kf_rr`: ERCB가 "전체 pool을 스마트하게 가중"한 것이 "keyframe만 쓰는 단순 RR"보다도
  나은지 — 이게 0에 가깝다면 ERCB의 이득 대부분이 사실 "dense frame을 배제/억제하는 효과"와
  다르지 않다는 뜻이고, 여전히 크게 양수라면 ERCB의 가중치 자체가 keyframe-pool-RR보다도
  추가 가치를 낸다는 뜻이다.
- 실패/미완료 run은 조용히 제외되며(summary_kfrr.json의 count로 확인 가능), 완료된 job이
  하나도 없는 조건은 표에서 count=0으로 나타난다.
"""
    (HERE / "summary_kfrr.md").write_text(result)
    print(json.dumps({
        "main_manifest_state": main_manifest["state"],
        "kfrr_manifest_state": kfrr_manifest["state"],
        "rows": len(rows), "aggregate_by_condition": by_condition,
    }, indent=2))


if __name__ == "__main__":
    main()
