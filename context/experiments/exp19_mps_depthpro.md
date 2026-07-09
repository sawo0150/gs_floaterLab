# exp19 — MPS + DepthPro Ellipsoidal Plateau (기본형)

- 날짜: 2026-07-05
- result dir: `results/experiments/exp19_mps_depthpro_20260705_085950`
- config: `3dgs-custom/configs/plateau_loss/mps_depthpro_v4.yaml`
- script: `scripts/experiments/run_exp19_mps_depthpro.sh`
- 관련 라운드: `rounds/round7_plateau_mps.md`

## 목적

Round 6에서 ORB init 기준 최선이었던 DepthPro ellipsoidal plateau를 **MPS full 데이터**(exp08 하이퍼파라미터)에 적용했을 때 baseline 대비 효과 확인.

## 설정 (exp08 대비 diff)

- plateau: ellipsoidal, DepthPro v4 앵커 (`anchors_all_depth_pro.npy`, D_target=0.50m)
- alpha_n=0.4, alpha_t=0.9, tau_n_max=0.30, tau_t_max=0.60
- start_iter=5000, lambda=0.01 (고정)
- pop2_zclip: Z≥2.0m, iter 5000부터 1000 간격

## 결과

| 항목 | 값 | vs exp08 |
|---|---:|---:|
| PSNR@7k | 28.09 | - |
| PSNR@30k | 32.753 | -0.26 dB |

## Verdict

**보류** — λ=0.01 고정으로는 PSNR 손실만 확인. 이후 exp25(tau 확대)가 이 설정을 개선해 -0.04dB까지 회복. floater 지표 비교는 미완.
