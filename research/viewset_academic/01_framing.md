# View-set 구성의 학술적 프레이밍

> 대상: `vigs_slam_final_system_explainer.html` §05–06 (view set / training order)
> 코드: `VIGS-SLAM-main-integration-20260828`
> - `vigs/map_scheduler.py` — `pose_balanced_frontier_subset`(L1096), `ActiveArchiveReplayQueue`(L1259),
>   `CausalShuffleQueue`(L597), `admit_mature_service`(L472), `admit_bounded`(L355)
> - `vigs/gs_backend.py` — `_mapping_active_archive_partition`(L3500), work-credit minting(L7403)

---

## 0. 한 문장

> **지금 문서는 "우리가 이렇게 했더니 잘 됐다"로 쓰여 있는데, 실제 구조는
> "streaming view-set 구성을 admission / design / ordering 세 결정으로 분리하고,
> 각각이 서로 다른 목적함수에 지배됨을 보인다"는 논문 명제 하나로 묶인다.**
> 이 분리 자체가 contribution이고, 세 다리 각각에 붙일 문헌이 이미 존재한다.

문서 §1.3이 이미 `compute allocation ≠ view-set membership ≠ optimizer order`라고
써 놨다. **이걸 부제가 아니라 논문의 thesis로 올리는 게 이 작업의 핵심이다.**

---

## 1. 가장 큰 문제: 리뷰어는 이걸 active learning으로 읽는다

"novelty로 view를 고른다"는 서술을 보면 리뷰어는 자동으로 **active learning /
acquisition function** 프레임으로 읽고, "왜 BALD/BADGE와 비교 안 했나"를 묻는다.
그런데 이 시스템의 Stage C 결과(novelty-first가 shuffle보다 AUC MSE +10.64%)는
**그 프레임이 틀렸다는 실험적 증거**다.

정확한 진술은 이것이다:

| 결정 | 무엇을 고르나 | 지배 목적 | 맞는 문헌 |
|---|---|---|---|
| **Admission** | 몇 장 받을까 | 처리량/안정성 | queueing, 자기-클럭 흐름제어 |
| **Design (membership)** | 어떤 걸 남길까 | risk 근사 오차 | quadrature / coreset / OED |
| **Ordering** | 어떤 순서로 | 수렴률 | random reshuffling (RR) |

**Design 단계에서 novelty는 유효하고(−0.35%), Ordering 단계에서는 해롭다(+10.64%).**
같은 신호가 한 단계에서는 도움이 되고 다른 단계에서는 해가 된다는 것 —
이게 이 논문에서 가장 인용하기 좋은 문장이 될 수 있다.

---

## 2. Admission = 자기-클럭 admission control (지금 가장 저평가된 부분)

### 코드가 실제로 하는 것

`map_scheduler.py:472 admit_mature_service`:

```
mature_service_steps  ← 이번에 완료된 dense Adam update 수
   단, replay_pool_mature_before == True 일 때만 적립      (gs_backend.py:7403)
credit += Δmature_service_steps
quota   = credit // required_opportunities        (r = 2)
credit -= admitted · r
pending 비면 credit = 0                            (과거 compute가 미래를 선불 못 함)
```

그리고 admission은 interval별 water-filling(`min`으로 가장 적게 받은 interval부터).

### 이건 token bucket이다

`credit += service; quota = ⌊credit/r⌋`는 정확히 **credit-based flow control /
token bucket regulator**이고, "완료된 서비스가 다음 입력을 허가한다"는 구조는
TCP의 **ACK self-clocking**과 같은 원리다. 문서는 이걸 "화폐처럼 쓴다"고 비유로만
설명하는데, 이름을 붙이면 바로 정리(定理)를 쓸 수 있다.

### 논문에 넣을 수 있는 명제 (코드에서 바로 증명됨)

> **Proposition (exposure invariant).** `admit_mature_service` 하에서, 새 view가
> 허가되기 위해 소비되는 credit은 오직 *"그 update 시점에 이미 pool 안의 모든
> dense view가 `r`회 이상 서비스받은 상태"*에서 발생한 update로만 적립된다.
> 따라서 임의의 시점 t에서 pool의 크기 |S_t|는
> `|S_t| ≤ |bootstrap_t| + (1/r)·#{mature service steps}`로 상한되며,
> pool은 optimizer가 실제로 소화한 것보다 빠르게 자랄 수 없다.

이건 "GPU에 맞춰 적응한다"는 정성적 주장보다 훨씬 강하다. **하드웨어·장면·fps에
무관한 불변식**이고, 실제로 5070 Ti / 5090에서 replay 수가 4,504 vs 12,175으로
자동으로 벌어진 것(§11.1)이 이 불변식의 실측 증거다.

### 이 프레이밍이 주는 추가 이득

- **"우리는 hyperparameter를 안 늘렸다"를 정량화할 수 있다.** 고정 FPS(K)를 쓰면
  장면×GPU마다 튜닝해야 하지만, work-credit은 `r` 하나(=2)뿐이고 그마저도
  "각 view가 받아야 할 최소 노출 횟수"라는 의미가 있다.
- 대신 **`r`에 대한 sensitivity 실험이 반드시 필요하다** (§6 참조). 지금은 r=2가
  근거 없이 고정돼 있어서 리뷰어가 바로 짚는다.

---

## 3. Design = SE(3) 위의 quadrature / streaming k-center

### 코드가 실제로 하는 것

`map_scheduler.py:1096 pose_balanced_frontier_subset`:

```
d(i,j) = hypot( ‖t_i−t_j‖ / median Δt_KF ,  d_SO(3)(R_i,R_j) / median ΔR_KF )
minimum_selected_distance ← nearest-archive distance 로 초기화
반복: argmax_i minimum_selected_distance[i] 선택, 갱신
target_count = min(|frontier|, |frontier intervals|)     # ≈ interval당 1장
```

### 세 가지를 정확한 이름으로 부를 수 있다

**(a) 문서 §1.2의 "curve에 점 찍기"는 quadrature다.**
`R(θ)=E_{v∼p}[ℓ(θ;v)]`를 유한 `S`로 근사하는 오차는, `ℓ(θ;·)`가 pose metric에서
Lipschitz라면 **fill distance(= covering radius) `h_S = sup_v min_{s∈S} d(v,s)`**로
상한된다. 즉

> `|R(θ) − R_S(θ)| ≤ L · h_S + (표본 분산 항)`

이건 scattered-data approximation / QMC의 표준 결과이고, **"왜 coverage를 최대화하는가"에
대한 정량적 답**이 된다. 지금 문서는 이걸 그림으로만 설명한다.

**(b) greedy farthest-point = Gonzalez k-center, 2-근사 보장이 있다.**
`argmax_i min_j d(i, selected_j)`는 Gonzalez(1985)의 greedy k-center이고, 얻어진
covering radius는 최적의 2배 이내다. 즉 **fill distance에 대한 근사보장이 공짜로 따라온다** →
(a)의 오차 상한이 실제로 통제된다고 말할 수 있다.

**(c) 그런데 이 구현은 평범한 k-center가 아니라 "archive를 이미 선택된 center로 둔
streaming k-center"다.** `minimum_selected_distance`를 `nearest_archive_values`로
초기화하기 때문에, 첫 선택부터 **archive가 이미 덮은 영역은 피한다.** 이게 코드가
문서보다 나은 지점이다 — 문서는 active/archive를 "frontier 대표 뽑기"로만 설명하지만,
실제로는 **union(active ∪ archive) 위의 covering radius를 줄이는 incremental k-center**다.
논문에서는 이렇게 써야 한다:

> frontier에서 뽑는 대표는 archive가 이미 제공한 covering을 조건부로 하여 선택되므로,
> 선택 기준은 "새 view가 얼마나 novel한가"가 아니라 **"전체 view-set의 fill distance를
> 얼마나 줄이는가"**이다.

**(d) metric의 정규화가 셀링포인트다.**
`median Δt_KF`, `median ΔR_KF`로 나누는 것은 **경험적 motion 통계로 whitening한
scale-free SE(3) metric**이다. 덕분에 장면 크기·속도·fps에 대한 임계값이 코드에
등장하지 않는다(docstring도 그렇게 주장한다). exp59에서 절대 상수의 교차 장면 전이가
깨졌던 이력이 있으므로, **"이 논문의 view 선택에는 장면 종속 상수가 없다"는 주장은
강하게 밀 가치가 있다.** 단, median이 정지 구간에서 0에 가까워질 때의 거동은
`robust_positive_scale`의 fallback으로만 처리되니 논문에서 한 줄 언급 필요.

**(e) temporal quota는 stratification이다.**
`target_count ≈ interval 수`(interval당 1장) + interval별 water-filling은
**시간 축으로 stratify한 뒤 stratum 안에서 coverage 최적화**하는 것이다.
Stage B의 세 조건이 정확히 이 구조를 검증한다:

| 조건 | 통계학적 이름 | 결과 |
|---|---|---|
| temporal uniform | systematic sampling | 기준 |
| representative | **stratified + within-stratum coverage** | −0.35% |
| global coverage | stratification 제거, coverage만 | **+3.88%** |

→ 논문 문장: **"stratification이 coverage보다 우선한다. coverage는 stratum 내부에서만
유효한 개선이다."** 이건 survey sampling의 상식과 일치해서 리뷰어가 납득하기 쉽다.

---

## 4. Ordering = random reshuffling (여기가 가장 문헌이 탄탄하다)

### 코드가 실제로 하는 것

`CausalShuffleQueue`(L597): "Shuffle-without-replacement over a candidate set that
grows online" — epoch마다 각 view 정확히 1회.

### 붙일 이론

문서 §6.3의 분산 식

```
Var(ĝ_B) ∝ (1/B)(1 − (B−1)/(N−1))
```

은 **유한모집단 보정(finite population correction, FPC)**이고 survey sampling(Cochran)의
표준 결과다. 그런데 진짜 강한 근거는 그 다음에 있다:

> **Random reshuffling(RR)이 with-replacement SGD보다 빠르다는 것은 정리로 증명돼 있다.**
> Gürbüzbalaban–Ozdaglar–Parrilo, *Why random reshuffling beats SGD* (Math. Prog. 2021);
> HaoChen–Sra (ICML 2019); Mishchenko–Khaled–Richtárik (NeurIPS 2020).
> smooth + strongly convex에서 RR은 `O(1/K²)`, SGD는 `O(1/K)`.

**문서의 실측(shuffle vs with-replacement = +1.68%)은 이 이론이 예측하는 방향과
크기 모두에 부합한다.** 지금은 이걸 "우리 실험 결과"로만 제시하는데, RR 문헌을
인용하면 **작은 효과 크기(1.68%)가 오히려 이론과의 정합성 증거**가 된다.
(작은 차이를 방어해야 하는 상황이 근거로 바뀐다 — 이득이 크다.)

### novelty-first가 왜 나쁜가 — 이게 논문의 진짜 이론 파트

문서 §6.2가 2차 Taylor로 설명하는데, 표준 용어로 바꾸면 훨씬 강해진다:

1. **greedy top-k 선택은 population gradient의 편향 추정량이다.** importance
   sampling으로 SGD를 가속하려면 **반드시 unbiased reweighting**이 필요하다
   (Needell–Ward–Srebro NeurIPS 2014; Zhao–Zhang ICML 2015;
   Katharopoulos–Fleuret *Not All Samples Are Created Equal* ICML 2018).
   novelty-first는 재가중 없이 결정론적으로 상위를 반복하므로 편향이 사라지지 않는다.
2. **coverage/Fisher는 잘못된 대리변수다.** 올바른 기준은 population gradient와의
   정렬(`g_R^T g_v`)이며, 이건 **gradient-matching coreset**의 목적함수 그 자체다
   (CRAIG, Mirzasoleiman et al. ICML 2020; GradMatch, Killamsetty et al. ICML 2021).
3. 그런데 **gradient-matching은 학습만큼 비싸다** — 문서 §6.3이 정확히 이 지적을 한다.
   따라서 shuffle은 "포기"가 아니라 **계산 가능한 unbiased 대안**이다.

**이 3단 논법이 이 논문의 가장 깔끔한 이론 서사다:**

> 올바른 선택 기준(gradient alignment)은 측정 가능하지만 감당 불가능하고,
> 감당 가능한 기준(coverage/Fisher)은 올바른 기준과 무상관이며(ρ≈0.005),
> 따라서 unbiased random reshuffling이 계산 예산 안에서의 최적 정책이다.

§6.2의 192개 one-step counterfactual(coverage ρ=0.005 vs Adam-alignment ρ=0.994)은
**이 논법의 직접 실험 증거**이고, 매우 좋은 실험이다. 논문에서 그림 하나를 여기에
써야 한다.

---

## 5. Active/Archive = bounded importance ratio를 가진 stratified sampler

### 코드가 실제로 하는 것

`ActiveArchiveReplayQueue`(L1259) docstring + `pose_balanced_frontier_subset` 끝부분:

```
D_A   = [p/(1+p)] · (1 + mean Fisher novelty),  p = median(d_active→archive)
odds_A = (|A|/|H|) · (1 + D_A)
P(A)   = odds_A / (1 + odds_A)
```

`p/(1+p) ∈ [0,1)`, `fisher ∈ [0,1]` → `D_A ∈ [0,2)` → 배수 `1+D_A ∈ [1,3)`.

### 두 개의 명제를 그대로 쓸 수 있다 (코드에서 검증됨)

> **Proposition 1 (no-harm / consistency).** `D_A = 0`이면
> `P(A) = |A|/(|A|+|H|)`로, full-pool uniform sampling의 주변분포와 정확히 일치한다.

> **Proposition 2 (bounded importance ratio).** 임의의 demand에서 active view가
> 뽑힐 확률은 uniform 대비 최대 3배이다. 따라서 제안분포는 uniform에 대해 절대연속이며
> Radon–Nikodym 도함수가 `[·, 3]`로 유계다 → gradient 추정량의 편향·분산이 유계다.

**Proposition 2가 이 설계의 안전성 논거 전체를 대신한다.** 문서는 "최신 interval이
optimizer를 독점하지 못한다"고 서술로 말하는데, **유계 importance ratio**라고 쓰면
한 줄로 정당화된다. 리뷰어가 "왜 recency bias가 안 생기냐"고 물을 때의 답이기도 하다.

### 그리고 이 축은 continual learning 문헌에 그대로 걸린다

- unbounded archive = **experience replay buffer**, FIFO 삭제 = 문서가 기각한 sliding window.
- active/archive 분리 = **stability–plasticity tradeoff**.
- 메모리 상한이 필요해지면 표준 해법은 **reservoir sampling**(Vitter 1985)이고,
  코드에 이미 `--mapping_bounded_replay_archive` 플래그가 있다 → *"메모리 유계 변형은
  reservoir로 자연 확장된다"*를 future work가 아니라 **설계된 확장점**으로 쓸 수 있다.

### ⚠ 정직하게 남겨야 할 이론적 틈

RR의 수렴 보장은 **하나의 pool을 permute**할 때의 결과다. 이 구현은 pool을
Bernoulli로 고른 뒤 **각 pool 안에서** without-replacement를 한다. 따라서
`D_A > 0`이면 합집합 위의 순서는 순수 RR이 아니라 **stratified RR**이고,
위 RR 정리들이 그대로 적용되지는 않는다. 논문에서는:

- `D_A=0`에서 uniform을 복원한다는 Proposition 1을 **연속성 논거**로 쓰고,
- stratified RR로 명시한 뒤, 엄밀한 수렴률은 **미해결로 남긴다**고 쓰는 게 안전하다.

이걸 숨기면 이론에 밝은 리뷰어에게 잡힌다. 명시하면 오히려 "한계를 아는 논문"이 된다.

---

## 6. E_K(B) 곡선 = compute-optimal view density (§5.1을 승격시키기)

문서 §5.1의

```
E_K(B) = E_∞,K + A_K · exp[−(B/τ_K)^{β_K}]
```

는 **stretched-exponential learning curve**이고, "budget B가 주어질 때 최적 K"를 묻는 것은
**compute-optimal scaling** 문제다(Chinchilla류 프레이밍이 그대로 통한다).

- 작은 K: `τ_K` 작음(빨리 수렴) but `E_∞,K` 큼(하한 높음)
- 큰 K: `τ_K` 큼 but `E_∞,K` 작음 (D02→D12에서 `E_∞ ×0.56`)
- ⇒ **budget마다 최적 K가 다르다** → 고정 FPS는 원리적으로 틀렸다.

**이게 work-credit admission의 존재 이유에 대한 이론적 정당화다.** 지금 문서는
§5.1(왜 고정 K가 아닌가)과 §5.2(work credit)를 나란히 두기만 하는데,
**"K*(B)가 B에 의존하고 streaming에서는 B를 미리 모르므로, 관측 가능한 완료 서비스를
B의 대리변수로 쓴다"**로 논리적으로 연결하면 §5 전체가 하나의 논증이 된다.

---

## 7. 논문 구조 제안

```
3. Streaming view-set construction
   3.1 Problem: risk over the trajectory manifold, causal constraint
   3.2 Three decisions and why they must be separated   ← thesis
   3.3 Admission: self-clocked credit control  (+ exposure invariant proposition)
   3.4 Design: stratified streaming k-center on a whitened SE(3) metric
              (+ fill-distance → risk bound, Gonzalez 2-approx)
   3.5 Ordering: random reshuffling
              (+ why gradient-alignment is right but unaffordable;
                 coverage is affordable but uncorrelated, ρ=0.005)
   3.6 Active/archive mixture (+ Prop 1 no-harm, Prop 2 bounded ratio)

4. Experiments
   4.1 Ablation by decision (이미 있음 — Stage B / C / K-sweep)
   4.2 Cross-hardware invariance (5070 Ti vs 5090; admission이 자동 적응)
   ...
```

**핵심 재배치 하나:** 지금 §5.3의 Stage B 표(membership)와 §6.1의 Stage C 표(order)는
문서에서 멀리 떨어져 있는데, **논문에서는 반드시 나란히 놓아야 한다.** 같은 신호
(novelty/coverage)가 membership에서는 −0.35%, ordering에서는 +10.64%라는 대비가
이 논문의 시그니처 결과이기 때문이다.

---

## 8. 리뷰어가 먼저 찌를 곳 (지금 상태 기준)

| # | 취약점 | 대응 |
|---|---|---|
| R1 | **Stage B의 −0.35%는 노이즈일 가능성** (3 seed, 단일 장면) | seed 수 늘리거나 **"membership에서 novelty는 중립"으로 약하게 주장**. 어차피 논문 주장은 "ordering에서 해롭다"이므로 손해 없음 |
| R2 | `r=2` (required_opportunities)가 근거 없음 | r∈{1,2,4} sweep. admission의 유일한 상수라 **반드시 필요** |
| R3 | demand 식의 `p/(1+p)`, `1+fisher` 함수 형태가 임의적 | Prop 2(유계 3배)만 주장하고 **정확한 형태는 중요치 않음을 보이는 sensitivity** 제시 |
| R4 | Stage B/C가 단일 장면(784 view)인데 시스템 결론은 4장면 | 최소 2장면에서 Stage C(가장 큰 효과) 재현 |
| R5 | active/archive가 순수 RR이 아님 | §5의 정직한 한계 서술 |
| R6 | "active learning과 비교 안 함" | Stage C의 novelty-first/residual-first가 **이미 greedy acquisition의 대리 실험**임을 명시. BADGE류는 gradient-embedding이므로 §4의 "비싸다" 논거에 포함 |
| R7 | PSNR 개선이 view-set 때문인지 carve/PGBA 때문인지 | 문서 §11.3이 이미 정직하게 인정 중 — **논문에서도 같은 톤 유지** |

---

## 9. 지금 문서에서 바로 고칠 것 (표현만)

1. "novelty를 보조로 쓴다" → **"design 단계의 tie-break이며 ordering에는 관여하지 않는다"**
   (코드가 정확히 그러함: `frontier_fisher`는 FPS의 4순위 tie-break key,
   그리고 demand 스칼라에만 들어감)
2. "화폐처럼 쓴다" → **"완료 서비스에 의해 self-clock되는 admission control"**
3. "curve에 점 찍기" → **"trajectory manifold 위의 quadrature; fill distance가 risk 근사 오차를 지배"**
4. "무한 epoch 병목을 피한다" → **"stratified sampler; zero-demand에서 uniform 주변분포 복원"**
5. §5.4의 `d(i,j)` 식에 **"empirical motion statistics로 whitening된 scale-free SE(3) metric,
   장면 종속 상수 없음"**을 명시 (exp59 교훈과 직결되는 셀링포인트)

---

## 10. 인용 목록 (초안)

**Ordering / RR**
- Gürbüzbalaban, Ozdaglar, Parrilo. *Why random reshuffling beats stochastic gradient descent.* Math. Programming, 2021.
- HaoChen, Sra. *Random shuffling beats SGD after finite epochs.* ICML 2019.
- Mishchenko, Khaled, Richtárik. *Random reshuffling: simple analysis with vast improvements.* NeurIPS 2020.

**Importance sampling / selection bias**
- Needell, Ward, Srebro. *Stochastic gradient descent, weighted sampling, and the randomized Kaczmarz algorithm.* NeurIPS 2014.
- Zhao, Zhang. *Stochastic optimization with importance sampling.* ICML 2015.
- Katharopoulos, Fleuret. *Not all samples are created equal: deep learning with importance sampling.* ICML 2018.

**Gradient-matching coreset (올바르지만 비싼 기준)**
- Mirzasoleiman, Bilmes, Leskovec. *Coresets for data-efficient training (CRAIG).* ICML 2020.
- Killamsetty et al. *GRAD-MATCH.* ICML 2021.

**Design / coverage**
- Gonzalez. *Clustering to minimize the maximum intercluster distance.* TCS 1985. (k-center 2-approx)
- Cochran. *Sampling Techniques.* (stratification, FPC)
- (OED) Fedorov / Pukelsheim — A/D/E-optimality, Fisher 기반 설계의 전제

**Continual learning / replay**
- Vitter. *Random sampling with a reservoir.* ACM TOMS 1985.
- (ER / stability–plasticity 표준 문헌 1–2편)

**Flow control**
- (token bucket / credit-based flow control 표준 레퍼런스 1편, 또는 TCP self-clocking: Jacobson 1988)

---

## 11. 요약 — 무엇이 진짜 contribution인가

1. **분리 자체.** admission/design/ordering이 서로 다른 목적함수를 가지며, 하나의
   heuristic으로 합치면 안 된다는 것. 세 축을 각각 통제한 ablation이 이미 있다.
2. **self-clocked admission.** 장면·GPU·fps 상수 없이 pool 성장을 optimizer 처리량에
   묶는 불변식. cross-hardware 실측이 증거.
3. **"같은 신호가 단계에 따라 부호가 바뀐다"는 실증.** novelty: design에서 중립~약간 이득,
   ordering에서 −10.6%. 여기에 gradient-alignment 상관(0.994 vs 0.005) 측정이 붙는다.
4. (부수) whitening된 SE(3) metric으로 장면 종속 임계값 제거.

**가장 약한 고리는 3번의 앞쪽 절반(design에서의 novelty 이득 −0.35%)이므로,
거기는 주장을 낮추고 뒤쪽 절반(ordering에서의 해악)에 무게를 싣는 게 안전하다.**
