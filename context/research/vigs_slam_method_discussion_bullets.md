# VIGS-SLAM 연구 방향 논의용 메모

> 목적: 확정된 논문 Method를 보고하는 문서가 아니라, 현재 contribution 후보와
> 검증 경계를 사수님과 논의하기 위한 발표용 bullet note.
>
> 2026-09-04 업데이트: 구현·실측되지 않은 GPU-token admission은 contribution 후보에서
> 제외하고, 실제 final-v7 A/B를 완료한 **entropy-regularized count-balanced block
> reshuffling (ERCB)**을 첫 번째 후보로 올린다.
>
> 현재 상태: ERCB의 품질·시간·entropy feasibility는 확인했으며, trajectory-balanced
> membership은 두 번째 후보로 유지한다. GPU-token admission은 후속 확장 아이디어다.

## 0. 먼저 전달할 한 문장

- 제한된 online mapping service는 다음 세 결정으로 분해할 수 있지만, 현재 contribution
  후보는 **membership과 ordering**에 둔다.
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
  - 주어진 cardinality 안에서 trajectory를 고르게 대표하는 frame을 pool에 넣는다.
  - pool 안에서는 count가 적은 view에 soft preference를 주되, \(K\)-view block 안에서는
    비복원 추출하여 random reshuffling의 coverage를 유지한다.
  - GPU-token cardinality는 이 구조에 붙일 수 있는 후속 확장이지만 현재 contribution은 아니다.

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
- Admission hard constraint는 전체 설계의 바깥쪽 resource model이며 아직 구현하지 않았다.
- 현재 구현된 부분은 ordering objective를 한 step의 count-variance 증가량에 대한
  entropy-regularized surrogate로 바꾸고, 그 Lagrangian의 closed-form Gibbs distribution을
  사용하는 것이다.

## 3. Contribution 후보 1 — Entropy-Regularized Count-Balanced Block Reshuffling

### 전달할 핵심

- Admitted pool의 view를 priority score로 정렬하지 않는다.
- 최종 exposure count variance를 줄이는 방향과 random shuffle에 가까운 방향을 하나의
  entropy-regularized local optimization으로 묶는다.
- 그 해는 추가 heuristic 없이

$$
p_t(i)\propto\exp(-\beta n_i)
$$

인 단순한 Gibbs distribution이다.

### Count imbalance potential과 Lagrangian으로 분포 유도

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

- 한 step에서 view \(i\)를 선택할 확률을 \(p_i\), 그리고 위 식에서 view별로
  달라지는 비용을

$$
d_i=n_i-\bar n
$$

로 둔다. Count imbalance를 줄이는 선택만 강제하면 minimum-count view에 확률이 몰리므로,
randomness를 보존하기 위해 entropy regularization을 더한다.

$$
\min_{\mathbf p}
\quad
\sum_{i=1}^{N}p_i d_i
+
\tau\sum_{i=1}^{N}p_i\log p_i
\qquad
\text{s.t.}\quad
\sum_{i=1}^{N}p_i=1,\;\;p_i>0.
$$

- 여기서 두 번째 항은 \(-\tau H(\mathbf p)\)이며, \(\tau>0\)가 클수록 uniform
  sampling에 가까워진다.
- 정규화 제약에 대한 Lagrange multiplier \(\lambda\)를 도입하면 Lagrangian은

$$
\mathcal L(\mathbf p,\lambda)
=
\sum_i p_i d_i
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
d_i+\tau(\log p_i+1)+\lambda
=0
$$

이므로

$$
p_i
=
\exp\!\left(
-\frac{d_i}{\tau}
\right)
\exp\!\left(
-1-\frac{\lambda}{\tau}
\right).
$$

- 뒤의 항은 모든 view에 공통인 정규화 상수다. 따라서
  \(\sum_i p_i=1\)을 대입하면

$$
p_i
=
\frac{
\exp(-d_i/\tau)
}{
\sum_j\exp(-d_j/\tau)
}.
$$

- \(\beta=1/\tau\), \(d_i=n_i-\bar n\)이고 \(\bar n\)은 모든 view에 공통이므로
  최종 구현식은

$$
p_t(i)
=
\frac{\exp(-\beta n_i)}
{\sum_j\exp(-\beta n_j)}
$$

가 된다.
- \(\tau>0\)일 때 entropy 항의 Hessian은
  \(\operatorname{diag}(\tau/p_i)\succ0\)이므로 이 stationary point가 simplex 내부의
  유일한 minimizer다.
- 즉 이 분포는 임의로 정한 exponential heuristic이 아니라,
  **한 step의 count-variance 증가량을 낮추면서 선택 entropy를 최대한 보존하는 해**다.

### \(K\)-view statistical block

- One-step categorical sampling은 같은 view를 연속 선택할 수 있어 full-pool coverage가
  쉽게 깨진다.
- 이를 막기 위해 block 시작 시 count를 \(n_i^{(b)}\)로 고정하고, current pool에서
  최대 \(K\)개를 sequential weighted sampling without replacement로 뽑는다.

$$
\mathcal W_b^{(0)}=\mathcal A_{\tau_b},
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
- **admission과 분리된 순수 ordering 효과:** 아직 미검증
- **production default 교체:** 보류
- **opt-in block128_beta002 구현:** 유지
- **논문 contribution 후보:** high-entropy count balancing과 \(K\)-view 비복원 coverage의
  결합. 일반적인 lifetime equality나 pool-independent admission까지 주장하지 않음

## 4. Contribution 후보 2 — Trajectory-Balanced View Membership

### 전달할 핵심

- 현재 cardinality rule이 허용한 \(Q_t\)장을 global novelty 순서로 고르지 않는다.
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

## 5. 기존 active/archive는 어디에 두는가

- exp69 pose-active/archive는 더 이상 세 번째 contribution 후보가 아니다.
- 이유
  - Active bonus는 uniform full-pool objective에 대해 의도적인 sampling bias다.
  - Paired 12F에서 약 −0.92dB였고, 다른 장면에서 geometry non-inferiority도 일관되지 않았다.
  - Admission, membership, ordering 효과가 결합되어 해석이 어렵다.
- 앞으로의 위치
  - 비교 baseline 또는 선택적 system heuristic
  - ERCB의 active-bonus ablation
  - 본문 contribution의 기본 정의에서는 제외

## 6. 두 contribution 후보를 하나의 이야기로 묶으면

- **3.1 Entropy-regularized ordering**
  - admitted pool에서 count가 적은 view에 Gibbs weight를 부여
  - \(K\)-view weighted sampling without replacement로 local coverage 보존
  - 결정 대상: 다음 statistical block의 순서 \(\pi_b\)

- **3.2 Trajectory-balanced membership**
  - supervision cardinality가 주어졌을 때 keyframe interval 전체에 slot을 고르게 배치
  - temporal maximin으로 같은 interval 안의 중복을 줄임
  - 결정 대상: 어떤 view가 admitted pool에 들어가는가

- 두 요소의 역할은 분리된다.
  - Membership은 optimizer가 볼 수 있는 supervision support를 정한다.
  - ERCB는 그 support 안에서 exposure와 randomness의 trade-off를 정한다.
  - GPU-token admission은 이 둘과 연결할 수 있는 후속 확장 아이디어이며,
    현재 contribution 후보에는 포함하지 않는다.

- 한 문장 contribution 후보

> **We introduce entropy-regularized count-balanced block reshuffling for
> causal 3DGS mapping: a Lagrangian-derived count-Gibbs distribution softly
> favors under-trained views, while weighted sampling without replacement
> preserves high-entropy coverage over each statistical block.**

- 한국어 발표용

> **누적 학습 횟수가 적은 view를 조금 더 자주 보되, 우선순위로 고정 정렬하지 않고
> \(K\)-view 비복원 block 안에서 높은 무작위성을 유지하는 scheduler입니다.**

## 7. 현재 확정된 사실과 아직 미완료인 부분

### 코드와 실험으로 확인된 부분

- Inter-keyframe RGB를 RGB-only dense replay로 사용하는 경로
- Temporal maximin과 interval water filling membership
- Dense view SE(3) interpolation과 DROID trajectory filling
- ERCB distribution \(p(i)\propto\exp(-\beta n_i)\)
- Statistical block마다 remaining set을 초기화하는 \(K\)-view 비복원 추출
- \(\beta=-1\)에서 production final-v7 동작이 유지되는 opt-in integration
- \(K=128,\beta=0.02\)의 두 trajectory quality/time/entropy 결과
- 60 regression tests와 12 full-run audit

### 아직 구현·검증하지 않은 부분

- 동일 admitted set과 동일 update 수를 고정한 순수 ordering A/B
- Age-adjusted fairness와 raw lifetime fairness 중 최종 논문 target 선택
- 세 장면 이상에서의 quality와 geometry non-regression
- \(K=128\)과 \(\beta=0.02\)의 장면·budget 간 일반화
- GPU-token admission은 contribution이 아닌 후속 system extension으로 별도 검증

## 8. 사수님께 확인받고 싶은 질문

- ERCB를 첫 contribution으로 두고 trajectory membership을 두 번째로 두는 구성이
  system paper의 중심 이야기로 충분히 명확한가?
- Count potential에서 Lagrangian을 거쳐 Gibbs distribution을 얻는 유도가 Method의
  핵심 동기로 충분한가?
- Fairness target은 무엇이어야 하는가?
  - Raw lifetime count equality
  - Arrival age를 고려한 causal quota equality
- \(K=128\)을 method parameter로 제시하려면 어떤 추가 장면·budget sweep이 필요한가?
- EOS rematuration을 포함한 final-map 결과와 strict zero-tail 결과를 어떻게 분리할 것인가?

## 9. 다음 실험 순서

1. 동일 admitted set·동일 update 수·동일 Gaussian budget을 고정해 순수 ordering A/B 구성
2. 다음 ordering baseline 비교
   - Full-pool uniform reshuffling
   - Production causal shuffle
   - exp69 active/archive
   - Raw least-count
   - ME-QARR / ME-BDS
   - ERCB \(K\in\{1,32,128,N\}\), \(\beta\) log sweep
3. 다음 scheduler 지표와 실제 mapping 품질을 함께 보고
   - causal equalization regret
   - Jain fairness
   - normalized entropy \(\rho_H\)
   - cohort mixing
   - minibatch gradient MSE
   - held-out PSNR / SSIM / LPIPS
4. Steady, burst, accelerating growth와 여러 horizon에서 worst-case Pareto frontier 확인
5. 세 장면 이상에서 quality와 geometry non-regression 확인
6. 위 검증을 통과한 뒤에만 production default와 논문 contribution 채택 여부 결정
7. GPU-token admission은 ERCB의 필수 구성요소가 아니라 별도의 후속 system ablation으로 검토

## 10. 논의 마무리용 요약

- 기존 문제
  - Growing pool에서 uniform one-step sampling은 최근 view의 exposure가 부족할 수 있다.
  - Raw least-count는 균등성은 높이지만 순서의 무작위성을 과도하게 잃을 수 있다.
  - Priority ordering은 empirical mapping objective를 왜곡할 수 있다.

- 첫 번째 contribution 후보
  - Count-variance 증가량과 entropy를 하나의 constrained optimization으로 정의
  - Lagrangian을 풀어 \(p_i\propto\exp(-\beta n_i)\)인 Gibbs distribution 유도
  - \(K\)-view weighted sampling without replacement로 random-shuffle coverage 보존

- 두 번째 contribution 후보
  - 주어진 supervision cardinality 안에서 temporal maximin과 interval water filling으로
    trajectory support를 구성

- exp72가 이미 보여준 것
  - \(K=128,\beta=0.02\)는 두 trajectory에서 품질·시간·conditional entropy를 보존할 수 있다.

- exp72가 보여주지 못한 것
  - 일반적인 raw lifetime equality
  - admission과 완전히 분리된 순수 ordering 효과
  - 여러 장면과 compute budget에 대한 일반화

- 지금 가장 정직한 결론

> **ERCB는 실제 구현과 A/B가 있는 첫 contribution 후보이며, 현재 claim은
> Lagrangian-derived soft count balancing과 high-entropy block coverage까지다.
> Lifetime equality와 admission invariance는 추가 검증 전까지 claim에서 제외한다.**
