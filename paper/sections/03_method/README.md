# 3. Method

latex 대상: `latex/sec/3_method.tex` (소절 전체가 한 파일에 들어간다)

> 본문에서 가장 두꺼운 절(3.25p). 유도 전문은 Supplementary로 밀고 결과 식과 직관만 남긴다.

| 소절 | 분량 | 문단 | 계획 문서 |
|---|---:|---|---|
| [(도입) Method opening](3-0_overview/) | 0.17 p | roadmap 1문단 (7문장 19줄) | `3-0_overview/plan/CURRENT.md` |
| [3.1 Compute-Paced View Growth (★C1)](3-1_compute_paced_view_growth/) | 0.83 p | **5** + `Slot placement.` run-in (12/12/16/10/12/6줄) | `3-1_compute_paced_view_growth/plan/CURRENT.md` |
| [3.2 Entropy-Regularized Count Balancing — ERCB (★C2)](3-2_ercb/) | 0.68 p | 5 (10/10/12/14/20줄) | `3-2_ercb/plan/CURRENT.md` |
| [3.3 Causal Free-Space Carving (★C3)](3-3_carve/) | 0.36 p → 0.7 p | — (팀원. 채워지면 §3.1 수준) | `3-3_carve/plan/CURRENT.md` |

§3 현재 2.05 p, 팀원 §3.3 이 채워지면 **≈ 2.4 p**. 옛 계획은 3.25 p 였다.

> §3.1 만 5문단이다. taming3dgs §3.2 는 4문단이고 우리 P2–P5 가 거기 1:1로 대응하는데,
> **P1("왜 keyframe 밖까지 받아들이나")이 한 문단 더 든다.** taming3dgs 는 *왜 densify 하나*를
> 설명할 필요가 없지만 우리는 그 선택 자체를 설명해야 하기 때문이다. 근거는 claims A2·A3.

## 분량은 코퍼스 실측으로 잡는다 (2026-09-06)

같은 성격(메커니즘 명세) 소절의 총 줄수, 2단 기준. Taming3DGS 는 1단이라 단어 수로 환산했다.

| 소절 | 줄 | 수식 | | 소절 | 줄 | 수식 |
|---|---:|---:|---|---|---:|---:|
| CoMapGS 3.3 | 29 | 2 | | LM-RS 4.1 | 67 | 1 |
| **Taming3DGS 3.2** ★ | **31** | 1 | | LM-RS 4.5 | 88 | 1 |
| Taming3DGS 3.4 | 38 | 0 | | chen2026cover 4.2 | 101 | 5 |
| LM-RS 4.3 | 55 | 1 | | Point-SLAM 3.1 | 106 | 3 |
| SparseGS 3.2 | 60 | 2 | | Taming3DGS 3.3 | 136 | 3 |

**중앙값 ≈ 63.** ★ 우리 §3.1 과 문제가 가장 가까운 Taming3DGS 3.2 는 **4문단 31줄**로 끝낸다.

방침: **중앙값보다 조금 위**에 두되 chen2026cover 4.2(101)·Point-SLAM 3.1(106) 아래로 유지한다.
우리는 그림 하나와 수식 3개를 더 갖고 있어 그만큼의 여유만 인정한다.
Taming3DGS 3.3(136)만큼 쓰는 건 그 논문의 헤드라인 기여일 때 정당화되는 분량이고,
우리 세 소절은 서로 대등해야 한다.

> 이 개편으로 §3 이 3.0 p → 2.0 p 로 줄면서 **본문이 처음으로 8쪽 안에 들어갔다**
> (References 가 p9 → p8). 측정은 `scripts/pagemap.sh`.

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
Preliminaries 는 **아예 두지 않는다.** 배경식 2개를 넣어봤지만 §3.1·§3.2 가 참조하는 곳이
한 군데도 없었고, 두 소절이 쓰는 기호는 전부 우리 것이라 각자 쓰이는 자리에서 정의된다.
3DGS 소개는 §2 가, mapping loss 는 §3.3 carve 가 필요할 때 그 자리에서 진다.

전체 지도는 [`../README.md`](../README.md), 서사는
[`../../plan/outline/CURRENT.md`](../../plan/outline/CURRENT.md).
