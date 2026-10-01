# ATTR — attribute the bulk gain over vanilla

> **현재 채택 설정 실행:** [동료용 인계 안내](selected_recipe/HANDOFF.md) — 3:3:6, 40 renders/KF, init1.25×, 보호 opacity pruning 0.1/300. 이전 ablation 기본값과 구분한다.

Status: **Exp124 representative 3-family gate complete; full causal attribution remains active.**

- 2026-10-01 **ADOPTED B**: [main 채택·병합 검증](b_condition_main_adoption/README.md) — `6d200f0f`, KF metric RGBD + dense RGB, normal OFF, warp backward ON; 공식 진입점 4/4 재검증 완료.

- 2026-10-01 **EVIDENCE**: [four-scene fixed40 dense-depth 비교](dense_depth_four_scene/README.md)
  — 24/24 완료, seeds0·1. dense RGB가 PSNR 4/4 최고; dense depth 추가는 −0.066~−0.216dB,
  Aria 독립 front mass/수동 floater 감소와 behind mass 증가를 함께 확인. 기본값 채택·main merge 없음.

## 질문

R4와 비교하는 것이 아니라 official vanilla에 비해 어떤 변경이 동일 physical
render당 품질을 높였는가? 그 변경의 runtime/VRAM/geometry tradeoff는 무엇이며,
논문 contribution으로 일반화할 수 있는가?

## 이미 확정된 사실

- C1/ERCB 이전 Stage0에서 이미 vanilla 대비 약 +1.11 dB가 존재했다.
- Exp109에서 candidate Gaussian 수는 dataset마다 vanilla 대비 0.82×–2.35×로
  달랐지만 모든 dataset에서 이겼다. capacity 하나만으로 전체 gain을 설명할 수 없다.
- 동일 render 수에서도 candidate는 더 많은 view를 한 Adam step에 묶고 Adam
  step 수가 다르다. 따라서 view diversity, gradient sum scale, Adam moment cadence가
  모두 후보 원인이다.
- dense/ERCB는 main result에서 physical render의 약 1.4%뿐이므로 +1.29 dB의
  주원인이라고 주장할 수 없다.

## 사전 등록한 분해 순서

| Arm | 바꾸는 것 | 목적 |
|---|---|---|
| V0 | official vanilla | 기준 |
| V1 | custom backend/cache/kernel만 | 시스템 구현 차이 |
| V2 | D1 native service grouping만 | view/Adam grouping 효과 |
| V3 | online-rank PPM birth만 | capacity/birth 효과 |
| V4 | V2 + V3 | 상호작용과 bulk gain 회복 여부 |
| V5 | V4 + geometry carrier를 보존한 supplementary dense | dense의 독립 추가 가치 |
| V6 | V5에서 RR vs normalized ERCB | ERCB의 선택 정책 가치 |

첫 gate는 RPNG table_01, UTMM square-1, Aria1253의 공통 설정이다. 각 arm은
동일 causal packet마다 동일 physical render credit을 받고, render와 Adam을
별도로 기록한다. 3-family gate 전에는 17-scene으로 확장하지 않는다.

## Exp124 — paper-aligned role service gate

Exp119--123에서 RGB-only dense view가 historical RGB--D keyframe을 직접
대체할 때 view-specific geometry constraint가 손실됨을 확인했다. Exp124는
geometry carrier를 보존한 채 마지막 반복 1개와 기존 aux-KF appearance slot만
dense photometric service로 재배치했다.

- UTMM square-1/RPNG table_01/Aria1253에서 total dense render share
  **11.50/11.03/11.58%**
- normalized ERCB↔RR selection trace 차이 **41/115/57행**
- physical render·Adam·causality·held-out·zero-tail·geometry scope 모두 PASS
- normalized−backbone PSNR 평균 **−0.146190dB**
- normalized−RR 평균 **+0.007519dB**: ERCB quality gain은 미입증

따라서 기존 final의 “dense/ERCB가 약 1%뿐인 문제”는 구조적으로 해소됐지만,
official vanilla 대비 bulk gain의 원인 분해와 strict-live 검증은 아직 남았다.
세부 결과는 [exp124 카드](../../exp124_role_aware_dense_service.md)에 있다.

## 구현 메모

기존 `--official-frontier-parity`는 10-iteration뿐 아니라 isotropic loss와 PGBA
동작까지 함께 바꾸므로 단일요인 arm에 사용할 수 없다. Exp124는 per-event
render ledger와 geometry/appearance role separation을 먼저 구현했으며, 다음
attribution은 이 active path 위에서 V0--V6의 아직 미분리된 schedule/birth 효과를
분해해야 한다.

## 2026-09-25 — dense gain recovery diagnosis

[복원 진단 카드](dense_gain_recovery/README.md): full-Gaussian dense routing은 Aria +0.092/RPNG −0.197dB로 일반화되지 않았다. 실제 IMU pose-refresh 오류 두 가지를 수정하고 6개 CPU regression test를 통과했으나 품질 차이는 +0.028/−0.012dB다. Aria 고정지도에서 1000/5000회 모두 KF-only full이 KF+dense full보다 높아 단순 scope/반복량 변경으로 과거 이득은 복원되지 않았다. 추가 pose alignment는 일부 회복하나 별도 compute를 사용한다. Production은 유지하고 causal dense pose와 view inventory 차이를 다음 분리 대상으로 남긴다.

## 2026-09-25 — hypothesis1 visual pose verified in fixed-map diagnostic

[영상 기반 dense pose 검증](causal_visual_dense_pose/README.md): 동일 Aria 지도·Adam·학습순서에서5000회 mixed 학습의 pose만 바꿔27.7515→28.5812dB(+0.8297), KF-only28.2619보다+0.3193dB로 dense 이득이 복원됐다. IMU refresh-only27.9764보다도+0.6048dB라 알려진 보정 오류만의 효과는 아니다. 반면 causal online pair는Aria−0.0159/RPNG+0.1162dB에 추가3.064/10.513초가 들어 일관된 online/strict 복원은 미완이다. Production은 변경하지 않았다.

## 2026-09-25 — visual pose 교차장면 완료

[3-scene 전이 검증](visual_pose_transfer/README.md): fixed-map5k에서는 visual pose가 원본dense보다3/3 개선하고 KF-only보다2/3 개선했다. 그러나 online pose 추가효과는 +0.014~0.051dB로 작다. Pose만으로 online dense 이득을 복원하지 못했으며, 공통 photometric 학습 경로·실제 count·성장 정책의 연결을 후속 방향으로 정리했다. Production 미변경.

- 2026-09-26 [Dense blur 후보 선별](dense_blur_filter/SUMMARY.md):12runs, dense 이득유지, gate 자체의 PSNR/속도개선은 미확인. opt-in 구현 및 검증 완료.

## 2026-09-26 추가 검증

- [KF RGB-only 대조군](kf_rgb_control/SUMMARY.md)
- [κ / τ / blur 공통 설정 탐색](growth_entropy_blur/SUMMARY.md)

- 2026-09-27 [현재 unified RR vs ERVS](unified_rr_ervs/SUMMARY.md): 3scene 평균ERVS+0.0755dB,2승1패.

- 2026-09-27 [15회예산2×2](unified_rr_ervs/SUMMARY15.md): ERVS효과+dense효과분리,단일seed12run.

- 2026-09-27: [최근 생성 점 보호 pruning-only](protected_prune/SUMMARY.md) — RPNG40 세 조건 한정; 0.7은−0.690dB, 0.1은−0.153dB/GS−55.3%.

## 2026-09-28 recent KF quota

[Window 비율 비교](window_quota/SUMMARY.md): 3:3:6 / 1:5:6 / 0:6:6, 세 장면 fixed40. 작은 recent 몫은 대체로 보존되지만 제거 시 RPNG·UTMM 하락. 채택 3:3:6 유지.
