# 논문 실험 REGISTRY

> **append-only.** 기존 행을 수정하지 말고, 정정은 아래 "정정" 절에 새로 적는다.
> 계획 전체는 [`../plan/experiment_table/CURRENT.md`](../plan/experiment_table/CURRENT.md).
> 공통 평가 계약은 [`protocol/CURRENT.md`](protocol/CURRENT.md).

| ID | 목적 | 세우는 claim | 머신 | 담당 | 상태 | 카드 |
|---|---|---|---|---|---|---|
| P01 | GPU-token admission 구현 + 이론식 대조 | B1, B4, B5 | 5070Ti | 나 | 미착수 | [P01](P01_token_admission/) |
| P02 | rate invariance (5090 vs 5070Ti, pace sweep) | B2 | 양쪽 | 나 | 미착수 | [P02](P02_rate_invariance/) |
| P03 | C1 위에서 ERCB 재검증 + K/β sweep | C2, C4, C6 | 5090 | 나 | 미착수 | [P03](P03_ercb_revalidation/) |
| P04 | carve incremental 이식 | D3 | 5070Ti | 팀원 | 진행중 | [P04](P04_carve_incremental/) |
| P05 | cross-scene 일반화 | A4 | 양쪽 | 나 | 미착수 | [P05](P05_cross_scene/) |
| P06 | baseline 비교 | A4 | 양쪽 | 나 | 미착수 | [P06](P06_baselines/) |

## 완료 시 3종 세트 (필수)

`context/` 의 exp 카드 규칙을 그대로 따른다.

1. `Pnn_*/result.md` 에 결과 추가 (**append-only**)
2. 이 REGISTRY의 상태 열 갱신
3. `../PAPER_STATUS.md` "최근 흐름"에 날짜 붙여 새 항목 추가

추가로, 결과가 claim을 바꾸면:

4. `../plan/claims/` 를 `newver.sh` 로 버전 업

## 정정

- **2026-09-05 — P01 상태 정정:** 위 최초 행의 “미착수”를 **부분 완료**로 정정한다.
  exp73에서 5090 기준 baseline vs token-only/no-prepurchase를 aria1253·aria301_305에 실행했고,
  7개 gate-free run·526 admission poll에서 token-law 정수 오차 0을 확인했다. 다만 token/carry,
  동일 bootstrap을 유지한 순수 gate-removal, 5070Ti/slowdown arm은 미실행이다.
