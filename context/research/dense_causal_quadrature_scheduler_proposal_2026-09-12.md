# Dense incremental supervision에서 출발한 scheduler 신규 설계

2026-09-12. 수학적 모델 및 독립적인 설계 제안. 구현·품질·overhead 검증 전이며 학술적 최초성은 주장하지 않는다.

## 1. 문제와 설계 목표

출발점은 사용자가 관측한 현상이다: 실험한 조건에서 dense incremental frame pool을 사용하면 같은 학습 예산에서 더 빠르고 높은 수렴을 보였다. 이를 모든 장면·밀도에서 성립하는 법칙으로 가정하지 않는다.

모든 causal training frame을 보존한다. 신규 관측의 service latency를 제한하고, 실제 전체 목표를 잘 감소시키는 학습 방향을 공급한다. 추가 full backward는 하지 않고 전체 mapping 시간의 1–3% 이내 overhead를 목표로 한다. 가벼운 gradient/optimizer 변경은 허용되지만 우선 sampling만 바꾸는 구성을 제안한다.

기존 ERCB는 frame별 count 부족이 현재 학습 가치로 연결된다고 기대했다. 이번 모델의 기본 단위는 독립 frame이 아니라 **시점에 따라 달라지는 gradient 함수**다. 인접 frame이 서로 영향을 주는 정도는 함수의 국소적인 연속성으로 표현한다.

## 2. Dense가 도움이 될 수 있는 이유: view 분포 근사와 update 근사를 분리

현재까지 관측한 trajectory에서 시점 x의 loss와 gradient를 ℓ(x,θ), g_θ(x)라고 하자. 관심 있는 연속 view 분포 q_*에 대한 gradient와 도착한 training pool D의 gradient는

$$
G_* = \int g_\theta(x)dq_*(x),\qquad
G_D = \sum_{i\in D}q_i g_\theta(x_i).
$$

q_*는 이론적 평가 대상이며 미래 held-out을 scheduler에 입력한다는 뜻이 아니다. 실제 scheduler의 기준은 현재 도착한 training pool의 q_i다.

한 block에서 선택한 평균 gradient를 $\hat G_S$라 하면

$$
\|\hat G_S-G_*\|
\le\underbrace{\|\hat G_S-G_D\|}_{\text{scheduler가 만드는 오차}}
+\underbrace{\|G_D-G_*\|}_{\text{관측 분포의 오차}}.
$$

Gradient가 선택한 view 거리에서 L_g-Lipschitz이면 coupling과 Jensen 부등식으로

$$
\boxed{\|G_D-G_*\|\le L_g W_1(q_D,q_*)}.
$$

같은 trajectory를 고르게 더 촘촘히 관측하여 q_D가 q_*에 가까워지면, 반복 횟수를 늘리지 않아도 학습 gradient의 분포 편향이 줄 수 있다. 균일한 1D trajectory discretization에서 간격 h가 작아지면 적절한 quadrature weight의 W_1 오차도 O(h)로 줄어든다.

그러나 frame 수 자체가 W_1 감소를 보장하지 않는다. 특정 시점의 복제, 불균일한 dwell, pose 오류, blur, occlusion 경계는 이 설명의 조건을 깨거나 L_g를 크게 만든다. Exp66의 기존 비교에는 loss·초기 상태 차이도 있었으므로 수식이 그 실험의 원인을 확정하지 않는다.

중요한 해석: dense는 전체 평균 gradient를 더 잘 대표할 수 있는 관측을 공급한다. Scheduler가 그 관측을 실제로 사용하지 않으면 입력 density만으로 이득이 생기지 않는다.

## 3. 실시간 근사를 위한 핵심 가정

짧은 optimization 구간에서 gradient 함수를

$$
\boxed{g_\theta(x)=A_\theta\phi(x)+e_\theta(x)}
$$

로 근사한다. $\phi(x)\in\mathbb R^d$는 저차원 관측 특징, A_θ는 현재 장면·지도에 따른 큰 선형 map이며 $\|A_\theta\|_{op}\le M$, $\|e_\theta(x)\|\le\epsilon$라고 가정한다.

이것은 raw pose가 Gaussian gradient를 정확히 결정한다는 주장이 아니다. Pose/low-resolution RGB/visibility 특징만으로 이 근사가 충분한지는 가장 중요한 미확인 가정이다. 대안으로 실제 학습에서 얻은 signed gradient sketch와 causal 이웃 보간을 φ로 사용한다. 이 경우 projection·staleness·보간 오류가 ε에 들어간다.

현재 pool의 특징 평균을

$$
m_t=\sum_{i\in D_t}q_i\phi_i
$$

라고 하면 B개 frame의 특징 평균 $\bar\phi_S$에 대해

$$
\boxed{\|\hat G_S-G_D\|\le M\|\bar\phi_S-m_t\|+2\epsilon}.
$$

따라서 매 후보의 full gradient를 새로 계산하지 않고, **작은 특징 벡터의 평균 오차**로 gradient 대표성을 제어할 수 있다. ε가 크면 이 방법의 근거도 약해진다. 차원을 줄이는 것만으로 정확성을 보장하지 않는다.

### 수렴과의 조건부 연결

고정 topology, L-smooth F_D, 같은 θ에서 계산한 평균 gradient로 한 번의 SGD update를 하는 경우

$$
F_D(\theta-\hat G_S/L)
\le F_D(\theta)-\frac{\|G_D\|^2}{2L}
+\frac{(M\|\bar\phi_S-m_t\|+2\epsilon)^2}{2L}.
$$

이 식은 특징 평균 오차를 줄이는 목적이 단순한 frame fairness가 아니라 수렴의 감소량 하한과 연결된다는 근거다. 실제 RR 대비 held-out 가속 보장은 아니다.

실제 B회의 sequential SGD를 이 minibatch 식과 같다고 취급하지 않는다. 국소 gradient norm≤G_max와 gradient Lipschitz 상수 L에서 frozen-gradient sum과 실제 displacement의 차이는

$$
\left\|\Delta\theta+\eta\sum_{r=1}^B g_{i_r}(\theta_0)\right\|
\le\frac{\eta^2LG_{max}B(B-1)}2
$$

로 제한할 수 있다. 따라서 작은 block/prefix 제어가 필요하다. Adam 및 topology 변경에는 이 SGD bound를 그대로 주장하지 않는다.

## 4. 주 후보 1 — 신규 관측을 포함한 평균 보상 sampling

### 핵심 구성

신규 frame을 먼저 service 대상으로 확보하고, 나머지를 무조건 uniform으로 채우는 대신 **그 신규 관측이 만든 평균 편향을 보상하는 과거 관측**으로 짧은 block을 완성한다.

이는 신규와 비슷한 frame만 고르는 것도, 가장 먼 frame을 고르는 것도 아니다. 선택 기준은 현재 전체 pool의 특징 평균이다.

B개의 service slot 중 m개의 필수 신규/ticket frame을 집합 U로 확보하면, 나머지 B-m개의 관측이 목표로 해야 할 평균은

$$
\boxed{\phi_{\mathrm{need}}=
\frac{Bm_t-\sum_{i\in U}\phi_i}{B-m}}.
$$

남은 관측을 φ_need에 가까운 평균이 되도록 고른다. 모든 frame은 저장 pool에 계속 남고, selection shortlist만 작게 유지한다.

### 왜 dense와 연결되는가

고정된 의도 시점 u_b에서 실제 이용 가능한 frame x_b까지의 거리가 h 이내이고 φ가 L_φ-Lipschitz라면

$$
\left\|\frac1B\sum_b\phi(x_b)-\frac1B\sum_b\phi(u_b)\right\|
\le L_\phi h.
$$

Dense 관측은 의도한 조합을 실제 frame으로 실현할 때의 discretization 오차를 줄일 수 있다. Sparse 관측의 단순 반복으로는 존재하지 않는 중간 시점의 제약을 만들 수 없다. 단, 의미 없이 중복된 frame이 늘어나는 경우에는 이런 이득이 없다.

### Entropy가 들어가는 정확한 위치

기한 조건을 만족하는 B-slot sequence들의 집합을 F_t, 그 안에서의 무작위 기준분포를 P_0(S)라고 하자. 이상적인 선택은

$$
P^*=\arg\min_{P:\operatorname{supp}(P)\subset F_t}
\mathbb E_{S\sim P}[E(S)] +\tau D_{KL}(P\|P_0),
$$

$$
E(S)=\sum_{k=1}^B w_k
\left\|\sum_{r=1}^k\phi_{i_r}-k m_t\right\|^2,
\quad w_k\ge0.
$$

$$
P^*(S)\propto P_0(S)\exp(-E(S)/\tau),\quad S\in F_t.
$$

Entropy는 기한을 어기면서 uniform에 머물라는 압력이 아니라, **대표성이 비슷한 유효 sequence 사이에서 무작위성을 유지하는 항**이다.

Unique frame B개를 균등 가중하는 하나의 block의 empirical ID entropy는 항상 log B이므로, 그것을 block 선택 목적에 넣으면 상수일 뿐이다. 여기서는 sequence 분포의 entropy/KL을 사용한다.

### 저비용 구현 근사

전 sequence를 탐색하지 않는다. 예시 설계점은 d=16–32, 후보 C=16–32, block B=8–16이다. 측정·최적화된 값은 아니다.

1. Due ticket을 먼저 고려하고, 자유 slot마다 archive RR 후보 몇 개를 가져온다.
2. 현재 prefix 편차 r_k에 대해 후보 j의 국소 오차 증가
   $\Delta E_j=2\langle r_k,\phi_j-m_t\rangle+\|\phi_j-m_t\|^2$를 계산한다.
3. Remaining-support 기준분포에 $\exp(-\Delta E_j/\tau)$를 곱해 무작위 선택한다.
4. 선택 후 r_k와 remaining support를 갱신한다. Due-time 위치 제약을 유지한다.
5. 다음 block에는 새 도착과 갱신된 특징을 반영한다.

이 local soft selection은 위 전역 Gibbs 분포의 정확한 sampler가 아니다. 이는 구현용 근사이며, 필요하면 작은 C에서 1-step lookahead 또는 block 후반의 제한된 swap으로 보완한다.

순수 산술 비용은 O(BCd). 특징을 새로 얻는 비용, archive 접근·GPU 동기화가 별도로 존재한다. 기존 메모리의 작은 특징만 읽는 구성을 우선한다.

### 구조적인 한계도 드러난다

φ_need가 과거 특징들의 convex hull 바깥에 있으면 nonnegative frame selection으로 완전한 평균 보상이 불가능하다. 이는 solver 문제가 아니라 latency와 정확한 전체 평균 보존 사이의 실현 가능성 문제다.

이때 전체 pool을 제외한 작은 shortlist의 hull만으로 전체 문제의 불가능성을 판정하지 않는다. Shortlist 오차와 실제 불가능성을 구별한다. New view가 고유한 신규 방향을 포함하면 남는 bias를 기록하고, 그것이 실제 품질 향상에 유리한 bias인지 평가한다.

## 5. 신규 후보 2 — 인접 관측의 학습 효과를 공유하는 service field

주 후보 1은 대표 gradient 공급에 집중한다. 별도의 탐색 후보로 직접 count를 장면의 유효 학습량으로 바꾼다.

같은 장면 제약을 공유하는 정도를 $K_{ij}\in[0,1]$, K_jj=1로 근사하고

$$
s_i(t)=\sum_{u\le t}K_{i,I_u}a_u
$$

를 유효 service로 둔다. a_u는 실제 적용된 update의 크기·신뢰도를 나타내는 양이다. 인접한 다른 frame을 학습해도 해당 frame에 credit이 전달된다.

설명용 모델 $R(s)=\sum_i q_i A_i e^{-s_i}$에서는 다음 service의 gain이

$$
R(s)-R(s+K_{:j})
=\sum_iq_i A_i e^{-s_i}(1-e^{-K_{ij}})
$$

로 나온다. Low count 자체보다 **아직 학습되지 않은 공유 제약을 얼마나 많이 개선하는지**를 기준으로 삼을 수 있다.

실시간 근사는 keyframe interval 내 작은 이웃 graph나 coarse scene-cell별 누적 service로 한다. 전체 N×N kernel은 만들지 않는다. 모든 frame의 deadline은 직접 ticket으로 유지하며 간접 credit만으로 완료 처리하지 않는다.

이 후보는 강한 가정이 있다. K를 비음수 overlap만으로 만들면 interference를 표현할 수 없다. Exponential learning curve와 동일한 credit scale도 실제 3DGS의 사실이 아니다. 따라서 signed gradient 검증을 통과하지 않은 pose/Fisher 유사도만으로 주 방법에 채택하지 않는다. Exp69의 novelty/active 방식과 비교해 다른 효과가 입증되어야 한다.

## 6. 신규 후보 3 — 신규/과거 pair의 관측 방향 보상과 update 혼합

Sampling으로 평균을 보상하기 어려운 경우, 동일 예산에서 이미 계산할 신규·과거 두 gradient를 같은 parameter에서 얻고 혼합 비중만 조정하는 후보를 둔다. 두 full backward를 추가하는 것이 아니라 원래의 두 service를 묶는다. 두 optimizer step이 하나로 바뀌는 차이는 명시한다.

첫 후보의 특징으로 보상에 유리한 pair를 고른 뒤, actual gradient와 고정 preconditioner P에서

$$
d(\alpha)=P((1-\alpha)g_O+\alpha g_N)
$$

를 구성한다. 같은 시점의 기준 방향 $\hat G$에 대해 국소 목적

$$
\max_{0\le\alpha\le1}
\eta\hat G^Td(\alpha)-\frac{L\eta^2}{2}\|d(\alpha)\|^2
$$

를 service 요구와 함께 푼다. 이는 1차원 이차식이다. 원 raw count/entropy 정책과 달리 실제 방향과 크기를 본다.

선택 proxy가 틀렸을 때도 fresh pair gradient로 보완할 가능성이 있다. 반면 gradient buffer와 O(P) memory traffic, Adam moment 처리, sparse visibility union, backward/optimizer cadence가 비용을 만든다. 단순한 식이라고 전체 모듈 비용이 작다고 볼 수 없다. 1–3% 목표는 미검증이며 후보 1보다 후순위다.

## 7. 실제 만들 때 우선순위

주 후보는 **신규 관측을 포함한 평균 보상 sampling**이다. 원래 ERCB에 coefficient만 추가하는 대신 학습 단위를 독립 frame에서 연속 관측의 gradient field로 바꾼다는 점이 핵심이다.

공통 prototype의 범위:

- Arrival별 cheap 특징 및 전체 target moment 갱신.
- Service deadline ticket 관리.
- Small candidate shortlist와 국소 평균 보상 선택.
- 전체 archive 보존, zero-tail, held-out exclusion 유지.
- 기존 update에서만 얻는 signed gradient sketch로 특징 proxy를 감사. Proxy 감사 비용도 총 비용에 포함.

성능 주장은 동일 wall-clock held-out convergence와 age-conditioned 품질에서 판단한다. Conditional gradient-model bound, feature moment 개선, 높은 entropy 자체를 품질 성공으로 기록하지 않는다.

순서상 문헌 추가 수집보다 이 신규 구성의 작은 prototype과 proxy 적합성 확인이 다음 작업이다. 특징 proxy가 Gaussian gradient를 설명하지 못하면 신규성 여부와 무관하게 이 구성을 기각하거나 paid gradient sketch 기반으로 바꾼다.

## 8. 신규성의 범위

Quadrature, moment matching, entropy regularization, local gradient approximation은 기존 수학적 도구다. 신규성을 검토할 대상은 **dense causal view field를 근사하고, 필수 신규 service를 포함한 뒤 남은 관측으로 평균 및 prefix 편차를 보상하는 실시간 매핑 모듈의 구체적인 구성**이다.

이 문서는 기존 논문 알고리즘을 그대로 옮긴 구현안이 아니다. 그러나 독립적으로 구성했다는 사실만으로 학술적 최초성이 증명되지는 않는다. 문헌 대비 신규성 검토와 3DGS 실측은 아직 남아 있다.

사용자 최종 선호: 기존 접근을 배제하지 않는다. 아래 도구에서 영감을 얻되, dense incremental 관측과 실시간 제약에 맞게 재구성한다.

| 참고할 기존 접근 | 가져올 부분 | 이번에 새로 풀어야 하는 부분 |
|---|---|---|
| [GraB](https://proceedings.neurips.cc/paper_files/paper/2022/file/3acb49252187efa352a1ae0e4b066ced-Paper-Conference.pdf) | 짧은 gradient prefix의 편차와 순서의 관계 | 전체 epoch가 아닌 causal block, 필수 신규 frame, 바뀌는 target mean |
| [GRAD-MATCH](https://proceedings.mlr.press/v139/killamsetty21a.html) | 전체 gradient를 대표하는 조합을 고르는 관점 | 매 candidate fresh backward 없는 cheap 특징과 제한된 shortlist |
| [OCS](https://arxiv.org/html/2106.01085) | 대표성·중복·과거 compatibility를 구분 | Memory 축소 없이 모든 frame 보존, 신규 sampling의 기한 조건 |
| [A-GEM](https://arxiv.org/html/1812.00420), [PCGrad](https://papers.neurips.cc/paper_files/paper/2020/file/3fe78a8acf5fda99de95303940a2420c-Paper.pdf) | 충돌을 update 차원에서 다루는 관점 | 후보 3의 같은 예산 paid pair, Adam 실제 displacement와 latency의 공동 처리 |

원형을 재사용하는 것과 원 정리를 그대로 주장하는 것은 다르다. 이 변형에 원 논문의 수렴 정리가 자동 적용되지는 않는다. 구체적인 문헌·비용 검토는 [참고 후보 조사](ercb_realtime_scheduler_candidates_2026-09-12.md)에 남겼다.
