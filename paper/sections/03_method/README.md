# 3. Method

latex 대상: `latex/sec/3_method.tex` (소절 전체가 한 파일에 들어간다)

> 본문에서 가장 두꺼운 절(3.25p). 유도 전문은 Supplementary로 밀고 결과 식과 직관만 남긴다.

| 소절 | 분량 | 문단 | 계획 문서 |
|---|---:|---|---|
| [(도입) Method opening](3-0_overview/) | 0.25 p | roadmap 1문단 + `Notation.` run-in | `3-0_overview/plan/CURRENT.md` |
| [3.1 Compute-Paced View Growth (★C1)](3-1_compute_paced_view_growth/) | 1.0 p | 5 (`Slot placement.` run-in 포함) | `3-1_compute_paced_view_growth/plan/CURRENT.md` |
| [3.2 Entropy-Regularized Count Balancing — ERCB (★C2)](3-2_ercb/) | 0.95 p | 5 | `3-2_ercb/plan/CURRENT.md` |
| [3.3 Causal Free-Space Carving (★C3)](3-3_carve/) | 1.0 p | — (팀원) | `3-3_carve/plan/CURRENT.md` |

## 진단 소절을 두지 않는다 (2026-09-06)

코퍼스 11편에서 §3 소절 구성을 세어보니 **진단에 소절을 준 것은 CaRtGS 하나뿐**이었다.

| 논문 | 진단 소절 |
|---|---|
| Taming3DGS, LM-RS, chen2026cover, MonoGS, Point-SLAM, EDGS, SparseGS, CoMapGS | **없음** |
| CaRtGS (`A. Computational Misalignment`) | 있음 |

지배적 패턴은 **진단을 각 소절 첫 문단(P1)에 분산**하는 것이다 (taming3dgs §3.2 형식).
그리고 **"세 결정으로 분해"라는 중심 주장은 §1 이 진다** — taming3dgs 도 contribution bullet 을
§1 에 두고 §3 도입에서 한 번 훑을 뿐이다.

> ⚠ `notes/structure_survey/cartgs.md` 는 A↔C 대칭을 "§3 의 핵심 구조"라고 썼는데
> **한 편만 보고 일반화한 것**이다. 그 파일 머리에 정정을 달아뒀다.

## 절 제목은 확정이다

근거는 [`../../notes/naming/CURRENT.md`](../../notes/naming/CURRENT.md).
2026-09-06 변경: 옛 `3-2_trajectory_membership` 은 기여로 세지 않기로 하여
`3-1_.../absorbed/` 로 옮겼고 §3.1 의 run-in 볼드 한 문단이 된다.
Preliminaries 는 독립 절로 빼지 않고 도입의 `Notation.` run-in 이 된다.

전체 지도는 [`../README.md`](../README.md), 서사는
[`../../plan/outline/CURRENT.md`](../../plan/outline/CURRENT.md).
