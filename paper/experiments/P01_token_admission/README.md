# P01 — GPU-Token Admission 구현 및 이론식 대조

| 항목 | 값 |
|---|---|
| 세우는 claim | B1, B4, B5 |
| 비교 arm | ① baseline(maturity gate) ② token/carry ③ token/no-prepurchase |
| 핵심 지표 | A(t) vs A*(t) 일치도, admission 간격의 pool-size 의존성, 최종 pool 크기 |
| 장면 | aria1253 |
| 머신 | 5070Ti |
| 담당 | 나 |
| 상태 | 미착수 |

> **이 실험이 논문의 크리티컬 패스 시작점.** 실패 시 C1은 주장 불가하고 P03도 의미를 잃는다.

- **계획(사전등록)** → [`plan/CURRENT.md`](plan/CURRENT.md)
- **결과** → [`result.md`](result.md) (append-only)
- **평가 계약** → [`../protocol/CURRENT.md`](../protocol/CURRENT.md)

## 버전 이력

| 종류 | 버전 | 날짜 | 트리거 | 무엇이 바뀌었나 |
|---|---|---|---|---|
| plan | [v01](plan/v01_2026-09-05_initial.md) | 2026-09-05 | paper/ 폴더 개설 | 최초 작성 |
