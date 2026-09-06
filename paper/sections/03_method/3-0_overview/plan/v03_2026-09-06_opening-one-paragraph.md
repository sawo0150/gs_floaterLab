# 3.0 Method 도입 — 무엇을 쓸 것인가 (v03, 2026-09-06)

> **번호 없는 도입.** roadmap 한 문단 + `Notation.` run-in. 0.25 p.
> v02 는 5문단 48줄이었다. 코퍼스 조사 결과 그건 관행에서 크게 벗어난다.

## v02 에서 바뀐 것과 그 근거

Method 도입의 실제 길이를 재봤다 (첫 소절 직전까지, 줄 수):

| 논문 | 줄 | 내용 |
|---|---:|---|
| Photo-SLAM | 4 | 개요 |
| Point-SLAM | 8 | roadmap |
| CaRtGS | 10 | roadmap |
| SparseGS | 10 | `Overview.` run-in |
| VIGS-SLAM | 11 | 개요 |
| SplatFace | 13 | 개요 |
| LM-RS | 32 | roadmap **한 문단** (소절 5개 열거) |
| EDGS | 33 | roadmap **한 문단** (소절 4개 열거) |
| MonoGS | 0 | 바로 `3.1` |

**5~7문장, 8~13줄, 한 문단이 관행이다.** 32~33줄짜리도 문단은 하나이고 소절이 많아 길어진 것이다.

그리고 §3 소절 구성을 11편에서 세어보니 **진단에 소절을 준 것은 CaRtGS 하나뿐**이었다.

| 논문 | 진단 소절 |
|---|---|
| Taming3DGS, LM-RS, chen2026cover, MonoGS, Point-SLAM, EDGS, SparseGS, CoMapGS | **없음** |
| CaRtGS (`A. Computational Misalignment`) | 있음 |

→ ⚠ **정정.** `notes/structure_survey/cartgs.md` 는 A↔C 대칭을 "§3 의 핵심 구조"라고 썼는데,
그건 CaRtGS 한 편의 특징이지 관행이 아니다. 한 편만 보고 일반화한 것이다.

→ **진단은 각 소절 첫 문단(P1)에 분산한다** (taming3dgs §3.2 형식).
→ **"세 결정으로 분해"라는 중심 주장은 §1 이 진다.** taming3dgs 도 contribution bullet 3개를
§1 에 두고 §3 도입에서 한 번 훑을 뿐이다.

## 문단 계약 (2블록)

### ① Roadmap — 한 문단, 6문장, 12줄

코퍼스에서 뽑은 자리 다섯 개를 채운다.

| 자리 | 하는 일 | 실물 |
|---|---|---|
| ① 범위 | 이 절이 무엇을 다루는가 | cartgs *"In this section, we delve into…"* / point-slam *"This section details how…"* / edgs *"Our goal is to…"* |
| ② 부품 열거 또는 기존과의 대비 | 몇 개짜리인가, 기존과 뭐가 다른가 | sparsegs *"consists of three key components: A, B, and C"* / edgs *"**Instead of** …, we …"* |
| ③ 순서어로 소절 훑기 | first / then / next / finally | 5편 전부 |
| ④ 소절마다 '얻는 것' 한 구절 | 그 소절이 무엇을 해결하는가 | lmrs *"**thereby providing** …"* / *"**which results in** …"* / *"**which eliminates** …"* |
| ⑤ 그림 지목 | 개요 그림 한 번 | point-slam *"An overview … Fig. 2."* / sparsegs *"Fig. 2 showcases …"* |

우리 6문장:

| # | 자리 | 내용 |
|---|---|---|
| 1 | ① 범위 | 온라인 mapper 가 **도착한 supervision 을 제한된 update 에 어떻게 배분하는가** |
| 2 | ② 대비 | 기존은 이를 keyframe 하나에 묶는다. *Instead*, 세 결정으로 분해한다 |
| 3 | ③④ §3.1 | 완료된 GPU service 가 증가 속도를 정한다, **그럼으로써** pool 크기·하드웨어와 무관해진다 |
| 4 | ③④ §3.2 | **그러나 이는 순서를 답하지 않으므로** count 균형 비복원 block 으로 순서를 정한다 |
| 5 | ③④ §3.3 | **순서가 정해져도 free-space 오류가 남으므로** causal carve evidence 로 억제한다 |
| 6 | ⑤ 그림 | Fig. 2 가 전체 흐름을 보여준다 |

★ **3·4·5 의 접속어가 다음 소절이 존재해야 하는 이유다** (lmrs §4 도입 형식).
없으면 "세 트릭을 붙였다"로, 있으면 "한 문제를 끝까지 따라간다"로 읽힌다.
원본은 [`plan/outline/CURRENT.md`](../../../../plan/outline/CURRENT.md) 의 화살표 다이어그램.

### ② `Notation.` — run-in, 8줄 + 배경식 2개

splatam §3 이 개요 문단 뒤에 run-in `Gaussian Map Representation.` 을 두는 형식.
vigsslam 은 이걸 쓰이는 소절 안에 두지만, 우리 배경식은 세 소절에서 다 쓰이므로 앞에 둔다.

- 3DGS 표현식 + VIGS-SLAM mapping loop 표기
- 배경식 (1)(2)
- **경계 문장으로 닫는다:** *"Equations (1)–(2) are standard 3DGS and VIGS-SLAM formulations,
  restated here for notation. All remaining equations are ours."*

⚠ 제목을 `Preliminaries.` 로 두지 않는다. 넣는 것이 표기와 배경식뿐이라 `Notation.` 이 정확하고,
무엇보다 **번호 없는 run-in 으로 Method 를 여는 논문은 전부 roadmap 이나 개요이지 표기가 아니다.**

## v02 에서 이 절이 잃은 것과 간 곳

| v02 문단 | 어디로 |
|---|---|
| P0 Preliminaries | → `Notation.` run-in 으로 축소 (이 절에 남음) |
| P1 Roadmap | → 위 한 문단 (이 절에 남음) |
| P2 Diagnosis 인용 | → **§3.1 P1 에 흡수.** baseline 문장 인용이 곧 그 소절의 진단이다 |
| P3 Diagnosis 분해 | → **§1 문단 4·5.** roadmap 문장 3·4·5 가 세 소절을 부르며 한 번 더 훑는다 |
| P4 Scope guard | → **§3.2 P5** (등식 조건·계보·실패) + **§6 Limitations** |

## Contribution 으로 주장하지 않을 것

- 이 분해가 유일하거나 최적이라는 것
- 이상화된 objective 의 최적해를 실제로 푼다는 것
  (근거: [`plan/claims/CURRENT.md`](../../../../plan/claims/CURRENT.md) §A1)

## 열린 질문

- Fig. 2 (system diagram) 를 1단으로 할지 2단으로 할지 — [`plan/figures/CURRENT.md`](../../../../plan/figures/CURRENT.md)
