# 3.0 Method 도입 — 무엇을 쓸 것인가 (v03, 2026-09-06)

> **번호 없는 도입. roadmap 한 문단, 그게 전부다.** 7문장 19줄, 0.17 p.
> Notation·배경식은 두지 않는다.
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

### ① Roadmap — 한 문단, 7문장, 19줄

코퍼스에서 뽑은 자리 다섯 개를 채운다.

| 자리 | 하는 일 | 실물 |
|---|---|---|
| ① 범위 | 이 절이 무엇을 다루는가 | cartgs *"In this section, we delve into…"* / point-slam *"This section details how…"* / edgs *"Our goal is to…"* |
| ② 부품 열거 또는 기존과의 대비 | 몇 개짜리인가, 기존과 뭐가 다른가 | sparsegs *"consists of three key components: A, B, and C"* / edgs *"**Instead of** …, we …"* |
| ③ 순서어로 소절 훑기 | first / then / next / finally | 5편 전부 |
| ④ 소절마다 '얻는 것' 한 구절 | 그 소절이 무엇을 해결하는가 | lmrs *"**thereby providing** …"* / *"**which results in** …"* / *"**which eliminates** …"* |
| ⑤ 그림 지목 | 개요 그림 한 번 | point-slam *"An overview … Fig. 2."* / sparsegs *"Fig. 2 showcases …"* |

우리 7문장. **문장 3 이 셋을 먼저 세어주고**, **4·5·6 은 전부 같은 꼴**이다 —
[깨지는 offline 가정] → [무엇을 하는가 §ref] → [무엇을 얻는가].

| # | 자리 | 내용 |
|---|---|---|
| 1 | ① 전제 | 온라인 매핑은 **아직 도착 중인** 데이터셋에 모델을 맞춘다 |
| 2 | ② 대비 | offline 3DGS 는 이 사실이 깨뜨리는 세 가정 위에 있고, 기존 온라인 시스템은 그 셋을 **keyframe 규칙 하나로 물려받는다** |
| 3 | ② 셋 세어주기 | **§ref 를 꺼내기 전에 독자의 말로 셋을 센다** — *how much* supervision may enter / *in which order* it is revisited / *what constrains* the geometry it does not yet determine. sparsegs *"consists of three key components: A, B, and C"* 자리 |
| 4 | ③④ §3.1 | **고정 집합 위의 고정 예산이 성립하지 않으므로** 완료된 GPU service 가 증가 속도를 정한다 → **which makes** 그 속도가 집합 크기·하드웨어와 무관해진다 |
| 5 | ③④ §3.2 | **셔플링은 유한 고정합 위에 정의되는데** 자라는 집합은 그렇지 않으므로 count 균형 비복원 block → **which** 무작위성을 버리지 않고 노출을 고르게 한다 |
| 6 | ③④ §3.3 | **기하는 가진 뷰로 결정되는데** free space 는 아직 미결정이고 **floater 가 그 미결정의 가시화**이므로 causal carve evidence → **which** 미래 프레임 없이 제거한다 |
| 7 | ⑤ 그림 | Fig. 2 가 **한 원인의 세 결과**가 한 pass 안에서 맞물리는 것을 보여준다 |

### 이 묶음의 근거

세 소절은 병렬 나열이 아니라 **"데이터셋이 아직 도착 중"이라는 한 사실의 세 결과**다.
전문과 대안 검토는 [`plan/outline/CURRENT.md`](../../../../plan/outline/CURRENT.md) 의 중심 문장.

⚠ **성립 조건:** carve 가 *관측 부족으로 생긴* floater 를 다룰 때만 성립한다.
관측이 충분해도 최적화가 만든 floater 라면 이 틀은 무너지고 "학습 루프의 세 손잡이"로 되돌아가야 한다.
**팀원 확인 전까지 §3.3 초안을 쓰지 않는다.**

★ **4·5·6 의 접속어가 다음 소절이 존재해야 하는 이유다** (lmrs §4 도입 형식).
없으면 "세 트릭을 붙였다"로, 있으면 "한 문제를 끝까지 따라간다"로 읽힌다.
원본은 [`plan/outline/CURRENT.md`](../../../../plan/outline/CURRENT.md) 의 화살표 다이어그램.

### ② Notation·배경식은 두지 않는다 (2026-09-06 결정)

한때 `Notation.` run-in + 3DGS 배경식 2개를 넣었다가 뺐다. 이유는 **안 쓰이기 때문**이다.

- 넣어본 배경식 (1)(2)를 **§3.1·§3.2 가 참조하는 곳이 한 군데도 없었다.**
  자기 자신을 소개하는 문장 하나가 유일한 참조였다
- 두 소절이 쓰는 기호 `S(t)` `κ` `γ` `A*` `B_t` `Q_t` `n_i` `Φ` `β` `τ` `ρ_H` 는
  **전부 우리 것**이고 각자 쓰이는 자리에서 정의된다. 3DGS 에서 물려받는 기호가 없다
- 따라서 *"여기부터가 우리 수식"* 이라는 경계 문장도 막을 혼동이 없어 불필요하다

코퍼스도 갈린다 — **배경 블록이 아예 없는 논문이 셋**이다 (Point-SLAM, SparseGS, CoMapGS).

| 배경 블록 | 논문 |
|---|---|
| **없음** | Point-SLAM, SparseGS, CoMapGS |
| 소절 번호 부여 | Taming3DGS 3.1, MonoGS 3.1, EDGS 3.1, chen2026cover §3, LM-RS §3 |
| 쓰이는 소절 안 run-in | VIGS-SLAM (`Preliminary.` in §3.3) |

→ **3DGS 소개는 §2 가 진다.**
→ **mapping loss 는 §3.3 carve 가 항을 더할 때 그 자리에서 꺼낸다.** vigsslam 이 `Preliminary.` 를
§3.3 안에 둔 것과 같은 이유다. carve 가 그 식을 쓰는 게 확정되기 전에 자리를 잡아두지 않는다
(P02 소절을 미리 잡지 않은 것과 같은 논리).

## v02 에서 이 절이 잃은 것과 간 곳

| v02 문단 | 어디로 |
|---|---|
| P0 Preliminaries | → **폐기.** 배경식이 어디서도 안 쓰였다 (위 ② 참조) |
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
