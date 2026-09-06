# 3.2 Entropy-Regularized Count Balancing — ERCB (★C2)

| 항목 | 값 |
|---|---|
| 한 줄 claim | count imbalance 감소와 random shuffle 근접을 하나의 entropy-regularized 문제로 묶으면 해가 p(i)∝exp(-βn_i)다 |
| latex 대상 | `latex/sec/3_method.tex` |
| 담당 | 나 |
| 상태 | plan v01 / draft 없음 |
| 근거 실험 | P03 |
| 그림·표 | Fig.5 |
| 목표 분량 | 0.82 p (5문단 84줄 + 수식2 6줄) |
| ⚠ claim boundary | exp72에서 lifetime 균등화는 실패 — P03 재검증 전 '균등화한다' 주장 금지 |

- **무엇을 쓸지** → [`plan/CURRENT.md`](plan/CURRENT.md)
- **실제 문장** → `draft/CURRENT.md` (영어 문장을 쓰기 시작할 때 생성)

## 버전 이력

| 종류 | 버전 | 날짜 | 트리거 | 무엇이 바뀌었나 |
|---|---|---|---|---|
| plan | [v01](plan/v01_2026-09-05_initial.md) | 2026-09-05 | paper/ 폴더 개설 | 최초 작성 |
| plan | [v02](plan/v02_2026-09-06_derivation-flow.md) | 2026-09-06 | P3·P4 가 항목당 3줄로 과부하 | **정확한 대상 → 완화 1·2·3** 으로 재구성. 0.68p → 0.82p. 수식 3 → 2. 등식 감사를 P3 끝으로, Plackett–Luce 를 P4 첫 문장으로. `ρ_H`→§4, replay 선행→§2.3 |

> 절 제목의 근거는 [`notes/naming/CURRENT.md`](../../../notes/naming/CURRENT.md). 제목은 확정이며 바꾸지 않는다.
