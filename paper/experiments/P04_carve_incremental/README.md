# P04 — Carve Loss의 Incremental 이식

| 항목 | 값 |
|---|---|
| 세우는 claim | D3 |
| 비교 arm | ① carve off ② 현 v7-64 ③ 이식판 |
| 핵심 지표 | region GT AUC/AP, precision@0.75% budget, held-out ΔPSNR, score-age p95 |
| 장면 | aria1253, 301_305 |
| 머신 | 5070Ti |
| 담당 | 팀원 |
| 상태 | 진행중 |

> ⚠ §3.4를 독립 contribution으로 낼지 scheduler lane으로 낼지 **미합의**. 결정 전까지 실험 설계는 두 안 모두를 지지하도록 둔다.

- **계획(사전등록)** → [`plan/CURRENT.md`](plan/CURRENT.md)
- **결과** → [`result.md`](result.md) (append-only)
- **평가 계약** → [`../protocol/CURRENT.md`](../protocol/CURRENT.md)

## 버전 이력

| 종류 | 버전 | 날짜 | 트리거 | 무엇이 바뀌었나 |
|---|---|---|---|---|
| plan | [v01](plan/v01_2026-09-05_initial.md) | 2026-09-05 | paper/ 폴더 개설 | 최초 작성 |
