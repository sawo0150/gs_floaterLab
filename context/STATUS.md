# STATUS — 현재 상태 (1페이지 엄수)

> 마지막 갱신: 2026-07-29. 이 문서가 넘치면 내용을 `knowledge/` 또는 `rounds/`로 밀어낸다.

## 현재 1차 목표

**30dB보다 먼저 pure-online strict streaming held-out 27dB를 달성한다.**
판정 계약은 timestamp 순 Aria RGB photo+IMU only, MPS 후처리 입력 0개,
fixed 1.5×(length1253 기준 97.65초 이내), 마지막 센서 frame 뒤 optimizer
update 0회이며, fixed evaluator 252장은 Gaussian mapping supervision에서도
완전히 제외한다. 현재 단일-run best는 26.535dB로 0.465dB가 남았다.
다만 직접 영향 late bin은 악화한 run이므로 27dB는 반복 검증해야 한다.
27dB 달성·반복 검증 전에는 hard carve/floater pruning을 품질 레버로 섞지
않으며, carve 검증과 동일 strict 조건의 30dB+는 그 다음 단계로 둔다.

> **2026-07-29 최신 목표 판정 정정:** 아래 과거 Best 표의 26.535dB는
> 최신값이 아니다. strict-disjoint 단일 최고는 late-iters3의
> **27.0039dB**이나 3회 중 1회만 27을 넘었고 평균은 **26.8419dB**라,
> 현재 목표는 **strict 27dB 반복 달성** 상태다. adaptive6500도
> 26.8067dB로 기각했다. MPS 후처리 입력은 계속 0개이며 30dB·carve는 후순위다.

> **2026-07-29 최신 목표 달성 정정:** 삭제될 pre-IMU Gaussian mapping을
> IMU metric 초기화 뒤로 미루자 strict-disjoint fixed가
> **27.0039/27.0371dB**로 2/2 재현됐다(평균 27.0205). 두 run 모두
> RGB+IMU only/MPS0/fixed 1.5×/97.65초 deadline/tail update 0 계약을
> 통과했다. **strict pure-online 27dB 1차 목표는 완료**했으며, 다음은 이
> 고품질 map 위에서 carve/floater 억제를 검증한 뒤 strict 30dB로 간다.

> **2026-07-29 최신 best 정정:** pre-IMU gate에 append-only PPM birth와
> post-freeze dense supervision을 유지한 채 freeze를 1050→850으로 앞당기자
> fixed가 **27.5822/27.6958dB**로 2/2 재현됐다(평균 **27.6390dB**).
> 97.282/97.200초, tail update 0, MPS 입력 0 계약을 모두 통과했다.
> 따라서 strict 27dB 1차 목표의 현재 recipe는 freeze850이며, 남은 품질 병목은
> frame1000–1199 **22.91–23.45dB**, 1200–1252 **19.38–19.51dB**인 후반
> coverage다.

> **2026-07-29 최신 best 추가 정정:** freeze 경계를 더 좁혀 800에서
> **27.8568/27.8361dB**를 재현했다(평균 **27.8464dB**, range 0.0207).
> freeze750은 27.6969로 다시 하락해 freeze800을 채택한다. 평가용 online
> depth-anchor carve proxy도 freeze800에서 **15,252/15,573개
> (26.72/27.04%)**로, 과거 freeze1050 anchor control 16,639개(28.98%)보다
> 평균 7.37% 적었다. MPS0, 97.65초 deadline, tail update 0은 모두 통과했다.

## 현재 Best

| 기준 | 실험 | PSNR@30k | 비고 |
|---|---|---:|---|
| **ORB 종합 챔피언** | **exp44d2 (RoMA+PPM 하이브리드 init + densify + carve)** | **33.799 (신기록)** | test 32.479(+0.93dB), 먼지 234, 14분 |
| **ORB fast-track** | **exp44d (하이브리드 init, 15k)** | 32.347 | 먼지 147, 학습 8분 |
| ORB baseline | exp30 / exp30r | 32.906 / 32.579 | run-to-run 노이즈 ±0.33dB 실측 |
| **MPS 트랙 채택** | exp08 (baseline) / **exp39b (carve softlite+force)** | 33.012 / **32.913** | **가시 먼지 96→0, 기여 6.42→0.21%** |
| Pop1 해결 | exp13 (camera-bound filter) | 32.855 | 확정 유지 |
| **Incremental 3DGS** | **exp51 축A+B (Photo-SLAM Replay, SLAM+PPM+depth λ=0.5+init dedup)** | **25.29dB** | **held-out 163뷰. D1-b(23.11) 대비 +2.42dB. 밀도(C)·예산(F) 둘 다 거의 무효과 — 시각진단으로 잔여 갭=depth-init 바늘형 floater 확정, 다음 축E(carve loss 이식)** |
| **Incremental 3DGS** | **exp50 Phase A&B (DiskChunGS)** | **-** | **RTX 5070 Ti 빌드 완주 및 euroc_stereo_inertial 예제 구현 성공 (Phase C 실행 준비)** |
| Incremental (자체) | exp48_v4 (PPM K=3 + RoMA + Selective Reset) | 18.23dB (median 18.27) | held-out 163뷰 평가, 리셋 차단으로 가우시안 116만 개 보존 |
| **Strict streaming 1.5×** | **exp57 fixed-eval exclusion + freeze1050/append birth/offsets1+4** | **strict-disjoint fixed 252-view 26.535dB (단일 최고)** | **SSIM/LPIPS 0.84302/0.28891, 4,975 update, 89,337GS, RGB+IMU only, MPS 없음, tail update 0, 97.250s. 이 수치는 birth2× run이나 late bins는 1× control보다 악화해 2×는 미채택. 기존 1× recipe 단일 최고 26.450, 27dB까지 숫자상 0.465dB** |
| **참조(별도 아키텍처)** | **exp52 VIGS-SLAM(무수정, 단안 RGB+IMU, DROID-SLAM 트래킹)** | 폴리싱포함 kf 30.90 / **순수온라인 held-out 22.82** | **1253. ⚠ 정정: kf 30.90은 26k-iter 오프라인 색정제 포함 수치(실측 검증됨). `--pure_online` 실측 결과 순수 온라인 held-out PSNR은 22.73dB(1253)/23.53dB(rot) — 우리 exp51(25.29dB)보다 낮음. 실시간 배수는 exp53+54로 1.52배→0.94배까지, exp55(내용-적응 예산+carve)로 **평균 gaussian 수 −35.9%**·**가시 floater −7.5%**(둘 다 PSNR/시간 비용 없음) 추가 확보. **exp56(mapping iters 10→7 + init_itr_num 1050→600 + n_global_views 2→6 + Camera 행렬 캐싱)로 갱신: 59.80s→45.79s(실시간 배수 0.92→0.70배, −23.4%), PSNR 22.61/22.95→23.49/23.88(mean +0.88dB, kf +0.93dB), map() 성사 +64% — "gaussian 수를 줄여도 안 빨라지는" 원인을 기존 계측 재분석으로 규명(픽셀/커널-launch 고정비가 지배적)한 뒤 iters를 낮춰 1차 개선, `map_call` 로그 집계로 "호출 26회 중 2~3회(맵 초기화/IMU 재초기화)가 시간의 49%"를 발견해 init_itr_num으로 2차 개선, 회귀분석으로 "카메라 수(n_view)가 시간을 지배"함을 계수로 확정한 뒤 "프론티어 window는 그대로, 과거-뷰 곁눈질만 늘리기"로 3차 개선(Phase7), rasterizer batch 구현을 프로파일로 조사하다 발견한 "카메라 pose 불변인데 매 view마다 행렬 역산 재계산" 무위험 버그를 캐싱으로 고쳐 4차 개선(Phase8, 이 세션 최고 ROI) — 4단계 전부 시간·품질 동시 개선.
**Phase 11(renderCUDA 커널 레벨 멀티카메라 batch화, opt-in `kernel_batch_render`)로 5차
개선: 45.79s→44.00s(−3.9%), PSNR 23.49/23.88→23.46/23.98(무손실), rasterize
avg/call 139.4ms→66.8ms(−52.1%)** | 

## 지금 열려 있는 질문

1. ~~exp40br·exp39b~~ → 완료: 재현 성공(region 462/가시 25), MPS도 -0.10dB에 가시 먼지 0. **양 트랙 레시피 확정.**
2. **train PSNR is not a reliable metric for floater quality** (floater=residual parasite). Instead, quality is evaluated with region GT metric and visual inspection.
3. ~~exp37 1순위~~ → **역전 기각**: 표준 GT 지표로 baseline의 4.7배 최악(region_n 16,454). dense init 축은 carve와 결합해야만 의미.
4. 잔여 가시 floater ~28개(exp40b)는 3D 신호 한계 — multi-view 색 일관성은 기각됐고(흰 방), 렌더-GT 잔차 축은 미탐색.

## 확정된 방법론 (요약: rounds/round8_*)

- **Carve Loss** (`3dgs-custom/eval/carve_loss.py`): 빈공간 증거 score `w·(1−maxop)` (수동 라벨 AUC 0.98) 위에 ① softlite opacity 압력(λ0.02) ② 예산 top-K prune(0.75%) ③ 출생 게이트(0.95; split의 29.5%가 허공 출생) ④ carve-potential force(xyz 견인, 진동 평형 위 일관 편향). 추가 입력 불필요(SLAM+카메라).
- 표준 지표: region GT(`floater_metric_region.py`) + ray-density 상호보완. 오프라인 청소: `extract_floaters_rulebase.py`(예산 top-K) + 3D 삭제 영역(`build_floater_region.py`).

## 최근 흐름 (최신순)

- **2026-07-29 (exp57 recent5% newborn-only — 첫 양성 미재현, 기각)**:
  forced recent dense step의 appearance+opacity gradient를 freeze 이후 태어난
  Gaussian 행에만 별도 Adam으로 적용했다. 첫 run은 **27.9030dB**와 floater
  15,126개로 양성이었지만 반복은 **27.7545dB/15,786개**였다. 평균
  **27.8288dB**는 freeze800 평균보다 −0.0177dB, floater 평균 15,456개는
  +43.5개다. 97.234/97.236s, tail0, MPS0는 통과했지만 안정적 이득이 없어
  기각한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 late1000 newborn appearance 정착 — 전체 무이득 기각)**:
  frame1000 이후 PPM newborn 행만 appearance+opacity 1-step으로 자기 RGB에
  정착시켰다. fixed는 **27.8391dB**로 freeze800 평균 대비 −0.0074dB,
  floater는 **15,412개**로 기준 평균과 동일했다. 1000–1199는 +0.518dB지만
  final bin은 −0.280dB로, keyframe-local 정착도 오차를 뒤로 이동시켰다.
  97.232s/tail0/MPS0를 통과했지만 30dB 레버가 아니므로 기각한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 late1000 PPM birth2× — tail 이동만, floater 증가로 기각)**:
  freeze800에서 frame1000 이후 append-only PPM birth만 2×로 늘렸다.
  Gaussian은 83.9k→103.6k(+23.5%)였지만 fixed는 **27.8335dB**로
  freeze800 평균 대비 −0.0129dB였다. 1000–1199는 +0.499dB, 1200–1252는
  −0.536dB로 오차를 뒤로 밀었고 visible floater 절대 수는 평균
  15,412.5→**16,988(+10.2%)**로 늘었다. 97.218s/tail0/MPS0는 통과했다.
  late density 단독은 종료하고 마지막 newborn 정착/coverage 구조를 다음 축으로 둔다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 freeze800 — strict 27.846dB 평균 + floater 동시 개선)**:
  append-birth 조건의 freeze 경계를 850→800→750으로 좁혔다. freeze800은
  fixed **27.8568/27.8361dB**(평균 **27.8464**, range 0.0207), freeze750은
  27.6969로 하락했다. freeze800 floater proxy는 **15,252/15,573개
  (26.72/27.04%)**로 freeze1050 anchor control 16,639개(28.98%)보다
  평균 1,226.5개(7.37%) 적었다. 두 채택 run은 97.235/97.271s,
  tail0, RGB+IMU only/MPS0를 통과했다. freeze800을 채택하며 frame1000 이후
  23.0–23.5/19.7dB late coverage가 strict30의 다음 병목이다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 freeze850 — strict fixed 27.639dB 평균으로 채택)**:
  pre-IMU gate, append-only PPM birth, post-freeze dense supervision을 유지하고
  freeze 경계를 1050→950→900→850으로 앞당겼다. freeze950은
  **27.4717/27.4509dB**(평균 27.4613), freeze900은 27.4644, freeze850은
  **27.5822/27.6958dB**(평균 **27.6390**)였다. freeze850 두 run 모두
  97.282/97.200s, tail update 0, RGB+IMU only/MPS0를 통과했다. 기존
  freeze1050 평균 27.0205 대비 **+0.6185dB**다. 다만 마지막 두 bin은
  22.91–23.45/19.38–19.51dB여서 30dB의 다음 병목은 후반 coverage다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 batch2 평균-gradient Adam×2 — update↑, 품질↓ 기각)**:
  추가 render/backward 없이 batch 평균 gradient를 Adam에 두 번 적용했다.
  pre-IMU gate 포함 paired 600 smoke에서 optimizer/view update는
  **2,714→3,100(+14.2%)** 늘었지만 fixed는 **27.4518→27.2989dB
  (−0.153)**, SSIM/LPIPS도 악화했다. 48.251s/tail0, RGB+IMU only/MPS0
  계약은 통과했다. stale 평균 gradient 반복은 순차 stochastic Adam을 대체하지
  못하므로 full 1,253에 승격하지 않고 기각한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 batch forward + sequential Adam — 54.5% 느려 조기 기각)**:
  batch2의 optimizer-step 감소를 막으려고 두 batched view loss의 gradient를 각각
  구해 Adam 두 step을 적용했다. 90,770GS/1024² microbenchmark에서 순차
  **7.7485ms** 대비 batch-grad **11.9746ms**로 54.54% 느렸다. 현재 custom
  autograd가 loss별 호출마다 batch 전체 backward를 재실행하기 때문이다.
  수치적으로는 실행 가능했지만 속도 정지 조건을 만족해 runtime 구현과
  smoke/full replay 전에 기각했다. 처리량을 늘리려면 Python 조합이 아니라
  CUDA backward API가 한 번에 per-view Gaussian gradient를 반환해야 한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 loss-priority within-epoch — fixed 26.973dB, family 종료)**:
  priority50의 uniform coverage 손실을 분리하려고 모든 causal dense view를
  epoch당 정확히 한 번 쓰면서 loss EMA로 순서만 가중했다. fixed는
  **26.9726dB**로 priority50의 26.9249보다 회복했지만 uniform control 평균보다
  여전히 −0.0479dB이고 27 미달이다. 4,876 update, 78,508GS,
  **97.2382s/tail0**, RGB+IMU only/MPS0 계약은 통과했다. priority50 손실의
  주원인은 coverage 감소였고 hard-view ordering도 순이득이 없어 family를 닫는다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 loss-prioritized replay 50% — fixed 26.925dB, 기각)**:
  causal하게 관측한 per-view loss EMA에 background step 50%를 재배분하고 나머지
  50%는 uniform shuffled coverage를 유지했다. fixed는 **26.9249dB**로 strict27
  control 평균보다 −0.0956dB였다. SSIM/LPIPS는 0.85448/0.27687로 소폭
  좋아졌지만 PSNR 목표를 깨뜨렸다. 4,927 update, 76,002GS,
  **97.2459s/tail0**, RGB+IMU only/MPS0 계약은 통과했다. 어려운 view 반복이
  uniform coverage 손실을 상쇄하지 못해 priority를 기각하고 default 0을 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp58 fixed-view pose-gradient skip — −1.96%, 조기 기각)**:
  background view pose가 고정이라는 점을 이용해 `dL_dtau` SE3 계산만 생략하는
  저위험 가지를 90,770GS/1024²에서 검증했다. forward는 bit-exact이고 Gaussian
  gradient 상대오차는 8.76e-8~3.65e-6이었지만, full **3.0617ms** 대비 skip
  **3.1216ms**로 오히려 1.96% 느렸다. 커널/launch 구조를 그대로 둔 산술 일부
  생략은 ROI가 없어 1253 replay 전에 기각했다. 임시 CUDA/Python patch는 전부
  원복하고 baseline extension 재빌드 및 실제 render+backward pose gradient까지
  확인했다. strict 30dB 속도 축은 `BACKWARD::preprocess` 전체 batch 또는
  update 효율 개선처럼 더 큰 구조 변화가 필요하다.
  → [exp58](experiments/exp58_cuda_visibility_backward_plan.md)
- **2026-07-29 (exp57 strict27 background carve — 품질·floater 동시 악화)**:
  depth-anchor diagnostic paired run에서 background carve off→λ0.05는 fixed
  **27.0124→26.8402dB**, visible floater **16,639→17,036**, 비율
  **28.976→29.689%**로 둘 다 악화했다. online wall 97.281/97.229s와
  tail0/RGB+IMU only/MPS0 계약은 통과했다. PPM과 regular frontier carve는
  유지하되 background carve는 끄고, 같은 evidence의 hard prune 확대도
  중단한다. 이 scene의 floater 수는 수동 region GT가 아닌 기존 carve proxy임을
  명시한다. 다음 품질 축은 strict 30dB를 직접 겨냥한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 pre-IMU GS gate — strict 27dB 2/2 재현, 채택)**:
  IMU metric 초기화 직후 전부 삭제되던 초반 GS를 init 완료까지 보류했다.
  fixed는 **27.0039/27.0371dB**(평균 27.0205, 범위 0.0332), online wall은
  **97.207/97.241s**, tail0이었다. raw scale도 ungated 1.038~1.040에서
  tracking-only와 같은 0.9736대로 돌아와 초반 GS 경합의 인과가 확인됐다.
  두 run 모두 RGB+IMU only/MPS0/fixed evaluator exclusion 계약을 통과했다.
  strict 27 반복 목표를 완료하고 gate를 채택하며, 다음은 고품질 strict map에
  carve/floater 억제를 이식한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 window8 scale-bin 대조 — 26.703dB, 축 종료)**:
  첫 window8의 scale1.035 교란을 제거하려 quantum0.01을 써 raw
  1.03995→**1.040**을 적용했지만 fixed는 **26.7031dB**였다.
  첫 run보다 −0.142dB이고 window10 quant 평균보다도 낮다.
  **97.261s/tail0/RGB+IMU only/MPS0** 계약은 통과했다. window8의
  26.845는 안정된 인과 이득이 아니므로 window8·quantum0.01을 기각하고
  frontier window 축을 종료한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 frontier window8 — fixed 26.845dB, 유망하지만 미채택)**:
  window 10→8로 frontier gradient 집중을 시도해 background 5,023 update,
  fixed **26.8454dB**를 얻었다. quantized-window10 평균보다 +0.114dB이나
  27에는 0.155dB 부족했고, raw scale이 달라 applied scale도 1.035로 이전
  1.040 run들과 다른 bin이라 순수 window 효과를 확정할 수 없다.
  **97.242s/tail0/RGB+IMU only/MPS0** 계약은 통과했다. 26.9 사전 반복
  기준에도 못 미쳐 반복하지 않고 default window10을 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 IMU scale quantum0.005 — 분산 10× 감소, 평균 26.731dB)**:
  online metric scale을 0.005 간격으로 causal 반올림해 세 run 모두 1.040을
  적용했다. fixed는 **26.728/26.755/26.712dB**(평균 26.731, 범위 0.043)로
  unquantized 범위 0.431보다 약 10배 안정화됐다. 모두 deadline/tail0/
  RGB+IMU only/MPS0을 통과했다. 다만 평균 품질은 −0.111dB이고 27 미달이라
  품질 레시피로는 기각, default off A/B stabilizer로만 보존한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 tracking-only 대조 — GS interleaving이 pose 분산 증폭)**:
  GS를 제거한 두 strict replay는 keyframe 111개가 같고 xyz 평균/최대 차이가
  1.05/3.82mm였다. mapping 동시 실행은 최대 38.3mm였으며 IMU rescale도
  tracking-only 0.9736대, mapping 1.038~1.040으로 갈렸다. tracker 자체보다
  regular GS 부하가 IMU-init/keyframe 상태와 pose 분산을 크게 증폭하는 경로를
  확인했다. no-mapping queue guard 버그 두 곳도 default-preserving 수정했다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 반복 분산 원인 — background 전 pose가 이미 다름)**:
  quota 두 run은 keyframe 116개의 timestamp가 완전히 같지만 최종 xyz 평균
  절대차가 0.60/1.17/1.88cm, 최대 3.83cm였다. background 시작 전 kf17에서
  이미 최대 1.03cm 차이가 났다. 따라서 background sampling이 아니라
  tracker/PGBA 수치 변동 또는 regular GS GPU interleaving이 map topology와
  PSNR 분산의 선행 원인이다. 다음 안정화 범위를 이 둘로 좁힌다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 causal quota5200 — 26.859/26.676dB, 분산 억제 실패)**:
  frame 진행률별 background 누적 step 상한을 causal하게 unlock하는 quota를
  구현했지만 두 run은 fixed **26.8585/26.6756dB**(평균 26.7671),
  update 4,676/4,305회로 여전히 갈렸다. 둘 다 97.65s/tail0/RGB+IMU only/MPS0
  계약은 통과했다. strict tail0에서는 부족분 catch-up이 불가능하고 frame700
  이전부터 topology가 달라져 background pacing만으로 분산을 못 막는다.
  quota5200은 기각하고 default off로 둔다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 late-iters3 freeze1060 — 26.720dB, 경계 스캔 종료)**:
  freeze1050보다 regular mapping을 10 frame 더 허용했지만 fixed는
  **26.7204dB**, background 4,747 update, 77,007GS였다. 마지막 bins도
  23.415/19.850dB로 회복되지 않았다. **97.203s/tail0/RGB+IMU only/MPS0**
  계약은 통과했다. freeze1040/1060 양쪽 이동이 모두 실패했으므로 1050을
  유지하고 boundary 스캔을 종료한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 causal feedback target6500 — low13/high25, 26.807dB 기각)**:
  target6500은 causal controller가 low 13회/high 25회로 실제 전환했고
  5,310 background update를 확보했지만 fixed는 **26.8067dB**였다.
  **97.265s/tail0/RGB+IMU only/MPS0** 계약은 통과했다. 처리량 feedback은
  작동했으나 map topology·gradient 품질 변동을 해결하지 못해 feedback 축을
  종료한다. 1차 목표는 30dB가 아니라 strict 27dB 반복 달성으로 유지하고,
  hard carve/pruning은 그 뒤로 둔다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 causal feedback target5100 — low0/high38, 26.800dB)**:
  frame 진행률 대비 replay step 목표로 iters2/3을 고르는 feedback을 구현했다.
  target5100은 mapping 종료 시 목표선이 너무 낮아 low 선택 0회/high 38회로
  static late3와 같았고, 5,233 update에도 fixed **26.800dB**였다.
  97.221s/tail0 계약은 통과했다. 실제 제어가 발생하도록 target6500을 검증한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 late2→second700 iters3 — fixed 26.792dB, 고정경계 종료)**:
  650–699만 iters2, 이후 iters3인 최소 절충도 background 4,782 update,
  fixed **26.792dB**에 그쳤다. 97.247s/tail0 계약은 통과했지만 static frame
  경계가 wall scheduler 분산을 제어하지 못한다. second700/850을 종료하고,
  현재 frame 대비 replay step 목표로 iters2/3을 고르는 causal feedback으로 간다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 late2→second850 iters3 — fixed 26.693dB 기각)**:
  두 번째 frontier schedule을 구현해 650–849 iters2, 850–1049 iters3를
  적용했다. 4,988 background update를 확보했지만 fixed는 **26.693dB**로,
  iters3 적용 구간을 절반으로 줄인 frontier 보강 손실이 컸다. 97.218s/tail0
  계약은 통과했다. 다음은 650–699만 iters2로 두는 second700 최소 절충이다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 late-iters3 세 번째 26.572dB — 반복 27 미달)**:
  세 번째 run은 background update가 5,161→4,757회로 줄며 fixed
  **26.572dB**였다. late3 3회는 27.004/26.949/26.572dB(평균 26.842)라
  최초 27 초과는 유효한 single best지만 반복 달성은 아니다. 다음은 iters2의
  replay 처리량을 보존하고 후반만 iters3로 올리는 2단계 스케줄이다.
  97.216s/tail0/RGB+IMU only/MPS0 계약은 통과했다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 late-iters4 — fixed 26.658dB 기각)**:
  frame650 이후 frontier 반복을 4로 늘리자 background update가
  5,161→4,362회(−799), GS는 78,566개로 늘었고 fixed는 **26.658dB**로
  악화했다. 97.248s/tail0 계약은 통과했지만 추가 frontier gradient보다 replay
  수렴 손실이 커 기각한다. late-iters3를 유지하고 세 번째 반복으로 판정한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 late-iters3 — 최초 27.004dB, 반복 26.949dB)**:
  frame650 이후 frontier mapping 반복을 2→3으로 늘려 fixed
  **27.0039/26.9492dB**(평균 26.9765)를 얻었다. late-iters2 3-run 평균보다
  +0.219dB이고 두 run 차이도 0.055dB라 품질 효과는 재현됐다. 둘 다 5,161
  background update, **97.234/97.254s**, tail 0, RGB+IMU only/MPS 0 계약을
  통과했다. 최초 27 초과는 유효하지만 반복 run이 27 미만이라 1차 목표 달성을
  아직 확정하지 않고 late-iters4를 검증한다. hard carve/pruning도 계속 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 background SSIM interval2 — fixed 26.703dB 기각)**:
  background에서 SSIM을 매 2번째 step에만 계산했지만 update는 5,253회로
  0ms 기존 범위에서 늘지 않았고 fixed는 **26.703dB**, SSIM/LPIPS는
  0.83674/0.32105로 악화했다. SSIM은 처리량 병목이 아니며 gradient 생략 손해만
  확인돼 default interval1을 유지한다. 97.227s, tail update 0 계약은 통과했다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 0ms 3회 평균 26.758dB, freeze1040 26.489dB 기각)**:
  0ms uniform shuffled 세 번째 반복은 fixed **26.628dB**, 5,242 update,
  **97.227s**, tail 0이었다. 세 run은 26.882/26.764/26.628dB로 평균
  **26.758dB**이며 단순 반복만으로 27을 넘지는 못했다. freeze 경계 미세 스캔
  1040은 **26.489dB**, 4,639 update, 97.429s로 1000–1199 coverage를 잃어
  기각하고 freeze1050을 유지한다. root `ENOSPC` 동안 `/dev/shm`에서 실행한
  metric/provenance는 공간 확보 뒤 정식 결과 경로에 보존했다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 shuffled recent 5% — late 개선, fixed 26.472dB 기각)**:
  shuffled epoch에서 recent fraction이 무시되던 opt-in 분기 버그를 수정해 0ms
  채택점에 late non-eval RGB 5%를 적용했다. 마지막 bins는 uniform 반복 대비
  **23.383→23.655, 19.197→19.696dB**로 올랐지만 0–999 손실이 더 커 fixed
  전체는 **26.472dB**, 5,247 update, 97.259s, tail 0이었다. 작은 late 편향도
  공유 Gaussian의 전역 균형을 깨므로 기각하며 0ms uniform best 26.882를 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 background idle guard 0ms — 26.882/26.764dB, 채택)**:
  1ms 아래의 idle slot도 회수하되 queue-empty/tracking-inactive 조건을 유지해 두
  strict run을 실행했다. fixed 252-view는 **26.882/26.764dB**(평균 26.823),
  update 5,731/5,234회, online wall **97.233/97.252s**, tail update 0이었다.
  두 run 모두 1ms 단일 최고 26.752를 넘었으므로 0ms를 채택하고 strict 단일
  최고를 **26.882dB**로 정정한다. 27dB까지 0.118dB지만 두 run 모두 아직
  27 미만이며 후반 bins도 23.039/19.968 및 23.383/19.197dB라 성공 판정과
  hard carve/pruning은 계속 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 background idle guard 1ms — 26.687/26.752dB, 채택)**:
  shuffled dense epoch에서 idle guard를 5→1ms로 낮춰 두 strict run을 실행했다.
  fixed 252-view는 **26.687/26.752dB**(평균 26.719), update는
  5,335/5,166회, online wall은 **97.229/97.242s**였고 둘 다 RGB+IMU only,
  MPS 0, tail update 0 계약을 통과했다. 직전 shuffled 3-run 평균보다
  +0.196dB이고 두 run 모두 기존 best 26.639를 넘어 채택한다. strict 단일
  최고를 **26.752dB**로 정정하며 27dB까지 0.248dB가 남았다. 마지막 bins는
  여전히 23.329/19.664dB 수준이라 hard carve/pruning은 계속 보류한다.
  root disk `ENOSPC`로 첫 PLY 저장이 중단돼 불완전한 2MB 파일만 삭제했고,
  `/dev/shm` 복구 결과의 metric/provenance만 정식 결과 경로에 보존했다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 shuffled dense epoch — median 26.528dB, best 26.639dB 채택)**:
  독립 background RNG 위에서 매 causal dense view를 epoch당 한 번 무작위 순서로
  쓰는 sampler를 3회 검증했다. fixed는 **26.402/26.639/26.528dB**,
  median/mean **26.528/26.523dB**로 independent RNG 평균 26.428보다 +0.095dB다.
  모두 97.65s/tail0 계약을 통과했고 3회 중 2회가 independent 최고를 넘었다.
  shuffled epoch를 채택하며 strict-disjoint 단일 최고를 **26.639dB**로 정정한다.
  27dB까지 0.361dB이고 hard carve/pruning은 계속 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 background 전용 RNG — fixed 26.414/26.441dB, 안정화 채택)**:
  background worker와 frontier mapper가 전역 Python RNG를 thread-race로 공유하던
  원인을 분리하고 `background_polish_seed=0` 전용 난수열을 사용했다. 두 strict
  반복은 fixed **26.414/26.441dB**(차이 0.028dB), legacy union
  26.40510/26.40489dB(차이 0.00021dB), 4,736/4,792 update,
  **97.268/97.265s**, tail 0이었다. 27dB 향상 레버는 아니지만 기존 recipe의
  26.069~26.450 변동을 크게 줄여 이후 A/B의 인과 판정 기반으로 채택한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 post-PGBA forced keyframe 3장 — fixed 25.776dB, 축 종료)**:
  global PGBA 교란을 분리하려고 cutoff1120 뒤 1152/1202/1249만 강제 보존했다.
  세 frame 모두 남고 **97.292s**, tail 0을 통과했지만 fixed는 **25.776dB**,
  4,993 update, 77,199GS였다. late bins는 23.171/19.837dB로 52-view 가중
  control 대비 +0.085dB뿐이며 전체 환산 기대 이득은 약 +0.018dB다.
  pre-freeze scheduler 손실을 상쇄할 수 없고 27dB 레버 규모도 아니므로
  forced-keyframe 보존 축을 종료하고 1×/refine=0 자연 keyframe recipe를 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 forced late keyframe 보존 4장 — fixed 25.720dB, 기각)**:
  evaluator와 겹치지 않는 1102/1152/1202/1249를 강제 생성하고 frontend
  redundancy removal에서도 보존했다. 네 장 모두 최종 keyframe에 남았고
  1000–1199/1200–1252는 control보다 +0.320/+1.335dB 개선됐지만, fixed 전체는
  **25.720dB**, 4,737 update, 78,378GS, **97.264s**, tail 0으로 −0.730dB
  하락했다. 특히 800–999가 −1.242dB라 late coverage 이득이 전역 trajectory/map
  상태 손실을 상쇄하지 못했다. 4장 보존 recipe는 기각하며, frame1102가 PGBA
  cutoff1120 이전인 교란을 분리하려면 이후 frame만 쓰는 좁은 검증이 필요하다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 newborn appearance+opacity 1-step — fixed 26.421dB, 기각)**:
  freeze 뒤 exact newborn의 geometry는 고정하고 RGBD birth view에서 color/SH/opacity만
  1회 정착시켰다. strict-disjoint fixed 결과는 **26.421dB**, SSIM/LPIPS
  0.84076/0.30292, 4,719 update, 74,991GS, **97.286s**, tail 0이었다.
  paired refine=0 control보다 전체 −0.029dB이며, 직접 영향 52-view 평균도
  **−0.132dB**였다(1000–1199 −0.299dB, 1200–1252 +0.423dB).
  마지막 12장만 좋아지고 전체 후반 coverage는 개선되지 않았으므로 기각한다.
  newborn RGBD 보정과 birth 밀도 축을 모두 종료하고, 1×/refine=0 recipe를 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 PPM birth 2× — fixed 26.535dB, late 인과 기각)**:
  freeze 뒤 PPM 표본만 2배로 늘렸다. fixed는 **26.535dB**, LPIPS 0.28891,
  4,975 update, 89,337GS, **97.250s**, tail 0으로 숫자상 신기록이다. 그러나
  직접 영향 구간 1000–1199/1200–1252는 1× control보다 −0.532/−0.368dB라
  전체 상승은 더 좋은 pre-freeze scheduler state 때문이다. 2×를 채택하지 않고
  1×를 유지한다. 유효 단일 최고 숫자는 남기되 27dB 성공은 반복 재현해야 한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 newborn RGBD paired control — refine 기각, best 26.450dB)**:
  exact-newborn RGBD 1-step 반복은 **26.360dB**로 첫 26.332를 반복했지만,
  동일 시점 refine=0 control이 **26.450dB**, SSIM/LPIPS 0.84346/0.29784,
  4,830 update, 75,003GS, **97.287s**, tail 0으로 더 높았다. refine은 control
  대비 −0.09~−0.12dB이고 late bin도 낮아 noisy depth로 newborn을 더 움직이는
  축을 기각한다. control은 유효한 새 단일 최고지만 동일 recipe 분산이
  26.069~26.450이라 27dB는 반복 재현이 필수다. 남은 단일 최고 갭은 0.550dB다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 exact-newborn RGBD 1-step — fixed 26.332dB, 반복 필요)**:
  freeze 뒤 PPM birth가 생성만 되고 자신을 만든 RGBD keyframe을 한 번도 학습하지
  않는 구조를 발견했다. fresh Adam+exact row mask로 기존 map/topology를 고정하고
  newborn만 1회 RGBD 정착시켰다. full은 **26.332dB(+0.263)**, LPIPS 0.29921,
  4,998 update, 75,068GS, **97.267s**, tail 0으로 새 단일-run best다. 하지만
  상승이 intervention 이전 200–999에서 나왔고 late bin은 오히려 낮아 scheduler
  분산과 인과 효과가 섞였다. 동일 설정 반복 전 미채택이며 27dB까지 0.668dB다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 non-eval endpoint frame1249 — tail 양성, 전체 기각)**:
  마지막 미완료 causal interval을 닫으려고 평가 frame1252가 아닌 frame1249를
  keyframe으로 강제했다. dense 등록은 약 448→454장, 1200–1252 PSNR은
  20.334→**21.413dB(+1.078)**였지만 fixed 전체는 **25.144dB**, 4,621 update,
  75,966GS, **97.298s**, tail 0이었다. intervention 전 구간까지 흔들린 것은
  parallel scheduler 분산이며, 마지막 bin 12장의 가중 기대 이득도 약 +0.05dB라
  0.931dB 갭의 주축이 될 수 없다. 유리한 run을 고르지 않고 기각하며, 다음은
  freeze 뒤 PPM newborn의 online RGBD 정착을 검토한다. strict best는 26.069dB다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 topology-only freeze1050 — fixed 25.472dB, 기각)**:
  regular mapping은 계속하되 frame1050 이후 birth/densify/prune만 막았다.
  strict-disjoint fixed 252-view는 **25.472dB**, 4,630 update, 66,588GS,
  **97.266s**, tail 0으로 기준선보다 −0.597dB였다. 1000–1199/1200–1252도
  22.458/18.165dB로 더 악화됐다. 600-frame topology-freeze450 실패를 full에서도
  재확인했으므로 이 축을 종료하고 freeze1050+append-only PPM birth를 유지한다.
  strict best 26.069dB와 27dB 전 hard-carve 보류도 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 late appearance+opacity recent50 — 전체 −0.626dB, 기각)**:
  late recent-view step에만 xyz/scale/rotation을 동결하고 color/SH/opacity를
  갱신했다. strict-disjoint fixed 252-view는 **25.443dB**, 4,743 update,
  79,524GS, **97.268s**, tail 0이었다. frame1200–1252는
  20.334→21.192dB로 +0.857dB 회복했지만 0–199가 −1.928dB,
  800–1199도 악화됐다. geometry를 막아도 공유 Gaussian의 appearance/compositing
  충돌로 초기 영역이 무너지므로 newborn-only와 함께 forced-recent sampling
  계열을 종료한다. 다음은 late view를 편향 표집하지 않고 정상 frontier update에
  남기되 topology만 고정하는 방식이다. strict best 26.069dB를 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 최초 strict-disjoint 기준선 — fixed 252-view 26.069dB)**:
  evaluator의 frame `idx%5==0`+마지막 frame을 Gaussian init·PPM birth·regular/global
  map window·background polish에서 모두 제외하는 mapping-side guard를 구현했다.
  frame0 제외 시 첫 trainable keyframe에 잘못된 origin/depth packet을 쓰던 초기화
  버그도 함께 수정했다. append-only PPM birth 채택점 재실행 결과 fixed 252-view
  **26.0686dB**, SSIM/LPIPS 0.83314/0.33314, 4,715 update, 78,534GS,
  **97.238s/97.65s**, post-stream update 0이었다. provenance는 RGB+IMU-only,
  MPS 입력 0이다. 기존 union 26.396은 held-out best에서 제외하고 이 값을 최초
  유효 기준선으로 채택한다. 1000–1199/1200–1252가 **23.723/20.334dB**라
  남은 0.931dB도 late coverage가 지배한다. 27dB 전 hard carve는 계속 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 중대정정 — force-final 무효 + evaluator union 발견)**:
  force-final은 evaluator가 항상 포함하는 마지막 RGB를 PPM birth supervision으로
  사용했으므로 26.426/26.321dB를 **held-out 판정 제외**하고 기존 26.396dB로
  되돌린다. 비평가 offset2 frame1102/1152/1202 강제 keyframe은 legacy
  **26.195dB**, fixed offset0 **26.317dB**로 개선이 없었다. 더 근본적으로 기존
  `mean_psnr`이 fixed evaluator view와 모든 keyframe의 union 평균임을 확인했다.
  앞으로 JSON에 동일 252장 `fixed_eval_mean_*`과 keyframe overlap 수를 별도
  기록하며, Gaussian mapping에서도 fixed eval frame을 제외한 재검증 전에는
  strict-disjoint held-out 성공을 주장하지 않는다. recent50 gradient를 신규
  Gaussian에만 격리한 run도 legacy/fixed **24.516/24.612dB**로 강하게
  실패했다. 모든 실행은 RGB+IMU-only, 1.5×, zero-tail을 지켰고 hard carve는
  계속 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 final RGB 강제 keyframe — 단일 최고 26.426dB, 미재현)**:
  마지막 keyframe 뒤 18.9dB coverage를 보강하려고 final RGB를 motion threshold와
  무관하게 online keyframe으로 승격해 기존 Omnidata prior→BA depth→append-only
  PPM birth를 실행했다. 원 run은 **26.426/26.304dB**, 5,395 update,
  92,201GS, **97.370s**로 기존 단일 최고를 +0.030dB 경신했고 마지막 구간도
  +0.478dB였다. 그러나 동일 설정 반복은 **26.321/26.203dB**로 append-only
  26.312dB와 사실상 같아 recipe 개선은 미재현이다. 단일 최고 숫자만
  26.426dB로 갱신하고 force-final은 채택하지 않는다. 두 run 모두
  RGB+IMU-only/MPS 없음/fixed 1.5×/zero-tail을 통과했다. 27dB까지 단일
  최고 기준 0.574dB이며 hard carve는 계속 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 per-view late coverage 진단 + append-only PPM birth)**:
  채택 recipe의 per-view 지표를 새로 저장해 구간별로 분석했다. frame0–999는
  26.35~28.47dB지만 freeze 뒤 1000–1199는 **22.782dB**, 1200–1252는
  **18.884dB**로 무너져 남은 갭이 late coverage임을 확정했다. regular
  map/densify/prune는 freeze한 채 새 tracked keyframe의 online depth에서
  PPM Gaussian birth만 허용하자 paired control **26.122→26.312dB**,
  1000–1199는 **+0.604dB** 개선됐다. 다만 22k GS가 늘고 kf는
  26.976→26.106dB로 하락했으며 기존 최고 26.396을 넘지 못했다. birth 예산
  절반은 26.269dB였다. late RGB 50% 강제 표집은 마지막 구간을
  18.949→22.256dB로 회복했지만 초기 구간을 훼손해 전체 25.375dB, 약한
  15%도 26.142dB로 기각했다. grayscale geometry/RGB appearance 1:1 교대도
  **25.439dB**로 joint gradient보다 나빴다. 모든 run은 RGB+IMU-only,
  MPS 없음, fixed 1.5×, zero-tail을 통과했다. strict 최고
  26.396(반복 26.083)을 유지하고 27dB 전 hard carve는 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 background DSSIM 0.1/0.3 — 기존 0.2 유지)**:
  held-out PSNR과 background loss를 더 맞추기 위해 DSSIM weight를 기존 0.2에서
  0.1/0.3으로 대칭 스캔했다. 0.1은 **26.003/26.884dB**, 0.3은
  **26.232/27.148dB**로 둘 다 최고 26.396dB를 넘지 못했다. 0.3의
  SSIM/LPIPS는 0.83896/0.30885로 좋았지만 PSNR 채택 기준에는 미달했다.
  두 run 모두 약 5.1k update, 97.27s, zero-tail로 strict 계약을 통과했다.
  기존 0.2를 유지하고 loss-weight 축을 닫는다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 offset weighting·SH·camera 분해 — 전부 기각)**:
  strict 최고 recipe의 남은 갭을 phase 비율, view-dependent appearance, camera
  nuisance로 분리했다. offset1:4 sampling weight를 0.3:0.7로 바꿔도
  **26.133dB**, SH degree1은 **26.099dB**, `f_rest` LR 4×도
  **26.133dB**로 개선이 없었다. 기존 camera `full` 실패를 다시 분해한
  exposure-only는 **25.650/26.471dB**, bounded pose-only는
  **25.724/26.592dB**로 둘 다 기각했다. pose-only는 추가 camera update
  비용 때문에 Gaussian update도 3,633회로 감소했다. 전 run이 RGB+IMU-only,
  MPS 없음, fixed 1.5×, zero-tail을 지켰다. Gaussian-only dense random
  start700과 strict 최고 26.396dB(반복 26.083)를 유지하며 27dB 전 hard
  carve는 계속 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 dense-only maturity700 — strict 최고 26.396dB, 반복 26.083dB)**:
  freeze1050/post-freeze RGB/optical offsets1+4에서 background pool의 keyframe을
  제외하고 dense RGB만 random sample했다. start650은 **26.229dB**였고,
  maturity 경계를 500/700/750으로 스캔하자 **26.125/26.396/26.328dB**로
  start700이 최고였다. 최고 run은 5,112 update, 70,320GS,
  **97.290s**, SSIM 0.83888, LPIPS 0.31609이며 동일 조건 반복은
  **26.083dB**로 0.313dB 낮아 scheduler 변동을 함께 기록한다.
  dense-only round-robin은 22.754dB, late-iters1은 26.304dB, full camera
  refinement는 25.452dB, post-freeze LR1.25는 25.894dB로 모두 기각했다.
  offsets3개 이상을 모두 trajectory-filler에 넣으면 late CUDA assert가
  재현됐고, optical1+4/interpolation 추가 phase 또는 appearance-opacity
  gradient split은 안정적으로 완주했지만 25.74~25.92dB로 품질 미달이었다.
  strict 계약과 hard-carve 보류를 유지하며 27dB까지 최고값 기준 0.604dB다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 post-freeze causal RGB + offsets1+4 — strict 신기록 26.129dB)**:
  직전 기록의 설명을 정정한다. 기본 freeze1050 sampler는 coordinate guard 때문에
  frame1049 이후 RGB를 실제로 제외하고 있었다. frozen map은 PGBA의 pose/scale
  변환을 계속 받으므로, 새 opt-in으로 freeze 뒤 도착한 RGB도 도착 이후에만
  background supervision으로 허용했다. offset4는 **25.616dB**(+0.181),
  평가 offset0을 계속 제외한 offsets1+4는 **26.129/27.152dB**, SSIM 0.82804,
  LPIPS 0.33335, 5,576 update, 70,510GS, **97.309s**로 추가 +0.513dB였다.
  MPS 없음/strict 1.5×/zero-tail을 준수한 새 best이며 27dB까지 0.871dB다.
  offsets1–4 전체는 frame1077 부근 CUDA device-side assert로 실패해 판정에서
  제외했다. hard carve는 아직 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 optical offset4 + freeze1050 — strict 신기록 25.435dB, 반복 재현)**:
  optical dense replay가 late non-keyframe coverage를 계속 공급하도록 둔 채 regular
  growing-map만 고정하는 경계를 1000/1050/1075/1100으로 스캔했다. held-out은
  각각 **25.050/25.435/25.198/24.685dB**였고, freeze1050이 no-freeze
  24.538dB보다 **+0.897dB** 높았다. 동일 seed 재실행도 **25.347dB**
  (원 run 대비 −0.088dB)로 이득을 재현했다. 원 run/반복은 각각
  5,748/5,301 update, 68,970/68,513GS, 97.283/97.403s이며 모두 strict
  deadline과 zero-tail을 통과했다. 1075의 과성장(72,897GS)과 1100의 late
  prune(52,649GS) 모두 나빠, 더 많은 Gaussian 자체가 답이 아니라 topology를
  안정시키는 시점이 중요하다. 새 strict best는 25.435dB이고 27dB까지
  1.565dB가 남아 hard carve는 계속 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 optical offset 선별 — offset4 strict 신기록 24.538dB)**:
  trajectory-filler dense view를 stride5의 offset별로 분리했다. 600-frame
  held-out은 offset1/2/3/4가 각각 **25.704/25.336/24.865/25.746dB**였고,
  offsets1–4 전체와 best 둘의 혼합(1+4)은 **24.027/24.232dB**로 크게
  악화됐다. optical pose는 수를 늘리는 것보다 일관된 단일 phase 선택이 중요하다.
  full 승격한 offset1은 24.465dB로 기존 best 미달, offset4는
  **24.538/24.521dB**, SSIM 0.80179, LPIPS 0.39362, 5,025 update, 67,145GS,
  **97.309s**로 held-out +0.055dB 신기록이었다. deadline margin 0.341초,
  RGB+IMU-only/MPS 없음/zero-tail을 모두 통과해 offset4를 채택한다.
  27dB까지 2.462dB가 남아 hard carve는 계속 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 causal trajectory-filler dense pose — strict 신기록 24.483dB)**:
  keyframe 양 끝점이 도착한 완료 구간의 과거 RGB frame만 `PoseTrajectoryFiller`로
  optical refinement해 dense supervision pose를 만들었다. MPS pose/depth/point
  cloud는 전혀 쓰지 않았다. 600-frame에서는 interpolation 대비 held-out
  **+0.477dB(25.336)**였으나, 최초 full은 PGBA refresh가 optical pose를 다시
  interpolation으로 덮는 버그 때문에 24.115dB였다. 이를 endpoint interpolation
  대비 local SE(3) residual로 저장하고 PGBA 뒤 재합성하도록 수정했다. 최종 full은
  **24.483/24.520dB**, SSIM 0.80350, LPIPS 0.39884, 4,581 update, 62,069GS,
  **97.287s**로 기존 best 대비 held-out **+0.164dB**이며 deadline을 0.363초
  통과했다. strict best로 채택하되 27dB까지 2.517dB가 남아 hard carve는 계속
  보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 stable-map freeze1000 — kf +1.63dB, held-out 기각)**:
  기존 freeze899의 late coverage 손실을 줄이면서 마지막 약 20초를 fixed-map
  수렴에 쓰기 위해 현재 best에 `mapping_freeze_after_frame=1000`을 결합했다.
  update는 5,087→**6,370**, keyframe PSNR은 24.385→**26.015dB(+1.630)**로
  크게 올랐고 **97.264s**로 deadline도 통과했다. 그러나 held-out은
  **24.031dB(−0.288)**, SSIM 0.77372로 악화됐다. stable-map 수렴은 실제로
  강하지만 late 신규 시점 coverage/일반화를 닫는 손해가 더 크므로 기각한다.
  27dB 갭은 단순 update 수가 아니라 growing map과 late non-keyframe coverage를
  함께 보존해야 풀린다. strict best 24.319dB와 27dB 전 hard carve 보류를 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 background LR parameter-group 분리 — full 기각)**:
  uniform LR 실패 원인을 분리하려고 SH+opacity와 xyz+scale+rotation 배율을
  독립 적용했다. 600-frame에서 appearance+opacity 1.5×는 **24.654dB
  (−0.205)**로 기각됐고, geometry-only 1.5×는 **25.090dB(+0.231)**로
  prefix 이득의 출처가 geometry임을 확인했다. 그러나 geometry-only full은
  5,247 update, 65,531GS, **97.300s(deadline 통과)**에도
  **23.816/23.916dB**로 strict best보다 held-out −0.503dB였다. 높은 geometry
  LR은 evolving full map에서 누적 안정성을 해치므로 parameter-group 분리를
  포함한 background LR 배율 계열을 종료한다. strict best 24.319dB와 1차 목표
  27dB, 그 전 hard carve 보류를 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 background LR×1.5 초기-step 제한 — prefix 양성, full 재기각)**:
  무제한 LR×1.5의 full 붕괴를 막기 위해 background 첫 2,500회 또는 1,000회에만
  배율을 적용하고 이후 자동으로 1.0으로 복귀시켰다. 600-frame에서는 cap2500이
  **25.181/25.252dB(+0.322/+0.573)**, cap1000이
  **24.990/24.932dB(+0.131/+0.253)**로 모두 기준보다 좋았다. 그러나 full
  cutoff1120에서는 각각 **24.216/24.283dB**, **24.217/24.311dB**로 strict
  best보다 held-out −0.103/−0.102dB였다. 둘 다 97.27~97.28s로 deadline을
  통과했지만 full 일반화가 없으므로 초기-step 제한형을 포함한 uniform
  all-parameter LR 압축 계열을 종료한다. strict best 24.319dB와 1차 목표 27dB,
  그 전 hard carve 보류를 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 background LR×1.5 — prefix 양성, full 강한 기각)**:
  background step에만 LR multiplier를 적용하고 frontier LR은 즉시 복원하는 opt-in을
  구현했다. 600에서 1.5×는 **24.949/25.004dB**로 기준보다 +0.090/+0.325dB,
  2.0×는 24.706dB로 내려가 1.5×를 full 승격했다. 그러나 cutoff1120 full은
  5,225 update, 68,507GS, **97.272s(deadline 통과)**에도
  **23.749/23.840dB**로 strict best보다 held-out −0.571dB였다. evolving map에
  높은 LR을 끝까지 누적하면 후반을 불안정하게 하므로 고정 multiplier는 기각한다.
  다음은 prefix 양성만 살리는 초기 step 제한형 LR이다. strict best 24.319dB,
  1차 목표 27dB와 그 전 hard carve 보류를 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 CUDA batch2 replay — view 처리량↑, 품질 기각)**:
  background batch2가 kernel-batch render를 사용하므로 600 start300에서 시험했다.
  1,995 optimizer step으로 3,990 view를 처리해 batch1의 3,284 view보다 +706
  늘었고 48.308s로 시간도 유지했다. 그러나 **24.433/24.206dB**로 batch1보다
  held-out −0.426dB였다. 평균 gradient 한 번은 두 순차 Adam step을 대체하지
  못하므로 view 처리량보다 optimizer step 횟수가 중요하다. batch1을 유지하고,
  다음은 step 수를 보존한 background 전용 LR 압축이다. strict best 24.319dB,
  1차 목표 27dB와 그 전 hard carve 보류는 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 replay start400 — 600에서 강한 기각)**:
  start300에서 regular map을 너무 일찍 7→2로 줄였는지 분리하려고 전환점을
  frame400으로 늦췄다. 2,159 update, 37,316GS, 48.298s로 deadline 경계는
  지켰지만 **23.993/23.795dB**로 start300의 24.859/24.679보다 held-out
  **−0.866dB**였다. 현재는 후반 regular 반복 보존보다 Gaussian-full random
  replay 누적량이 더 중요하므로 50% 상대 경계(start300/600, start650/full)를
  유지한다. 다음은 같은 시작점에서 batch당 view 수를 늘리는 처리량 축이다.
  strict best 24.319dB, 1차 목표 27dB와 그 전 hard carve 보류를 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 tracking stride2 + Gaussian replay — 600에서 기각)**:
  모든 RGB+IMU는 계속 ingest하되 visual tracker만 2-frame마다 실행해 replay 예산을
  늘렸다. 600 start300/late-iters2에서 update는 3,284→3,599였지만 결과는
  **24.525/24.281dB**, 38,940GS, 48.537s로 stride1의 24.859/24.679dB,
  48.276s보다 품질과 시간 모두 악화됐다. pose/geometry supervision 손실이 추가
  315 update 이득보다 커 full로 승격하지 않는다. tracking_stride1과 strict best
  24.319dB를 유지하고, 다음은 tracker를 약화하지 않는 frontier/replay 시작 경계다.
  1차 목표 27dB와 그 전 hard carve 보류도 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 PGBA cutoff1070 — 과도한 억제로 기각)**:
  cutoff1120이 마지막 frame1184 PGBA만 막아 +0.220dB였으므로, 1077·1119·1184
  세 late PGBA를 모두 막아 안정 구간을 늘렸다. update는 5,087→6,489로 늘고
  **97.271s(deadline −0.379s)**를 통과했지만 결과는 **24.091/24.060dB**로
  cutoff1120보다 held-out −0.229dB였다. 따라서 PGBA 자체를 줄이는 방향이 아니라
  마지막 재수렴 불가능한 한 번만 억제하는 **cutoff1120을 유지**한다. 새
  `eval_metrics_only`로 동일 지표 계산을 유지하며 per-view PNG 저장만 생략했다.
  strict best 24.319dB, 1차 목표 27dB, 27dB 전 hard carve 보류는 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 PGBA cutoff1120 — strict 신기록 24.319dB)**:
  마지막 PGBA가 random replay의 누적 상태를 종료 직전 다시 흔드는 문제를 직접
  분리했다. frame1120 이전 online PGBA와 전체 local frontend BA는 유지하고 이후
  global PGBA만 억제했다. full strict 결과 **24.319/24.385dB**, SSIM 0.78868,
  LPIPS 0.44374, 5,087 update, 66,784GS, **97.264s(deadline −0.386s)**로 기존
  best보다 held-out +0.220dB다. RGB+IMU-only, MPS 없음, zero-tail을 준수해 새
  strict best로 채택한다. 평가지표 계산은 완료됐으나 PNG/intrinsics 저장 도중
  디스크 부족이 발생해 해당 부가 artifact는 부분 저장으로 기록한다. 1차 목표는
  strict held-out 27dB이며 그 전 hard carve는 계속 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 post-PGBA1188 burst — 실행기회 0회로 기각)**:
  마지막 PGBA 직후 남은 약 65 frame 동안만 Gaussian-full random settle을
  집중하려고 background/late-iters1 시작을 frame1188로 맞췄다. 그러나 tracking이
  종료까지 연속 active여서 idle scheduler가 **0 update**였고, 결과는
  **22.997/23.307dB**, 86,469GS, **97.867s(deadline +0.217s)**였다. fixed
  1.5× wall time의 앞선 idle compute는 나중으로 저장할 수 없으므로 late burst
  가설은 구조적으로 기각한다. 다음은 마지막 PGBA 자체를 더 일찍 끝내 이전
  Gaussian-full update가 최종 좌표계에서 누적되게 하는 축이다. strict best
  24.099dB와 27dB 전 hard carve 보류를 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 Gaussian-full random late-iters1 — 경계 기각)**:
  채택된 late-iters2보다 post-PGBA settle 예산을 더 확보하려고 600 start300에서
  regular map 반복을 1로 낮췄다. update는 3,284→3,644로 늘었지만 결과는
  **24.789/24.729dB**, 38,248GS, 48.278s로 iters2의 24.859/24.679 대비
  held-out −0.070dB, kf +0.050dB의 혼재였다. 27dB 경로의 승격 기준인 held-out
  순개선을 넘지 못해 full은 실행하지 않고 **late-iters2를 채택점으로 유지**한다.
  strict best 24.099dB와 27dB 전 hard carve 보류는 변함없다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 PGBA xyz Adam moment 공변 변환 — 600에서 기각)**:
  PGBA의 `x'=C'+R(x-C)/s`에 맞춰 xyz Adam 1차 moment를 `Rm/s`, diagonal
  2차 moment를 `R²v/s²`로 변환하는 opt-in을 구현했다. 90도 회전/scale2 synthetic
  수치검증은 기대값과 일치했고 600 strict도 3,380 update로 정상 완주했다. 그러나
  Gaussian-full random+late-iters2 기준 **24.677/24.533dB**, 37,411GS,
  48.286s로 변환 없는 24.859/24.679보다 held-out **−0.182dB**였다. diagonal
  Adam state로는 회전 후 축간 covariance를 보존하지 못해 full로 승격하지 않는다.
  strict best 24.099dB와 27dB 전 hard carve 보류를 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 Gaussian-full random + late-iters2 — deadline-valid 신기록)**:
  fixed-map 27dB의 필수 조건이 all-Gaussian gradient였는데 기존 full 예산 재배분은
  appearance-only만 시험한 누락을 바로잡았다. frame650부터 regular map depth를
  7→2로 줄이고, 도착 완료 RGB를 uniform random으로 뽑아 camera-fixed
  xyz/scale/rotation/opacity/SH 전체에 update했다. 600-frame start300은
  **24.859/24.679dB**, 3,284 step으로 control 대비 +2.398dB였다. full strict는
  **24.099/24.202dB**, SSIM 0.77781, LPIPS 0.45834, 4,730 step, 67,759GS,
  **97.274s**로 deadline 97.65s를 0.376초 남기고 통과했다. 마지막 sensor frame
  뒤 optimizer update는 0회이고 RGB+IMU-only/MPS 금지를 준수했다. 27dB에는
  2.901dB 부족하지만 기존 deadline-valid 최고 23.782보다 +0.317dB인 새 strict
  best로 채택한다. 27dB 전 hard carve는 계속 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 robust residual historical sampler — 600에서 기각)**:
  regular mapping에서 이미 계산한 per-view RGBD loss를 EMA로 저장하고, historical
  global 6-slot 중 절반을 robust-capped high-residual view, 나머지를 uniform
  random으로 선택했다. 추가 render/backward는 없었다. 결과는
  **18.364/18.368dB**, 31,338GS, online 48.273s로 paired control보다 held-out
  **−4.097dB**였다. growing map의 높은 residual은 유익한 supervision보다
  pose/occlusion 불일치 outlier를 가리켜 hard mining이 geometry를 훼손한다.
  count-only와 high-residual historical sampler를 모두 종료한다. strict 최고
  23.982dB, 1차 목표 27dB, MPS 금지/zero-tail 및 27dB 전 hard carve 보류는
  유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 least-used historical balancing — 600에서 기각)**:
  추가 view-op 없이 regular mapper의 historical keyframe 6개 global slot만 uniform
  random에서 least-used 우선(random tie-break)으로 바꿨다. 하지만 600-frame
  결과는 **19.859/19.710dB**, 33,102GS, online 48.285s로 paired control
  22.461/22.455보다 held-out **−2.602dB**였다. 모든 과거 view를 공평하게
  강제하는 것은 성장 map에서 stale/conflicting gradient를 과대표집한다. 단순
  coverage-count balancing은 종료하고, 다음 sampler는 현재 map의 residual처럼
  유효성을 직접 반영해야 한다. strict 계약과 최고 23.982dB, 1차 목표 27dB,
  27dB 전 hard carve 보류는 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 topology-only freeze — 600에서 강하게 기각)**:
  기존 freeze가 cutoff 뒤 optimizer까지 멈춰 late coverage를 잃은 효과를 분리하려고,
  새 Gaussian birth/densify/prune만 멈추고 tracked viewpoint 등록·PGBA·regular
  RGBD optimizer는 계속하는 opt-in을 구현했다. 600-frame cutoff450은
  29,929GS, online 48.353s였으나 held-out/keyframe이
  **17.135/17.345dB**로 paired control 22.461/22.455보다 held-out
  **−5.326dB** 붕괴했다. topology 안정화보다 후반 신규 표면 표현 손실이 훨씬
  크며, full 후보 cutoff899와 거의 같은 상대 시점(75% vs 72%)이므로 full로
  승격하지 않는다. RGB+IMU-only, MPS 금지, zero-tail을 준수했다. strict 최고
  23.982dB와 1차 목표 27dB, 27dB 전 hard carve 보류는 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 regular mapper target-row dense PCGrad — 600에서 즉시 기각)**:
  별도 background optimizer가 아니라 regular `map()`의 RGBD gradient를 그대로
  보존하면서, 추가 dense gradient만 `newest_frame - 150` 이전 출생 Gaussian
  행에 PCGrad+norm cap으로 합치는 opt-in을 구현했다. 600-frame paired control
  22.461/22.455dB 대비 결과는 **20.636/20.686dB(held-out −1.825dB)**,
  32,158GS, online 48.284s로 크게 악화됐다. prefix 단계부터 명확한 음성이므로
  1,253 full로 승격하지 않고 이 target-row projection 축을 종료한다. 실행은
  RGB+IMU-only, MPS 금지, fixed 1.5×, zero-tail을 준수했다. strict 최고
  23.982dB와 1차 목표 27dB는 유지하며, 27dB 전 hard carve는 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 regular-preserving mature-row polish — full strict 기각)**:
  기존 fixed-lineage 실패에서 regular gradient까지 끊은 효과를 분리하려고, full
  map을 공동 렌더하되 추가 dense gradient만 cutoff 이전 출생 행에 제한하고 별도
  Adam으로 step하는 opt-in을 구현했다. regular mapper의 gradient/densify/prune은
  old/late 모두 그대로 유지했다. 600 target300은 control 22.461 대비
  **23.444/23.297dB(+0.983 held-out)**, 1,504 step, 28,622GS, 48.266s였지만
  full target650은 **21.983/22.144dB, 1,724 step, 63,019GS, 98.966s**로 품질과
  deadline 모두 실패했다. RGB+IMU-only, MPS 금지, zero-tail은 준수했다.
  same-tensor background의 대상/스케줄 축도 종료하며, 다음은 별도 polish가 아닌
  regular mapper의 per-arrival supervision 개선이다. strict 최고 23.982dB,
  1차 목표 27dB와 27dB 전 hard carve 보류는 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 independent origin-partition dual-map union — full strict 기각)**:
  stable snapshot과 late overlay를 parameter merge 없이 최종 render-time union했다.
  point ID 기준 첫 구현은 pre-snapshot clone/split 자손까지 late row로 중복 포함해
  600-frame 20.990dB로 붕괴했으며, `unique_kfIDs > snapshot_source_frame`인 실제
  late-origin만 append하도록 수정하자 **22.665/22.368dB**, 868 step,
  33,173GS, 48.282s로 control 22.461 대비 +0.204dB 회복했다. 그러나 snapshot650
  full strict는 **22.786/22.714dB, 1,078 step, 69,386GS, 99.490s**로 strict 최고
  대비 −1.196dB이고 deadline도 1.840초 초과해 기각했다. RGB+IMU-only,
  MPS 금지, zero-tail은 준수했다. same-tensor와 submap merge/union 축은 종료하며
  strict 최고 23.982dB, 1차 목표 27dB, 27dB 전 hard carve 보류는 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 growing-map random — prefix +2.315dB, full 전부 기각)**:
  freeze 없는 random dense replay는 600-frame에서 control 22.461 대비
  **24.776dB(+2.315)**였지만 full start300은 4,427 step에도 **22.404dB**,
  start899도 22.777로 일반화되지 않았다. PGBA geometry Adam moment reset은
  22.226으로 역효과여서 원복. fixed cutoff899로 old base 40,630개를 background
  Adam, late overlay 21,963개를 regular mapper에 맡겨도 22.044dB였다.
  geometry를 막고 late map iters 7→2로 확보한 예산에 appearance random
  2,056회를 넣으면 **23.060/23.345dB, 74,368GS, 97.435s**로 deadline은
  통과했지만 최고 23.982 미달. same-global-tensor background 축은 소진했고
  다음은 keyframe-local stable submap+late overlay의 render-time union이다.
  27dB 전 hard carve 보류.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 spatial double-buffer — 600 양성, full strict 기각)**:
  stable snapshot을 random settle해 frame500에 appearance residual로 합치고 late
  overlay와 공동 렌더 reconciliation한 600-frame run은 paired control
  22.461dB 대비 **23.003dB(+0.542)**, kf +2.887dB였다. 그러나 snapshot650,
  merge/freeze1040으로 승격한 1,253-frame strict 1.5×는
  **23.782/25.039dB, 1,436 step, 65,996GS, 97.285s**였다. deadline은
  0.365초 통과하고 zero-tail/MPS 금지를 지켰지만 strict 최고 23.982보다
  −0.200dB여서 기각. prefix 이득이 full late coverage로 일반화되지 않았다.
  1차 목표는 strict held-out 27dB, hard carve는 그 전까지 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 stable-map random settle — 강한 국소 신호, 전체 27dB 미달)**:
  regular RGBD gradient를 보존하고 dense gradient를 parameter-group별 PCGrad+norm
  cap으로 더했지만 600-frame control 22.461dB 대비 최선
  **22.405dB(appearance-only, −0.056)**로 순이득은 없었다. 다음으로 frame 899에서
  GS birth/prune/map update를 멈추고 tracking+PGBA pose transform만 계속하며 남은
  스트림에서 dense settle을 실행했다. 시간순 round-robin은 16.942dB로 붕괴했지만
  fixed-map 성공 경로처럼 random view sampling으로 바꾸자 400-frame에서
  **17.767→21.767(+4.000)dB**, full strict에서 cutoff 이전 시점은 약
  **26.57dB**까지 회복했다. 그러나 cutoff 이후 새 관측을 지도에 넣지 못해 전체는
  **23.080/26.097dB, 3,399 step, 55,172GS, 97.289s**로 deadline은 0.361초
  통과했어도 27dB 미달. full completed-map snapshot을 random joint-context
  settle하고 late births를 frontier에 보존하는 residual delta merge도 600-frame
  all/appearance scope가 21.805/22.234dB로 control 미달이었다. random settle은
  유효 레버로 보존하되 단일 freeze·snapshot merge는 종료한다. 다음은 late
  overlay를 최종 공동 렌더 loss로 reconciliation하는 spatial double-buffer이며,
  strict 최고 23.982dB와 27dB 전 hard carve 보류는 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 regular-map dense 전용 iteration — 기각)**:
  independent worker가 frontier packet timing을 바꾸는 문제를 피하려고 regular
  `map()`의 총 iteration/optimizer-step/densify schedule은 고정한 채 마지막 1/7
  iteration만 causal dense RGB 12장으로 교체했다. 동일 600-frame paired control
  **22.461/22.455dB, 34,517GS, online 48.311s** 대비 dense weight 1.0은
  **22.012/21.928dB, 33,669GS, 48.287s**, weight 0.25도
  **22.035/22.035dB, 33,878GS, 48.281s**로 각각 held-out −0.449/−0.426dB였다.
  시간은 보존됐지만 최소 1회 교체에서도 현재 frontier RGBD 제약 하나를 잃는
  손해가 지배적이고, gradient를 1/4로 낮춰도 회복되지 않았다. 따라서
  dense-only replacement family는 full strict로 승격하지 않는다. 다음 품질 축은
  regular RGBD gradient를 보존한 채 dense gradient의 충돌 성분만 제한하는
  gradient projection/norm budget이며, strict 최고 23.982dB와 27dB 전 hard
  carve 보류 원칙은 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 overlap-aware joint-context/delta merge — full strict 기각)**:
  snapshot target을 현재 frontier complement와 공동 렌더해 overlap/occluder 문맥을
  보존했고, stale absolute overwrite를 막는 residual delta merge
  `frontier += α·(polished−source)`도 구현했다. 400-frame은 control 대비
  +0.178dB, 600-frame 첫 run은 +0.146dB였지만 idle guard 5/20ms 및 paired
  control에서 이득이 재현되지 않았다. authoritative 1,253-frame background-off
  paired A/B는 control **23.357/23.603dB, 77,544GS, 99.062s** 대비 delta
  **22.512/22.667dB, 76,684GS, 98.675s**로 −0.845/−0.936dB였고 둘 다
  97.65s deadline 초과. non-preemptive snapshot GPU step이 frontier packet
  timing과 densify/prune schedule을 바꾸는 것이 지배적이므로 independent snapshot
  family를 종료한다. 다음은 결정론적으로 frontier view-op를 재배분하거나 regular
  map() 내부에 dense gradient를 융합하는 방향이다. strict 최고 23.982dB와 27dB 전
  hard carve 보류 원칙은 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 dense pose-only alignment — +0.084dB지만 control 미달)**:
  `torch.autograd.grad`로 Gaussian leaf gradient를 완전히 차단하고 dense camera
  SE(3)만 보정한 뒤 같은 view로 Gaussian mapping하는 2-stage 경로를 구현했다.
  runtime assert로 Gaussian `.grad` 누출 0을 검증하고 cached pose 충돌 없이 완주.
  600-frame start300/no-align **22.234dB** 대비 1-step/84뷰는
  **22.318(+0.084)dB**, online 비용 약 +0.03초. 3-step/155회는 22.296으로
  상한이 오르지 않았고 no-dense control 22.402에도 −0.084dB였다. 따라서
  endpoint filter·slot 축소·pose alignment까지의 direct dense foreground family를
  종료하고 full strict run으로 승격하지 않는다. 다음은 final-map dense gradient의
  성장 중 소실을 막는 overlap-aware spatial submap이다. strict 최고 23.982dB와
  27dB 전 hard carve 보류 원칙은 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 causal dense pose-confidence sampler — 손실 축소, 순이득 없음)**:
  양쪽 keyframe이 도착한 dense frame의 interval alpha를 보존하고 endpoint까지의
  정규화 거리를 pose-confidence로 쓰는 sampler를 구현했다. 600-frame control
  **22.402/22.388dB** 대비 dense 3-slot 무필터는 21.867dB(−0.535),
  endpoint≤0.20은 21.955(−0.447), 교체를 1-slot으로 줄이면
  **22.262(−0.140)**까지 회복했다. endpoint≤0.10은 46개 후보로 줄어도
  22.250이라 추가 개선이 없었다. 보간 pose 오차와 tracked-global 희석이 원인인
  것은 확인했지만 control을 못 넘어 full strict run은 실행하지 않았다. 다음은
  dense pose 자체의 photometric alignment 또는 update 소실을 막는 overlap-aware
  spatial submap이며, strict 최고 **23.982dB**와 carve 보류 원칙은 유지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 snapshot/dense foreground A/B 기각)**:
  strict RGB+IMU-only 600-frame no-snapshot control은 held-out/keyframe
  **22.402/22.388dB**. target-only snapshot full merge는 400-frame control 대비
  −2.506dB, 약한 alpha 0.25도 −0.267dB였고, 공통 point ID만 섞는 evolving
  overlap merge도 **21.640dB(−0.762)**라 snapshot merge 계열을 중단한다.
  causal dense RGB 3장을 foreground global slot에 넣는 방법은 300-frame에서
  +1.035dB였으나 600-frame에서 −0.535dB로 역전했고 lag150·weight0.25도
  −0.362dB였다. update 양보다 보간 pose 신뢰도가 병목이므로 다음은 keyframe
  endpoint 근처의 arrived RGB만 고르는 pose-confidence sampler다. strict 최고
  **23.982dB**는 유지되며 27dB 전 hard carve pruning은 계속 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (프로젝트 1차 목표 확정 — strict streaming held-out 27dB)**:
  사용자 결정으로 당장의 성공 기준을 30dB가 아니라 **pure-online strict streaming
  held-out 27dB**로 확정했다. strict는 timestamp 순 Aria RGB photo+IMU-only,
  MPS 후처리 trajectory/depth/point cloud 금지, fixed 1.5× live budget,
  마지막 프레임 뒤 optimizer update 0회(zero-tail)를 모두 만족해야 한다.
  고정 calibration만 허용하며 학습 pose/depth는 당시까지의 online 추정치만 쓴다.
  27dB 달성 전 hard carve/floater pruning은 보류하고, 달성 후 carve 검증,
  그 다음 동일 strict 조건의 30dB+로 진행한다.
- **2026-07-29 (exp57 1차 목표 strict 27dB 전환 — dense 누락 수정 +0.112dB)**:
  목표를 MPS 없는 RGB+IMU-only, fixed 1.5×, zero-tail held-out **27dB 먼저**로
  조정. dense scheduler가 마지막 keyframe 쌍만 처리해 후보 약 954장 중 450장만
  등록하던 버그를 고쳐 모든 도착 완료 인접 구간을 causal하게 처리, **931장**으로
  회복했다. strict held-out/keyframe은 **23.982/24.402dB**로 +0.112/+0.102dB,
  LPIPS도 개선해 현재 최고지만 online 104.752s로 deadline 미달. SE(3) pose refresh
  batch화 후 late frontier 7→2 재배분은 4,215 update에도 **24.113dB**, frame1000
  집중은 23.879, 모든 RGB를 보존한 tracking 20→10fps는 23.417, view≤703만 독립
  polish한 temporal chunk는 overlap/occluder 부재로 **18.860dB**라 모두 기각.
  27dB 미달이므로 floater labeling과 hard carve pruning은 아직 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 frontier fast rolling — update +44.9%에도 품질 악화)**:
  MPS 없이 timestamp 순 Aria RGB+IMU만 사용. 매-step finite host sync 제거와
  queue poll 2→0.2ms로 snapshot이 아닌 최신 frontier를 직접 갱신했다. strict
  1.5× 전체에서 update는 1,441→**2,088(+44.9%)**로 늘었지만 held-out/keyframe은
  23.870/24.300→**23.728/24.170dB**, online은 **103.212s=1.585×**로 악화.
  growing map에 round-robin update를 더 넣는 축도 기각한다. 다음은 동일 예산에서
  arrived RGB를 residual·coverage·viewpoint novelty·staleness로 선별하는 축이다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 pure-online independent snapshot/double-buffer 기각)**:
  센서 입력을 timestamp 순 Aria RGB photo 1,303장+IMU로만 고정하고
  **MPS 후처리 trajectory/depth/point cloud를 절대 사용하지 않았다**. 고정 calibration
  외 pose/depth는 해당 시점까지 VIGS가 online 추정한 값만 허용했다. 별도 Gaussian
  model+Adam, stable point ID rebase, PGBA 후 causal dense-pose refresh, 종료 전
  publish를 구현해 strict 1.5× 전체 검증. all-parameter snapshot은 held-out
  **20.926dB**로 geometry drift가 컸고, rebase 때 SH appearance만 보존해도
  **23.551/23.933dB**, 73,107 GS, 3,951 update, **103.911s=1.596×**로 rolling
  23.870dB/1.569×보다 낮았다. full-scene snapshot double-buffer는 기각하며,
  다음은 arrived RGB를 frontier가 직접 소비할 때 supervision coverage를 높이고
  update를 압축하는 방향이다. 30dB 미달 map이므로 hard carve prune은 보류한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 30dB update 실행비 압축 — 미세 최적화만으로 부족)**:
  MPS 없이 Aria RGB photo+IMU replay로만 진단. PyTorch subset indexing/scatter를
  CUDA `active_indices`로 대체한 rasterizer는 gradient 상대오차 3.7e-6 이하로
  통과했지만 cached subset도 update당 **2.05%** 개선뿐이었다. single-view
  polishing의 중복 loss graph를 제거해도 15k held-out **30.321dB** 재현 시간은
  **63.53s**로 그대로였고, per-step CUDA/`loss.item()` 동기화를 milestone-only로
  바꾼 fast loop도 5k **20.95→19.30s(−7.9%)**, held-out **28.325dB**였다.
  이는 post-stream fixed-map 상한 진단일 뿐 pure-online 성공이 아니다. strict
  1.5×의 약 22초 여유에 30dB를 넣으려면 미세 최적화가 아니라 update 수 압축 또는
  별도 spatial chunk의 stream 중 독립 수렴이 필요하다. 입력 계약은 계속
  `mps_inputs=[]`, photo+IMU 및 당시 online VIGS pose/depth만 허용한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 lineage freeze 정정 재실험 — cutoff 버그 정정 후에도 기각)**:
  직전 18.004dB run은 `unique_kfIDs`(frame index)에 sensor timestamp cutoff를
  전달해 모든 Gaussian을 한꺼번에 freeze한 단위 버그가 있었으므로 **무효**로
  정정한다. frame index로 수정하고 opacity reset/scale clamp 직접 write까지
  completed mask를 적용한 유효 전체 run은 held-out/keyframe **22.002/22.216dB**,
  77,799 GS, 102.505s=1.575×였다. 이어 completed의 gradient/momentum/densification만
  막고 opacity/size prune 및 cap을 다시 허용하며, 현재 RGB+VIGS online depth만
  쓰는 background carve를 결합했지만 **21.868/22.066dB**, 57,109 GS,
  약 103.77s=1.594×였다. post-hoc online-depth floater는
  11,609/55,061=**21.084%**로 rolling 21.633%보다 −0.549%p뿐인 반면 PSNR은
  −2.002dB. 따라서 Gaussian 누적을 막아도 일부 lineage 동결이 성장 map의 전역
  visibility/gradient 결합을 깨므로 same-tensor freeze는 기각한다.
  provenance는 `strict_aria_rgb_imu_only`, `mps_inputs=[]`,
  `post_stream_refinement=false`; 학습 입력은 timestamp 순 photo+IMU와 그때까지의
  VIGS online pose/depth뿐이며 MPS 후처리 데이터는 금지한다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 strict completed-lineage same-tensor freeze — 강한 기각)**:
  Aria timestamp 순 RGB photo+IMU만 쓰는 strict 1.5× 조건에서 clone/split에도
  보존되는 `unique_kfIDs`를 lineage로 삼아, 150-frame lag를 지난 Gaussian을
  frontier Adam/densify/prune/cap에서 freeze하고 별도 background Adam으로만
  polishing했다. 200-frame smoke는 20 step 정상 실행했지만 전체 1,303-frame
  run은 1,237 step 후 held-out/keyframe **18.004/18.071dB**로 이전 strict
  rolling 23.870/24.300 대비 **−5.866/−6.229dB** 붕괴. Gaussian도
  **66,214→96,757**, post-hoc online-depth 진단 visible floater도
  **21.633%→27.840%**로 악화했고 online **102.391s=1.573× live**로 deadline도
  실패했다. separate Adam은 momentum overwrite를 막았지만 같은 tensor에서 초기
  저품질 lineage까지 prune으로부터 영구 보호한 구조가 누적을 만들었다.
  **same-tensor lineage mask 방식은 폐기**; 다음에는 별도 Gaussian model의
  spatial chunk를 독립 polish한 뒤 overlap 검증·중복 제거·merge해야 한다.
  provenance `mps_inputs=[]`, 학습 입력은 photo+IMU 및 online VIGS pose/depth뿐.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 Aria photo+IMU-only strict 1.5× — 30dB 재현 실패)**:
  `--strict_aria_online`으로 timestamp 순 RGB photo+IMU만 허용하고 MPS 경로,
  external gray/carve 입력, tail refinement를 실행 시 거부하도록 고정했다.
  PPM init과 soft carve는 도착한 RGB 및 VIGS online depth/pose만 사용. dense RGB
  GPU 영구 cache로 PGBA OOM이 난 문제를 CPU-resident view로 수정하고, background
  LR의 frontier 누출도 제거한 뒤 완주. frame 700 이후 150-frame lag를 둔
  arrived-only rolling polish는 1,441 step을 흡수했지만 held-out/keyframe은
  **23.870/24.300dB**, Gaussian **66,214개**, online **102.129s =
  1.569× live**로 1.5× deadline도 4.48s 넘었다. post-hoc online-depth carve
  진단은 visible floater 13,611/62,918(21.633%)로 30dB offline map의
  21.999%와 사실상 동급. batch4, LR×2, half→full coarse 축도 모두 30dB/시간
  동시 기준에 실패. **완성 map 15k=30.389dB 상한은 유효하지만 성장 map에 흩뿌린
  update는 소실되므로 rolling 단일-map은 기각**; 다음은 완료 spatial chunk를
  freeze/polish/merge하는 double-buffer streaming. MPS는 계속 금지.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 held-out 30dB 최초 달성 — dense RGB 4-offset)**:
  evaluator `idx%5==0`은 그대로 제외하고 dense supervision을 한 offset 239장→
  `idx%5∈{1,2,3,4}` 954장으로 확대. supervision별 **loss**를 tracked keyframe은
  RGB+BA depth+normal, dense non-keyframe은 RGB-only로 분리하되, 둘 다
  xyz/scale/rotation/opacity/color 전체 Gaussian에 gradient가 흐르게 한 것이 핵심.
  고정 online trajectory held-out/keyframe이 5k 28.236/28.109,
  10k 29.618/29.404, **15k 30.389/30.321dB**, 20k 30.505/30.428.
  15k→20k +0.116dB뿐이라 15k 채택. 반대로 parameter hard split은 25.04dB로
  붕괴, soft split 28.83, per-view exposure 28.23으로 기각 — dense photometric
  gradient가 geometry까지 도달해야 함을 대조군으로 확정. online 75.45s +
  15k refinement 62.83s = **138.28s, 2.124× live**라 30dB 품질 목표는 달성했고
  실시간화는 rolling chunk/exp58로 refinement를 숨기거나 압축하는 후속 과제.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 Aria gray geometry-only + carve-score prune — 전부 기각)**:
  VRS factory calibration으로 Fisheye624 좌·우 522장을 464 pinhole로 rectification,
  RGB와 평균/최대 0.079/0.089ms로 동기화해 실제 extrinsic pose에 연결. gray는
  xyz/scale/rotation만, RGB는 SH/color/opacity만 gradient를 허용한 50:50 5k는
  held-out **24.00→20.77dB**로 geometry 붕괴. gray 10% + xyz ±5mm/scale·rotation
  trust-region은 **24.83dB@1.470×**로 안전하지만 기존 27.87보다 −3.04dB.
  opacity를 전혀 쓰지 않은 depth-anchor carve score 상위 5%(4,010/80,205) pruning도
  **24.72→22.30dB**, 총 **1.552× live**로 품질·시간 모두 실패. 기존 exp57
  27.87dB@1.428× 채택 유지. 흑백은 다음에 photometric hard split이 아니라
  stereo metric depth/epipolar geometry constraint로 써야 함.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 최종 성공 — held-out 27.87dB @ 1.428× live)**:
  2× stream에서 causal background 5k를 전부 넣어도 24.24dB로 1.5×와 같아
  step 수가 아니라 미성숙 map에 너무 일찍 적용한 update 소실이 병목임을 확인.
  online camera pose/exposure 정렬은 crash를 고쳤지만 22.15dB로 붕괴해 기각.
  반대로 고정 map에서 camera를 건드리지 않고 non-eval dense RGB 230장으로
  Gaussian-only 5k를 돌리면 **20.25초에 held-out 27.73dB**. 최종 timestamp-paced
  1× 검증은 online map 72.49초 + dense Gaussian 5k 20.47초 =
  **92.96초(65.1초 live의 1.428×)**, held-out/keyframe **27.87/27.82dB**,
  SSIM/LPIPS 0.87185/0.25555로 **27dB@1.5× 목표 최초 달성**. 채택 레시피는
  stable-map boundary + dense RGB + pose/exposure 고정 Gaussian-only settle.
  실제 장치 adapter는 아직 없고, 무한 live에서는 완료 chunk를 freeze/polish하는
  rolling double-buffer로 이 20초 tail을 숨겨야 함. MPS는 postprocess이므로 live
  pose source가 아니며 Fisheye624+IMU localization pose를 사용해야 함.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 dense RGB gradient 상한 + 1.5× causal 통합)**:
  evaluator와 겹치지 않는 비키프레임 RGB 231장(`idx%5==2`, keyframe 제외)을 고정
  online checkpoint polishing에 추가하자 5k/45.10s held-out/keyframe이
  **22.83/23.22→26.13/27.79(+3.30/+4.57dB)**. 기존 keyframe-only 5k의 held-out
  개선폭 +2.15dB보다 **+1.15dB** 커 supervision 밀도가 gradient 품질의 핵심임을
  확인. 이어 실제 1.5× timestamp stream에서 다음 keyframe이 도착한 뒤에만 직전
  구간의 과거 RGB pose를 SE(3) 보간하는 causal dense scheduler 구현. 전체 실측은
  dense 108장+3,821 step, held-out/keyframe **24.23/24.50**으로 기존 keyframe-only
  background 23.98/24.37 대비 **+0.25/+0.13dB**, LPIPS도 개선. tracking은
  97.33s로 97.65s deadline 내였으나 mapper drain 포함 98.47s로 **0.84% 초과**.
  dense 방향은 채택하지만 5k 25.62dB 유지는 아직 실패. 다음은 2×에서 5k cap 상한과
  residual/novelty sampler를 검증. MPS는 postprocessing이므로 실제 live pose는
  Fisheye624+IMU localization이 같은 dense-view 인터페이스에 공급해야 함.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 1.5× Aria stream 검증 + 앞선 26k 해석 정정)**:
  먼저 정정: 5k full은 held-out/keyframe 25.62/27.94(+2.15/+4.03dB), 26k는
  25.69/**30.62**(+2.22/+6.71dB)로 원래처럼 keyframe 30dB를 정상 재현했다.
  held-out trajectory를 polishing 전 pose로 고정한 curve와 offline BA+final remap+
  refined pose를 반영한 기존 exp56 final을 섞어 "5k 이후 과적합"이라 단정한 것은
  과한 해석이므로 철회. 추가로 사용자의 "Aria 입력이 1.5배 느리다면?"을 실제
  timestamp interval 1.5×(65.10→97.65초) causal replay로 검증. offline과 동일하게
  camera pose까지 background 갱신한 smoke는 cached inverse tensor와 `update_pose()`
  in-place 변경의 autograd version 충돌로 실패. 안전한 Gaussian-full(SH/xyz/opacity/
  scale/rotation, RGB+depth+normal, pose/exposure 고정)로 전체 A/B: control과
  background 모두 약 102초로 **추가 지연 없이 3,194 step(5k의 64%) 흡수**,
  held-out/keyframe **23.74/24.18→23.98/24.37(+0.25/+0.19dB)**, LPIPS도
  0.4663→0.4561 개선. 하지만 고정 checkpoint 5k의 25.62dB는 유지하지 못했고,
  control 자체도 97.65초 deadline을 4.4% 초과. 다음은 2.5~3k cap과 input backlog/
  deadline token gate로 true-live deadline을 먼저 강제한 뒤 cache-safe boundary에서
  pose/exposure scope를 여는 것.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-29 (exp57 Phase 0/1 — polishing 압축 성공, SH-only scheduler 기각, true-streaming 속도 기준 반전)**:
  동일 online checkpoint의 full refinement 곡선에서 held-out이 2k/14.21s
  **+1.28dB**, 5k/36.31s **+2.15dB** 상승했지만 5k→26k 추가 156초는
  **+0.07dB뿐**(keyframe만 +2.68dB)이라 기존 26k 후반의 training-view 과적합을
  확인. SH/color-only는 더 싸지만 2k/9.30s +0.59dB, 5k/23.17s +0.73dB로 상한이
  낮음. tracking event+5ms idle guard+과거 view round-robin+SH-only causal
  scheduler를 구현해 paced 300 smoke에서 +0.24/+0.23dB를 냈으나, paced 1253
  A/B(768 step)는 held-out/keyframe −0.08/−0.04dB로 run noise를 넘지 못해
  **채택 보류**. 더 중요한 발견: source timestamp로 pace한 background-off control도
  **74.75s/65.1s=1.15배** — 기존 exp56의 44~52초(0.68~0.80배)는 unpaced reader에서
  mapper packet drop이 더 많이 일어난 처리량 수치였고 실제 live deadline 보장이
  아니었음. VIGS는 이미 RGB+IMU reader queue로 causal replay 가능하지만 실제 Aria
  live adapter는 아직 없고 MPS는 postprocessing이라 live pose source가 될 수 없음.
  다음은 paced replay를 본선 하네스로 고정해 frontier/map deadline budget을 먼저
  1.0배 아래로 만든 뒤, SH+exposure/opacity/confidence-gated geometry를 단계적으로
  연다.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md)
- **2026-07-28 (exp57/58 계획 재편 — 품질 축 우선, CUDA 후속은 번호 이동)**:
  기존 독립 exp57 카드는 없었고 exp56 Phase 9~11에 CUDA 내부 visibility skip과
  `BACKWARD::preprocess` 최적화 구상만 흩어져 있었음. 사용자 결정으로 이 고위험
  속도 축을 **exp58**로 정식 분리하고, 새 **exp57**은 실시간 품질 도약 전담으로
  재정의: frontier update와 causal background polishing을 별도 queue로 분리하고,
  랜덤 과거 뷰 대신 residual·coverage·viewpoint novelty·staleness 기반 global replay를
  사용. 첫 단계는 exp56 checkpoint에서 0/250/500/1k/2k/5k/26k polishing 압축 곡선을
  측정해 held-out 상승이 초반에 실제 존재하는지 확인하며, 이후 SH/color-only polishing을
  온라인 여유 시간에 분산. 기존 STATUS/exp56의 역사적 `exp57` 언급은 번호 재배정 전
  표현이며 현재는 **exp58을 의미함**.
  → [exp57](experiments/exp57_causal_background_polishing_plan.md),
  [exp58](experiments/exp58_cuda_visibility_backward_plan.md)
- **2026-07-28 (exp56 Phase 11 — renderCUDA 커널 레벨 멀티카메라 batch화, 결론: 채택. Phase 8b/10과 달리 첫 순이득)**:
  Phase 8/8b/10이 계속 고위험으로 미뤄온 `forward.cu`/`backward.cu` 직접 수정을
  범위를 좁혀 시도 — `renderCUDA`(forward+backward)만 `grid.z=camera`로 진짜
  배치(`preprocessCUDA`/정렬/`computeCov2DCUDA`(SE3 포즈 그래디언트 `dL_dtau`가
  있는 곳)는 카메라별 host-loop 그대로 무수정). 구현 직후 원인불명 segfault
  발생(`compute-sanitizer` 0 errors인데도 크래시) → `gdb` 백트레이스로 정확히
  진단: `focal_x_t`/`focal_y_t`를 GPU 텐서로 할당해놓고 host for문에서
  `focal_x_acc[b]=...`로 CPU가 GPU 포인터를 직접 역참조하던 버그(호스트 벡터에
  채운 뒤 한 번만 업로드하는 방식으로 수정). 재빌드 후 Phase 8b 기준 검증
  통과(forward bit-exact, backward 상대오차 atomic 노이즈 수준), length=300
  스모크 통과 후 1253 전체 실측: **`vigs_track_total` 45.79→44.00s(−3.9%),
  PSNR 23.49/23.88→23.46/23.98(무손실), rasterize avg/call 139.4→66.8ms
  (−52.1%, 배치화한 부분만 놓고 보면 launch 비용이 정확히 절반)**. backward는
  거의 그대로(348.9→368.5ms) — 배치 안 한 `BACKWARD::preprocess`가 여전히
  backward 시간을 지배하기 때문. `Training.kernel_batch_render`(opt-in, 기본
  false) 신규 플래그로 배선, 코드는 자산으로 보존.
  → [exp56 Phase 11](experiments/exp56_mapping_fixedcost_reduction.md)
- **2026-07-28 (exp56 Phase 10 — frustum pre-filter 실제 구현·1253 실측, 결론: 기각. Phase 9를 뒤집지 않고 오히려 재확인)**:
  Phase 9가 "N이 유의미하다"를 확인한 뒤, `render_filtered()`/`frustum_prefilter()`를
  실제로 구현(기존 `render()` 무수정, host-side에서 gaussian 부분집합만 뽑아 넘김,
  뷰마다 개별 필터링). 수치 검증(Phase 8b 기준, float32 atomic 노이즈 수준 일치)과
  length=300 라이브 스모크 테스트 통과 후 1253 전체 실측: **온라인 루프 −0.89%
  (45.79→45.38s, 잡음 수준), PSNR −0.35/−0.29dB, map() 성사 36→30회(−17%) — 기각.**
  `map_call` 로그로 원인 진단: rasterize avg/call이 139ms→**290ms로 오히려 2배
  느려짐** — 필터링 자체(행렬곱+5개 인덱싱 연산, map() 1회당 최대 17번)가 만드는
  추가 커널 launch 비용이 줄어든 gaussian 수만큼 아낀 시간보다 컸음. **이건 Phase
  9를 뒤집는 게 아니라 오히려 더 강하게 재확인** — "N-비례가 유의미하다"와
  "host-side에서 N을 줄이면 공짜로 이득"은 다른 명제이고, launch 자체가 비싸다는
  Phase 9 결론상 필터링을 CUDA 커널 내부(preprocessCUDA)에 융합해야만 진짜 이득이
  남 — 처음부터 고위험으로 미뤄온 forward.cu/backward.cu 직접 수정과 결국 같은
  결론으로 수렴. `Training.frustum_prefilter` 기본값 false 유지(코드는 `batch_render`
  와 같은 패턴으로 자산 보존).
  → [exp56 Phase 10](experiments/exp56_mapping_fixedcost_reduction.md)
- **2026-07-28 (exp56 Phase 9 — "고정비 지배" 결론 재검증: 통제된 마이크로벤치마크로 N도 상당히 유의미함을 확인, exp57 방향 재조정)**:
  지도교수 미팅 피드백("view 개수보다 iter당 시간이 중요, backprop할 gaussian을
  visibility로 선별하면 쉬움")이 Phase 0/5의 "고정비(N-무관) 지배" 결론과
  충돌한다는 걸 exp57 설계 논의 중 발견 — 실측으로 재검증. 카메라 1개 고정,
  gaussian N만 1만~9만(exp56 최종 체크포인트 실측 서브샘플)으로 바꿔 forward/
  backward를 반복 측정. **방법론 버그 발견**: `torch.profiler` key_averages()가
  C++ 확장 wrapper(`_RasterizeGaussians[Backward]`)의 self_device_time에 자식
  커널 시간을 중복 합산(N=90,770에서 프로파일러 총합 8.39ms vs 순수 wall-clock
  3.43ms, 2.4배 과대) — `torch.cuda.synchronize()` 기준 wall-clock으로 교차검증해
  이걸 잡아냄. **진짜 결과**: forward는 N-비례가 56.4%, backward는 84.6%(R²=0.988/
  0.999)로 N이 상당히 유의미 — Phase 0/5의 "N-무관 고정비 지배"는 다변량 실측
  로그에서 여러 항목이 섞여 계수가 희석된 결과였을 가능성. 지도교수의 visibility
  기반 backprop 선별 제안이 이 결과로 재확인됨(backward N-slope이 forward의
  3.3배) → exp57에 "coarse frustum pre-filter로 유효 N 절감" 항목 공식 추가.
  → [exp56 Phase 9](experiments/exp56_mapping_fixedcost_reduction.md)
- **2026-07-27 (exp56 Phase 8b — batch 렌더링 실제 구현·검증·통합, 결론: 정확하지만 속도 이득 없음, 채택 안 함)**:
  사용자가 "물어보지 말고 batch cuda 될 때까지 끝까지 가보라"고 명시적으로
  요청 — Phase 8에서 보류했던 실제 구현에 착수. 기존 단일-카메라 CUDA 커널
  (forward.cu/backward.cu)은 VIGS가 이미 크게 확장한 버전(SE3 리대수 카메라
  pose 그래디언트까지 손으로 미분한 커널)이라 직접 수정하는 대신, **커널은
  1바이트도 안 바꾸고 C++에서 카메라 수만큼 루프 도는 안전한 설계**로
  신규 구현(`rasterize_points_batch.{h,cu}`). 실행 전 raw 바인딩 레벨(forward
  bit-exact, backward float32 잡음 수준) + Python 통합 레벨(실제 Camera/
  GaussianModel로 재검증) 둘 다 수치 검증 통과 후 통합 — 이 과정에서 실제
  버그 2건 발견·수정(`colors_precomp` 자리에 `sh` 오기입, `viewspace_points`
  슬라이싱으로 `.grad`가 안 채워지는 leaf-tensor 문제).
  **1차 실전 실행(1253 전체)에서 PSNR 붕괴(6.65dB) 발견** — 원인은
  `render_batch()`의 `depth` 반환 shape이 `render()`의 `(1,H,W)` 관례와
  다른 `(H,W)`였던 것: `get_loss_normal()`의 reshape 로직이 매 호출 조용히
  실패하고 `except Exception: pass`가 이를 은폐(시간이 34s로 빨라 보였던 것도
  batch화 덕이 아니라 손실 계산 자체가 거의 안 되고 있었기 때문). 격리
  수치검증은 이 project-specific loss 함수를 안 건드려서 못 잡아낸 사례 —
  "커널 수학이 맞다"와 "실제 파이프라인 통합이 맞다"는 다른 질문임을 재확인.
  수정 후 재실행: **크래시 없음, PSNR도 오히려 소폭 개선(23.55/24.07)했지만
  시간은 개선 없음**(45.79→47.37s, 정규 호출 평균 761.6ms→755.7ms로 <1%
  차이) — Phase 8에서 `torch.profiler`로 예견한 "진짜 병목은 CUDA 커널
  실행 자체라 Python 오버헤드만 없애는 걸로는 이득이 없다"가 실측으로
  확정됨. `batch_render` 기본값 false로 원복(채택 안 함), 코드는 향후
  커널-레벨(forward.cu/backward.cu 자체에 batch 차원을 넣는) 작업의 기반
  자산으로 보존. exp56 최종 채택 레시피는 Phase 1+4+7+8(카메라 캐싱)까지 —
  45.79s, 실시간 배수 0.70배, PSNR 23.49/23.88로 변경 없음.
  → [exp56](experiments/exp56_mapping_fixedcost_reduction.md)
- **2026-07-27 (exp56 Phase 8 — batch 렌더링 구현을 프로파일로 먼저 검증, 대신 무위험 카메라 캐싱 발견해 이 세션 최고 ROI 달성)**:
  사용자가 "batch 구현 ㄱㄱ"(Phase 5/7에서 식별한 rasterizer 멀티카메라
  batch화) 요청 — 실제 CUDA 커널 수정 전에 `torch.profiler`로 `render()`
  1회를 격리 분석. **확인: Python autograd 디스패치 오버헤드는 작고(0.1~
  0.14ms/call), 뷰-연산당 고정비의 정체는 진짜 CUDA 커널 실행/launch** —
  즉 batch화는 forward.cu/backward.cu(~2800줄)의 타일 정렬·블렌딩 커널
  자체를 고쳐야 하는 큰 작업이고, 그래디언트가 조용히 틀려질 수 있는
  위험도가 Phase 3(stream 분리, 크래시로 바로 티가 남)보다 높음 — 이번
  세션에서 안전하게 검증까지 마치기 어렵다 판단해 **보류**. 대신 프로파일링
  중 **`Camera.world_view_transform`/`full_proj_transform`/`camera_center`가
  카메라 pose가 안 바뀌는데도 매 `render()` 호출마다 `torch.linalg.inv()`를
  포함해 재계산**되고 있음을 발견 — R/T가 바뀌는 지점이 `update_RT()`
  단 한 곳뿐임을 grep으로 확인한 뒤 세 property에 캐싱 추가(그래디언트
  수학은 안 건드리는 무위험 변경). **결과: 시간 −3.0%(47.20→45.79s), PSNR
  +0.52/+0.45dB, map() 성사 26→36회(+38%) — 전부 개선, 이 세션 최고 ROI.**
  exp55 baseline 대비 최종 누적: **45.79s(실시간 배수 0.70배, −23.4%),
  PSNR mean +0.88dB·kf +0.93dB** — 시간을 거의 1/4 줄이면서 PSNR을 거의
  1dB 끌어올린 결과. batch 렌더링 자체는 실시간 여유가 커져 시급성이
  낮아진 채 고위험 후보로 계속 보류.
  → [exp56](experiments/exp56_mapping_fixedcost_reduction.md)
- **2026-07-27 (exp56 Phase 7 — Phase 6과 정반대: 프론티어 window 보존한 채 과거-뷰만 늘리니 PSNR 개선, n_global_views=6 채택)**:
  Phase 6 실패 원인("프론티어가 과거 keyframe과 gradient 예산을 경쟁")을
  사용자가 정확히 짚어 "그럼 window는 안 건드리고 `include_global`의
  하드코딩된 `2`(iteration마다 과거 keyframe 랜덤 2개 추가)만 늘리면 안
  되냐"고 제안 — `Training.n_global_views`로 config화해 6/10 두 지점 테스트.
  **결과: 둘 다 PSNR 개선(+0.17~0.30dB), 시간 비용은 무시할 수준(+0.25~
  0.9%)** — Phase 6과 정반대. 6과 10은 PSNR 동급(수확체감)이라 시간·coverage·
  궤적이 더 나은 `n_global_views=6` 채택. exp55 baseline 대비 최종 누적:
  **47.20s(−21.1%), PSNR mean +0.36dB·kf +0.48dB, 궤적도 개선** — 시간과
  품질을 동시에 끌어올린 결과. 사용자가 이어서 "batch 구현 ㄱㄱ" 요청 —
  rasterizer 멀티카메라 batch 착수(Phase 8, 진행 중, 별도 기록 예정).
  → [exp56](experiments/exp56_mapping_fixedcost_reduction.md)
- **2026-07-27 (exp56 Phase 6 — iters↓·n_view↑ 재배분 품질 가설 기각, window를 키울수록 PSNR 단조 악화)**:
  Phase 5 회귀식("같은 iters×n_view 예산이면 시간은 그대로")에서 나온
  자연스러운 후속 질문 — "그럼 iters를 낮추고 카메라 뷰를 늘리면 다양한
  뷰를 봐서 품질이 좋아지지 않을까"를 실측. `Training.window_size`가 로드만
  되고 실제로는 한 번도 안 쓰이던 dead config였음을 발견(`current_window`
  상한이 `10`으로 하드코딩, 우연히 config 기본값과 일치) — 실제 로직에
  연결해 두 지점(window=15/iters=5→n_view=16, window=19/iters=4→n_view=20,
  둘 다 iters×n_view는 baseline과 비슷하게 유지) 테스트. **결과: 시간은
  회귀식 예측대로 거의 무변화(46.2~46.3s)지만 PSNR이 −1.09~1.32dB(축1)→
  −3.46~3.64dB(축2)로 window를 키울수록 단조 악화** — 노이즈(±0.24~0.33dB)
  를 훨씬 벗어나는 명백한 반증. 3번째 지점(window=25/iters=3)은 추세가
  이미 명확해 실행 없이 기각 확정. 원인 분석: window를 키우면 incremental
  SLAM의 "프론티어"(최근 keyframe, 아직 안 수렴한 영역)가 과거 keyframe들과
  제한된 gradient 예산을 나눠 쓰게 되고 iters까지 줄어 수렴이 희석되는
  구조 — Phase 5 회귀식은 순수 연산 시간 모델이라 이런 최적화 동역학은
  설명 못 함, 시간과 품질이 서로 다른 메커니즘임을 확인. window_size는
  기본값(10)으로 원복(코드 연결 자체는 유지). **함의**: CLAUDE.md 로드맵의
  "dense-frame supervision"(뷰 개수를 늘리는 방향)을 나중에 시도할 때
  단순히 뷰만 늘리면 역효과가 날 수 있다는 경고 — 프론티어 집중 설계가
  같이 필요.
  → [exp56](experiments/exp56_mapping_fixedcost_reduction.md)
- **2026-07-27 (exp56 Phase 5 — 파트별 시간을 파라미터 회귀식으로 규명, `iters×n_view`가 압도적임을 계수로 확정)**:
  "40초를 파트별로 나누고, 각 파트가 어떤 param에 종속되는지, 관계식(추세선)을
  꼼꼼히 규명해달라"는 요청. 세션 전체 실험(exp55~56, 11개 run, 548개 실제
  `map()` 호출)의 기존 `map_call` opt-in 로그(`iters`/`n_view`/`n_gauss`
  메타)를 처음 집계해 최소자승 회귀(`scripts/analysis/
  exp56_fit_timing_model.py`, 신규 재사용 도구). **직렬(GPU 경합 0) 데이터
  기준 R²=0.93~0.998**로 rasterize/loss_compute/backward/optimizer_step
  각각의 관계식 도출(실측 대비 5% 이내로 검증 통과). 결론: **`iters×n_view`
  (반복 횟수 × 카메라 수) 항의 계수가 압도적**(뷰-연산 1회당 ≈3.5ms 고정),
  gaussian 수 계수는 그 1/10 수준(1000개당 0.005~0.13ms), 해상도 계수는
  통계적으로 0과 구분 안 됨. 병렬로 재피팅하면 고정비 계수만 거의 2배로
  뜀(gaussian/해상도 계수는 그대로) — GPU 경합이 "커널 launch 대기시간"만
  정확히 부풀린다는 걸 계수 레벨로 확인. **"왜 n_view에 이렇게 종속적인가"도
  코드로 규명**: `vigs/gaussian/renderer/__init__.py::render()`가 원본
  3DGS(Inria) 코드 그대로라 애초에 카메라 1대 전용(batch 미지원) —
  `map()`이 Python for문으로 카메라를 하나씩 순차 처리하며 고정비를 매번
  새로 지불하는 구조. **다음 후보 식별(고위험, 미착수)**: rasterizer가
  멀티카메라 batch를 지원하면 뷰당 고정비의 최대 91%(n_view=11 기준)를
  아낄 여지 — `thirdparty/diff-gaussian-rasterization` CUDA 소스 수정이
  필요해 Phase 3의 stream-분리 크래시와 같은 성격의 리스크, 별도 신중한
  라운드로 분리.
  → [exp56](experiments/exp56_mapping_fixedcost_reduction.md)
- **2026-07-27 (exp56 Phase 4 — 이 세션 최대 발견: map() 호출 26회 중 2~3회가 mapping 시간의 49% 차지, init_itr_num 1050→600 채택)**:
  "1iter당 연산량을 줄이려면 어떤 핵심 부분을 건드려야 하나, 최소 50% 줄일
  수 있는 지점을 알려달라"는 요청에 `/loop`로 반복 조사. 그동안 한 번도
  집계하지 않았던 `map_call` opt-in 로그(`iters`/`n_view`/`n_gauss` 메타)를
  처음 파싱 — **`map()` 호출 26회가 균일하지 않았음을 발견**: 정규 keyframe
  (21회, iters=7)·PGBA(4회, iters=20) 외에, **맵 최초 초기화 + IMU 재초기화
  시(`track_frontend.py`의 `remove_all_gaussians()`가 `t1==imu_late_init_from`
  일 때 gaussian을 통째로 삭제) 무거운 초기화 경로(iters=90~131)를 타는
  호출이 2~3회 있는데, 이 소수 호출이 합쳐서 전체 mapping 시간의 49.3%를
  차지**하고 있었음. `Training.init_itr_num`(초기화 반복 횟수 기준값,
  1050)을 300/600으로 낮춰 재검증 — 300은 시간 최대(46.15s)지만 PSNR
  −0.35~0.44dB로 실손실(노이즈 ±0.24~0.33dB 초과) → 기각. **600은 시간
  −6.2%(50.17→47.08s) 확보하면서 PSNR은 사실상 무손실(kf 오히려 +0.05dB),
  map() 성사 횟수 26→30회 증가** → 채택. **exp53+54+55+56 누적 최종: 47.08s,
  실시간 배수 0.72배(exp55 baseline 대비 −21.3%), kf PSNR 23.21(+0.26dB
  개선)**. 미해결 한 가지: `remove_all_gaussians()`가 코드상 정확히 한 번만
  조건 성립하는데 실측 로그엔 초기화급 호출이 2~3회로 보임 — 정확한 원인은
  다음 조사 후보.
  → [exp56](experiments/exp56_mapping_fixedcost_reduction.md)
- **2026-07-26 (exp56 부록 — render_downsample 무효과가 GPU 경합 때문 아니냐는 재검증, 경합 가설 기각)**:
  Phase 2/3의 "데이터量(픽셀·gaussian 수)을 줄여도 mapping이 안 빨라진다"는
  결론이 전부 병렬(`parallel: true`) 모드에서만 나온 것 아니냐는 재확인
  질문 — 순수 직렬(`parallel: false`, tracking과 GPU 경합 0)로 iters=7
  baseline vs render_downsample=2(픽셀 1/4)를 재비교. **결과: 직렬에서도
  rasterize/backward/loss_compute가 겨우 −3.4%/−1.0%/−1.9%만 감소**(병렬
  측정치 −5.5~−7.7%보다도 작음) — 경합 가설 기각, 데이터量은 병렬·직렬
  무관하게 이 시간 구조를 거의 안 좌우함이 재확인됨. 대조로 `iters`
  10→7은 직렬에서도 −20~24%로 확실히 비례(rasterize −22.0%, backward
  −24.2%, loss_compute −20.9%) — "GPU 연산량"은 (a)커널 1회가 처리하는
  데이터量(거의 공짜)과 (b)커널 호출 횟수(iters, 거의 선형)로 나뉜다는
  구조적 사실을 병렬/직렬 양쪽에서 확정.
  → [exp56](experiments/exp56_mapping_fixedcost_reduction.md)
- **2026-07-26 (exp56 — mapping 고정비 규명 + iters 10→7 채택, 전 지표 동시 개선)**:
  "gaussian 개수를 줄여도 왜 속도가 안 줄어드나"는 사용자 질문에 답하려
  기존 `_Sect` 세부 타이밍 계측(rasterize/backward/loss_compute/optimizer_step/
  densify_prune, 신규 실행 없이 exp55의 직렬 재실행 timing.csv 재분석)을
  뜯어봄. **Phase 0**: 순수 map() 68.16s 중 rasterize 40%+backward 34%+
  loss_compute 24% — loss_compute는 순수 픽셀(해상도) 고정비로 gaussian
  개수(N)와 완전 무관, rasterize/backward도 이 N 규모(85k~130k)에선 exp54
  축6+2·exp55 Phase2가 반복 확인한 대로 고정비가 N-비례 항을 압도 — **N을
  줄이는 레버가 이미 소진됐음을 원리적으로 확정**. **Phase 1**: 그렇다면
  N 대신 `iters`(고정비에 곱으로 걸림)를 낮추는 실험 — `map()` iters
  10→7→5 스캔. **결과: iters=7에서 시간 −16.1%(59.80→50.17s), PSNR
  mean/kf 둘 다 +0.21dB 개선, map() 성사 횟수도 22→26회 증가**라는 전
  지표 동시 개선(오늘 오전 반대 방향 iters↑ 테스트의 정확히 대칭 결과 —
  `_gs_queue` 드롭 정책 하에서 coverage가 반복 깊이보다 지배적임을 양방향
  실험으로 재확인). iters=5는 7과 사실상 동급(수확체감) → **iters=7 채택**.
  **Phase 2**: 이 새 baseline 위에 exp54 축4(render_downsample=2)도 재검증
  — 시간 이득 −1.7%뿐에 PSNR −0.8dB 손해로 기각(구 baseline 때와 같은 결론
  재확인). exp53+54+55+56 최종 = **50.17s, 실시간 배수 0.77배(예산
  대비 여유 3배 확대), PSNR 22.82/23.16(exp55 대비도 개선)**.
  → [exp56](experiments/exp56_mapping_fixedcost_reduction.md)
- **2026-07-26 (exp56 Phase 3 — coverage/GPU경합 직접 겨냥 3축 전부 기각)**:
  사용자 제안으로 `queue_size`↑·CUDA Graph·mapping 전용 stream 분리 3축을
  전부 실행. **`queue_size` 2→4**: 역효과(50.17→52.38s, PSNR −0.25/−0.11dB,
  map() 성사 횟수도 26→25회로 오히려 감소) — 드롭 정책이 "최근 N개만 유지"라
  버퍼가 클수록 mapper가 더 오래된 packet부터 처리하게 돼 신선도만 나빠짐,
  기각·`queue_size=2` 유지. **CUDA Graph**: 조사 후 구현 안 함 — keyframe마다
  gaussian 개수·`current_window` 구성이 달라 거의 매 호출 재capture 필요(Adam도
  `capturable=True` 미설정), 재capture/재컴파일 비용이 iters=7 루프 절감분보다
  클 가능성이 높아 이 workload(동적 shape)엔 구조적으로 안 맞음 — exp53
  축D와 같은 성격의 "조사 후 기각". **mapping 전용 CUDA stream 분리**: 구현
  중 레이스 컨디션을 코드 리딩으로 먼저 발견해 수정했음에도(`demo.py`의
  `_gs_queue.join()` 뒤 `wait_stream` 추가) **실행하자 keyframe 10~11에서
  CUDA illegal memory access로 크래시** — 레포 전체에 명시적 stream 관리가
  없어 tracking/mapping이 legacy default stream의 암묵적 교차동기화로
  우연히 "안전"했던 것으로 추정, custom rasterizer(`thirdparty/diff-gaussian-
  rasterization`)가 진짜 동시실행엔 미검증 상태. 안전하게 프로세스 종료·
  `nvidia-smi`로 GPU 정상 확인, 코드는 기본 off로 남기고 경고 주석 추가.
  **exp56의 실질적 성과는 Phase 1(iters 10→7) 단독으로 확정** — 50.17s,
  실시간 배수 0.77배, PSNR 22.82/23.16.
  → [exp56](experiments/exp56_mapping_fixedcost_reduction.md)
- **2026-07-25 (exp55 부록 — mapping iters 상향 테스트, 기각)**: "실시간이 되긴
  하는데 품질이 아쉽다, 남는 예산(5.3s)만큼 mapping iters를 더 줄 수 있지
  않나"는 질문에 직접 실측. 정규 keyframe `map()` 호출의 `iters`를 10→15,
  10→20으로 올려 각각 1253 전체 재실행(그 외 exp55 최종 레시피 동일). **결과:
  iters=15는 예산 내(62.53s, 0.96배)지만 PSNR 22.36/22.66로 baseline(22.61/
  22.95)보다 악화, iters=20은 PSNR 뒤섞이면서 예산까지 초과(65.91s, 1.01배)**.
  원인: `_gs_queue`의 드롭-온-풀 정책 — iters를 올릴수록 `map()` 1회가 느려져
  mapper가 더 뒤처지고, 처리되는 keyframe 수 자체가 줄어듦(22→19→16회) —
  "한 keyframe에 더 깊게"가 "더 적은 keyframe만 커버"로 상쇄되고도 남음.
  **결론: `iters=10` 유지(기각), 다음 후보는 keyframe coverage를 지키는
  `Training.queue_size`(현재 2) 확대.** → [exp55](experiments/exp55_adaptive_density_carve_plan.md)
- **2026-07-23 (exp55 부록 — 직렬 실행으로 tracking/mapping 순수 시간 분리, "tracking-bound" 결론이 병렬 한정이었음을 발견)**:
  "지금 상태로 직렬 돌리면 각 프로세스 순수 시간이 어떻게 되나" 확인 요청 →
  `Training.parallel: false`로 exp55 최종 레시피 그대로 재실행. **순수 tracking
  27.9s vs 순수 mapping 80.1s**(직렬 총합 114.5s, `N,gs_mapping`/`N,pgba_call_gs`
  블로킹 mapping 태그 합을 빼서 분리 — tracking-only가 motion_filter+frontend+
  pgba_run 합(27.85s)과 거의 정확히 일치해 교차검증됨). 이게 exp54가 확정한
  "tracking-bound"(병렬에서 tracking 50.87s>mapping 47.92s)와 정면 모순돼
  파고든 결과 **두 가지 발견**: ①**GPU 경합이 병렬 tracking을 거의 2배로
  부풀림** — 순수 27.9s vs 병렬 측정 50.87s, 차이 23초가 mapping과 GPU를
  나눠 쓰는 경합 비용(세션 초반의 정성적 "gs_parallel에서 frontend가 느려진다"
  가설이 정량 확인됨). ②**병렬은 "겹쳐서 숨기는" 것뿐 아니라 mapping 작업
  자체를 skip하고 있었음** — `map()` 호출 횟수 직렬 110회 vs 병렬 22회(5배
  차이), `_gs_queue`가 mapper가 못 따라잡으면 오래된 패킷을 버리는 구조라
  keyframe의 약 80%가 매핑 업데이트를 못 받음(최종 gaussian 수는 85k~90k로
  비슷하지만 densify/최적화 반복 횟수는 5배 차이). **함의**: 현재 실시간
  배수(0.92배)는 진짜지만, 그 안의 tracking·mapping 배분은 순수 아키텍처
  비용이 아니라 큐 드롭 정책+GPU 경합의 부산물 — "tracking-bound"라는 exp54
  표현은 병렬 실행 조건 한정이었음을 명확히 정정. 다음 조사 후보: `queue_size`
  확대로 드롭을 줄이며 실시간 예산 안에 드는지, GPU 경합을 줄이는 CUDA stream
  우선순위 스케줄링으로 tracking의 23초 경합 비용을 회수할 수 있는지.
  → [exp55](experiments/exp55_adaptive_density_carve_plan.md)
- **2026-07-22 (exp55 Phase 3 완료 — region GT 없이 새 floater 지표를 직접 만들어 carve loss 효과 검증, 가시 floater -7.5%·PSNR 비용 없음)**:
  "carve loss까지 구현해보고 의미있는지 확인해달라"는 요청. 기존 표준 지표
  `floater_metric_region.py`가 `data/03_rgb_3dgs_full`(ORB 배치) 좌표계 전용
  수동 라벨 GT라 1253/VIGS엔 적용 불가함을 코드로 확인 — 지표 없이 채택/기각을
  판단하지 않고, **carve_loss.py 자신의 검증된(AUC 0.98) 신호 설계**(transit/
  terminal ray-cast 필드 → rho → w=rho·min(d5nn_slam/τ,1))를 오프라인 진단
  지표로 새로 구현해 직접 검증. `gs_backend.py`에 `_export_depth_anchors()`
  신규 — VIGS 자신의 BA-정제 추적 depth(학습된 가우시안과 무관)를 성기게
  unprojection해 COLMAP 포맷으로 export, exp43의 "depth-anchor carve" 선례를
  그대로 따름(ORB 대신 depth 언프로젝션을 anchor로). **실측 중 버그 2건 발견·
  수정**: `1./disps_up`가 0-disparity에서 Inf를 내는데 첫 필터가 못 거름(anchor
  좌표 NaN까지 오염) → `isfinite` 추가, 그래도 남는 초원거리 값(수백~수천m)엔
  상한(`d<20.0`)도 추가 — 두 버그 다 "혹시나" 하고 실제로 값 범위를 찍어봐서
  발견([[feedback_verify_unmeasured]] 원칙 재확인). `scripts/analysis/
  exp55_score_carve_vigs.py`(신규, 재사용 가능) 작성해 이 필드로 최종 PLY의
  각 gaussian에 score를 매겨 carve_lambda=0/0.05를 동일 조건에서 비교.
  **결과: 가시(op>0.3) floater(score>0.3) 수 14,199→13,066(−8.0%), 비율
  18.76%→17.35%(상대 −7.5%), 평균 score(전체/가시) 둘 다 −4~5%** — 네 지표가
  전부 일관되게 개선(우연이라기엔 방향이 너무 일치). 동시에 **PSNR은 22.53/
  22.84→22.61/22.95로 오히려 소폭 상승, evo APE·시간도 사실상 동급** — 이전
  라운드에서 관측했던 "carve PSNR 비용 −0.1~0.3dB"는 단일 비교의 노이즈였던
  것으로 재해석(이번엔 매칭 페어로 재측정). **결론: carve loss는 거의 공짜로
  floater를 줄임 — `carve_lambda=0.05` 채택.** 한계: carve-on/off 각각 단일
  비교라 이 지표 자체의 run-to-run 노이즈 폭은 아직 미측정, 가시 floater
  문지방(op>0.3·score>0.3)은 carve_loss.py 원 설계값을 그대로 가져온 것으로
  이번 VIGS 적용에 대해 사람이 재라벨링 검증한 건 아님 — 두 한계 다 정직하게
  기록. → [exp55](experiments/exp55_adaptive_density_carve_plan.md)
- **2026-07-22 (exp55 Phase 1+2 구현·실행·검증 — 평균 gaussian 수 −35.9%, PSNR 손실 없음. Phase 3도 구현·실행했으나 floater 지표 부재로 기본 off)**:
  "평균 gaussian per frame 수가 확실히 줄어서 mapping 속도가 빨라졌으면 하는 게
  목적, phase1~3 다 구현·실행해달라"는 요청에 따라 `/loop`로 전부 실행.
  **Phase 1(캘리브레이션)**은 계획했던 "로컬 영역 독립 학습" 대신 시간 내 가능한
  실용적 대체 설계로 실행 — 같은 시퀀스를 dense(`ds=64`)/sparse(`ds=384`) 두
  전역 예산으로 돌려 keyframe별 PSNR을 비교(`eval_rendering_kf`·
  `create_pcd_from_image_and_depth`에 opt-in per-keyframe 로깅 신규 추가).
  **결과: Sobel 평균과 "밀도 증가로 얻는 PSNR 이득" 사이 Pearson r=0.538**(113
  keyframe) — 사용자 가설을 실측으로 확인, 상위 10%(디테일 多)는 +0.70dB
  이득·하위 10%(단조)는 −2.70dB 손해. 이 곡선을 10/90 백분위 2점 선형보간으로
  피팅해 배율 함수(0.91~1.57배)로 저장(`config/exp55/aria1253_content_curve.json`,
  저장소에 영구 저장). **Phase 2(적응 예산 컨트롤러)**: `pcd_downsample`
  128→256·`pcd_downsample_init` 32→64로 베이스를 훨씬 성기게 하고, 그 위에
  프레임별 배율을 곱함. 사용자가 요청한 "명시적 max cap"도 신규 구현
  (`enforce_kf_caps()` — 기존에 있던 per-gaussian 출생 keyframe 태그
  `unique_kfIDs`로 그룹핑해 상한 초과 keyframe의 저opacity 가우시안부터 pruning,
  growth_allowance=2.0로 densify가 초기 배정의 최대 2배까지는 자유롭게 채우도록
  허용). **결과: 평균 gaussian 수 94,219→60,439(−35.9%), 최종 개수
  131,771→85,196(−35.3%), PSNR 22.78/23.14→22.77/23.30(동급, kf는 오히려
  +0.16dB), evo APE(Sim3) 2.41→1.90cm(오히려 개선)** — 사용자가 명시한 목표를
  정확히 달성. 시간은 61.34→59.39s(−3.2%)로 상대적으로 작은데, exp54에서 이미
  규명한 tracking-bound 상태(tracking 50.87s>mapping 47.92s) 때문 — gaussian
  절감이 wall-clock엔 부분적으로만 반영됨, 이 결과의 진짜 가치는 "속도"보다
  "동일 품질에 필요한 연산량 자체가 35% 줄었다"는 것. **Phase 3(carve loss
  온라인 근사)**: `carve_loss.py`의 배치(전체 카메라 사전 확보) 구조를 그대로
  못 쓴다는 기존 판단대로, voxel field 대신 훨씬 가벼운 **depth-violation
  전용 근사**를 신규 설계·구현 — VIGS가 매 `map()` 호출마다 이미 갖고 있는
  BA-정제 추적 depth(`disps_up`)를 신뢰 표면 삼아, 렌더 depth가 그보다
  margin 이상 카메라 쪽으로 가까운 픽셀만 편측 페널티(기존 대칭 L1 depth
  loss와 달리 floater 특유의 신호만 잡음). 테스트 결과 크래시 없이 정상
  동작하나 PSNR −0.1~0.3dB 비용 확인, **floater가 실제로 줄었는지 잴 지표가
  없어(region GT를 incremental 결과물에 적용 가능한지 미확인) 기본값
  off로 유지** — Phase 3 완결의 다음 과제는 코드가 아니라 floater 품질 지표
  확보. Phase 2Q(품질 지향 스윕)는 이번 라운드 미실행. → [exp55](
  experiments/exp55_adaptive_density_carve_plan.md)
- **2026-07-22 (exp55에 Phase 2Q 추가 — 품질(pure_online PSNR) 지향 스윕, 사용자가 우선순위를 속도보다 품질로 명시)**:
  exp55 계획 직후 사용자가 우선순위를 명확히 함 — 시간 단축은 "되면 좋은" 수준이고
  **1순위는 pure_online PSNR을 exp53+54 최종 레시피(22.78/23.14) 위로 실제로 끌어올리는
  것**. exp54 축7(PPM, 동일 예산에서 +0.16dB)을 반대 방향으로 활용 — 예산을 아끼는
  대신 **늘리는** 쪽으로 스윕하는 Phase 2Q 신설: Q1(`pcd_downsample`을 128보다 낮춰
  96→64→48까지, PPM 유지) Q2(PPM 가중치 강도 γ 스윕, `p ∝ sob^γ`로 일반화해 얼마나
  세게 엣지에 몰아줘야 최적인지 탐색) Q3(`pcd_downsample_init`을 32보다 낮춰 초기
  keyframe 골격 품질에 투자, axis2/6+2와 정반대 방향) Q4(`densify_grad_threshold`
  하향 재평가, exp54는 상향 방향만 봤음). **Q1·Q3가 헤드라인 후보** — exp54는 지금까지
  예산을 줄이는 방향만 스캔했고, 늘리는 방향은 이 incremental 트랙에서 한 번도
  스캔된 적이 없음. 현재 실시간 레시피(61.34s)가 예산(65.1s) 대비 ~6% 슬랙을
  남기고 있어 최소한 이만큼은 품질에 재투자 가능. Phase 1(캘리브레이션) 없이도
  Q1부터 바로 착수 가능해 실행 순서를 Phase 2Q 우선으로 재배열. 여전히 계획
  단계, 미착수. → [exp55](experiments/exp55_adaptive_density_carve_plan.md)
- **2026-07-22 (exp55 신설 — 내용-적응 per-frame gaussian 예산 + carve loss 이식 계획, 3단계)**:
  사용자 제안: exp54가 `pcd_downsample`을 장면 전체에 균일 적용했던 것과 달리,
  keyframe마다 GT 이미지의 Sobel/std(엣지·디테일 정도)에 맞춰 gaussian 예산을
  차등 배정 + init은 최소로 주고 densify로 채움("적게 시작해 키우는 쪽이 싸다")
  + densify가 활발해지며 생기는 floater 위험은 carve loss로 통제. **exp54
  축2·축6+2 결과와의 긴장 관계를 먼저 명시**: 그 실험들은 "전역적으로 성기게
  시작 + 보정 증식 억제"였고 시간 절감이 없었음(이미 tracking-bound라 gaussian
  개수 자체가 더 이상 지배 변수가 아님을 확인) — exp55는 "총량 축소"가 아니라
  "같은 총량의 효율적 재배분"이 목표라는 점이 다름, 다만 "적게 시작해 키우는
  게 싸다"는 전제 자체는 재검증 필요. **exp44 Instant-GI/PPM 선례**(44e2: 신경망
  PPM≈수제 Sobel 확률맵)를 근거로, 관계 캘리브레이션도 신경망 대신 Sobel/std
  직접 계산으로 하는 쪽을 권고(exp54 축7에서 이미 이식한 계산 재사용 가능). 3단계:
  ①Sobel/std↔PSNR-고정 시 필요 gaussian 개수 관계 캘리브레이션(선결 조건, 관계
  곡선 없이 축을 흔들면 또 다른 임의 상수 스윕일 뿐) ②그 관계로 per-frame
  적응 예산 컨트롤러 구현, exp54 최종 레시피(61.34s/0.94배) 대비 재검증 ③carve
  loss 이식 — **CLAUDE.md North Star 2단계("floater 억제를 고품질 지도 위에
  이식")와 자연 합류**. `carve_loss.py`는 "카메라 전체+SLAM anchor 전체로
  한 번에" evidence field를 빌드하는 배치 구조라 VIGS의 온라인 루프(미래
  keyframe을 모름)엔 그대로 못 씀 — 이식이 아니라 사실상 재설계 필요, 첫 작업은
  코드 이식이 아니라 온라인 근사 설계 자체(슬라이딩 윈도우 field vs `disps_up`
  depth-violation 채널만 활용 등). 계획만 수립, 미착수. → [exp55](
  experiments/exp55_adaptive_density_carve_plan.md)
- **2026-07-22 (exp53+54 나머지 축 전부 실행 — `/loop` 자동화, 실시간 배수 1.12배→0.94배, 5070 Ti에서 최초로 실시간 돌파)**:
  "안 한 축들 빠짐없이 구현까지 해서 다 실험 돌려달라"는 요청에 따라 exp53
  축B~D·exp54 축4~7을 전부 실행. **exp53 축B**(`motion_filter.thresh` 2.4→3.6):
  온라인 루프 72.91→**61.67s(−15.4%, 이 세션 최대 레버)** — keyframe 발생률 자체를
  낮춰 tracking·mapping 양쪽 작업량을 동시에 줄이는 유일한 축(다른 축은 한쪽만
  줄임), 이 지점에서 **최초로 실시간(0.947배) 돌파**. **축C**(`frontend_window`/
  `radius` 25/2→15/1): 60.65s(−1.7% 추가). **exp54 축4**(신규 구현 —
  `vigs.py::call_gs()`에 `render_downsample` 추가, 매핑 렌더 해상도를 절반으로):
  58.09s(−4.2%)지만 PSNR −0.8dB라 이미 실시간을 넘긴 지금은 미채택(코드는 보존,
  eval 해상도 불일치로 크래시하던 `eval_utils.py` 버그도 같이 수정). **축5**
  (`max_viewpoints` 20→10): 거의 무변화(−0.7%)에 PSNR −1.7dB로 최악의 ROI, 기각.
  **축6+2 결합**(densify 공격성 3배+init 밀도 2배 희석): "성긴 init을 densify가
  보충 증식해 상쇄된다"던 가설을 실제로 억제(최종 gaussian 116,143로 축1의
  122,957보다도 적게 성공)했는데도 **시간은 그대로** — 이 지점부턴 gaussian
  개수/밀도 축 전체가 소진됐음을 확정. **exp54 축7**(신규 구현 — PPM
  content-adaptive 샘플링을 `gaussian_model.py::create_pcd_from_image_and_depth()`에
  이식, `Dataset.ppm_sampling` 플래그): 동일 예산에서 속도 변화 없이 PSNR
  +0.16dB 순개선(exp44 "PPM=품질 왕"이 VIGS에서도 재현) — 공짜 이득이라 채택.
  **exp53 축D**(correlation 해상도)는 조사 결과 `num_levels`/`radius`가 사전학습된
  ConvGRU 가중치의 입력 채널 수와 shape로 고정 결합돼 있어 **재학습 없이는 구현
  불가로 판정**(실행하지 않고 결론만 기록). **최종 레시피**(축A+B+C+exp54축1+축7)
  = **61.34s, 실시간 배수 0.94배** — baseline(1.52배)에서 실시간의 62%를 실제로
  깎아 5070 Ti 단일 GPU에서 **처음으로 실시간(<1.0배) 달성**. tracking(52.31s)·
  mapping(49.79s) 둘 다 개별 예산 이하, evo APE(Sim3)는 2.41cm로 ORB(13cm) 대비
  5.4배 여유 유지. 남은 미탐색 축은 E(커널 튜닝, 고위험·저기대효과)뿐이나 이미
  목표 달성으로 낮은 우선순위. 코드는 VIGS-SLAM(업스트림 저장소)에 uncommitted로
  유지(3dgs-custom과 동일한 dirty-worktree 방침). → [exp53](
  experiments/exp53_frontend_realtime_plan.md) · [exp54](
  experiments/exp54_gsmapping_speed_ablation_plan.md)
- **2026-07-22 (exp53+54 실제 실행 — `/loop` 자동화, 실시간 배수 1.52배→1.12배)**:
  "exp53·54를 실제로 실행해달라"는 요청에 따라 `/loop`로 여러 턴에 걸쳐 축을 순서대로
  스캔. **exp53 축A**(`track_frontend.py`의 `iters1`/`iters2`, 4/2→1/0): 온라인 루프
  98.94→**78.41s(−20.7%, 이 세션 단일 축 최대 레버)**, evo APE(Sim3)는 2/1·1/1·1/0
  세 단계 전부 **1.59cm로 완전 고정**(ORB 13cm보다 8배 우위 유지, pass 기준 여유 큼) —
  재선형화 반복을 사실상 1회로 줄여도 dense correlation 정보량이 충분해 수렴엔 지장
  없다는 뜻으로 해석, **채택**. **exp54 축1**(`pcd_downsample`, 64→128): −3.3%, 부작용
  없음, **채택**. **exp54 축2**(`pcd_downsample_init`, 32→64)와 **축3**(`map() iters`,
  10→5)은 **기각** — 축2는 densify가 성긴 init을 보충 증식해 최종 gaussian 수가 오히려
  늘고 시간도 +1.2%(축2·축6이 상쇄 관계임을 발견), 축3은 −1.5% 시간에 −0.46dB PSNR로
  ROI가 나쁘고 **이 시점 tracking이 이미 91%를 차지함을 규명**(exp53 우선순위를
  끌어올린 근거). **축A(1/0)+축1(ds128) 조합 = 72.91s(1.12배)**, 이 세션 최고 기록 —
  tracking 총합(61.27s)·mapping 총합(53.23s)이 둘 다 개별적으로 65.1초 예산 아래로
  내려온 첫 지점. `pcd_downsample=256`까지 더 미는 시도는 무효(72.68s 변화 없음,
  tracking-bound 재진입)+PSNR만 −1.3dB 추가 손실이라 기각, 128 확정. 남은 갭(72.91s
  vs 이론적 완벽 병렬 61.27s)은 오버랩 효율 저하(88.3%→78.1%)가 원인으로 추정 —
  순수 연산량 축소보다 스레드/큐 동기화 튜닝이 다음 레버일 가능성. 코드
  (`track_frontend.py`·`config/aria1253.yaml`)는 VIGS-SLAM(업스트림 저장소)에
  uncommitted로 유지(3dgs-custom과 동일한 dirty-worktree 방침). → [exp53](
  experiments/exp53_frontend_realtime_plan.md) · [exp54](
  experiments/exp54_gsmapping_speed_ablation_plan.md)
- **2026-07-21 (exp54 신설 — GS Mapping 연산 시간 ablation, 7축)**:
  exp52의 "rasterize+backward+loss_compute=81.4%" 발견을 구체화하는 신규 트랙.
  사용자와 논의해 7축 확정: ①keyframe gaussian 밀도(`pcd_downsample`) ②init gaussian
  밀도(`pcd_downsample_init`) — **사용자가 "voxel당 밀도"로 제안했다가, 코드 확인 결과
  이 코드베이스엔 voxel 다운샘플이 없고 `random_down_sample`(uniform random)만 있어서
  ①과 같은 다이얼임을 확인·정정, 대신 init 전용 파라미터가 시퀀스 전체에 compounding
  되는 진짜 별도 축임을 발견해 ②로 대체** ③`iters`(map() 반복횟수) ④렌더 해상도
  ⑤`max_viewpoints` ⑥densify 공격성 ⑦**PPM 기반(Sobel content-adaptive) 샘플링** —
  사용자가 지목한 "PPM"은 이 프로젝트 exp44/48에서 이미 검증된 content-adaptive
  확률맵 샘플링(`build_depthmono_ppm_chunks.py`의 `ppm_sample()`, Sobel gradient
  가중 확률로 edge/디테일 영역 우선 샘플링) — VIGS의 uniform random downsample을
  이걸로 교체하면 같은 gaussian 개수로 더 높은 PSNR(exp44 "PPM=품질 왕" 재확인)
  또는 동일 PSNR을 더 적은 개수로 달성해 rasterize/backward를 무료로 줄일 가능성.
  같은 1253 씬에 대해 이미 PPM 결과물이 존재해(`05_incremental_dense/chunk_*/
  sparse/0/ppm_points3D.txt`) 이식 난이도 낮음. 계측은 exp52 인프라 재사용, 절대
  pass 기준 없이 "시간 대 PSNR" 트레이드오프 곡선 탐색이 목적. 미착수.
  → [exp54](experiments/exp54_gsmapping_speed_ablation_plan.md)
- **2026-07-20 (exp52 GS Mapping 루프 최대 세분화 — 12단계, `process_track_data` 전체로 계측 범위 확장 + PPT 정정판 재생성)**:
  기존 `map()` 내부 5단계(rasterize/loss_compute/backward/optimizer_step/densify_prune)
  만으론 `_process_track_data_impl()`(pose/scale 업데이트·camera 생성·`add_next_kf` 등
  map() **바깥** 부가작업)가 완전히 미계측이었음 — `gs_backend.py`에 `_Sect` 6개 추가해
  전체 계측. 1253 재실행 결과(GS Mapping 스레드 총 93.0초, 12단계): rasterize 36.2%+
  backward 22.7%+loss_compute 22.5%=81.4%로 여전히 압도적, `process_track_data` 부가작업
  (camera_init+add_next_kf+render_for_mask+pose_scale_update+w2c_compute)은 4.2%뿐
  (가설과 달리 무시할 수준). **신규 발견**: `map_dispatch`(89.15초, `self.map()` 호출
  전체를 감싼 태그) − 기존 5단계 합(77.15초) = **12.0초(12.9%)의 새 미계측 포켓** —
  `map()` 코드 재검토 결과 매 iteration마다 전체 gaussian에 대해 계산하는
  `isotropic_loss`(scaling.mean 등, gaussian 개수 늘수록 커짐)와
  viewpoint 샘플링(`torch.randperm` 기반)이 유력 후보(다음 계측 대상, 아직 개별
  계측 안 함). 이번 발견으로 GS Mapping 스레드의 실제 총 부하는 기존 "raw 76.22초"
  (map() 내부 5단계만)보다 **93.0초에 더 가까움**을 확인.
  **PPT 정정판**(`context/ppt/ppt0720/`) 재생성: 위 timing-bug 정정 수치(150.56s/
  98.94s/88.3%/1.52배 등) 전부 반영 + 신규 슬라이드 2개(타이밍 버그 정정 요약,
  GS Mapping 12단계 세분화) 추가, 총 10슬라이드로 재구성. → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-20 (exp52 ⚠ 중대 정정 — "온라인 루프 총합"에 리더 프로세스 인위적 20초 슬립이 섞여있던 버그 발견·수정, 실시간 격차 대폭 축소)**:
  "27.0초 오버헤드 중 미계측 21.1초가 정확히 뭔지" 실험으로 확인하라는 요청에 따라
  `demo.py` 메인루프에 `pbar_update`/`pbar_set_description`/`save_trajectory_periodic`
  계측 추가 후 1253 전체 재실행 — 셋 다 합쳐 **0.14초**뿐이라 "Python 루프 오버헤드"
  가설 기각. 계속 남은 ~20.85초 갭을 추적한 끝에 **진짜 원인 확정**: 리더 서브프로세스
  (`mono_stream`)가 마지막 프레임 큐잉 후 `time.sleep(20)`을 하고 종료하는데,
  `reader.join()`이 `TRACK_LOOP_DONE_EPOCH` 마커 출력보다 **먼저** 실행되도록 코드가
  짜여 있어 이 인위적 20초 대기가 모든 "온라인 루프 총합" 측정에 그대로 섞여
  있었음(트래킹/매핑 연산과 무관한 프로세스 종료 대기). **`motion_filter`/`frontend`/
  `PGBA`/`gs_mapping` 등 개별 구성요소 수치·fps스윕(ORB vs VIGS)·evo 궤적비교는 이
  버그와 무관**(전부 `vigs_track_total`/컴포넌트 태그를 직접 합산, 문제의 마커 안 씀)
  — 오직 "총합"과 거기서 파생된 배수만 영향받음. `demo.py` 수정(타이밍 마커를
  `reader.join()`보다 앞으로 이동) 후 1253 전체로 재검증: **순차 실행 150.56초
  (기존 보고 180.10초 대비 −29.5초, 실시간 대비 2.77배→2.31배), `_gs_parallel: true`
  98.94초(기존 133.04초 대비 −34.1초, 2.04배→**1.52배**)**. 수정 후 `demo_loop` 태그
  합이 실측 총합과 0.2초 이내로 거의 완전히 일치 — 미계측 잔여 21.1초가 사실상
  해소됨. 오버랩 효율도 66.0%→88.3%로 상향, 이론적 최선(완벽 병렬)도 90.5초→85.77초로
  하향(여전히 예산 65.1초 초과지만 격차 축소). **결론 방향은 안 바뀜**(①gs_mapping
  연산량 감소 최우선 ②frontend는 경합 대응이 핵심 ③미계측 오버헤드는 이제 해결됨)
  — 다만 exp53이 메꿔야 할 남은 격차 자체가 훨씬 작아짐(1.52배 → 1.0배). 사용자
  요청으로 이 강도 높은 재검증·정정 자체가 "미계측 항목을 실험으로 꼼꼼히 검증하라"는
  피드백에서 나온 것 — 앞으로도 "미계측/추정" 표시된 수치는 방치하지 말고 계측
  추가해 실제로 확인할 것. → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-20 (exp53 신설 — Frontend Tracking 실시간화 트랙, exp52에서 분리)**:
  exp52가 gs_mapping(≈50%)뿐 아니라 **Frontend Tracking 자체도 이미 실시간 예산을
  초과**한다는 걸 확정한 데 이어(위 항목), 사용자와 논의해 이 부분을 전담하는
  신규 트랙으로 분리. **exp52는 종료 아님** — mapping 쪽 실시간성(gs_parallel,
  추후 RTX 5090 재검증 등)은 exp52에서 계속. exp53은 dense correspondence
  품질을 먼저 계측(①confidence weight ②iteration별 delta 수렴 — 축A 사전진단용
  ③BA 재투영 오차)한 뒤, 축A(`iters1=4`/`iters2=2` 반복 축소, 최우선)·축B
  (`motion_filter.thresh` 상향, keyframe 밀도 자체 억제)·축C(`frontend_window`
  /`radius`/`nms` 축소)·축D(correlation 해상도 축소, 낮은 우선순위)·축E(커널
  튜닝, 보류)를 순서대로 스캔. Pass 기준: frontend 총합≤실제 녹화시간(65.1초),
  evo APE(Sim3)는 exp50(ORB, 13cm)보다 항상 우위 유지(안 그러면 dense
  correspondence 채택 의의 자체가 사라짐). 미착수. → [exp53](experiments/exp53_frontend_realtime_plan.md)
- **2026-07-20 (exp52 원 논문 검증 + frontend 내부 구조 상세화 + ⚠정정: VIGS fps 스윕 "프레임당 비용 증가" 해석 오류)**:
  DROID-SLAM(NeurIPS21)·VIGS-SLAM(ECCV26) 원 논문을 `context/reference/papers/`에
  다운받아 직접 읽고 검증. **DROID-SLAM 원문**: "2대의 3090 GPU로만 실시간"(frontend/
  backend GPU 분리), EuRoC/TUM은 다운샘플+프레임스킵 조건부, **TartanAir(빠른 모션)
  에서는 원 저자도 8fps로 실시간 실패** — 우리가 겪은 "DROID 계열은 실시간이 빡빡함"이
  구현 문제가 아니라 아키텍처 계열의 원래 특성임을 원문으로 확인. **VIGS-SLAM 부록
  Table 9**(RTX 5090+i7-14700K 공식 벤치마크): tracking만 39.83fps(RPNG 30fps 목표
  대비 여유) vs tracking+mapping 12.02fps(목표의 40%) — **"매핑이 실시간 최대
  병목"이라는 우리 결론을 저자 자신의 최상급 GPU 수치가 독립 재확인**. 부록 6절
  실시간 데모도 iPhone 17 Pro→RTX 5090 조합임을 확인.
  **Frontend Tracking 내부 구조 상세화**(`factor_graph.py::get_network_update()`
  코드 대조): ConvGRU는 (hidden state + context feature + correlation feature +
  motion feature) → (새 hidden state + dense flow revision + confidence + damping
  + 8×8 업샘플마스크)를 냄 — pose/depth는 GRU가 직접 안 내고 별도 `bundle_adjust`
  (DBA layer)가 냄. `iters1=4`+`iters2=2`(하드코딩) 반복은 고전 Gauss-Newton의
  재선형화와 동일 원리(재투영→룩업→GRU→BA→재투영 반복). "윈도우 채우고 다음
  윈도우로" 아니라 **매 keyframe마다 슬라이딩 윈도우**(`frontend_window=25`,
  `frontend_radius=2`/`nms=1`)로 오래된 edge는 버려짐. "dense correspondence"는
  edge 개수(3~52개, 오히려 sparse)가 아니라 **edge 하나 안의 픽셀 밀도**를 뜻함.
  **⚠정정**: fps 스윕에서 "VIGS는 fps 낮출수록 프레임당 비용이 커진다(73→222ms)"고
  썼던 서술이 오해 소지 있었음 — timing.csv를 call-count/per-call로 재분해하니
  **per-call 비용은 거의 안 변함**(bundle_adjust만 12.7→15.1ms 소폭↑, 나머지는 오히려
  감소)이고 **frontend 총합도 fps 낮출수록 감소**(48.3→32.9초). "프레임당 평균"은
  분모(입력 프레임 수, 4배 감소)로 나눈 착시였고, 진짜 원인은 **keyframe 개수가
  입력 fps와 거의 무관**(VIGS −6.6%, ORB −20.8%, 둘 다 optical-flow/모션 임계값
  기반이라 실제 카메라 이동량으로 결정됨). 결론 방향(VIGS는 fps 낮춰도 실시간
  안 됨, 5fps도 1.11배)은 안 바뀌지만 **원인이 "계산이 힘들어짐"이 아니라 "keyframe
  발생량 자체가 안 줄어듦"** — 다음 레버는 `iters1`/`iters2` 축소나
  `motion_filter.thresh` 상향(keyframe 밀도 억제) 쪽. → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-19 (exp52 궤적 정확도 evo 평가 + dense correspondence 아키텍처 분석 — VIGS depth가 tracking BA와 공동 최적화됨을 소스로 확인)**:
  위 fps 스윕의 6개 궤적을 MPS `closed_loop_trajectory.csv`(GT) 기준 `evo_ape`로
  평가. **SE3(raw) RMSE는 ORB 0.16~0.25m vs VIGS 0.11~0.21m로 비슷하지만, 스케일
  보정(Sim3) 후엔 ORB 13cm대 vs VIGS 1.3cm로 10배 차이** — VIGS의 dense
  correlation 트래킹이 궤적 "형태" 정확도에서 압도적. 스케일 보정계수는 둘 다
  작음(ORB 0.953~0.980, VIGS 1.025~1.048) — ORB는 캘리브레이션된 스테레오
  기준선(하드웨어 상수)에서 스케일을 얻어 안정적인 반면, VIGS는 IMU 융합 1회성
  초기화(`imu_late_init_from`)에서 나온 전역 스칼라 하나가 살짝 편향되어 전체
  궤적에 균일하게 곱해짐 — "형태 정확도"와 "절대 스케일"은 독립적인 두 축임을 확인.
  **소스 추적으로 mapping 기하와의 연결고리 규명**: `factor_graph.py`의 dense
  correlation+학습된 GRU가 코너 특징점(ORB는 keyframe당 겨우 150~166개 매칭,
  ~3010개 추출 중 95% 손실)이 아니라 사실상 전체 픽셀을 포즈 추정에 구속조건으로
  씀. 결정적으로 `vigs.py:169`의 `call_gs()`가 Gaussian mapper에 넘기는 depth는
  Omnidata 원본이 아니라 **`self.video.disps_up`** — Omnidata는 `mono_depth_alpha:
  0.01`의 약한 prior로만 쓰이고 실제 depth는 JDSA(Joint Dense Scale-aware BA)로
  **포즈와 같은 최적화에서 공동 정제됨**(normals만 Omnidata raw). 우리
  exp50/51 파이프라인은 반대로 depth-pro를 트래킹과 **완전히 무관한 독립
  프로세스**로 돌림 — exp51 depth supervision 축(+2.42dB)이 VIGS 급 형태
  정확도까지 못 간 구조적 원인이자, **이 프로젝트가 처음부터 쫓던 floater(같은
  3D 지점이 view마다 다른 위치로 삼각측량되는 문제)의 뿌리와 정확히 같은
  메커니즘**임을 확인. 다음 과제로 남김(depth를 keyframe별 독립 정적 prior가
  아니라 트래킹 포즈 최적화와 공동 정제하는 구조 — 우리 ORB 기반 트래킹에
  dense-correlation을 도입하는 건 별도 아키텍처 결정 필요, exp51 범위 밖).
  → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-19 (exp52 트래킹 전용 fps 스윕 — exp50(ORB) vs VIGS, 동일 60초 창에서 20/10/5fps 비교)**:
  `_gs_parallel`로도 2.04배 미달이었던 데서 "tracking 자체가 무거운 거 아니냐"는
  질문 제기 → VIGS의 dense 단안 트래킹과 우리가 실제 채택할 exp50(ORB-SLAM3 기반
  흑백 stereo-inertial)을 동일 조건에서 직접 비교. 1253 흑백 SLAM 카메라 첫 60초를
  stride 1/2/4로 subsample(20/10/5fps), ORB는 `times.txt` subsample만으로 코드
  무수정 재사용, VIGS는 기존 `--length`/`--stride` 옵션 재사용. **첫 시도 때 두
  스윕을 동시 실행했다가 GPU 경합으로 VIGS가 OOM 크래시(`_gs_parallel`과 동일 패턴)
  → 순차 실행으로 재격리.** 벤치마크 중 DiskChunGS 매퍼 스레드에서 별개의 새 CUDA
  버그(`invalid configuration argument`, 71% 지점) 발견 → `GaussianMapper::run()`의
  매핑 루프를 `try/catch`로 감싸 매퍼 예외가 트래킹까지 죽이지 못하게 방어적 수정.
  **결과(60초 창 기준, 1.00배=실시간)**: ORB 20/10/5fps = 40.55초(0.68배)/25.52초
  (0.43배)/17.06초(0.28배) — VIGS 20/10/5fps = 87.68초(1.46배)/77.60초(1.29배)/
  66.80초(1.11배). **ORB는 프레임당 비용이 fps 무관 고정(~25ms)이라 fps를 낮추면
  여유가 선형으로 커지는 반면, VIGS는 프레임당 비용이 fps를 낮출수록 커져(73→222ms,
  dense correlation 탐색범위가 프레임 간격에 비례) 5fps까지 내려도 여전히
  미달(1.11배).** 매핑뿐 아니라 트래킹 아키텍처도 exp50 경로가 실시간에 유리함을
  확정 — exp52의 "VIGS 유효 레버만 이식" 결론 강화. → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-19 (exp52 구조적 전환 — `_gs_parallel: true`로 온라인 루프 180.1→133.0초(−26.1%), 업스트림 레이스 컨디션 발견·수정)**:
  "gs_mapping을 0으로 줄여도 실시간 되나?"를 직접 계산(180.10−90.5=89.6초>65.1초 녹화시간)
  → **순차 구조로는 컴포넌트 최적화만으로 실시간 불가**임을 확정, 구조적 전환으로 방향
  전환. tracking→CPU 이관안은 기각(TensorRT GPU 전용, GPU 1장뿐). 코드베이스 내장
  `_gs_parallel: true`(비동기 tracking/mapping 오버랩) 첫 실행에서 `IndexError`
  크래시 → **업스트림 진짜 버그 발견**: IMU 재초기화 시 메인 스레드의
  `remove_all_gaussians()`가 락 없이 `self.gaussians`를 교체해 `_gs_worker` 백그라운드
  스레드의 락 보호 `map()`과 경합(`config/iphone.yaml`도 `parallel: true`라 죽은
  코드 아님). `with self._gaussian_lock:`로 수정. 수정 후 재실행이 또 다른 문제로
  막힘: `_gs_worker`가 daemon 스레드라 죽어도 메인 프로세스가 안 죽고 계속 돌아
  **좀비 프로세스가 GPU 메모리 10.83GiB를 계속 점유** → 재시도가 그 메모리와 다투다
  OOM, 게다가 CUDA 컨텍스트 손상으로 정상 종료도 못하고 행(hang). 두 정체 프로세스
  `kill -9`로 정리 후 깨끗한 GPU에서 재실행 → 완주. **결과: 온라인 루프
  180.10→133.04초(−26.1%), PSNR 22.90/23.09→22.63/22.89dB(오차범위 내 동일),
  실시간 대비 2.77배→2.04배.** 매핑 실제 연산(86.24초)의 66%(56.92초)가 트래킹과의
  GPU 유휴시간 오버랩으로 흡수됨, 34%(29.20초)만 GPU 경합으로 critical path에 누출.
  사용자의 구조적 직관이 실측 확인됨 — 다만 2.04배로 아직 실시간 미달. → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-19 (exp52 ⚠ 정정 — 1253 실제 녹화시간은 65초·~20fps, "실시간 대비" 배수 전부 재계산)**:
  사용자 질문("1253 전체 데이터 녹화 시간?")으로 발견 — RGB 프레임 타임스탬프(첫~끝)로
  직접 계산한 실제 녹화 시간은 **1253 65.1초(1303프레임, ~20fps)**, **1253_rot 74.85초
  (1498프레임, ~20fps)**. 이전 실시간 배수 계산이 전부 "~10fps" 오가정(2배 오차) 위에서
  나온 것이었음 — 정정: 가속 전 온라인 루프(1253) 209.36초 → 실시간의 **3.22배**(1.6배
  아님), 1253_rot 344.7초 → **4.60배**(2.3배 아님), imu_cpp+TensorRT 전부 적용 후(180.10초)
  → **2.77배**(여전히 3배 가까이 느림, 5.1%/14.0% 등 상대적 개선폭 자체는 정확했으므로
  변경 없음 — 절대적인 "실시간과의 거리"만 재계산 필요했음). → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-17 밤 (exp52 VIGS-SLAM 클론·빌드·평가 — 소스검증 4건 + 1253 베이스라인 keyframe 30.90dB)**:
  `github.com/cvg/VIGS-SLAM` 클론(`repos/main/VIGS-SLAM` 심링크) 후 `vigs-slam-5090` conda env를
  실제로 빌드(공식 `environment_5090.yaml` 그대로는 6가지 이슈로 전부 실패 — lietorch==0.2
  PyPI 부재/torch-scatter 빌드순서/nvidia-cuda-runtime 버전충돌/pycuda TensorRT전용 제외/
  diff-gaussian-rasterization의 `<cstdint>` 누락/conda-forge CUDA 헤더 경로 — 전부 해결).
  데모 실행이 keyframe 1에서 재현성 있게 SIGSEGV → `PYTHONFAULTHANDLER=1`로 근본원인 특정
  (`vigs/imu.py:170` sophuspy `SO3.exp` — PyPI 프리빌트 wheel이 numpy 2.x와 ABI 불일치,
  `--force-reinstall --no-binary=:all:` 소스 재빌드로 해결). **소스 직접 분석으로 exp51 시절
  가정 4건 검증/정정**: ① isotropic scale loss+scale clamp(우리 exp51엔 없음, 신규 이식 후보)
  ② "비가시만 선별 opacity reset"은 코드는 있으나 **공개 config 5개 전부에서 비활성** — 실제
  교훈은 "선택 리셋"이 아니라 "그냥 주기적 전체 리셋을 안 한다" ③ init 렌더-alpha 중복방지용
  `transmittance` 계산은 **100% dead code** 확인 — 우리 exp51 축B가 진짜 기여였음을 재확증
  ④ **normal supervision(Omnidata) 신규 발견** — depth 외 축, 바늘형 floater에 유효할 후보.
  **베이스라인(알고리즘 무수정) 실행**: RPNG 데모 held-out 25.75dB. **1253 데이터**(projectaria_tools로
  VRS에서 RGB-IMU 외부파라미터 직접 추출, 기존 Aria.yaml IMU-cam1 값과 소수점 6자리까지
  일치해 교차검증) held-out **26.85dB**, **keyframe 30.90dB**, 6~8분/129kf/201k가우시안.
  ⚠ 단 이 수치는 트래킹 후 붙는 26,000-iteration 오프라인 폴리싱을 포함 — **실시간 수치
  아님**, `--pure_online` 재검증 필요(다음 스텝). 1253_rot도 같은 절차로 실행 중.
  → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-18 밤 (exp52 imu_cpp+DroidNet TensorRT 전부 적용 — 온라인 루프 −14.0%, 그래도 매핑 비중은 오히려 50.2%로 증가)**:
  이전에 스코프 밖으로 미뤘던 항목 마저 처리 — `imu_cpp`(README 선택 C++ IMU
  프리적분 모듈) 빌드(시스템 패키지 이미 있어 즉시 성공), DroidNet fnet·update_module
  TensorRT화(README 예시 shape는 우리 데이터와 안 맞아 실측 shape로 재 export —
  fnet 고정 (1,1,3,464,464), update_module H=W=58 고정+num(edge수) 동적 3~52 —
  `trtexec` 바이너리 없어 Python TensorRT API로 `IOptimizationProfile` 직접 구성).
  **결과: imu_integrate 12.42→0.19초(−98.5%, 사실상 공짜), feature_encoder −78%,
  prior_extractor −77%, 그러나 update_op_forward는 12.54→13.62초(+8.6%, 효과 없음
  — 네트워크가 이미 가벼움+동적 shape 재바인딩 오버헤드+TRT/PyTorch 경계 동기화
  비용 추정, "뭐든 TRT면 빨라진다"가 아님을 확인). **온라인 루프 총합 209.4→180.1초
  (−14.0%), PSNR 완전 무변화(22.73→22.90dB).** 그런데 gs_mapping(rasterize+backward)
  비중은 **30.2%→50.2%로 오히려 커짐** — 다른 항목들이 줄면서 분모가 작아진 결과.
  **최종 결론: 매핑을 최적화하지 않는 한 나머지를 아무리 가속해도 온라인 루프의
  절반은 여전히 매핑.** → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-18 밤 (exp52 TensorRT 가속 실측 — Omnidata 78%↓이나 온라인 루프는 5.1%↓에 그침, 매핑이 여전히 승부처)**:
  병목 분석에서 지목된 "TensorRT 미사용"을 실제로 해결 — `tensorrt-cu12`/`pycuda`/`onnx`
  계열 재설치(`trtexec` CLI가 pip wheel엔 없어 **Python TensorRT API로 직접 엔진
  빌드**, `Builder`+`OnnxParser`+FP16 config), Omnidata depth/normal만 ONNX 익스포트→
  `onnxsim`→FP16 엔진(85초×2, 1회성). **결과: prior_extractor(Omnidata) 46.45ms→10.15ms
  (−78%), motion_filter 총합 27.0→15.8초(−41.5%), 그러나 온라인 루프 전체는
  209.4→198.7초(−5.1%)에 그침** — Omnidata 비중이 애초 7%뿐이라 이론대로 작은 순
  이득(motion_filter 감소 −11.2초가 거의 그대로 반영, model_loading +0.6초가 유일한
  상쇄). PSNR 완전 동일(22.73→22.54dB, 오차범위). DroidNet update_module(12.5초,
  6.0%)의 TensorRT화가 다음 후보지만 동적 shape라 훨씬 복잡 — 스코프 밖으로 보류.
  **결론 불변: 매핑(rasterize+backward, 30%)이 여전히 최대 병목, TensorRT는 보조
  수단일 뿐 승부수가 아님.** → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-18 밤 (exp52 온라인 루프 함수 단위 병목 분해 — gs_mapping rasterize+backward가 30%로 최대, 미계측 오버헤드도 30%)**:
  이전 병목 분석("트래킹 vs 매핑" 거친 단위)을 커널/함수 단위로 더 쪼갬 —
  `factor_graph.py::update()`(correlation lookup/update-op 신경망/CUDA BA solve/upsample)와
  `motion_filter.py::track()`(feature_encoder/Omnidata prior_extractor/context_encoder/
  flow_check)에 동일한 opt-in 타이머 추가. 1253 전체(1303프레임) 온라인 루프 208.2초 완전
  분해 결과: **gs_mapping의 rasterize+backward 62.8초(30.2%, 단일 최대 원인)** > frontend의
  **bundle_adjust(CUDA BA solve) 28.6초(13.7%)** > gs_mapping의 loss_compute 15.8초(7.6%)
  ≈ motion_filter의 **prior_extractor(Omnidata depth+normal) 14.5초(7.0%, TensorRT 미사용이
  직접 원인 — 우리 빌드는 pycuda/TensorRT를 제외했음)** > frontend의 update_op_forward(DROID
  GRU) 12.5초(6.0%). **미계측 오버헤드가 ~62초(30%)** 로 그 자체로 큰 비중(모델 로딩·IPC·
  Python 제어흐름·GPU 동기화 대기로 추정, 더 파려면 torch.profiler/py-spy 필요). **결론:
  매핑(rasterize+backward)이 트래킹 핵심연산(BA solve)보다 확실히 무겁다는 기존 결론이
  함수 단위로도 재확인됨.** → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-18 (exp52 ⚠ 정정 — `--pure_online` 실측: "keyframe 30dB"는 6~8dB가 오프라인 폴리싱 몫, 순수 온라인은 우리보다 낮음)**:
  병목 분석에서 나온 가설("오프라인 폴리싱이 PSNR을 몇 dB나 사주는가")을 실제로
  `--pure_online` 플래그로 전체 데이터셋 재실행해 검증(`demo.py`에 평가 전용 opt-in 훅
  추가 — `--pure_online`이 원래 스킵하는 `traj_filler`+`eval_rendering`을 온라인 루프
  종료 **직후**, 최종 BA·색정제 없이 호출해 순수 온라인 PSNR만 측정, 온라인 시간 측정에는
  영향 없음). **결과: 1253 순수 온라인 held-out 22.73dB/keyframe 22.95dB(온라인 루프
  207.6초), 1253_rot held-out 23.53dB/keyframe 23.61dB(344.7초)** — 앞서 보고한 폴리싱
  포함 수치(26.85/30.90, 25.08/30.31) 대비 **폴리싱이 held-out +1.55~4.12dB, keyframe
  +6.70~7.95dB를 만들어낸 것**이었음이 실측 확정. **핵심 정정: 순수 온라인 품질(22.7~23.5dB)은
  우리 exp51 축A+B(held-out 25.29dB)보다 오히려 낮다** — "VIGS가 우리보다 우월하다"는
  이전 인상은 폴리싱 포함 수치와 우리 무폴리싱 수치를 비교한 불공정 비교였음. 온라인
  루프 시간도 재확인(1253 실시간의 1.6배, rot 2.3배 — rot가 온라인 단계에서도 더 느림).
  **다음 방향 수정: VIGS 아키텍처를 그대로 가져오기보다, normal supervision(exp51에 없는
  축)처럼 폴리싱 없이도 우리 축A+B를 능가할 구체적 레버를 찾는 쪽이 더 정확한 질문.** →
  [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-18 (exp52 병목 분석 확정 — 오프라인 색정제가 전체시간의 80%, 온라인 루프는 실시간에 근접)**:
  `vigs.py`/`gs_backend.py`에 opt-in 타이밍 계측(`VIGS_TIMING_LOG`, 미설정 시 no-op) 삽입 후
  1253 250프레임 서브셋으로 트래킹만(A, 57.3초) vs 트래킹+매핑(B, 280.8초) 절제 실험 +
  phase별 실측. **B의 79.7%(195.9초)가 `offline_color_refinement`(26,000 iteration, config에
  고정돼 데이터 크기와 무관) 하나** — 앞서 본 keyframe 30dB의 상당 부분이 이 고정비용
  폴리싱에서 나옴을 시사. **온라인 구간(motion_filter+frontend+gs_mapping)만 떼면 41.9초/
  250프레임 = Aria 캡처 속도(25초분) 대비 약 1.7배** — 온라인 루프 자체는 생각보다 실시간에
  가까움. 온라인 구간 안에서는 gs_mapping(23.3초, render+backward가 97.9%)이 트래킹
  (18.7초)보다 비쌈. **결론: 실시간화 최우선 과제는 온라인 최적화가 아니라 오프라인
  폴리싱 압축/스킵** — `3dgs_before_final.ply`(폴리싱 전) 자체를 평가해 PSNR 기여분을
  정량화하는 게 다음 스텝. → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-17 밤 (exp52 후속 — 1253_rot도 keyframe 30dB 유지)**: 같은 절차(Tcb 재추출,
  소수점까지 1253과 일치)로 회전 궤적 데이터(1498프레임) 실행 → held-out 25.08dB / **keyframe
  30.31dB**, 266,423가우시안, **총 소요 12.5분**(파일 타임스탬프로 정확히 측정 — 처음에
  `ps aux` 누적 CPU 시간을 경과 시간으로 잘못 읽어 "24분"이라 썼던 것을 사용자 지적으로
  정정). 1253 대비 소폭 하락(-1.77dB/-0.59dB)하지만 회전 궤적에서도 크게 안 무너짐 —
  우리 carve loss가 rot에서 겪은 run-to-run 분산 이슈와는 다른 종류의 견고성. →
  [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-17 밤 (results/experiments/ 정리 — Plateau 시대 36개 run archive)**: 317개로
  비대해진 `results/experiments/`에서 **완전히 닫힌 축(exp01-37, Plateau loss 시대 — carve
  loss(exp38+)가 전면 대체)** 을 `results/archive/mps_plateau_era/`·`archive/orb_plateau_era/`로
  이동(36개 run). STATUS.md·PPT 스크립트가 지금도 경로로 직접 참조하는 챔피언/기준선만
  남김(exp08, exp13, exp30/exp30r, exp32_lineage_diag, exp37) — 이동 후 전부 경로 존재
  확인·`index_runs_by_exp.py` 재생성 완료. exp38 이후(현재 방법론의 근거)는 미손대짐;
  exp44(72 run, 대부분 중간탐색)는 추가 정리 여지 있으나 보류. 상세:
  `results/archive/README_plateau_era_archive.md`.
- **2026-07-17 (exp51 진단 확정 — 잔여 갭은 depth-init 바늘형 floater, 배치 30.2dB가 진짜 상한 아니었음)**:
  사용자 지적("일반 3dgs로 33 나왔었는데")으로 발견: "배치 30.2dB"는 exp48 시절 8,550-iteration
  예산 캡을 씌운 통제실험 수치였을 뿐 진짜 배치 상한이 아니었음 — 동일 장면(301_1253) 풀 30k 배치는
  exp30 baseline(ORB init) test **31.5dB**, exp44d2 챔피언 test **32.5dB**(exp44_fast_geometry_plan.md
  기존 확정표). 축A~C는 전부 8,550~16,950 iteration 캡 안에서만 실험한 것이었음. **51-F(예산 3.3배,
  iters_per_kf=500, 28,581 iter) 재검증 → 25.59dB(+0.30만)** — 학습량 부족 가설도 강하게 기각.
  Photo-SLAM 키프레임 샘플러(`useOneRandomSlidingWindowKeyframe`) 코드 직접 확인 결과 최근 키프레임
  편향이 아니라 등록된 전원을 균등 순환하는 방식임도 확인 — 재방문 빈도 편향도 아님. **시각 진단으로
  확정**: 최악 뷰(frame_00449 근방, 화이트보드+문 장면)의 GT/render를 직접 대조 — GT는 평범한데
  **render는 화면 전체가 바늘형(needle) floater 아티팩트로 뒤덮임**(28,581 iter 학습 후에도).
  "블러/저화질"이 아니라 명백한 depth-init 실패로 인한 floater — 한번 anchored된 바늘형 가우시안은
  순수 photometric gradient로는 잘 안 사라짐(축B의 dedup도 "새 점 스킵"이지 "기존 나쁜 점 제거"가
  아니라 무력). **결론: 밀도·예산·재방문 빈도 전부 아니고 정확히 프로젝트의 기존 carve loss 방법론
  (exp38~44d2, 배치에서 -83~93% 먼지 검증됨)이 타겟하는 문제.** 다음: 축E — carve loss를 incremental
  파이프라인(LibTorch C++)에 이식. → [exp51](experiments/exp51_dense_supervision_plan.md)
- **2026-07-17 (exp51 축C 종결 — 밀도는 고정·비례 예산 둘 다 무효과 확정, 현재 최선 25.29dB 축A+B)**:
  사용자 결정(옵션 a+c 동시 진행)에 따라 ① 예산비례 밀도 재검증: D=2 replay(113 서브청크)를 예산
  안 나누고 그대로 150 iter/청크(총 16,950 iter, D1-b의 2배)로 재학습 → **25.30dB** — 앞서의 고정예산
  결과(25.11)와도, 밀도 안 늘린 축A+B(25.27~25.29)와도 전부 오차범위 내 동일. **"예산 희석" 가설도
  기각 — 밀도 자체가 이 지점에서 추가 레버가 아님을 확정.** ② per-view 진단(축A+B 25.29dB 모델의
  held-out per_view.json): 최악 뷰가 두 클러스터에 집중 — 기존 진단된 저텍스처 화이트보드 근접면
  (frame 430-700대, exp48 기록과 일치)과 신규 발견된 specular 바닥+글레어+잡동사니 구간(frame
  313-329/1057-1073, 렌더에 바늘형 floater 스펙클 육안 확인). **결론: 남은 갭(25.29→30.2)은
  windowed/times-of-use 아키텍처 문제가 아니라 장면 콘텐츠 난이도(저텍스처+specular/clutter)가
  지배적** — 밀도·예산을 아무리 늘려도 이 어려운 뷰들의 depth-pro/SLAM 신호 자체가 나빠 개선이 안 됨.
  **exp51 축C(keyframe 밀도) 여기서 종료**(D=3/4 미실행, 정지 규칙 충족), **현재 확정 최선 = 축A+B
  25.29dB.** 다음 후보: 축E(floater 억제, 진단된 두 클러스터 타깃) 또는 이 장면에서 배치 상한
  30.2dB 자체의 재현 가능성 재검토. → [exp51](experiments/exp51_dense_supervision_plan.md)
- **2026-07-17 (exp51 축C 첫 시도 — keyframe 밀도 2배 고정예산으로는 무효과, 다음 방향 결정 필요)**:
  `build_photoslam_replay_dense.py`(신규): 원본 57 keyframe 각각의 dense 구간에서 D개 균등 프레임을
  승격시켜 각각을 독립 gaussian-생성 청크(`chunk_NNN_Y`)로 만듦 — sub-frame 0(원 keyframe)만 SLAM
  extra point 받고 전 sub-frame이 자기 뷰 기준 causal PPM+depth 타깃(축A 재사용)을 받음. D=2로 113개
  서브청크 생성(57→113, 원본 chunk_000은 dense 프레임 부족으로 승격 없음). **총 iteration 예산을 D1-b와
  동일하게 고정**(iters_per_kf 150→75)해 축A(λ=0.5)+축B(dedup) 위에 학습 → **25.11dB — 축A+B(25.27~25.29)
  대비 개선 없음(오차범위 내).** N은 927k로 비슷한 규모(dedup이 정상 작동해 중복 급증은 안 일어남).
  **해석: "뷰 다양성 부족"이 병목이 아니라, 예산을 뷰 수에 비례해 나눈 것(150→75 iter/뷰)이 상쇄 효과를
  만들었을 가능성** — 순수 밀도 효과와 예산 희석 효과가 이 실험 설계로는 분리 안 됨. D=3/4을 같은
  방식(고정예산)으로 반복해도 같은 결론이 나올 공산이 커 **일단 보류**(정지규칙: 2연속 동일원인 실패
  방지). 다음 결정 필요: ① 예산을 밀도에 비례해 늘려 순수 밀도 효과 재검증 ② 축C 접고 축D(dense
  supervision-only)나 축E(floater)로 전환 ③ 축A+B(25.29dB)를 현재 최선으로 확정, 다른 병목(윈도우
  아키텍처) 재검토. → [exp51](experiments/exp51_dense_supervision_plan.md)
- **2026-07-17 (exp51 축B 완료 — init 렌더-alpha 중복방지, PSNR 무변화·N -16%, 축C 인에이블러 확정)**:
  래스터라이저에 `out_alpha`(=1-T, 픽셀별 누적 opacity) 출력 추가(backward 불필요 — init 시점
  `NoGradGuard` 안에서만 사용). `trainReplay`에서 새 keyframe 추가 직전, 그 keyframe의 pose로 **현재
  가우시안 맵을 먼저 렌더**해 alpha를 얻고, 이번 청크의 init 후보점(world xyz)을 같은 카메라로 투영해
  픽셀 alpha가 threshold(0.5) 이상인("이미 덮인") 점을 스킵 — VIGS-SLAM이 변수만 만들고 실제로는 마스킹
  안 하던(`transmittance` 계산 후 미사용) 부분을 제대로 구현. `EXP51_DEDUP_INIT`/`EXP51_DEDUP_ALPHA_THRESH`
  env var로 토글. **결과: 25.27dB(축A 25.29와 오차범위 내, PSNR 무변화) — 가우시안 수는 1,089k→917k
  (-16%) 품질 손실 없이 감소.** dedup 로그로 의도대로 동작 확인(청크 1: 12494개 중 6798개 유지 vs
  청크 56: 9361개 중 130개만 유지 — 맵이 찰수록 스킵률 급증). **결론: dedup 자체는 PSNR 레버가 아니라
  축 C(keyframe 밀도 2~4배)의 인에이블러** — dedup 없이 밀도만 올리면 중복점이 배로 늘어 낭비·부작용
  위험, dedup이 이를 막아 밀도 실험을 안전하게 해줌. 다음: 축 C(keyframe 57→114→171→228 밀도 스캔).
  → [exp51](experiments/exp51_dense_supervision_plan.md)
- **2026-07-17 (exp51 축A 완료 — depth supervision +2.42dB 확정, 그러나 26dB 미만이라 축B/C로 계속)**:
  Photo-SLAM CUDA 래스터라이저(forward.cu/backward.cu/rasterizer_impl.cu/rasterize_points.cu)에 3dgs-custom의
  `out_invdepth`/`dL_dout_invdepth` 패턴을 이식(alpha-weighted expected inverse depth, forward accumulation +
  backward `dL_dtz -= dL_dinvdepth/(t.z)^2`) — vanilla Photo-SLAM 래스터라이저엔 depth 출력 자체가 없었음(내부
  정렬용 view-space z만 존재, 픽셀 depth 이미지 미출력). `GaussianRenderer::render()` 리턴 튜플에 5번째 원소로
  추가(4개 기존 호출부 `std::get<0..3>`라 하위호환, 명시적 튜플 타입 1곳만 수정). depth 타깃은 신규
  `scripts/incremental/build_depth_targets.py`(`build_depthmono_ppm_chunks.py`의 causal `calib_depth()` 재사용)로
  keyframe RGB에 SLAM-보정 dense inverse-depth를 사전계산(56/57 성공, chunk_000만 SLAM point 부족으로 스킵) —
  **raw depth-pro를 그대로 안 쓰고 SLAM point로 Huber 보정한 값만 사용**(사용자 요구사항 반영). init(SLAM+PPM)은
  그대로 유지, depth loss는 photometric loss에 additive(사용자 요구사항 반영). λ는 `EXP51_LAMBDA_DEPTH` env var로
  재빌드 없이 스캔 가능하게 설계. **결과: baseline(D1-b 재확인, λ=0) 22.87dB(D1-b 23.11과 오차범위 내 — 래스터라이저
  patch 회귀 없음 확인) → λ=0.1: 25.11 → λ=0.5: 25.29(+2.42, 최고) → λ=1.0: 25.06(과대 λ는 photometric 희생).**
  depth supervision이 VIGS 조사에서 예측한 대로 실제 큰 레버임을 확정했으나, exp51 결정 규칙(≥28dB=depth만으로
  충분) 기준 미달(26dB 미만) → **축B(init 렌더-alpha 중복방지)+축C(keyframe 밀도 57→2/3/4배) 결합이 다음 단계로
  확정.** → [exp51](experiments/exp51_dense_supervision_plan.md)
- **2026-07-17 (프로젝트 목표 명문화 + exp51 계획 — 진짜 병목은 depth supervision)**: 사용자와 North Star 정리 → CLAUDE.md/AGENTS.md에 최종 그림(Aria 흑백 SLAM localization + RGB incremental 고품질·floater無·실시간 mapping)과 현재 단계 우선순위 명시. **핵심 재프레임: "22dB 지도에 floater(carve) 먼저 넣는 건 순서 오류 — 고품질(30dB+)이 선결"**(저품질에선 이미지가 floater를 요구, exp43 12F 확인). exp49 D1(hybrid init 튜닝)은 PPM +0.97dB(23.11), RoMA·times_of_use·기타 무효로 마무리 — init 미세튜닝은 수확체감. **VIGS-SLAM(ECCV2026, ETH CVG) 조사로 진짜 레버 규명**: VIGS도 keyframe만 supervise(우리와 동일, "dense 프레임 다 씀"은 오해)이나 품질이 좋은 건 ① **RGB+depth supervision**(depth가 gaussian 앵커링, 우리는 RGB photometric only라 빠짐 — exp43 벽의 원인도 이것) ② isotropic loss+scale clamp+visible-only opacity reset ③ init 중복방지 훅(alpha로 이미 덮인 픽셀 스킵, 공개코드엔 미완성). **exp51 신설**: depth supervision(축A, SLAM point로 보정한 depth-pro 사용, init은 유지)·init 중복방지(축B, 빈 픽셀만)·keyframe 밀도 2/3/4배(축C)·dense supervision(축D)·floater억제(축E). baseline D1-b 23.11 → 목표 배치상한 30.2. loop 첫 사이클=축A(판 가르는 실험). → [exp51](experiments/exp51_dense_supervision_plan.md)
- **2026-07-16 밤 (exp50 B1 — Fisheye624 라이브 stereo-inertial 트래킹 root-cause 수정으로 최초 성공)**: exp49 B1(Photo-SLAM)에서 Fisheye624 이식 후 라이브 트래킹이 매 keyframe마다 리셋되던 문제를, DiskChunGS(같은 ORB-SLAM3 계열)에 동일 패치를 이식해 재현한 뒤 3단계로 근본 진단. IMU_STEREO로 돌려도 증상 불변 → "IMU 부재" 가설 기각. **① 파일 무결성**: Fisheye624 원본과 byte-identical, 카메라 수학은 무죄. **② 계측**: ORB 추출 N~1500 정상이나 stereo 매칭 성공은 9~31개뿐(~98% 손실). **③ 근본 원인 2건**: (a) `ComputeStereoFishEyeMatches()`가 `mpCamera`를 무조건 `static_cast<KannalaBrandt8*>`로 캐스팅 — 실제론 `Fisheye624*`라 UB, 엉뚱한 왜곡모델로 삼각측량 → `GeometricCamera`에 `virtual TriangulateMatches` 추가해 가상 디스패치로 전환. (b) `mpCamera2` 설정 조건이 `cameraType()==KannalaBrandt`로 하드코딩돼 `Fisheye624Type`이 안 걸림 → rectified pinhole용 블록매칭 경로로 잘못 빠짐(fisheye 매칭 함수 자체가 호출도 안 됨) → 조건에 `Fisheye624Type` 추가. **수정 후 stereo 매칭 9~31→33~76개(지속), 리셋 0회 — Aria Fisheye624 IMU_STEREO 라이브 트래킹 최초 성공.** 이후 GaussianMapper의 COLMAP 카메라 export가 PINHOLE만 지원해 크래시 — 예상된 다음 관문(RGB 매핑 카메라 분리 주입 설계로 해결 예정). 부수적으로 `euroc_stereo_inertial.cpp`의 `output_directory` argv 인덱스 버그(Phase C 미실행 방증)도 발견·수정. → [exp50](experiments/exp50_diskchungs_plan.md)
- **2026-07-16 밤 (exp50 Phase A&B 완료 — DiskChunGS 빌드 완주 및 Stereo-Inertial 연동 성공)**: ETH Zurich의 최신 out-of-core 가우시안 SLAM 기법인 DiskChunGS의 전체 빌드(Phase A) 및 EuRoC Stereo-Inertial 예제 구현(Phase B)을 완벽하게 마무리함. TensorRT 제거에 따른 OpenCV StereoSGBM fallback 처리, PyTorch C++ API 버전 호환성(c10::cuda::CUDACachingAllocator 대신 cudaMemGetInfo 적용, torch::linalg::inv 대신 torch::inverse), glm::perspective 형변환 오류 패치 등을 완료하여 `✓ Build completed successfully!` 획득. `bin/euroc_stereo_inertial` 바이너리 생성 완료로 Phase C 데이터셋 평가 실행 준비 완비. → [exp50](experiments/exp50_diskchungs_plan.md)
- **2026-07-16 밤 (exp49 Phase C — Photo-SLAM incremental replay가 exp48 18dB 천장 돌파, held-out 22dB)**: Phase A(train_colmap 생존 검증, 매핑 백엔드 우리 RGB 동작 확인)에 이어 Phase C 구현·완주. 신규 `build_photoslam_replay.py`가 OpenMAVIS 57 keyframe을 per-keyframe 바이너리 COLMAP 청크로 생성, 신규 `GaussianMapper::trainReplay`(+`train_replay.cpp`)가 시간순 replay(keyframe 추가→increasePcd→trainForOneIteration, times-of-use 슬라이딩 윈도우). v1(iters_per_kf=150=총 8550, exp48 동일 예산): 크래시 없이 완주, N 716k. **held-out 163뷰(3dgs-custom render.py로 exp48과 동일 llffhold-8 하네스) PSNR 평균 22.14dB / 중앙값 21.67 / PSNR<15 = 5개.** exp48 자체 incremental(18.0~18.23dB, PSNR<15 35~41개) 대비 **+3.9dB, 붕괴 뷰 1/7로 급감** — 동일 예산·동일 eval에서 아키텍처 전환만으로 천장 돌파. 좌표계 정렬 확인(문 키패드·비상구 GT 일치, max 39dB). 배치 상한 30.2dB와의 격차는 ① raw SLAM init(hybrid 미적용) ② floater 바늘 아티팩트 — 둘 다 Phase D(hybrid init+carve loss)가 겨냥. v1 무튜닝이라 헤드룸 큼. ⚠ eval 중 GPU 확보하려다 사용자의 별개 Isaac Sim 프로세스를 종료함(사과, 재시작 필요). 다음: Phase D 방법론 이식. → [exp49](experiments/exp49_photoslam_plan.md)
- **2026-07-16 밤 (exp49 착수 — Photo-SLAM으로 incremental baseline 이관, 빌드 완료)**: exp48 종결 판단 — vanilla 3dgs-custom 위에 windowed/online을 얹는 자체구현이 근본 한계(reset_opacity·LR감쇠·윈도우 이탈을 맨땅에서 재발견). survey list(Awesome-3DGS-SLAM) 조사 후 **Photo-SLAM(ORB-SLAM3+GS, CVPR24)** 채택 — EuRoC config에서 `opacity_reset_interval:0`·상수 LR·hard-evict 없는 times-of-use 슬라이딩 윈도우 확인, exp48에서 하나씩 꺼봤다 실패한 것들이 여기선 geometry densification과 묶여 통째 적용돼 있음. `repos/main/Photo-SLAM` 심링크 연결 후 **RTX 5070 Ti(Blackwell)+CUDA12.8+LibTorch2.9+자체빌드 OpenCV4.13 조합으로 전체 빌드 성공**(로직 불변, 호환성 패치만: CUDA arch 120·헤더·torch::cat·c10 API·CMP0146 등). 핵심 우회로 발견: `train_colmap.cpp`가 `GaussianMapper`를 `pSLAM=nullptr`로 구동 → **매핑 백엔드만 떼어 우리 데이터 replay 가능, Aria Fisheye624가 스톡 ORB-SLAM3에서 안 되는 문제를 통째로 우회**. Phase A(파이프라인 생존)→B(1253 RGB 배치 baseline, 동일 eval 하네스)→C(incremental replay 진입점)→D(hybrid init+carve loss 이식) 계획. → [exp49](experiments/exp49_photoslam_plan.md)
- **2026-07-16 밤 (exp48 ⚠ eval 스크립트 버그 발견 — 바로 아래 항목의 "chunk 18/19 공백" 설명 폐기, 진짜 원인 재확정)**: 사용자 요청으로 antigravity의 v2~v4 결과("median 18.27dB, chunk18/19 사이 공백이 원인")를 검증하던 중, `3dgs-custom/scene/dataset_readers.py:238~248`에서 **`--eval` 시 `llffhold` 기본값 8이 항상 참이라 `sparse/0/test.txt`가 전혀 안 읽히고**, 대신 전체 1,303프레임을 이름순 정렬 후 8번째마다 뽑는 게 실제 테스트셋임을 발견(우연히 개수 163으로 동일해 안 들킴). 실측 검증: eval 인덱스 "00056.png"의 실제 원본은 `test.txt` 가정대로면 `frame_00636`(책상)이어야 하나, 실제로는 `frame_00449`(화이트보드)와 픽셀 일치. **즉 이전 항목의 "held-out 163뷰=frame_580~742 연속 블록", "chunk_019 vs chunk_021", "chunk18/19 사이 공백" 전부 잘못된 프레임 매핑 위의 이야기.** 매핑을 llffhold-8 기준으로 바로잡아 같은 v4 런의 `per_view.json`을 재분석한 결과, 여전히 뚜렷한 비무작위 패턴 확인: **chunk 14-20(프레임 ~430-700, kf 54-83) 평균 9.6~17dB로 최악, chunk 47-56(후반부, 프레임 ~1230-1300) 평균 25~34dB로 최고.** 육안 검증: chunk 15 대표 이미지가 정확히 그 화이트보드 근접샷(최초 직감은 맞았고 청크 번호만 틀렸음), chunk 50은 반복 등장하던 그 복도 뷰. map point 수로는 설명 안 됨(나쁜 구간이 오히려 SLAM point 더 많음, 62~338 vs 3~97) — **화이트보드류 저텍스처 근접 표면 자체가 SLAM·depth-pro 양쪽 다에게 근본적으로 어려운 영역**이라는 게 진짜 원인. antigravity의 K=3 PPM/RoMA/selective-reset 3연속 수정이 거의 안 움직인 것(18.0→18.23dB)도 이걸로 설명됨 — "대표 프레임이 놓쳤다"가 아니라 그 영역 자체가 어떤 init 방법으로도 잘 안 잡히는 저텍스처 지역이었기 때문. eval 버그 자체는 지금까지의 모든 exp48 PSNR 숫자에 일관 적용됐으므로 상호 비교는 유효(같은 기준), 다만 "특정 구간 콕 집어 분석"할 때는 반드시 llffhold-8 기준으로 매핑할 것. 다음 과제: ① eval 버그를 고칠지(`llffhold=0`으로 test.txt 사용 vs 지금 방식 표준 채택) 결정, ② 저텍스처 구간 전용 대책(풀 하이브리드 예산 확대 또는 근본 한계 인정), ③ 후반부 고PSNR이 "반복 방문 성숙" 때문인지 궤적 대조로 확인. → [exp48](experiments/exp48_incremental_plan.md)
- **2026-07-16 밤 (exp48 Incremental 3DGS 하이브리드 완벽 완주 및 Selective Opacity Reset 도입)**: PPM K=3 다각도 투영(v2) 및 RoMA dense correspondence(v3_hybrid)를 이식하여 18.12dB까지 점진적 개선. 온라인 3DGS의 고질적 병목인 전역 opacity 리셋의 루프 홀(윈도우 밖 영역이 리셋 후 복원되지 못해 궤멸)을 규명하고, 활성 윈도우 가우시안만 선별 리셋하는 **Selective Opacity Reset** 기법을 제안 및 구현(v4). 그 결과 가우시안 소멸을 차단(83만→116만 개 보존)하여 **중앙값 PSNR이 17.20→18.27dB로 대폭 상승(1.07dB 쾌거)**. 여전히 18dB대에 정체하는 이유는 held-out 163뷰가 하나의 연속 블록으로 구성되어 chunk 18(전방 뷰)과 chunk 19(후방 뷰) 사이에 공간적 학습 공백이 발생하여 co-optimization이 일어나지 않기 때문임을 규명. 향후 윈도우 크기를 확장하여(예: window_size = 10 또는 15) 두 뷰포인트를 동시에 최적화하는 진단으로 이어갈 것을 권장함. → [exp48](experiments/exp48_incremental_plan.md)
- **2026-07-16 밤 (exp48 PSNR 30 벽 원인 규명 — 대표 프레임 1장의 커버리지 구멍)**: 바로 아래 항목(depth-mono+PPM 연결, 18.0dB)에서 왜 여전히 통제 실험 30.2dB에 못 미치는지 분석. "샘플링 운" 가설은 draw_count-PSNR 상관계수 0.025로 기각. 163개 held-out 뷰의 PSNR을 프레임 단위로 정렬하니 최저 10개(`frame_00633~641`)와 최고 10개(`frame_00726~738`)가 각각 촘촘히 뭉쳐있어 국소적 원인임을 확인. 실제 청크 이미지 폴더로 역추적(타임스탬프 이분탐색 방식은 인덱싱이 밀려 오답 — 실제 파일 목록 대조 필수)한 결과 최저 구간은 `chunk_019`, 최고 구간은 `chunk_021` 소속. 두 청크의 depth-mono+PPM 대표 프레임(keyframe당 `frame_00001.jpg` 1장만 사용)을 육안 대조: **`chunk_019` 대표 프레임은 책상/선반 장면인데 실제 GT(`frame_00636`)는 화이트보드 근접 샷 — 완전히 다른 뷰.** 반대로 `chunk_021` 대표 프레임은 실제 GT(`frame_00736`)와 거의 동일한 복도 뷰. **원인 확정: depth-mono+PPM init이 청크당 대표 프레임 1장에만 묶여있어, 그 청크의 dense 50프레임 동안 카메라가 크게 움직이면 대표 프레임이 놓친 영역은 init 자체가 없는 채로 photometric loss만 받음** — 여기에 기존에 밝혀진 "윈도우 벗어나면 못 여문다" 문제가 곱해져 청크별로 30dB대/10dB대 양봉분포가 생기고 평균이 눌림. 다음 제안: 대표 프레임 1장 → 청크 내 다중 프레임(처음/중간/끝 등)으로 depth-mono+PPM 소스 확장 — RoMA 연결보다 우선순위 높은 저비용 고효과 후보. → [exp48](experiments/exp48_incremental_plan.md)
- **2026-07-16 밤 (exp48 depth-mono init 연결 — 첫 실제 개선)**: 배치 챔피언(exp44d2) init이 RoMA+PPM+depth-mono 3종 조합이라는 지적을 받아, 그중 depth-mono+PPM(Sobel 적응 샘플링) 먼저 연결. 신규 `build_depthmono_ppm_chunks.py`가 `build_hybrid_init_scene.py`의 depth-lift 로직을 재사용하되 **그 keyframe 시점까지 누적된 SLAM point만으로 Huber 스케일 보정**(인과 순서 유지) — 57개 중 56개 keyframe 성공. `train_incremental.py`에 `--init_source both` 추가해 SLAM+PPM 결합 결과 **평균 PSNR 15.7→18.0dB, PSNR<15 뷰 107→41개** — 가설 라운드 2(opacity_reset·LR, 전부 무효과)와 달리 **처음으로 실제 개선**. 다만 통제 실험(30.2dB)과는 여전히 격차 큼 — "윈도우 벗어난 영역은 안 여문다"는 근본 문제는 미해결, 더 나은 재료로 그 위에서 개선된 정도. 다음: RoMA 연결(같은 인과 순서 원칙), 아키텍처 재설계 여부는 별도 결정. → [exp48](experiments/exp48_incremental_plan.md)
- **2026-07-16 밤 (exp48 opacity_reset·LR 가설 둘 다 기각 — ancestor 추적으로 진짜 원인 재규명)**: 바로 아래 항목의 "유력 범인 opacity_reset" 가설을 실제로 끄고(+LR도 고정값으로) 재검증했는데 **둘 다 무효과**(15.4~15.6dB, 그대로). `--trace_event`(신규, `ancestor_idx` 계보 추적) 진단으로 event 5의 gaussian 혈통을 57개 이벤트 끝까지 따라간 결과, reset이 윈도우 밖 영역을 96% 죽이는 메커니즘 자체는 실재 확인됐으나, **꺼도 안 죽을 뿐 살아남은 gaussian이 opacity 0.14~0.16 수준에서 "미성숙 상태로 방치"돼 결과는 똑같이 나쁨.** → **결론: opacity_reset·LR 감쇠는 증상이었지 근본 원인이 아니었음. "윈도우를 벗어나는 순간 그 어떤 설정으로도 다시 여물 기회가 없다"는 구조 자체가 진짜 원인.** 다음 결정: ① VINGS-Mono의 관측시점 즉시-국소정리 방식으로 아키텍처 재설계 vs ② 윈도우를 훨씬 키워서 회복 경계값 스캔. → [exp48](experiments/exp48_incremental_plan.md)
- **2026-07-16 (exp48 Phase 0b "완료" 판정 철회 + v2 재설계 + 원인 진단)**: 바로 아래 07-15 항목의 "크래시 없이 완주"는 프로세스 생존만 확인한 것이었고, **실제 held-out 163뷰 PSNR을 재보니 15.8dB**(챔피언 32~35dB 대비 사실상 미학습) — 성공 기준 3(렌더 정상)을 검증 없이 통과시킨 오판. 원인: "1 keyframe=1 이미지, 재방문 없음" 구조라 장면의 97%가 사실상 1회성 학습 후 방치. `train.py`는 incremental 오염 제거 후 원복, 신규 `train_incremental.py`(로컬 윈도우+freeze-when-stable, VINGS-Mono_custom 이식)로 재설계. **4개 변형(keyframe-only/dense frame/densify 유무) 전부 15~17dB 천장에서 안 움직임.** 결정적 통제 실험: 같은 8,550 iteration을 원본 batch train.py로 전체 씬 동시 접근하면 **30.2dB** — "iteration 부족"이 아니라 **windowed 구조 자체가 원인**임을 확정. 유력 범인: `reset_opacity`(3000 iter마다 전체 opacity 강제 리셋)가 윈도우에서 이미 빠진 영역을 영구히 죽임 — **VINGS-Mono_custom 코드 대조로 확증**(`reset_opacity`/LR 감쇠 스케줄이 그 코드베이스엔 아예 없음, 온라인 세팅과 근본적으로 안 맞아 의도적으로 뺀 것으로 판단). 다음: opacity_reset 끄기·LR 고정값 전환 검증. → [exp48](experiments/exp48_incremental_plan.md)
- **2026-07-15 밤 (exp48 incremental Phase 0b 완주, ⚠ 아래 07-16 항목에서 판정 철회됨)**: 57개 keyframe 전체 warm-start 루프를 크래시 없이 완주. 소요 시간 ~17분. Gaussian 수 405개(chunk_000) → ~52,000개(chunk_056)로 단조 증가 확인. 코드 리뷰 수정 3건 포함: ① capture/restore에 트래킹 버퍼 9종 포함(학습 이력 보존), ② chunk≥1에서 `extra_points3D.txt` 분리 공급(더블 로딩 제거), ③ `getNerfppNorm()`에 radius=0 fallback 추가 (chunk_015에서 단일 카메라 청크의 cameras_extent=0 원인으로 모든 Gaussian이 전량 prune되는 치명적 버그 수정). → [exp48](experiments/exp48_incremental_plan.md)
- **2026-07-15 (exp47 속도 최적화 트랙 완료)**: **S2(cheapcarve)에서 화질 무손실(35.116dB) + 시간 60% 단축(26.8분)으로 최대 성과.** S1S4(53.8분/34.47dB), S4(53.8분/34.40dB), S5(1시간3분/34.40dB), S6(56분/35.55dB), TARGET(12.6분/32.94dB, 기각) 완주. GPU 상주(CUDA)가 전송 오버헤드가 아닌 CPU Carve 연산이 병목임을 증명. 최종 Pareto 최적 속도-품질 가속 레시피 도출: **S2(cheapcarve) + S4(kf300) + S5(budget235k) + 30k iterations = 예상 21~23분 완주 및 PSNR ~34.4dB (품질 하한 충족)**. → [exp47](experiments/exp47_speed_track_plan.md)
- **2026-07-15 (exp46 8축 배치 완주)**: **init이 floater의 단일 지배 레버로 확정.** init측 축(1 305hybrid +1.33dB·먼지461→4 / 2 12Fhybrid +3dB / 3 표면확신opacity 먼지-21%) 전부 성공, loss/carve/densify측 축(7 원거리감쇠·7b max-dist·B footprint carve ×5역효과·6 no-densify -1.3dB) 전부 실패. birth-redirect(5) 소폭. **경량화(A 122k)는 +3dB 소실→baseline** — dense init이 품질 근원이나 무거움, 중간 budget(250~350k) 탐색이 분단위 파이프라인 다음 관문. 사용자 원거리 통찰: 진단 옳음(먼지 98% 원거리)·처방(loss 제거) 무효. → [exp46](experiments/exp46_basin_reframe_plan.md)
- **2026-07-14 (exp46 basin 실험)**: **"좋은 init(depth-lift hybrid)"이 전 장면 단일 지배 레버 확증.** 305: PSNR 35.84(최고)·free-space 먼지 461→4. **12F(fog): PSNR 32→35.07(+3dB), 먼지 청소 후에도 유지 → fog=환원불가(b) 예측 결정적 반박, 12F도 (a)형.** 원거리 photometric 감쇠(사용자 축7)는 진단은 확증(먼지 98% 원거리)이나 처방 기각(먼지↑·PSNR↓ — 먼 영역은 loss 빼기가 아니라 양의 prior 필요). self-diagnosis 규칙3 수정("carve off"→"depth-lift hybrid init"). 신규 과제: init dedupe/budget(hybrid 362-586k 무거움). → [exp46](experiments/exp46_basin_reframe_plan.md)
- **2026-07-13 오후 (vr 채널)**: 사용자 질문("SLAM 포인트 없이 12F floater 잡기")에서 출발 — ① **SLAM-포인트-프리 탐지 성립**: depth-pro raw 0.855 → pose-기하 자가 보정(스테레오+IMU 캘리브레이션 덕에 pose가 미터) 0.893, SLAM 보정 상한 0.908=12F 신기록. ② vr을 CarveLoss score 채널로 통합(depth_dir config)했으나 **학습 효과 무** — "탐지≠제거" 간극 확정: underfit 장면에선 이미지가 먼지를 요구해 압력이 못 이김. ③ **12F에서 carve 자체 -1dB → 자가진단 경고 시 carve off가 파이프라인 규칙로 확정.** vr 용도는 오프라인 청소·pseudo-label·SLAM-프리 탐지. → [exp43 카드](experiments/exp43_cross_scene_plan.md)
- **2026-07-13 오전 (231 사이클)**: **exp43 종결** — ① 305 재현 런으로 depth-anchor carve **성공 확정**(먼지 -83% 정밀 재현). ② rot '가시 먼지 역증가' 미스터리 해결: 응집·force·재분배 가설 3연속 기각 끝에 **대조군(baseline 재실행 106→1,091)이 run-to-run 분산임을 입증** — carve 무죄, **먼지 지표 단일 런 비교 금지**(pitfalls). ③ 라벨 없는 **앵커 자가진단 2규칙 완성**(`anchor_self_diagnosis.py`, 4/4 장면): SLAM 자기NN<0.05m → SLAM / depth 교차불일치<0.04 → depth / 둘 다 실패 → 문제 클래스(12F가 정확히 해당). 새 장면 파이프라인 라벨 없이 전자동으로 폐합. 시차 쌍 hyb2는 rot에서 여전히 부적합(회전 궤적 축 보류). → [exp43 카드](experiments/exp43_cross_scene_plan.md)
- **2026-07-13 새벽 (오버나이트)**: **exp43 교차 장면 트랙 완주 — 305에서 carve 학습 재현 성공** (depth-anchor 처방: 먼지 -83%·가시 -76%·PSNR 동급). 사용자 라벨 3종(1253_rot/305/12F) 검증: rot는 pseudo-label 정밀도 100%·AUC 0.98(같은 방 자동화 가능), 305·12F는 SLAM 커버리지 부족으로 champion score 실패(0.80/0.86) → **depth-pro 표면 앵커로 회복(0.905)**. 실패 5건 정직 기록: dynamic carve 자기강화 가설 기각, nomaxop 기각, rot hybrid 이식(+1.37dB나 먼지 ×10, 작은 시차 삼각측량), rot depth 앵커 불량(회전 궤적), 305 1차 OOM. **결론: carve 성패 = 앵커 품질. 다음 열쇠 = 라벨 없는 앵커 자가진단 + 시차 기반 쌍 선택.** → [exp43 카드](experiments/exp43_cross_scene_plan.md)
- **2026-07-12 오후**: **exp44 고속 geometry 트랙 완주 — 44h 레시피 채택** (총 ~11분/장면: SLAM 후 init 전처리 3분 + 학습 7.5분 → PSNR 32.08·먼지 -63%). 4원칙 확립: 먼지는 init에서(필터 -96%)·색은 선불(+1.6dB)·갭은 배치(스냅 init)·용량은 densify 3k로 충분. RoMA(44c) 불필요 판정. 교차 장면: 305 라벨 대기, 1253_rot pseudo-label 완비, 복도류(12F/2F/3F/snu) 전멸 → 저텍스처 한계 별도 축. → [exp44 카드](experiments/exp44_fast_geometry_plan.md)
- **2026-07-12 심야~아침**: **carve loss 학습 검증 트랙(exp38~40) 하룻밤 완주 — exp40b 채택** (학습이 회당 ~10분임이 판명되어 7 run 수행). 렌더 A/B로 "floater=train PSNR 기생충" 발견(수동 편집조차 -3.7dB → train PSNR 지표 부적합), gradient 프로브로 진동 평형 확인 → carve-potential force(3D force 부활) 구현·실증(무비용 -45% 가시 먼지), softlite+force 결합이 PSNR 무손실로 region 먼지 -86%. 출생 로그로 "허공 split 29.5%, 먼지가 먼지를 낳는 연쇄" 규명. → [exp38-40 카드](experiments/exp38_40_carve_track.md), [round8_gpu_queue_plan](rounds/round8_gpu_queue_plan.md)
- **2026-07-11**: **Carve Loss 설계 완료 (분석만, 학습 없음)** — 카메라→SLAM 포인트 ray의 free-space carving 증거비 ρ(x)에 anchor 거리를 곱한 score w(x)가 수동 floater 판별 **AUC 0.974** (plateau 0.511). 수동 floater가 opacity 중앙값 0.044의 "한계 생존자"임을 발견(카드의 op>0.5 서술은 오류였음, 정정 완료). **부수 피해 재정량**: 원안 prune 규칙은 표면 시각 기여량 3.83% 손실로 폐기, 안전 규칙(w>0.9 & op<0.1 & contrib<p90)은 **recall 69.4%·기여손실 0.39%·구멍 0**. densify 게이트는 출생 91% 차단 가능하나 기여량 13.75% 영역에 걸려 학습 검증 필요. 렌더 PSNR 검증용 pruned 모델 4종 준비 완료(GPU 대기). → [carve_loss_design](rounds/round8_carve_loss_design.md)
- **2026-07-11**: **plateau 방식으로 수동 floater 2,817개를 해결할 수 없음을 학습 없이 정량 확정** (`verify_plateau_capability.py`). 실제 학습 field(DepthPro anchor + ellipsoidal 적응형 tau) 기준 floater의 66%가 plateau 안이라 gradient 0 (측정 telemetry로 교차검증됨), 정규화 거리 D의 floater 판별 AUC 0.511(무작위). 단 raw 유클리드 거리는 AUC 0.93(SLAM) — **신호는 존재하나 적응형 tau가 판별력을 파괴**. λ 크기는 애초에 문제 아니었음. → [exp32_lineage_diag §3](experiments/exp32_lineage_diag.md)
- **2026-07-11**: 사용자가 직접 SuperSplat으로 정밀 편집한 `point_cloud_cleaned.ply` (2,817개 floater 삭제)에 대한 수동 분석 완료. 수동 floater들은 표면 대비 RGB gradient를 2.23배 높게 받으며 소멸에 저항했고, Plateau gradient는 0.58배 적게 받으며 허공(outlier)에 방치되었음을 입증. 대다수(69%)가 3k~7k step 사이의 후반부에 split(평균 5.73회)을 통해 생성되었고, Seed 5061(10%) 등 특정 조상 포인트가 증식을 대량 주도함. -> [exp32_lineage_diag](experiments/exp32_lineage_diag.md)
- **2026-07-10**: floater 계보 및 gradient 분리 진단 실험(`exp32_lineage_diag`) 완료. 명시적 floater가 미관측 void 영역에 갇혀 RGB gradient가 정상의 1/4배(`0.14` vs `0.55`)로 억제되었음을 입증. 특히 Plateau loss가 10배 더 강하게 복구력을 가했음에도 이들이 opacity > 0.5로 생존했으며, 특정 seed 두 개(7015, 5392)가 전체 floater의 70%를 생산하는 주범임을 최초 정량 확인. -> [exp32_lineage_diag](experiments/exp32_lineage_diag.md)
- **2026-07-10**: floater 지표 재검토. \|Z\|>4m·plateau-inside-ratio 둘 다 부정확함을 확인 — plateau loss 없이도 enlarged tau는 자연히 97~98% "안"(tau가 커서 변별력 없음). ray-density 기반(카메라가 한 번도 안 본 3D voxel + opacity) 재측정 결과 **enlarged tau plateau(exp33/36)가 기본 tau(exp32/35)보다 진짜 floater(opacity>0.5)가 6.6배 많음** — enlarged tau의 넓은 plateau가 관측 불가 공간까지 침범하기 때문(불관측 voxel의 8~22배가 plateau 안). exp37(dense init)이 모든 지표에서 최선으로 재확인. → `experiments/exp30_37_orb_native_track.md`, `knowledge/pitfalls.md`
- **2026-07-09**: exp30~37 — **OpenMAVIS(ORB) 데이터셋 재현 트랙 완료**. MPS 트랙(exp08~29)에서 검증한 방법(anchor init, plateau)을 실제 목표 데이터(`data/03_rgb_3dgs_full`)로 재현. **핵심 결과**: exp37(SLAM core seed dense init 148,564pts, plateau 없음) PSNR 32.621, **|Z|>4m=0** — 이 트랙 최고의 floater 억제. plateau의 tau 크기 효과는 MPS와 정반대(ORB는 기본 tau가 더 나음). 고confidence anchor seed로 추가 dense init 2종(144,830 / 65,095pts)도 생성, 3D 균질성 확인(NN spacing이 voxel 크기와 일치, 근/원거리 편향 없음). → `experiments/exp30_37_orb_native_track.md`
- **2026-07-09**: exp28/29 — 정렬 anchor로 plateau 재실행. **예상외 결과**: 기본 tau(exp29=32.752)도 enlarged tau(exp28=32.864)도 미정렬 버전(exp19=32.753, exp25=32.969)과 거의 동일 — plateau loss 자체에는 정렬 효과가 미미함 (λ가 작아 위치 오차의 영향이 작았던 것으로 추정). 정렬이 크게 효과 본 곳은 **anchor를 init으로 쓸 때**뿐 (exp27→27c +2.07dB).
- **2026-07-09**: exp27/27b/27c — anchor를 init으로 사용해 품질 검증. **좌표계 버그 발견**: exp19~26의 anchor는 Atlas world 그대로였음. Umeyama 정렬(rmse 2cm) 후 anchor init 31.611 (대조군 30.583, 미정렬 29.540). → `experiments/exp27_anchor_init.md`
- **2026-07-07**: scripts/·results/ 재구조화. scripts는 pipeline/experiments/diagnostic/analysis/anchors 5분류, results는 experiments/rounds/diagnostic/datasets/logs/archive 6분류 (각 README 참조). 실패 run은 `results/archive/failed_runs/`. 문서 내 경로 참조 일괄 갱신됨.
- **2026-07-07**: data/ 전면 재구축. 순수 OpenMAVIS 체인(VRS→EuRoC→SLAM→전체 프레임 RGB 3DGS)으로 `data/03_rgb_3dgs_full` 생성 (1303장, ORB 7,205pts, reprojection 검증 통과). 재현: `scripts/pipeline/run_full_pipeline.sh`. 기존 심링크 무더기 제거 (`data/README.md` 참조).
- **2026-07-05**: exp19~26 MPS plateau 변형 sweep 완료. tau 확대(exp25)만 유효, opacity_weight/exp_loss/adaptive_prune는 모두 PSNR 악화. → `rounds/round7_plateau_mps.md`
- **2026-07-05**: exp15~18 ORB plateau (Round 6). 어떤 설정도 baseline 못 이김. ellipsoidal >> spherical (+1.0dB). → `rounds/round6_plateau_orb.md`
- **2026-06-30**: exp13 camera-bound filter로 Pop1 -99% 해결 (PSNR -0.16dB). → `rounds/round5_findings_summary.md`

## 다음 실험 후보 (우선순위순)

> **프로젝트 목표 재정의 (07-12)**: Aria glass 실시간 촬영 스트림 → 분 단위 turnaround로 geometry 좋은 3DGS recon. 실시간 경로엔 MPS 사용 불가 → ORB 트랙이 본선.
> **재우선순위 (07-15 밤)**: exp47 배치 속도 트랙은 종료, **exp48 incremental이 최우선**. 아래 0번이 현재 실질 1순위.
> **재우선순위 (07-17 밤)**: "실시간"이 최우선 기준으로 재확인됨. exp52 VIGS-SLAM이 1253에서 keyframe 30.90dB를 냈지만 오프라인 폴리싱 포함 수치라 **`--pure_online` 재검증(진짜 온라인 품질 + 프레임당 FPS)이 축E보다 먼저 봐야 할 질문**으로 부상.
> **재우선순위 (07-18 밤)**: `--pure_online` 실측 완료 — 순수 온라인 VIGS(22.7~23.5dB)가 우리 exp51(25.29dB)보다 낮음이 확정됐으므로 **VIGS 이식보다 exp51 자체 개선(축E carve loss, normal supervision)이 다시 최우선**.
> **참고 (07-19)**: exp52에서 "실시간화는 컴포넌트 가속이 아니라 구조(비동기 tracking/mapping 오버랩)로 풀어야 한다"는 일반 교훈을 확보(`_gs_parallel`로 −26.1%). 우선순위는 안 바뀜(여전히 0번 exp51이 최우선) — 이 교훈은 CLAUDE.md 3단계("라이브 통합")에서 exp50에 재사용할 자산.
> **참고 (07-20)**: exp52에서 신규 발견한 "Frontend Tracking 자체가 실시간 병목"을 **exp53(신설)**으로 분리해 전담 트랙화(계획 단계, 미착수). 우선순위는 안 바뀜(여전히 0번 exp51이 최우선) — exp53은 exp51 완료 후 착수하거나 여유 볼 때 병행.
> **참고 (07-21)**: exp52의 gs_mapping 12단계 세분화(rasterize+backward+loss_compute=81.4%)를 구체화하는 **exp54(신설, GS Mapping 연산량 ablation, 7축, PPM 이식 포함)**. 우선순위는 안 바뀜(여전히 0번 exp51이 최우선) — exp53/54는 실시간화 트랙으로 exp51과 병행 가능.

0. **exp51 축E(carve loss 이식) 또는 normal supervision 이식**: VIGS 비교로 "폴리싱 없는 우리 축A+B(25.29dB)가 VIGS의 순수 온라인(22.7~23.5dB)보다 이미 낫다"가 확정됐으니, VIGS 아키텍처 자체를 가져오기보다 그 소스에서 발견한 유효 레버(normal supervision, isotropic loss+scale clamp)를 우리 파이프라인에 이식하는 쪽으로 복귀.
0''. **exp48b (carve loss + anti-drift)**: Phase 0b 성공. warm-start loop가 약 52k Gaussian을 유지하면서 57청크 전체 돌아감을 확인 — 다음은 exp48b로 **carve loss과 옵 영역 보호(anti-drift)를 incremental loop에 이식**하는 단계.
0'. exp47 잔여 축(S2 cheapcarve + S4 keyframe subset 조합 등)은 **exp48 Phase 1+에서 청크당 학습 예산 튜닝에 재사용** — 배치 트랙 자체로는 더 이상 추가 실행 안 함.
1. ~~exp44 (고속 geometry 트랙)~~ → **완료**. ~~exp43 (교차 장면)~~ → **완료**. ~~held-out 뷰 평가 도입~~ → **완료**.
2. exp40b 잔여 가시 floater ~25개의 정체 확인 (패치 투영 or SuperSplat) + 렌더-GT 잔차 기반 신호 탐색. (exp48과 무관, 낮은 우선순위로 대기)
3. carve field의 타 장면 일반화는 exp43에서 이미 검증됨(305/rot) — 신규 장면 투입 시에만 재점검.

## 확정된 사실 (자세한 근거는 knowledge/)

- Floater는 두 집단: Pop1(SLAM init outlier) / Pop2(densification floater) → `knowledge/floater_populations.md`
- init 626,811pts의 출처는 ORB-SLAM이 아니라 **Aria MPS semi-dense**, confidence 필드는 현재 버려짐 → `reference/workspace_map.md`
- VGGT는 현 시점 OpenMAVIS 대체 불가 (닫힌 축) → `archive/vggt_evaluation.md`
