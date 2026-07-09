# exp25 — Enlarged Tau + Lambda Schedule (plateau 계열 현재 최선)

- 날짜: 2026-07-05
- result dir: `results/experiments/exp25_mps_tau_enlarged_20260705_121443`
- config: `mps_depthpro_tau_enlarged.yaml`
- script: `scripts/experiments/run_exp25_tau_enlarged.sh`
- 관련 라운드: `rounds/round7_plateau_mps.md`

## 목적

plateau 반경(tau)을 2-3배 키워 표면 Gaussian 대부분(40-60%)을 plateau 안에 넣고, gradient가 진짜 floater에만 타게팅되게 함. tau 효과 단독 검증 (opacity_weight/exp_loss/adaptive_prune 모두 OFF).

## 설정 (exp19 대비 diff)

- alpha_n: 0.4 → 0.8, alpha_t: 0.9 → 1.8 (2x)
- tau_n_max: 0.30 → 0.80m (2.7x), tau_t_max: 0.60 → 2.00m (3.3x)
- lambda: 0.01 고정 → schedule [7000, 0.10] → [15000, 0.03]
- start_iter: 5000 → 7000 (densification 이후)

## 결과

| 항목 | 값 | 비교 |
|---|---:|---|
| PSNR@7k | 28.23 | - |
| PSNR@30k | **32.969** | exp08 대비 -0.04 dB, exp13 대비 +0.11 dB |

## Verdict

**보류 (유망)** — MPS plateau 계열 최선. PSNR은 baseline과 사실상 동급까지 회복. **단, plateau의 목적인 floater/ambiguity 지표 개선 여부가 미확인** — 이것이 STATUS 1순위 할 일. floater 개선이 확인되면 채택으로 승격.

## 남은 검증

- ambiguity/positive_ratio, gaussian/large_scale_ratio (tfevents에 있음)
- 저장된 PLY의 Z-outlier count, |Z|max
- exp08/exp13 대비 고정 view 시각 비교
