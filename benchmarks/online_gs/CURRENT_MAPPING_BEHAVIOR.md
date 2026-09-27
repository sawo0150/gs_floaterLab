# 현재 gsSLAM mapping 동작 — exp94 공식 코드 기준

> 기준일: 2026-09-24  
> 대상: 논문 main-result인 **exp94 normalized-variance ERCB B-track**  
> 목적: 코드를 개발하지 않은 동료 연구자가 “어떤 frame을 언제, 얼마나,
> 어떤 loss로 학습하는가”를 한 문서에서 이해할 수 있게 한다.

## 1. 한 문장 요약

현재 mapper는 각 유효 mapping packet마다 **기존 VIGS의 multi-keyframe native
mapping을 먼저 전부 수행**하고, 그 뒤에 **intermediate RGB 1장**과 **보조
keyframe 1장**을 각각 독립적인 single-view appearance Adam step으로 추가한다.
FRONTIER/BALANCED 상태는 이 작업량을 나누는 scheduler가 아니라, 현재 공식
설정에서는 **densify/prune 허용 여부와 과거 keyframe 선택 방식만 바꾸는
상태표시자**다.

17개 scene 실측을 합치면 다음과 같다.

| 기준 | Native keyframe mapping | Intermediate dense | Auxiliary keyframe |
|---|---:|---:|---:|
| Adam step | 34,865 (82.13%) | 3,793 (8.94%) | 3,793 (8.94%) |
| training render | 527,484 (98.58%) | 3,793 (0.71%) | 3,793 (0.71%) |

따라서 **Adam step 기준** intermediate 비중은 8.94%지만, native Adam 하나가
평균 15.13개의 keyframe view를 동시에 렌더하기 때문에 **physical render 기준
intermediate 비중은 0.71%**다. 이 둘을 섞어서 “dense 사용 비율”이라고 부르면
안 된다.

## 2. 이 문서가 설명하는 정확한 버전

현재 `/home/intern/VIGS-SLAM-paper-full` checkout은 `816832e6`이며, 이는 exp94
mapper clean commit `ce25ad7f`의 문서-only descendant다. 현재 두 핵심 mapper
파일은 exp94 source lock과 byte-identical하다.

| 파일 | exp94/current SHA-256 |
|---|---|
| `vigs/gs_backend.py` | `97fbc00b85b9241ea73b7b97e152fbf8ed7b83bc142990a01fa9ae81b15c5853` |
| `vigs/map_scheduler.py` | `7495509ff5bd784d82782b48085f5c76c3e40e9ad875f1fa67b854d8f9c0d050` |

공식 candidate 명령의 핵심 flag는 다음과 같다.

```text
--time-scale unbounded
--fixed-event-dense-opportunities-per-packet 1
--compute-paced-dense-admission
--compute-paced-dense-token-cost 1
--c1-c2-global-residue-integration
--service-shortfall-ercb
--stage6r-keyframe-appearance-replay
--stage6r-native-global-keyframe-selection-audit
--stage6r-native-global-keyframe-ercb
--density-policy online_rank
--online-density-mean-multiplier 2.5
--online-density-span 2.0
--dense-replay-scope appearance
--profile dense_rr_imu
--observation-topology-gate
--ercb-selection-potential normalized_variance
```

중요하게도 **`--mapping-model-scheduler`는 없다.** 따라서 소스에 구현된
FRONTIER→BALANCED→REPLAY의 full work-allocation 기능은 이 결과에서 꺼져 있다.

## 3. 먼저 구분해야 하는 세 종류의 “scheduler”

| 층 | 하는 일 | exp94에서 실제 역할 |
|---|---|---|
| Timeline scheduler | frozen archive의 control, dense arrival, mapping packet을 timestamp 순서로 전달 | 인과 순서와 reset/rescale 경계를 보존 |
| Topology state controller | FRONTIER/BALANCED/REPLAY 상태를 관측 기반으로 갱신 | topology gate와 native historical-KF selector 전환에 사용 |
| ERCB selector | 이미 인과적으로 도착·admit된 후보 중 다음 학습 view를 선택 | dense, auxiliary-KF, native historical-KF 세 pool에 적용 |

즉 `BALANCED`는 “dense와 keyframe을 50:50으로 학습한다”는 뜻이 아니다.
현재 설정에서 regular packet의 작업량은 BALANCED 전후 모두 기본적으로
`native 7 + dense 1 + auxiliary-KF 1` Adam step이다.

## 4. 입력 view의 세 종류

| 종류 | 보유 supervision | Gaussian birth | 학습에서의 위치 |
|---|---|---:|---|
| Tracked keyframe | RGB + online depth + normal + tracker pose | 있음 | native current window, native historical pool, auxiliary-KF pool |
| Intermediate dense frame | RGB + 양쪽 causal KF로 만든 pose, IMU rotation shaping | 없음 | admit된 일부만 별도 1-view appearance step |
| Fixed held-out frame | 평가 RGB/pose | 없음 | 모든 mapping·birth·selector pool에서 제외 |

여기서 `dense`는 depth가 촘촘하다는 뜻이 아니라, **tracker keyframe 사이에 도착한
RGB intermediate frame을 더 촘촘히 사용한다**는 뜻이다. 이 view는 mapping에
사용될 때도 RGB-only이며 Gaussian geometry supervision으로 사용되지 않는다.

## 5. 전체 실행 흐름

```text
frozen causal tracker archive
        │
        ├─ control: IMU metric rescale / mapper reset
        ├─ dense arrival: 두 causal KF 사이의 intermediate RGB 후보 적재
        └─ mapping packet
             │
             ├─ held-out UID 제거, IMU metric init 전 packet은 skip
             ├─ 새 tracked KF의 Gaussian birth
             ├─ native mapping
             │    ├─ init packet: floor(600 / current-window-size) Adam
             │    ├─ regular packet: 7 Adam
             │    └─ pose-scale correction: 20 Adam, 최대 12 views/Adam
             ├─ C1이 허용한 intermediate RGB 1장
             │    └─ 1 render + 1 appearance-only Adam
             └─ C1이 허용한 keyframe 1장
                  └─ 1 render + 1 appearance-only Adam

end of sensor stream → 추가 optimizer step 0 → saved PLY → held-out evaluation
```

17개 scene에서 archive event 3,989개 중 실제 학습 packet은 3,793개였다.

| event 종류 | 수 | packet당 native work | 비고 |
|---|---:|---:|---|
| IMU metric init 전 keyframe update | 135 | 0 | 정책상 skip |
| Mapper reset | 44 | 0 | 새 map generation 시작 |
| Metric rescale | 17 | 0 | scale control |
| Generation 첫 keyframe packet | 44 | 54/60/66/75 Adam | `floor(600 / window)` |
| 일반 keyframe packet | 3,281 | 7 Adam | main online mapping 경로 |
| Pose-scale correction | 468 | 20 Adam | 최대 12 keyframe views/Adam |

각 3,793개 학습 packet 뒤에 dense 1회와 auxiliary-KF 1회가 모두 완료되어,
총 `map()` 호출은 정확히 `3,793 × 3 = 11,379`회였다.

## 6. Native mapping 한 iteration에서 무슨 일이 일어나는가

### 6.1 View 구성

설정은 `window_size: 10`, `n_global_views: 6`이다. 다만 현재 window 갱신 코드가
`len(current_window) > window_size`일 때만 잘라내므로, steady state의 실제
current window는 **최대 11장**이다. 따라서 일반 native iteration은 보통:

```text
최근/current keyframe 최대 11장
+ window 밖 historical keyframe 최대 6장
= 최대 17 keyframe renders → loss 합산 → Adam step 1회
```

이 off-by-one은 17-scene 로그에서도 확인된다. 일반 7-step packet의 native
render는 Adam당 평균 **16.94장**이었다. 이를 10장 window라고 가정해 계산하면
현재 결과의 실제 work를 잘못 설명하게 된다. 이 코드를 10장으로 고치면 알고리즘과
physical render budget이 달라지므로 exp94 재현이 아니다.

| Native 경로 | events | Adam | renders | renders/Adam |
|---|---:|---:|---:|---:|
| Generation init | 44 | 2,538 | 26,160 | 10.31 |
| Regular mapping | 3,281 | 22,967 | 389,004 | 16.94 |
| Pose-scale correction | 468 | 9,360 | 112,320 | 12.00 |
| **합계** | **3,793** | **34,865** | **527,484** | **15.13** |

### 6.2 Loss와 parameter update

Native keyframe view는 다음 supervision을 사용한다.

- RGB mapping loss: L1 + DSSIM (`lambda_dssim=0.2`)
- online keyframe depth loss
- normal loss (`lambda_dnormal=0.5`, mapper 내부에서 `/10` scale)
- native iteration에만 isotropic-scale prior

여러 view loss는 native Adam step에서 **합(sum)**으로 들어가며 view 수로 평균내지
않는다. 한 native Adam과 한 single-view dense Adam은 optimizer step 수는 각각
1이지만, render 수와 gradient scale, 계산량이 동등하지 않다.

Native step은 xyz, SH/color, opacity, scale, rotation을 모두 갱신할 수 있다.
반면 뒤의 두 replay step은 하네스가 gradient를 `f_dc`, `f_rest`에만 남기므로
**appearance-only**다. opacity도 갱신하지 않는다.

`kernel_batch_render=true`는 한 native iteration의 여러 카메라를 CUDA batch로
렌더하는 실행 최적화다. 논리적인 physical render 수는 여전히 카메라 수만큼 센다.

## 7. Gaussian birth와 topology

### 7.1 새 Gaussian birth

새 tracked keyframe이 들어오면 online depth에서 point를 만들고 PPM sampling으로
Gaussian을 추가한다. 고정된 Aria 전용 curve 대신 현재까지 관측한 RGB Sobel 평균의
causal rank를 사용한다.

\[
m_t=\operatorname{clip}\left(2.5+2.0(q_t-0.5),\;0.35,\;3.0\right),
\]

여기서 \(q_t\)는 현재 frame까지의 causal mid-rank다. dataset 이름, 전체 stream
길이, 미래 frame은 쓰지 않는다. 17개 scene 2,885개 tracked keyframe에서 실제
multiplier는 평균 **2.463**, 최소 **1.503**, 최대 **3.000**이었다.

### 7.2 Densify/prune

- native iteration counter가 `150k + 50`에 도달할 때 densify/prune을 시도한다.
- intermediate/auxiliary appearance step은 이 topology counter를 올리지 않는다.
- FRONTIER에서는 native render의 densification statistic을 모으고 topology를 허용한다.
- BALANCED 이후 observation gate가 densify/prune과 statistic 축적을 막는다.
- 하지만 **새 keyframe birth 자체는 BALANCED 이후에도 계속된다.** topology gate는
  native densify/prune gate이지 birth freeze가 아니다.
- `gaussian_reset=2,000,000,001`이어서 이 실험 길이에서는 주기적 opacity reset은
  사실상 꺼져 있다.
- carve loss와 hard floater pruning도 이 exp94 recipe에서는 꺼져 있다.

따라서 최종 Gaussian 수 증가는 주로 **계속되는 keyframe birth + 초기 FRONTIER
densification**에서 오며, intermediate appearance step이 Gaussian을 새로 만들거나
geometry를 직접 이동시켜서 생기는 것이 아니다.

## 8. Intermediate dense frame: C1 admission과 ERCB selection

Intermediate frame은 “도착”, “admit/register”, “실제 선택”의 세 단계를 구분해야
한다.

- **C1**: 제한된 GPU work로 어떤 도착 view를 실제 training pool에 넣을지 결정
- **C2 / ERCB**: 이미 C1을 통과한 pool에서 다음에 학습할 view의 순서를 결정

### 8.1 도착과 C1 admission

1. 두 causal keyframe endpoint 사이에 도착한 intermediate UID를 모은다.
2. 각 interval 안에서는 endpoint와 기존 선택점에서 가장 멀리 떨어진 frame부터
   고르는 1-D temporal maximin 순서를 만든다. 이는 **pool membership 순서**일 뿐
   optimizer의 학습 순서는 아니다.
3. map generation당 전역 bootstrap 1장을 무료 admit한다.
4. 그 뒤에는 **완료된 dense Adam 1회가 pending dense 1장**을 admit한다
   (`token_cost=1`). pending이 없을 때 생긴 credit은 미래 frame에 이월하지 않는다.
5. 여러 interval에 pending이 있으면 현재 admit 수가 가장 적은 interval부터
   water-fill한다.

이 구조 때문에 카메라가 많이 도착해도 전부 VRAM/training pool에 올리지 않는다.
17개 scene에서 38,675장 중 3,810장, 즉 **9.85%만 register**되었다.

### 8.2 Normalized-variance ERCB

Admit된 view 중 실제 한 장을 뽑을 때는 다음 per-view Gibbs 법칙을 쓴다.

\[
p_i \propto
\exp\left[-\frac{\log(1.5)}{T+1}n_i\right],
\]

여기서 \(n_i\)는 view \(i\)의 완료된 service 수이고
\(T=\sum_j n_j\)다. 이는 `Var(count)/mean(count)` potential의 증가량에서 나온
normalized-variance selector다. 학습이 진행될수록 \(1/(T+1)\) 때문에 balancing
strength가 약해진다. 이 값을 상쇄하는 scene별 temperature는 없다.

추가 제약은 다음과 같다.

- block size 8의 Gumbel-top-k ordering
- global growing residue 안에서는 모든 현재 member가 한 번 서비스되기 전 반복 금지
- 새 arrival은 진행 중 residue에 합류하지만 이미 materialize된 block은 바꾸지 않음
- 선택 count는 draw 시점이 아니라 해당 Adam step이 실제 완료된 뒤 commit
- loss, image content, scene 이름, 미래 horizon은 selector가 보지 않음

그러므로 ERCB는 **interval 기반 admission + per-view selection**이다. Interval 자체를
Gibbs로 뽑는 알고리즘이라고 쓰면 현재 구현과 다르다.

## 9. 두 종류의 keyframe 재사용

### 9.1 Auxiliary keyframe appearance step

Dense step과 별개인 keyframe 전용 C1/C2 queue가 있다.

- 각 map generation에서 keyframe 1장을 bootstrap admit
- 완료된 auxiliary-KF service 1회당 기다리는 keyframe 최대 1장 admit
- 매 유효 packet 뒤 1장 선택, 1 render, 1 appearance-only Adam
- dense와 별도 selection count, RNG, LR clock을 사용
- 같은 normalized-variance 법칙과 global no-repeat residue를 사용

17개 scene에서 tracker keyframe 2,885개 중 2,403개, 즉 **83.29%가 이 보조
경로에서 적어도 한 번 선택**되었다. 총 service는 3,793회다.

### 9.2 Native historical keyframe

Regular native step은 current window 밖의 과거 keyframe을 최대 6장 추가한다.

- FRONTIER: 기존 `torch.randperm` 균일 무작위 선택
- BALANCED/REPLAY: transactional normalized-variance ERCB 선택
- 한 native Adam에 필요한 최대 6장을 유지하기 위해 residue epoch 경계를 넘어갈 수 있음
- 선택된 6장은 current-window keyframe들과 **같은 native multi-view Adam**에 들어감
- Adam이 성공한 뒤에만 6개 service count를 commit

전체 regular native 22,967 step에서 historical-keyframe service는 136,451회,
즉 audited step당 평균 **5.94장**이었다. 초기 pool이 작은 구간 외에는 사실상
6개 slot이 유지된다는 뜻이다.

## 10. FRONTIER / BALANCED / REPLAY의 정확한 의미

Controller의 설계상 상태 정의는 다음과 같다.

| 상태 | 관측 의미 | 현재 exp94에서 바뀌는 것 |
|---|---|---|
| FRONTIER | topology capacity가 아직 안정됐다고 볼 증거가 부족 | densify/prune 허용, native historical KF는 uniform |
| BALANCED | topology 관측 2회 이상 + 직전 prune 전 capacity 회복 | densify/prune 정지, native historical KF에 ERCB 활성화 |
| REPLAY | dense opportunity pass가 추가로 충분히 완료 | full scheduler라면 replay가 work를 소유하지만 exp94에서는 그 allocator가 꺼져 있음 |

FRONTIER→BALANCED는 frame 번호나 scene별 cutoff가 아니라 다음 관측으로 결정한다.

1. 독립적인 topology event를 최소 2회 관측
2. 최근 net-prune 직전 Gaussian capacity까지 다시 회복

그러나 exp94는 `--mapping-model-scheduler`를 켜지 않았으므로 BALANCED가 되어도:

- regular native 7 iteration을 sqrt(window)로 줄이지 않음
- native work를 replay iteration으로 대체하지 않음
- worker saturation에 따라 work 비율을 바꾸지 않음
- 별도 idle replay를 돌리지 않음 (`idle_replay_calls=0`)

즉 현재 결과에서 state는 **work allocator가 아니라 topology/selector gate**다.

17-scene regular mapping audit는 다음과 같다. Init과 20-step pose correction은 이
native-global audit의 대상이 아니므로 분모는 regular 22,967 step이다.

| 상태 | Regular packets | Audited native iterations | 비율 |
|---|---:|---:|---:|
| FRONTIER | 453 | 3,171 | 13.81% |
| BALANCED | 2,828 | 19,796 | 86.19% |
| REPLAY | 0 | 0 | 0.00% |

`Regular packets`는 각 7-step call의 첫 audited iteration에서 관측한 상태로
분류했다. 이 panel에서는 packet 중간에 상태가 갈린 경우가 없어 iteration count도
각각 packet 수의 정확히 7배다.

최종 상태는 17 scene 중 15개가 BALANCED, 짧은 UTMM `fast-straight`와
`slow-straight-2` 2개가 FRONTIER였다.

## 11. 17-scene 실측: 후보 pool과 실제 사용률

아래 비율은 scene 평균의 평균이 아니라 모든 scene count를 합친 work-weighted
수치다.

| Dataset | Scenes | Tracked KF | Dense arrived | Dense registered | Dense selected unique | Aux-KF selected unique |
|---|---:|---:|---:|---:|---:|---:|
| RPNG | 8 | 2,368 | 29,830 | 3,258 (10.92%) | 3,235 (10.84%) | 1,987 (83.91%) |
| UTMM | 7 | 308 | 5,887 | 313 (5.32%) | 296 (5.03%) | 254 (82.47%) |
| Aria | 2 | 209 | 2,958 | 239 (8.08%) | 235 (7.94%) | 162 (77.51%) |
| **전체** | **17** | **2,885** | **38,675** | **3,810 (9.85%)** | **3,766 (9.74%)** | **2,403 (83.29%)** |

`selected unique / arrived`가 낮은 주된 이유는 ERCB가 frame을 버려서가 아니라,
그 앞단의 **compute-paced C1 admission budget**이 pool membership을 제한하기
때문이다. ERCB는 admit된 pool 안의 순서를 균형화한다.

## 12. 17-scene 실측: 학습량 비율

| Dataset | Native Adam | Dense Adam | Aux-KF Adam | Native renders | Dense renders | Aux-KF renders |
|---|---:|---:|---:|---:|---:|---:|
| RPNG | 29,847 | 3,250 | 3,250 | 452,915 | 3,250 | 3,250 |
| UTMM | 3,093 | 306 | 306 | 43,803 | 306 | 306 |
| Aria | 1,925 | 237 | 237 | 30,766 | 237 | 237 |
| **전체** | **34,865** | **3,793** | **3,793** | **527,484** | **3,793** | **3,793** |

전체를 view source로 다시 묶으면:

- Adam 기준 keyframe 관련(native + auxiliary): **91.06%**
- Adam 기준 intermediate dense: **8.94%**
- Render 기준 keyframe 관련: **99.29%**
- Render 기준 intermediate dense: **0.71%**
- Keyframe : intermediate render service 비율: 약 **140.1 : 1**

이 수치는 “intermediate RGB contribution이 없다”는 뜻은 아니다. Single-view
appearance Adam은 native multi-view Adam과 optimizer dynamics가 다르고, 별도 LR
clock을 갖는다. 다만 논문에서 “dense frame을 다수 학습한다”거나 “학습 view의 큰
부분이 intermediate다”라고 서술하면 현재 구현의 물리적 render 비율과 맞지 않는다.

## 13. Scene별 원시 scheduling 요약

표의 `D A/R/S`는 dense arrived/registered/selected-unique, `Adam N/D/K`는
native/dense/aux-KF, `State F/B/R`은 regular native audit iteration 수다.

| Dataset/scene | KF | D A/R/S | Aux-KF unique | Adam N/D/K | State F/B/R | Final |
|---|---:|---:|---:|---:|---:|---|
| aria/aria1253 | 91 | 932/102/100 | 73 | 853/101/101 | 224/441/0 | BALANCED |
| aria/aria301_305 | 118 | 2026/137/135 | 89 | 1072/136/136 | 182/742/0 | BALANCED |
| rpng/table_01 | 210 | 1728/270/267 | 188 | 2492/269/269 | 210/1400/0 | BALANCED |
| rpng/table_02 | 289 | 1999/383/380 | 275 | 3465/382/382 | 189/2114/0 | BALANCED |
| rpng/table_03 | 430 | 5105/601/598 | 342 | 5524/600/600 | 189/3353/0 | BALANCED |
| rpng/table_04 | 345 | 4467/482/480 | 272 | 4397/481/481 | 210/2639/0 | BALANCED |
| rpng/table_05 | 273 | 4626/374/371 | 218 | 3389/373/373 | 266/1981/0 | BALANCED |
| rpng/table_06 | 186 | 1989/245/242 | 165 | 2226/244/244 | 224/1260/0 | BALANCED |
| rpng/table_07 | 173 | 3624/237/234 | 135 | 2219/236/236 | 259/1162/0 | BALANCED |
| rpng/table_08 | 462 | 6292/666/663 | 392 | 6135/665/665 | 231/3682/0 | BALANCED |
| utmm/ego-centric-1 | 43 | 1146/41/39 | 39 | 386/40/40 | 168/98/0 | BALANCED |
| utmm/ego-centric-2 | 45 | 979/50/48 | 37 | 461/49/49 | 196/133/0 | BALANCED |
| utmm/ego-drive | 67 | 998/77/73 | 56 | 746/76/76 | 217/273/0 | BALANCED |
| utmm/fast-straight | 10 | 226/5/3 | 3 | 164/4/4 | 14/0/0 | FRONTIER |
| utmm/slow-straight-2 | 14 | 406/5/2 | 2 | 169/4/4 | 7/0/0 | FRONTIER |
| utmm/square-1 | 71 | 1219/72/70 | 70 | 615/71/71 | 189/294/0 | BALANCED |
| utmm/square-2 | 58 | 913/63/61 | 47 | 552/62/62 | 196/224/0 | BALANCED |

각 scene의 render 수, 최종 Gaussian 수와 품질은 공식 결과표
`context/experiments/benchmark_custom/metric_benchmark_v2_fixed_eval_20260917/summary.md`
에서 함께 볼 수 있다.

## 14. 현재 설정에서 켜지지 않은 것

코드에 존재한다고 해서 exp94 결과에 모두 들어간 것은 아니다.

| 기능 | exp94 상태 |
|---|---|
| Full FRONTIER/BALANCED/REPLAY work allocator | OFF |
| Idle/background replay | 실측 0회 |
| Dense view의 full geometry update | OFF; SH appearance만 |
| Dense view의 native global slot 참여 | OFF (`fixed_work_dense_global_views=0`) |
| Auto topology freeze | OFF; observation gate만 사용 |
| Frame/scene별 topology cutoff | 없음 |
| Background polish / final color refinement | OFF |
| Carve loss / hard floater pruning | OFF |
| Post-EOS optimization | 0회 |

## 15. B-track 결과를 해석할 때의 경계

이 실행은 `time_scale=unbounded`인 **causal mapping-only fixed-work benchmark**다.

- 같은 frozen causal tracker packet을 candidate와 vanilla가 공유한다.
- 미래 frame과 held-out supervision을 사용하지 않는다.
- 마지막 sensor frame 이후 optimizer update는 0이다.
- candidate가 실제 완료한 physical render 수를 vanilla가 맞춘다.
- candidate와 vanilla의 Adam step 수는 같을 필요가 없다. 한 Adam에 묶는 view 수가
  다르므로 render가 공정성의 물리 단위다.

하지만 tracker와 mapper가 실제 wall-clock에서 GPU를 경쟁하고 deadline을 지키는
strict live C-track 증거는 아니다. 명령에 `--deadline-reserve-ms 20`이 남아 있어도
deadline 자체가 `unbounded`라 이 결과에서는 실시간 제한으로 작동하지 않는다.

## 16. 코드에서 어디를 보면 되는가

| 질문 | 파일과 위치 |
|---|---|
| 새 KF, current window, init/7/20-step dispatch | `/home/intern/VIGS-SLAM-paper-full/vigs/gs_backend.py:5832`, `:6040` |
| state가 full allocator와 분리되는 지점 | `/home/intern/VIGS-SLAM-paper-full/vigs/gs_backend.py:6823` |
| current + historical KF batch 구성 | `/home/intern/VIGS-SLAM-paper-full/vigs/gs_backend.py:6938`, `:7137` |
| RGBD/normal vs RGB-only loss | `/home/intern/VIGS-SLAM-paper-full/vigs/gs_backend.py:6303` |
| topology cadence와 Adam commit | `/home/intern/VIGS-SLAM-paper-full/vigs/gs_backend.py:7714`, `:7816` |
| temporal maximin과 C1 admission | `/home/intern/VIGS-SLAM-paper-full/vigs/map_scheduler.py:161`, `:299` |
| dense normalized ERCB | `/home/intern/VIGS-SLAM-paper-full/vigs/map_scheduler.py:1660` |
| auxiliary-KF C1/C2 | `/home/intern/VIGS-SLAM-paper-full/vigs/map_scheduler.py:2353` |
| native historical-KF ERCB | `/home/intern/VIGS-SLAM-paper-full/vigs/map_scheduler.py:2635` |
| topology state machine | `/home/intern/VIGS-SLAM-paper-full/vigs/map_scheduler.py:3457` |
| online-rank birth와 appearance gradient mask | `benchmarks/online_gs/exp78b_replay_gsslam_mapping.py:140`, `:1018` |
| packet 뒤 dense 1 + KF 1 실행 | `benchmarks/online_gs/exp78b_replay_gsslam_mapping.py:2665` |
| 공식 flag 묶음 | `benchmarks/online_gs/run_exp78b_stage6rx4_cross_sequence.py:95` |

가장 직접적인 실행 증거는 각 scene의
`normalized_variance_s0/mapping_replay_runtime.json`이다. 예를 들어:

```text
results/experiments/exp94_normalized_metric_v2_fixed_eval/
  rpng/table_01/normalized_variance_s0/mapping_replay_runtime.json
```

여기서 `events`, `fixed_event_dense_opportunity_ledger`,
`fixed_event_keyframe_opportunity_ledger`,
`stage6r_native_global_keyframe_selection_ledger`를 함께 봐야 Adam, render, selector,
state 비율을 재구성할 수 있다.

## 17. 연구 관점에서의 가장 중요한 결론

1. 현재 성능 이득의 backbone은 여전히 **큰 keyframe birth + full native
   multi-keyframe mapping**이다.
2. ERCB는 이 backbone을 대체하지 않고 세 곳의 view ordering을 보강한다.
3. Intermediate frame은 arrival 수는 매우 크지만 C1 때문에 약 10%만 admit되며,
   physical render의 0.71%를 차지한다.
4. 현재 BALANCED는 “replay 중심 학습”이 아니라 **topology를 닫고 historical-KF
   selection을 ERCB로 전환한 상태**다.
5. 따라서 contribution을 설명할 때는 “dense replay가 대부분의 학습을 소유한다”보다
   **제한된 별도 appearance update와 coverage-aware keyframe 재사용을 기존 native
   mapper에 결합한다**고 쓰는 것이 현재 코드에 정확하다.
