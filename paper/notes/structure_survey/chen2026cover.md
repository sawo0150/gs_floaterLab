# chen2026cover (CONVERGE) — 구조 해부 (§3, §4, §5)

## 기본 정보

| | |
|---|---|
| 논문 | CONVERGE: coverage 기반 next-best-view metric (Fisher Information Gain 유도) |
| venue | **CVPR proceedings 조판 실물** (쪽번호 19444–19452) — 우리와 같은 규약 |
| 전체 | 9쪽 (본문 ~8쪽) |
| 절 구성 | 1 Intro / 2 Related / **3 Preliminaries** / **4 Method** / 5 Results / **6 Limitations** / 7 Conclusion |
| §4 Method | 약 3쪽, 수식 25개, 그림 1개 |
| §5 Results | 약 1.5쪽, 표 2개 + 그림 2개 |
| 왜 보나 | **유도(derivation)로 굴러가는 §3**. CaRtGS에 없던 것. 우리 §3.3(Lagrangian→Gibbs)의 직접 모델 |

---

## ★ 발견 1 — Preliminaries를 Method에서 **분리해 독립 절**로 뺐다

CaRtGS는 배경 수식을 `III.B System Overview` 안에 넣었지만, CONVERGE는 아예 **§3을 따로 만들었다.**

```
3. Preliminaries
   3.1 Radiance Fields      ← Eq (1)(2): 렌더링 방정식. 전부 남의 것
   3.2 Gaussian Splatting   ← 표기 G = {(µ,Σ,c,σ)}. 전부 남의 것
4. Method
   4.1 ~ 4.4                ← Eq (3)–(25): 전부 이 논문의 것
```

효과: **"§4에 있는 수식은 전부 우리 것"**이 절 번호만으로 보장된다.
§3.2 첫 문장이 그 계약을 명시한다 — *"While our proceeding analysis is general to any radiance field
representation, we introduce a popular state-of-the-art representation that we use in our implementation."*
= 이 절은 일반성 확보용 배경이고 기여가 아니라는 선언.

→ **우리도 §3.0을 "Preliminaries + 문제 분해"로 두면 3DGS·VIGS-SLAM 배경 수식과
token law·Gibbs 유도가 절 번호로 갈린다.**

## ★ 발견 2 — §4 도입 Roadmap이 **유도 단계를 번호로 나열**한다

> *"Our derivation of an interpretable and tractable information gain metric proceeds in three steps:
> (1) expressing Fisher Information Gain as a quadratic form over transmittance patterns;
> (2) extending this metric to a view-direction-aware formulation;
> (3) relaxing this form to a coverage-based surrogate."*

한 문장에 소절 개수·순서·각 단계가 하는 일이 다 들어있다. 독자는 3쪽짜리 유도에 들어가기 전에
**지도를 받는다.** CaRtGS의 Roadmap은 "분석하고 제안한다" 수준이었는데 이쪽이 훨씬 강하다.

## ★ 발견 3 — §4 골격은 "**정확하지만 계산 불가 → 완화 → 실용형**"

| 소절 | 하는 일 | 상태 |
|---|---|---|
| 4.1 Formulating a Gain Metric | FIG를 정의하고 `log(1+wᵀG⁻¹w)`로 닫힌 형태 유도 | **정확하나 W 저장 불가** |
| 4.2 Tractable Metric | primitive당 스칼라 하나만 저장하는 proxy로 치환 | 완화 1 |
| 4.3 Extension to View Directions | 시점 의존 색 모델로 일반화 | 확장 |
| 4.4 Transmittance-Agnostic Metric | transmittance를 버리고 coverage만 남김 | 완화 2 → 최종형 |

CaRtGS가 **문제 N개 ↔ 해법 N개 대칭**이었다면, 여기는 **단일 대상을 단계적으로 깎아 나가는** 모양이다.
§3의 shape이 하나가 아니라는 뜻이다.

## ★ 발견 4 — 유도 중간에 **두 번째 Diagnosis**를 넣어 다음 소절을 정당화한다

§4.3 끝:

> *"Although simple, in practice, we find several reasons for concern for using Equations (10),(11),(16),(17)
> as a view metric. **First**, computing the transmittance terms for every pixel-primitive pair is
> computationally expensive and memory-hungry. **Second**, these transmittance values are typically noisy
> and can change rapidly during training... **In addition**, the 3DGS is a proxy of the ground-truth geometry.
> Therefore, intertwining the view metric too deeply with the 3DGS parameters leads to suboptimal
> reconstruction... We find that abstracting away transmittance effects leads to more reliable behavior,
> **as shown in Table 9.**"*

- 자기가 방금 유도한 식 4개를 번호로 지목해 문제 삼는다
- 이유 3개를 First/Second/In addition으로 센다
- **Forward pointer**로 실험 표를 가리켜 "이건 취향이 아니라 측정된 것"임을 밝힌다
- 그리고 §4.4가 그 문제를 푼다

즉 **Diagnosis는 §3 맨 앞에만 오는 게 아니다.** 소절 전이마다 올 수 있다.

## ★ 발견 5 — **가정 원장(assumption ledger)**: 근사마다 조건을 명시한다

§4.4는 근사 5개를 연달아 쓰는데, **하나도 그냥 넘어가지 않는다.**

| 근사 | 붙인 조건 |
|---|---|
| `Σ_c(αᶜ)² ≈ max_c(αᶜ)²` | *"which holds true if there is a dominant αᶜ across cameras"* |
| `\|visᶜ\|`를 상수 취급 | *"We make the simplifying assumption that ... is constant across cameras"* |
| β를 spherical Gaussian kernel로 고정 | *"a design decision and can be selected as an arbitrary value ... though the derivation can be broadly extended to decaying spherical kernels"* |
| κ가 크다고 가정 | *"If κ is large, then the color seen from direction d corresponds to ... (a natural choice)"* |
| exp를 1차 Taylor로 | *"can be approximated by its first-order Taylor expansion"* |

→ **우리 §3.3과 §3.1이 그대로 이 형식을 따라야 한다.**
`Φ(n)=½Σ(n_i−n̄)²` → `Δ_iΦ` → Lagrangian → `p ∝ exp(−βn_i)`로 가는 길에
"1회 교체의 1차 근사", "K-view 비복원에서 snapshot `n_i^(b)`을 고정", "β=1/τ 재매개화" 같은
가정이 여럿 들어있는데, 지금 우리 문서엔 **가정이 흩어져 있고 조건이 안 붙어 있다.**

## ★ 발견 6 — **등식 → 부등식 감사**: 무엇이 손실됐는지 문장으로 못박는다

§4.1 후반:

> *"However, note that with additional constraints, Eq. (7) is no longer equality. Rather, we have the tight
> bound by Cauchy-Schwarz `wᵀG⁻¹w ≥ 1/(wᵀGw)`, with equality when w is an eigenvector of G.
> **Regardless, minimizing Eq. (8) subject to additional constraints on w still applies upward pressure to the FIG.**"*

- 등식이 깨지는 **정확한 지점**을 지목
- 대신 성립하는 것(tight bound)과 등식 회복 조건(고유벡터)을 명시
- 그러고도 무엇을 여전히 주장할 수 있는지("upward pressure")를 약하게 말한다

→ **우리 claims의 금지 문장 "exact EIG 계산 주장 금지"에 대한 정확한 해답이 이 문장이다.**
금지는 "말하지 마라"가 아니라 **"이렇게 말해라"**로 바뀔 수 있다.
ERCB도 같다: β=0이 full-pool random reshuffling과 같아지는 것은 **K ≥ N_t일 때뿐**인데,
지금은 그 조건이 문서에만 있고 서술 문장이 없다.

---

## §5 Results 골격

```
5. Results        (도입 문단: 무엇과 비교하는가 = Setup 통째로 여기에)
  5.1 Fixed Dataset Photometric Comparisons
  5.2 Ablations
  5.3 Compute Time                ← 계산량을 독립 소절로
6. Limitations                    ← 독립 절
7. Conclusion
```

Setup을 별도 소절로 안 빼고 **§5 도입 문단 하나에 몰아넣었다.** (CVPR 8쪽 압박 때문으로 보인다.)
그 한 문단에 들어간 것: baselines 3개 + random + oracle / 데이터셋 3종 15장면 /
초기 10 view / 200 step마다 1 view / 30K step 종료 / Nerfstudio 구현 / 반복 실행 여부.

→ **우리 §4.1 Setup도 소절 남발하지 말고 한 문단 + run-in 볼드로 압축 가능.**

## ★ 발견 7 — **"random이 강하다"를 먼저 인정하고 시작한다**

§5.1 첫 문장이 이것이다:

> *"We observe that a random baseline is performant for view selection on a fixed dataset.
> Visually, random is generally similar in reconstruction quality to CONVERGE (Fig. 2)."*

그리고 **이유를 댄다** — *"Human-captured datasets are naturally well-distributed... Therefore random
inherits this dataset bias and achieves good coverage."*
그 다음 gap이 벌어지는 **레짐을 찾아간다**: Embodied + Sparse에서 1.5 PSNR 차.

| Setting | Random | Fisher-RF | CONVERGE |
|---|---|---|---|
| Embodied | 22.48 | 22.27 | **23.21** |
| Sparse | 22.81 | 21.74 | 22.80 ← **동률. 그대로 싣는다** |
| Embodied + Sparse | 20.89 | 21.24 | **22.39** |

Sparse에서 random과 **똑같은 숫자(22.80 vs 22.81)를 숨기지 않고 표에 넣었다.**
그리고 §6에서 다시 인정한다 — *"our method is only as good as the random baseline in very sparse
initialization regimes."*

→ ★ **이것이 우리 C2(ERCB)의 서술 템플릿이다.**
우리도 β=0 ≡ random인 구간이 있고, exp72에서 1253은 −0.084 dB(오히려 손해), rot은 +0.362 dB다.
지금 계획은 이 비대칭을 설명할 자리가 없는데, CONVERGE 방식대로 하면 **약점이 아니라 레짐 분석이 된다.**

## ★ 발견 8 — **Table 2가 method×baseline이 아니라 setting×method**

Table 1은 dataset × method(전통형), Table 2는 **setting × method**이고 맨 위에
`All / Splatfacto 24.83` = 전 view를 다 본 infeasible oracle 행이 있다.
"우리가 남보다 낫다"가 아니라 **"제약을 걸면 어디서 갈리는가 + 상한은 어디인가"**를 보여준다.

## §6 Limitations — 유도의 가정 원장을 그대로 감사한다

> *"CONVERGE is derived from **a set of approximations that trade off fidelity for scalability.**
> In particular, the metric relies on a coverage-based surrogate that **lower-bounds** the Fisher
> Information Gain while **discarding explicit transmittance effects.** ... this approximation may be less
> reliable in scenes with extreme clutter where transmittance carries additional information,
> **though we have not observed this behavior in commonly used datasets.**"*

§4에서 붙인 가정 → §6에서 "이 가정이 깨지면 어디가 무너지는지" 회수. **§4와 §6이 짝**이다.
마지막 절("아직 관측하진 못했다")까지 정직하다.

---

## ★ 훔칠 것

1. **Preliminaries를 독립 절/소절로 분리** → 기여 수식의 경계를 절 번호로 보장
2. **Roadmap에서 유도 단계를 (1)(2)(3)으로 열거** → §3.3 도입 문단에 그대로
3. **가정 원장** — 근사마다 성립 조건 한 구절씩. §3.1 token law, §3.3 Gibbs 유도 양쪽
4. **등식→부등식 감사 문장** — 금지 문장을 "허용 문장"으로 바꾸는 형식
5. **소절 전이의 두 번째 Diagnosis** — "First/Second/In addition" + Forward pointer
6. **random이 강하다는 것을 먼저 인정 → 이유 → 레짐 탐색** (C2 서술의 뼈대)
7. **setting × method 표 + oracle 상한 행**
8. **§4 가정 ↔ §6 Limitations 짝 맞추기**
9. **Compute Time을 독립 소절로** — *"In fixed time budget settings (e.g. on a real-time robot system),
   CONVERGE is appealing as it can process many more images than other methods"* ← 우리 1.5× budget 논리와 동일

## ✗ 우리와 다른 점

- **online/streaming이 아니다.** fixed candidate pool에서 teleport로 고르며, 도착 순서 제약이 없다.
  우리의 arrived-only·causal 제약은 여기 없다 → 그래서 우리가 낼 자리가 있다.
- **계산 예산 계약이 없다.** 30K step 고정일 뿐 wall-time 예산이 없다. §5.3에서 초/뷰만 보고.
- **실패한 설계를 안 싣는다.** 성능이 동률인 것은 싣지만, 시도했다 버린 대안은 없다 → LMRS 부록이 그 예.

## 없는 move

| 이 논문에 없는 것 | 우리에게 필요한가 |
|---|---|
| 인과/스트리밍 계약 정의 | **필요** — vigsslam이 예를 준다 |
| 계산 예산 고정 하의 비교 | **필요** — taming3dgs가 예를 준다 |
| 시도했다 버린 대안 기록 | **필요** — exp72 lifetime 실패, exp59 전이 실패. lmrs 부록이 예 |
| 하이퍼파라미터 민감도 곡선 | **필요** — κ 스윕, exp73 κ=16 이상치 |
