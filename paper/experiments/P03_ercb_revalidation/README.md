# P03 — C1 위에서 ERCB 재검증

| 항목 | 값 |
|---|---|
| 세우는 claim | C2, C4, C6 |
| 비교 arm | ① token만 ② token+ERCB(K=128, β=0.02) ③ K/β sweep {1,32,128}×{0,0.02} |
| 핵심 지표 | held-out PSNR, ρ_H, lifetime count middle/first, 최종 pool 크기 |
| 장면 | aria1253, rot |
| 머신 | 5090 |
| 담당 | 나 |
| 상태 | 미착수 |

> exp72가 실패한 **pool-independence와 lifetime 균등화를 다시 판정**하는 실험. exp72와 달리 admission이 고정되어야 ordering 효과가 분리된다.

- **계획(사전등록)** → [`plan/CURRENT.md`](plan/CURRENT.md)
- **결과** → [`result.md`](result.md) (append-only)
- **평가 계약** → [`../protocol/CURRENT.md`](../protocol/CURRENT.md)

## 버전 이력

| 종류 | 버전 | 날짜 | 트리거 | 무엇이 바뀌었나 |
|---|---|---|---|---|
| plan | [v01](plan/v01_2026-09-05_initial.md) | 2026-09-05 | paper/ 폴더 개설 | 최초 작성 |
