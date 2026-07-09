# exp22 — Exponential Loss Kernel

- 날짜: 2026-07-05
- result dir: `results/experiments/exp22_mps_exploss_20260705_104742`
- config: `mps_depthpro_exploss.yaml`
- script: `scripts/experiments/run_exp22_exploss.sh` (`run_seq_22_23_24.sh`로 순차 실행)
- 관련 라운드: `rounds/round7_plateau_mps.md`

## 목적

quadratic hinge 대신 지수 커널 `exp(clamp(D-1,0,8))-1`로 먼 floater에 훨씬 큰 gradient(D=5에서 54.6x vs quadratic 8x)를 주는 것 검증.

## 설정 (exp21 대비 diff)

- exp_loss: true
- lambda: 0.10 → 0.05 (exp loss가 3-7x 커서 절반으로)

## 결과

| 항목 | 값 | vs exp08 |
|---|---:|---:|
| PSNR@7k | 28.00 | - |
| PSNR@30k | 29.917 | -3.10 dB |

## Verdict

**기각** — exp21보다 더 나쁨. 강한 커널 + opacity weight 조합은 과격한 개입으로 photometric 최적화를 지속적으로 방해.
