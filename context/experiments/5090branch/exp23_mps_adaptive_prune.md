# exp23 — Adaptive Floater Pruning

- 날짜: 2026-07-05
- result dir: `results/experiments/exp23_mps_adaptive_prune_20260705_111821`
- config: `mps_depthpro_adaptive_prune.yaml`
- 관련 라운드: `rounds/round7_plateau_mps.md`

## 목적

gradient 유도 대신 명백한 floater를 직접 제거: `d_euc > 1.5m AND (opacity > 0.5 OR max_scale > 0.15m)` 조건으로 500 iter마다 pruning.

## 설정 (exp21 대비 diff)

- adaptive_prune: true (d_euc=1.5m, opacity=0.5, scale=0.15m, interval=500, start=7000)
- loss는 exp21과 동일 (quadratic opacity-weighted, λ=0.10)

## 결과

| 항목 | 값 | vs exp08 |
|---|---:|---:|
| PSNR@7k | 28.30 (sweep 중 최고) | - |
| PSNR@30k | 26.655 | **-6.36 dB (최악)** |

## Verdict

**기각** — 7k 시점엔 sweep 중 가장 좋았으나 30k에서 붕괴. 500 iter 간격의 반복 pruning이 정상 Gaussian까지 지속적으로 제거해 후반 수렴을 파괴한 것으로 추정. anchor 거리 기반 hard pruning은 threshold가 매우 보수적이어야 함.
