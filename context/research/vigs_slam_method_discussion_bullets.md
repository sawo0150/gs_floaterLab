# VIGS-SLAM 연구 방향 논의용 메모

> 목적: 확정된 논문 Method를 보고하는 문서가 아니라, 현재 contribution 후보와
> 검증 경계를 사수님과 논의하기 위한 발표용 bullet note.
>
> 2026-09-04 업데이트: 기존 maturity-gated work-credit와 pose-active/archive allocation을
> 중심 contribution으로 두는 구성을 철회하고, **GPU-token admission + trajectory-balanced
> membership + entropy-regularized block reshuffling**의 세 단계로 다시 정리한다.
>
> 현재 상태: ERCB의 실제 final-v7 A/B에 이어, gate-free GPU-token admission도 exp73에서
> 실제 두 장면·7 run으로 구현·검증했다. 다만 exp73는 순수 gate-removal ablation이 아니라
> interval별 무료 bootstrap까지 제거한 token-only 정책 교체다.

## 0. 먼저 전달할 한 문장

- 제한된 online mapping service를 다음 세 결정으로 분리하려고 한다.
  - **Cardinality:** 지금까지 실제로 완료된 GPU work로 몇 장을 admit할 수 있는가?
  - **Membership:** 허용된 수 안에서 trajectory의 어떤 frame을 admit할 것인가?
  - **Ordering:** admitted pool을 어떤 확률분포와 비복원 순서로 학습할 것인가?

$$
\underbrace{S(t)\longmapsto(B_t,Q_t)}_{\text{GPU-token cardinality}}
\;\longrightarrow\;
\underbrace{(Q_t,\mathcal C_t)\longmapsto\mathcal A_t}_{\text{trajectory membership}}
\;\longrightarrow\;
\underbrace{(\mathcal A_t,\mathbf n_t)
\longmapsto(\mathcal W_t,p_t,H_t)}_{\text{entropy-regularized ordering}}
$$

- 한 문장 안의 기호는 다음 뜻이다.
  - \(S(t)\): 시각 \(t\)까지 **실제로 완료된** dense-view optimizer update의 누적량
  - \(B_t\): 완료된 GPU work로부터 남아 있는 admission token
  - \(Q_t\): 이번 시점에 새로 admit할 수 있는 view 수
  - \(\mathcal C_t\): 이미 도착했지만 아직 admit되지 않은 causal inter-keyframe candidate
  - \(\mathcal A_t\): 현재까지 admit되어 replay 가능한 dense-view pool
  - \(\mathbf n_t=(n_i(t))\): admitted view별 실제 누적 학습 횟수
  - \(\mathcal W_t\): 현재 statistical block에서 아직 선택되지 않은 without-replacement
    remaining set
  - \(p_t\): \(\mathcal W_t\)에서 다음 view를 고르는 확률분포
  - \(H_t=H(p_t)\): 그 분포의 conditional Shannon entropy

- 말로 풀면 다음과 같다.
  - GPU가 실제로 끝낸 update만 token으로 바꾼다.
  - 그 token으로 허용된 수만큼 trajectory를 고르게 대표하는 frame을 pool에 넣는다.
  - pool 안에서는 count가 적은 view에 soft preference를 주되, \(K\)-view block 안에서는
    비복원 추출하여 random reshuffling의 coverage를 유지한다.

## 1. 문제를 이렇게 보고 있음

- Dense correspondence 기반 GS-SLAM은 Gaussian을 어디서 초기화할지는 상당 부분 해결했다.
- 아직 남은 문제는 제한된 mapping update를 **어떤 supervision에 배분할지**다.
  - Tracker keyframe은 tracking을 위해 선택된다.
  - Photometric map optimization에 좋은 supervision 집합과 tracking에 좋은 keyframe 집합이
    같아야 할 이유는 없다.

- Keyframe 사이 RGB는 이미 도착한 causal observation이다.
  - 전부 버리면 trajectory coverage를 잃는다.
  - 전부 즉시 넣으면 growing pool에 update가 희석된다.
  - 고정 dense FPS는 GPU가 실제로 감당한 service를 반영하지 않는다.

- 따라서 핵심 질문은 다음과 같다.

> **이미 도착한 RGB stream에서, 현재까지 실제로 확보한 GPU mapping service만으로
> 감당할 수 있는 supervision set을 만들고, 그 안의 view를 충분히 random하면서도
> 장기적으로 편향되지 않게 학습할 수 있는가?**

## 2. 하나의 수학적 모델로 묶기

### 이상적인 전체 문제

- Admission은 resource feasibility를 나타내는 hard constraint로 둔다.
- Scheduler는 최종 exposure 불균형과 random shuffle에서 벗어나는 정도를 함께 줄인다.

$$
\min_{\pi}
\quad
\underbrace{\Phi(\mathbf n_T)}_{\text{final exposure imbalance}}
+
\tau\,
\underbrace{
D_{\mathrm{KL}}\!\left(P_\pi\,\|\,P_{\mathrm{shuffle}}\right)
}_{\text{departure from random reshuffling}}
$$

subject to

$$
\kappa\,[A(t)-A_0]_+\le B_0+\gamma S(t),
\qquad \forall t.
$$

- \(A(t)\)는 시각 \(t\)까지 admit된 누적 view 수다.
- \(\kappa\)는 view 한 장을 admit하는 데 요구하는 service-token 가격이다.
- \(\gamma\)는 완료된 optimizer update 한 회를 token으로 바꾸는 환산 계수다.
- \(B_0\)는 초기 service-token allowance이고, \(A_0\)는 token 과금에서 제외하는 초기
  bootstrap view 수다. \(A_0=0\)이면 모든 admission을 같은 token law로 과금한다.
- \(\tau\)는 exposure balance와 randomness의 trade-off이고
  \(\beta=1/\tau\)로 다시 쓸 수 있다.

### 이 식을 과장하지 않을 범위

- 위 문제는 설계 원리를 보여주는 이상화된 trajectory-level objective다.
- 실제 구현이 전역 \(P_\pi\)에 대한 KL을 직접 계산하거나 전역 최적해를 푸는 것은 아니다.
- 구현은 다음 두 부분으로 분해한다.
  - Admission hard constraint는 deterministic GPU-token controller로 정확히 만족
  - Ordering objective는 한 step의 count-variance 증가량에 대한 entropy-regularized
    surrogate로 풀어 closed-form Gibbs distribution을 사용

## 3. Contribution 후보 1 — Pool-Independent GPU-Token Admission

### 전달할 핵심

- 기존 exp69의 “모든 현재 view의 lifetime count가 2 이상인가?”라는 maturity gate를
  admission 조건에서 제거한다.
- 새 view는 pool 전체가 한 epoch를 끝냈는지와 무관하게, **완료된 GPU service token**만으로
  admit한다.
- Candidate가 충분하면 정확히 \(\kappa/\gamma\)개의 완료 update마다 한 장이 들어온다.

### Deterministic token law

- 시각 \(t\)까지 실제로 완료된 dense-view Adam update 수를

$$
S(t)=\sum_{s\le t} b_s
$$

로 둔다. B1 profile에서는 성공한 replay step마다 \(b_s=1\)이다.

- 지금까지 resource constraint가 허용하는 누적 admission 상한은

$$
A^\star(t)
=
\min\!\left(
M(t),\;
A_0+
\left\lfloor
\frac{B_0+\gamma S(t)}{\kappa}
\right\rfloor
\right)
$$

이다. \(M(t)\)는 시각 \(t\)까지 인과적으로 도착해 candidate가 될 수 있는 전체 view 수다.

- 실제 admitted set 크기가 \(|\mathcal A_{t^-}|\)라면 이번에 열리는 quota는

$$
Q_t
=
\min\!\left(
|\mathcal C_t|,\;
\left[A^\star(t)-|\mathcal A_{t^-}|\right]_+
\right).
$$

- 같은 식을 남은 token으로 쓰면

$$
B_t
=
B_0+\gamma S(t)
-\kappa\bigl(|\mathcal A_t|-A_0\bigr),
\qquad B_t\ge0.
$$

- Admission 한 장마다 \(B_t\leftarrow B_t-\kappa\)로 차감한다.
- 완료되지 않은 queued CUDA work, 미래 frame, 최종 sequence length는 사용하지 않는다.

### 이 방식이 정의상 만족하는 것

- **Pool-size independence**
  - Admission 간격은 \(|\mathcal A_t|\)가 아니라 \(\kappa/\gamma\)로 결정된다.
- **Hardware adaptation**
  - 동일 wall time에 완료되는 \(S(t)\)가 두 배면 admission 속도도 두 배다.
- **Causality**
  - 완료된 update와 이미 도착한 \(\mathcal C_t\)만 사용한다.
- **No maturity gate**
  - \(\min_i n_i\), full-pool epoch 완료, “모든 view 두 번” 조건이 없다.
- **Resource feasibility**
  - 모든 prefix에서 \(\kappa[A(t)-A_0]_+\le B_0+\gamma S(t)\)를 유지한다.

### 구현 시 명시할 정책

- Pending candidate가 없을 때 token을 무한히 쌓아 두면 다음 interval 도착 시 burst admission이
  생길 수 있다.
- 두 정책 중 하나를 논문에서 고정해야 한다.
  - **Carry:** 이미 완료한 service는 미래 candidate에도 사용할 수 있음
  - **No-prepurchase:** \(\mathcal C_t=\varnothing\)이면 \(B_t<\kappa\)가 되도록 초과 token 폐기
- “미래 compute를 당겨 쓰지 않는다”는 두 정책 모두 만족하지만, admission burst 특성은
  다르므로 실험에서는 구분해야 한다.
- exp73 구현은 더 보수적인 **no-prepurchase**를 사용한다.

### 기존 maturity gate와의 차이

- 기존 exp69/exp72 동작
  - 새 view의 count가 0이면 \(\min_i n_i\ge2\) 조건이 깨져 gate가 닫힌다.
  - Pool이 커질수록 한 pass가 길어지고 admission과 ordering이 서로 결합한다.
- 새 token 동작
  - 어느 view가 몇 번 선택됐는지는 ordering 문제에서만 사용한다.
  - Admission은 완료된 총 service \(S(t)\)만 본다.
  - 따라서 scheduler를 바꿔도 동일 \(S(t)\)라면 동일 cardinality를 얻을 수 있다.

### 현재 증거와 claim boundary

- exp73에서 최초 전역 seed 한 장 뒤 모든 신규 view를 token으로 admission하는 경로를 실제
  final-v7에 opt-in 구현했다.
- 두 장면 7개 gate-free run의 admission poll 526개에서

$$
A_{\mathrm{paid}}(u)=\left\lfloor\frac{u}{\kappa}\right\rfloor
$$

  의 정수 오차가 모두 0이었다. 즉 완료된 dense update에 대한 admission slope는 실제
  growing pool에서도 정확히 \(1/\kappa\)였다.
- 공통 \(\kappa=22\)는 aria1253 2회 평균 27.711dB(baseline 대비 +0.003dB)와
  aria301_305 28.815dB(−0.119dB)로 두 장면 모두 −0.2dB 품질 기준을 통과했다.
- 단, exp73는 gate만 제거한 실험이 아니다.
  - 기존: interval별 무료 bootstrap + maturity-gated paid admission
  - exp73: 최초 seed 1장 + token-only paid admission
  - 따라서 1253 pool 422.5→275.5 감소는 gate 제거가 아니라 bootstrap 제거와
    \(\kappa=22\) pacing의 결합 효과다. 305 pool은 674→749로 증가했다.
- Selection CV는 1253/305에서 0.951/0.942로 악화했다. 그러므로 현재 claim은
  **gate-free token law의 정확성과 두 장면의 \(\kappa=22\) feasibility**까지이며,
  순수 gate 효과, final count 균등성, universal \(\kappa\), production default는 아니다.

## 4. Contribution 후보 2 — Trajectory-Balanced View Membership

### 전달할 핵심

- Token controller가 허용한 \(Q_t\)장을 global novelty 순서로 고르지 않는다.
- 먼저 trajectory interval을 고르게 대표하고, information signal은 같은 interval 안의
  중복을 줄이는 보조 기준으로 제한한다.
- 이 단계는 training-set membership만 결정하며 다음 optimizer target을 정하지 않는다.

### Causal interval

- 연속한 두 keyframe을 \(k_{j-1},k_j\)라 두면

$$
\mathcal I_j=(k_{j-1},k_j)
$$

- 오른쪽 endpoint \(k_j\)까지 실제로 도착한 뒤에만 후보를 만든다.

$$
\mathcal C_j
=
\left\{
v\mid k_{j-1}<v<k_j,\;
v\notin\mathcal K_t,\;
v\notin\mathcal E
\right\}
$$

- \(\mathcal K_t\)는 tracking keyframe, \(\mathcal E\)는 held-out evaluation frame이다.

### Interval 내부: temporal maximin

$$
v_j^\star
=
\arg\max_{v\in\mathcal C_j\setminus\mathcal A_j}
\min_{u\in\{k_{j-1},k_j\}\cup\mathcal A_j}
|\tau(v)-\tau(u)|.
$$

- 첫 view는 interval 중앙 부근에 놓인다.
- 이후 가장 큰 temporal gap을 반복적으로 나눈다.
- 거의 같은 timestamp의 frame이 quota를 독점하는 것을 막는다.

### Interval 사이: water filling

$$
j^\star
=
\arg\min_{
j:\mathcal C_j\setminus\mathcal A_j\ne\varnothing
}
|\mathcal A_j|.
$$

- Pending candidate가 있는 interval 중 현재 admitted count가 가장 작은 곳을 먼저 채운다.
- 긴 interval 하나나 고밀도 구간 하나가 전체 \(Q_t\)를 독점하지 못하게 한다.

### Non-keyframe pose

- Endpoint pose 사이의 SE(3) 보간으로 초기화한다.

$$
\alpha_v
=
\frac{\tau_v-\tau_{k_{j-1}}}
{\tau_{k_j}-\tau_{k_{j-1}}},
$$

$$
T_v^{(0)}
=
\operatorname{Exp}\!\left(
\alpha_v
\operatorname{Log}
\left(T_{k_j}T_{k_{j-1}}^{-1}\right)
\right)
T_{k_{j-1}}.
$$

- 이후 DROID 계열 dense correspondence의 trajectory filling으로 보정한다.
- 오른쪽 endpoint가 도착한 과거 interval만 처리하므로 causal하다.
- Dense view는 RGB supervision만 사용하고 keyframe depth를 억지로 복제하지 않는다.

### 현재 실험이 말해 주는 것

- 동일 784-view cardinality에서 global coverage-only selection은 temporal baseline보다
  AUC가 약 3.88% 나빴다.
- Residual-based membership도 약 1.64% 나빴다.
- Interval quota 안의 representative selection 이득은 약 0.35%로 작았다.
- 따라서 강한 claim은 “novel frame을 잘 찾는다”가 아니다.
- 더 안전한 claim은 **cardinality와 ordering 사이에 trajectory representation을 독립된
  문제로 두고 temporal support를 우선 보존한다**는 것이다.

## 5. Contribution 후보 3 — Entropy-Regularized Count-Balanced Block Reshuffling

### 전달할 핵심

- Admitted pool의 view를 priority score로 정렬하지 않는다.
- 최종 exposure count variance를 줄이는 방향과 random shuffle에 가까운 방향을 하나의
  entropy-regularized local optimization으로 묶는다.
- 그 해는 추가 heuristic 없이

$$
p_t(i)\propto\exp(-\beta n_i)
$$

인 단순한 Gibbs distribution이다.

### Count imbalance potential에서 분포 유도

| 기호 | 이 소절에서의 역할 |
|---|---|
| \(t\) | 현재 online mapping 또는 replay 선택 시점 |
| \(i,j\) | admitted view index. \(i\)는 선택 후보이고 \(j\)는 정규화 합의 index |
| \(\mathcal A_t\), \(N=|\mathcal A_t|\) | 시점 \(t\)의 admitted view pool과 그 크기 |
| \(n_i\), \(\mathbf n\) | view \(i\)의 실제 누적 optimizer-update 횟수와 전체 count vector |
| \(\bar n=N^{-1}\sum_i n_i\) | 현재 pool의 view당 평균 학습 횟수 |
| \(\mathbf e_i\) | \(i\)번째 성분만 1인 단위 vector. \(\mathbf n+\mathbf e_i\)는 view \(i\)를 한 번 더 선택한 상태 |
| \(\Phi(\mathbf n)\), \(\Delta_i\Phi\) | count 불균형 potential과 view \(i\)를 한 번 선택했을 때의 증가량 |
| \(p_i\), \(p_t(i)\) | view \(i\)를 다음 optimizer target으로 선택할 확률 |
| \(\Delta_N\) | \(p_i\ge0\), \(\sum_i p_i=1\)을 만족하는 \(N\)-차원 probability simplex |
| \(H(p)\) | 선택분포의 Shannon entropy. 클수록 uniform selection에 가까움 |
| \(\tau>0\), \(\beta=1/\tau\) | entropy temperature와 inverse temperature. \(\beta\)가 클수록 low-count view 선호가 강함 |
| \(\lambda\) | \(\sum_i p_i=1\) 제약에 대응하는 Lagrange multiplier |

- 모든 \(\log\)는 natural logarithm을 사용한다.
- \(n_i\)는 frame의 age가 아니라 실제 mapping loss와 optimizer update에 사용된 횟수다.

- 현재 pool 크기를 \(N\), view \(i\)의 누적 학습 횟수를 \(n_i\), 평균을
  \(\bar n=N^{-1}\sum_i n_i\)라 두고

$$
\Phi(\mathbf n)
=
\frac12\sum_{i=1}^{N}(n_i-\bar n)^2
$$

로 정의한다.

- View \(i\)를 한 번 더 학습했을 때의 정확한 증가량은

$$
\Delta_i\Phi
=
\Phi(\mathbf n+\mathbf e_i)-\Phi(\mathbf n)
=
n_i-\bar n
+\frac12\left(1-\frac1N\right).
$$

- 마지막 항은 모든 \(i\)에 공통이므로, count가 작은 view를 고를수록 다음-step
  imbalance 증가가 작다.

- 다음 선택분포를 simplex \(\Delta_N\) 위에서

$$
p_t
=
\arg\min_{p\in\Delta_N}
\left[
\sum_i p_i(n_i-\bar n)
-\tau H(p)
\right],
$$

$$
H(p)=-\sum_i p_i\log p_i
$$

- 정규화 제약 \(\sum_i p_i=1\)에 대한 Lagrange multiplier \(\lambda\)를 도입한다.
  \(-\tau H(p)=\tau\sum_i p_i\log p_i\)이므로 Lagrangian은

$$
\mathcal L(p,\lambda)
=
\sum_i p_i(n_i-\bar n)
+
\tau\sum_i p_i\log p_i
+
\lambda\left(\sum_i p_i-1\right)
$$

이다.

- 각 \(p_i\)에 대한 stationary condition은

$$
\frac{\partial\mathcal L}{\partial p_i}
=
n_i-\bar n
+
\tau(\log p_i+1)
+
\lambda
=0
$$

이므로

$$
p_i
=
\exp\!\left[-\frac{n_i-\bar n}{\tau}\right]
\exp\!\left[-1-\frac{\lambda}{\tau}\right]
$$

가 된다. 두 번째 지수항은 모든 view에 공통인 정규화 상수이므로
\(\sum_i p_i=1\)을 적용하면

$$
p_t(i)
=
\frac{
\exp[-\beta(n_i-\bar n)]
}{
\sum_j\exp[-\beta(n_j-\bar n)]
},
\qquad
\beta=\frac1\tau.
$$

- \(\tau>0\)이면 entropy 항이 strictly convex이므로 위 stationary point는 simplex 내부의
  유일한 minimizer다.
- \(\bar n\)은 공통항이므로 구현식은

$$
p_t(i)
=
\frac{\exp(-\beta n_i)}
{\sum_j\exp(-\beta n_j)}
$$

가 된다.

### \(K\)-view statistical block

| 기호 | 이 소절에서의 역할 |
|---|---|
| \(K\) | 한 block에서 중복 없이 미리 뽑아 둘 최대 view 수 |
| \(b\) | statistical block index |
| \(k\) | block \(b\) 내부의 sequential draw index, \(k=0,\ldots,K-1\) |
| \(t_b\) | block \(b\)를 생성하는 online 시점 |
| \(n_i^{(b)}\) | block 생성 시 고정한 view \(i\)의 count snapshot |
| \(\mathcal W_b^{(k)}\) | \(k\)번째 draw 직전에 아직 선택되지 않은 remaining view set |
| \(p_{b,k}(i)\), \(I_{b,k}\) | remaining set에서 view \(i\)를 뽑는 conditional probability와 실제 추출 결과 |

- One-step categorical sampling은 같은 view를 연속 선택할 수 있어 full-pool coverage가
  쉽게 깨진다.
- 이를 막기 위해 block 시작 시 count를 \(n_i^{(b)}\)로 고정하고, current pool에서
  최대 \(K\)개를 sequential weighted sampling without replacement로 뽑는다.

$$
\mathcal W_b^{(0)}=\mathcal A_{t_b},
$$

$$
p_{b,k}(i)
=
\frac{
\exp(-\beta n_i^{(b)})
}{
\sum_{j\in\mathcal W_b^{(k)}}
\exp(-\beta n_j^{(b)})
},
\qquad i\in\mathcal W_b^{(k)},
$$

$$
I_{b,k}\sim p_{b,k},
\qquad
\mathcal W_b^{(k+1)}
=
\mathcal W_b^{(k)}\setminus\{I_{b,k}\}.
$$

- \(K\)개를 뽑거나 remaining set이 빌 때 block을 닫는다.
- 다음 block은 그 시점의 growing pool로 \(\mathcal W\)를 다시 만든다.
- 실제 renderer batch는 B1이며, 미리 만든 block order를 한 view씩 소비한다.
- Block 중간에 도착한 view는 다음 block부터 참여한다.

### 두 극단과 정확한 random-shuffle claim

- \(\beta=0\)
  - 현재 block에서 가능한 모든 ordered \(K\)-subset에 균등하다.
  - \(K\ge N_t\)일 때에만 전체 pool의 \(N_t!\)개 permutation에 정확히 균등한
    **full-pool random reshuffling**이 된다.
- \(\beta\rightarrow\infty\)
  - 현재 minimum-count view부터 선택하는 randomized least-count에 접근한다.
- 유한 \(\beta>0\)
  - 덜 학습된 view에 soft preference를 주되 모든 remaining view에 non-zero support를 둔다.
- Count가 비슷해지면 weight가 자동으로 같아져 uniform without-replacement block으로
  돌아간다.

### Entropy 측정

| 기호 | 이 소절에서의 역할 |
|---|---|
| \(|\mathcal W_b^{(k)}|\) | 현재 draw에서 선택 가능한 remaining view 수 |
| \(H(p_{b,k})\) | 해당 draw의 conditional Shannon entropy |
| \(\rho_H\) | 모든 draw의 entropy 합을 동일 support에서 가능한 uniform maximum으로 정규화한 값 |

- 각 draw의 uniform maximum은 \(\log|\mathcal W_b^{(k)}|\)이다.
- Run-level normalized conditional entropy를

$$
\rho_H
=
\frac{
\sum_{b,k}H(p_{b,k})
}{
\sum_{b,k}\log|\mathcal W_b^{(k)}|
}
$$

로 보고한다.
- \(\rho_H=1\)이면 같은 remaining support에서 uniform draw와 동일한 entropy다.

### exp72 실제 final-v7 A/B

- 실제 변경
  - replay draw distribution만 opt-in ERCB로 교체
  - admission rule, mapping loss, optimizer, PGBA, Gaussian budget, terminal dust-GC,
    EOS rematuration은 control과 동일
  - 기본값 \(\beta=-1\)은 기존 final-v7 queue를 그대로 사용
- 최선 설정

$$
K=128,\qquad\beta=0.02.
$$

| Scene | baseline PSNR | ERCB PSNR | ΔPSNR | online wall 변화 | \(\rho_H\) |
|---|---:|---:|---:|---:|---:|
| aria1253 | 27.708 | 27.624 | −0.084 dB | +0.033% | 0.99869 |
| aria1253rot | 24.814 | 25.177 | +0.362 dB | +0.014% | 0.99842 |

- 확인된 것
  - 두 trajectory 모두 사전 정의한 −0.2dB quality non-regression 기준 통과
  - online wall-time 차이 0.04% 미만
  - uniform maximum conditional entropy의 99.84% 이상 유지
  - 60 scheduler regression tests와 12개 full-run audit 통과
  - \(K=1,\beta=0\)은 aria1253에서 −2.863dB, \(K=32,\beta=0.02\)는 −2.082dB
  - 따라서 높은 one-step entropy만으로는 부족하고 충분히 긴 without-replacement
    coverage가 실제 3DGS 품질에 중요하다는 증거를 얻음

### 실패한 조건

- aria1253에서는 middle/first lifetime count가 0.971이었지만,
  aria1253rot에서는 baseline 0.758에서 ERCB 0.520으로 악화했다.
- 따라서 **일반적인 raw lifetime-count equalization은 실패**했다.
- Final pool도 aria1253 422.5→333, rot 353→334로 변했다.
- 원인은 exp72가 기존 minimum-count maturity gate를 유지해 ordering이 admission 시점과
  cardinality에 계속 영향을 주기 때문이다.
- 따라서 **pool-size-independent admission도 실패**했다.

### 현재 판정

- **품질 보존 scheduler 후보:** 성공
- **높은 conditional entropy:** 성공
- **일반적인 lifetime 균등화:** 실패
- **pool-independent admission:** 실패
- **production default 교체:** 보류
- **opt-in block128_beta002 구현:** 유지
- **논문 contribution:** GPU-token admission과 결합해 admission을 분리한 뒤 재검증 전에는
  완성된 공동 방법론으로 주장하지 않음

## 6. 기존 active/archive는 어디에 두는가

- exp69 pose-active/archive는 더 이상 세 번째 contribution 후보가 아니다.
- 이유
  - Active bonus는 uniform full-pool objective에 대해 의도적인 sampling bias다.
  - Paired 12F에서 약 −0.92dB였고, 다른 장면에서 geometry non-inferiority도 일관되지 않았다.
  - Admission, membership, ordering 효과가 결합되어 해석이 어렵다.
- 앞으로의 위치
  - 비교 baseline 또는 선택적 system heuristic
  - ERCB의 active-bonus ablation
  - 본문 contribution의 기본 정의에서는 제외

## 7. 세 contribution을 하나의 이야기로 묶으면

- **3.1 GPU-token cardinality**
  - 완료된 GPU service만큼 supervision pool을 확장
  - 결정 대상: \(|\mathcal A_t|\)
  - maturity gate와 pool epoch에 독립

- **3.2 Trajectory membership**
  - 열린 \(Q_t\)개 slot을 keyframe interval 전체에 고르게 배치
  - 결정 대상: 어떤 \(v\)가 \(\mathcal A_t\)에 들어가는가

- **3.3 Entropy-regularized ordering**
  - admitted pool에서 count imbalance를 줄이는 Gibbs weight와 \(K\)-view 비복원
    coverage를 결합
  - 결정 대상: 다음 statistical block의 순서 \(\pi_b\)

- 한 문장 contribution 후보

> **We decouple causal dense supervision into GPU-token admission,
> trajectory-balanced membership, and entropy-regularized block reshuffling:
> completed mapping service controls how many views enter the pool, temporal
> maximin controls which views enter, and a count-Gibbs distribution produces
> high-entropy without-replacement replay within the admitted pool.**

- 한국어 발표용

> **GPU가 실제로 끝낸 update만큼 pool을 키우고, 열린 slot은 trajectory 전체에 고르게
> 배치하며, admitted view는 count가 적은 쪽에 soft preference를 주는 \(K\)-view 비복원
> block으로 학습한다.**

## 8. 현재 확정된 사실과 아직 미완료인 부분

### 코드와 실험으로 확인된 부분

- Inter-keyframe RGB를 RGB-only dense replay로 사용하는 경로
- Temporal maximin과 interval water filling membership
- Dense view SE(3) interpolation과 DROID trajectory filling
- ERCB distribution \(p(i)\propto\exp(-\beta n_i)\)
- Statistical block마다 remaining set을 초기화하는 \(K\)-view 비복원 추출
- \(\beta=-1\)에서 production final-v7 동작이 유지되는 opt-in integration
- \(K=128,\beta=0.02\)의 두 trajectory quality/time/entropy 결과
- 60 regression tests와 12 full-run audit
- Gate-free token-only admission 구현과 64 scheduler regression tests
- exp73의 7개 gate-free run·526 admission poll에서 token-law 정수 오차 0
- \(\kappa=22\)의 aria1253 2회와 aria301_305 1회 품질 기준 통과

### 아직 구현·검증하지 않은 부분

- GPU slowdown과 hardware 변화에서의 admission tracking
- 동일 admitted set과 동일 update 수를 고정한 순수 ordering A/B
- GPU-token admission과 ERCB를 결합한 end-to-end 결과
- Age-adjusted fairness와 raw lifetime fairness 중 최종 논문 target 선택
- 세 장면 이상에서의 quality와 geometry non-regression
- Interval bootstrap을 유지한 순수 gate-removal ablation
- Scene-general 또는 online-adaptive \(\kappa\) 결정 규칙

## 9. 사수님께 확인받고 싶은 질문

- 세 축을 **cardinality--membership--ordering**으로 분리한 framing이 system paper의
  중심 contribution으로 충분히 명확한가?
- Exp73의 token-only 정책을 C1 정의로 채택할지, interval bootstrap을 유지하는 순수
  gate-removal arm을 먼저 추가할지?
- Fairness target은 무엇이어야 하는가?
  - Raw lifetime count equality
  - Arrival age를 고려한 causal quota equality
- ERCB는 독립 contribution인가, GPU-token admission을 뒷받침하는 optimizer scheduling
  component인가?
- \(K=128\)을 method parameter로 제시하려면 어떤 추가 장면·budget sweep이 필요한가?
- EOS rematuration을 포함한 final-map 결과와 strict zero-tail 결과를 어떻게 분리할 것인가?

## 10. 다음 실험 순서

1. \(\kappa=22\) token-only admission 아래 동일 admitted set·동일 update 수·동일 Gaussian
   budget으로 ERCB의 순수 ordering A/B 구성
2. 다음 ordering을 비교
   - Full-pool uniform reshuffling
   - Production causal shuffle
   - exp69 active/archive
   - Raw least-count
   - ME-QARR / ME-BDS
   - ERCB \(K\in\{1,32,128,N\}\), \(\beta\) log sweep
3. 평균 rank 대신 worst-case Pareto frontier 보고
   - causal equalization regret
   - Jain fairness
   - normalized entropy \(\rho_H\)
   - cohort mixing
   - minibatch gradient MSE
   - held-out PSNR / SSIM / LPIPS
4. 필요하면 interval bootstrap을 유지하고 gate만 제거한 arm을 추가해 gate 효과를 분리
5. GPU slowdown·다른 hardware에서 service당 admission slope가 유지되는지 확인
6. Quality와 geometry non-regression을 세 장면 이상에서 확인한 뒤에만 production default와
   논문 contribution 채택 여부 결정

## 11. 논의 마무리용 요약

- 기존 문제
  - Fixed FPS는 GPU capacity를 반영하지 않는다.
  - Maturity gate는 growing pool 크기와 admission을 결합한다.
  - Priority ordering은 empirical mapping objective를 왜곡할 수 있다.

- 새 방법 후보
  - Admission: completed GPU-token hard constraint
  - Membership: temporal maximin + interval water filling
  - Ordering: count-Gibbs + \(K\)-view sampling without replacement

- exp72가 이미 보여준 것
  - \(K=128,\beta=0.02\)는 두 trajectory에서 품질·시간·entropy를 보존할 수 있다.

- exp72가 보여주지 못한 것
  - 일반 lifetime equality
  - pool-independent admission
  - gate-free end-to-end 방법론

- exp73가 새로 보여준 것
  - maturity count 없이 완료된 dense update만으로 token admission 가능
  - 7개 run·526 poll에서 \(A_{paid}(u)=\lfloor u/\kappa\rfloor\) 정확히 만족
  - \(\kappa=22\)가 현재 두 장면에서 품질 기준 통과

- exp73도 보여주지 못한 것
  - interval bootstrap을 유지한 순수 gate 효과
  - final count 균등성
  - scene-general \(\kappa\)와 production readiness

- 지금 가장 정직한 결론

> **GPU-token admission은 exp73에서 실제로 분리·검증했고 ERCB도 개별 feasibility를
> 확인했다. 다음 핵심은 \(\kappa=22\) token-only admission 아래 동일 membership을 고정해
> ERCB가 균등성과 품질을 함께 보존하는지 공동 A/B하는 것이다.**
