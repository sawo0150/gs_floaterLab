# ATTR — attribute the bulk gain over vanilla

Status: **Exp124 representative 3-family gate complete; full causal attribution remains active.**

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
