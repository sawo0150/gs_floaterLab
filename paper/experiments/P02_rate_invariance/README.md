# P02 — Rate Invariance (하드웨어·입력속도 불변성)

| 항목 | 값 |
|---|---|
| 세우는 claim | B2 |
| 비교 arm | 같은 trace × {5090, 5070Ti} × pace {0.75, 1.0, 1.5, 2.0}× |
| 핵심 지표 | S(t)당 admission 수, held-out PSNR range, topology drop |
| 장면 | aria1253, rot |
| 머신 | 양쪽 동시 |
| 담당 | 나 |
| 상태 | 미착수 |

> **Fig.4가 여기서 나온다. C1의 유일한 실증.** 두 GPU가 같은 trace·같은 config임을 먼저 검증할 것.

- **계획(사전등록)** → [`plan/CURRENT.md`](plan/CURRENT.md)
- **결과** → [`result.md`](result.md) (append-only)
- **평가 계약** → [`../protocol/CURRENT.md`](../protocol/CURRENT.md)

## 버전 이력

| 종류 | 버전 | 날짜 | 트리거 | 무엇이 바뀌었나 |
|---|---|---|---|---|
| plan | [v01](plan/v01_2026-09-05_initial.md) | 2026-09-05 | paper/ 폴더 개설 | 최초 작성 |
