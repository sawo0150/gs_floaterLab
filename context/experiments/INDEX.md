# Experiment Index

전 실험 목록. 상세는 각 카드 참조. baseline 대비 Δ는 PSNR@30k 기준.

## Full 30k, MPS init 1311장 (메인 트랙)

| Exp | 날짜 | 한 줄 설정 | PSNR@30k | vs exp08 | Verdict | 카드 |
|---|---|---|---:|---:|---|---|
| exp01 | 06-16 | full baseline (886k Gaussians) | - | - | 기준선 | [exp01-12](exp01-12_param_sweep.md) |
| exp02 | 06-16 | sparse densification | 33.377 | +0.37 | 최고 PSNR이나 large-scale 위험 | 〃 |
| exp03 | 06-16 | + large-scale 개선 | 33.052 | +0.04 | 보류 | 〃 |
| exp04 | 06-16 | 구조 개선 계열 | 32.831 | -0.18 | 기각 | 〃 |
| exp05 | 06-16 | beta1=0.95 | 조기중단 | - | 기각 | 〃 |
| exp06 | 06-16 | beta1=0.85 | 32.879 | -0.13 | beta1=0.85 채택 | 〃 |
| exp07 | 06-16 | pruning 완화 | 조기중단 | - | 기각 | 〃 |
| **exp08** | 06-16 | dens_until7000 + prune001 + beta1_low | **33.012** | 기준 | **현재 best baseline** | [exp08](exp08_best_baseline.md) |
| exp09 | 06-16 | densify_until=5000 | 조기중단 | - | 너무 이름, 기각 | [exp01-12](exp01-12_param_sweep.md) |
| exp10 | 06-16 | position LR 낮춤 | 32.574 | -0.44 | 기각 | 〃 |
| exp11 | 06-16 | position LR 완화 | 32.682 | -0.33 | 기각 | 〃 |
| exp12 | 06-16 | + sparse depth prior (0.01→0.002) | 32.587 | -0.43 | 기각 (outlier 고정 위험) | 〃 |
| exp13 | 06-30 | + camera-bound pcd filter | 32.855 | -0.16 | **Pop1 해결 확정** | [exp13](exp13_pcd_filter.md) |
| exp19 | 07-05 | + DepthPro ellipsoidal plateau (λ=0.01) | 32.753 | -0.26 | 보류 | [exp19](exp19_mps_depthpro.md) |
| exp20 | 07-05 | + λ schedule 0.10→0.03→0 | 31.693 | -1.32 | 기각 | [exp20](exp20_mps_scheduled.md) |
| exp21 | 07-05 | + opacity_weight, λ=0.10 | 30.770 | -2.24 | 기각 | [exp21](exp21_mps_opacity_weighted.md) |
| exp22 | 07-05 | + exp loss kernel, λ=0.05 | 29.917 | -3.10 | 기각 | [exp22](exp22_mps_exploss.md) |
| exp23 | 07-05 | + adaptive prune (d>1.5m) | 26.655 | -6.36 | 기각 (후반 붕괴) | [exp23](exp23_mps_adaptive_prune.md) |
| exp24 | 07-05 | exp loss + adaptive prune | 미완 (27k Terminated) | - | 보류 (낮은 우선순위) | [exp24](exp24_mps_exp_and_prune.md) |
| **exp25** | 07-05 | + enlarged tau (2-3x) + λ 0.10→0.03 | **32.969** | **-0.04** | **plateau 최선, floater 지표 검증 필요** | [exp25](exp25_mps_tau_enlarged.md) |
| exp26 | 07-05 | + enlarged tau + λ=1.0→0.03 | 32.706 / 32.674 (2회) | -0.31 | 기각 (λ=1.0 과함) | [exp26](exp26_mps_lambda1.md) |
| exp27 | 07-09 | anchor 7,338 pts를 init으로 (미정렬) | 29.540 | -3.47 | **좌표계 버그 발견** — anchor는 Atlas world였음 | [exp27](exp27_anchor_init.md) |
| exp27b | 07-09 | MPS 랜덤 7,338 init (대조군) | 30.583 | -2.43 | 개수 통제 대조군 | 〃 |
| exp27c | 07-09 | 정렬된 anchor 7,338 init | 31.611 | -1.40 | **anchor 배치 합격** (대조군 +1.03dB), \|Z\|>4m 8개 | 〃 |

> **⚠ 좌표계 발견 (07-09)**: exp19~26의 plateau anchor는 MPS world가 아닌 raw Atlas world였다 (표면 대비 median 0.48m, scale x0.95 오차). **Round 7 결론은 정렬 anchor로 재검증 필요.** 상세: [exp27](exp27_anchor_init.md)

## ORB init 656장 (Round 6, plateau 검증 트랙 — baseline 29.023)

| Exp | 날짜 | 한 줄 설정 | PSNR@30k | vs orb_baseline | Verdict | 카드 |
|---|---|---|---:|---:|---|---|
| exp_orb_baseline | 07-05 | plateau 없음 | 29.023 | 기준 | 기준선 | [round6](../rounds/round6_plateau_orb.md) |
| exp15 | 07-05 | spherical plateau, ORB 앵커 | 27.908 | -1.10 | 기각 (과밀집→투명화) | 〃 |
| exp16 | 07-05 | ellipsoidal plateau, ORB 앵커 | 28.924 | -0.10 | ellipsoidal 채택 | 〃 |
| exp17 | 07-05 | ellipsoidal, Metric3D 앵커 | 27.668 | -1.35 | 기각 (앵커 품질) | 〃 |
| exp18 | 07-05 | ellipsoidal, DepthPro 앵커 | 28.934 | -0.09 | DepthPro 앵커 채택 | 〃 |

## 기타 (닫힌 축)

| Exp | 내용 | 결과 | 기록 |
|---|---|---|---|
| exp13_vggt64 (번호 중복 주의) | VGGT64 3DGS 7k | Test PSNR 17.04 | [archive/vggt_evaluation.md](../archive/vggt_evaluation.md) |
| exp14 | OpenMAVIS64/MPS 3DGS 7k | Test PSNR 18.65 | 〃 |

> **번호 중복 주의**: `exp13`은 pcd_filter (메인 트랙)와 vggt64 (VGGT 트랙) 두 개가 존재. result dir 이름으로 구분.
