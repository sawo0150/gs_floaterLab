# ERCB 계열 수식 비교와 최종 Service-Shortfall Scheduler 서술안

> 작성일: 2026-09-09
> 목적: 초기 ERCB, exp76 mean-normalized ERCB, exp75 relative-shortfall 방식을
> 하나의 논리로 비교하고, 논문에서 최종 제안식을 어떻게 유도·설명할지 정리한다.

## 0. 번호와 최종 방법 확인

현재 실험 번호상 세 식은 다음과 같다.

1. **초기식:** raw interval-service ERCB
2. **exp76:** threshold-free mean-normalized ERCB
3. **exp75:** relative-floor service-shortfall ERCB

“심각한 학습 부족만 타게팅한다”는 전제와 정확히 일치하는 식은 **exp75**다.
exp76은 모든 interval을 상대 service에 따라 계속 재가중하는 threshold-free 대조식이다.
따라서 본 문서는 exp75 식을 최종 제안식으로 둔다. 이후 논문에서는 실험 번호 대신
`Entropy-Regularized Service-Shortfall Random Reshuffling`과 같이 목적을 드러내는
이름을 사용하는 것이 좋다.

---

## 1. 공통 설정

시점 `t`까지 admission된 frame을 시간적으로 인접한 interval
$G_1,\ldots,G_{M_t}$으로 묶는다. interval $j$의 frame 수와 누적 optimizer
service를

$$
m_j=|G_j|,
\qquad
c_j(t)=\sum_{s\le t}\mathbf 1[J_s=j]
$$

로 두고, member당 service를

$$
r_j(t)=\frac{c_j(t)}{m_j}
$$

로 정의한다. 현재 전체 frame의 평균 service는

$$
\mu_t
=\frac{\sum_jc_j(t)}{\sum_jm_j}
=\sum_jq_jr_j(t),
\qquad
q_j=\frac{m_j}{\sum_km_k}
$$

이다. $q_j$는 frame-uniform sampling이 interval 공간에 유도하는 기준분포다.
세 방식 모두 outer interval은 이 기준분포를 중심으로 선택하고, 선택된 interval 내부
frame은 persistent random reshuffling으로 비복원 추출한다.

---

## 2. 세 수식의 비교

### 2.1 초기 ERCB: raw service의 전역 균등화

가장 단순한 entropy-regularized count balancing은 다음 one-step 문제다.

$$
p_t^{\mathrm{raw}}
=\arg\max_{p\in\Delta}
\left\{
-D_{\mathrm{KL}}(p\|q)
-\beta\,\mathbb E_{j\sim p}[r_j]
\right\}.
$$

닫힌형 해는

$$
p_{t,j}^{\mathrm{raw}}
\propto
q_j\exp(-\beta r_j),
\qquad
w_j^{\mathrm{raw}}
=m_j\exp(-\beta r_j)
$$

이다. 구현에서 $r_{\min}$을 빼도 모든 weight에 같은 상수가 곱해지므로 분포는
변하지 않는다.

이 식은 randomness를 유지하면서 service가 적은 interval을 선호한다는 장점이 있다.
그러나 $r_j$의 절대 크기가 trajectory 길이와 optimizer budget에 따라 계속 증가하므로,
같은 $\beta$의 의미가 장면과 horizon에 따라 달라진다. 또한 이미 충분히 학습된
interval 사이의 작은 count 차이까지 계속 줄이려 한다.

### 2.2 exp76: mean-normalized ERCB

절대 scale 문제를 없애기 위해 상대 service

$$
x_j(t)=\frac{r_j(t)}{\mu_t}
$$

를 사용한다.

$$
p_t^{\mathrm{norm}}
=\arg\max_{p\in\Delta}
\left\{
-D_{\mathrm{KL}}(p\|q)
-\gamma\,\mathbb E_{j\sim p}[x_j]
\right\},
$$

$$
p_{t,j}^{\mathrm{norm}}
\propto q_j\exp(-\gamma x_j),
\qquad
w_j^{\mathrm{norm}}
=m_j\exp\!\left(-\gamma\frac{r_j}{\mu_t}\right).
$$

이 식은 count 전체를 같은 배수로 늘려도 선택분포가 변하지 않는 scale-free law다.
Threshold, clipping, phase switch가 없고 수학적으로 가장 단순하다. 하지만 모든
interval을 계속 전역적으로 재가중하므로 목표는 여전히 **relative equality**다.
“충분히 학습된 interval은 기본 RR에 맡기고 심각한 부족만 복구한다”는 목적은 표현하지
못한다.

### 2.3 exp75 최종식: one-sided relative service shortfall

최종 방법은 정확한 equality 대신 다음의 minimum service requirement를 둔다.

$$
x_j(t)\ge\rho,
\qquad 0<\rho\le1.
$$

즉 모든 interval을 평균과 같게 만들 필요는 없지만, 어떤 interval도 평균 service의
$\rho$배보다 심하게 뒤처지지 않도록 한다. 요구조건 위반량을 나타내는 nonnegative
slack $\xi_j$를 도입한다.

$$
x_j+\xi_j\ge\rho,
\qquad
\xi_j\ge0.
$$

Squared service-shortfall objective를

$$
\mathcal S_\rho(\mathbf x)
=
\min_{\boldsymbol\xi}
\frac{1}{2\rho}\sum_jq_j\xi_j^2
\quad
\text{s.t.}\quad
x_j+\xi_j\ge\rho,\ \xi_j\ge0
$$

로 정의하면 최적 slack은

$$
\xi_j^*=[\rho-x_j]_+
$$

이고, 따라서

$$
\mathcal S_\rho(\mathbf x)
=\frac{1}{2\rho}
\sum_jq_j[\rho-x_j]_+^2
$$

가 된다. Interval $j$의 normalized marginal shortfall는

$$
d_j
=-\frac{1}{q_j}\frac{\partial\mathcal S_\rho}{\partial x_j}
=\left[1-\frac{x_j}{\rho}\right]_+
=\left[1-\frac{r_j}{\rho\mu_t}\right]_+.
$$

따라서 $[\,\cdot\,]_+$는 기존 ERCB에 사후적으로 붙인 clipping이 아니다.
**Minimum-service inequality의 nonnegative violation slack을 제거하면 직접 나오는
one-sided marginal utility**다.

이 utility 아래에서 frame-uniform 기준분포와의 KL divergence를 최소화하면

$$
p_t^*
=\arg\max_{p\in\Delta}
\left\{
\gamma\,\mathbb E_{j\sim p}[d_j]
-D_{\mathrm{KL}}(p\|q)
\right\},
$$

$$
p_{t,j}^*
\propto q_j\exp(\gamma d_j),
\qquad
w_j^*=m_j\exp(\gamma d_j)
$$

를 얻는다. 현재 exp75 구현과 정확히 같은 weight다.

---

## 3. 세 식이 실제로 뜻하는 것

| 구분 | 초기 raw ERCB | exp76 normalized ERCB | exp75 service-shortfall |
|---|---|---|---|
| 최적화 대상 | 절대 service가 작은 interval | 평균 대비 service가 작은 interval | minimum requirement를 위반한 interval만 |
| 목표 | raw count equality | relative count equality | severe under-training 방지 |
| horizon/scale 불변 | 아니오 | 예 | 예 |
| 충분히 학습된 interval 재가중 | 계속함 | 계속함 | 추가 bonus 없음 |
| correction 크기 | count gap에 따라 무제한 증가 가능 | 상대 count gap에 따라 증가 | $1\le e^{\gamma d_j}\le e^\gamma$ |
| threshold 의미 | 없음 | 없음 | service adequacy ratio $\rho$ |
| randomness 기준 | $q_j$ | $q_j$ | $q_j$ |
| 논문상 핵심 한계 | $\beta$ 단위가 horizon 의존 | equality 자체가 과도할 수 있음 | $\rho$ sensitivity를 보여야 함 |

중요한 점은 exp75에서도 $d_j=0$인 interval을 버리지 않는다는 것이다.
이들은 bonus만 받지 않을 뿐, frame-uniform base weight $q_j$를 통해 계속 선택된다.
따라서 hard mining이나 active-only replay가 아니라 **RR 위에 severe-shortfall correction만
bounded하게 추가하는 방식**이다.

---

## 4. 논문에서 권장하는 전개 순서

### 4.1 문제 전제

Growing causal pool에서 optimizer budget은 제한되어 있다. Uniform RR은 높은 mixing을
제공하지만, 늦게 도착한 interval이나 빠른 pool growth 구간은 평균보다 훨씬 적은 service를
받을 수 있다. 반대로 모든 lifetime count를 정확히 같게 만드는 것은 충분히 학습된 과거
interval의 유효한 service까지 빼앗고 short-window mixing을 악화할 수 있다.

따라서 목표를 다음처럼 한정한다.

> Preserve random-reshuffling diversity while correcting only severe relative
> service shortfalls.

### 4.2 Paper-ready method paragraph

> Let $r_j(t)=c_j(t)/|G_j|$ denote the optimizer service per view in temporal
> interval $G_j$, and let $\mu_t=\sum_jc_j(t)/\sum_j|G_j|$ be the current
> frame-average service. Rather than enforcing exact lifetime-count equality, we
> require each interval to receive an adequate fraction $\rho$ of the current
> average, i.e., $r_j(t)/\mu_t\ge\rho$. Introducing a nonnegative slack for
> violations of this requirement yields the squared service-shortfall objective
> $\mathcal S_\rho=(2\rho)^{-1}\sum_jq_j[\rho-r_j/\mu_t]_+^2$, where
> $q_j\propto|G_j|$ is the frame-uniform base measure. Its normalized marginal
> shortfall is $d_j=[1-r_j/(\rho\mu_t)]_+$. We then choose the distribution
> that maximizes expected shortfall reduction while remaining close to the
> frame-uniform base measure in KL divergence, which gives
> $p_j^*\propto|G_j|\exp(\gamma d_j)$.

### 4.3 비복원 구현 문장

> At each outer block, we instantiate these weights through a
> Plackett--Luce/Gumbel-top-$K$ draw over all eligible intervals, yielding
> $K$ distinct interval IDs. Frames within each selected interval are served
> by a persistent random-reshuffling queue. Hence, both outer interval selection
> and inner frame selection are without replacement.

### 4.4 안전하게 주장할 수 있는 성질

- $r_j/\mu_t$를 사용하므로 공통 count scaling과 trajectory horizon에 불변이다.
- $0\le d_j\le1$이므로 shortage bonus는 최대 $e^\gamma$로 bounded된다.
- $r_j\ge\rho\mu_t$이면 추가 correction이 0이고 frame-uniform base sampling은 유지된다.
- 유한 support에서 KL-regularized one-step objective의 닫힌형 해다.
- Outer block과 inner frame에서 중복 없는 random reshuffling을 유지한다.

다음 주장은 피해야 한다.

- 전체 online trajectory에 대해 entropy가 전역 최대라는 주장
- 모든 view의 lifetime count가 같아진다는 주장
- 이 scheduler만으로 non-convex 3DGS convergence가 보장된다는 주장
- $\rho=0.5$가 이론적으로 유일한 최적값이라는 주장

---

## 5. $\rho=0.5$와 $\gamma=\log3$의 위치

두 파라미터의 역할은 다르다.

- $\rho$: 어떤 상태를 “심각한 under-training”으로 볼지 정하는 service-level ratio
- $\gamma$: 심각한 부족 interval에 줄 최대 bonus의 log-odds

현재 $\rho=0.5$는 “평균의 절반 미만을 severe shortfall로 본다”는 해석 가능한
설계값이지만, 수학적으로 자동 결정된 값은 아니다. 논문에서는 development scene에서
한 번 고정하고 다른 scene으로 transfer했다고 설명하며, 최종 제출 전에는 최소한

$$
\rho\in\{0.25,0.5,0.75,1.0\}
$$

sensitivity가 필요하다. $\gamma=\log3$은 full shortage와 no-shortage 사이의 최대
bonus를 3배로 제한한다. 현재 2×/3×/4× 실험에서는 3×가 공통 절충점이었다.

---

## 6. 실험 결과

### 6.1 동일 zero-tail protocol의 주 비교

아래 표는 305·12F, 독립 2 seeds, fixed VIGS pose/init, 모든 causal arrival 즉시
admission, 마지막 arrival 이후 optimizer update 0회, llffhold-8 held-out 평가의
완전히 같은 protocol이다. `Causal RR`은 regularization을 넣기 전 frame-uniform
random-reshuffling starting point다.

| Scene (2-seed 평균) | Causal RR | exp76 normalized | exp75 service-shortfall | exp76 − RR | exp75 − RR |
|---|---:|---:|---:|---:|---:|
| 305 | 32.076 | 32.196 | **32.703** | +.119 | **+.626** |
| 12F | 26.963 | 27.022 | **27.223** | +.059 | **+.260** |

305·12F의 4개 matched run을 metric별로 집계하면 다음과 같다.

| 4-run 평균 | Causal RR | exp76 normalized | exp75 service-shortfall |
|---|---:|---:|---:|
| overall PSNR Δ vs RR | 0 | +.089 (4/4 양수) | **+.443 (4/4 양수)** |
| worst-Q1 PSNR Δ vs RR | 0 | +.233 (4/4 양수) | **+.836 (4/4 양수)** |
| RR-hard-Q1 PSNR Δ | 0 | +.660 (4/4 양수) | **+1.103 (4/4 양수)** |
| late-third PSNR Δ | 0 | +.006 (3/4 양수) | **+.639 (4/4 양수)** |
| frame selection-count CV ↓ | .999 | .904 | **.901** |
| dynamic temporal entropy ↑ | **.974** | .973 | .961 |

핵심 관찰은 exp76과 exp75의 count CV가 `.904`와 `.901`로 거의 같은데도, exp75의
overall·worst·late 품질이 모두 훨씬 높다는 점이다. 즉 이득은 global count equality를
더 강하게 만든 결과가 아니다. Exp75는 RR entropy의 약 96%를 유지하면서 correction을
severe-shortfall support에만 집중했다.

추가 3F까지 포함한 exp75 메인 결과는 3 scenes×2 seeds에서 causal RR 대비 overall
**6/6 양수**, 평균 **+.326dB**, worst-Q1 **+.654dB**, RR-hard-Q1 **+.897dB**,
late-third **+.522dB**였다. 1253 stress control은 overall 평균 `-.009dB`로 동률이었지만
worst-Q1 `+.793dB`, late-third `+1.111dB`였다. 따라서 universal overall win이 아니라
메인 3-scene win과 additional-scene lower-tail recovery로 범위를 구분한다.

### 6.2 초기 raw ERCB 결과를 같은 표에 직접 넣지 않는 이유

초기 raw ERCB의 기존 quality run은 topology 고정 뒤 45k replay를 준 shared-checkpoint
protocol이었다. 선택값 `K=32, beta=.05`는 45k에서 causal RR 대비 305 `+.286dB`,
12F `+.009dB`였지만, 3F 79,081-step transfer는 `-.254dB`였다. 이는 raw scale과
장면 전이 문제를 발견한 진단 evidence다.

이 수치를 위 zero-tail 표의 절대 PSNR과 직접 순위화하면 update budget과 topology
protocol이 달라 불공정하다. 논문에서 초기 raw ERCB까지 동일한 세-arm 표로 제시하려면
305·12F·3F의 zero-tail 2-seed run을 추가해야 한다. 현재 주 표는 동일 protocol이 확보된
`Causal RR / exp76 / exp75`만 사용한다.

---

## 7. 최종 결론과 논문 positioning

초기 ERCB는 entropy와 낮은 service의 절충을 제공하지만 absolute count scale에
의존한다. Exp76은 이를 평균으로 정규화해 scale 문제와 수식 복잡도를 해결했고 RR보다
일관되게 나았지만, 충분히 학습된 interval까지 계속 재가중하여 exp75보다 평균 `.354dB`,
late-third `.632dB` 낮았다.

최종 exp75 식은 목표를 exact equality에서 minimum service adequacy로 바꾼다.
$[\,\cdot\,]_+$는 heuristic clipping이 아니라 이 inequality의 nonnegative slack을
제거한 결과이며, KL regularization은 correction 이후에도 frame-uniform RR 다양성을
유지한다. 따라서 논문의 중심 문장은 다음이 가장 적절하다.

> We do not equalize all lifetime counts. We preserve random reshuffling and
> allocate a bounded correction only to temporal intervals whose per-view
> optimizer service falls below a prescribed fraction of the current mean.

---

## 8. 근거 자료

- exp75 전체 탐색 및 최종 결과:
  [`../../experiments/exp75/exp75_block_weighted_rr_30k_loop.md`](../../experiments/exp75/exp75_block_weighted_rr_30k_loop.md)
- exp75 machine-readable 결과:
  [`../../experiments/exp75/evidence/zero_tail_selected_summary.json`](../../experiments/exp75/evidence/zero_tail_selected_summary.json)
- exp76 normalized 실험:
  [`../../experiments/exp76/exp76_mean_normalized_softmax_ablation.md`](../../experiments/exp76/exp76_mean_normalized_softmax_ablation.md)
- exp76 machine-readable 결과:
  [`../../experiments/exp76/evidence/exp76_summary.json`](../../experiments/exp76/evidence/exp76_summary.json)

수식 서술과 관련된 선행 형식:

- Rockafellar and Uryasev, *Optimization of Conditional Value-at-Risk*:
  threshold 초과분을 positive-part shortfall로 목적함수에 직접 포함한다.
  <https://sites.math.washington.edu/~rtr/papers/rtr179-CVaR1.pdf>
- Du and de Veciana, *Efficiency and Optimality of Largest Deficit First*:
  요구 service와 실제 payoff의 차이를 nonnegative deficit queue로 정의한다.
  <https://users.ece.utexas.edu/~gustavo/papers/DuD17a.pdf>
- Kumar et al., *Self-Paced Learning for Latent Variable Models*:
  선택변수를 포함한 목적함수에서 thresholded sample selection을 유도한다.
  <https://papers.nips.cc/paper_files/paper/2010/hash/e57c6b956a6521b28495f2886ca0977a-Abstract.html>

## 9. 아직 필요한 최종 ablation

1. $\rho\in\{0.25,0.5,0.75,1.0\}$를 305·12F development에서 비교한 뒤 한 값을 고정한다.
2. 고정한 $\rho$를 3F와 독립 seed에 재튜닝 없이 transfer한다.
3. 논문 표에 초기 raw ERCB를 직접 포함하려면 동일 zero-tail 조건으로 재실행한다.
4. 실제 VIGS-SLAM RGB+IMU-only wall-clock budget에서 admission과 결합해 재검증한다.

현재 evidence는 fixed-pose causal-offline 3dgs-custom scheduler ablation이며,
실제 strict VIGS-SLAM 수렴 보장으로 확대해석하지 않는다.
