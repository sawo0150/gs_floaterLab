# exp24 — Exp Loss + Adaptive Prune 조합 (미완)

- 날짜: 2026-07-05
- result dir: `results/experiments/exp24_mps_exp_and_prune_20260705_114814`
- config: `mps_depthpro_exp_and_prune.yaml`
- 관련 라운드: `rounds/round7_plateau_mps.md`

## 목적

명백한 floater는 pruning으로 직접 제거 + 애매한 floater는 exp loss gradient로 유도하는 조합 전략.

## 설정

- exp22의 exp_loss + opacity_weight (λ=0.05) + exp23의 adaptive_prune 전부 켬

## 결과

| 항목 | 값 |
|---|---:|
| PSNR@7k | 28.14 |
| PSNR@30k | **없음 — iter 27,170에서 Terminated** (log 참조) |

## Verdict

**보류 (낮은 우선순위)** — 91% 지점에서 프로세스 kill. 다만 구성 요소인 exp22(-3.10dB)와 exp23(-6.36dB)이 단독으로 모두 나빴으므로 재실행 가치 낮음. 7k 시점 궤적도 exp22와 유사.
