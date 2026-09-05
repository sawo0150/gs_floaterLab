# P01 — GPU-Token Admission 구현 및 이론식 대조

| 항목 | 값 |
|---|---|
| 세우는 claim | B1, B4, B5 |
| 비교 arm | 완료: baseline vs token/no-prepurchase; 남음: token/carry, 순수 gate-removal |
| 핵심 지표 | A(t) vs A*(t) 일치도, admission 간격의 pool-size 의존성, 최종 pool 크기 |
| 장면 | aria1253, aria301_305 |
| 머신 | 5090 완료; 5070Ti 남음 |
| 담당 | 나 |
| 상태 | **부분 완료** — exp73 7 run·526 poll |

> exp73은 원래 사전등록 계획 이전/밖에서 수행된 탐색적 부분 결과다. token law는 확인했지만
> carry 비교·순수 gate 효과·hardware rate는 아직 확인하지 않았다.

- **계획(사전등록)** → [`plan/CURRENT.md`](plan/CURRENT.md)
- **결과** → [`result.md`](result.md) (append-only)
- **평가 계약** → [`../protocol/CURRENT.md`](../protocol/CURRENT.md)

## 버전 이력

| 종류 | 버전 | 날짜 | 트리거 | 무엇이 바뀌었나 |
|---|---|---|---|---|
| plan | [v01](plan/v01_2026-09-05_initial.md) | 2026-09-05 | paper/ 폴더 개설 | 최초 작성 |

## exp73 연결

- [P01 결과 기록](result.md)
- [`context/experiments/exp73/` 카드](../../../context/experiments/exp73/exp73_gate_free_token_admission_real_ablation.md)
- [machine-readable evidence](../../../context/experiments/exp73/evidence/exp73_gate_free_token_admission_summary.json)
