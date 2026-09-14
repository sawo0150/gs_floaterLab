# exp26 — Enlarged Tau + λ=1.0 강제 이동

- 날짜: 2026-07-05
- result dir: `results/experiments/exp26_mps_lambda1_20260705_133444`, `results/experiments/exp26_mps_lambda1_20260705_140526` (2회 실행, 둘 다 30k 완주)
- config: `mps_depthpro_lambda1_schedule.yaml`
- 관련 라운드: `rounds/round7_plateau_mps.md`

## 목적

exp25의 enlarged tau를 유지한 채 phase 1에서 λ=1.0으로 photometric을 압도해 floater를 강제 이동시키고, 이후 점진적으로 photometric에 주도권 반환.

## 설정 (exp25 대비 diff)

- lambda_schedule: [7000, 1.00] → [15000, 0.10] → [22000, 0.03]

## 결과

| 항목 | run1 | run2 | vs exp08 |
|---|---:|---:|---:|
| PSNR@7k | 28.14 | 28.25 | - |
| PSNR@30k | 32.706 | 32.674 | -0.31 dB |

## Verdict

**기각** — λ=1.0 phase가 photometric 최적화를 8k iter 동안 압도한 손실을 후반에 회복 못 함. exp25(max λ=0.10)보다 일관되게 나쁨. **λ는 0.10 근처가 상한**이라는 근거.
