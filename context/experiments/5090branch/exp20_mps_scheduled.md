# exp20 — 2-Phase Lambda Schedule (강한 초기 pull)

- 날짜: 2026-07-05
- result dir: `results/experiments/exp20_mps_scheduled_20260705_094147`
- config: `mps_depthpro_scheduled.yaml`
- 관련 라운드: `rounds/round7_plateau_mps.md`

## 목적

densification 기간(1k-7k)에 강한 plateau pull(λ=0.10)로 Gaussian을 미리 당겨두고, 이후 photometric loss에 주도권을 넘기는 스케줄 검증.

## 설정 (exp19 대비 diff)

- lambda_schedule: [1000, 0.10] → [7000, 0.03] → [15000, 0.00]
- start_iter: 5000 → 1000

## 결과

| 항목 | 값 | vs exp08 |
|---|---:|---:|
| PSNR@7k | 27.13 | - |
| PSNR@30k | 31.693 | -1.32 dB |

## Verdict

**기각** — densification 중 강한 plateau가 오히려 geometry 형성을 방해. PSNR@7k부터 이미 exp19보다 낮음. "densification 이전/중 개입은 위험"의 근거.
