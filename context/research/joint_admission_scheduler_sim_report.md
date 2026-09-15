# Growing-pool admission과 frame scheduling의 공동 문제 정의

> 날짜: 2026-09-04  
> 범위: scheduler-only 합성 시뮬레이션. 실제 3DGS PSNR/geometry 실험이 아니다.  
> 최종 판정: **요구한 세 조건을 그대로 동시에 만족하는 \((\kappa,\beta)\)는 없었다.**

## 0. 결론

이번 분석에서 처음 사용한 terminal count metric은 count multiset만 비교하여
"누가 그 count를 받았는가"를 가렸다. 이를 수정해 각 view의 실제 admission 시점을
저장하고, 초기 cohort와 정확히 stream 절반 \(T/2\) 부근에 admission된 cohort를 직접
비교했다.

수정 후 결과는 다음과 같다.

- GPU-token admission 자체는 타당하다. backlog가 있을 때
  \(A(u)=\lfloor u/\kappa\rfloor\)로 두면 pool 증가율은 현재 pool 크기와 무관하고,
  모든 sweep에서 target tracking error와 budget violation이 정확히 0이었다.
- maturity gate는 빠른 admission 부하에서 실패한다. \(B=32\), 18,000 update,
  \(\kappa=32\)일 때 uniform gate는 목표 admission의 18.9%만 처리했고 최대 455.9 frame
  뒤처졌다. active bonus를 넣어도 28.4%, 402.2 frame lag였다.
- 그러나 token admission 위의 scheduling에는 **유효한 단일 \(\beta\)가 없었다.**
  terminal lifetime equality를 강하게 만들수록 full-pool shuffle entropy와
  trajectory-correlated gradient mixing이 무너졌다.
- \(B\in\{8,16,32\}\), \(\kappa=16\)부터 4096, \(\beta=0\)부터 \(\infty\)까지
  확장해도 사전 정의한 공동 조건을 만족한 점은 0개였다.

따라서 현재 전제 아래에서는 \(\beta\)를 추천하면 안 된다.

- full-pool uniform objective가 우선이면 \(\beta=0\)이고, fairness 목표를
  age-adjusted exposure로 바꿔야 한다.
- lifetime count equality가 우선이면 큰 \(\beta\) 또는 least-count가 맞지만,
  그 gradient는 full-pool uniform objective에 대해 unbiased하다고 말할 수 없다.
- 둘 다 원하면 bounded pool, admission stop 뒤 catch-up tail, 또는 objective 변경 중
  하나가 필요하다. strict zero-tail + unbounded growing pool에서는 세 요구를 그대로
  유지할 수 없다.

## 1. 공통 수학 모델

### 1.1 GPU work clock과 admission

완료된 optimizer update 수를 \(u\), 그때까지 도착한 candidate 수를 \(C(u)\),
추가 admission 수를 \(A(u)\)라 한다. saturated backlog에서 token controller는

\[
A(u)=\min\!\left(C(u),\left\lfloor\frac{u}{\kappa}\right\rfloor\right),
\qquad
N(u)=N_0+A(u)
\]

로 정의한다. GPU가 실제 시간당 \(R\) update를 처리하면 backlog 구간의 pool 성장률은

\[
\frac{dN}{dt}\simeq \frac{R}{\kappa}
\]

이다. 이 식에는 현재 pool 크기 \(N\)이 없으므로 요구 2를 직접 만족한다. 반대로
`min count >= 2` gate는 admission을 service history와 pool 크기에 다시 결합하므로 이
성질을 잃는다.

### 1.2 Terminal lifetime equality

view \(i\)의 실제 lifetime selection count를

\[
n_i(T)=\sum_{u=1}^{T}\mathbf 1[I_u=i]
\]

로 둔다. 목표는 마지막 순간에 모든 view의 raw count를 무조건 같게 만드는 것이 아니라,
arrival causality와 한 logical minibatch 안의 비복원 선택을 지키는 범위에서 count
dispersion을 최소화하는 것이다.

그 causal lower bound는 매 block마다 현재 minimum-count view \(B\)개를 고르는
`causal least-count` oracle로 계산한다. unit increment의 convex dispersion에 대한
exchange argument로, 더 큰 count를 올리는 행동은 더 작은 count를 올리는 행동보다
terminal squared dispersion을 개선할 수 없으므로 이 greedy endpoint가 count-leveling
한계가 된다.

평가값은 다음 네 개다.

1. oracle count multiset 대비 terminal NRMSE
2. oracle 대비 Jain-index regret
3. 초기 cohort와 실제 \(T/2\) admission cohort의 mean-count ratio
4. 동일 ratio의 causal oracle 값

세 번째가 사용자가 말한 “앞 view와 절반부터 들어온 view가 비슷한가”를 직접 측정한다.
마지막에 들어온 view는 이 비교에서 제외한다.

### 1.3 Full-pool shuffle target

시점 \(u\)의 admitted pool에서 크기 \(B\)의 ordered batch를 완전한 random
reshuffling으로 뽑는 기준분포는

\[
P_0(i_1,\ldots,i_B\mid\mathcal V_u)=\frac{1}{(N_u)_B},
\qquad
(N)_B=\frac{N!}{(N-B)!}
\]

이다. 다음을 측정한다.

- normalized policy entropy:
  \(\widehat H(P)/\log (N)_B\). 1이면 exact uniform shuffle다.
- temporal Wasserstein distance: 선택된 frame index가 trajectory 일부에 몰리는지 측정한다.
- cohort entropy: trajectory bin 전체가 한 batch에 섞이는지 측정한다.
- gradient MSE ratio:

  \[
  R_g=
  \frac{\mathbb E\|\bar g_{\mathrm{batch}}-\bar g_{\mathrm{pool}}\|^2}
  {\frac{N-B}{B(N-1)}\,\operatorname{Var}_{\mathrm{pool}}(g)}.
  \]

  분모는 uniform without-replacement batch mean의 정확한 finite-population variance다.
  \(R_g=1\)이 ideal shuffle이고, IID·smooth trajectory·abrupt regime의 3개 synthetic
  gradient field를 사용했다.

## 2. 탐색한 단순 scheduler family

Lifetime count가 작은 view를 선호하되 randomness를 유지하는 ERCB
(entropy-regularized count balancing)를 사용했다. batch 안에서 이미 뽑힌 view를
제외하며 순차적으로

\[
p_\beta(i\mid\mathcal R)
=\frac{\exp(-\beta n_i)}
{\sum_{j\in\mathcal R}\exp(-\beta n_j)}
\]

로 뽑는다.

이 분포는 한 번의 선택마다

\[
\arg\max_{p\in\Delta}
\left\{H(p)-\beta\,\mathbb E_p[n_i]\right\}
\]

의 Gibbs 해다. 따라서 임의의 heuristic score 합이 아니라, entropy와 낮은 lifetime
count 사이의 가장 단순한 Lagrangian family다.

- \(\beta=0\): exact full-pool uniform random shuffle
- \(\beta\to\infty\): randomized causal least-count
- 중간 \(\beta\): 두 endpoint의 연속적 절충

비교군은 latest 16 view에 3배 odds를 주는 active bonus와, uniform/active bonus 위에
`minimum count >= 2` maturity gate를 붙인 두 방식이다.

## 3. 공동 acceptance specification

가중합은 단위 재조정만으로 답이 바뀌므로 쓰지 않았다. 다음 조건을 전부 만족해야
feasible로 판정했다. seed randomness에는 각 scenario의 5/95 percentile을 사용했다.

| 범주 | 조건 |
|---|---:|
| admission | budget violation = 0, target NRMSE = 0 |
| terminal fairness | oracle NRMSE \(\le0.10\) |
| terminal fairness | Jain regret \(\le0.01\) |
| half-vs-first | \(0.90\le n_{T/2}/n_{0}\le1.10\) |
| shuffle | normalized entropy \(\ge0.95\) |
| gradient | 3-field mean MSE ratio \(\le2.0\) |
| gradient | worst-field MSE ratio \(\le3.0\) |
| temporal mix | Wasserstein / uniform \(\le2.0\) |

각 점의 `constraint_violation_factor`는 위 조건을 각 한계로 정규화한 뒤 취한 최댓값이다.
1 이하여야 feasible다. 이 threshold는 정리가 아니라 현재 operating specification이며,
CSV에 모두 노출했다.

## 4. Sweep

### 4.1 주 sweep

- \(B=32\)
- horizon: 6,000 / 12,000 / 18,000 optimizer updates
- 16 random seeds
- \(\kappa\): 32, 48, 64, 96, 128, 192, 256, 384, 512, 768, 1024,
  1536, 2048, 3072, 4096
- \(\beta\): 0, 0.0025, 0.005, 0.0075, 0.01, 0.0125, 0.015, 0.02,
  0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 1, \(\infty\)
- scheduler 21개(ERCB 18 + controls 3), 총 15,120 scheduler trajectories

### 4.2 Batch sensitivity

동일한 3개 horizon에서 \(B=8,16\)을 각각 8 seeds로 추가 실행했다. 두 경우도
feasible point가 없었다.

| \(B\) | feasible 수 | 최소 위반점 \((\kappa,\beta)\) | violation | half/first | oracle half/first | entropy | gradient mean / worst |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0 | (1024, 0.005) | 1.705 | 0.609 | 0.687 | 0.842 | 2.75 / 4.72 |
| 16 | 0 | (1024, 0.005) | 1.449 | 0.621 | 0.676 | 0.935 | 2.53 / 3.72 |
| 32 | 0 | (768, 1.0) | 1.640 | 0.549 | 0.548 | 0.643 | 3.22 / 4.61 |

위 “최소 위반점”은 채택점이 아니다. 최소 한 조건을 44.9–70.5% 초과하므로 작은
threshold 조정으로 해결되는 경계도 아니다.

## 5. 왜 feasible set이 비는가

### 5.1 빠른 admission: equality와 uniform gradient가 충돌한다

예를 들어 \(B=32,\kappa=128\)에서:

| scheduler | half/first | entropy | gradient mean / worst | fairness NRMSE |
|---|---:|---:|---:|---:|
| \(\beta=0\), exact uniform | 0.30 | 1.00 | 1.1 / 1.2 | 0.65 |
| \(\beta=0.03\) | 0.70 | 0.90 | 12.4 / 22.0 | 0.20 |
| \(\beta=\infty\), least-count | 0.98 | 0.21 | 26.4 / 44.2 | 0.00 |

causal oracle는 half/first 0.98까지 가능하지만, 이를 실제로 달성하려면 늦은 trajectory
구간을 full-pool uniform보다 훨씬 많이 선택해야 한다. gradient signature가 trajectory와
연관된 smooth/regime field에서는 이것이 곧 systematic gradient bias다.

### 5.2 느린 admission: causal oracle 자체가 half cohort를 따라잡지 못한다

logical batch가 비복원일 때 한 view는 block마다 최대 한 번만 선택될 수 있다. \(T/2\)에
들어온 view는 남은 기간에 최대 약

\[
\frac{T}{2B}
\]

번만 선택될 수 있다. 동시에 pool이 \(B\)에 가깝다면 새 view를 서비스하는 동안에도
오래된 view 다수를 매 block 계속 선택해야 한다.

실제로 \(B=32\)에서 causal oracle half/first는 \(\kappa=128\)일 때 0.98이지만,
\(\kappa=256,512,768,1024\)에서 각각 0.72, 0.64, 0.55, 0.53으로 떨어졌다.
이 영역은 scheduler를 바꿔도 0.9 equality가 물리적으로 불가능하다.

### 5.3 장기 exact incompatibility

한 update를 한 단위 시간으로 보고 constant positive admission으로
\(N(t)\simeq t/\kappa\)라 하자. full-pool uniform sampling 아래, 시점 \(a\)에 들어온
view의 expected lifetime count는

\[
\mathbb E[n_a(T)]
\simeq\int_a^T\frac{dt}{N(t)}
=\kappa\log\frac{T}{a}.
\]

따라서 \(T/2\)에 들어온 view는 약 \(\kappa\log2\)를 받지만 더 오래된 view는 더 많이
받는다. exact uniform shuffle은 lifetime equality를 만들지 않는다.

반대로 terminal equality를 유지하면 최종 평균 count는

\[
\bar n(T)=\frac{T}{N(T)}\to\kappa
\]

다. \(cT\) 시점에 이미 있던 old cohort는 그때 이미 평균 \(\kappa\)가량 서비스됐다.
그런데 이후 exact uniform shuffle은 이 old cohort에

\[
\int_{cT}^{T}\frac{N(cT)}{N(t)}dt
\simeq cT\log(1/c)=\Theta(T)
\]

의 추가 서비스를 준다. terminal count를 \(\kappa+o(1)\)에 유지해야 한다는 조건과
모순이다.

즉 다음 세 exact 요구는 infinite horizon에서 동시에 성립할 수 없다.

1. constant positive admission rate
2. age와 무관한 terminal lifetime-count equality
3. 매 시점 full-pool uniform random shuffle

이번 sweep는 이 exact 충돌이 현재 finite horizon과 tolerance에서도 사라지지 않음을
보인 것이다.

## 6. Admission 결과: token은 채택 가능, gate는 부하 의존적

\(B=32\), long stream 18,000 update의 결과다.

| \(\kappa\) | token actual/target | gate uniform | gate + active bonus | gate uniform max lag |
|---:|---:|---:|---:|---:|
| 32 | 1.000 | 0.189 | 0.284 | 455.9 frames |
| 64 | 1.000 | 0.377 | 0.571 | 175.2 frames |
| 96 | 1.000 | 0.554 | 0.804 | 83.5 frames |
| 128 | 1.000 | 0.726 | 0.974 | 38.6 frames |
| 256 | 1.000 | 0.993 | 1.000 | 1.4 frames |

active bonus는 gate collapse를 constant factor로 완화하지만 제거하지 않는다. 반면 token
controller는 모든 \(\kappa\)와 horizon에서 target을 정확히 추적했다. 따라서
**admission mechanism은 gate-free GPU token으로 분리하는 것이 맞다.** 다만 \(\kappa\)의
품질상 허용값은 scheduling objective를 먼저 선택한 뒤 정해야 한다.

실제 시스템에서 candidate input rate가 \(\lambda\) frame/s이고 GPU service가
\(R\) update/s이면 모든 candidate를 받기 위한 load condition은

\[
\kappa=\frac{R}{\lambda}.
\]

해당 \(\kappa\)가 선택한 scheduling objective의 quality frontier 밖이면 GPU service를
늘리거나 candidate를 thinning해야 한다.

## 7. 다음 설계에서 먼저 선택해야 할 전제

현재 세 문장을 모두 유지한 채 새로운 \(\beta\)만 찾는 탐색은 중단해야 한다. 다음 중
하나를 명시적으로 택해야 문제가 잘 정의된다.

### A. Full-pool uniform mapping objective가 우선

- scheduler: \(\beta=0\), exact random reshuffling
- fairness: raw lifetime equality가 아니라 arrival 이후 uniform sampling 기댓값
  \(q_i(T)=\sum_{t=a_i}^T1/N_t\)에 대한 discrepancy
- 장점: uniform gradient claim과 일치
- 단점: 초기 view와 halfway view의 raw total count는 같지 않다

### B. Raw lifetime equality가 우선

- scheduler: least-count 또는 fairness-constrained maximum entropy
- objective: scheduler가 유도하는 non-uniform weighted mapping objective로 명시
- 장점: 초기와 halfway cohort의 total opportunity를 맞출 수 있는 부하에서는 강한 equality
- 단점: full-pool uniform-unbiased gradient claim을 포기해야 한다

### C. 두 목표를 근사적으로 모두 원함

- bounded archive/coreset으로 \(N\)을 제한하거나
- admission을 종료 전에 멈추고 causal catch-up 구간을 두거나
- zero-tail을 완화해 terminal catch-up을 허용해야 한다

이 중 어느 것도 허용하지 않으면 현재 문제의 feasible set은 비어 있다.

## 8. 재현 파일

- simulator: `context/research/joint_admission_scheduler_sim.py`
- 주 sweep: `context/research/joint_admission_scheduler_outputs/`
- batch sensitivity: `context/research/joint_admission_scheduler_batch_sensitivity/`
- 핵심 그림:
  - `joint_admission_scheduler_outputs/feasibility.png`
  - `joint_admission_scheduler_outputs/admission.png`
  - `joint_admission_scheduler_outputs/tradeoff.png`

주 sweep 재실행:

```bash
MPLCONFIGDIR=/tmp/gs_scheduler_v2_mpl \
conda run -n 3dgs python context/research/joint_admission_scheduler_sim.py \
  --steps 12000 --seeds 16 --batch-size 32 \
  --kappas 32,48,64,96,128,192,256,384,512,768,1024,1536,2048,3072,4096 \
  --betas 0,0.0025,0.005,0.0075,0.01,0.0125,0.015,0.02,0.03,0.05,0.075,0.1,0.15,0.2,0.3,0.5,1,inf \
  --output-dir context/research/joint_admission_scheduler_outputs
```

