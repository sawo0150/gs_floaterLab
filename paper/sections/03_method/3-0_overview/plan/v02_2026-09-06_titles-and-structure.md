# 3.0 Problem Formulation — 무엇을 쓸 것인가 (v02, 2026-09-06)

> 한 줄 claim: **온라인 mapper의 결정을 cardinality → membership → ordering 세 단계로 분해한다**
> ⚠ claim boundary: 이상화된 trajectory-level objective이며 전역 최적해를 푸는 것이 아님.

## 이 절의 역할

세 contribution이 **왜 하나의 논문인가**를 성립시키는 절. 이게 없으면 C1/C2/C3가
서로 무관한 세 트릭으로 읽힌다.

## 반드시 넣을 내용

- [ ] **배경 셋업** — VIGS-SLAM tracking backend, `G_θ = {(μ,q,s,o,c)}`, keyframe mapping은
  대체하지 않고 그 위에 inter-keyframe RGB를 photometric supervision으로 추가
- [ ] **세 단계 분해 식**
  ```
  S(t) ↦ (B_t,Q_t)   →   (Q_t,C_t) ↦ A_t   →   (A_t,n_t) ↦ (W_t,p_t,H_t)
   cardinality            membership              ordering
  ```
- [ ] **이상화된 전체 문제** (설계 원리를 보이는 용도)
  ```
  min_π  Φ(n_T) + τ·D_KL(P_π ‖ P_shuffle)
  s.t.   κ[A(t) − A_0]_+ ≤ B_0 + γS(t),  ∀t
  ```
- [ ] **⚠ 과장하지 않을 범위** — 한 문단을 따로 할애한다
  - 구현이 전역 `P_π` 에 대한 KL을 직접 계산하지 않는다
  - admission hard constraint는 deterministic controller로 **정확히** 만족시키고,
    ordering objective는 한 step의 count-variance 증가량에 대한 entropy-regularized
    **surrogate**로 풀어 closed-form Gibbs를 얻는다
  - 이 문단이 리뷰어의 "전역 최적화라며?" 공격을 미리 막는다
- [ ] **causal contract 명시** — 미래 frame, 최종 trajectory 길이, held-out loss, 평가 영상
  미사용. 고정 calibration은 허용.
- [ ] **기호표** (본문 표 1개) — 이후 모든 절이 이 표를 참조

## Contribution으로 **주장하지 않을** 것

- 이 분해가 유일하거나 최적이라는 것
- 이상화된 objective의 최적해를 실제로 푼다는 것
  (근거: [`../../../../plan/claims/CURRENT.md`](../../../../plan/claims/CURRENT.md) §A1)

## 다음 절로의 연결

> "세 결정 중 첫째는 자원 제약이다: 지금까지 실제로 확보한 GPU service로 몇 장을
> 감당할 수 있는가?" → §3.1

## 문단 계약 (5문단)

각 행이 문단 하나. move 이름과 출처 논문은 `notes/structure_survey/_framework_moves.md`.

| # | move | 내용 | 출처 |
|---|---|---|---|
| 0 | **`Preliminaries.` run-in 볼드** | 3DGS 표현식 + VIGS-SLAM mapping loop 표기. 마지막에 경계 문장: *"Equations (1)–(2) are standard 3DGS and VIGS-SLAM formulations, restated here for notation. All remaining equations are ours."* | vigsslam §3.3 / chen2026cover §3.2 |
| 1 | **Roadmap (사슬형)** | *"먼저 §3.1에서 학습 뷰를 얼마나 늘릴지를 다룬다. 그러나 이는 늘어난 뷰를 어떤 순서로 볼지 답하지 않으므로 §3.2에서 … 순서가 정해져도 free-space 오류가 남으므로 §3.3에서 …"* — `plan/outline/`의 화살표를 산문으로 | lmrs §4 도입 |
| 2 | **Diagnosis (인용형)** | VIGS-SLAM 원문 인용 — *"For each new keyframe, we run 10 mapping iterations. In each iteration, we randomly sample keyframes from the frontend tracking frame graph."* → **이 한 문장에 세 결정이 뭉쳐 있다** | vigsslam §3.3 |
| 3 | **Diagnosis (분해)** | 세 문제에 이름을 준다. **§3.1/3.2/3.3과 같은 이름·같은 순서.** 각각 "왜 지금 방식이 답이 아닌지" 한 문장씩 + 기호표 | cartgs III.A |
| 4 | **Scope guard** | 이상화된 objective를 전역으로 푸는 게 아님 + causal contract 한 문장(상세는 §4.1) | claims §A1 |

## 세 문제의 이름 (§3.1/3.2/3.3과 반드시 일치)

| # | §3.0에서 부르는 이름 | 대응 소절 |
|---|---|---|
| 1 | 학습 뷰를 **얼마나** 늘릴 것인가 | §3.1 **Compute-Paced View Growth** |
| 2 | 늘어난 뷰를 **어떤 순서로** 볼 것인가 | §3.2 **Entropy-Regularized Count Balancing (ERCB)** |
| 3 | 순서가 정해져도 남는 **free-space 오류** | §3.3 **Causal Free-Space Carving** (팀원 확정 대기) |

## v01에서 종결된 질문

- ~~membership을 헤드라인에서 뺀 지금, 3단 분해를 그대로 쓸 것인가?~~
  → **종결.** membership은 기여로 세지 않고 **§3.1의 run-in 볼드 한 문단**이 된다
  (사수님 판단: 기여라기엔 약하고 절 하나를 주기도 아님).
  세 문제 = 세 기여 = 세 소절로 **완전 대칭**이 된다.
  보관: `../../3-1_compute_paced_view_growth/absorbed/`
- ~~Preliminaries를 독립 절로 뺄 것인가?~~
  → **종결. 빼지 않는다.** vision 25편 중 독립 절은 4편뿐이고 GS-SLAM은 예외 없이 안 뺀다.
  근거: `../../../../notes/naming/CURRENT.md`

## 남은 열린 질문

