# Growing-pool 실시간 매핑: 수렴과 service latency를 함께 다루는 후보

작성: 2026-09-12. 상태: 문헌 검토 및 방법론 제안. 구현·GPU 실험·성능 측정 결과가 아니다.

후속 사용자 steering: 기존 방법론의 직접 이식보다 dense incremental supervision 관측에서 출발하는 새로운 구성을 우선한다. 따라서 이 문서는 문헌 참고와 비용 분석으로 남긴다. 주 제안은 [dense gradient-field 기반 신규 설계](dense_causal_quadrature_scheduler_proposal_2026-09-12.md)로 이동한다.

## 1. 사용자와 합의한 범위

- 도착한 모든 training frame을 보존한다. 후보 shortlist는 저장 pool을 대체하지 않는다.
- 미래 frame/pose/geometry를 scheduler 입력으로 사용하지 않는다. Fixed held-out은 학습·선택에서 제외한다.
- 목표는 신규 관측의 반영 지연을 제한하면서 같은 wall-clock에서 held-out 품질을 빠르게 개선하는 것이다.
- 가벼운 gradient 보정 및 optimizer 변경도 후보로 허용한다.
- 추가 full backward 없이 이미 수행하는 학습의 통계를 재사용한다. 추가 mapping 비용 1–3% 이내가 설계 목표다. 현재 어느 후보도 이 수치를 실측 통과하지 않았다.
- Topology/carve/pruning을 품질 레버로 함께 변경하지 않는다. 특히 27dB 미달 지도에 carve를 추가하지 않는다.

## 2. 현재 근거와 정정

ERCB가 모든 조건에서 실패한 것은 아니다. Exp75 relative-floor는 기존 세 장면에서 overall 6/6 개선을 보였으나, 외부 transfer에서는 overall 우위를 재현하지 못했다. Count CV·entropy만으로 그 차이를 설명할 수 없다는 것이 현재 근거다. Interference, 간접 학습, topology가 각 실패의 실제 원인인지는 아직 분리되지 않았다.

관련 로컬 근거:

- [exp75](../experiments/exp75/exp75_block_weighted_rr_30k_loop.md): count-only와 loss-calibrated 분기, relative-floor 결과.
- [exp76](../experiments/exp76/exp76_mean_normalized_softmax_ablation.md): 비슷한 count CV와 높은 entropy가 최고 품질을 보장하지 않음.
- [외부 transfer](../experiments/ERCB_ablation/README.md): artificial init의 offline/noncausal 한계.
- [exp69](../experiments/exp69/exp69_result.html): pose-balanced active + unbounded archive가 12F에서 실패. 이 구조에 새 이름만 붙이지 않는다.

## 3. 공통 수학적 목적

현재 도착한 pool의 frame-uniform 목적을 F_t, gradient를 G_t라 하자. 실제 parameter displacement를 Δθ라 하면, 국소 smooth 모델에서

$$
F_t(\theta+\Delta\theta)-F_t(\theta)
\le \langle G_t,\Delta\theta\rangle+\frac L2\|\Delta\theta\|^2.
$$

따라서 다음 셋은 다른 주장이다: 높은 ID entropy, 전체 gradient 근사, 실제 목적의 빠른 감소. 이 문서의 후보들은 마지막 목표를 위한 서로 다른 근사를 제시한다. Training loss 감소는 held-out PSNR 향상의 충분조건도 아니다.

SGD에서 g_i를 선택한다면 감소량 하한의 기준은

$$
U_i=\eta\langle G_t,g_i\rangle-\frac{L\eta^2}{2}\|g_i\|^2.
$$

이 식을 전체 frame에 매번 정확하게 계산하면 실시간 조건을 위반한다. 핵심 설계 과제는 제한된 상태로 방향·변동·위험을 근사하는 것이다.

### 공통 service 장치

모든 후보에 같은 초기-service ticket/기한 장치를 붙인다. 도착 frame별 첫 k회의 직접 service 의무와 due time을 관리하고, 이미 다른 mapping 경로에서 받은 직접 service도 차감한다. 미래 도착을 미리 사용하지 않는다.

- 예상 service 확률 증가나 평균 queue 안정성만으로 hard deadline을 주장하지 않는다.
- 실제 기한 보장에는 update 처리량, burst 도착 상한, block 길이, 비선점 GPU 작업 길이를 반영한 실행 가능한 ticket 배정이 필요하다.
- 보수적인 평균 용량 조건은 kλ < μ_reserved다. 이는 충분한 최악 지연 보장이 아니다.
- Zero-tail에서는 due time이 종료 이후인 ticket을 완료했다고 주장할 수 없다. 위반·미완료를 별도 기록한다.
- Gradient가 평가됐지만 적용 전에 전부 버려진 경우를 유효한 service 완료로 세지 않는다. 적용된 service와 실제 품질 반영 시간은 따로 평가한다.

이 장치는 수렴 기법의 대체재가 아니라 공통 제약이다. 과거 모든 frame의 반복 간격까지 일정하게 제한하는 것은 고정 처리량과 무한 growing pool에서 불가능하다.

## 4. 후보 A — Service 부채와 감소량을 함께 사용하는 ERCB 확장

### 아이디어와 근거

Lifetime count 차이를 service 의무의 미완료량 Q_j로 바꾸고, 현재 전체 목적의 감소량 proxy를 함께 사용한다. Queue 안정성과 utility를 함께 최적화하는 drift-plus-penalty에서 유도 동기를 얻는다. 원 이론의 가정이 성립하는 queueing 문제에서의 결과를 3DGS 수렴 정리로 가져오지는 않는다. [Neely 강의노트](https://ee.usc.edu/stochastic-nets/docs/network-optimization-notes.pdf)

동일 비용의 한 service action을 j에 주면 Q_j가 1 감소한다. 제곱 queue potential의 감소에 Q_j 항이 등장하므로, 조건부 후보 집합 C 위에서

$$
p^*=\arg\max_{p\in\Delta(C)}
\left\{\sum_jp_j(Q_j+V\widehat U_j)-\tau D_{KL}(p\|q_C)\right\}
$$

$$
p_j^*\propto q_{C,j}\exp((Q_j+V\widehat U_j)/\tau).
$$

기존 ERCB처럼 임의의 신규 bonus를 더한 식이 아니라, 미완료 service와 품질 utility의 공동 목적에서 나오는 형태다. 다만 softmax만으로 deadline은 보장하지 않는다. Q의 스케일과 V, τ는 실제 설계 파라미터로 남는다.

### 실시간 근사

- Per-frame utility를 모두 구하지 않고 신규/과거 두 집합의 통계로 시작한다. 필요하면 소수 interval cohort로 확장한다.
- 현재 training update에서 나온 signed gradient sketch와 second-moment 통계를 집계한다.
- 전체 목표의 기준 gradient는 선택 편향을 가진 전체 EMA로 만들지 않는다. 전체 archive의 균등 추출로 수행하는 실제 학습 slot을 사용해 갱신한다. 이 slot도 기존 예산을 소비한다.
- 그 기준 역시 시간 지연이 있는 추정이다. 신규 도착과 parameter 변화가 빠르면 정확한 현재 전체 gradient가 아니다.
- 배분 비중은 block마다 갱신하고 quota로 실현한다. 내부 frame과 순서는 비복원으로 선택한다.

신규/과거 두 집합이면 확률 갱신은 scalar 문제다. 그룹 평균을 g_N,g_O, 신규의 population fraction을 ε라 하면 G=(1-ε)g_O+εg_N이고, 필요한 방향 정보는 ||g_N||², ||g_O||², <g_N,g_O>로 줄어든다. 실제 SGD utility에는 개별 gradient의 second moment도 필요하다.

### 비용과 한계

배분 자체는 O(d), d는 sketch 차원이다. 주요 비용은 sketch를 얻는 GPU 메모리 순회 및 집계다. 단순히 차원을 줄였다고 추출 비용도 작다고 주장할 수 없다.

추정 utility가 틀리면 service 부채와 함께 잘못된 frame을 우선할 수 있다. 확률을 0으로 만드는 hard top-score 정책보다 기준 RR 탐색을 남기는 것이 필요하다. Latency 제약과 전체 loss 감소가 충돌하는 상황도 있으며 두 목표의 동시 보장을 일반적으로 주장할 수 없다.

**위치:** ERCB를 가장 적게 수정하는 후보. 다만 새로운 정보인 signed gradient 관계를 실제로 추가한다.

## 5. 후보 B — Service 기한을 고려한 짧은 block의 gradient prefix balancing

### 아이디어와 근거

Count 합이 아니라 centered gradient의 prefix 합이 크게 치우치지 않도록 순서를 정한다. GraB는 stale gradient를 이용한 balancing으로 고정 finite-sum 문제에서 RR보다 나은 수렴률을 분석한다. 그 정리는 smoothness·gradient error·herding 조건을 필요로 하며 growing pool, deadline, Adam, topology 변경에는 그대로 적용되지 않는다. [GraB 원 논문](https://proceedings.neurips.cc/paper_files/paper/2022/file/3acb49252187efa352a1ae0e4b066ced-Paper-Conference.pdf)

### 우리 문제를 위한 변형 — 제안, 원 논문 알고리즘 아님

1. 전체 epoch를 기다리지 않고 짧은 block을 구성한다. Due ticket은 반드시 포함하고 나머지는 archive RR 후보로 채운다.
2. 이미 실제 학습에서 관측한 frame의 sketch를 사용한다. 신규 frame은 처음부터 정확한 gradient를 아는 것으로 취급하지 않는다. 첫 유상 service 후 얻은 sketch부터 사용한다.
3. Block 구성의 평균 방향 편향과, block 내부 순서의 prefix 편차를 분리한다.
4. Deadline을 지키는 범위 안에서 signed balancing 또는 pair balancing으로 순서를 개선한다.

고정된 block S의 cached sketch 평균을 $\bar z_S$라 하면 순서 목적은

$$
\min_\pi\max_{k\le |S|}\left\|\sum_{r=1}^k(z_{\pi(r)}-\bar z_S)\right\|.
$$

현재 전체 목표 sketch $\hat m$와 비교한 prefix 편차는

$$
\sum_{r=1}^k(z_{\pi(r)}-\hat m)
=\sum_{r=1}^k(z_{\pi(r)}-\bar z_S)+k(\bar z_S-\hat m).
$$

따라서 **순서 balancing만으로 신규 과다배분에 의한 block 평균 편향을 고칠 수는 없다.** 구성 단계에서 전체 목표와의 차이도 제어해야 한다. 고정된 작은 archive 후보 집합에서 이 편차를 줄이는 교체만 허용하는 변형을 검토할 수 있다.

Greedy 예시 점수는 누적 편차 r에 대해

$$
\Delta E_j=2\langle r,z_j-\hat m\rangle+\|z_j-\hat m\|^2.
$$

이 점수를 작게 하는 frame을 고르는 것은 직관적인 진단 baseline일 뿐, GraB의 정리를 물려받는 구현이 아니다. 원 논문도 naive greedy herding의 반례를 제시한다. 정식 후보는 balancing 기반 순서와 greedy를 구분해야 한다.

### 실시간 근사

- 예시 설계점: 16–32 candidate, 32–64차원 sketch, 8–16 update block. 이 값들은 최적값·측정값이 아니다.
- Block 후보 shortlist는 일시적이며 전체 frame archive를 삭제하지 않는다. 선택되지 않은 archive도 RR 경로에 계속 남는다.
- 큰 GPU gradient를 CPU로 복사하지 않는다. Small sketch를 block 단위로 batch 전송하거나 선택까지 GPU에서 수행한다.
- Gaussian ID를 key로 sketch한다. Row index는 prune/compact 뒤 의미가 바뀌므로 사용할 수 없다.
- 큰 topology 변경·pose 수정·optimizer scale 변화 시 오래된 sketch를 무효화하거나 confidence를 낮춘다.

원본 GraB-sampler의 별도 LeNet 벤치마크도 단순 변형에서 8.7–22% 시간 overhead를 보고한다. 우리 비용 목표를 충족하는 근거가 아니며 full-vector 구현의 직접 이식은 우선 제외한다. [GraB-sampler](https://arxiv.org/html/2309.16809)

**위치:** 순서와 수렴의 연결이 가장 직접적인 후보. 단, stale/sketched/deadline-constrained 변형의 효력은 새 검증이 필요하다.

## 6. 후보 C — 신규 update가 해칠 관측을 찾는 근사 MIR replay

### 아이디어와 근거

신규를 제때 학습시키되, 그 update가 손상할 과거 view를 찾아 보완한다. MIR은 가상 신규 update 이후 loss가 증가할 replay sample을 선택한다. 원 구현의 virtual update와 candidate loss 재평가는 우리의 실시간 제약에 부적합하다. [MIR](https://papers.nips.cc/paper_files/paper/2019/file/15825aee15eb335cc13f9b559f166ee8-Paper.pdf)

### 우리 문제를 위한 근사

신규 update가 $\Delta\theta_N$일 때 과거 i의 loss 증가는 1차로

$$
\Delta\ell_i\approx\langle g_i,\Delta\theta_N\rangle.
$$

SGD라면 interference 점수는 $[-\eta\langle g_i,g_N\rangle]_+$다. Signed cached sketch를 사용해 작은 candidate 집합에서 이 값을 근사한다.

- 신규 gradient는 실제로 수행한 학습에서 얻는다. 추가 speculative backward는 하지 않는다.
- 과거 candidate는 causal pose/visibility overlap으로 일부 좁히되 global RR 후보도 포함한다.
- Overlap은 계산을 줄이는 후보 필터다. Positive transfer나 conflict의 부호를 증명하는 신호가 아니다.
- Cached gradient로 고른 과거 frame을 실제 replay하고 그 sketch를 갱신한다.
- 모든 replay를 conflict 복구로 채우지 않고 global coverage를 유지한다.

### 기대와 위험

실제로 신규 update가 일부 공유 Gaussian에만 손상을 만든다면 전체 과거 replay보다 적은 비용으로 그 손상을 줄일 수 있다. 반대로 가장 충돌하는 관측만 번갈아 학습하면 oscillation을 키울 수 있다. 보호할 gradient와 함께 학습하면 좋은 gradient는 같은 개념이 아니다.

과거의 pose-balanced active/archive 방식과 달리 선택 근거가 signed loss-increase proxy다. 그러나 signed sketch를 제거하고 overlap만 쓰면 이미 실패한 novelty/active 계열과 실질적으로 가까워진다.

**위치:** 구체적인 interference가 있을 때 가치가 큰 후보. 범용 첫 선택보다는 A/B의 경쟁 후보로 둔다.

## 7. 후보 D — 신규·과거 두 gradient의 저차원 혼합 보정

### 아이디어와 근거

신규를 일정 시간 안에 실제 학습시키고, 과거와 충돌하는 update 성분을 직접 조정한다. A-GEM은 평균 memory gradient에 대한 제약을, PCGrad는 task gradient 간 충돌 성분의 projection을 사용한다. 이들을 3DGS에 그대로 적용하는 대신 두 view/group만 사용하는 변형을 검토한다. [A-GEM](https://arxiv.org/html/1812.00420), [PCGrad](https://papers.neurips.cc/paper_files/paper/2020/file/3fe78a8acf5fda99de95303940a2420c-Paper.pdf)

### 정확히 설명할 수 있는 국소 모델

같은 parameter에서 계산한 신규·과거 gradient와 고정 SPD preconditioner P를 사용해

$$
d(\alpha)=P((1-\alpha)g_O+\alpha g_N),\qquad\Delta\theta=-\eta d(\alpha).
$$

두 집합의 1차 비악화 조건은

$$
g_O^Td(\alpha)\ge0,\qquad g_N^Td(\alpha)\ge0.
$$

$a=g_O^TPg_O,b=g_N^TPg_N,c=g_O^TPg_N$라 하고 c<0이면

$$
\frac{-c}{b-c}\le\alpha\le\frac{a}{a-c}.
$$

즉 세 scalar reduction으로 안전한 혼합 비중의 구간을 계산할 수 있다. 이 안에서 service 요구 비중에 가까운 α를 고르는 것이 한 후보다. c≥0이면 두 gradient의 모든 convex mixture가 1차 비악화 조건을 만족한다. 완전 반대 방향이면 구간이 한 점으로 수축하고 update가 0이 될 수 있다.

이 보장은 sampled 두 loss의 1차 조건이다. 전체 pool·held-out·유한 step·다음 update까지의 보장이 아니다. 이를 빠른 수렴 보장이라고 쓰면 안 된다.

### 연산 계약

- 기존 예산에서 실행할 두 view backward를 하나의 pair로 묶어 재사용한다. 선택을 위한 추가 full backward를 붙이지 않는다.
- 두 gradient를 같은 parameter에서 얻으려면 그 사이 optimizer step을 보류한다. 따라서 두 sequential Adam step과 동일한 연산 의미가 아니다.
- 두 backward 후 한 optimizer 적용이므로 backward 수와 optimizer update 수를 따로 기록하고 wall-clock으로 비교한다.
- 두 computation graph를 동시에 보관할 필요는 없지만 첫 gradient를 저장할 추가 공간은 필요하다. Full-vector 메모리 순회 비용도 생긴다.
- Sparse Adam의 visibility mask를 pair의 union으로 처리할지, moment state를 어떻게 갱신할지 명시해야 한다.

### Adam 주의

Raw-gradient Euclidean projection 뒤 기존 Adam을 호출하면 위의 실제 displacement 제약이 깨질 수 있다. 고정 preconditioner와 momentum을 포함한 affine displacement에서 조건을 풀거나 실제 step을 제약해야 한다. P와 moment를 어떻게 유지할지 결정하기 전에는 drop-in 모듈이라고 부르지 않는다.

XYZ/opacity 등 일부 parameter group만 보정하면 비용을 낮출 수 있지만 그 공간에서의 보호일 뿐 전체 gradient 보장이 아니다. 세 scalar를 구하는 산술은 작아도 그 산술을 위한 O(P) 읽기·버퍼 비용은 작지 않을 수 있다.

**위치:** 사용자가 optimizer 변경을 허용했으므로 유효한 후보. Sketch staleness를 피할 수 있는 장점과 update cadence 변경이라는 큰 tradeoff가 있다. 메모리·시간 확인 전 1순위 이식으로 정하지 않는다.

## 8. 공통 근사 인프라와 오차

### 관측 가능한 신호

로컬 `.codex-work/3dgs-custom-main/train.py`에는 RGB backward 직후 signed xyz gradient 접근과 densification 통계 경로가 있다. `scene/gaussian_model.py::add_densification_stats`의 screen-space gradient norm은 방향을 소거한 통계다. 이를 cross-view Gaussian gradient 내적의 대용으로 사용하면 안 된다. 이 확인은 로컬 offline checkout에 한정하며 strict VIGS backend의 같은 기능을 확인한 것은 아니다.

Sketch 예시는 $z_i=S P_t^{1/2}g_i$다. Frozen diagonal P의 metric에서 signed 관계를 근사하려는 정의다. 다음 위험을 다뤄야 한다.

- Gradient field가 millions of coordinates이면 projection을 만드는 비용이 후보 scoring보다 지배적일 수 있다.
- Parameter group마다 learning-rate/scale이 다르다. XYZ만의 내적을 전체 Adam 방향이라고 부르지 않는다.
- Dense Gaussian이 보이지 않는 frame에서도 temporal adjacency만으로 gradient를 보간하지 않는다.
- Gaussian birth에는 새 stable ID, pruning에는 tombstone/epoch invalidation이 필요하다. Cached aggregate만으로 삭제 좌표를 정확히 제거할 수 없을 수 있다.
- Random projection의 고정 벡터 norm 보존 결과만으로 adaptive selection된 모든 미래 gradient의 정확성을 보장하지 않는다.
- Small candidate bank는 전체 gradient에 대한 정확한 추정이 아니다. Full archive의 실제 균등 학습 slot을 통해 기준을 갱신하고, 그 slot의 예산도 포함한다.

정확한 fresh vector x_i에 대한 cached proxy가 $\hat x_i$이고 $\|x_i-\hat x_i\|\le e_i$, 기준 mean 오차가 $\|m-\hat m\|\le e_m$라면, 고정된 prefix에 대해

$$
\left\|\sum_{r=1}^k(x_{\pi(r)}-m)\right\|
\le
\left\|\sum_{r=1}^k(\hat x_{\pi(r)}-\hat m)\right\|
+\sum_{r=1}^k e_{\pi(r)}+k e_m.
$$

이 식은 실측 bound가 아니라 삼각부등식으로 얻은 조건부 관계다.
Cached balancing을 아무리 잘해도 staleness와 target 오류가 크면 무효라는 뜻이다. 실제로 e_i를 알 수 있다는 주장은 하지 않는다. 재관측 시 proxy 오차를 측정해 사용 수명과 fallback을 정해야 한다.

## 9. 문헌에서 취할 것과 직접 이식하지 않을 것

| 문헌 | 읽은 핵심 | 이번 작업에서의 역할 |
|---|---|---|
| [GraB, NeurIPS 2022](https://proceedings.neurips.cc/paper_files/paper/2022/file/3acb49252187efa352a1ae0e4b066ced-Paper-Conference.pdf) | Stale-gradient balancing과 순서의 수렴 분석 | 후보 B의 이론적 출발점. 정리 직접 전이 금지 |
| [GraB-sampler, preprint](https://arxiv.org/html/2309.16809) | 실제 구현의 gradient 추출·시간 비용 | 원형 직접 이식의 비용 경고 |
| [MIR, NeurIPS 2019](https://papers.nips.cc/paper_files/paper/2019/file/15825aee15eb335cc13f9b559f166ee8-Paper.pdf) | 신규 update 이후 손상될 memory 선택 | 후보 C의 signed influence 근사 |
| [A-GEM, ICLR 2019](https://arxiv.org/html/1812.00420) | 평균 memory 보호 제약 | 후보 D의 국소 보호 조건 |
| [PCGrad, NeurIPS 2020](https://papers.neurips.cc/paper_files/paper/2020/file/3fe78a8acf5fda99de95303940a2420c-Paper.pdf) | 충돌 gradient 보정 | 후보 D와 비교할 optimizer baseline |
| [OCS, ICLR 2022](https://arxiv.org/html/2106.01085) | 대표성·다양성·과거 affinity 분리 | 이 셋을 entropy 하나로 대체하지 말아야 한다는 근거. 후보 전체 fresh gradient 평가와 memory 축소는 직접 이식 제외 |
| [GRAD-MATCH, ICML 2021](https://proceedings.mlr.press/v139/killamsetty21a.html) | 전체 training/reference gradient 근사 | 후보 B의 구성 단계 참고. 큰 OMP/coreset 탐색 제외 |
| [GCR, CVPR 2022](https://research.google/pubs/gcr-gradient-coreset-based-replay-buffer-selection-for-continual-learning/) | 과거 data gradient를 대표하는 replay coreset | 전체 frame 저장을 줄이는 방식은 이번 범위에서 제외 |
| [Soft Mining, CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/html/Kheradmand_Accelerating_Neural_Field_Training_via_Soft_Mining_CVPR_2024_paper.html) | Neural field의 pixel-level soft importance sampling | RGB ray/pixel 방식과 full-image Gaussian rasterizer의 비용 차이 때문에 우선 이식 제외 |
| [Importance Sampling, ICML 2018](https://proceedings.mlr.press/v80/katharopoulos18a.html) | Gradient-norm 근사와 분산 감소에 따른 sampling | 보정 확률만 높이고 utility가 늘었다고 해석하지 않기 위한 참고 |
| [Neely, stochastic optimization notes](https://ee.usc.edu/stochastic-nets/docs/network-optimization-notes.pdf) | Queue debt와 utility의 공동 최적화 | 후보 A 및 service 실행 가능성의 출발점 |

논문 저자들의 수렴률·속도 향상은 해당 논문의 조건과 workload에 대한 것이다. 위 후보들의 3DGS 성능 예측치가 아니다. 이 조합의 학술적 신규성은 별도 검토가 필요하다.

## 10. 우선순위와 구체적인 다음 작업

| 후보 | 수렴을 겨냥하는 지점 | 주요 상태/비용 | 우선순위 |
|---|---|---|---|
| A | Service 의무 아래 전체 목적의 감소량을 높이는 배분 | 두 집합 sketch/moment, scalar 또는 소수-group 배분 | 최소 ERCB 확장 후보 |
| B | 짧은 prefix의 gradient 편차를 줄이는 구성·순서 | Small candidate sketch cache, bounded block balancing | 순서 중심 주 후보 |
| C | 신규 update가 만드는 과거 손상을 효율적으로 복구 | Signed sketch + 작은 overlap/global shortlist | Interference 대응 경쟁 후보 |
| D | Fresh 신규·과거 gradient의 충돌을 update 단계에서 제어 | 두 paid backward/pair, gradient buffer와 reductions | Optimizer 변경 허용 시 경쟁 후보 |

추천은 B를 주 연구 후보, A를 가장 작은 변경의 경쟁 후보로 준비하는 것이다. D는 cached sketch가 너무 빨리 낡는 경우의 중요한 대안이다. C는 충돌이 주된 병목인 장면에서 따로 평가한다. 네 후보를 한꺼번에 합치지 않는다.

작업 산출물은 원인 분석 보고서에 머무르지 않고 다음 두 prototype으로 구체화하는 것이 좋다:

1. 공통 service ticket 실행기 + 기존 update 통계 hook. 강제 service와 선택 policy를 독립 교체 가능하게 한다.
2. 같은 hook 위에 A의 소수-group controller와 B의 bounded block ordering을 각각 구현한다. 동일한 service executor와 동일한 paid gradient 예산으로 비교한다.

첫 선택 기준은 overhead 1–3% 이내, 지연 분포 개선, held-out quality-vs-wall-clock 개선의 동시 충족이다. Proxy 통계는 후보를 해석·기각하기 위한 것이며 최종 성과 지표를 대체하지 않는다.

추가 실험을 수행한다면 당시 결과를 experiment card/INDEX/STATUS의 세 기록에 남긴다. 이번 문헌·설계 검토는 실험 결과가 아니므로 완료 실험으로 등록하지 않았다.
