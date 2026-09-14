# exp75 — Block-weighted random reshuffling 30k loop

> 상태: **진행 중** (2026-09-06). 이 카드는 각 training/render batch가 끝날 때마다 누적 갱신한다.

## 목표와 성공 조건

성장하는 causal full-frame pool에서 count-balanced sampling을 조금씩 수정해, 일반
`causal_rr`보다 held-out PSNR이 높은 단일 recipe를 찾는다. 1253에서 선택한 파라미터를
재튜닝하지 않고 305와 12F에 전이하며, 세 장면 모두에서 baseline을 넘어야 성공으로 판정한다.

모든 run은 30,000 optimizer update, `-r 4`, seed 0, llffhold-8 held-out 평가를 사용한다.
품질 판정은 train metric이 아닌 held-out 전체/시간순 thirds PSNR로 한다.

## 현재 주 방법

`block_weighted_rr(K, beta)`는 블록 경계에서 현재 causal pool의 view마다

\[
\log w_i=-\beta(n_i-n_{\min})
\]

를 주고 Gumbel top-k로 최대 `K`개의 서로 다른 view를 뽑는다. 이는 정확한
Plackett–Luce weighted sampling without replacement이다.

- 블록 내부 중복은 0이다.
- `beta=0`은 uniform random K-permutation이다.
- `beta>0`은 lifetime selection count가 작은 view의 다음 블록 포함 확률을 높인다.
- 최종 방법에서는 `K=128`을 scheduler 시간 해상도로 고정하고 `beta`만 조절한다.
- `K=64/256/512`는 `K=128` 선택의 민감도 진단용이며 scene별 튜닝에는 쓰지 않는다.

## 실행 기록

### Stage A — 1253 선별 sweep

| Scene | K | beta | 상태 | 역할 |
|---|---:|---:|---|---|
| 1253 | 64 | 0.01 | **35.06090**, thirds 35.65973/36.03515/33.47672 | K 민감도 |
| 1253 | 64 | 0.02 | **34.99177**, thirds 35.55051/35.96483/33.44963 | K 민감도 |
| 1253 | 64 | 0.05 | **35.04808**, thirds 35.53075/35.91540/33.68914 | K 민감도 |
| 1253 | 128 | 0.01 | **35.03865**, thirds 35.84926/35.78512/33.46655 | beta 후보 |
| 1253 | 128 | 0.02 | **34.93425**, thirds 35.75617/35.55666/33.47470 | beta 후보 |
| 1253 | 128 | 0.05 | **35.00867**, thirds 35.61774/35.83823/33.55877 | beta 후보 |
| 1253 | 256 | 0.02 | **35.01906**, thirds 35.52485/35.97154/33.55143 | K 민감도 |
| 1253 | 512 | 0.02 | **34.98487**, thirds 35.78211/35.84825/33.30949 | K 민감도 |

고정 비교 baseline은 exp74의 1253 `causal_rr` 30k held-out **35.20214 dB**
(thirds 36.07725 / 36.13585 / 33.37712 dB)이다.

**Stage A 판정:** strict-block 8개 모두 전체 PSNR에서 baseline을 넘지 못했다. `K=128`
최선은 `beta=0.01`로 −0.16349 dB다. `beta=0.05`는 후반 third를 +0.18165 dB
개선하지만 전체는 −0.19347 dB다. 모든 native block의 duplicate 수는 0으로 구현 계약은
통과했다. K 변화가 승패를 바꾸지 않았으므로 이후에는 `K=128`을 고정한다.

### Stage B — blind transfer

1253 결과에서 전체 PSNR에 가장 가까운 `beta=0.01`과 후반 third 개선이 큰
`beta=0.05`를 진단 후보로 골랐다. 성공 후보로 채택한 것은 아니며, 두 값을 305와 12F
30k에 그대로 적용해 scene/load별 반응을 확인한다.

| Scene | causal RR 30k | K=128, beta=.01 | K=128, beta=.05 |
|---|---:|---:|---:|
| 1253 | 35.20214 | 35.03865 (−0.16349) | 35.00867 (−0.19347) |
| 305 | 34.54090 | 34.26338 (−0.27752) | **34.63384 (+0.09294)** |
| 12F | **27.63997**, thirds 29.81165/28.37964/24.72862 | **27.71463 (+0.07466)** | 27.54994 (−0.09003) |

세 장면에 동일한 beta로 전부 이기지는 못했지만, count correction이 RR을 실제로 이기는
장면은 확인했다. 12F는 약한 correction, 305는 강한 correction에서 승리했다. 강한
`beta=.05`의 thirds를 보면 305는 36.44188/33.39141/34.06824, 12F는
28.69388/28.51652/25.43942다. 두 장면 모두 중·후반은 RR보다 좋아졌지만 초반 손실이
전체 승패를 좌우했다. 이 공통 failure mode가 Loop 2 stable-pool correction의 근거다.

## 이전 변형의 진단 결과 (주 결과와 분리)

`lag_rr`와 `mixed_deficit_rr`는 성장 중 deficit correction이 현재 global epoch에서 이미
선택된 view를 다시 고를 수 있어 strict block-wise 비복원 방법이 아니다. 따라서 이 결과는
알고리즘 탐색 근거로만 남기고 주 방법의 random-reshuffling 증거로 쓰지 않는다.

1253에서 가장 나았던 진단 후보 `mixed_deficit_rr(rho=0.35)`는 held-out 35.15129 dB로
baseline보다 0.05085 dB 낮았지만, 후반 third는 33.80985 dB로 0.43273 dB 높았다.
이는 약한 count correction이 후반 view에는 도움을 주지만 전체 품질 역전은 아직 만들지
못했음을 뜻한다.

## 판정 보류 사항

- 현재 strict block 후보는 아직 render 전이므로 PSNR 결론을 내리지 않는다.
- seed 0 단일 선별 뒤, 세 장면 동시 승자가 나올 경우 최소 반복 seed로 승리를 확인한다.
- 데이터는 held-out RGB를 photometric training에서 제외하지만, fixed VIGS pose/init은 전체
  파이프라인 산출물이라 strict input-disjoint online 결과로 주장하지 않는다.

## 2026-09-06 추가 가설 — 왜 같은 30k가 공정한 saturation 비교가 아닌가

일반 causal RR은 각 growing epoch의 coverage를 잘 보존하므로 uniform full-pool objective에
대해 매우 강한 baseline이다. 반면 lifetime count balancing은 늦은 view의 과소 노출을
보정하는 동안 오래된 view를 덜 뽑는 의도적 bias를 만든다. 따라서 다음 두 조건이 없으면
RR보다 낮아질 가능성이 높다.

1. arrival 때문에 실제 count skew가 충분히 커야 한다.
2. full pool이 갖춰진 뒤 그 skew를 갚을 optimizer service가 충분해야 한다.

장면마다 비교 가능한 계산량은 raw iteration `T`보다

\[
E_{tail}=\frac{T-a_{last}}{N}
\]

인 **post-arrival full-pool-equivalent epoch**다. 현재 30k는 다음처럼 서로 다른
saturation 수준을 뜻한다.

| Scene | train views N | last arrival | tail epochs @30k | T for 10 tail epochs | T for 20 tail epochs |
|---|---:|---:|---:|---:|---:|
| 1253 | 1,140 | 8,821 | 18.58 | 20,221 | 31,621 |
| 305 | 2,352 | 18,661 | 4.82 | 42,181 | 65,701 |
| 12F | 1,925 | 24,421 | 2.90 | 43,671 | 62,921 |

즉 1253의 30k는 거의 20 tail epochs지만, 305와 12F는 각각 4.8/2.9 epoch뿐이다.
따라서 30k 세 장면 수치만으로 count correction의 포화 성능을 비교하면 안 된다. 30k는
동일 raw-budget 결과로 유지하고, 후속 loop에서는 `E_tail=10,20`의 동등 load regime를
추가한다. 이때도 각 장면 안에서는 RR와 후보에 정확히 같은 update budget을 준다.

또한 fixed `beta`가 scene별 count scale에 민감하면, 다음 단순 변형으로 count lag를 현재
range 또는 mean으로 정규화해 `beta`를 최대/최소 selection odds라는 dimensionless 값으로
바꾼다. 이 변형은 현재 strict-block 결과가 세 장면에 전이되지 않을 때만 도입한다.

## Loop 2 준비 — stable-pool phase correction

Loop 1이 1253 전·중반을 잃고 후반만 개선한 원인을 반영해
`stable_pool_block_rr`를 구현했다.

- growth/densification 중에는 seed가 같은 `causal_rr`와 선택열이 정확히 같다.
- `iteration >= densify_until_iter`이고 새 arrival이 `K=128` step 동안 없을 때만 lifetime
  count-weighted block RR로 전환한다.
- 전환은 미래의 EOS를 보지 않고 과거 arrival 정지만 사용하므로 causal하다.
- 전환 뒤 각 block도 Gumbel top-k 비복원 추출이라 block 내 duplicate는 0이다.
- scheduler 단위 테스트 10개 전부 통과: pre-switch RR 동일성, causal switch 시점,
  post-switch block 무중복을 포함한다.

이 변형은 Loop 1의 305/12F 전이 결과를 확인한 뒤 실행한다.

### Loop 2 실행

세 장면 공통 recipe `stable_pool_block_rr(K=128, beta=.05)`를 30k·seed 0에서 실행한다.
Loop 1의 세 장면 결과를 보고 고른 development recipe이므로, 세 장면 승리 후에도 새 seed
또는 추가 외부 장면 검증 없이는 일반화 완료로 판정하지 않는다.

| Scene | 상태 | 실제 weighted phase 시작 예정 |
|---|---|---:|
| 1253 | **34.96431**, RR 대비 −0.23783 | max(15,000, 8,821+128) = 15,000 |
| 305 | **34.57628**, RR 대비 **+0.03538** | 18,661+128 = 18,789 |
| 12F | **27.68096**, RR 대비 **+0.04099** | 24,421+128 = 24,549 |

Loop 2도 세 장면 공통 승리는 실패했다. thirds는 1253
35.28377/35.99756/33.60569, 305 35.83395/33.56526/34.32964, 12F
29.25193/28.28120/25.50975다. 세 장면 모두 중·후반은 개선 방향이지만 최종 초반
held-out이 감소했다. 따라서 growth 단계 선택열을 같게 만드는 것만으로 forgetting을 막지는
못했다. 이후 refinement에서 late-biased update가 shared Gaussian을 이동시키기 때문이다.

전환 시 baseline count CV/min–max는 1253 0.633/5–60, 305 0.926/0–39,
12F 1.059/0–83이다. 305·12F에는 아직 한 번도 선택되지 않은 view가 있지만 1253에는 없다.
이는 count correction의 이득 조건이 단순 scene length보다 **전환 시 service starvation**과
관련 있음을 시사한다.

### Loop 3 — 1253 correction strength 분해

`stable_pool_block_rr(K=128)`에서 `beta=0/.005/.01`을 1253 30k에 실행한다.
`beta=0`은 stable phase의 uniform K-permutation control이므로 block reset 효과를 분리한다.
`.005/.01`은 `.05`의 early forgetting을 줄이는 약한 count correction이다. 1253에서
baseline을 넘는 값이 있을 때만 동일 값을 305·12F로 전이한다.

| beta | 상태 |
|---:|---|
| 0 | **35.07180**, RR 대비 −0.13034, CV 0.343 |
| .005 | **35.01356**, RR 대비 −0.18858, CV 0.324 |
| .01 | **34.94220**, RR 대비 −0.25994, CV 0.310 |

Loop 3 판정은 전부 실패다. `beta=0`도 낮으므로 1253 손실의 첫 원인은 count weight만이
아니라, 포화된 full-pool RR epoch를 K=128 subset block으로 자르며 epoch-level coverage를
버린 것이다. 여기에 beta를 높일수록 count CV는 줄지만 PSNR은 더 낮아져, 1253 30k에서는
count equality와 quality가 반대 방향이다. 이 장면에 fixed-block beta를 더 미세 sweep하지
않는다.

### Loop 4 — entropy-floor RR

prior 비엄격 `mixed_deficit_rr(rho=.35)`가 1253에서 −0.05085 dB까지 접근한 근거를
strict K-block 비복원 방식으로 옮겼다. 각 block 위치에서 `(1-rho)`는 persistent global
RR queue, `rho`는 현재 minimum-count cohort를 사용하며, 이미 block에 선택된 view는 양쪽
모두에서 제외한다. deficit draw는 RR queue에서 제거하지 않아 장기 count catch-up이
가능하다.

- `rho=0`: persistent RR coverage control
- 모든 rho에서 block 내 duplicate 0
- `rho=0` static pool에서 각 full epoch exact RR인 단위 테스트 통과
- 1253 scheduler-only entropy ratio: rho .1/.2/.35 = .978/.974/.966

| rho | 1253 30k 상태 |
|---:|---|
| 0 | **35.07043** (−0.13171), CV .325 |
| .1 | **35.09684** (−0.10530), CV .265 |
| .2 | **35.19759** (−0.00455), CV .219 |
| .35 | **35.20084** (−0.00130), CV .170 |

`rho=.2/.35`는 baseline 35.20214와 사실상 동률이지만 명목상 승리가 아니므로 성공으로
세지 않는다. `.35` thirds는 35.61542/36.16835/33.81108로 baseline 대비
−0.46183/+0.03250/**+0.43396**이다. count correction의 late 이득과 early 비용이 거의
정확히 상쇄된다.

### Loop 5 — iteration/saturation regime

1253의 초기 구간이 더 포화되면 late 이득이 early 비용보다 커지는지 확인하기 위해,
`causal_rr`와 `entropy_floor_rr(K=128,rho=.35)`를 **동일 45k**에서 새로 paired 실행한다.
30k와 45k point cloud를 모두 저장해 anytime curve도 비교한다. 한쪽에만 추가 iteration을
주는 방식은 사용하지 않는다.

| 1253 45k arm | 상태 |
|---|---|
| causal RR | train 45k 완료, 평가 대기 |
| entropy-floor rho=.35 | train 45k 완료, 평가 완료 |

| iteration | causal RR | entropy-floor rho=.35 | delta |
|---:|---:|---:|---:|
| 30k paired checkpoint | 35.17229 | 35.14533 | −0.02697 |
| 45k | 35.43810 | **35.56092** | **+0.12282** |

45k thirds는 RR 36.34005/36.16369/33.79384, entropy-floor
36.21664/36.27088/34.18309다. 초반 −0.12341, 중반 +0.10719, 후반 **+0.38925**로,
30k에서 거의 상쇄되던 late 이득이 45k에서 전체 승리로 전환됐다. 같은 run의 30k에서도
후보가 아직 낮으므로 iteration crossing을 숨긴 cherry-pick이 아니라 saturation curve로
보고한다.

사용자 요청에 따라 endpoint-only 판정을 중단한다. 선택 후보의 반복 검증에서는 RR와 후보
모두 `15k,20k,25k,30k,35k,40k,45k`를 저장·render하여

\[
t_{cross}=\min\{t:\operatorname{PSNR}_{candidate}(t)>
\operatorname{PSNR}_{RR}(t)\}
\]

와 이후 checkpoint에서 승리가 유지되는지를 보고한다. 현재 seed0 run은 이미 30k/45k만
저장했으므로 두 점을 먼저 판정하고, 다음 반복 run부터 5k 간격 protocol을 적용한다.

305·12F에도 같은 45k paired protocol을 적용한다.

| Scene/arm | 상태 |
|---|---|
| 305 causal RR | 30k/45k 평가 완료 |
| 305 entropy-floor rho=.35 | 30k/45k 평가 완료 |
| 12F causal RR | 30k/45k 평가 완료 |
| 12F entropy-floor rho=.35 | 30k/45k 평가 완료 |

seed 0의 공통 45k 결과는 다음과 같다.

| Scene | Iter. | causal RR | entropy-floor | delta | thirds delta (early/mid/late) |
|---|---:|---:|---:|---:|---:|
| 1253 | 30k | 35.17229 | 35.14533 | −0.02697 | −0.341/−0.259/+0.525 |
| 1253 | 45k | 35.43810 | **35.56092** | **+0.12282** | −0.123/+0.107/**+0.389** |
| 305 | 30k | 34.36956 | **34.68645** | **+0.31689** | −0.837/+0.145/**+1.642** |
| 305 | 45k | 35.10528 | **35.85385** | **+0.74857** | −0.421/+0.422/**+2.245** |
| 12F | 30k | **27.59735** | 27.50587 | −0.09148 | −0.405/−0.201/**+0.331** |
| 12F | 45k | 28.17952 | **28.28587** | **+0.10635** | −0.216/−0.026/**+0.561** |

따라서 **동일한 단일 recipe가 45k seed 0에서 세 장면 모두 RR을 이기는 첫 결과**를
얻었다. 개선은 일관되게 late third 회복에서 나오고, 1253·12F는 30k에서는 아직 전체
평균이 낮다가 45k에 역전한다. 이는 count correction이 무조건 좋은 것이 아니라,
성장 종료 뒤 후발 view deficit을 갚을 service가 충분한 saturation regime에서 유리하다는
가설과 맞는다. 반면 305는 전환 시 count min=0, CV=.926으로 starvation이 가장 뚜렷해
30k부터 이미 이겼다.

아직 seed 0 한 번이므로 이 결과를 3-scene 일반화 완료로 확정하지 않는다. 다음 실행은
seed 1에서 세 장면 모두 15k/20k/25k/30k/35k/40k/45k를 저장·평가해 crossover 시점과
45k 승리 반복 여부를 동시에 검증한다.

## Loop 6 — KF-interval hierarchical softmax RR

사용자 제안에 따라 frame별 lifetime count가 아니라 **KF interval에 배정된 총 optimizer
update 수**를 softmax 상태로 쓰는 `interval_softmax_rr`를 추가했다. 같은 arrival step에
들어온 frame들을 interval \(G_j\)로 묶고 interval service를

\[
c_j(t)=\sum_{s\le t}\mathbf 1[J_s=j]
\]

로 기록한다. 바깥 sampler는 현재 interval들에서

\[
w_j=\exp\{-\beta(c_j-c_{\min})\}
\]

를 사용해 \(K_I\)개의 서로 다른 interval을 Plackett--Luce 방식으로 비복원 추출한다.
선택된 interval 안에서는 그 interval의 frame들만을 대상으로 별도의 persistent uniform RR을
한 번 진행한다. 따라서 (1) count가 의미하는 단위가 GPU quota를 받은 KF interval이고,
(2) 짧은 block이 한 시간 구간의 인접 frame으로 붕괴할 수 없으며, (3) interval 내부 frame도
중복 없이 순환한다.

outer block의 각 순차 위치에서 아직 선택되지 않은 interval 집합을 \(R\)라 하면 softmax는

\[
p^*=\arg\max_{p\in\Delta(R)}
\left[\mathcal H(p)-\beta\,\mathbb E_{j\sim p}(c_j-c_{\min})\right]
\]

의 닫힌형 해다. 즉 \(\beta\)는 임의의 heuristic 점수가 아니라 선택 entropy와 누적
interval-service deficit 사이의 Lagrange multiplier다. 또한 \(M\ge K_I\)이면 한 outer
block의 interval ID는 정확히 \(K_I\)개가 모두 다르므로 empirical interval entropy는 가능한
최댓값 \(\log K_I\)이고 collision은 0이다. interval \(j\)가 총 \(c_j\)번 선택됐을 때 내부
RR에 의해 그 안의 frame별 횟수 차이는 항상 1 이하이다.

전체 interval pool을 한 epoch 동안 전부 순회하면 모든 interval이 정확히 한 번씩 선택되어
\(\beta\)가 빈도에는 영향을 주지 않고 순서만 바꾸므로, outer RR은 full epoch가 아니라 짧은
통계 block으로 정의한다. scheduler-only 3-scene screen에서 \(K_I=8/16/32\),
\(\beta=0/.0025/.005/.01/.02\)를 30k/45k에 비교했다. \(K_I=32\)가 128-step temporal
entropy를 가장 잘 보존했고, \(\beta=.005\)는 45k에서 다음 절충을 보였다.

| Scene | RR interval-count CV | interval-softmax CV | RR temporal H@128 | interval-softmax H@128 |
|---|---:|---:|---:|---:|
| 1253 | .193 | **.071** | .981 | **.981** |
| 305 | .664 | **.249** | .979 | .970 |
| 12F | .580 | **.370** | .979 | .977 |

즉 전체 trajectory mixing entropy를 거의 유지하면서 interval quota 편차는 줄일 수 있다.
`beta=.01`은 CV를 더 낮추지만 305/12F temporal entropy가 약 .962/.970까지 내려가므로,
실제 PSNR 선별 sweep은 사전 고정한 \(K_I=32\)와
\(\beta\in\{0,.0025,.005,.01\}\)로 시작한다. `beta=0`은 계층화 자체의 효과를 분리하는
control이다. 구현 회귀 16개는 모두 통과했다.

seed 1 entropy-floor 반복 batch는 1253 RR 45k와 7개 checkpoint 저장 직후 중단했고,
미완성 후보 run은 만들지 않았다. GPU는 이 interval-level 사용자 제안을 우선 검증하는 데
배정한다. 완료된 RR checkpoint는 후속 anytime baseline으로 보존한다.

### 2026-09-06 scene 선정 protocol 정정

1253 한 장면 PSNR로 \(\beta\)를 고르는 계획은 사용자 지적에 따라 실행 전에 철회한다.
1253은 45k baseline RR의 interval-count CV가 .193으로 이미 비교적 균등해 count correction에
불리한 out-of-regime control이다. 이를 결과에서 삭제하지는 않되 주 ablation scene 선정과
parameter tuning에는 쓰지 않는다.

성능 결과와 무관한 baseline-only 난이도 지표를

\[
R_s(T)=\frac{\operatorname{std}_j c^{RR}_{s,j}(T)}
             {\operatorname{mean}_j c^{RR}_{s,j}(T)}
\]

로 사전 정의한다. raw 45k에서 \(R_s\ge.5\)인 scene을 growing-pool high-skew regime으로
간주한다.

| Scene | \(R_s(45k)\) | 역할 |
|---|---:|---|
| 1253 | .193 | out-of-regime robustness control |
| 305 | .664 | in-regime ablation |
| 12F | .580 | in-regime ablation |
| 3F | .760 (VRS 길이 기반 사전 simulation) | in-regime external stress |
| 2F | .374 | optional spatial-extent control |

이 구분은 장면 이름이 아니라 arrival/budget 구조로도 설명된다.

| Scene | last arrival / 45k | arrival 뒤 full-pool-equivalent epochs | interval-size CV |
|---|---:|---:|---:|
| 1253 | .196 | 31.74 | .210 |
| 305 | .415 | 11.20 | .303 |
| 12F | .543 | 10.69 | .360 |
| 3F | .811 | 2.00 | .017 |

1253은 pool 성장이 일찍 끝나 RR도 31.7회의 추가 epoch를 받아 자연히 균등화되는 반면,
3F는 전체 budget의 81%까지 pool이 증가해 RR이 후발 구간 deficit을 갚을 시간이 2 epoch뿐이다.
따라서 제안법의 예상 우세 조건은 특정 방 이름이 아니라 **arrival horizon이 길고 post-arrival
service가 적어 RR exposure skew가 큰 growing-pool regime**이다. interval-size CV는 raw
interval-total 방식의 별도 교란요인이며 size-aware base measure가 이를 보정한다.

따라서 주 ablation은 305·12F·3F 세 장면이며, 1253은 "잘 되는 장면만 골랐다"는 해석을
막는 negative/control 결과로 같이 공개한다. \(K_I=32,\beta=.005\)는 1253 PSNR이 아니라
세 기존 schedule의 interval-CV 감소와 temporal entropy 보존 Pareto에서 사전 고정한다.
진행 중이던 1253 batch는 `beta=0/.0025/.005` control까지만 보존하고 `.01`은 실행하지 않는다.

## Loop 7 — interval-size-aware softmax RR

Loop 6 원형 \(K_I=32,\beta=.005\)는 45k에서 305를 **+0.32601dB** 개선했지만
12F는 **−0.05405dB**로 근소하게 졌다. 1253 control도 −0.10767dB였다. 원형은
interval 총 service를 직접 동일화하므로, 크기가 1–30 frame인 305 interval에서 짧은
interval의 한 frame이 최대 214회 선택되는 문제가 확인됐다.

sampling unit과 outer 비복원 제약은 유지하되, variable interval size에서 beta=0의
frame-uniform base measure를 보존하도록 다음 한 줄만 바꾼다.

\[
\log w_j = \log |G_j|
 -\beta\left(\frac{c_j}{|G_j|}-\min_k\frac{c_k}{|G_k|}\right).
\]

즉 interval 총 count \(c_j\)는 그대로 로깅하되, 같은 총량을 강요하지 않고 interval당
평균 frame service를 correction 상태로 쓴다. \(\beta=0\)에서는 interval 선택 확률이
\(|G_j|\)에 비례하고 내부 frame이 uniform이므로 frame marginal이 uniform이다.

3-scene scheduler-only Pareto에서 \(K_I=32,\beta=.02\)를 PSNR 평가 전에 고정했다.

| Scene | RR frame CV | size-aware CV | RR temporal H@128 | size-aware H@128 |
|---|---:|---:|---:|---:|
| 1253 | .211 | **.143** | .981 | .981 |
| 305 | .386 | **.321** | .979 | .978 |
| 12F | .578 | **.433** | .979 | .974 |

raw interval-total 방식보다 frame fairness와 temporal mixing이 동시에 개선되며, 구현 포함
18개 scheduler test가 통과했다. 다음 실제 PSNR은 이 단일 값을 305·12F에 먼저 적용하고,
통과하면 3F에 그대로 전이한다.

실제 held-out 결과에서 size-aware correction은 두 in-regime 장면과 두 budget을 모두
통과했다.

| Scene | Iter. | causal RR | size-aware interval | delta |
|---|---:|---:|---:|---:|
| 305 | 30k | 34.36956 | **34.76444** | **+0.39488** |
| 305 | 45k | 35.10528 | **35.55346** | **+0.44818** |
| 12F | 30k | 27.59735 | **27.64640** | **+0.04905** |
| 12F | 45k | 28.17952 | **28.29745** | **+0.11793** |

45k count CV는 305에서 RR .3860→**.3207**, 12F에서 .5781→**.4330**으로
감소했고, 최근 temporal entropy ratio는 각각 .9781/.9738이었다. 모든 native outer
block의 interval 중복은 0이다. 특히 raw interval-total 방식이 12F에서 −.05405dB였던
것과 달리 size-aware 방식은 +.11793dB이므로, variable group size에 대한 base-measure
보정이 필요하다는 진단을 지지한다. 이 결과 뒤에도 \(K_I=32,\beta=.02\)를 바꾸지 않고
사전 지정한 3F transfer를 수행한다.

개선 구간도 가설과 일치한다. 45k thirds delta(후보−RR)는 305에서
−.298/**+.652/+.990dB**, 12F에서 −.205/−.145/**+.704dB**다. 즉 전체 평균 승리는
기존에 잘 학습된 초반을 더 강화해서가 아니라, growing pool의 후발 구간 coverage를
회복해서 발생한다. 30k에서도 late-third delta는 305 +.324, 12F +.455dB다.

## 추가 외부 장면 후보

사용자가 `/home/intern/aria_data/`에 추가한 12개 VRS/MPS 묶음의 전송 완료를 확인했다.
closed-loop trajectory는 모두 1kHz이며 quality score 평균은 0.994 이상이다. RGB 20Hz를
가정한 사전 load audit에서 가장 정보량이 큰 두 후보는 다음과 같다.

| 후보 | duration | 예상 RGB/train | 10Hz 경로 길이 | 공간 extent | 사전 선택 이유 |
|---|---:|---:|---:|---:|---|
| 0416 301-3F | 242.6s | 4,869/4,260 | 132.5m | 48.0m | 가장 긴 pool-growth/revisit stress |
| 0416 301-2F | 119.0s | 2,396/2,096 | 154.0m | 72.5m | 가장 큰 이동·공간 다양성 stress |

위 frame 수는 이제 VRS `camera-rgb` stream에서 직접 읽은 값이며 예상치가 아니다.
3F를 **interval-softmax 우세 예상 외부 장면**으로, 2F를 별도의 넓은 공간 일반화 장면으로
사전에 고정한다. 결과를 본 뒤 scene을 고르는 cherry-pick을 피하기 위해 이 선택을 먼저
기록한다.

3F는 pseudo-KF interval을 RGB 8장 단위, interval당 60 optimizer update로 구성하면 마지막
arrival이 약 36.5k이고 train pool이 4,260장이다. 따라서 raw-budget 비교는 45k로 하되,
장면 길이 차이를 보정한 비교는

\[
T_{10}=a_{last}+10N\simeq79.1\text{k}
\]

에서 추가한다. 이 조건은 기존 세 장면과 동일하게 마지막 arrival 뒤 full-pool-equivalent
10 epoch를 제공한다. VRS RGB 추출과 MPS pose/semidense point 변환 뒤, 1253에서 고른
\(K_I,\beta\)를 재튜닝 없이 적용한다.

변환 완료 뒤 PSNR을 보기 전에 exact schedule을 재생한 사전 screen은 다음과 같다. 이 결과는
`evidence/aria3F_scheduler_preregistered_screen.json`에 고정했다.

| Budget | Scheduler | frame-count CV | temporal H@128 |
|---:|---|---:|---:|
| 45k | causal RR | .7603 | .9783 |
| 45k | size-aware, \(K_I=32,\beta=.02\) | **.7004** | .9758 |
| 79,081 | causal RR | .4325 | .9791 |
| 79,081 | size-aware, \(K_I=32,\beta=.02\) | **.3511** | .9762 |

따라서 3F는 실제 arrival schedule에서도 사전 정의한 \(R_s(45k)\ge.5\) 조건을 통과한다.
후보는 RR 대비 count CV를 줄이면서 normalized temporal entropy를 0.976 이상 유지할 것으로
예측된다. 이 예측과 parameter는 held-out render를 보기 전에 확정했으며, 실제 PSNR 결과가
나쁘더라도 장면이나 값을 사후 교체하지 않는다.

### Loop 8 — 3F 사전 지정 transfer 실패와 topology-stage 분리

사전 고정한 size-aware \(K_I=32,\beta=.02\)의 3F held-out 결과는 실패다.

| Iter. | causal RR | size-aware interval | delta | count CV (RR→candidate) |
|---:|---:|---:|---:|---:|
| 45k | **29.26094** | 29.01926 | −.24168 | .7603→.7004 |
| 79,081 | **30.04542** | 29.79179 | −.25363 | .4325→.3511 |

45k thirds delta는 −.282/−.282/−.162dB이고, 79,081에서도
−.563/+.099/−.297dB다. 즉 count fairness 개선만으로 quality가 좋아진다는 가설은
3F에서 기각된다. 결과를 보고 3F나 79k endpoint를 제외하지 않는다.

가장 직접적인 차이는 3F의 arrival이 36.5k까지 이어져 Gaussian densification 종료 15k와
크게 겹친다는 점이다. 기존 후보는 topology가 생성·분할되는 민감한 단계부터 sampling law를
바꾸므로, 이후 appearance 단계에서 count가 균등해져도 초기 topology 손실을 되돌리지 못할 수
있다. 실제 frozen Gaussian 수도 RR 408,667개와 후보 438,823개로 **+7.38%** 달라져,
scheduler 비교가 topology 차이까지 유발했음을 확인했다. 이를 검증하는 다음 최소 수정은 별도
tunable 경계를 만들지 않고 **기존 3DGS
`densify_until_iter=15k`를 stage boundary로 그대로 사용**한다.

\[
I_t\sim
\begin{cases}
\text{causal RR}, & t<\tau_d,\\
\text{size-aware interval softmax RR}(K_I=32,\beta=.02), & t\ge\tau_d,
\end{cases}
\qquad \tau_d=15000.
\]

두 번째 단계의 interval/frame count에는 첫 단계에서 받은 service도 그대로 포함한다. 같은
seed에서 \(t<\tau_d\)의 draw가 causal RR와 완전히 동일함을 unit test로 검증했고, 총 20개
scheduler test가 통과했다. PSNR 전에 고정한 schedule-only 결과는 다음과 같다.

| Scene/budget | RR count CV | staged count CV | staged temporal H@128 |
|---|---:|---:|---:|
| 305/45k | .3860 | **.3183** | .9776 |
| 12F/45k | .5781 | **.4650** | .9729 |
| 3F/45k | .7603 | **.7077** | .9769 |
| 3F/79,081 | .4325 | **.3540** | .9765 |

따라서 correction 강도와 block 크기는 바꾸지 않고 topology-sensitive 구간만 baseline과
동일하게 보호한다. 먼저 실패한 3F에 적용하고, 통과할 때만 305·12F로 역전이한다.

staged 결과는 topology confound는 제거했지만 late recovery 크기는 부족했다.

| Iter. | RR | staged candidate | delta | thirds delta (early/mid/late) |
|---:|---:|---:|---:|---:|
| 45k | 29.26094 | **29.39950** | **+.13856** | −.188/+.413/**+.190** |
| 79,081 | **30.04542** | 30.04091 | −.00451 | −.626/+.542/**+.070** |

frozen Gaussian은 407,502개로 RR 408,667개와 0.29%만 달라져 기존 non-staged의
438,823개(+7.38%)와 달리 topology 교란은 제거됐다. 그러나 사용자와 합의한 late-effect
기준에서 +.190/+.070dB는 충분히 크지 않으므로 성공으로 세지 않는다.

여기서 3F protocol의 구조적 문제가 드러났다. 마지막 arrival은 36,481인데 기본
`densify_until_iter=15,000`이므로 train view 4,260장 중 약 절반은 topology growth가 끝난
뒤에야 도착한다. appearance replay만으로 아직 생성되지 않은 late-region geometry를 회복할
수 없으므로, 이는 scheduler의 late recovery를 측정하는 공정한 조건이 아니다. 다음 진단은
양 arm 모두

\[
\tau_d=36{,}500\simeq a_{last}
\]

로 맞춰 모든 admitted cohort가 topology 형성 기회를 갖게 한다. 후보는 \(t<\tau_d\)에서
RR와 동일하고 densification이 끝난 뒤에만 correction을 시작하므로 양 arm의 topology law도
동일하다. 이 변경은 후보만의 추가 compute가 아니라 RR와 후보에 공통 적용한다.

PSNR 이전 schedule-only screen에서 \(K=32,\beta=.02\)는 3F count CV를 45k
.7603→.7382, 79,081 .4325→.3719로 줄이고 H@128은 .9758/.9766을 유지한다.
`.05/.1`은 더 강한 count correction이지만 H가 .966/.948 이하로 내려가므로 PSNR을 보고
고르지 않고 기존 `.02`를 유지한다.

실제 arrival-aligned 결과는 두 endpoint 모두 실패했다.

| Iter. | RR | candidate | overall delta | worst-Q1 delta | RR-hard-Q1 delta |
|---:|---:|---:|---:|---:|---:|
| 45k | **32.54523** | 32.45665 | −.08858 | −.11440 | +.21582 |
| 79,081 | **34.29523** | 34.08225 | −.21297 | −.12539 | +.34897 |

동일 RR-hard frame은 좋아졌지만 후보 자체의 lower tail이 악화했으므로 채택하지 않는다.
또한 densification 연장만으로 RR 자체가 기존 29.261/30.045에서 32.545/34.295dB로 크게
상승해, 이 조건에서는 sampling correction보다 topology service가 지배적임을 보여준다.
따라서 arrival-aligned densification 결과는 중요한 compute-axis control로 보존하되 제안
scheduler의 성공 evidence에는 포함하지 않는다.

### Quality lower-tail 평가 추가

사용자 제안에 따라 기존 overall PSNR과 temporal thirds를 삭제하지 않고, 시간 위치와 무관한
하위 품질 꼬리를 추가한다. 각 방법 자체의 per-view PSNR 하위 25% 평균을
`worst-Q1`(lower-tail CVaR-25)로 보고, baseline에서 가장 어려웠던 25%의 frame ID를 고정해
후보에서 다시 평가한 값을 `RR-hard-Q1`로 별도 보고한다. 후자는 서로 다른 frame 집합을 골라
생기는 착시를 막고, 전자는 후보 자체의 최악 꼬리가 실제로 올라갔는지 확인한다.

| Pair @45k | overall delta | late-third delta | worst-Q1 delta | RR-hard-Q1 delta |
|---|---:|---:|---:|---:|
| 305 size-aware | +.448 | +.990 | **+1.023** | **+1.421** |
| 12F size-aware | +.118 | +.704 | **+.979** | **+1.126** |
| 3F staged | +.139 | +.190 | **+.353** | **+.431** |

3F staged 79,081은 overall −.005dB로 동률이지만 worst-Q1 +.332,
RR-hard-Q1 +.388dB다. 따라서 현 evidence에서 가장 일반적인 효과는 특정 late index만이
아니라 **전체 held-out 분포의 under-trained/hard-view lower tail 회복**이다. 최종 ablation은
overall/thirds/worst-Q1/RR-hard-Q1/count CV/entropy를 모두 유지하며, lower-tail만 골라
평균 열세를 숨기지 않는다.

### Loop 9 — staged를 방법론에서 제거하고 shared-topology replay branch로 재정의

사용자 지적대로 고정 15k 이전에 causal RR, 이후 제안법을 쓴다고 **하나의 scheduler**를
정의하면 실제 VIGS 이식과 논문 설명이 애매하다. staged 결과는 원인 진단에는 유효하지만
최종 방법론으로 주장하지 않는다.

실제 VIGS에는 이미 `TopologyReplayController`의 `FRONTIER/BALANCED/REPLAY` 상태가 있고,
replay queue는 `allows_replay()`가 열린 뒤에만 service된다. 따라서 제안법의 정확한 범위는
**replay phase에서 사용하는 단일 sampler**다. frontier/topology mapping은 scheduler의
일부가 아니다.

offline ablation도 이를 반영해 다음 protocol로 고친다.

1. 공통 causal topology run을 iteration 14,999까지 한 번만 수행하고 model+optimizer
   checkpoint를 저장한다.
2. 두 arm 모두 그 **동일 checkpoint**에서 branch한다.
3. branch 뒤 baseline은 causal RR replay, 후보는 size-aware interval softmax replay를 쓴다.
4. 과거 arrival와 service count는 CUDA work 없이 scheduler만 fast-forward해 복원한다.

이렇게 하면 초반 causal RR은 제안 알고리즘의 구성요소가 아니라 두 arm이 공유하는 initialization
contract다. Gaussian tensor와 optimizer state까지 동일하므로, branch 이후 차이는 replay order
뿐이다. iteration 14,999를 쓰는 이유는 기본 densification의 마지막 update까지 checkpoint에
포함하면서 후보의 첫 replay draw를 15,000에서 시작시키기 위해서다. scheduler fast-forward
회귀를 추가해 총 21개 test가 통과했다.

참고로 독립 staged run의 45k 결과는 다음과 같지만, shared-checkpoint로 재현되기 전에는 최종
수치로 채택하지 않는다.

| Scene | overall delta | worst-Q1 delta | late-third delta |
|---|---:|---:|---:|
| 305 | +.775 | +.866 | +1.550 |
| 12F | +.161 | +.990 | +.867 |
| 3F | +.139 | +.353 | +.190 |

305 shared-checkpoint smoke test는 independent-run 효과의 상당 부분이 topology/run variance였음을
드러냈다. 두 branch의 frozen Gaussian은 정확히 592,695개로 같았다.

| Iter. | overall delta | worst-Q1 delta | RR-hard-Q1 delta | late-third delta |
|---:|---:|---:|---:|---:|
| 30k | −.300 | −.188 | +.146 | −.247 |
| 45k | **+.116** | +.077 | +.507 | **+.561** |

따라서 독립 staged 305의 +.775dB를 최종 evidence로 쓰지 않는다. 동일 topology에서도
45k replay-only late recovery는 남지만 자체 worst-Q1 개선은 약하다. 이제 shared checkpoint를
고정한 채 \(K=32\), \(\beta\in\{.02,.05,.1\}\)만 305·12F에서 sweep한다. 두 장면의
overall/worst-Q1/entropy Pareto로 공통 \(\beta\)를 정한 뒤 3F에는 재튜닝 없이 전이한다.

### Loop 10 — shared-topology \(\beta\) sweep 및 3F 전이값 사전 고정

여기서 `staged_interval_size_softmax_rr`라는 클래스명은 **공통 checkpoint를 정확히 재개하기
위한 실험 harness 이름**일 뿐, 논문 방법론의 이름이나 two-stage scheduler를 뜻하지 않는다.
iteration 14,999까지 실제로 checkpoint를 만든 causal-RR draw/count/RNG 상태를 동일하게
복원하고, topology가 고정되는 iteration 15,000부터 replay picker만 교체한다. 최종 논문의
제안법은 VIGS의 frontier/admission과 분리된 **단일 replay-phase sampler**로 정의한다.

동일 model·optimizer·592,695 Gaussian(305) 또는 동일 model·optimizer·291,453 Gaussian
(12F)에서 branch한 결과는 다음과 같다. 표의 PSNR은 후보−RR이며 entropy는 마지막
1,024 draw의 normalized temporal entropy다.

| Scene | \(\beta\) | 30k overall | 45k overall | 45k worst-Q1 | 45k thirds (early/mid/late) | 45k count CV | entropy |
|---|---:|---:|---:|---:|---:|---:|---:|
| 305 | .02 | −.300 | +.116 | +.077 | −.200/−.012/**+.561** | .318 | .9966 |
| 305 | **.05** | −.411 | **+.286** | **+.205** | −.526/+.330/**+1.054** | .248 | .9914 |
| 305 | .10 | −.273 | +.085 | +.082 | −.979/+.386/+.848 | **.189** | .9861 |
| 12F | .02 | +.026 | **+.081** | **+.483** | −.390/−.004/+.636 | .465 | **.9927** |
| 12F | **.05** | **+.034** | +.009 | +.446 | −.886/+.065/**+.849** | .371 | .9791 |
| 12F | .10 | −.253 | −.210 | −.316 | −1.559/+.064/+.863 | **.314** | .9753 |

해석은 단순하다. \(\beta=.1\)은 count CV를 가장 낮추지만 12F overall과 자체 lower tail을
악화시키는 과보정이라 탈락한다. \(\beta=.02\)는 가장 안전한 품질 보존형이고,
\(\beta=.05\)는 305·12F 모두 45k overall이 음수가 아니면서 worst-Q1을 올리고 late third를
각각 +1.054/+0.849dB 회복하는 Pareto knee다. 사용자 요청의 핵심인 under-trained tail
회복을 우선해 **\(K_I=32,\beta=.05\)를 3F 사전 고정 transfer 값으로 선택**한다. 3F 결과를
본 뒤 값을 바꾸지 않는다.

이 결과는 앞부분 RR을 제안법으로 정당화하지 않는다. 앞부분은 topology confound를 없애는
공통 initialization contract이고, main comparison의 estimand는 동일 checkpoint 이후의
replay ordering 효과다. 실제 VIGS end-to-end에서는 기존 frontier mapping을 그대로 두고
첫 replay service부터 baseline causal RR 또는 제안 sampler를 사용해야 한다.

### Loop 11 — 3F transfer 실패와 loss-calibrated count softmax

사전 고정한 \(K_I=32,\beta=.05\)의 3F shared-topology transfer는 실패했다. 두 arm은
동일 checkpoint에서 branch했고 최종 Gaussian 수도 정확히 410,985개다.

| Iter. | overall delta | worst-Q1 delta | RR-hard-Q1 delta | thirds delta (early/mid/late) |
|---:|---:|---:|---:|---:|
| 30k | −.382 | −.269 | −.171 | −.888/−.253/−.005 |
| 45k | −.146 | +.219 | +.289 | −.946/+.207/+.301 |
| 60k | −.027 | +.189 | +.284 | −.705/+.402/+.222 |
| 79,081 | −.254 | +.073 | +.118 | −.953/−.012/+.204 |

후보는 final count CV를 .432→.263으로 낮추고 RR의 temporal count thirds
27.41/16.24/12.03을 23.65/17.46/14.58로 보정했다. 그러나 early view에서 빼 온 약
3.76 update/frame의 품질 손실이 mid/late의 이득보다 컸다. 즉
“낮은 lifetime count = 높은 현재 marginal utility”라는 count-only 가정이 틀렸다.
3F 결과를 이유로 \(\beta\)만 다시 고르는 것은 하지 않는다.

다음 최소 수정은 관측 가능한 photometric residual로 count pressure를 보정한다. interval
\(j\)의 member 수, 누적 service, per-observation EMA loss를 각각 \(|G_j|,c_j,\bar\ell_j\)라 하면

\[
w_j
=|G_j|\exp\!\left[-\beta\left(\frac{c_j}{|G_j|}-r_{\min}\right)\right]
\bar\ell_j^{\alpha}.
\]

이 weight로 매 block에서 \(K_I=32\)개 interval을 Plackett–Luce 비복원 추출하고, interval
내 frame은 기존 persistent RR로 선택한다. \(\beta\)는 exposure 균형, \(\alpha\)는 동일
count에서 residual 비율이 selection odds에 미치는 정도다. 처음 보는 interval은 관측된
EMA loss의 median을 써서 loss term을 중립화한다. 단순 lifetime count만으로 복구 불가능한
late geometry에 compute를 쓰는 문제를 줄이면서 비복원 mixing은 보존한다.

shared-topology development sweep은 305·12F에서 다음 세 설정만 비교한다:
\((\beta,\alpha)\in\{(.02,.5),(.02,1),(.05,.5)\}\). 여기서 공통값을 고른 뒤 3F에 다시
재튜닝 없이 전이한다. 이 역시 `staged_*` 클래스는 checkpoint 재현용 harness일 뿐이며,
제안 sampling law는 위의 단일 식이다. 구현 후 scheduler 단위 테스트는 23개 모두 통과했다.

#### 사용자 검토에 따른 loss term 비채택

loss-calibrated arm 6개는 학습까지 완주했지만, loss를 넣는 순간 count balancing의 효과와
hard-example mining의 효과를 분리할 수 없어 논문 논리가 흐려진다는 사용자 지적을 받아들였다.
held-out 렌더 sweep은 중단하고 이 arm은 원인 진단으로만 보존한다. **주 방법에는 image loss,
gradient norm, residual priority를 넣지 않는다.**

### Loop 12 — bounded normalized-count interval RR

3F 실패에서 고칠 것은 loss가 아니라 fixed \(\beta\)의 단위 문제다. raw per-member count
\(r_j=c_j/|G_j|\)의 범위는 장면 길이와 시점에 따라 달라지므로 같은 \(\beta\)도 실제 최대/최소
odds를 장면마다 다르게 만든다. 이를 다음처럼 무차원화한다.

\[
z_j=\frac{r_j-r_{\min}}{r_{\max}-r_{\min}+\epsilon},\qquad
w_j=|G_j|\exp(-\gamma z_j).
\]

따라서 count correction의 최대 odds ratio는 항상 \(e^\gamma\) 이하이고 absolute count나
trajectory 길이에 무관하다. count span이 0이면 정확히 interval-size base law로 돌아간다.
outer \(K_I=32\) Plackett–Luce 비복원 block과 inner frame RR은 그대로다. 이는 loss term 없이
early interval의 service를 지나치게 빼앗던 raw-count softmax의 문제만 직접 고친다.

개발 sweep은 해석 가능한 세 odds cap만 사용한다:
\(e^\gamma\in\{2,4,8\}\), 즉 \(\gamma\in\{\log2,\log4,\log8\}\). 305·12F에서 공통값을
선택하고, 사용자가 3F를 필수 성공 장면에서 제외하도록 범위를 조정했으므로 두 장면 반복 seed로
최종 검증한다. 3F는 topology/arrival stress control로 실패 결과를 그대로 남긴다. 구현 후
scheduler 회귀 테스트는 25개 모두 통과했다.

#### Seed 0 결과와 odds cap 선택

두 arm의 Gaussian 수는 305에서 모두 592,695개, 12F에서 모두 291,453개였다. 아래 delta는
동일 checkpoint의 causal RR 대비 값이다.

| Scene | odds cap | 30k overall | 45k overall | 45k worst-Q1 | 45k RR-hard-Q1 | 45k late | count CV | recent H |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 305 | **2×** | −.028 | +.105 | +.251 | +.704 | +.672 | .323 | **.9954** |
| 305 | 4× | −.177 | +.023 | +.170 | +.865 | +.983 | .260 | .9890 |
| 305 | 8× | −.252 | +.152 | +.330 | +1.029 | +1.206 | **.223** | .9876 |
| 12F | **2×** | +.156 | **+.087** | +.435 | +.534 | +.633 | .527 | **.9957** |
| 12F | 4× | +.144 | +.067 | +.473 | **+.702** | **+.812** | .477 | .9912 |
| 12F | 8× | **+.311** | +.039 | **+.479** | +.605 | +.797 | **.436** | .9881 |

세 cap 모두 45k overall과 자체 worst-Q1을 두 장면에서 동시에 개선했다. 그러나 2×는 두 장면
모두 recent-1024 temporal entropy 0.995 이상, interval-block duplicate 0을 유지하고 30k
overall도 평균적으로 양수다. 보정 강도가 가장 작아 early 희생과 parameter sensitivity도 가장
낮다. 따라서 **\(K_I=32,\gamma=\log2\)**를 seed 1 반복 검증 전에 고정한다. seed 1은 seed 0
checkpoint를 재사용하지 않고, 각 장면의 causal-RR 공통 topology checkpoint부터 새로 만들어
prefix camera order와 model state가 정확히 대응하도록 한다.

### Loop 13 — post-arrival polishing 폐기와 pure-online zero-tail 재정의

사용자 검토에서 30k/45k 결과는 마지막 training view가 도착한 뒤 여러 full-pool-equivalent
replay를 추가로 주므로 실제 online scheduler 차이를 약하게 만든다는 문제가 확인됐다. 따라서
shared-checkpoint, 1/2/4-epoch tail polish, topology 종료 뒤 sampler 전환은 최종 방법 evidence에서
모두 제외한다. 최종 비교는 다음 계약만 사용한다.

1. training view는 자신의 causal arrival에 즉시 admission한다. maturity gate와 pending pool은 없다.
2. 첫 update부터 마지막 update까지 하나의 동일 sampler만 쓴다.
3. 총 update 수는 마지막 training-view arrival과 정확히 같다. 이후 update는 0회다.
4. RR와 후보는 같은 data/pose/init/resolution/update 수로 각각 독립 학습한다.
5. 품질은 학습에 쓰지 않은 llffhold-8 held-out view로만 평가한다.

장면별 zero-tail budget은 305가 \(T=18{,}661,N=2{,}352\), 12F가
\(T=24{,}421,N=1{,}925\), 3F가 \(T=36{,}481,N=4{,}260\), 추가 1253이
\(T=8{,}821,N=1{,}140\)이다. 자동 감사에서 모든 arm에
`total_iterations == max(arrival_iteration)`가 성립했다.

### Loop 14 — 단일 relative-floor interval softmax RR

고정 two-pass target은 장면의 평균 service가 달라지면 너무 일찍 꺼지는 문제가 있었다. 이를
절대 count가 아닌 현재 평균 대비 상대 부족분 하나로 바꿨다. interval \(G_j\)의 누적 service를
\(c_j\), member당 service를 \(r_j=c_j/|G_j|\), 현재 전체 frame 평균을
\(\mu_t=\sum_jc_j/\sum_j|G_j|\)라 하면

\[
h_t=\rho\mu_t,\qquad
d_j=\left[1-\frac{r_j}{h_t}\right]_+,\qquad
w_j=|G_j|\exp(\gamma d_j).
\]

고정값은 \(\rho=1/2\), \(K_I=8\)이다. 매 block에서 전체 eligible interval을 알고
Plackett--Luce(Gumbel top-k)로 \(K_I\)개를 **비복원** 추출하고, interval 내부 frame도
persistent RR로 뽑는다. loss/residual/gradient/active bonus와 phase switch는 없다.
\(r_j\ge h_t\)면 frame-uniform base weight \(|G_j|\), 완전히 부족하면 최대 odds가
\(e^\gamma\)다. 이 식은

\[
p^*=\arg\max_p\{-D_{KL}(p\|q)+\gamma\mathbb E_p[d_j]\},
\quad q_j\propto|G_j|
\]

의 해 \(p_j^*\propto |G_j|e^{\gamma d_j}\)라서, 기존 softmax를 버린 것이 아니라
그 utility를 bounded·scale-free deficit으로 바꾼 형태다.

305/12F seed 0에서 2×와 4×를 먼저 비교했다. 2×는 12F에서 overall/worst-Q1/late가
각각 −.119/−.329/−.077dB라 약했고, 4×는 두 장면에서 lower-tail을 복구했지만 early를
과보정했다. 중간값 3×(`gamma=log(3)`)를 12F/1253에서 먼저 확인한 뒤 305와 3F에
그대로 transfer했다. 결과를 본 뒤 장면별 파라미터를 바꾸지 않았다.

### Loop 15 — 선택값 \(K_I=8,\rho=.5,\gamma=\log3\), zero-tail 최종 결과

아래는 제안법−causal RR의 held-out PSNR이다. Worst-Q1은 각 결과 자체의 하위 25%,
RR-hard-Q1은 RR에서 정한 하위 25% frame을 고정해 후보에서 다시 측정한 값이다.

| Scene | Seed | RR | Proposed | Overall Δ | Worst-Q1 Δ | RR-hard-Q1 Δ | Late-third Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| 305 | 0 | 32.154 | 32.641 | **+.487** | **+1.081** | **+1.382** | **+.594** |
| 305 | 1 | 31.999 | 32.764 | **+.765** | **+1.286** | **+1.734** | **+.914** |
| 12F | 0 | 27.021 | 27.244 | **+.222** | **+.668** | **+.856** | **+.493** |
| 12F | 1 | 26.905 | 27.203 | **+.298** | **+.310** | **+.440** | **+.555** |
| 3F | 0 | 28.676 | 28.768 | **+.093** | **+.203** | **+.397** | **+.196** |
| 3F | 1 | 28.735 | 28.828 | **+.093** | **+.378** | **+.571** | **+.383** |

메인 3장면×2 seed에서 overall/worst-Q1/RR-hard-Q1/late-third가 전부 **6/6 양수**다.
평균 delta는 각각 **+.326/+.654/+.897/+.522dB**이고, 가장 작은 overall도 +.093dB다.
따라서 “late만 올리고 평균은 숨긴다”가 아니라 메인 세 장면에서는 기존 평균 PSNR까지 모두
RR를 이겼다.

사전 선언한 추가 1253 transfer에서는 seed 0/1 overall이 −.068/+.049dB로 평균 −.009dB,
사실상 동률이었으나 worst-Q1은 +.539/+1.046dB, RR-hard-Q1은 +.952/+1.604dB,
late-third는 +.910/+1.312dB였다. 즉 이 장면은 early→late 품질 재분배가 강하며 universal
overall win이라고 쓰면 안 된다.

Scheduler 감사 결과 메인 6 run의 count CV 평균은 RR .9793→후보 .8835로 감소했다.
동적 128-update temporal entropy ratio는 RR .9719→후보 .9616으로 약 1.0%p 낮아졌으므로
“RR보다 entropy가 높다”고 주장하지 않는다. 대신 절대 entropy 약 96%를 유지했고, 후보의
20,512개 native interval block에서 interval duplicate는 정확히 0이었다. 즉 gain은 무질서도를
최대화해서가 아니라 **높은 mixing을 거의 유지하면서 심각하게 under-served한 interval에만
bounded correction을 준 결과**로 해석한다.

후보는 메인 6 run 평균 Gaussian 수를 428,857→445,733(+3.9%)로 바꿨다. pure-online
end-to-end 효과에는 이 topology 경로도 포함되므로 결과 자체는 유효하지만, 고정 topology에서
replay 순서만의 효과라고 주장할 수는 없다. 또한 이 ablation은 fixed VIGS pose/init를 쓰는
3dgs-custom causal offline harness이며 RGB+IMU-only full strict VIGS-SLAM 결과는 아니다.

**최종 판정:** goal의 “하나의 count-balanced softmax가 causal RR를 세 장면에서 이김”은
zero-tail·두 독립 seed·held-out overall 기준으로 달성했다. 채택 후보는
`relative_floor_interval_softmax_rr(K=8, rho=.5, gamma=log(3))`다. Admission은 별도
GPU-token controller를 섞지 않고 이 ablation에서는 모든 causal arrival을 즉시 받는다.
Production VIGS 이식 전에는 실제 online pose와 고정 wall-clock budget에서 동일 식을 재검증한다.

재현 및 evidence:

- `run_zero_tail_relative_floor_odds3.sh`
- `run_zero_tail_relative_floor_odds3_transfer.sh`
- `analyze_zero_tail_selected.py`
- `evidence/zero_tail_selected_summary.json`
- `evidence/zero_tail_selected_ablation.png`
