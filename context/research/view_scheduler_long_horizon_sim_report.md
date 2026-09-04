# Growing-Pool View Scheduling: 장기 시뮬레이션과 실제 final-v7 A/B

> 목적: exp69 v7의 maturity gate를 없애더라도, 시간이 지날수록 커지는 causal view pool에서
> (1) 누적 gradient가 uniform full-pool objective에서 크게 벗어나지 않고,
> (2) 모든 view가 자신이 pool에 존재한 시간에 비례하여 공정한 학습 기회를 받는
> scheduler를 찾는다.
>
> 현재 결론: 합성 실험에서는 **ME-QARR((C=1))**가 가장 강한 장기 공정성을,
> **ME-BDS((C=2))**가 공정성과 짧은 구간 mixing의 가장 좋은 절충을 보였다. 후속
> exp72는 이 두 알고리즘 자체가 아니라 count-Gibbs 분포를 사용하는 ERCB를 실제
> final-v7에 이식했다. (K=128,\beta=0.02)는 두 trajectory에서 품질과 실행시간을
> 보존했지만, 일반적인 lifetime 균등화와 pool-independent admission에는 실패했다.
> 따라서 ERCB는 opt-in engineering candidate로만 유지하고, 논문 방법론이나 production
> default로 승격하지 않는다.

## 0. 먼저 전달할 결론

- 단순히 최종 update 횟수를 같게 만드는 것은 잘못된 공정성이다. 일찍 도착한 view는 오래
  pool에 있었으므로 늦게 도착한 view보다 더 많이 선택되는 것이 정상이다.
- view (i)의 올바른 목표 update 횟수는, 자신이 도착한 뒤 매 step의 uniform probability를
  누적한

  \[
  q_i(T)=\sum_{t=a_i}^{T}\frac{1}{N_t}
  \]

  이다. 여기서 (a_i)는 도착 시점, (N_t)는 시점 (t)의 pool 크기다.
- ME-QARR/ME-BDS는 실제 횟수 (n_i(T))와 quota (q_i(T))의 차이를 직접 관리하므로
  이론적으로는 “모든 view를 두 번 본 뒤에야 새 view를 받는다”는 global maturity gate가
  필요 없다. 다만 이 gate-free 구성을 실제 VIGS-SLAM에 이식한 A/B는 아직 없다.
- **ME-QARR**는 임의로 성장하는 pool에서도 모든 시점에

  \[
  \max_i |n_i(t)-q_i(t)| < 1
  \]

  을 보장한다. 고정 pool에서는 매 epoch가 (N!)개의 순열에 정확히 균등한 **uniform random
  reshuffling**이 된다.
- **ME-BDS((C))**는 공정성 오차를 (C)회 이내로 허용하는 대신, 그 제약을 지키는 모든
  다음 선택 중 균등 추출한다. 따라서 주어진 공정성 상한 아래에서 one-step conditional
  Shannon entropy가 최대다.
- 12,000 update, 48 random seeds, 5가지 성장 패턴에서 ME-QARR가 전체 평균 순위 1위였다.
  ME-BDS((C=2))는 view별 최악 오차를 2회 미만으로 제한하면서 256-step gradient mixing을
  IID uniform 수준으로 회복하여 두 목표의 Pareto knee였다.
- exp72 실제 A/B의 ERCB는 statistical block 안에서

  \[
  p(i\mid\mathcal R)\propto\exp(-\beta n_i)
  \]

  로 비복원 추출한다. 최선 설정 (K=128,\beta=0.02)는 aria1253에서 −0.084dB,
  aria1253rot에서 +0.362dB였고 online wall-time 차이는 0.04% 미만, conditional entropy는
  uniform maximum의 99.84% 이상이었다.
- 그러나 rot의 middle/first lifetime count 비율은 0.758에서 0.520으로 악화했고 기존
  maturity gate도 유지됐다. 즉 **품질 보존은 성공했지만, lifetime fairness와 admission
  문제를 해결했다는 주장은 실패**했다.

## 1. 무엇을 공정하다고 볼 것인가

### 1.1 Causal uniform target

Optimizer update를 (t=1,\ldots,T), 그때까지 도착한 view 집합을
\(\mathcal V_t\), 크기를 \(N_t=|\mathcal V_t|\)라 하자. 한 번의 update에서 하나의
view (I_t\in\mathcal V_t)를 선택한다. view (i)의 실제 누적 선택 횟수는

\[
n_i(T)=\sum_{t=1}^{T}\mathbf 1[I_t=i]
\]

이다. 매 시점 현재 pool에서 uniform sampling을 했을 때 view (i)가 받아야 할 누적
기댓값은

\[
q_i(T)
=\sum_{t=1}^{T}\frac{\mathbf 1[i\in\mathcal V_t]}{N_t}
=\sum_{t=a_i}^{T}\frac{1}{N_t}
\]

이다. 따라서 age-adjusted exposure discrepancy를

\[
e_i(T)=n_i(T)-q_i(T)
\]

로 정의한다. 늦게 도착한 view를 오래된 view와 같은 raw count까지 억지로 끌어올리는
`least-count` 방식은 과거에 존재하지 않았던 기간의 quota까지 소급해서 주는 셈이다.

### 1.2 Gradient target

현재 pool의 uniform mapping objective와 gradient를

\[
L_t(\theta)=\frac{1}{N_t}\sum_{i\in\mathcal V_t}\ell_i(\theta),
\qquad
\mu_t=\nabla_\theta L_t
=\frac{1}{N_t}\sum_{i\in\mathcal V_t}g_{i,t}
\]

로 둔다. Scheduler가 만든 gradient stream의 누적 오차는

\[
\Delta_T
=\frac{1}{T}\sum_{t=1}^{T}\left(g_{I_t,t}-\mu_t\right)
\]

이다. 시뮬레이션은 \(\|\Delta_T\|\)뿐 아니라 256-step window별 오차도 측정한다.

view별 gradient signature가 시간에 따라 고정되어 \(g_{i,t}=g_i\)인 통제 조건에서는
다음 항등식이 정확히 성립한다.

\[
\Delta_T
=\frac{1}{T}\sum_i\bigl(n_i(T)-q_i(T)\bigr)g_i
=\frac{1}{T}\sum_i e_i(T)g_i.
\]

즉 exposure discrepancy를 제한하면 누적 gradient discrepancy도 직접 제한된다. 다만 실제
3DGS에서는 \(g_{i,t}\)가 \(\theta_t\)와 topology에 따라 변하므로, 이 항등식만으로 실제
수렴이나 PSNR을 보장한다고 주장하면 안 된다. 이번 시뮬레이션은 시간 변조 gradient를 별도로
넣어 이 한계를 stress-test했다. exp72가 count-Gibbs family의 실제 품질 보존 가능성은
확인했지만 ME-QARR/ME-BDS의 실제 수렴을 검증한 것은 아니므로, 두 제안 알고리즘의 직접
시스템 A/B는 여전히 필요하다.

## 2. 제안 알고리즘

### 2.1 Fair clock와 service tag

전역 fair clock을

\[
H_t=\sum_{s=1}^{t}\frac{1}{N_s}
\]

로 둔다. view (i)가 도착할 때 그 직전 clock을 baseline으로 저장한다.

\[
b_i=H_{a_i-1}.
\]

그러면 quota와 service tag는

\[
q_i(t)=H_t-b_i,
\qquad
f_i(t)=b_i+n_i(t)
\]

이고, discrepancy는

\[
e_i(t)=n_i(t)-q_i(t)=f_i(t)-H_t
\]

가 된다. 모든 view의 공통항 (H_t)를 빼면 되므로, 가장 quota가 부족한 view를 찾는 것은
가장 작은 service tag (f_i)를 찾는 것과 같다.

### 2.2 ME-QARR: exact random reshuffling + sub-one discrepancy

ME-QARR(Maximum-Entropy Quota-Aware Random Reshuffling)는

\[
\mathcal M_t=\arg\min_{i\in\mathcal V_t} f_i(t-1),
\qquad
I_t\sim\operatorname{Uniform}(\mathcal M_t)
\]

로 선택한 뒤 (n_{I_t}\leftarrow n_{I_t}+1)로 갱신한다.

```text
on_arrival(i):
    b[i] <- H
    n[i] <- 0
    push(heap, key=b[i], random_tie_key)

on_optimizer_step():
    H <- H + 1 / current_pool_size
    i <- uniform random argmin of (b[j] + n[j])
    n[i] <- n[i] + 1
    update heap key of i by +1
    return i
```

Heap의 동일 tag에 독립 continuous random key를 부여하고 최솟값을 뽑으면 exact uniform
tie-breaking을 (O(\log N_t))에 구현할 수 있다. 메모리는 (O(N_t))다.

#### 보장 1: 임의의 growing pool에서 discrepancy가 1 미만이다

현재 service tag의 span을

\[
S_t=\max_i f_i(t)-\min_i f_i(t)
\]

라 하자.

1. 초기에는 모든 tag가 같으므로 (S_0=0)이다.
2. 새 view의 tag는 (b_i=H_{t-1})이다. \(\sum_i e_i=0\)이므로 (H_{t-1})는 기존
   tag들의 평균이고, 따라서 기존 최솟값과 최댓값 사이에 들어온다. Arrival은 span을
   증가시키지 않는다.
3. ME-QARR는 최솟값을 가진 tag 하나만 1 증가시킨다. (S_{t-1}\le1)이면 갱신 뒤에도
   (S_t\le1)이다.
4. (H_t)는 갱신된 tag들의 평균이므로

   \[
   |e_i(t)|=|f_i(t)-H_t|\le S_t\le1.
   \]

유한한 두 개 이상의 view에서는 평균이 양 끝점 사이에 있으므로 실제 절댓값은 1보다
작다. 이 보장은 pool 크기나 stream 길이에 의존하지 않는다.

#### 보장 2: 고정 pool에서는 exact uniform random reshuffling이다

고정 pool에서는 모든 (b_i)가 같다. 따라서 한 번 뽑힌 view의 tag만 1 커지고, 나머지
view가 모두 한 번씩 뽑힐 때까지 다시 뽑힐 수 없다. 각 위치에서 아직 뽑히지 않은 view
중 균등 선택하므로 임의의 순열 \(\pi\)가 나올 확률은

\[
\Pr(\pi)
=\frac1N\frac1{N-1}\cdots\frac11
=\frac1{N!}.
\]

따라서 “random shuffle과 유사하다”가 아니라 **각 epoch가 모든 순열에 정확히 균등하다**고
말할 수 있다.

#### 보장 3: 강한 공정성 제약 아래에서 가장 random하다

다음 선택 후에도 (S_t\le1)을 지킬 수 있는 view는 현재 최소 tag 집합
\(\mathcal M_t\)뿐이다. 그보다 큰 tag를 선택하면 최소 tag가 남은 상태에서 선택된 tag만
1 증가하므로 span이 1을 초과한다. 이 feasible support 위의 Shannon entropy

\[
\mathcal H(p)=-\sum_{i\in\mathcal M_t}p_i\log p_i
\]

는 (p_i=1/|\mathcal M_t|)일 때 최대다. 그러므로 ME-QARR는 **sub-one deterministic
fairness를 유지하는 모든 다음 행동 중 one-step conditional entropy를 최대화한다.**

논문에서는 다음처럼 범위를 정확히 한정해야 한다.

> ME-QARR recovers exact uniform random reshuffling for a static view set and,
> under online arrivals, maximizes the one-step conditional entropy over all
> selections that preserve the sub-one cumulative exposure discrepancy.

“모든 가능한 온라인 scheduler 중 전역 entropy가 최대”라고 쓰는 것은 현재 증명보다 강한
주장이므로 피한다.

### 2.3 ME-BDS(​(C)): maximum-entropy 완화형

Burst arrival 직후에는 (C=1) 제약이 과거의 작은 deficit부터 정확히 갚게 만들므로,
짧은 window에서 새 cohort와 과거 cohort가 덜 섞일 수 있다. 이를 위해 허용 가능한 tag
span을 (C\ge1)로 일반화한다.

\[
\mathcal F_t(C)
=\left\{
i\in\mathcal V_t:
\operatorname{span}\left(\mathbf f(t-1)+\mathbf 1_i\right)\le C
\right\},
\]

\[
I_t\sim\operatorname{Uniform}\bigl(\mathcal F_t(C)\bigr).
\]

- Uniform distribution은 유한 feasible set에서 Shannon entropy를 최대화한다.
- 매 step 갱신 뒤에도 \(\operatorname{span}(\mathbf f)\le C\)다.
- (H_t)가 tag의 평균이므로 모든 시점에 \(|n_i-q_i|\le C\)다.
- (C=1)은 ME-QARR와 같다.
- (C\to\infty)이면 IID uniform sampling에 가까워진다.

즉 (C)는 “randomness를 얼마나 넣을지”를 설명하기 어려운 temperature가 아니라,
**한 view가 uniform quota로부터 최대 몇 update까지 벗어날 수 있는가**라는 직접 해석 가능한
단위다.

## 3. 비교 대상과 시뮬레이션 설정

### 3.1 비교한 scheduler

- `uniform_iid`: 매 step 현재 pool에서 복원 uniform sampling. 조건부 gradient는
  unbiased지만 finite-run exposure 편차가 누적된다.
- `production_causal_shuffle`: 현재 VIGS-SLAM `CausalShuffleQueue` 동작을 모사했다.
  새 view를 진행 중인 epoch의 임의 위치에 삽입하고, pool 내부는 비복원 shuffle한다.
- `active_archive_D0`: exp69 active/archive 구조에서 demand bonus만 0으로 둔 대조군이다.
- `exp69_active_archive_D1/D2`: 최신 active 16개 view에 각각 (1+D\)의 odds multiplier를
  주었다. 실제 코드가 허용하는 중간값과 최댓값 stress case다.
- `raw_least_count`: arrival age를 무시하고 raw count가 가장 작은 view를 고른다.
- `ME-QARR`, `ME-BDS(C=2,3,4)`.

### 3.2 Stream과 gradient

- optimizer update: 각 run 12,000회
- scheduler random seed: 48개
- 성장 패턴 5개:

| 패턴 | 최종 view 수 | 의미 |
|---|---:|---|
| static | 256 | 고정 pool |
| steady growth | 1,031 | 일정한 view arrival |
| bursty growth | 704 | 큰 cohort가 간헐적으로 도착 |
| accelerating growth | 1,299 | 후반으로 갈수록 arrival이 빨라짐 |
| near saturation | 6,031 | 2 update마다 1 view 도착하는 용량 한계 |

- view gradient: 8차원 synthetic signature
- gradient field 4개: IID stationary, trajectory 순서에 따라 부드럽게 변하는 field,
  그 field의 시간 변조, trajectory 중간에서 방향이 바뀌는 regime-shift 시간 변조
- short-window mixing: 256 update 단위
- 총 rank case: fairness 10개(5 pattern × 2 metric) + gradient 40개
  (5 pattern × 4 field × 2 metric) = 50개

## 4. 결과

아래 수치는 5개 성장 패턴 전체 평균이다. Gradient 수치는 view signature RMS로 정규화한
백분율이다. `worst max |error|`만 5 pattern × 48 seed의 최악값이다.

| Scheduler | quota RMSE ↓ | worst max \(|n-q|\) ↓ | final gradient bias ↓ | final gradient RMSE ↓ | 256-step mixing RMSE ↓ |
|---|---:|---:|---:|---:|---:|
| IID uniform | 3.764 | 31.333 | **0.094%** | 0.771% | **5.144%** |
| production causal shuffle | 0.609 | 3.509 | 3.153% | 3.174% | 9.239% |
| exp69 active/archive, (D=1) | 3.473 | 46.125 | 4.806% | 4.841% | 11.314% |
| raw least-count | 7.427 | 43.667 | 30.496% | 30.505% | 58.168% |
| **ME-QARR, (C=1)** | **0.306** | **0.875** | 0.313% | **0.324%** | 5.831% |
| **ME-BDS, (C=2)** | 0.392 | 1.875 | 0.187% | 0.330% | 5.300% |
| ME-BDS, (C=3) | 0.512 | 2.875 | 0.088% | 0.333% | 5.321% |
| ME-BDS, (C=4) | 0.644 | 3.875 | 0.219% | 0.433% | 5.233% |

핵심 해석은 다음과 같다.

- **ME-QARR는 공정성에서 가장 강하고, 최종 gradient RMSE도 가장 낮다.** 50개 평가 항목의
  평균 rank 2.56으로 전체 1위였다.
- **ME-BDS((C=2))는 short-window mixing까지 포함한 가장 좋은 절충점이다.** IID uniform의
  256-step mixing RMSE 5.144%와 거의 같은 5.300%이면서, quota RMSE는 3.764에서
  0.392로 약 9.6배 작고, 최악의 per-view 오차는 31.333회가 아니라 1.875회였다.
- ME-QARR와 (C=2)의 final gradient RMSE는 0.324%와 0.330%로 사실상 같다. 차이는
  burst 직후의 짧은 window에서 발생한다.
- `production_causal_shuffle`는 고정 pool에서는 잘 작동하지만 membership churn이 빠르면
  새 arrival을 unfinished epoch에서 반드시 한 번 서비스하는 동작이 age-adjusted quota를
  초과시킨다. Near-saturation의 adversarial gradient에서 최악 bias는 16.41%였다.
- exp69의 (D>0) active bonus는 uniform full-pool objective를 목표로 삼는 한 의도적인
  sampling bias다. Active/archive가 메모리 보존에는 도움을 주어도 uniform exposure를
  보장하지는 않는다.
- `raw_least_count`가 near-saturation에서 거의 모든 view를 두 번 보는 것처럼 보이는 것은
  장점이 아니다. 늦게 들어온 view에 과거 quota를 소급 지급하느라 오래된 view의 정당한
  exposure를 빼앗았고, 전체 gradient bias가 30.50%까지 커졌다.

전체 rank는 다음과 같다.

| 순위 | Scheduler | 50-case 평균 rank ↓ |
|---:|---|---:|
| 1 | ME-QARR | 2.56 |
| 2 | ME-BDS((C=2)) | 2.96 |
| 3 | ME-BDS((C=3)) | 3.84 |
| 4 | ME-BDS((C=4)) | 4.52 |
| 5 | production causal shuffle | 4.74 |

![전체 trade-off](view_scheduler_long_horizon_outputs/tradeoff.png)

![시간에 따른 exposure discrepancy](view_scheduler_long_horizon_outputs/representative_deficit.png)

## 5. 실제 final-v7 검증: exp72 ERCB statistical block

### 5.1 구현한 분포

exp72는 ME-QARR/ME-BDS와 구분되는 entropy-regularized count balancing(ERCB) 구현이다.
Statistical block (b)가 시작되는 시점을 (\tau_b), 그때의 eligible pool을
\(\mathcal R_b^{(0)}=\mathcal V_{\tau_b}\)라 하자. Block 안의 (k)번째 draw는

\[
p_{b,k}(i)
=\Pr(I_{b,k}=i\mid\mathcal R_b^{(k)})
=\frac{\exp(-\beta n_i)}
{\sum_{j\in\mathcal R_b^{(k)}}\exp(-\beta n_j)},
\qquad i\in\mathcal R_b^{(k)},
\]

\[
\mathcal R_b^{(k+1)}=\mathcal R_b^{(k)}\setminus\{I_{b,k}\}
\]

로 정의한다. (K)개를 뽑거나 remaining set이 빌 때 block을 끝내고, 다음 block에서 현재
pool로 remaining set을 다시 만든다. 실제 optimizer는 B1이므로 queue에서 한 view씩
소비한다. (K=1)은 매 update의 full-support categorical draw이고,
(K\ge |\mathcal V|)는 weighted full-pool permutation이다.

첫 구현처럼 remaining set을 full-pool epoch가 끝날 때까지 유지하면 모든 view가 결국
한 번씩 뽑히므로 (\beta)는 lifetime exposure가 아니라 epoch 내부 순서만 바꾼다. 최종
exp72 구현은 이 오류를 수정해 remaining set을 statistical block마다 초기화한다.

### 5.2 실제 A/B 결과

모든 arm은 final-v7 RTX 5090 original-timestamp 1× profile, mapping loss, optimizer,
PGBA, Gaussian budget, terminal dust-GC와 EOS rematuration을 동일하게 유지했다. Scheduler만
opt-in으로 교체했고 기본값 (\beta=-1)은 기존 final-v7 queue를 그대로 사용한다.

| Scene | final-v7 baseline | (K=128,\beta=0.02) | ΔPSNR | wall-time 변화 | entropy ratio |
|---|---:|---:|---:|---:|---:|
| aria1253 | 27.708 | 27.624 | −0.084dB | +0.033% | 0.99869 |
| aria1253rot | 24.814 | 25.177 | +0.362dB | +0.014% | 0.99842 |

품질 비열화 기준 −0.2dB를 두 trajectory 모두 통과했고, conditional entropy는 uniform
maximum의 99.84% 이상이었다. 반면 block 크기가 짧은 (K=32,\beta=0.02)는 aria1253에서
−2.082dB, B1 uniform((K=1,\beta=0))은 −2.863dB였다. 실제 3DGS에서는 높은 one-step
entropy만으로 충분하지 않고, 일정 길이의 without-replacement coverage가 품질에 중요하다는
증거다.

### 5.3 실패한 조건과 해석 범위

- aria1253의 middle/first count는 0.971이었지만 aria1253rot에서는 baseline 0.758에서
  0.520으로 악화했다. 따라서 ERCB가 일반적으로 raw lifetime count를 균등화한다는 주장은
  기각한다.
- 최종 admitted pool도 aria1253 422.5→333, rot 353→334로 바뀌었다. 기존
  `minimum count >= 2` maturity gate가 그대로 남아 scheduler의 선택 순서가 gate 개방과
  admission 수에 영향을 주었기 때문이다. 이 실험은 pool-size-independent admission을
  달성하거나, 동일 membership에서 순수 ordering 효과만 분리한 실험이 아니다.
- 이 결과는 ME-QARR/ME-BDS의 실증이 아니다. 다만 높은 entropy와 긴 비복원 block을
  결합한 replay law가 실제 final-v7 품질·시간을 보존할 수 있다는 engineering feasibility를
  보여준다.
- 구현은 `block128_beta002` arm으로만 유지하며 production default는 바꾸지 않는다.

구현 단위 test와 기존 scheduler 회귀를 합쳐 60 tests, 두 trajectory sweep을 포함한 12개
full-run audit를 통과했다. 상세 수치와 machine-readable 근거는
[exp72 카드](../experiments/exp72/exp72_entropy_count_scheduler_real_ablation.md)에 기록한다.

## 6. “모든 view를 두 번 학습”은 scheduler만으로 보장할 수 없다

시점 (T)까지 들어온 view가 (M(T))개이고 optimizer service가 총 (S(T))회라면, 모든
view를 최소 (r)회 학습시키기 위한 필요조건은

\[
rM(T)\le S(T)
\]

이다. Near-saturation 시뮬레이션은 12,000 update 동안 6,031개 view가 도착했다. 모든
view를 두 번 보려면 12,062 update가 필요하므로 어떤 scheduler도 이를 만족할 수 없다.
ME-QARR에서 전체 view의 47.7%만 두 번 이상 선택된 것은 starvation이 아니라, 늦게 도착해
아직 quota가 2에 도달하지 않은 view가 많기 때문이다. 반면 (q_i\ge2)인 view가 두 번보다
적게 선택된 비율은 모든 seed에서 0이었다.

arrival이 optimizer update (K)회당 한 view인 장기 선형 성장
\(N_t\simeq t/K\)이라면, 고정된 view (i)의 quota는 대략

\[
q_i(T)
\simeq K\int_{a_i}^{T}\frac{dt}{t}
=K\log\frac{T}{a_i}.
\]

따라서 각 고정 view의 기회는 장기적으로 무한히 늘지만 증가 속도는 로그다. Pool이 계속
커질 때 epoch가 느려지는 현상은 scheduler 버그만이 아니라 유한 compute의 구조적 한계다.
이를 더 빠르게 만들려면 다음 셋 중 하나가 반드시 필요하다.

- optimizer service rate를 늘린다.
- admission rate를 낮추되 어떤 view를 제외했는지 명시한다.
- archive를 유한하게 만들어 uniform objective 자체를 바꾼다.

ME-QARR/ME-BDS가 해결하는 것은 “없는 compute 만들기”가 아니라, 주어진 service를
pre-arrival debt나 active bonus 없이 causal uniform quota에 가장 가깝게 배분하는 일이다.

## 7. 논문에 넣을 주장과 넣으면 안 되는 주장

### 안전하게 주장 가능한 문장

- **Static pool:** exact uniform random reshuffling over all (N!) permutations.
- **Growing pool, (C=1):** deterministic sub-one age-adjusted exposure discrepancy.
- **Growing pool, general (C):** maximum one-step conditional entropy among all next
  selections that preserve the tag-span bound (C).
- **Simulation:** lower final gradient discrepancy and substantially tighter exposure balance
  than IID sampling, production causal shuffle, raw least-count, and active/archive priority
  under the tested synthetic streams.
- **Real final-v7 A/B:** ERCB with (K=128,\beta=0.02) stayed within −0.084dB on aria1253,
  improved aria1253rot by +0.362dB, retained at least 99.84% of uniform conditional entropy,
  and changed online wall time by less than 0.04% under the tested configuration.

### 아직 주장하면 안 되는 문장

- 모든 online schedule을 통틀어 trajectory-level entropy가 전역 최대라는 주장
- 실제 non-convex 3DGS gradient가 unbiased라는 무조건적 주장
- exp72 ERCB 결과가 ME-QARR/ME-BDS의 실제 성능을 검증했다는 주장
- (K=128,\beta=0.02)가 장면 일반적인 lifetime equality를 보장한다는 주장
- 기존 maturity gate를 둔 exp72가 pool-independent admission을 달성했다는 주장
- 두 trajectory 결과만으로 PSNR, geometry 또는 floater가 일반적으로 좋아진다는 주장
- unbounded pool인데 모든 새 view가 고정 시간 안에 두 번 학습된다는 주장

## 8. 현재 추천

합성 결과와 exp72 실제 A/B를 함께 보면 현재 권고는 다음과 같다.

1. **이론적 주 후보:** ME-BDS((C=2)). 합성 실험에서 gradient mixing과 age-adjusted
   fairness의 Pareto knee였지만, 아직 실제 VIGS-SLAM 채택법으로 쓰지 않는다.
2. **정리와 특수형:** ME-QARR((C=1)). sub-one discrepancy와 static exact random
   reshuffling을 설명하는 가장 깔끔한 형태이며, 이 역시 실제 A/B 전이다.
3. **실제 구현 후보:** ERCB (K=128,\beta=0.02)는 품질·시간 보존 scheduler ablation으로
   opt-in 유지한다. lifetime fairness나 admission을 해결하는 논문 contribution으로는 쓰지
   않는다.
4. **다음 핵심 실험:** scheduler보다 admission controller를 먼저 분리한다. GPU service
   token으로 admission을 결정하고 동일 admitted set·동일 optimizer update·동일 Gaussian
   budget을 고정한 뒤 final-v7 / ME-QARR / ME-BDS((C=2)) / ERCB를 비교해야 ordering의
   순수 효과를 판별할 수 있다.
5. **Fairness 정의:** raw lifetime equality와 age-adjusted quota를 혼용하지 않는다. 본
   문서의 이론적 target은 후자이며, exp72의 raw cohort ratio는 별도 진단값이다.
6. **Active/archive:** uniform mapping objective를 논문의 기준으로 삼는다면 service bonus는
   제거한다. Active set을 유지해야 한다면 그 bonus는 별도의 weighted objective로 명시하고
   uniform-unbiased claim과 분리해야 한다.

exp72로 “고엔트로피 block scheduler가 실제 시스템에서 무비용으로 동작할 수 있는가”에는
긍정적인 답을 얻었다. 그러나 “장기적으로 모든 view가 공정한가”와 “pool 증가와 무관하게
admit되는가”에는 부정적인 답을 얻었다. 따라서 다음 단계는 (\beta) sweep이 아니라 gate를
service-token admission으로 분리한 controlled A/B다.

## 9. 재현 파일

- 시뮬레이터: [`view_scheduler_long_horizon_sim.py`](view_scheduler_long_horizon_sim.py)
- 전체 per-run fairness: [`fairness_runs.csv`](view_scheduler_long_horizon_outputs/fairness_runs.csv)
- gradient case 집계: [`gradient_cases.csv`](view_scheduler_long_horizon_outputs/gradient_cases.csv)
- 전체 rank: [`aggregate_ranking.csv`](view_scheduler_long_horizon_outputs/aggregate_ranking.csv)
- machine-readable 요약: [`summary.json`](view_scheduler_long_horizon_outputs/summary.json)
- 실제 A/B 카드:
  [`exp72_entropy_count_scheduler_real_ablation.md`](../experiments/exp72/exp72_entropy_count_scheduler_real_ablation.md)
- 실제 구현·테스트·요약 데이터: VIGS-SLAM-custom의 `exp72-entropy-count-scheduler`
  브랜치 `exp72_axes/`

재실행 명령:

```bash
MPLCONFIGDIR=/tmp/vigs_scheduler_mpl \
python gs_floaterLab/context/research/view_scheduler_long_horizon_sim.py \
  --steps 12000 --seeds 48
```
