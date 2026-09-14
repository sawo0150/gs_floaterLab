# exp21 — Opacity-weighted Plateau Loss

- 날짜: 2026-07-05
- result dir: `results/experiments/exp21_mps_opacity_weighted_20260705_101731`
- config: `mps_depthpro_opacity_weighted.yaml`
- 관련 라운드: `rounds/round7_plateau_mps.md`

## 목적

high-opacity floater에 xyz와 opacity 양쪽으로 gradient를 줘서 "표면으로 이동하거나 투명해져서 pruning되거나" 유도.

## 설정 (exp19 대비 diff)

- opacity_weight: true
- start_iter: 5000 → 7000 (densification 이후)
- lambda: 0.01 → 0.10 (고정, 스케줄 없음)

## 결과

| 항목 | 값 | vs exp08 |
|---|---:|---:|
| PSNR@7k | 28.14 | - |
| PSNR@30k | 30.770 | -2.24 dB |

## Verdict

**기각** — opacity 경로로 gradient가 새면서 정상 Gaussian까지 투명화된 것으로 추정. λ=0.10 고정이 후반까지 계속 눌러 PSNR 대폭 손실.
