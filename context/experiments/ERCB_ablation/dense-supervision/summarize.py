#!/usr/bin/env python3
"""Table for paper §3.1: view density K vs streaming budget.

Builds the evidence the section's argument needs, in the incremental setting
rather than the batch one the ledger currently cites (exp51/exp66):

  A2 (P1)  inter-keyframe frames are usable supervision
           -> at each budget, the best K > 1 beats K = 1 (keyframe-only)
  A3 (P2)  the optimal view-set density depends on the compute budget
           -> the argmax K* moves as the per-interval update budget changes

K = per-interval pool: the VIGS keyframe plus K-1 in-between frames
(farthest-point-in-time). K=1 is keyframe-only; K=all is every arrived frame.
Everything else is inherited verbatim from benchmark-B, with densification as
the single change, so the numbers sit next to the existing ERCB tables.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH_B = HERE.parent / "benchmark-B"
BUDGETS = (15, 30, 60)


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


def collect() -> tuple[dict, dict, dict]:
    """(psnr, pool_size, updates) keyed by (family, scene, budget, k_label)."""
    psnr, pool, updates = {}, {}, {}
    endpoints = json.loads((HERE / "evidence/manifest.json").read_text())
    for job in endpoints["jobs"]:
        if job.get("state") != "complete":
            continue
        label = "1" if job["arm"] == "kf_only" else "all"
        key = (job["family"], job["scene"], job["budget"], label)
        psnr[key] = final_psnr(job["output"], job["total_iterations"])
        updates[key] = job["total_iterations"]
        names = job.get("eligible_names_file")
        if names:
            pool[key] = len(json.loads(Path(names).read_text())["arrival_iteration_by_name"])
        else:
            schedule = json.loads(Path(job["schedule"]).read_text())
            pool[key] = len(schedule["arrival_iteration_by_name"])
    sweep_path = HERE / "evidence/manifest_k.json"
    if sweep_path.is_file():
        for job in json.loads(sweep_path.read_text())["jobs"]:
            if job.get("state") != "complete":
                continue
            key = (job["family"], job["scene"], job["budget"], str(job["k"]))
            psnr[key] = final_psnr(job["output"], job["total_iterations"])
            pool[key] = job["pool_frames"]
            updates[key] = job["total_iterations"]
    return psnr, pool, updates


def main() -> None:
    psnr, pool, updates = collect()
    scenes = sorted({(f, s) for f, s, _, _ in psnr})
    ks = ["1", "2", "4", "8", "all"]

    lines = ["| scene | budget (upd/interval) | " + " | ".join(f"K={k}" for k in ks)
             + " | K* | best−K1 |",
             "|---|---|" + "---:|" * (len(ks) + 2)]
    shifts, gains = {}, {b: [] for b in BUDGETS}
    for family, scene in scenes:
        for budget in BUDGETS:
            row = {k: psnr.get((family, scene, budget, k)) for k in ks}
            if row.get("1") is None:
                continue
            present = {k: v for k, v in row.items() if v is not None}
            best = max(present, key=present.get)
            gain = present[best] - present["1"]
            gains[budget].append(gain)
            shifts.setdefault((family, scene), {})[budget] = best
            cells = []
            for k in ks:
                value = row[k]
                if value is None:
                    cells.append("—")
                elif k == best and best != "1":
                    cells.append(f"**{value:.2f}**")
                else:
                    cells.append(f"{value:.2f}")
            lines.append(f"| {family}/{scene} | {budget} | " + " | ".join(cells)
                         + f" | **{best}** | {gain:+.2f} |")

    pool_lines = ["| scene | budget | " + " | ".join(f"K={k}" for k in ks) + " |",
                  "|---|---|" + "---:|" * len(ks)]
    for family, scene in scenes:
        for budget in BUDGETS:
            if (family, scene, budget, "1") not in updates:
                continue
            total = updates[(family, scene, budget, "1")]
            cells = []
            for k in ks:
                size = pool.get((family, scene, budget, k))
                cells.append(f"{total/size:.1f}" if size else "—")
            pool_lines.append(f"| {family}/{scene} | {budget} | " + " | ".join(cells) + " |")

    summary_gain = " · ".join(
        f"budget {b}: {statistics.fmean(v):+.2f}dB ({sum(1 for x in v if x > 0)}/{len(v)})"
        for b, v in gains.items() if v)
    shift_lines = [f"- {f}/{s}: " + " → ".join(f"budget{b} K*={d[b]}" for b in BUDGETS if b in d)
                   for (f, s), d in shifts.items()]

    report = f"""# Table X — per-interval view density K vs streaming budget

논문 §3.1의 두 전제를 **incremental 조건에서** 세우기 위한 표다. 현재 claim ledger는
A2/A3의 근거로 배치 실험(exp51/exp66)만 인용하고 있다.

- **A2 (P1)**: keyframe 사이 frame이 쓸 수 있는 supervision이다 → 각 budget에서 최적
  `K>1`이 `K=1`(keyframe-only)을 이겨야 한다.
- **A3 (P2)**: 최적 view-set 밀도가 compute budget에 따라 움직인다 → `K*`가 budget에
  따라 이동해야 한다.

`K` = interval당 pool 크기. VIGS keyframe 1장 + 그 interval의 중간 frame `K-1`장
(keyframe을 시드로 한 farthest-point-in-time 선택). `K=1`은 keyframe-only,
`K=all`은 도착한 모든 frame.

## 계약

benchmark-B에서 그대로 상속: stride20 dataset/init, causal arrival schedule,
event당 update 예산(15/30/60), `causal_rr`, seed 0, `-r 4`, RGB-only loss,
llffhold-8 held-out, zero-tail, scene·budget별 총 update 수.
**benchmark-B와 다른 것은 densification을 켠 것 하나뿐**이며 그 스케줄은 각 run 자기
예산의 고정 비율(1/60에서 시작, 1/2까지, opacity reset 1/10)로 장면 무관하게 통일했다.

## 결과 — held-out PSNR (dB)

{chr(10).join(lines)}

평균 이득(최적 K − K=1): {summary_gain}

### K* 이동 (A3)

{chr(10).join(shift_lines) if shift_lines else "- (아직 데이터 부족)"}

## 왜 최적점이 생기는가 — view당 update 수

같은 예산을 더 많은 view가 나눠 가지므로 K가 커질수록 view당 서비스가 줄어든다.

{chr(10).join(pool_lines)}

## 해석 제한

- pose/init은 사전 VIGS run의 고정 replay다. strict online localization 근거가 아니다.
- densification이 켜져 있어 arm별 최종 Gaussian 수가 다르다.
- held-out이 llffhold-8이라 held-out frame이 중간 frame과 시간적으로 인접하다. 모든
  arm이 동일 held-out을 쓰지만 이 인접성은 큰 K에 유리할 수 있다.
- 단일 seed다. 이 프로젝트의 run-to-run PSNR 분산은 과거 ±0.33dB로 실측된 바 있다.
"""
    (HERE / "summary.md").write_text(report)
    (HERE / "evidence/summary.json").write_text(json.dumps({
        "psnr": {"/".join(map(str, k)): v for k, v in psnr.items()},
        "pool": {"/".join(map(str, k)): v for k, v in pool.items()},
        "updates": {"/".join(map(str, k)): v for k, v in updates.items()},
    }, indent=2) + "\n")
    print(report)


if __name__ == "__main__":
    main()
