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

## OpenMAVIS(ORB) 데이터셋 재현 트랙 — exp30~37 (진행 중, baseline 32.671)

MPS 트랙(exp08~29)에서 검증한 방법들을 실제 목표 데이터셋(OpenMAVIS pose + ORB init, `data/03_rgb_3dgs_full`)으로 재현하는 트랙. exp08과 직접 비교 금지 — exp30이 이 트랙의 기준선.

| Exp | 한 줄 설정 | PSNR@30k | 상태 | 카드 |
|---|---|---:|---|---|
| **exp30** | baseline (ORB 원본 7,205 init) | **32.906** | 완료 — 기준선 (run-to-run 노이즈 ±0.24dB 확인됨) | [exp30-37](exp30_37_orb_native_track.md) |
| exp31 | 일반 anchor(obs≥3, 7,108) init | 32.671 | 완료 | 〃 |
| exp32 | + plateau 기본 tau, 일반 anchor | 32.903 | 완료 (baseline과 동급) | 〃 |
| exp33 | + plateau enlarged tau, 일반 anchor | 32.536 | 완료 (MPS와 반대로 열세, floater는 최소) | 〃 |
| exp34 | 고confidence anchor(obs≥10&fr≥0.5, 1,438) init | 31.970 | 완료 (exp31보다 -0.7dB) | 〃 |
| exp35 | + plateau 기본 tau, 고confidence anchor | 32.799 | 완료 (exp32와 비슷한 패턴) | 〃 |
| exp36 | + plateau enlarged tau, 고confidence anchor | 32.591 | 완료 | 〃 |
| **exp37** | dense confidence+monodepth init (148,564), plateau 없음 | **32.621** | **완료 — \|Z\|>4m=0, 이 트랙 최고 floater 억제** | 〃 |
| exp32_lineage_diag | exp32 + lineage & decoupled grad tracking | 32.903 | 완료 — 진단 및 계보 추적 성공 | [exp32_lineage_diag](exp32_lineage_diag.md) |
| carve_loss_design | (분석만) free-space carve 기반 신규 loss 설계, 수동 라벨 리그전 Round 1~10 | 학습 없음 | 완료 — AUC 0.98, 예산 0.75%로 recall 55%, exp38/39 구현 완료 | [round8_carve_loss_design](../rounds/round8_carve_loss_design.md) · [요약](../rounds/round8_carve_loss_summary.md) |

## Carve Loss 학습 검증 트랙 — exp38~40 (07-12, baseline exp30/30r)

| Exp | 한 줄 설정 | PSNR@30k | region_n/가시 | Verdict | 카드 |
|---|---|---:|---:|---|---|
| exp30r | baseline 재현 (노이즈 측정) | 32.579 | 3,749 / 180 | PSNR 노이즈 ±0.33dB 실측 | [exp38-40](exp38_40_carve_track.md) |
| exp38a | soft0.05+prune+gate | 32.266 | 559 / 27 | 억제 최강, -0.3dB 과비용 | 〃 |
| exp38b | prune+gate만 | 32.663 | 1,744 / 187 | soft가 가시 먼지 주역임을 분리 | 〃 |
| exp38c | softlite0.02+prune+gate | 32.557 | 946 / 33 | PSNR 무손실 스위트스팟 | 〃 |
| exp39 | MPS 트랙 carve (full soft) | 32.666 | (MPS) 가시 96→2 | MPS 전이 성공 | 〃 |
| exp40br | 챔피언 재현 | 32.448 | 462 / 25 | 재현 확인 | 〃 |
| **exp39b** | MPS softlite+force | **32.913** | (MPS) 가시 **0** | **MPS 채택** | 〃 |
| exp40a | prune+gate+**force** | 32.667 | 1,309 / 134 | 3D force 부활 실증 (무비용) | 〃 |
| **exp40b** | softlite+prune+gate+force | **32.576** | **498 / 28** | **채택 — 챔피언 레시피** | 〃 |

> exp30~37 전체 완료 (2026-07-09). 큐 진행 중 발견된 자동 체인 중복 실행 버그와 run-to-run 노이즈(±0.24dB)는 카드 참조.

## 계획 및 신규 트랙 카드

| Exp | 내용 | 상태 | 카드 |
|---|---|---|---|
| exp43 | 교차 장면 완주: rot 점수 AUC 0.98·pseudo-label 정밀도 100% / 305 **depth-anchor carve 재현 성공**(먼지 -83%·PSNR 동급) / 실패 5건 정직 기록 — 결론: carve 성패=앵커 품질 | **완료** | [exp43](exp43_cross_scene_plan.md) |
| exp45 | 채택 큐 4종: 45a 노출 기각(-6dB)·45b dynamic 조건부(깨끗한 init 전제)·44e3 보류(먼지 ×4)·45c progressive resolution 진행 중 | 진행 | [exp44 카드 참조](exp44_fast_geometry_plan.md) |
| exp46 | basin 재프레임: floater=photo loss의 정당한 숏컷 분지 → 압력 대신 '올바른 geometry를 가까운 basin으로'. (a)도달불가=init/(b)환원불가=appearance 이분법 + 다음 실험 7축(원거리 photometric 감쇠 포함) | **완료** | [exp46](exp46_basin_reframe_plan.md) |
| exp47 | 속도 최적화 트랙: 품질 하한 고정하고 속도만 — S1 cuda·S2 carve저빈도·S3 iter·S4 keyframe subset·S5 중간budget. incremental per-chunk 레시피 확정 목적(목표 5분 내) | **완료** | [exp47](exp47_speed_track_plan.md) |
| **exp44** | **고속 geometry 트랙 완료 — 44h 레시피 채택** (스냅 init+densify≤3k+carve, 32.08/7.5분) · 품질 기함 44f(32.67/14분) | **완료** | [exp44](exp44_fast_geometry_plan.md) |
| exp48 | Incremental 3DGS: PPM K=3 + RoMA (Hybrid) 및 온라인 루프 홀인 Selective Opacity Reset 도입 (18.23dB). 종결 — eval 버그(llffhold-8이 test.txt 무시) 규명, 진짜 벽은 저텍스처 영역 + vanilla 3dgs가 online에 안 맞는 틀 | **종결** | [exp48](exp48_incremental_plan.md) |
| exp49 | Photo-SLAM(ORB-SLAM3+GS, CVPR24) 이관: opacity_reset off·상수 LR·times-of-use 슬라이딩 윈도우로 exp48 문제를 설계로 회피한 검증된 online baseline. 빌드 완료(Blackwell+CUDA12.8 호환패치). replay로 Fisheye624 우회 → 배치 baseline → incremental → 방법론 이식 | 계획 | [exp49](exp49_photoslam_plan.md) |
| exp50 | DiskChunGS: Out-of-Core 디스크 스왑 SLAM. B1에서 Fisheye624 라이브 트래킹 root-cause 2건 수정(하드코딩 static_cast, KannalaBrandt-only 게이트) 후 최초 성공(리셋 9~31→0, 매칭 33~76개 지속). 다음: RGB 매핑 카메라 분리 주입 | 진행 | [exp50](exp50_diskchungs_plan.md) |
| exp51 | Incremental mapping 30dB+로: **축A(depth supervision) 완료 — D1-b 23.11→25.29dB(λ=0.5, +2.42)**, 26dB 미만이라 축B(init 중복방지)+C(keyframe 밀도 57→2/3/4배)로 계속 | 진행중 | [exp51](exp51_dense_supervision_plan.md) |
