# exp57 — 실시간 품질 도약: causal background polishing + 정보량 기반 global replay

- 상태: **strict-disjoint photo+IMU-only 1.5× zero-tail held-out 27dB 진행 중 / 현재 검증 기준선 26.069dB (2026-07-29)**
- 기준선: exp56 Phase 11, `kernel_batch_render=true`
  - 순수 온라인 held-out/keyframe PSNR: **23.46 / 23.98dB**
  - 온라인 루프: **44.00s / 녹화 65.1s = 실시간 배수 0.68배**
  - 종료 후 26k 색정제 포함: exp56 유사 레시피 기준 held-out/keyframe **26.53 / 30.33dB**
- 목적: kernel micro-optimization만으로 몇 %를 더 줄이는 대신, 현재 확보한 실시간 여유를
  **프론티어를 방해하지 않는 인과적 전역 정제**에 재투자하여 순수 온라인 품질을 크게 올린다.
- 번호 변경: exp56 Phase 9~11에서 `exp57`로 부르던 CUDA 내부 visibility/
  `BACKWARD::preprocess` 후속은 [exp58](exp58_cuda_visibility_backward_plan.md)로 이동.

## 현재 1차 목표

- **성공 지표**: held-out PSNR **27dB 이상**
- **입력**: timestamp 순 Aria RGB photo + IMU only
- **금지 입력**: MPS 후처리 trajectory/depth/point cloud
- **시간 제약**: source duration 65.10초의 fixed **1.5× = 97.65초 이내**
- **종료 제약**: 마지막 센서 frame 뒤 optimizer update **0회(zero-tail)**
- 고정 calibration은 허용하지만 pose/depth supervision은 그 시점까지 online으로
  추정된 값만 사용한다.
- 27dB 달성 전에는 hard carve/floater pruning을 품질 레버로 섞지 않는다.
  27dB 달성 뒤 carve를 검증하고, 그 다음 동일 strict 조건에서 30dB+로 확장한다.

## 2026-07-29 실행 결과 요약

### 먼저 확인된 스트리밍 전제

사용자 질문("background global이면 스트리밍을 먼저 구현해야 하지 않나, MPS 데이터를
받아서")을 계기로 입력 경로를 다시 확인했다.

- VIGS의 `demo.py`는 이미 별도 reader process가 RGB+IMU를 시간순 queue로 공급하고,
  도착한 frame/keyframe만 `track()`/`call_gs()`에 넘긴다. 따라서 **미래 frame을
  미리 쓰지 않는 causal replay**는 이미 가능하다.
- 다만 기존 벤치는 파일을 가능한 빨리 읽는 unpaced replay였다. 실제 센서 cadence와
  queue 동작을 재현하지 못했다.
- `--realtime_replay`를 추가해 source timestamp에 맞춰 입력을 공급했다.
- 이 실험의 `data/aria1253/{rgb,imu.txt}`는 Aria 기록을 재생하는 입력이고 MPS pose를
  online 정답으로 넣은 것이 아니다. **실제 장치 live adapter는 아직 미구현**이며,
  MPS는 본질적으로 녹화 후 처리이므로 live pose source로 사용할 수 없다.

### Phase 0-A — full refinement 압축 곡선: 성공

한 번의 unpaced causal replay로 만든 동일 online checkpoint에서 누적 refinement를
실행했다. 모든 held-out 값은 milestone마다 동일한 online tracking trajectory를 고정해
렌더한 VIGS 평가값이며, keyframe 값만 refinement의 per-view pose를 반영한다.

| step | 순수 refinement 시간 | held-out PSNR | keyframe PSNR | held-out Δ |
|---:|---:|---:|---:|---:|
| 0 | 0.00s | 23.47 | 23.91 | — |
| 250 | 1.75s | 23.94 | 24.54 | +0.47 |
| 500 | 3.53s | 24.09 | 24.95 | +0.62 |
| 1,000 | 7.08s | 24.37 | 25.54 | +0.90 |
| 2,000 | 14.21s | 24.75 | 26.33 | +1.28 |
| 5,000 | 36.31s | 25.62 | 27.94 | +2.15 |
| 26,000 | 192.35s | 25.69 | 30.62 | +2.22 |

핵심 판독:

- 2k까지 held-out이 실제로 올라 Phase 0 진행 기준은 통과했다.
- **5k→26k의 추가 156초는 held-out +0.07dB뿐인데 keyframe은 +2.68dB**다.
  기존 26k의 후반 대부분은 실시간 품질이 아니라 training-view fitting이다.
- 따라서 26k 전체를 background로 옮길 이유가 없고 full-scope sweet spot은 2k~5k다.

### Phase 0-B — SH/color-only 곡선: 유효하지만 상한이 낮음

동일 방식의 별도 고정 checkpoint에서 geometry/opacity/pose/exposure gradient를 버리고
`f_dc`/`f_rest`만 갱신했다.

| step | 시간 | held-out PSNR | keyframe PSNR | held-out Δ |
|---:|---:|---:|---:|---:|
| 0 | 0.00s | 23.58 | 24.04 | — |
| 250 | 1.16s | 23.80 | 24.27 | +0.21 |
| 500 | 2.29s | 23.92 | 24.41 | +0.33 |
| 1,000 | 4.66s | 24.03 | 24.53 | +0.45 |
| 2,000 | 9.30s | 24.17 | 24.68 | +0.59 |
| 5,000 | 23.17s | 24.31 | 24.86 | +0.73 |

SH-only도 held-out을 올리지만 full 2k의 +1.28dB 대비 절반 이하다. 즉 큰 품질 도약의
상당 부분은 opacity/geometry/pose 쪽이며, SH-only만으로 26dB 목표는 불가능하다.

### Phase 1 — causal idle scheduler 1차 구현: 구조 검증, 품질은 기각

구현 내용:

- mapper queue가 비고 tracking event가 5ms 이상 idle일 때만 1-step 실행
- 새 tracking/map packet 우선, step 중간 선점 지연은 한 step으로 제한
- 현재 frontier window를 제외한 과거 도착 view를 round-robin 선택
- SH/color만 갱신, densify/prune 및 xyz/scale/rotation/opacity/pose/exposure 갱신 금지
- `background_polish_max_steps=1500`, worker 종료/저장 race 방지

300-frame paced smoke에서는 109 step으로 control 대비 held-out/keyframe
**+0.24/+0.23dB**였지만, 1,303-frame 전체 A/B에서는 run-to-run map 차이를 넘지 못했다.

| paced 1,303 | background off | SH-only background on | 변화 |
|---|---:|---:|---:|
| background step | 0 | 768 | +768 |
| online loop | 74.75s | 74.46s | 차이 없음 |
| held-out PSNR | 24.04 | 23.96 | −0.08dB |
| keyframe PSNR | 24.49 | 24.45 | −0.04dB |
| gaussian | 81,547 | 81,037 | 서로 다른 mapping schedule/run noise |

**판정: 1차 SH-only scheduler는 채택하지 않는다.** 실행 구조와 causality는 검증됐지만
전체 품질 이득이 없다. 정보량 sampler 구현으로 넘어가기 전에 parameter scope와
실시간 baseline을 먼저 해결해야 한다.

### 가장 중요한 반전 — 기존 "0.68배 실시간"은 true-streaming 측정이 아님

unpaced exp56 Phase 11은 44~52초에 끝났지만 paced control은 **74.75초 / 녹화
65.1초 = 1.15배**였다. unpaced 입력에서는 mapper가 밀리며 오래된 packet을 더 많이
drop해 빨리 끝났고, timestamp-paced 입력에서는 mapper가 더 많은 packet을 받아
처리하다 backlog가 생겼다. 따라서 기존 수치는 처리량 벤치로는 유효하지만 실제 live
cadence의 end-to-end deadline을 보장하지 않는다.

**다음 순서**:

1. paced replay를 본선 속도 하네스로 고정하고 exp56 frontier/map budget을 다시
   65.1초 아래로 맞춘다(명시적 deadline/token budget 또는 map packet rate 제한).
2. 그 위에서 1~2k 상당의 spare budget을 정확히 계측한다.
3. SH+exposure → +opacity → confidence-gated geometry 순으로 고정-checkpoint 곡선을
   측정하고, held-out 이득이 있는 최소 scope만 scheduler에 연다.
4. 그 뒤에야 residual/staleness/coverage sampler(Phase 2)를 비교한다.

산출물:

- `results/experiments/exp57_polish_curve`
- `results/experiments/exp57_appearance_curve`
- `results/experiments/exp57_background_{smoke,smoke_control,full,full_control}`
- VIGS 코드: `demo.py --realtime_replay/--polish_milestones/--polish_scope`,
  `vigs.py` idle scheduler, `gs_backend.py` milestone 및 appearance-only refinement,
  `config/exp57_background_polish.yaml`

## 2026-07-29 추가 — Aria 입력이 1.5배 느릴 때 5k 품질을 유지할 수 있는가

### 이전 26k 해석 정정

앞 절의 "5k→26k 후반은 과적합" 표현은 held-out과 keyframe을 분리하지 않아 너무
강한 결론이었다.

- 5k full: held-out **25.62**(+2.15), keyframe **27.94**(+4.03)
- 26k full: held-out **25.69**(+2.22), keyframe **30.62**(+6.71)

즉 기존처럼 26k에서 keyframe 30dB는 정상적으로 재현됐다. 이번 curve의 held-out은
polishing 전 online trajectory를 고정했지만 기존 exp56 final 26.53/30.33은 offline
BA+final remap+refined keyframe pose를 trajectory에 반영한 수치라 직접 비교가 아니다.
5k→26k held-out +0.07dB만으로 과적합을 확정할 수 없으며, pose를 milestone별로
trajectory에 반영한 재평가가 필요하다.

### 실험 설정

- 실제 RGB timestamp 간격을 `1.5×`로 늘림:
  65.10초 기록 → **97.65초 입력 stream**
- 미래 frame을 사용하지 않는 reader queue causal replay
- background 최대 5,000 step
- mapper/tracking 우선, 5ms 이상 idle일 때만 과거 view 1-step
- `--replay_time_scale 1.5` 추가

offline `color_refinement`와 똑같이 camera pose까지 background에서 갱신하는 1차
smoke는 Camera cached inverse tensor를 `update_pose()`가 in-place 변경해 다음
autograd graph와 충돌(`LinalgInvExBackward0 version mismatch`)했다. 해당 run은
실패로 기록하고 종료했다. 안전 범위를 **Gaussian-full**(SH+xyz+opacity+scale+
rotation, RGB/depth/normal loss; camera pose/exposure 고정, densify/prune 없음)로
축소해 재실행했다.

### 1.5× 전체 A/B 결과

| 1,303-frame, 1.5× paced | control | Gaussian-full background | 변화 |
|---|---:|---:|---:|
| 입력 target 길이 | 97.65s | 97.65s | — |
| online loop | 약 102.1s | 약 102.0s | **추가 지연 없음** |
| 실시간 배수(1.5× stream 기준) | 1.045배 | 1.044배 | 둘 다 약 4.4% 초과 |
| background step | 0 | **3,194** | 5k의 63.9% |
| held-out PSNR | 23.74 | **23.98** | **+0.25dB** |
| keyframe PSNR | 24.18 | **24.37** | **+0.19dB** |
| held-out LPIPS | 0.4663 | **0.4561** | 개선 |
| gaussian 수 | 70,971 | 66,281 | mapping schedule/coverage 차이 |

### 판정

- **1.5배 느린 Aria stream이면 약 3.2k의 안전한 Gaussian polishing을 추가 지연 없이
  흡수하며 품질도 +0.2~0.25dB 개선할 수 있다.**
- 그러나 고정 checkpoint에서 측정한 5k full 결과(held-out 25.62dB)는 유지하지
  못했다. 실제 stream에서는 5k 전부가 들어가지 않았고 camera pose refinement를
  제외했으며, background와 frontier의 schedule이 달라졌기 때문이다.
- control 자체도 target 97.65초보다 약 4.4초 느리므로 엄밀한 deadline은 아직
  실패다. 현재 3,194 step이 추가 지연을 만들지는 않았지만, true live 합격을 위해
  base mapper를 4~5% 줄이거나 input queue backlog를 보는 deadline-aware polish
  gate가 필요하다.
- 다음 유효 실험은 "무조건 5k"가 아니라 **2.5k~3k cap + queue backlog/deadline
  token gate**로 97.65초 안에 강제하고, exposure/pose는 cache-safe한 별도
  refinement boundary에서만 여는 것이다.

추가 산출물:

- `results/experiments/exp57_gaussianbg_15x_smoke`
- `results/experiments/exp57_gaussianbg_15x_full`
- `results/experiments/exp57_15x_control`
- 실패 기록: `results/experiments/exp57_fullbg_15x_smoke`

## 2026-07-29 추가 — dense RGB gradient의 상한과 1.5× causal 통합

### 비키프레임 RGB supervision 상한

종료 후 고정 online checkpoint에 keyframe뿐 아니라 비키프레임 RGB를 supervision으로
추가했다. evaluator가 쓰는 `idx % 5 == 0`과 겹치지 않도록 `idx % 5 == 2`만 사용했고,
keyframe도 제외했다. 총 231개 RGB-only view를 추가했으며 pose는 `traj_filler` 결과를
사용했다. 이 단계는 미래 frame을 모두 받은 뒤 실행한 **gradient-quality upper-bound**이고
causal online 결과가 아니다.

| step | 시간 | held-out PSNR | keyframe PSNR | held-out Δ |
|---:|---:|---:|---:|---:|
| 0 | 0.00s | 22.83 | 23.22 | — |
| 500 | 4.45s | 24.51 | 24.89 | +1.68 |
| 1,000 | 8.90s | 24.96 | 25.49 | +2.12 |
| 2,000 | 17.95s | 25.39 | 26.30 | +2.55 |
| 5,000 | 45.10s | **26.13** | **27.79** | **+3.30** |

기존 keyframe-only 5k의 within-run held-out 상승은 +2.15dB였다. dense RGB는 한 step
비용을 약 24% 늘렸지만 5k 개선폭을 **+1.15dB** 키웠다. 즉 현재 큰 병목은 단순
iteration 수뿐 아니라 gradient를 만드는 관측 뷰의 밀도이며, North Star 문서의
`dense-frame supervision` 우선순위를 VIGS에서도 직접 확인했다.

### 실제 1.5× stream에 causal 통합

다음 keyframe이 도착했을 때만 직전 두 tracked keyframe 사이의 과거 RGB frame pose를
SE(3) 보간해 mapper에 등록했다. 따라서 미래 keyframe은 사용하지 않으며, dense view는
Gaussian 생성·depth/normal loss·camera pose update 없이 RGB loss만 제공한다.
background sampler는 기존 keyframe과 도착 완료된 dense view를 함께 round-robin한다.

300-frame smoke에서 dense 29개/616 step으로 정상 완주한 뒤 1,253-frame을 두 번
실행했다. 평가 활성 run 결과:

| 1.5× paced | keyframe-only background | + causal dense RGB | 변화 |
|---|---:|---:|---:|
| 입력 target | 97.65s | 97.65s | — |
| tracking 입력 처리 | — | **97.33s** | deadline 내 |
| mapper drain 포함 online loop | 약 102.0s | **98.47s** | 0.82s 초과 |
| background step | 3,194 | **3,821** | +627 |
| causal dense view | 0 | **108** | +108 |
| held-out PSNR | 23.982 | **24.227** | **+0.245dB** |
| keyframe PSNR | 24.369 | **24.499** | **+0.131dB** |
| held-out LPIPS | 0.4561 | **0.4532** | 개선 |

평가 없는 독립 반복도 98.45s, dense 110개, 3,742 step으로 거의 같아 runtime은
재현됐다. 입력 자체는 cadence를 따라갔지만 종료 시 mapper backlog를 비우는 1.14초
때문에 엄밀한 end-to-end deadline은 **0.84% 실패**다.

판정:

- dense-frame gradient는 offline 상한(+3.30dB)과 causal 1.5×(+0.25dB) 모두
  held-out을 개선해 **방향 채택**.
- 그러나 1.5×에서 기존 5k checkpoint 25.62dB를 유지하지는 못했다. causal pose가
  단순 keyframe 보간이고, map이 계속 변하는 동안 3.8k step이 분산되며, 마지막
  미완결 keyframe 구간의 dense frame은 아직 등록되지 않는 차이가 있다.
- 다음은 2× budget에서 5k cap 상한을 확인하고, random/round-robin 대신 residual과
  view novelty로 dense view의 gradient 효율을 높인다. 실제 Aria live에서는 MPS가
  postprocessing pose source가 될 수 없으므로 Fisheye624+IMU localization pose를
  같은 dense-view 입력 인터페이스에 공급해야 한다.

추가 산출물:

- `results/experiments/exp57_densepolish_curve`
- `results/experiments/exp57_causal_dense_15x_{smoke,full,eval}`
- VIGS 코드: `--background_dense_stride`, causal SE(3) keyframe-bracket 등록,
  keyframe+dense background sampler

## 2026-07-29 최종 — 27dB를 1.5× live budget 안에서 달성

### streaming 중 분산 5k가 안 된 이유

2× timestamp stream(130.20초 budget)에서 causal dense Gaussian background를
5,000 step 전부 실행했지만 held-out/keyframe은 **24.24/24.51dB**로 1.5×의
24.23/24.50과 같았다. 실행은 128.59초로 deadline을 통과했다. 즉 step 수가 아니라
**계속 생성·prune·pose-correct되는 미성숙 map에 gradient를 너무 일찍 적용해 update가
소실되는 것**이 병목이었다.

offline full refinement와의 차이를 좁히려고 camera pose/exposure까지 background Adam으로
갱신하는 cache-safe 경로도 구현했다. `update_pose()`를 `no_grad`에서 commit해 기존
`LinalgInvExBackward` crash는 해결했지만, 1.5× 전체 품질이 **22.15dB**로 붕괴했다.
SLAM이 map 좌표를 계속 바꾸는 동안 photometric camera pose를 별도로 움직이면 geometry
gradient가 잘못 정렬되므로 **online full-scope는 기각**한다.

frame 800 이후에만 Gaussian-safe polishing을 실행하는 late-start도 980 step,
22.16dB로 실패했다. 다만 이 시기 실험들은 최종 Gaussian 수가 64k~80k로 크게 달라지는
mapper 비결정성이 있었으므로 late-start 단독 효과로 과해석하지 않는다. 이후 Python/
NumPy/PyTorch seed를 명시적으로 고정했다.

### 고정 map에서 Gaussian-only dense curve

camera pose/exposure를 완전히 고정한 채 RGB-only dense view 230개와 keyframe을 섞어
Gaussian 파라미터(SH/xyz/opacity/scale/rotation)만 갱신했다.

| step | refinement 시간 | held-out PSNR | keyframe PSNR | held-out Δ |
|---:|---:|---:|---:|---:|
| 0 | 0.00s | 22.99 | 23.30 | — |
| 1,000 | 4.09s | 25.17 | 25.24 | +2.18 |
| 5,000 | **20.25s** | **27.73** | **27.66** | **+4.74** |

이 결과로 pose refinement 없이도 27dB를 넘었다. 이전 full dense curve가 5k에
26.13dB/45.10초였던 것보다 오히려 빠르고 높다. camera optimizer 비용 제거뿐 아니라
seed/run checkpoint 차이가 함께 있으므로 절대 차이를 parameter-scope 효과만으로
해석하지는 않지만, 채택 레시피는 더 안전한 Gaussian-only다.

### 최종 timestamp-paced 1× + tail settle 검증

실제 source timestamp cadence(65.10초)를 그대로 재생하고 background 경쟁 없이
frontier map을 끝까지 안정화한 뒤, 지금까지 도착한 frame만 사용해 dense pose를 채우고
Gaussian-only refinement를 실행했다. evaluator view(`idx%5==0`)와 supervision
view(`idx%5==2`)는 겹치지 않는다.

| 시점 | 누적 계산시간 | live 대비 | held-out PSNR | keyframe PSNR |
|---|---:|---:|---:|---:|
| online map 완료 | 72.49s | 1.114× | 23.66 | 23.93 |
| + dense Gaussian 1k | 76.63s | 1.177× | 25.54 | 25.61 |
| + dense Gaussian 5k | **92.96s** | **1.428×** | **27.87** | **27.82** |

5k 최종 SSIM/LPIPS는 held-out **0.87185 / 0.25555**다. 따라서 exp57의 목표였던
**held-out 약 27dB를 1.5× live budget(97.65초) 안에서 달성**했다. 4.69초의
deadline margin이 남는다.

판정과 제품화 경계:

- **채택**: stable-map boundary + non-eval dense RGB + Gaussian-only 5k settle.
- 이 결과는 실제 Aria 파일을 timestamp대로 공급한 causal replay이며 미래 frame은
  사용하지 않는다. 다만 실제 장치 adapter 자체를 구현한 것은 아니다.
- 유한 녹화가 끝난 뒤 20.5초 정제해 1.428×에 도달한 결과다. 무한 live stream에서
  항상 최신 map이 즉시 27dB인 것은 아니다. 제품화는 완료된 spatial/temporal chunk를
  freeze해 20초 안에 polish하는 rolling double-buffer가 필요하다.
- MPS pose는 녹화 후 처리라 live 의존성으로 쓰지 않는다. 실제 Aria에서는
  Fisheye624+IMU localization이 확정한 chunk pose와 RGB frame을 동일한 dense
  supervision 인터페이스에 넘긴다.

추가 산출물:

- `results/experiments/exp57_causal_dense_20x_eval`
- 실패: `exp57_causal_dense_fullscope_15x_eval`,
  `exp57_causal_dense_late800_15x_eval`
- `results/experiments/exp57_densepolish_gaussian_curve`
- **최종 채택 run**:
  `results/experiments/exp57_paced1x_tail_dense_gaussian`

## 30dB 달성 — dense RGB 4-offset + source별 loss gradient (2026-07-29)

기존 채택안은 non-evaluator dense RGB를 `idx%5==2` 한 offset만 사용해 239장
정도였다. evaluator(`idx%5==0`)를 그대로 제외하면서 **1,2,3,4 네 offset을 전부**
등록하도록 확장해, 실행별 keyframe 중복을 제외한 dense supervision **954~955장**을
사용했다. 새로 추가한 dense supervision set은 evaluator frame과 겹치지 않는다.

핵심은 supervision별 gradient를 **parameter hard-freeze가 아니라 loss source로**
다르게 주는 것이다.

- tracked keyframe: RGB L1+SSIM + BA-refined inverse-depth + normal gradient
- dense non-keyframe: RGB L1+SSIM gradient만 사용
- 두 source 모두 `xyz/scale/rotation/opacity/color(SH)` 전체 Gaussian parameter에
  gradient가 도달. camera pose/exposure는 고정, densification/pruning 없음.

즉 dense frame에는 불확실한 보간 depth/normal을 만들지 않고 photometric
multi-view consistency만 주되, 그 photometric gradient가 geometry까지 움직이는 것은
허용한다.

### 최종 성공 곡선

실제 timestamp-paced 1× online map이 끝난 stable-map boundary에서, evaluator와
분리된 dense 954장 + tracked keyframe으로 Gaussian-only refinement를 연속 실행했다.
held-out trajectory는 모든 milestone에서 polishing 전 online trajectory로 고정했다.

| step | refinement | held-out PSNR | keyframe PSNR | SSIM | LPIPS |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.00s | 24.034 | 24.486 | 0.77758 | 0.45602 |
| 5k | 20.67s | 28.236 | 28.109 | 0.88233 | 0.23533 |
| 10k | 41.55s | 29.618 | 29.404 | 0.89959 | 0.19814 |
| **15k** | **62.83s** | **30.389** | **30.321** | **0.90604** | **0.18437** |
| 20k | 84.24s | 30.505 | 30.428 | 0.90811 | 0.17858 |

**held-out와 keyframe 모두 30dB를 넘었다.** 15k→20k는 21.42초를 더 쓰고
held-out +0.116dB뿐이므로 최소 채택점은 **15k**다. 이 run의 online loop는
75.45초, 따라서 15k까지 계산 합은 **138.28초 = 65.1초 live의 2.124×**다.
품질 목표 30dB는 달성했지만 아직 1.5× 또는 true-real-time은 아니다.

### supervision별 parameter gradient 대조군

같은 dense 4-offset 위에서 “각 supervision이 어떤 parameter를 움직여야 하는가”를
분리해 측정했다.

| 변형 | routing | 최종 held-out | 판정 |
|---|---|---:|---|
| hard split | 0~5k all; 이후 dense→color/opacity, keyframe depth/normal→geometry only | 5k 28.271 → 7.5k 25.667 → 10k **25.042** | depth-only geometry가 RGB map 파괴 |
| soft split | 0~5k all; 이후 dense→color/opacity, keyframe RGB+depth+normal→all | 10k 28.356, 15k **28.830** | 안전하지만 30dB 미달 |
| soft+exposure | soft split + 선택된 view exposure만 최적화, pose 고정 | 15k 28.133, 20k **28.229**(kf 29.361) | training-view exposure 과적합 |
| **loss-source split + all Gaussian** | keyframe RGB+depth+normal, dense RGB-only; parameter는 둘 다 all | 10k 29.618, 15k **30.389** | **채택** |

첫 exposure 구현은 1,066개 camera parameter group을 한 Adam에서 매번 순회해
230→59 iter/s로 느려지는 구현 병목이 있어 7.3k에서 중단했다. 선택된 camera의
`exposure_a/b` 두 값만 가진 optimizer를 view별 캐시하도록 고친 뒤 230~250
iter/s를 회복해 위 최종 exposure 대조군을 얻었다. 품질은 기각.

### 결론

- **supervision마다 loss modality는 달라야 한다**: dense RGB에 가짜 depth/normal을
  붙이지 않고, tracked keyframe에만 BA geometry prior를 준다.
- 그러나 **parameter를 source별로 hard 분리하면 안 된다**. Dense multi-view
  photometric gradient가 Gaussian geometry까지 도달해야 held-out 30dB가 된다.
- frame 수 증가는 iteration당 연산량을 늘리지 않는다(한 step에 view 하나 샘플).
  품질 이득은 239→954장 coverage 증가에서 왔다.
- 다음 속도 목표는 새 15k recipe를 바꾸는 것이 아니라, 완료 chunk rolling
  double-buffer와 exp58 CUDA backward 최적화로 62.83초 refinement를 숨기거나
  압축하는 것.

최종 산출물:

- `results/experiments/exp57_dense4_gaussian20k`
- 대조군: `exp57_dense4_staged10k`, `exp57_dense4_softstaged15k`,
  `exp57_dense4_exposure20k_fast`

## Aria 흑백 geometry-only / RGB appearance-only + carve-prune (2026-07-29)

사용자 제안대로 실제 Aria SLAM 좌·우 흑백 카메라를 추가 supervision으로 연결했다.
VRS factory calibration에서 Fisheye624 내·외부 파라미터를 읽어 464×464 pinhole
(f=232)로 rectification하고, RGB timestamp와 가장 가까운 cam0/cam1 frame을 매칭했다.
좌·우 각 261장, 총 522장이며 RGB와의 절대 timestamp 차이는 평균 **0.079ms**,
최대 **0.089ms**다. `T_gray_world = inv(T_device_gray) @ T_device_rgb @
T_rgb_world`로 VIGS의 RGB trajectory에 붙였다. 생성기는
`scripts/incremental/build_exp57_gray_supervision.py`.

학습 scope `sensor_split`을 구현했다.

- 흑백 step: luminance를 평균 0/RMS 1로 정규화한 photometric loss, Gaussian
  `xyz/scaling/rotation`만 gradient 허용. SH/color/opacity와 camera pose/exposure는
  차단.
- RGB step: 기존 L1+SSIM, `f_dc/f_rest/opacity`만 허용. geometry와 camera는 차단.
- 흑백 zero-support view의 0-분산 미분 NaN은 epsilon-inside-sqrt 정규화와
  non-finite step skip으로 방어. 전체 run에서는 skip 0회.

### A. 단순 sensor split 50:50 — 실패

5k 중 절반을 gray geometry, 절반을 RGB appearance/opacity에 배분했다.

| step | held-out PSNR | keyframe PSNR | refinement |
|---:|---:|---:|---:|
| 0 | 24.005 | 24.466 | 0s |
| 1k | 21.525 | 21.579 | 3.87s |
| 5k | **20.771** | **20.838** | 20.51s |

흑백의 cross-sensor photometric 오차를 색으로 설명하지 못하게 막자 Adam이 이를
geometry 이동으로 전부 설명해 mature RGB map을 훼손했다. 기존 exp57 채택값
27.87dB보다 −7.10dB이므로 즉시 기각.

### B. 제한형: gray 10% + geometry trust region — 안전해졌지만 실패

gray 비율을 10%(약 500 step)로 줄이고, refinement 시작 geometry에서
`xyz ±5mm`, raw log-scale/quaternion parameter `±0.02`를 넘지 못하게 제한했다.

| step | held-out PSNR | keyframe PSNR | refinement |
|---:|---:|---:|---:|
| 0 | 24.025 | 24.510 | 0s |
| 1k | 24.557 | 24.856 | 4.03s |
| 5k | **24.829** | **25.097** | 19.66s |

무제한안의 붕괴는 막았지만 기존 exp57 Gaussian-only 5k
**27.869/27.818dB**보다 held-out −3.04dB. RGB geometry를 잠근 손실을 제한된
gray geometry가 대체하지 못한다. online loop 76.05s + refinement 19.66s =
**95.72s, 1.470× live**로 시간은 1.5× 안이지만 품질 기준으로 기각.

### C. opacity-independent carve evidence 상위 5% prune — 실패

사용자 요청대로 opacity를 낮추는 loss나 opacity threshold를 쓰지 않고, 현재까지
도착한 RGB keyframe 146개와 BA depth anchor 20,244개로 transit/terminal voxel
evidence를 누적했다. score는 `rho * min(d5(anchor)/0.25, 1)`이며 opacity는 계산과
선택 어디에도 쓰지 않았다. score>0.3 중 상위 5%만 보수적으로 제거했다.

| 상태 | Gaussian | held-out PSNR | keyframe PSNR |
|---|---:|---:|---:|
| sensor-split 5k | 80,205 | 24.722 | 24.987 |
| + carve-score prune | **76,195** | **22.301** | **22.550** |

4,010개(5%) 제거로 held-out **−2.42dB**. score 계산+prune도 6.61s가 추가되어
online 75.53s + refinement 18.88s + carve 6.61s = **101.02s,
1.552× live**로 deadline도 실패했다. 첫 carve 실행은 intrinsics GPU tensor를
NumPy와 곱한 타입 버그로 pruning 직전에 실패했고, float 변환 수정 후 별도 전체
retry에서 위 결과를 얻었다.

### 판정

- **세 변형 모두 기각**, exp57 기존 채택 레시피(27.87dB@1.428×) 유지.
- 흑백 추가 시점 자체는 정확히 동기화·보정됐지만, “gray photometric
  geometry-only”는 appearance mismatch와 occlusion을 geometry error로 오인한다.
- 다음에 흑백을 다시 쓰려면 photometric loss가 아니라 **좌·우 stereo로 얻은
  metric depth/epipolar correspondence를 geometry constraint로 변환**해야 한다.
  RGB geometry를 완전히 잠그는 hard split도 재검토해야 한다.
- 현재 depth-anchor carve score는 진단용으로는 유효해도 hard prune selector로는
  specificity가 부족하다. prune 전 region GT 검증 또는 multi-view contribution
  보호항이 선결 조건이다.

산출물:

- `results/experiments/exp57_gray_sensor_split_5k`
- `results/experiments/exp57_gray_trust_5k`
- `results/experiments/exp57_gray_carveprune_retry`

## 문제 정의

현재 `map()`은 서로 목적이 다른 두 작업을 같은 iteration 예산에서 수행한다.

1. **Frontier fitting**: 방금 들어온 keyframe과 신규 gaussian을 빠르게 정착시킴.
2. **Global polishing**: 과거 지도의 색·opacity·geometry를 다시 다듬음.

exp56 Phase 6에서 window를 키우고 iters를 줄였을 때 PSNR이 최대 3.6dB 무너졌다.
프론티어가 과거 keyframe과 제한된 gradient 예산을 경쟁했기 때문이다. 반면 Phase 7은
window를 그대로 두고 global view만 2→6개로 늘려 PSNR을 개선했다. 즉 global replay는
유효하지만 **프론티어 update와 같은 예산을 경쟁시키지 않는 구조**가 필요하다.

또한 종료 후 26k-iteration 색정제가 keyframe PSNR을 약 6.5dB, held-out을 약 3dB 올린다.
이는 온라인 상태에 아직 큰 최적화 여지가 있음을 보여주지만, 현재처럼 세션 종료 뒤
196초가량 블로킹하는 구조는 실시간이 아니다.

## 핵심 가설

### H1. 프론티어와 전역 정제를 분리하면 coverage 손실 없이 품질을 올릴 수 있다

- `frontier update`: 최근 window 중심. RGB+depth+normal을 사용하고
  xyz/scale/opacity/SH 전체를 갱신한다.
- `background polish`: frontier queue가 비어 있을 때만 실행한다. 과거 view를 대상으로
  우선 SH/color만 갱신하고, 검증 후 opacity와 제한적 geometry를 단계적으로 연다.
- 새 tracking/keyframe packet이 도착하면 polishing은 즉시 양보한다.
- 도착한 keyframe만 사용하므로 미래 정보가 없는 causal order를 유지한다.

### H2. 같은 6개 global view라도 랜덤보다 정보량 기반 선택이 iteration 효율이 높다

각 keyframe에 다음 온라인 통계를 유지한다.

- 마지막 선택 시점과 누적 선택 횟수
- 최근 robust RGB/depth residual
- 저관측 gaussian 비율 또는 coverage deficit
- 현재 frontier와의 baseline/view-direction novelty
- depth/normal confidence

후보 score:

```text
view_score =
    robust_residual
  × coverage_need
  × viewpoint_novelty
  × staleness
  × geometry_confidence
```

specular/glare가 큰 뷰가 residual만으로 독점되지 않도록 residual clipping과
depth/normal confidence gate를 둔다. `n_global_views=6`, `window_size=10`,
frontier `iters=7`은 고정하여 순수 selection 효과를 격리한다.

### H3. 전역 polishing은 제한된 파라미터부터 열면 더 싸고 안전하다

단계별 parameter scope:

1. SH/color only
2. SH/color + exposure(가능한 경우)
3. + opacity
4. confidence가 높은 surface gaussian에 한해 작은 xyz/scale update

densification과 신규 gaussian 생성은 frontier에서만 허용한다. 이 분리는 과거 지도의
재증식과 floater 재발을 막으면서 backward graph와 optimizer 비용도 줄일 수 있다.

## Phase 0 — 오프라인 polishing 압축 곡선

온라인 통합 전에 exp56 최종 온라인 checkpoint 하나를 고정하고, 동일 view sampler와
동일 평가 하네스로 polishing iteration에 따른 품질/시간 곡선을 측정한다.

| polishing iterations | 목적 |
|---:|---|
| 0 | exp56 기준선 |
| 250 | 초기 상승률 |
| 500 | 실시간 여유 내 후보 |
| 1,000 | 수확체감 확인 |
| 2,000 | 온라인 분산 상한 후보 |
| 5,000 | 26k와의 잔여 격차 확인 |
| 26,000 | 기존 오프라인 상한 참조 |

각 지점에서 다음을 기록한다.

- held-out llffhold-8 PSNR/SSIM/LPIPS
- keyframe PSNR
- exp55 VIGS carve 진단 지표와 시각 검사
- 순수 GPU 시간 및 iteration당 시간
- gaussian 수와 parameter별 update norm

**판정**:

- 초반 500~2k에서 held-out이 의미 있게 상승하면 Phase 1로 진행.
- keyframe만 오르고 held-out이 거의 안 오르면 색 암기 위험으로 판정하고,
  view selection/geometry consistency를 먼저 강화한다.
- 5k까지 held-out 상승이 작으면 background color polish를 주력으로 채택하지 않고
  depth/normal confidence 및 init geometry 개선으로 방향을 전환한다.

## Phase 1 — Causal background polishing scheduler

별도 저우선순위 polish queue를 추가한다.

```text
tracking/frontier packet 도착
    -> frontier update 우선 수행
    -> 대기 packet이 없고 시간 budget이 남으면 polish 1~K step
    -> 새 packet 도착 시 polish 양보
```

필수 계측:

- frontier map() 성사 횟수와 queue drop 수
- polish step 수 및 중단 횟수
- tracking/mapping/polishing GPU 시간
- 시퀀스 시점별 held-out/keyframe PSNR
- 실시간 배수

첫 구현은 SH/color-only, random global view로 단순화하여 scheduler 자체 효과를 격리한다.

## Phase 2 — 정보량 기반 global replay

Phase 1 scheduler 위에서 sampler만 변경한다.

| 축 | sampler | 계산 예산 |
|---|---|---|
| A0 | random 6 | 기준 |
| A1 | residual + staleness | 동일 |
| A2 | + coverage need | 동일 |
| A3 | + viewpoint novelty + confidence gate | 동일 |

선택 score 계산 자체가 새 GPU launch 병목이 되지 않도록 통계는 각 view가 실제로 렌더된
시점에 갱신하고, 선택은 CPU의 작은 keyframe table에서 수행한다.

## Phase 3 — Parameter scope 확장

Phase 0~2에서 held-out 상승이 확인된 뒤에만 SH/color-only에서 범위를 확장한다.

| 축 | 갱신 파라미터 | 위험 |
|---|---|---|
| B0 | SH/color only | 가장 낮음 |
| B1 | + opacity | 먼지 재배분 가능 |
| B2 | + confidence-gated xyz/scale | geometry 개선 가능, floater 위험 |

B2는 depth/normal confidence가 높은 visible gaussian에만 작은 LR로 적용한다.
densification, clone, split은 계속 금지한다.

## Phase 4 — 남는 시간의 연산 최적화

알고리즘 축이 실제 held-out 개선을 만든 뒤 polish step 수를 늘리기 위해 다음을 검토한다.

1. 여러 view의 L1/depth/normal loss batch/fusion
2. normal loss를 frontier 또는 주기적 step에만 계산하는 절제
3. polish 전용 optimizer/parameter subset으로 backward graph 축소
4. 이후 [exp58](exp58_cuda_visibility_backward_plan.md)의 CUDA 내부 visibility skip

`BACKWARD::preprocess` 배치화는 품질 레버가 아니라 같은 update를 싸게 만드는 후속
가속 레버로 취급한다.

## 성공 기준

1차 목표:

- strict streaming held-out PSNR **27dB 이상**
- timestamp 순 Aria RGB photo+IMU only, MPS 후처리 입력 **0개**
- fixed **1.5× live budget 이내**
- 마지막 frame 뒤 optimizer update **0회**
- keyframe PSNR만 상승하고 held-out이 정체하는 과적합이 아닐 것
- 인과 순서를 지키고 미래 keyframe 정보를 사용하지 않을 것

27dB 달성 후:

- carve loss/floater 억제를 이식해 held-out PSNR과 region GT를 함께 검증
- 동일 strict 조건에서 held-out **30dB+**로 확장

## 실패 시 해석

- polish step은 늘었지만 held-out 무효 → 색 암기. geometry/init 신호가 병목.
- random은 무효, 정보량 sampler만 유효 → gradient 품질/분산이 병목.
- sampler도 무효 → view 수가 아니라 depth/normal target 품질 또는 표현력이 병목.
- 품질은 오르나 실시간 실패 → exp58/loss fusion으로 동일 update를 가속.

## 2026-07-29 추가 — Aria photo+IMU 전용 strict 1.5× 검증

### 입력 계약

사용자 지시에 따라 `--strict_aria_online`을 추가하고 다음을 실행 시 강제했다.

- 입력: `data/aria1253/rgb`의 timestamp 순 Aria RGB photo 1,303장 +
  `data/aria1253/imu.txt`의 IMU만 허용.
- `--pure_online --realtime_replay --replay_time_scale 1.5` 필수.
- 경로에 `mps`가 있거나 gray manifest/external carve anchor/tail
  `--polish_milestones`가 있으면 즉시 거부.
- provenance를 `input_provenance.json`에 기록. 최종 결과의 `mps_inputs=[]`,
  `post_stream_refinement=false`.
- PPM init(`Dataset.ppm_sampling=true`)과 soft carve
  (`Training.carve_lambda=0.05`)는 현재까지 도착한 RGB와 VIGS가 온라인으로 추정한
  depth/pose만 사용한다. hard carve pruning은 앞선 고품질 전 검증에서 PSNR을
  크게 훼손했으므로 이번 strict run에는 넣지 않았다.

### 구현 중 발견·수정한 문제

1. background optimizer가 `step()` 뒤 LR schedule을 바꾸고 그 LR을 다음 frontier
   update에 누출하던 순서 오류를 수정했다. polish step에만 전용 xyz LR을 적용한 뒤
   모든 group LR을 복원한다.
2. causal dense Camera가 모든 RGB를 GPU에 영구 cache하여 약 400장 시점 PGBA의
   986MiB correlation allocation과 충돌했다. dense RGB는 CPU에 두고 선택된 view만
   step 동안 전송하도록 바꿔 OOM 없이 완주했다.
3. 서비스 조건처럼 모델은 replay clock 전에 prewarm한다. 첫 사진에서는 알려진
   tensor 크기만 읽으며 supervision/update는 하지 않는다.
4. `--eval_online_final`은 online timer와 immutable map 저장 뒤 held-out을 render만
   하고 optimizer update는 0회 수행한다.

### 기각한 압축 보조축

| 축 | held-out curve | 순수 refinement 시간 | 판정 |
|---|---|---:|---|
| batch=4, full-res | 1k 26.588 → 5k 29.659 | 5k 62.90s | optimizer step 수가 중요, 기각 |
| 모든 Gaussian LR×2 | 2.5k 26.410 → 10k 28.480 | 10k 48.12s | 수렴/안정성 악화, 기각 |
| 5k half-res + 5k full | 2.5k 27.135, 5k 28.243, 10k 29.582 | 10k 52.05s | preprocess가 N 지배, full-res보다 느려 기각 |

### strict 1.5× 최종 결과

결과 디렉터리:
`results/experiments/exp57_strict15x_mature700_lag150_eval`

- scheduler: frame 700부터, 최신 frame 대비 150-frame 이상 지난 arrived-only view,
  non-evaluator RGB offsets `{1,2,3,4}`, fixed camera Gaussian update.
- causal background: **1,441 optimizer steps / 1,441 view updates**.
- held-out/keyframe: **23.870 / 24.300dB**, SSIM **0.77247**,
  LPIPS **0.47240**.
- Gaussian: **66,214개**.
- online: **102.129s** = 원본 65.10s의 **1.569×**. 1.5× input deadline
  97.65s보다 **4.48s 초과**.
- 동일 online-depth-anchor 기반 post-hoc carve 진단(학습 입력 아님):
  visible floater **13,611 / 62,918 = 21.633%**. 30dB offline map은
  **14,112 / 64,148 = 21.999%**라 비율 차이는 −0.37%p뿐이며, strict map의
  Gaussian 자체가 더 적어 절대 개수 감소를 floater 개선으로 해석하면 안 된다.

**결론: 실패.** 1.5× paced 입력 중 map이 성숙한 뒤 update를 시작하고 stability lag를
줘도 1,441회만 흡수됐고, held-out은 앞선 1.5× causal 결과 24.227dB보다도
0.36dB 낮다. 고정 완성 map에서는 15k가 30.389dB를 만들지만, 성장 중인 map에
분산된 update는 이후 densification/PGBA/재초기화로 효력이 소실된다. 따라서
`rolling polish`만으로 pure-online 30dB를 주장할 수 없다. 다음 유효 방향은
완료 공간 chunk를 freeze한 뒤 별도 map state에서 polish하고 merge하는
double-buffer streaming이며, 이 역시 입력은 photo+IMU와 online pose/depth로
제한해야 한다.

## 2026-07-29 추가 — completed-lineage same-tensor freeze 검증

앞 절의 double-buffer 가설에서 가장 작은 구현인 **동일 Gaussian tensor 안의
lineage freeze**를 먼저 검증했다.

### 구현

- clone/split 뒤에도 보존되는 `unique_kfIDs`를 Gaussian의 출생 lineage로 사용.
- 최신 frame보다 150 frame 이상 지난 lineage를 completed로 전환.
- completed lineage는 frontier Adam의 gradient와 momentum을 제거하고,
  frontier densify/prune/cap에서 보호.
- background polishing은 frontier와 optimizer state를 공유하지 않는 별도 Adam으로
  completed lineage만 갱신.
- frame 700 이후 도착 완료된 non-evaluator dense RGB view만 사용.
- 입력 계약은 계속 strict: timestamp 순 RGB photo 1,303장 + IMU만 사용,
  `mps_inputs=[]`, 종료 후 refinement 없음.

200-frame smoke에서 completed-lineage 경로가 20 step 실제 실행되고 정상 종료된 뒤
전체 1.5× replay를 실행했다.

| strict 1.5× | 이전 rolling baseline | completed-lineage freeze | 변화 |
|---|---:|---:|---:|
| background step | 1,441 | **1,237** | −204 |
| held-out PSNR | 23.870 | **18.004** | **−5.866dB** |
| keyframe PSNR | 24.300 | **18.071** | **−6.229dB** |
| held-out SSIM / LPIPS | 0.77247 / 0.47240 | **0.64835 / 0.66563** | 모두 악화 |
| Gaussian | 66,214 | **96,757** | **+46.1%** |
| online loop | 102.129s | **102.391s** | +0.262s |
| 원본 65.10s 대비 | 1.569× | **1.573×** | 1.5× deadline 4.74s 초과 |

동일 online-depth anchor를 재사용한 **post-hoc 진단만** 수행했다. 이 anchor는 학습에
사용하지 않았으며 MPS 데이터가 아니다.

| map | visible floater | visible floater 비율 |
|---|---:|---:|
| 이전 strict rolling | 13,611 / 62,918 | 21.633% |
| completed-lineage freeze | **22,556 / 81,020** | **27.840%** |
| 고정-map 30dB 참조 | 14,112 / 64,148 | 21.999% |

**판정: 강한 기각.** 별도 Adam으로 momentum overwrite는 막았지만, 같은 tensor에서
completed lineage를 frontier prune/cap으로부터 영구 보호하자 초기 저품질 Gaussian도
함께 고정되어 Gaussian 수와 floater가 누적됐다. 동시에 과거 lineage만 갱신하는
background gradient는 전체 장면의 가시성 결합을 보존하지 못해 PSNR이 5.87dB
붕괴했다. 따라서 “lineage mask만 둔 same-tensor double-buffer”는 폐기한다.
다음 시도는 완료 영역을 **별도 Gaussian model/checkpoint**로 떼어 독립적으로
polish한 뒤, overlap 검증과 중복 제거를 거쳐 render/merge하는 진짜 spatial chunk
구조여야 한다. 그 경우에도 입력은 도착한 Aria photo+IMU와 VIGS online pose/depth로만
제한한다.

## 2026-07-29 정정 — lineage cutoff 단위 버그 및 유효 재실험

위의 18.004dB 결과를 사후 감사한 결과, completed cutoff의 단위가 잘못된 것을
발견했다. `unique_kfIDs`는 sensor timestamp가 아니라 replay frame index
(`video.tstamp`: 0, 4, 11, ...)인데, 최초 구현은 cutoff에 sensor timestamp를
전달했다. 따라서 frame 700에서 모든 Gaussian을 한꺼번에 completed로 오판했다.
위 18.004dB run은 **구현 버그가 든 무효 결과**이며 same-tensor freeze의 성능
근거로 쓰지 않는다.

단위를 frame index로 통일하고, opacity reset 및 최종 scale clamp 같은 optimizer
밖의 직접 write도 completed mask를 지키도록 수정했다. smoke test에서
`frozen=22,891/27,838, cutoff=104`로 일부 lineage만 동결되는 것을 확인한 뒤
전체 strict 1.5× replay를 다시 수행했다.

| strict 1.5× | rolling baseline | 단위 수정 freeze | freeze + prune/carve |
|---|---:|---:|---:|
| background step | 1,441 | 1,190 | **1,227** |
| held-out PSNR | **23.870** | 22.002 | **21.868** |
| keyframe PSNR | **24.300** | 22.216 | **22.066** |
| held-out SSIM / LPIPS | **0.77247 / 0.47240** | 0.74379 / 0.50336 | **0.73490 / 0.51561** |
| Gaussian | 66,214 | 77,799 | **57,109** |
| online loop | 102.129s | 102.505s | **약 103.77s** |
| 원본 65.10s 대비 | 1.569× | 1.575× | **약 1.594×** |

`freeze + prune/carve`에서는 completed lineage의 gradient/momentum/densification은
막되, 저 opacity/과대 scale Gaussian을 영구 보존하지 않도록 opacity/size prune과
per-lineage cap은 허용했다. background RGBD loss에는 현재 RGB 및 VIGS online
tracked depth만 쓰는 depth-violation carve(`lambda=0.05`)를 적용했다. 그 결과
Gaussian 누적은 억제됐지만 held-out은 baseline보다 **−2.002dB** 낮았다.

동일 online-depth anchor를 쓴 post-hoc 진단(평가 전용, 학습 미사용):

| map | visible floater | visible floater 비율 |
|---|---:|---:|
| rolling baseline | 13,611 / 62,918 | 21.633% |
| freeze + prune/carve | **11,609 / 55,061** | **21.084%** |
| 고정-map 30dB 참조 | 14,112 / 64,148 | 21.999% |

floater 비율은 −0.549%p만 줄고 PSNR은 2.002dB 손실되어 품질 대비 이득이 없다.
따라서 **버그를 고친 유효 실험으로도 same-tensor completed-lineage freeze는
기각**한다. 단, 원인은 이전 기록의 “모든 초기 Gaussian 영구 보호”만이 아니다.
prune/cap을 다시 허용해 Gaussian 수를 baseline 아래로 낮춰도 품질이 회복되지
않았으므로, 성장 중 단일 visibility/compositing 표현에서 일부 lineage만 고정하는
구조 자체가 dense RGB gradient의 전역 결합을 깨는 것이 더 직접적인 원인이다.

입력 provenance는 세 run 모두 `policy=strict_aria_rgb_imu_only`,
`mps_inputs=[]`, `post_stream_refinement=false`이다. 학습 입력은 timestamp 순
Aria RGB photo와 IMU, 그리고 그 시점까지 VIGS가 online 추정한 pose/depth뿐이다.
MPS 후처리 데이터는 사용하지 않았고 앞으로의 exp57 pure-online 실험에서도
금지한다.

## 2026-07-29 추가 — 30dB update 실행비 압축 진단

입력 계약은 계속 동일하다. 아래 replay의 센서 입력은 timestamp 순 Aria RGB
photo 1,303장과 IMU뿐이며 MPS 후처리 데이터는 0개다. 다만 종료 후 fixed-map
polishing을 붙인 **속도/수렴 상한 진단**이므로 strict pure-online 성공 결과로
간주하지 않는다.

### CUDA-native visible subset

기존 `render_filtered()`가 만든 PyTorch advanced indexing 5개와 그 backward
scatter를 없애기 위해, full Gaussian tensor와 `active_indices`를 rasterizer에
직접 전달하도록 forward/backward CUDA preprocess를 확장했다.

- all-visible forward/radii: bit-exact
- L1+depth gradient 상대오차: xyz 1.15e-6, opacity 8.8e-8, scaling 1.2e-6,
  rotation 3.7e-6, feature 1.5e-7
- 90,770 GS, 1024px end-to-end: full 3.1696ms/update,
  cached subset 3.1047ms/update = **2.05% 개선**
- 매번 mask를 다시 계산하면 3.3058ms로 **4.3% 악화**

수치적으로는 유효한 opt-in 자산이지만 15k update를 실시간 예산으로 압축할 레버는
아니므로 전체 strict replay에는 투입하지 않았다.

### 동일 수학 polishing loop 정리

`color_refinement(batch_size=1)`이 같은 RGB/RGBD/normal loss graph를 두 번 만들고
첫 graph를 버리던 중복 계산을 제거했다. 이어 검증된 finite RGB dense view에 한해
`--polish_fast_loop` 옵션으로 매 update의 `cuda.synchronize()`, finite-loss host
branch, `loss.item()` 진행률 동기화를 제거하고 milestone에서만 동기화했다.

| 진단 | 5k held-out | 10k held-out | 15k held-out | refinement 시간 |
|---|---:|---:|---:|---:|
| 중복 loss 제거 | 28.345 | 29.582 | **30.321** | 20.95 / 42.01 / 63.53s |
| + fast loop | **28.325** | - | - | **19.30s @5k** |

중복 loss 제거 run은 15k에서 30dB를 재현했지만 기존 62.83s와 사실상 같았다.
fast loop는 5k 시간을 **7.9%** 줄이고 품질을 유지했으나, 선형 외삽한 15k도 약
58초라 strict 1.5×의 약 22초 여유에는 들어가지 않는다. 결론은 커널 launch/host
동기화 미세 최적화만으로 부족하며, 5k 부근에서 30dB에 도달하도록 update 수를
압축하거나 별도 spatial chunk를 stream 중 독립 수렴시키는 구조가 필요하다는 것이다.

산출물:

- `results/experiments/exp57_dense4_15k_nodup_loss_v2`
- `results/experiments/exp57_dense4_5k_fastloop`
- `scripts/analysis/exp57_cuda_subset_bench.py`

## 2026-07-29 추가 — independent snapshot/double-buffer 실측

### 입력 계약

이 절의 모든 실행은 **pure online**이다. replay가 timestamp 순서로 전달하는
Aria RGB photo 1,303장과 IMU만 센서 입력으로 사용했다. 고정 factory calibration은
허용하지만, 학습 pose/depth는 해당 시점까지 VIGS가 online으로 만든 값만 사용한다.
MPS trajectory/depth/point cloud 등 후처리 산출물은 절대 사용하지 않았고 provenance도
`policy=strict_aria_rgb_imu_only`, `mps_inputs=[]`,
`post_stream_refinement=false`로 기록됐다. 종료 후 online-depth anchor는 평가용
진단에만 허용하며 학습에는 넣지 않는다.

### 구현

- frontier와 optimizer state를 전혀 공유하지 않는 Gaussian snapshot 및 별도 Adam.
- clone/split/prune에도 유지되는 stable point ID로 100 frame마다 최신 frontier
  구조를 rebase.
- PGBA 뒤에는 도착한 dense RGB camera pose를 최신 causal keyframe pose 사이에서
  다시 보간.
- 종료 경계에서 snapshot을 publish하고 이후 optimizer update는 0회.
- rebase 시 보존 범위를 `all`과 `appearance`로 분리. `appearance`는 SH feature만
  보존하고 xyz/opacity/scale/rotation은 최신 frontier 값을 사용.

800-frame 1.5× smoke에서 fast loop는 snapshot update를 1,351→2,171회
(+60.7%) 늘렸고 stable-ID refresh/merge 및 PGBA dense-pose refresh가 정상 동작했다.

### strict 1.5× 전체 결과

| 변형 | snapshot update | held-out / kf PSNR | GS | online | 판정 |
|---|---:|---:|---:|---:|---|
| 초기 snapshot 고정 | 3,901 | 20.030 / 20.102 | 73,021 | 102.59s | late densification 누락, 기각 |
| 100f rebase, all 보존 | 3,919 | 21.625 / 21.810 | 72,356 | 102.60s | stale pose/geometry drift, 기각 |
| + causal dense-pose refresh, all | 3,921 | 20.926 / 21.136 | 71,179 | 약 103s | pose 보정으로도 회복 안 됨 |
| 100f rebase, **appearance만 보존** | **3,951** | **23.551 / 23.933** | **73,107** | **103.911s (1.596×)** | baseline보다 −0.319dB, 기각 |
| rolling baseline | 1,441 | **23.870 / 24.300** | 66,214 | **102.129s (1.569×)** | 비교 기준 |

appearance-only가 all-parameter 이식보다 +2.625dB 회복한 것은 오래 polish한
geometry를 성장 중인 최신 visibility field에 이식하는 것이 주된 붕괴 원인임을
보인다. 그러나 가장 좋은 snapshot도 rolling baseline보다 held-out −0.319dB이고
1.5× deadline 97.65초를 6.26초 넘었다. 따라서 **full-scene independent snapshot
double-buffer도 기각**한다. 다음 품질 축은 별도 snapshot update를 늘리는 것이
아니라, frontier가 실제로 소비하는 arrived RGB supervision의 coverage/정보량을
높이면서 동일 frame에 대한 중복 update를 압축하는 방향이어야 한다. 고품질 map이
아니므로 hard carve pruning은 아직 적용하지 않는다.

산출물:

- `results/experiments/exp57_snapshot_strict15x_start500_fast`
- `results/experiments/exp57_snapshot_rebase100_strict15x`
- `results/experiments/exp57_snapshot_rebase100_densepose_strict15x`
- `results/experiments/exp57_snapshot_appearance_rebase100_strict15x`

## 2026-07-29 추가 — frontier fast rolling update 밀도 A/B

snapshot 실패의 원인이 merge/rebase인지, update 수 부족인지 분리하기 위해 같은
low-latency loop를 최신 frontier에 직접 적용했다. validated RGB view에서 매 step
`torch.isfinite()` host synchronization을 생략하고 queue poll을 2ms→0.2ms로
줄였다. 입력은 계속 timestamp 순 Aria RGB+IMU only이고 MPS는 0개다.

300-frame smoke에서 913 update가 실제 실행되어 배선을 확인한 뒤, rolling baseline과
동일한 frame 700 시작, 150-frame stability lag, dense RGB offsets `{1,2,3,4}`,
Gaussian-full/camera-fixed 조건으로 전체 strict 1.5×를 실행했다.

| strict 1.5× | 기존 rolling | fast rolling | 변화 |
|---|---:|---:|---:|
| update | 1,441 | **2,088** | **+44.9%** |
| held-out PSNR | **23.870** | 23.728 | **−0.142dB** |
| keyframe PSNR | **24.300** | 24.170 | −0.130dB |
| SSIM / LPIPS | 0.77247 / 0.47240 | 0.76897 / 0.47094 | 혼재 |
| Gaussian | 66,214 | 67,554 | +1,340 |
| online | 102.129s (1.569×) | **103.212s (1.585×)** | deadline 초과 확대 |

**기각.** host synchronization을 줄여 update 수는 크게 늘었지만 품질은 오히려
소폭 낮아졌다. growing frontier에 round-robin update를 더 많이 넣는 것 자체는
30dB 방향이 아니다. 다음은 동일 update 예산에서 arrived RGB의 residual, coverage,
viewpoint novelty, staleness를 이용해 supervision 선택 품질을 높이는 축이다.

산출물:

- `results/experiments/exp57_frontier_fast_smoke300_enabled`
- `results/experiments/exp57_frontier_fast_strict15x`

## 2026-07-29 추가 — strict 27dB milestone 전환 및 coverage/예산 재배분

사용자 결정으로 pure-online의 1차 성공 기준을 held-out 30dB에서 **27dB**로
조정했다. 계약은 MPS 없이 timestamp 순 Aria RGB photo+IMU only, fixed 1.5×,
마지막 frame 이후 optimizer update 0회로 동일하다. 27dB 이전에는 low-quality map에
hard carve pruning을 섞지 않고 PSNR 원인을 먼저 해결한다.

### causal dense interval 누락 수정

기존 scheduler는 frontend 호출마다 마지막 keyframe 쌍 하나만 처리했다. 한 호출
사이에 여러 keyframe 상태가 갱신되거나 buffer가 변하면 중간 구간이 영구 누락되어,
non-evaluator dense 후보 약 954장 중 실제 등록은 450장뿐이었다. 도착한 keyframe의
모든 unseen 인접 구간을 한 번씩 순회하도록 수정했다. 어떤 dense frame도 양쪽
keyframe이 이미 도착하기 전에는 등록하지 않아 causal order는 유지된다.

300-frame smoke에서 등록 수가 **114→213장(1.87×)**으로 증가했다. 전체 strict
1.5×에서는 **450→931장**으로 회복했다.

| strict 1.5× | 기존 rolling | 모든 causal interval |
|---|---:|---:|
| dense RGB | 450 | **931** |
| update | 1,441 | 1,361 |
| held-out / kf PSNR | 23.870 / 24.300 | **23.982 / 24.402** |
| SSIM / LPIPS | 0.77247 / 0.47240 | **0.77262 / 0.46679** |
| Gaussian | 66,214 | 67,961 |
| online | 102.129s | **104.752s (1.609×)** |

coverage 수정은 held-out **+0.112dB**, LPIPS 개선으로 유효하지만 27dB에는 크게
부족하다. PGBA마다 931개 dense pose를 갱신하는 비용이 추가돼 시간은 악화했다.
동일 SE(3) 보간을 keyframe interval별 batch로 바꿔 CPU 왕복을 2×dense에서
1×keyframe으로 줄였으며 이후 run에서 약 3초를 회수했다.

### late frontier 반복 → mature dense update 재배분

frame 700 이후 일반 frontier `map()` 반복을 7→2로 줄이고 fast rolling에 예산을
넘겼다. dense 931장을 유지한 채 update는 **4,215회**로 증가했고 online도
**101.801s**로 줄었지만 held-out/keyframe은 **24.113/24.479dB**, Gaussian
81,580개였다. update를 frame 1000 이후에만 집중하고 반복을 1로 낮춘 조건은
1,010 update, **23.879/24.178dB**, 79,889 GS, 101.769s였다.

**둘 다 기각.** 5k에 가까운 update 수를 만들어도 growing map에 이르게 분산하면
소실되고, 끝의 mature 구간만 쓰면 실제 사용 가능한 GPU 시간이 약 4초라 update가
부족하다.

### 모든 RGB 보존 + visual tracking만 20→10fps

`tracking_stride=2`를 추가해 모든 RGB는 도착 즉시 보관하고 dense supervision 및
전체 held-out 평가에 그대로 사용하되, 무거운 VIGS visual tracking만 매 2번째
frame에 실행했다. IMU는 선택된 timestamp 사이를 기존 방식으로 preintegrate한다.
300-frame smoke는 전체 RGB 평가와 1,000 background update를 정상 완주했다.

전체 run은 2,574 update를 확보했지만 keyframe 108개, 최종 57,891 GS,
held-out/keyframe **23.417/23.764dB**, online **101.562s**였다. visual trajectory와
최종 PGBA/pruning 변화의 손실이 계산 이득보다 커 **기각**한다.

### fixed-view-horizon temporal completed chunk

기존 snapshot이 생성 이후 view까지, 그 시점 Gaussian이 없는 오래된 model에
학습한 문제를 차단했다. frame 703 snapshot은 view≤703만 2,560회 독립 polish하고
종료 시 이후 frontier birth 47,354개를 append했다. 그러나 최종 91,906 GS,
held-out/keyframe **18.860/18.939dB**, online **103.051s**로 강하게 실패했다.
과거 chunk만 렌더하면 이후 overlap/occluder가 빠진 상태에서 opacity와 geometry가
잘못 최적화되며, late Gaussian 단순 append로는 compositing을 복구할 수 없다.
temporal chunk는 overlap-aware joint rendering 없이 사용할 수 없다.

SSIM window cache도 수학/gradient bit-exact로 구현했지만 464² forward+backward
microbench가 0.792→0.799ms로 개선이 없어 속도 근거로 채택하지 않는다.

현재 strict 최고는 **23.982dB**다. 27dB 미달이므로 floater labeling/hard carve
pruning은 아직 실행하지 않았다.

산출물:

- `results/experiments/exp57_dense_allintervals_{smoke300,strict15x}`
- `results/experiments/exp57_late2_denseall_fast_strict15x`
- `results/experiments/exp57_late1_start1000_lag0_denseall_fast_strict15x`
- `results/experiments/exp57_trackstride2_{smoke300,start900_dense5k_strict15x}`
- `results/experiments/exp57_temporalchunk700_fixedhorizon_strict15x`

## 2026-07-29 추가 — snapshot merge 및 dense foreground 주입 A/B 기각

strict 27dB를 위해 snapshot/chunk의 결합 손실을 줄이는 방법과, 이미 causal하게
등록된 dense RGB를 foreground `map()`에서도 쓰는 방법을 600-frame smoke로
분리 검증했다. 모든 run은 timestamp 순 Aria RGB+IMU-only이고 MPS 입력과
post-stream optimizer update는 없다. 비교 기준은 같은 설정의 no-snapshot
control이며 held-out/keyframe은 **22.402/22.388dB**다.

| 조건 | held-out / kf PSNR | control 대비 | 판정 |
|---|---:|---:|---|
| target-only snapshot full merge, 400-frame | 16.959 / 16.150 | 400-frame control 19.465 대비 −2.506 | 기각 |
| target-only merge alpha 0.25 | 22.135 / 22.125 | −0.267 | 기각 |
| foreground global slot에 dense view 3개 | 21.867 / 21.698 | −0.535 | 기각 |
| dense lag 150 + loss weight 0.25 | 22.040 / 21.965 | −0.362 | 기각 |
| evolving snapshot overlap-only merge alpha 0.25 | 21.640 / 21.596 | −0.762 | 기각 |

target-only 실패를 point ID 재사용으로 의심했으나 조사 결과 `_next_point_id`는
reset 뒤에도 단조 증가하므로 ID 충돌은 없었다. full merge의 실패는 실제
geometry/appearance 상태 불일치다. alpha를 0.25로 낮추거나 현재 frontier와
공통 point ID만 섞어도 control을 이기지 못했으므로 snapshot merge 계열은
strict 27dB 경로에서 중단한다.

foreground dense-view 주입은 300-frame에서는 기존 all-interval smoke
14.278→15.313dB로 +1.035dB였지만 600-frame에서 역전됐다. 안정화 lag와 약한
loss weight로도 회복하지 못했다. 즉 online 보간 pose의 오차가 누적된 상태에서
무작위 dense RGB를 geometry gradient에 직접 섞는 것은 update 수보다 supervision
정확도를 악화시킨다. 다음 축은 dense frame을 무조건 더 넣는 것이 아니라,
keyframe endpoint 근처처럼 pose 신뢰도가 높은 arrived frame만 causal하게
선별하는 residual/pose-confidence sampler다.

산출물:

- `results/experiments/exp57_targetchunk_{smoke400,control_smoke400}`
- `results/experiments/exp57_targetchunk_{alpha025_smoke600,control_smoke600}`
- `results/experiments/exp57_mapdense3_{smoke300,smoke600}`
- `results/experiments/exp57_mapdense3_lag150_w025_smoke600`
- `results/experiments/exp57_snapshot_overlap_alpha025_smoke600`

## 2026-07-29 추가 — causal dense pose-confidence endpoint sampler

직전 dense foreground 주입 실패가 모든 보간 pose를 같은 신뢰도로 취급한 탓인지
분리했다. keyframe interval 내 보간 위치 `alpha`를 dense Camera에 보존하고,
`min(alpha, 1-alpha)`가 임계값 이하인 endpoint 인접 frame만 foreground global
후보로 쓰는 opt-in sampler를 구현했다. RGB/IMU 도착 뒤 양 endpoint keyframe이
모두 존재할 때만 등록하므로 causal order와 strict 입력 계약은 그대로다.

동일 600-frame no-dense control은 held-out/keyframe **22.402/22.388dB**,
online 48.330s다.

| foreground 조건 | eligible / total dense | held-out / kf | control 대비 | online |
|---|---:|---:|---:|---:|
| dense 3-slot, endpoint gate 없음 | 425 / 425 | 21.867 / 21.698 | −0.535 | 48.269s |
| dense 3-slot, endpoint≤0.20 | 135 / 425 | 21.955 / 21.841 | −0.447 | 48.256s |
| dense 1-slot, endpoint≤0.20 | 135 / 425 | **22.262 / 22.175** | **−0.140** | 48.287s |
| dense 1-slot, endpoint≤0.10 | 46 / 425 | 22.250 / 22.205 | −0.152 | 48.293s |

pose-confidence gate와 tracked-global 교체 3→1 축소는 held-out 손실을
−0.535→−0.140dB로 단조 회복했다. 이는 보간 pose 오차와 tracked keyframe
희석이 실제 원인이라는 증거다. 그러나 가장 좋은 0.20/1-slot도 control을 넘지
못했고 0.10으로 더 엄격하게 해도 개선되지 않았다. 따라서 direct foreground
replacement는 기각하고 전체 1.5× run으로 승격하지 않는다.

다음 품질 축은 단순 sampler 미세조정이 아니라 (1) Gaussian을 고정한 짧은
photometric pose alignment로 dense pose 자체를 개선한 뒤 supervision에 쓰거나,
(2) final-map 5k가 보여준 +4dB gradient가 성장 map에서 사라지지 않도록
overlap-aware spatial submap을 공동 렌더·merge하는 구조다. 둘 다 연산비가
추가되므로 strict deadline 회복 축과 함께 검증해야 한다.

산출물:

- `results/experiments/exp57_mapdense3_endpoint020_smoke600`
- `results/experiments/exp57_mapdense1_endpoint{020,010}_smoke600`

## 2026-07-29 추가 — Gaussian-frozen dense photometric pose alignment

endpoint sampler의 남은 −0.140dB가 보간 pose 오차 때문인지 직접 검증했다.
dense view가 foreground에 처음 선택될 때 Gaussian은 그대로 두고 RGB
L1+SSIM loss의 `cam_rot_delta/cam_trans_delta` gradient만
`torch.autograd.grad`로 받아 pose-only Adam step을 수행한 뒤, 보정 pose로
일반 Gaussian mapping을 다시 실행했다. step당 translation/rotation delta는
각 component 1e-3 이하로 제한했고 PGBA refresh 뒤 보정 상태를 초기화했다.

Gaussian optimizer의 모든 leaf `.grad`가 `None`인지 runtime assert해 gradient
격리를 검증했다. 300-frame smoke는 gradient 누출과 cached-matrix autograd
version 충돌 없이 완주했고 held-out **15.509dB**였다.

600-frame에서는 endpoint≤0.20, dense 1-slot, dense start frame 300을 고정했다.

| 조건 | pose align | held-out / kf | online | Gaussian |
|---|---:|---:|---:|---:|
| no-dense control | 0 | **22.402 / 22.388** | 48.330s | 34,006 |
| start300, no-align | 0 | 22.234 / 22.159 | 48.274s | 34,602 |
| start300, align≤1/view | 84 step / 84 view | **22.318 / 22.236** | 48.302s | 34,552 |
| start300, align≤3/view | 155 step / 89 view | 22.296 / **22.255** | 48.303s | 34,732 |

1-step alignment은 같은 dense 조건에서 held-out **+0.084dB**를 회복하면서
추가 online 비용이 약 0.03초뿐이라 pose 보정 자체는 작지만 유효했다. 그러나
no-dense control보다 여전히 −0.084dB이고, 3-step은 mean PSNR이 다시
−0.022dB 내려갔다. 현재 성장 map의 photometric landscape를 더 오래 따라가면
보간 pose GT에 가까워진다는 보장이 없다는 뜻이다.

따라서 dense pose alignment를 full strict run으로 승격하지 않는다. endpoint
filter/slot 축소/pose alignment를 모두 합쳐도 direct foreground dense replacement는
control을 넘지 못했으므로 이 family는 종료한다. 다음은 final-map dense 5k의
+4dB gradient가 성장 과정에서 소실되지 않도록, temporal append가 아니라
overlap-aware spatial submap을 frontier와 공동 렌더한 뒤 merge하는 구조다.

산출물:

- `results/experiments/exp57_denseposealign1_smoke300`
- `results/experiments/exp57_mapdense1_endpoint020_start300_{noalign,align1,align3}_smoke600`

## 2026-07-29 추가 — overlap-aware joint-context + residual delta merge

이전 temporal snapshot의 18dB 붕괴가 이후 overlap/occluder 부재 때문인지 분리하기
위해, snapshot target Gaussian은 gradient를 받되 현재 frontier의 나머지 Gaussian은
detached context로 함께 렌더하는 joint-context proxy를 구현했다. target lineage는
snapshot 직전 150 frame으로 제한하고, surviving stable point ID만 frontier에
합쳤다. 모든 run은 strict Aria RGB+IMU-only이며 MPS 입력과 post-stream optimizer
update는 0회다.

400-frame에서는 no-snapshot control **19.465/18.650dB** 대비 absolute merge가
**19.643/18.771dB(+0.178/+0.121)**로, snapshot 계열 최초로 control을 넘었다.
그러나 600-frame에서는 971 update가 **22.185/22.188dB**로 control
22.402/22.388보다 낮았다. update를 400회로 제한하면 **22.341/22.307**로
회복했지만 여전히 −0.061/−0.081dB였고, snapshot 시작을 450으로 늦춰도
**22.282/22.299**로 개선되지 않았다.

absolute snapshot이 이후 frontier 학습을 되돌리는 문제를 없애기 위해
`frontier += alpha * (polished_snapshot - source_snapshot)` 형태의 opt-in
`--snapshot_polish_merge_delta`를 구현했다. 600-frame 첫 run은
**22.548/22.524dB**로 당시 control 22.402/22.388보다 +0.146/+0.136dB였으나,
paired control 재실행은 22.461/22.455로 run-to-run mapping schedule 변동이
유의미함을 확인했다. snapshot branch에 빠져 있던 idle guard를 추가하고 5/20ms로
검증해도 각각 **22.307/22.304**, **22.353/22.313dB**로 paired control보다
낮았다.

authoritative 1,253-frame background-off paired A/B:

| strict 1.5×, tail optimizer 0 | no-snapshot control | joint-context delta |
|---|---:|---:|
| held-out PSNR | **23.357** | 22.512 (**−0.845**) |
| keyframe PSNR | **23.603** | 22.667 (**−0.936**) |
| Gaussian | 77,544 | 76,684 |
| online wall | 99.062s | 98.675s |
| deadline 97.65s | +1.412s | +1.025s |

delta 자체는 stale absolute overwrite를 고쳤지만, 같은 non-preemptive GPU worker에서
snapshot render/backward를 실행하면 frontier mapping packet의 처리 시점과
densify/prune 결과가 달라진다. 짧은 smoke의 국소 이득은 full stream에서 재현되지
않았고 품질·deadline 모두 실패했다. 따라서 independent snapshot/joint-context
family는 full strict 경로에서 종료한다. 다음은 opportunistic idle work가 아니라
frontier map()의 반복을 명시적으로 줄여 확보한 **결정론적 view-op 예산** 안에서
dense supervision을 재배분하거나, regular map() 자체에 dense gradient를 융합해
mapping schedule을 보존하는 방향이다.

산출물:

- `results/experiments/exp57_jointcontext_window150_{smoke400,smoke600}`
- `results/experiments/exp57_jointcontext_window150_cap400_smoke600`
- `results/experiments/exp57_jointcontext_start450_window150_cap400_smoke600`
- `results/experiments/exp57_jointcontext_delta_window150_cap400_{smoke600,strict15x}`
- `results/experiments/exp57_jointcontext_delta_guard{,20}_window150_cap400_smoke600`
- `results/experiments/exp57_jointcontext_paired_control_{smoke600,strict15x}`

## 2026-07-29 추가 — regular `map()` 내 dense 전용 iteration 기각

independent snapshot worker가 non-preemptive GPU work로 frontier packet timing과
densify/prune schedule을 바꾸던 문제를 제거하기 위해, dense supervision을 regular
`map()` 안에 결정론적으로 넣었다. 총 iteration 수, optimizer step 수,
`iteration_count`, densify/prune 시점은 control과 같게 유지하고 마지막 1/7
iteration만 causal dense RGB batch로 교체했다. dense 보간 pose의 오차가 새
Gaussian을 만들지 않도록 해당 iteration의 densification statistics는 수집하지
않았다. 모든 입력은 strict Aria RGB+IMU-only이고 MPS 입력과 post-stream
optimizer update는 0회다.

600-frame 결과:

| 조건 | held-out / kf PSNR | control 대비 | Gaussian | online |
|---|---:|---:|---:|---:|
| paired no-snapshot control | **22.461 / 22.455** | - | 34,517 | 48.311s |
| dense 전용 1회, batch 12, weight 1.0 | 22.012 / 21.928 | −0.449 / −0.528 | 33,669 | 48.287s |
| dense 전용 1회, batch 12, weight 0.25 | **22.035 / 22.035** | **−0.426 / −0.421** | 33,878 | 48.281s |

online 시간은 사실상 동일해 independent worker의 schedule jitter는 제거됐다.
그러나 가능한 최소 교체 횟수인 1회에서도 control보다 크게 낮았고, dense RGB
loss weight를 1/4로 낮춰도 held-out은 +0.023dB만 회복했다. 구현 확인 결과
`_frontier_mapping_view_loss()`의 RGB-only branch에 weight가 실제 적용됐으므로
dead flag 문제도 아니다. 주원인은 dense gradient 크기보다 regular RGBD
frontier iteration 하나를 통째로 잃는 것이다. Gaussian 수가 639~848개 감소한
것도 dense statistics 수집을 막았는데도 이후 예정된 prune/densify 상태가
gradient 변화에 민감함을 보여준다.

따라서 dense-only iteration replacement family는 종료하고 full 1,253-frame
strict run으로 승격하지 않는다. 다음 후보는 regular RGBD loss/backward를
보존한 상태에서 dense gradient를 별도로 계산해 충돌 성분만 투영하거나,
tracked-gradient norm의 작은 비율로 제한하는 방식이다. 이는 추가 backward
비용이 있으므로 600-frame에서 PSNR 순이득과 strict deadline 비용을 함께
검증해야 한다. 현재 strict 최고는 **23.982dB**이며, 27dB 미달이므로 hard
carve/floater pruning은 계속 보류한다.

산출물:

- `results/experiments/exp57_denseiter1_batch12_smoke600`
- `results/experiments/exp57_denseiter1_batch12_w025_smoke600`

## 2026-07-29 추가 — gradient projection 및 streaming stable-map boundary

### Regular RGBD를 보존한 dense PCGrad

dense-only iteration이 regular frontier RGBD 제약 하나를 잃어서 실패했으므로,
regular backward를 그대로 수행한 뒤 dense RGB gradient를
`torch.autograd.grad()`로 별도 계산했다. Adam parameter group마다 tracked
gradient와 음의 내적 성분을 투영하고, dense norm을 tracked norm의 일정 비율로
제한한 뒤 같은 optimizer step에 더했다. regular view의 densification statistics,
iteration 수, optimizer step 및 prune/densify schedule은 control과 동일하다.

600-frame paired control은 held-out/keyframe **22.461/22.455dB**, 34,517GS,
online 48.311s다.

| projected dense 조건 | held-out / kf | control 대비 held-out | Gaussian |
|---|---:|---:|---:|
| batch12, all group ratio 0.25 | 22.316 / 22.285 | −0.145 | 34,506 |
| batch12, all group ratio 0.10 | 22.374 / 22.313 | −0.087 | 34,674 |
| appearance 0.25, geometry 0 | **22.405 / 22.399** | **−0.056** | 34,324 |
| 위 조건 + endpoint≤0.20 | 22.298 / 22.318 | −0.163 | 34,452 |

dense-only replacement의 −0.449dB를 −0.056dB까지 회복했고 Gaussian 수도 control과
가까워 gradient 보호가 작동한 것은 확인했다. 하지만 ratio를 0으로 줄일수록
control로 수렴할 뿐 순이득은 없었고 endpoint gate도 역효과였다. 따라서 단일-map
PCGrad family는 full run으로 승격하지 않는다.

### 스트림 안에서 stable-map boundary 만들기

full-map 5k가 약 20초에 27dB를 넘긴 조건을 스트림 종료 전에 만들기 위해 trajectory
coverage를 분석했다. frame 1000 이후 keyframe의 96.2%가 이전 trajectory의 0.5m
안이고 최대 거리도 0.504m였다. 이를 근거로 opt-in
`--mapping_freeze_after_frame`을 구현했다.

- cutoff 이후 새 Gaussian birth, prune, densification, regular optimizer update를
  모두 중단한다.
- RGB+IMU tracking은 끝까지 계속한다.
- 이후 PGBA packet은 기존 Gaussian과 Camera의 pose/scale transform만 적용해
  frozen map을 online SLAM 좌표계에 유지한다.
- settle view는 cutoff 이전 RGB로 제한하고 마지막 sensor frame 뒤 update는 0회다.

frame300→400 smoke에서 1,247 step을 남은 입력 시간 안에 실행해 구조와 zero-tail을
검증했다. 그러나 시간순 round-robin view sampling은 동일 공간의 연속 구간을 Adam이
차례로 덮어쓰며 catastrophic forgetting을 만들었다. carve를 꺼도 해결되지 않았고,
offline fixed-map 성공 경로와 동일하게 uniform random sampling으로 바꾸자:

| 400-frame smoke, freeze300 | held-out / kf | step |
|---|---:|---:|
| temporal round-robin + carve | 17.828 / 18.988 | 1,239 |
| temporal round-robin, carve off | 17.767 / 18.901 | 1,247 |
| **random sampling, carve off** | **21.767 / 24.113** | 1,249 |

random sampling 하나로 held-out **+4.000dB**를 회복했고 같은 구간 no-freeze
control 19.465dB도 +2.302dB 넘었다. stable-map dense settle 자체는 강하게
유효하며, 이전 rolling 실험의 round-robin sampler가 숨은 실패 원인이었음을
확정했다.

authoritative 1,253-frame strict 1.5×, freeze899 결과:

| 조건 | held-out / kf | settle step | GS | online / deadline |
|---|---:|---:|---:|---:|
| round-robin + carve | 16.942 / 18.187 | 3,248 | 55,193 | 97.273s / 통과 |
| round-robin, carve off | 17.014 / 18.153 | 3,289 | 54,880 | 97.303s / 통과 |
| **random, carve off** | **23.080 / 26.097** | **3,399** | **55,172** | **97.289s / 0.361s 여유** |

저장 render의 JPEG 재계산 진단에서 random run은 frame 0~599 약 26.57dB,
600~898 약 24.79dB였지만 899 이후는 약 15~16dB였다. 즉 random settle은 완료
공간의 품질을 실제로 크게 올렸지만, 단일 map을 너무 일찍 freeze해 late view의
새 surface/occlusion coverage를 잃은 것이 전체 평균을 제한했다.

### Late births를 보존한 full-map snapshot 대조

freeze의 late coverage 손실을 피하려고 frame313의 full completed-map snapshot을
random sampling+carve off로 400 step joint-context settle했다. frontier는 계속
성장시키고 stable point ID의 residual delta만 merge해 late births를 보존했다.

| 600-frame 조건 | held-out / kf | control 대비 |
|---|---:|---:|
| full parameter delta merge | 21.805 / 21.703 | −0.656 |
| SH+opacity appearance delta만 merge | **22.234 / 22.247** | **−0.227** |

geometry delta를 막으면 회복됐지만 control 22.461dB를 넘지 못했다. snapshot에서
좋아진 completed 공간과 이후 frontier overlay를 parameter 복사/더하기만으로
reconcile할 수 없다는 뜻이다. 다음 구조는 stable base와 late overlay를 모두
최종 공동 렌더한 loss로 짧게 reconciliation하는 spatial double-buffer다.

모든 run은 `strict_aria_rgb_imu_only`, `mps_inputs=[]`,
`post_stream_refinement=false`이고 MPS 후처리 데이터와 tail optimizer update는
없다. 27dB 미달이므로 floater labeling/hard carve pruning은 실행하지 않았다.
현재 strict 최고는 **23.982dB**다.

산출물:

- `results/experiments/exp57_densepcgrad1_batch12_{r025,r010}_smoke600`
- `results/experiments/exp57_densepcgrad1_batch12_app025_geom0{,_endpoint020}_smoke600`
- `results/experiments/exp57_freeze300_{poseonly_dense_settle,random_nocarve}_smoke400`
- `results/experiments/exp57_freeze899_dense5k{,_nocarve}_strict15x`
- `results/experiments/exp57_freeze899_random_nocarve_strict15x`
- `results/experiments/exp57_fullsnapshot_random_jointdelta_{,app_}cap400_smoke600`

## 2026-07-29 추가 — spatial double-buffer reconciliation 기각

stable base를 먼저 random settle하고 late overlay를 계속 성장시킨 뒤, 두 부분을
최종 공동 렌더 loss로 짧게 reconciliation하는 spatial double-buffer를 구현했다.
frame 300 snapshot을 frame 500에서 appearance(SH+opacity) residual delta로 합치고
그 시점에 regular mapping을 freeze한 뒤, base와 late overlay를 함께 렌더하는
random background settle을 남은 스트림 시간에 수행했다. geometry delta는 late
coverage를 보존하기 위해 합치지 않았고 carve는 껐다.

600-frame 검증은 paired control **22.461/22.455dB** 대비
**23.003/25.342dB(+0.542/+2.887)**, 1,295 reconciliation step, 34,918GS,
online 48.288s로 강한 양성 신호를 보였다. 따라서 같은 구조를 전체 strict
1.5×에 승격해 snapshot 650, merge/freeze 1040으로 실행했다.

| 조건 | held-out / kf PSNR | reconcile step | GS | online / deadline |
|---|---:|---:|---:|---:|
| strict 기존 최고 | **23.982 / 24.402** | - | - | deadline 미달 run |
| double-buffer 600-frame | **23.003 / 25.342** | 1,295 | 34,918 | 48.288s |
| **double-buffer full 1,253** | **23.782 / 25.039** | **1,436** | **65,996** | **97.285s / 0.365s 여유** |

full run은 deadline과 zero-tail을 통과했지만 held-out은 기존 strict 최고보다
**−0.200dB**, 목표보다 −3.218dB였다. 600-frame의 큰 keyframe 이득도 full에서는
감소했고, merge 이후 213-frame의 늦은 coverage를 appearance-only residual과
짧은 joint settle만으로 일관되게 흡수하지 못했다. 따라서 이 schedule을 채택하지
않으며, 짧은 prefix 결과만 보고 전체 품질을 예측할 수 없다는 대조군으로 남긴다.

입력 provenance는 `strict_aria_rgb_imu_only`, `mps_inputs=[]`,
`post_stream_refinement=false`; 마지막 센서 프레임 뒤 optimizer update는 0회다.
1차 목표는 계속 **strict streaming held-out 27dB**이며 27dB 전 hard
carve/floater pruning은 실행하지 않는다. 현재 strict 최고는 **23.982dB**다.

산출물:

- `results/experiments/exp57_doublebuffer_s300_mf500_random_app_smoke600`
- `results/experiments/exp57_doublebuffer_s650_mf1040_random_app_strict15x`

## 2026-07-29 추가 — growing-map random replay full 일반화 실패

stable-map 실험에서 temporal round-robin보다 +4dB였던 uniform random sampler를
map을 freeze하지 않은 growing tensor에 적용했다. 600-frame start300에서는
1,741 step을 흡수해 paired control **22.461/22.455dB** 대비
**24.776/24.885dB(+2.315/+2.430)**, online 48.287s로 이 세션의 가장 강한
prefix 양성 신호가 나왔다.

그러나 같은 설정을 전체 1,253-frame으로 승격하자 4,427 step 뒤
**22.404/22.599dB**, 67,411GS, online 98.879s로 품질·deadline 모두 실패했다.
frame899로 늦춰 geometry를 포함한 random replay를 603회만 실행해도
**22.777/22.951dB**, 72,550GS, 98.934s였다. 600 prefix에는 없는 후반
PGBA가 Gaussian 좌표를 변환한 뒤 Adam geometry moment를 과거 좌표계에 남기는
문제를 발견해 PGBA 직후 xyz/scale/rotation moment reset도 A/B했지만
**22.226/22.405dB**로 더 악화되어 코드는 원복했다.

old base와 late overlay의 regular gradient 간섭을 분리하기 위해 fixed origin
cutoff를 지원하는 opt-in `--background_freeze_origin_cutoff`를 구현했다.
cutoff899 이전 lineage만 별도 background Adam으로 random settle하고 900 이후
21,963개 late Gaussian은 regular mapper가 계속 성장하게 했다. 구조는 최종
frozen **40,630/62,593**, 486 step으로 의도대로 작동했지만 held-out/keyframe은
**22.044/22.062dB**, online 98.944s였다. random sampler로 바꿔도 같은 tensor의
completed lineage를 joint regular gradient에서 끊는 방식은 전역 visibility 결합을
깨뜨린다는 기존 lineage-freeze 결론이 유지된다.

마지막으로 geometry drift 없이 GPU 예산만 재배분했다. frame899 이후 regular
map depth를 7→2 iterations로 줄이고 appearance-only random dense replay를
2,056회 실행했다. online은 **97.435s**로 deadline을 0.215초 통과했고 mapper
drain도 0.0065초였지만 품질은 **23.060/23.345dB**, 74,368GS에 그쳤다.

| full strict 조건 | held-out / kf | replay step | GS | online |
|---|---:|---:|---:|---:|
| growing gaussian, start300 | 22.404 / 22.599 | 4,427 | 67,411 | 98.879s |
| growing gaussian, start899 | 22.777 / 22.951 | 603 | 72,550 | 98.934s |
| 위 + PGBA moment reset | 22.226 / 22.405 | 592 | 72,400 | 99.029s |
| fixed lineage899 random | 22.044 / 22.062 | 486 | 62,593 | 98.944s |
| **appearance random + late iters2** | **23.060 / 23.345** | **2,056** | **74,368** | **97.435s 통과** |

모든 run은 `strict_aria_rgb_imu_only`, `mps_inputs=[]`,
`post_stream_refinement=false`다. 600-frame prefix 이득은 full stream 성공의
근거가 될 수 없으며, same-global-tensor background family는 sampler, geometry
scope, 시작 시점, fixed lineage, late iteration 재배분까지 소진했다. 다음 구조는
PGBA에 흔들리지 않는 keyframe-local stable submap과 late overlay를 parameter
merge 없이 render-time union하는 독립 dual-map이다. 현재 strict 최고
23.982dB와 1차 목표 27dB는 유지하며, 27dB 전 hard carve/floater pruning은
실행하지 않았다.

산출물:

- `results/experiments/exp57_growing_random_start300_{smoke600,strict15x}`
- `results/experiments/exp57_growing_random_start899_cap2500_strict15x`
- `results/experiments/exp57_growing_random_start899_cap2500_pgbareset_strict15x`
- `results/experiments/exp57_lineage899_random_fixedcutoff_strict15x`
- `results/experiments/exp57_growing_random_app_start899_late2_strict15x`

## 2026-07-29 추가 — origin-partition dual-map render-time union 기각

stable snapshot과 late overlay를 parameter copy/blend 없이 최종 공동 렌더하는
독립 dual-map을 구현했다. 첫 구현은 snapshot에 없던 point ID를 late row로
판정했기 때문에 snapshot 이전 Gaussian의 clone/split 자손 17,259개까지 overlay에
중복 포함했고, 600-frame held-out이 20.990dB로 붕괴했다. 이를 point ID가 아니라
`unique_kfIDs > snapshot_source_frame`인 실제 late-origin row만 append하도록
정정했다. joint-context optimization도 동일 origin partition을 사용한다.

정정한 600-frame run은 late overlay가 11,080개, 최종 union이 33,173개로
정상화됐고 held-out/keyframe **22.665/22.368dB**, snapshot step 868,
online 48.282s였다. paired control 22.461dB 대비 held-out **+0.204dB**라 전체
strict run으로 승격했다.

| 조건 | held-out / kf | snapshot step | late / union GS | online |
|---|---:|---:|---:|---:|
| 600, 잘못된 point-ID partition | 20.990 / 20.580 | 778 | 17,259 / 41,508 | 48.273s |
| **600, origin partition** | **22.665 / 22.368** | **868** | **11,080 / 33,173** | **48.282s** |
| **full 1,253, snapshot650** | **22.786 / 22.714** | **1,078** | **33,457 / 69,386** | **99.490s** |

full run은 snapshot source frame 652에서 시작했지만 held-out은 strict 최고
23.982dB보다 −1.196dB였고, 97.65s deadline도 1.840초 초과했다. 마지막 sensor
frame 뒤에는 union materialization과 평가만 했으며 optimizer update는 0회였다.
입력 provenance도 `strict_aria_rgb_imu_only`, `mps_inputs=[]`,
`post_stream_refinement=false`로 계약을 지켰다.

즉 prefix의 작은 이득은 full 후반 PGBA/visibility 변화에 일반화되지 않았고,
stable base와 late overlay를 단순 render-time union하는 것만으로는 둘의
appearance/occlusion 경계를 reconcile하지 못한다. same-tensor, residual merge,
spatial double-buffer, independent origin-partition union까지 모두 full strict에서
기각됐으므로 submap/merge 계열은 종료한다. 현재 strict 최고 23.982dB와 1차 목표
27dB는 유지하며, 27dB 전 hard carve/floater pruning은 실행하지 않았다.

산출물:

- `results/experiments/exp57_snapshotunion_s300_random_joint_smoke600`
- `results/experiments/exp57_snapshotunion_origin_s300_random_joint_smoke600`
- `results/experiments/exp57_snapshotunion_origin_s650_random_joint_strict15x`

## 2026-07-29 추가 — regular mapping 보존 mature-row polish 기각

기존 fixed-lineage 실험은 completed Gaussian을 background Adam으로 polish하는 대신
regular mapper의 gradient/densify/prune에서도 끊었기 때문에 전역 visibility 결합이
깨졌다. 이 원인을 분리하기 위해 `--background_target_origin_cutoff`를 추가했다.
현재 full map을 공동 렌더하되 추가 dense gradient만 cutoff 이전 출생 행에 남기고
별도 Adam으로 step한다. `_frozen_origin_cutoff`는 설정하지 않으므로 regular
mapper는 old/late Gaussian 모두 기존과 동일하게 gradient, densify, prune한다.

600-frame start/cutoff300 gaussian-scope random smoke는 1,504 update를 실행해
held-out/keyframe **23.444/23.297dB**, 28,622GS, online 48.266s였다. paired
control 22.461dB 대비 held-out **+0.983dB**라 full start/cutoff650으로 승격했다.

| 조건 | held-out / kf | background step | GS | online |
|---|---:|---:|---:|---:|
| 600 control | 22.461 / 22.455 | 0 | 34,517 | 48.311s |
| **600 mature-row target300** | **23.444 / 23.297** | **1,504** | **28,622** | **48.266s** |
| **full mature-row target650** | **21.983 / 22.144** | **1,724** | **63,019** | **98.966s** |

full run은 strict 최고보다 held-out −1.999dB이고 97.65s deadline도 1.316초
초과했다. 마지막 sensor frame 뒤 optimizer update는 0회였으며 provenance는
`strict_aria_rgb_imu_only`, `mps_inputs=[]`, `post_stream_refinement=false`다.

regular mapper를 보존해도 별도 Adam의 mature geometry update는 후반 PGBA와
densify/prune을 거치며 full 전역 일관성으로 일반화되지 않았다. 이로써
same-tensor background는 all-row, appearance-only, fixed/rolling lineage freeze,
regular-preserving mature-row target까지 소진했다. 별도 background optimizer의
대상/스케줄 변형은 종료하고, 다음 품질 축은 regular mapper 자체가 매 도착 시점에
소비하는 supervision을 개선하는 방향이다. strict 최고 23.982dB와 1차 목표
27dB는 유지하며 27dB 전 hard carve/floater pruning은 실행하지 않았다.

산출물:

- `results/experiments/exp57_target300_random_gaussian_smoke600`
- `results/experiments/exp57_target650_random_gaussian_strict15x`

## 2026-07-29 추가 — regular mapper target-row dense PCGrad 기각

별도 background optimizer 없이 regular `map()`의 기존 RGBD gradient와
densify/prune을 모두 보존하면서, 추가 dense-frame gradient만 오래된 Gaussian에
제한하는 변형을 검증했다. `--mapping_dense_projected_origin_lag 150`이면 각
mapping 시점에 `unique_kfIDs <= newest_frame - 150`인 행만 dense gradient의
PCGrad dot/norm 계산과 합산 대상이 된다. geometry/appearance 모두 norm ratio
0.25, batch 12, mapping call당 dense step 1회를 사용했다.

| 조건 | held-out / kf | GS | online |
|---|---:|---:|---:|
| 600 paired control | 22.461 / 22.455 | 34,517 | 48.311s |
| **600 target-lag150 dense PCGrad** | **20.636 / 20.686** | **32,158** | **48.284s** |

held-out이 control보다 **−1.825dB**로 크게 악화됐다. 전체 행 PCGrad가 앞서
22.405dB로 순이득이 없었던 데 이어, 과거 출생 행에만 투영해도 regular mapper의
causal visibility/geometry 결합을 해쳤다. 600 prefix부터 명확한 음성이므로
1,253 full strict run으로 승격하지 않는다. 이 결과로 regular mapper 내부
gradient projection의 행 대상 변형도 종료한다.

실행은 `strict_aria_rgb_imu_only`, `mps_inputs=[]`, fixed 1.5×,
`post_stream_refinement=false`를 준수했고 마지막 sensor frame 뒤 optimizer
update는 0회였다. strict 최고 23.982dB와 1차 목표 **strict held-out 27dB**는
유지한다. 27dB 전 hard carve/floater pruning은 실행하지 않았다.

산출물:

- `results/experiments/exp57_densepcgrad1_batch12_targetlag150_smoke600`

## 2026-07-29 추가 — topology-only freeze 기각

기존 `--mapping_freeze_after_frame`은 cutoff 뒤 Gaussian birth뿐 아니라 regular
optimizer update까지 모두 멈췄기 때문에, stable map polishing의 이득과 late
coverage 손실을 분리할 수 없었다. 이를 위해
`--mapping_topology_freeze_after_frame`을 추가했다.

- cutoff 이후에도 새 tracked viewpoint를 저장하고 PGBA pose/scale update와 regular
  RGBD `map()` optimizer step을 계속한다.
- 새 keyframe의 Gaussian birth와 `densify_and_prune()`만 중단한다.
- dense supervision 등록은 계속하며, 마지막 sensor frame 뒤 optimizer update는
  0회다.

600-frame에서 cutoff450을 사용했다. 이는 full 후보 cutoff899와 상대 진행률이
비슷하다(75% vs 71.7%).

| 조건 | held-out / kf | GS | online |
|---|---:|---:|---:|
| 600 paired control | 22.461 / 22.455 | 34,517 | 48.311s |
| **topology freeze450** | **17.135 / 17.345** | **29,929** | **48.353s** |

regular RGBD 업데이트를 보존했는데도 held-out이 **−5.326dB** 붕괴했다. 후반
keyframe의 photometric/depth gradient만으로는 앞선 Gaussian topology가 새로
드러난 표면과 occlusion을 표현할 수 없다. 따라서 stable topology를 일찍 만드는
것 자체가 이 sequence에서는 잘못된 가정이며, full 1,253 run으로 승격하지 않는다.

실행 provenance는 `strict_aria_rgb_imu_only`, `mps_inputs=[]`, fixed 1.5×,
`post_stream_refinement=false`다. strict 최고 23.982dB와 1차 목표 27dB는
유지하고, 27dB 전 hard carve/floater pruning은 실행하지 않았다.

산출물:

- `results/experiments/exp57_topologyfreeze450_smoke600`

## 2026-07-29 추가 — least-used historical global balancing 기각

regular mapper의 frontier window, global slot 수, iteration, optimizer step을
그대로 유지하면서 historical tracked-keyframe global slot의 sampling 분산만
줄이는 `--mapping_global_balanced_sampling`을 구현했다. 각 historical keyframe의
global 선택 횟수를 누적하고, 매 iteration에 least-used view부터 선택하되 동률은
seeded random으로 섞었다. 추가 render/backward와 dense 보간 pose는 없다.

| 조건 | held-out / kf | GS | online |
|---|---:|---:|---:|
| 600 paired control, uniform random | 22.461 / 22.455 | 34,517 | 48.311s |
| **least-used balanced** | **19.859 / 19.710** | **33,102** | **48.285s** |

held-out이 **−2.602dB**로 크게 악화됐다. 짧은 update budget에서 historical
coverage를 균일하게 만드는 것은 현재 성장 map과 맞지 않는 오래된
view/geometry gradient까지 강제로 재방문시킨다. uniform random의 stochastic
sampling이 단순 균등 coverage보다 훨씬 안전하므로 count-only balancing은
full로 승격하지 않는다. 다음 sampler는 선택 횟수가 아니라 현재 map에서 측정한
robust residual/유효성을 직접 반영해야 한다.

실행은 RGB+IMU-only, MPS 금지, fixed 1.5×, zero-tail을 준수했다. strict 최고
23.982dB와 1차 목표 27dB를 유지하고, 27dB 전 hard carve/floater pruning은
실행하지 않았다.

산출물:

- `results/experiments/exp57_balancedglobal_smoke600`

## 2026-07-29 추가 — robust residual historical sampler 기각

count-only balancing이 stale historical gradient를 과대표집했으므로, current-map
유효성을 직접 쓰는 `--mapping_global_residual_sampling`을 구현했다. 각 view가
regular RGBD map step에서 이미 낸 loss를 EMA(0.9)로 저장해 별도 render는 하지
않는다. high-residual score는 median+2×MAD로 cap하고 오래 갱신되지 않은 score는
감쇠했다. historical global 6-slot 중 50%만 이 score로 hard selection하고 나머지는
uniform random exploration으로 보존했다. map reset/IMU 재초기화 시 EMA도 비운다.

| 조건 | held-out / kf | GS | online |
|---|---:|---:|---:|
| 600 paired control | 22.461 / 22.455 | 34,517 | 48.311s |
| **robust high-residual 50%** | **18.364 / 18.368** | **31,338** | **48.273s** |

추가 compute 없이도 held-out이 **−4.097dB** 붕괴했다. 현재 growing map에서 큰
training loss는 “많이 배우면 좋은 view”가 아니라 아직 정합되지 않은 pose,
occlusion 경계, 새 표면을 포함한 outlier 신호다. robust cap과 uniform 50% 혼합도
이를 막지 못했다. 따라서 historical slot의 count-only balancing과 high-residual
hard mining은 모두 종료하며 full run으로 승격하지 않는다.

실행은 RGB+IMU-only, MPS 금지, fixed 1.5×, zero-tail을 준수했다. strict 최고
23.982dB와 1차 목표 27dB를 유지하고, 27dB 전 hard carve/floater pruning은
실행하지 않았다.

산출물:

- `results/experiments/exp57_residualglobal050_smoke600`

## 2026-07-29 추가 — Gaussian-full random + late-iters2 채택

기존 growing-map random replay는 600 prefix에서 +2.315dB였지만 full에서
실패했고, regular map 반복을 7→2로 줄여 update 예산을 확보한 full 대조군은
appearance-only만 실행했다. 반면 fixed-map 5k가 +4.74dB를 낸 필수 조건은
camera-fixed 상태에서 `xyz/scale/rotation/opacity/SH` 전체를 갱신하는
Gaussian-full gradient였다. 이 빠진 조합을 검증했다.

- regular frontier: start frame 이후 map iterations 7→2
- background: 이미 도착한 tracked+dense RGB를 uniform random, camera pose/exposure
  고정, Gaussian 전체 parameter update
- dense: stride5 evaluator offset0을 제외한 offsets1/2/3/4
- carve: 27dB 전 원칙에 따라 background hard/soft carve 모두 비활성

600-frame start300은 3,284 update를 흡수했다.

| 600 조건 | held-out / kf | update | GS | online |
|---|---:|---:|---:|---:|
| paired control | 22.461 / 22.455 | 0 | 34,517 | 48.311s |
| 기존 Gaussian random, regular iters7 | 24.776 / 24.885 | 1,741 | - | 48.287s |
| **Gaussian random + late iters2** | **24.859 / 24.679** | **3,284** | **38,241** | **48.276s** |

control 대비 held-out **+2.398dB**, 기존 random 대비 +0.083dB로 명확한 양성이어서
동일 상대 시작점인 frame650(전체의 51.9%)으로 full 승격했다.

| full strict 1.5× | 결과 |
|---|---:|
| held-out / keyframe PSNR | **24.099 / 24.202dB** |
| SSIM / LPIPS | **0.77781 / 0.45834** |
| background update | **4,730** |
| final Gaussian | **67,759** |
| online wall | **97.274s** |
| deadline | **97.65s 대비 0.376s 통과** |

이 run은 `strict_aria_rgb_imu_only`, `mps_inputs=[]`, fixed 1.5×,
`post_stream_refinement=false`이며 마지막 sensor frame 뒤 optimizer update는
0회다. 기존 deadline-valid 최고 23.782dB보다 **+0.317dB**여서 새 strict best로
채택한다. 전체 최고였지만 deadline을 놓친 23.982dB도 품질과 시간 모두 넘어섰다.

27dB까지는 2.901dB가 남았다. 600의 큰 이득이 full에서는 작아진 원인은 frame1188
부근 late PGBA가 864개 dense pose와 Gaussian 좌표계를 다시 바꾸고, 그 뒤 남은
입력 시간이 짧아 random settle이 재수렴할 시간이 부족한 패턴이다. 다음 축은
Gaussian-full gradient를 약화시키는 것이 아니라, late PGBA 직후 남은 update
예산을 우선 배정하거나 PGBA 직전 update의 유효 상태를 좌표 변환에 맞게 보존하는
방법이다. 27dB 전 hard carve/floater pruning은 계속 보류한다.

산출물:

- `results/experiments/exp57_growing_random_gaussian_start300_late2_smoke600`
- `results/experiments/exp57_growing_random_gaussian_start650_late2_strict15x`

## 2026-07-29 추가 — PGBA xyz Adam moment 공변 변환 기각

late PGBA가 Gaussian 좌표를 바꾼 뒤 Adam geometry moment가 이전 좌표계에 남는
문제를 reset 없이 바로잡기 위해 `--pgba_transform_xyz_adam_moments`를 구현했다.
PGBA의 local affine transform이 `x'=C'+R(x-C)/s`이므로:

- Adam first moment: `m' = Rm/s`
- diagonal second moment: `v' = diag(R diag(v) Rᵀ)/s² = R²v/s²`

90도 z-rotation과 scale2 synthetic test에서 `[1,2,3]→[-1,0.5,1.5]`,
`[1,4,9]→[1,0.25,2.25]` 기대값을 정확히 통과했다.

| 600 Gaussian-full random + late-iters2 | held-out / kf | update | GS | online |
|---|---:|---:|---:|---:|
| moment 변환 없음 | **24.859 / 24.679** | 3,284 | 38,241 | 48.276s |
| **xyz moment 공변 변환** | **24.677 / 24.533** | **3,380** | **37,411** | **48.286s** |

구현과 runtime은 정상이나 held-out이 **−0.182dB**다. Adam이 보존하는 것은 full
covariance가 아니라 축별 diagonal second moment뿐이라, 일반 3D 회전 후 생기는
축간 covariance를 정확히 나타낼 수 없다. 앞선 zero-reset도 더 크게 악화됐으므로
PGBA moment reset/근사 transform 축은 종료하고 full strict로 승격하지 않는다.

strict best는 24.099dB/97.274s로 유지한다. 입력은 RGB+IMU-only, MPS 금지,
fixed 1.5×, zero-tail이며 27dB 전 hard carve/floater pruning은 실행하지 않았다.

산출물:

- `results/experiments/exp57_growing_random_gaussian_start300_late2_xyzmoment_smoke600`

## 2026-07-29 추가 — Gaussian-full random late-iters1 경계 기각

채택된 start300/late-iters2 600 조건에서 regular frontier 반복을 2→1로 더
줄여 random Gaussian-full settle에 예산을 넘겼다.

| 600 조건 | held-out / kf | update | GS | online |
|---|---:|---:|---:|---:|
| **late iters2** | **24.859 / 24.679** | 3,284 | 38,241 | 48.276s |
| late iters1 | 24.789 / **24.729** | **3,644** | 38,248 | 48.278s |

update는 +360회 늘었지만 held-out은 −0.070dB, keyframe은 +0.050dB로 혼재했다.
held-out 27dB가 성공 지표이므로 full strict로 승격하지 않는다. 이 결과로
frontier RGBD 반복과 Gaussian-full random replay의 현재 최적 경계는 **2회**다.

strict best 24.099dB/97.274s를 유지한다. RGB+IMU-only, MPS 금지, fixed 1.5×,
zero-tail이며 27dB 전 hard carve/floater pruning은 실행하지 않았다.

산출물:

- `results/experiments/exp57_growing_random_gaussian_start300_late1_smoke600`

## 2026-07-29 추가 — post-PGBA1188 Gaussian burst 실행기회 0회

full best에서 마지막 PGBA가 frame1188에 864개 dense pose와 Gaussian 좌표를
갱신한 뒤 재수렴 시간이 짧았으므로, background start와 late-iters1을 모두
1188로 설정해 남은 stream 시간만 fixed-map형 Gaussian-full random settle에
쓰려 했다.

| 조건 | background update | held-out / kf | GS | online |
|---|---:|---:|---:|---:|
| post-PGBA1188 burst | **0** | **22.997 / 23.307** | 86,469 | **97.867s** |

frame1188 이후 tracking이 마지막 frame까지 연속 active였고, background worker의
idle guard를 만족한 구간이 한 번도 없어 optimizer update가 0회였다. 마지막
sensor frame 뒤 update는 금지되어 있으므로 종료 뒤 backlog를 처리하지 않았다.
deadline 97.65s도 0.217초 초과했다.

이는 구현 미배선이 아니라 fixed-rate streaming의 계산 인과성이다. 앞선 구간의
GPU idle 시간을 “저축”해 마지막 PGBA 뒤 사용할 수는 없다. late burst family는
종료하며, 다음 가능 경로는 마지막 PGBA를 더 이른 frame에서 끝내 그 이후의
Gaussian-full update가 같은 최종 좌표계에 누적되게 하는 것이다.

strict best 24.099dB/97.274s는 유지한다. RGB+IMU-only, MPS 금지, fixed 1.5×,
zero-tail이며 27dB 전 hard carve/floater pruning은 실행하지 않았다.

산출물:

- `results/experiments/exp57_postpgba1188_gaussian_late1_strict15x`

## 2026-07-29 추가 — late global PGBA cutoff1120, strict 신기록

마지막 PGBA가 이미 누적된 Gaussian-full random replay의 좌표계와 optimizer 상태를
종료 직전 다시 흔드는 효과를 직접 분리했다. `--pgba_disable_after_frame 1120`을
추가해 frame1120 이전 online PGBA는 그대로 허용하고, 이후 global PGBA만 억제했다.
local frontend BA와 tracking은 끝까지 계속 실행했으며 pose/depth 외부 입력은 쓰지
않았다.

| full strict 1.5× | 기존 late-iters2 | **PGBA cutoff1120** | 변화 |
|---|---:|---:|---:|
| held-out PSNR | 24.099 | **24.319** | **+0.220dB** |
| keyframe PSNR | 24.202 | **24.385** | **+0.183dB** |
| SSIM / LPIPS | 0.77781 / 0.45834 | **0.78868 / 0.44374** | 둘 다 개선 |
| background update | 4,730 | **5,087** | +357 |
| final Gaussian | 67,759 | **66,784** | −975 |
| online wall | 97.274s | **97.264s** | −0.010s |
| deadline margin | 0.376s | **0.386s** | 통과 |

`strict_aria_rgb_imu_only`, `mps_inputs=[]`, fixed 1.5×,
`post_stream_refinement=false`이고 마지막 sensor frame 뒤 optimizer update는
0회다. 따라서 새 deadline-valid strict best로 채택한다. 이는 PGBA 전체가 해롭다는
결론이 아니라, 현재 스케줄에서 **마지막 global 좌표계 변경 뒤 재수렴할 입력 시간이
부족하다**는 결과다.

평가의 PSNR/SSIM/LPIPS 계산은 완료됐지만, 이후 render PNG와 `intrinsics.npy`를
저장하던 중 디스크가 가득 차 프로세스가 exit 1로 끝났다. PLY, trajectory,
config, input provenance와 stdout 지표는 보존됐고, 해당 부가 artifact는 부분
저장으로 간주한다. 재현 가능한 탈락 실험의 render PNG 407MB만 정리했으며 원본
데이터와 체크포인트는 삭제하지 않았다.

27dB까지는 2.681dB가 남았다. 1차 목표는 계속 strict held-out 27dB이며, 달성 전
hard carve/floater pruning은 품질 레버로 섞지 않는다.

산출물:

- `results/experiments/exp57_growing_random_gaussian_start650_late2_pgbacut1120_strict15x`

## 2026-07-29 추가 — PGBA cutoff1070 과억제 기각

cutoff1120은 frame1184의 마지막 PGBA 하나만 억제했다. 좌표계 안정 구간을 더 길게
주면 random replay가 더 수렴하는지 확인하기 위해 cutoff1070으로 내려
frame1077·1119·1184의 세 late PGBA를 모두 억제했다.

| full strict 1.5× | cutoff1120 | **cutoff1070** | 변화 |
|---|---:|---:|---:|
| held-out / keyframe PSNR | **24.319 / 24.385** | 24.091 / 24.060 | −0.229 / −0.325dB |
| SSIM / LPIPS | **0.78868 / 0.44374** | 0.77892 / 0.45609 | 둘 다 악화 |
| background update | 5,087 | **6,489** | +1,402 |
| final Gaussian | 66,784 | 55,997 | −10,787 |
| online wall | 97.264s | 97.271s | +0.007s |
| deadline margin | 0.386s | 0.379s | 둘 다 통과 |

update 수 증가가 품질로 이어지지 않았고, 이전 PGBA가 제공하던 global geometry
보정까지 잃은 손해가 더 컸다. 따라서 “PGBA를 일찍 끝낼수록 좋다”는 가설은
기각하고, 종료 뒤 재수렴 시간이 없는 마지막 PGBA 하나만 막는 **cutoff1120을
채택점으로 유지**한다.

디스크 포화를 막기 위해 `--eval_metrics_only`를 추가했다. held-out/keyframe
렌더링과 PSNR/SSIM/LPIPS 계산 및 JSON 저장은 동일하고 per-view render/depth
이미지만 생략한다. strict provenance에도 이 선택을 기록했다.

RGB+IMU-only, MPS 금지, fixed 1.5×, zero-tail을 준수했다. strict best
24.319dB와 1차 목표 27dB를 유지하며, 27dB 전 hard carve/floater pruning은
실행하지 않았다.

산출물:

- `results/experiments/exp57_growing_random_gaussian_start650_late2_pgbacut1070_strict15x`

## 2026-07-29 추가 — tracking stride2 replay 재투자 기각

late 구간에서 tracking이 연속 active라 background idle 기회가 부족한 문제를 직접
겨냥했다. RGB와 IMU는 모두 timestamp 순으로 ingest하면서 visual tracker만 매
2번째 RGB에서 실행하고, 비워진 GPU 시간을 Gaussian-full random replay에 넘겼다.

| 600 start300 + late-iters2 | tracking stride1 | **stride2** | 변화 |
|---|---:|---:|---:|
| held-out / keyframe PSNR | **24.859 / 24.679** | 24.525 / 24.281 | −0.334 / −0.398dB |
| SSIM / LPIPS | - | 0.79492 / 0.47243 | - |
| background update | 3,284 | **3,599** | +315 |
| final Gaussian | 38,241 | 38,940 | +699 |
| online wall | **48.276s** | 48.537s | +0.261s |

추가 replay는 실제로 생겼지만 tracker 표본 감소에 따른 pose/geometry supervision
손실이 더 컸고, queue drain까지 포함한 online wall도 개선되지 않았다. 따라서
full strict로 승격하지 않고 `tracking_stride=1`을 유지한다.

RGB+IMU-only, MPS 금지, zero-tail을 준수했고 `--eval_metrics_only`로 optimizer
update 없는 동일 평가 지표만 저장했다. strict best 24.319dB와 1차 목표 27dB를
유지하며, 27dB 전 hard carve/floater pruning은 실행하지 않았다.

산출물:

- `results/experiments/exp57_growing_random_gaussian_start300_late2_trackstride2_smoke600`

## 2026-07-29 추가 — replay 시작 frame400 기각

start300에서 regular frontier `map()` 반복을 7→2로 너무 일찍 줄여 late geometry
coverage를 잃는지 분리하려고, background replay와 late mapping 전환을 모두
frame400으로 늦췄다.

| 600 late-iters2 | start300 | **start400** | 변화 |
|---|---:|---:|---:|
| held-out / keyframe PSNR | **24.859 / 24.679** | 23.993 / 23.795 | −0.866 / −0.884dB |
| SSIM / LPIPS | - | 0.79004 / 0.47365 | - |
| background update | **3,284** | 2,159 | −1,125 |
| final Gaussian | 38,241 | 37,316 | −925 |
| online wall | 48.276s | 48.298s | +0.022s |

regular 반복을 더 오래 보존한 이득보다 Gaussian-full random replay 1,125회를 잃은
손해가 훨씬 컸다. 따라서 약 50% 상대 경계인 600의 start300과 full의 start650을
유지하고, 다음 처리량 실험은 시작점을 바꾸지 않는다.

RGB+IMU-only, MPS 금지, zero-tail을 준수했고 지표-only 평가를 사용했다. strict
best 24.319dB와 1차 목표 27dB를 유지하며 27dB 전 hard carve/floater pruning은
실행하지 않았다.

산출물:

- `results/experiments/exp57_growing_random_gaussian_start400_late2_smoke600`

## 2026-07-29 추가 — CUDA batch2 replay 기각

`background_polish_step()`은 batch가 2 이상이면 Phase 11의
`render_kernel_batch()`를 사용하므로, 두 random view의 renderCUDA launch를 묶고
loss를 평균한 뒤 optimizer를 한 번 step한다. 같은 start300/late-iters2 조건에서
batch2를 시험했다.

| 600 | batch1 | **batch2** | 변화 |
|---|---:|---:|---:|
| held-out / keyframe PSNR | **24.859 / 24.679** | 24.433 / 24.206 | −0.426 / −0.473dB |
| SSIM / LPIPS | - | 0.79580 / 0.47739 | - |
| optimizer step | **3,284** | 1,995 | −1,289 |
| supervised view update | 3,284 | **3,990** | +706 |
| final Gaussian | 38,241 | 37,396 | −845 |
| online wall | 48.276s | 48.308s | +0.032s |

kernel batch로 view 처리량은 늘었지만 두 view 평균 gradient 한 번이 두 순차 Adam
step을 대체하지 못했다. 현재 수렴에는 view 수보다 optimizer step 횟수가
중요하므로 `background_polish_batch_size=1`을 유지한다.

RGB+IMU-only, MPS 금지, zero-tail을 준수했고 지표-only 평가를 사용했다. strict
best 24.319dB와 1차 목표 27dB를 유지하며 27dB 전 hard carve/floater pruning은
실행하지 않았다.

산출물:

- `results/experiments/exp57_growing_random_gaussian_start300_late2_batch2_smoke600`

## 2026-07-29 추가 — background LR 압축, prefix 양성이나 full 기각

같은 optimizer step 수에서 더 빨리 수렴시키기 위해 background step에만 모든
Gaussian parameter-group LR을 곱하고, step 직후 regular frontier LR을 원래 값으로
복원하는 `--background_polish_lr_multiplier`를 구현했다. 기본값 1.0은 기존
동작이며 strict provenance에 배율을 기록한다.

| 600 start300/late-iters2 | LR×1.0 | **LR×1.5** | LR×2.0 |
|---|---:|---:|---:|
| held-out PSNR | 24.859 | **24.949** | 24.706 |
| keyframe PSNR | 24.679 | **25.004** | 24.731 |
| background update | 3,284 | 3,436 | 3,378 |
| online wall | 48.276s | 48.278s | 48.309s |

1.5×가 +0.090/+0.325dB로 양성이어서 cutoff1120 full strict로 승격했다.

| full strict 1.5× | LR×1.0 | **LR×1.5** | 변화 |
|---|---:|---:|---:|
| held-out / keyframe PSNR | **24.319 / 24.385** | 23.749 / 23.840 | −0.571 / −0.546dB |
| SSIM / LPIPS | **0.78868 / 0.44374** | 0.77625 / 0.46338 | 둘 다 악화 |
| background update | 5,087 | 5,225 | +138 |
| final Gaussian | 66,784 | 68,507 | +1,723 |
| online wall | 97.264s | 97.272s | +0.008s |
| deadline margin | 0.386s | 0.378s | 둘 다 통과 |

prefix 양성이 full에서 일반화되지 않았고, evolving map에 높은 LR을 5k step 끝까지
누적한 후반 불안정이 지배적이다. 따라서 무제한 고정 multiplier는 기각한다. 다음
실험은 초기 background step에만 1.5×를 적용한 뒤 자동으로 1.0으로 복귀시켜
prefix 양성 신호와 full 안정성을 동시에 보존하는 제한형이다.

모든 run은 RGB+IMU-only, MPS 금지, fixed 1.5×, zero-tail을 준수했고 지표-only
평가를 사용했다. strict best 24.319dB와 1차 목표 27dB를 유지하며 27dB 전 hard
carve/floater pruning은 실행하지 않았다.

산출물:

- `results/experiments/exp57_growing_random_gaussian_start300_late2_lr150_smoke600`
- `results/experiments/exp57_growing_random_gaussian_start300_late2_lr200_smoke600`
- `results/experiments/exp57_growing_random_gaussian_start650_late2_lr150_pgbacut1120_strict15x`

## 2026-07-29 추가 — background LR 초기-step 제한형도 full 기각

무제한 LR×1.5가 600-frame prefix에서는 양성이지만 full에서 후반 불안정으로
붕괴했으므로, `--background_polish_lr_multiplier_steps`를 추가했다. background
optimizer의 성공한 step 수가 지정한 cap에 도달할 때까지만 1.5×를 적용하고 이후
자동으로 1.0×로 돌아간다. frontier optimizer LR은 각 background step 직후
계속 복원된다.

| 600 start300/late-iters2 | LR×1.0 | **LR×1.5 cap2500** | **LR×1.5 cap1000** |
|---|---:|---:|---:|
| held-out PSNR | 24.859 | **25.181** | **24.990** |
| keyframe PSNR | 24.679 | **25.252** | **24.932** |
| SSIM / LPIPS | - | 0.80079 / 0.45913 | 0.79860 / 0.45500 |
| background update | 3,284 | 3,358 | 3,325 |
| final Gaussian | 38,241 | 38,266 | 38,181 |
| online wall | 48.276s | 48.312s | 48.321s |

cap2500은 held-out +0.322dB, cap1000은 +0.131dB로 둘 다 prefix 양성이어서
full cutoff1120으로 승격했다.

| full strict 1.5× | LR×1.0 | **cap2500** | **cap1000** |
|---|---:|---:|---:|
| held-out PSNR | **24.319** | 24.216 | 24.217 |
| keyframe PSNR | **24.385** | 24.283 | 24.311 |
| SSIM / LPIPS | 0.78868 / 0.44374 | 0.78641 / 0.44812 | 0.78725 / 0.44671 |
| background update | 5,087 | 5,265 | 5,245 |
| final Gaussian | 66,784 | 66,530 | 67,953 |
| online wall | 97.264s | 97.267s | 97.282s |
| deadline margin | 0.386s | 0.383s | 0.368s |

제한형은 무제한안의 큰 붕괴는 막았지만 full held-out은 strict best보다 각각
−0.103dB, −0.102dB였다. 짧은 prefix에서의 최적 LR 구간이 evolving full map의
여러 성장 단계에 그대로 대응하지 않는다. cap을 더 줄이는 것은 결과가 이미
1.0× 기준으로 수렴하는 방향이며 2.681dB의 목표 격차를 설명할 레버가 아니다.
따라서 uniform all-parameter LR 배율 계열은 무제한·제한형 모두 종료한다.

모든 run은 RGB+IMU-only, MPS 금지, fixed 1.5×, zero-tail을 준수했고
`--eval_metrics_only`로 optimizer update 없는 동일 held-out 평가를 수행했다.
strict best 24.319dB와 1차 목표 27dB를 유지하며, 27dB 전 hard carve/floater
pruning은 실행하지 않았다.

산출물:

- `results/experiments/exp57_growing_random_gaussian_start300_late2_lr150cap2500_smoke600`
- `results/experiments/exp57_growing_random_gaussian_start650_late2_lr150cap2500_pgbacut1120_strict15x`
- `results/experiments/exp57_growing_random_gaussian_start300_late2_lr150cap1000_smoke600`
- `results/experiments/exp57_growing_random_gaussian_start650_late2_lr150cap1000_pgbacut1120_strict15x`

## 2026-07-29 추가 — background LR parameter-group 분리도 full 기각

uniform 1.5×가 full에서 무너지는 원인이 geometry인지 appearance인지 분리하기 위해
`--background_polish_lr_multiplier_scope`를 추가했다. `appearance_opacity`는
`f_dc`, `f_rest`, `opacity`만, `geometry`는 `xyz`, `scaling`, `rotation`만
배율을 적용한다. 기본값 `all`은 기존 동작과 동일하다.

| 600 start300/late-iters2 | LR×1.0 | appearance+opacity 1.5× | **geometry 1.5×** |
|---|---:|---:|---:|
| held-out PSNR | 24.859 | 24.654 | **25.090** |
| keyframe PSNR | 24.679 | 24.545 | **25.024** |
| SSIM / LPIPS | - | 0.79565 / 0.46104 | 0.79878 / 0.46109 |
| background update | 3,284 | 3,438 | 3,301 |
| final Gaussian | 38,241 | 37,496 | 38,301 |
| online wall | 48.276s | 48.298s | 48.299s |

appearance+opacity는 held-out −0.205dB였고 geometry-only는 +0.231dB였다. 따라서
prefix uniform LR 이득의 출처는 geometry 가속이며, appearance 배율은 오히려
해롭다는 인과 분리가 됐다. geometry-only를 full cutoff1120으로 승격했다.

| full strict 1.5× | LR×1.0 | **geometry 1.5×** | 변화 |
|---|---:|---:|---:|
| held-out / keyframe PSNR | **24.319 / 24.385** | 23.816 / 23.916 | −0.503 / −0.469dB |
| SSIM / LPIPS | **0.78868 / 0.44374** | 0.77948 / 0.46234 | 둘 다 악화 |
| background update | 5,087 | 5,247 | +160 |
| final Gaussian | 66,784 | 65,531 | −1,253 |
| online wall | 97.264s | 97.300s | +0.036s |
| deadline margin | 0.386s | 0.350s | 둘 다 통과 |

prefix의 geometry 수렴 가속은 확인했지만, 높은 geometry LR을 evolving full map의
PGBA·densification·신규 표면 성장 전체에 누적하면 형상 안정성을 해친다. 짧은
prefix 최적값을 full에 외삽할 수 없다는 이전 제한형 결과와 일치한다. 따라서
uniform, 초기-step 제한, parameter-group 분리를 포함한 background LR 배율
family를 종료한다. opt-in scope 코드는 향후 진단 자산으로 남기며 기본 동작은
변하지 않는다.

모든 run은 RGB+IMU-only, MPS 금지, fixed 1.5×, zero-tail을 준수했고
`--eval_metrics_only`로 optimizer update 없는 동일 평가를 수행했다. strict best
24.319dB와 1차 목표 27dB를 유지하며, 27dB 전 hard carve/floater pruning은
실행하지 않았다.

산출물:

- `results/experiments/exp57_growing_random_gaussian_start300_late2_lr150_appopacity_smoke600`
- `results/experiments/exp57_growing_random_gaussian_start300_late2_lr150_geometry_smoke600`
- `results/experiments/exp57_growing_random_gaussian_start650_late2_lr150_geometry_pgbacut1120_strict15x`

## 2026-07-29 추가 — stable-map freeze1000은 keyframe만 개선, held-out 기각

freeze899는 완료 구간을 강하게 정제했지만 899 이후 신규 surface를 잃어 held-out
23.080dB에 그쳤다. 반면 trajectory 분석에서 frame1000 이후 keyframe의 96.2%가
이전 궤적 0.5m 이내였으므로, 현재 best 레시피에
`--mapping_freeze_after_frame 1000`만 추가했다. boundary 뒤에도 RGB+IMU
tracking은 끝까지 계속했고, Gaussian birth/regular optimizer만 멈췄다.
background view horizon은 frame999로 고정됐으며 마지막 sensor frame 뒤 update는
0회다.

| full strict 1.5× | 기존 best | **freeze1000** | 변화 |
|---|---:|---:|---:|
| held-out PSNR | **24.319** | 24.031 | **−0.288dB** |
| keyframe PSNR | 24.385 | **26.015** | **+1.630dB** |
| SSIM / LPIPS | 0.78868 / 0.44374 | 0.77372 / 0.45578 | held-out 악화 |
| background update | 5,087 | **6,370** | +1,283 |
| final Gaussian | 66,784 | 67,944 | +1,160 |
| online wall | 97.264s | **97.264s** | 동일 |
| deadline margin | 0.386s | **0.386s** | 둘 다 통과 |

추가 fixed-map update는 keyframe fit을 1.63dB 올렸으므로 수렴 능력 자체는 명확히
유효하다. 하지만 frame1000 이후 map growth를 닫자 held-out 신규 시점 일반화가
악화됐다. “후반 keyframe이 기존 궤적 근처”라는 위치 통계만으로 신규 occlusion,
view direction, 비-keyframe 표면 coverage를 대체할 수 없다. 따라서 freeze1000은
채택하지 않는다.

이 결과는 strict 27dB의 병목이 단순 optimizer step 부족만이 아님을 좁힌다.
필요한 구조는 map을 고정해 수렴시키는 동시에 late surface와 non-keyframe
coverage를 계속 공동 표현해야 한다. 앞선 snapshot/dual-map의 hard partition도
실패했으므로, 다음 축은 분리된 map merge가 아니라 growing map 안에서 late
coverage를 보존하는 supervision/parameterization이어야 한다.

입력은 RGB+IMU-only, MPS 금지, fixed 1.5×, zero-tail이며 27dB 전 hard
carve/floater pruning은 실행하지 않았다. strict best 24.319dB를 유지한다.

산출물:

- `results/experiments/exp57_growing_random_gaussian_start650_late2_freeze1000_pgbacut1120_strict15x`

## 2026-07-29 추가 — causal optical dense pose와 PGBA residual 보존

### 가설과 online 계약

기존 dense RGB supervision은 양 끝 keyframe pose의 SE(3) interpolation만 사용했다.
반면 VIGS의 `PoseTrajectoryFiller.fill`은 이미 도착한 왼쪽/오른쪽 keyframe 사이의
과거 RGB frame을 optical correlation으로 refinement할 수 있다. 오른쪽 endpoint가
도착한 뒤 완료 구간만 처리하면 미래 입력을 쓰지 않으므로 causal이다.

`--background_dense_pose_source {interpolate,trajectory_filler}`를 opt-in으로
추가했다. strict run은 frame 순서 RGB photo와 IMU만 사용했고
`mps_inputs=[]`, fixed 1.5×, `post_stream_refinement=false`, 마지막 sensor frame 뒤
optimizer update 0을 유지했다. trajectory-filler 입력도 현재까지 도착한 RGB와
tracking state뿐이며 MPS postprocess pose/depth/point cloud는 사용하지 않았다.

### 600-frame 선별과 최초 full 실패

offset2, start300, late-iters1의 600-frame 선별은 optical dense view 107장,
3,291 background update, 36,397GS, online 48.288s에서 held-out/keyframe
**25.336/25.223dB**, SSIM 0.82074, LPIPS 0.38081이었다. 같은 late-iters2
interpolation 대조군 24.859dB보다 held-out **+0.477dB**여서 full로 승격했다.

하지만 최초 full late-iters1은 **24.115/24.141dB**(5,200 update, 47,268GS),
late-iters2는 **23.929/23.992dB**(4,494 update, 62,807GS)로 실패했다. 원인을
추적하자 PGBA 뒤 `_refresh_causal_dense_poses()`가 optical pose를 endpoint
interpolation으로 무조건 덮어쓰고 있었다. 즉 prefix에서 확인한 보정이 full의
global pose update 때 사라지는 구현 버그였다.

### local SE(3) residual 보존과 strict 신기록

각 optical pose를 `T_interp^-1 @ T_optical` local residual로 저장하고, PGBA 뒤에는
갱신된 endpoint의 `T_interp_new @ residual`로 재합성하도록 수정했다. scale
reinitialization 때 residual translation도 같은 배율로 조정한다.

| full strict 1.5× | 기존 interpolation best | optical + residual 보존 | 변화 |
|---|---:|---:|---:|
| held-out PSNR | 24.319 | **24.483** | **+0.164dB** |
| keyframe PSNR | 24.385 | **24.520** | **+0.135dB** |
| SSIM / LPIPS | 0.78868 / 0.44374 | **0.80350 / 0.39884** | 둘 다 개선 |
| background update | 5,087 | 4,581 | −506 |
| final Gaussian | 66,784 | 62,069 | −4,715 |
| online wall | 97.264s | **97.287s** | +0.023s |
| deadline margin | 0.386s | **0.363s** | 둘 다 통과 |

따라서 causal trajectory-filler pose와 PGBA residual 보존을 새 deadline-valid strict
best로 채택한다. 이 결과는 더 많은 update가 아니라 비-keyframe supervision의
pose 품질이 held-out 일반화에 실제 영향을 준다는 증거다. 다만 600-frame의
+0.477dB가 full에서는 +0.164dB로 축소됐고, 27dB까지 **2.517dB**가 남았다.
따라서 단독으로 목표를 해결한 것은 아니며 late reset/coverage와 optical dense
view의 수명 관리를 다음 병목으로 본다. 27dB 전 hard carve/floater pruning은
계속 실행하지 않는다.

산출물:

- 구조 확인(품질 판정 제외):
  `results/experiments/exp57_dense_trajfiller_start150_late2_smoke300`
- 600-frame:
  `results/experiments/exp57_dense_trajfiller_offset2_start300_late1_smoke600`
- residual 보존 전 full 실패:
  `results/experiments/exp57_dense_trajfiller_offset2_start650_late1_pgbacut1120_strict15x`,
  `results/experiments/exp57_dense_trajfiller_offset2_start650_late2_pgbacut1120_strict15x`
- 채택:
  `results/experiments/exp57_dense_trajfiller_residual_offset2_start650_late2_pgbacut1120_strict15x`

## 2026-07-29 추가 — optical stride phase 선별, offset4 strict 신기록

offset2의 성공 뒤 “optical dense view를 더 넣으면 coverage가 늘어난다”는 가설을
검증했다. 먼저 offsets1/2/3/4를 모두 넣자 600-frame 등록 view는 107→431장으로
늘었지만 update는 3,291→2,989회로 줄었고 held-out은 **25.336→24.027dB
(−1.309dB)**로 악화됐다. 따라서 coverage 수보다 trajectory-filler pose의
일관성이 중요하다고 보고 각 stride phase를 단독 분리했다.

| 600-frame, start300/late-iters1 | held-out / kf | update | online | 판정 |
|---|---:|---:|---:|---|
| offset2 기존 | 25.336 / 25.223 | 3,291 | 48.288s | 기준 |
| **offset1** | **25.704 / 25.553** | 3,284 | 48.316s | full 승격 |
| offset3 | 24.865 / 24.668 | 3,223 | 48.321s | 기각 |
| **offset4** | **25.746 / 25.463** | 3,249 | 48.338s | full 승격 |
| offsets1–4 | 24.027 / 23.576 | 2,989 | 48.289s | 강한 기각 |
| offsets1+4 | 24.232 / 24.039 | 3,328 | 48.288s | 강한 기각 |

단일 offset1과 offset4는 모두 강했지만 둘을 함께 넣으면 다시 붕괴했다. 이는 단순히
나쁜 offset3이 전체 혼합을 망친 것이 아니다. 서로 다른 optical phase의 작은 pose
오차가 동일 Gaussian geometry를 다른 방향으로 당기고, uniform random replay가
이를 평균내지 못한다. 현재 구조에서는 많은 dense view보다 **한 phase의 일관된
trajectory lineage**가 더 중요하다.

full은 authoritative 1,253-frame 범위로 실행했다. 중간에 `--length 1253`을 빠뜨린
1,303-frame 진단 run은 24.926dB였지만 101.024s로 strict 판정에서 제외하고,
아래 두 run만 채택 판정에 사용했다.

| full strict 1.5× | offset2 기존 best | offset1 | **offset4** |
|---|---:|---:|---:|
| held-out PSNR | 24.483 | 24.465 | **24.538** |
| keyframe PSNR | 24.520 | **24.553** | 24.521 |
| SSIM / LPIPS | 0.80350 / 0.39884 | 0.80335 / 0.39444 | 0.80179 / **0.39362** |
| background update | 4,581 | 4,591 | **5,025** |
| final Gaussian | 62,069 | 67,572 | 67,145 |
| online wall | 97.287s | **97.256s** | 97.309s |
| deadline margin | 0.363s | **0.394s** | 0.341s |

offset1은 keyframe과 시간은 좋지만 held-out이 기존 best보다 −0.018dB라 기각한다.
offset4는 held-out **+0.055dB**로 새 deadline-valid strict best다. 입력은
RGB+IMU-only, `mps_inputs=[]`, fixed 1.5×, post-stream optimizer update 0회다.
따라서 offset4 단독을 채택한다. 27dB까지 **2.462dB**가 남았으며, low-quality
map에 hard carve/floater pruning을 섞지 않는 원칙은 유지한다.

산출물:

- 600-frame:
  `results/experiments/exp57_dense_trajfiller_offsets1234_residual_start300_late1_smoke600`,
  `results/experiments/exp57_dense_trajfiller_offset1_residual_start300_late1_smoke600`,
  `results/experiments/exp57_dense_trajfiller_offset3_residual_start300_late1_smoke600`,
  `results/experiments/exp57_dense_trajfiller_offset4_residual_start300_late1_smoke600`,
  `results/experiments/exp57_dense_trajfiller_offsets14_residual_start300_late1_smoke600`
- full:
  `results/experiments/exp57_dense_trajfiller_offset1_residual_start650_late2_pgbacut1120_len1253_strict15x`,
  `results/experiments/exp57_dense_trajfiller_offset4_residual_start650_late2_pgbacut1120_len1253_strict15x`
- 판정 제외 1,303-frame 진단:
  `results/experiments/exp57_dense_trajfiller_offset1_residual_start650_late2_pgbacut1120_strict15x`

## 2026-07-29 추가 — optical replay + stable-map freeze1050, strict 25.435dB

과거 freeze1000은 keyframe만 26.015dB로 올리고 held-out을 24.031dB로 낮췄다.
당시는 keyframe-only/interpolation supervision이라 freeze 뒤 late 신규 시점
coverage를 잃었다. 현재 offset4 trajectory-filler는 완료된 causal interval의
비-keyframe RGB view를 계속 replay하므로, regular growing-map을 멈춘 뒤에도
late view direction supervision을 유지할 수 있다. 이 차이를 이용해 offset4
채택점에 `--mapping_freeze_after_frame`만 결합하고 경계를 스캔했다.

| full strict 1.5× | no-freeze | freeze1000 | **freeze1050** | freeze1075 | freeze1100 |
|---|---:|---:|---:|---:|---:|
| held-out PSNR | 24.538 | 25.050 | **25.435** | 25.198 | 24.685 |
| keyframe PSNR | 24.521 | 27.367 | **27.548** | 26.944 | 25.985 |
| SSIM | 0.80179 | 0.79946 | **0.80113** | 0.79883 | 0.79863 |
| LPIPS | 0.39362 | 0.36900 | **0.34930** | 0.35319 | 0.38420 |
| background update | 5,025 | 5,494 | **5,748** | 5,445 | 5,057 |
| final Gaussian | 67,145 | 64,226 | **68,970** | 72,897 | 52,649 |
| online wall | 97.309s | 97.274s | **97.283s** | 97.308s | 97.300s |

1050의 단일 최고값이 wall-time scheduler의 우연인지 확인하기 위해 같은 seed와
CLI로 한 번 더 실행했다.

| freeze1050 재현성 | 원 run | 반복 run | 차이 |
|---|---:|---:|---:|
| held-out PSNR | **25.435** | **25.347** | −0.088dB |
| keyframe PSNR | 27.548 | 27.129 | −0.419dB |
| SSIM / LPIPS | 0.80113 / 0.34930 | **0.80944 / 0.35248** | 혼재 |
| background update | 5,748 | 5,301 | −447 |
| final Gaussian | 68,970 | 68,513 | −457 |
| online wall | 97.283s | 97.403s | +0.120s |
| deadline margin | 0.367s | 0.247s | 둘 다 통과 |

고정 seed여도 실시간 idle scheduler가 실제 wall-time 여유에 따라 background step
수를 정하므로 bitwise deterministic하지 않다. 그럼에도 두 run 모두 기존 no-freeze
24.538dB보다 +0.809dB 이상 높아 freeze1050의 개선은 재현됐다. 1075는 Gaussian이
72,897개까지 늘었지만 품질이 낮았고, 1100은 late prune 뒤 52,649개로 크게 줄며
더 악화됐다. 즉 Gaussian 수의 단조 증가가 아니라 **충분한 late surface를 얻은 뒤
파괴적인 topology update 전에 고정하고 optical dense replay로 수렴시키는 시점**이
핵심이다.

새 strict best는 held-out **25.435dB**(반복 25.347dB), keyframe
27.548dB다. 두 run 모두 RGB+IMU-only, MPS 입력 0, fixed 1.5×,
post-stream optimizer update 0을 지켰다. held-out 27dB까지 **1.565dB**가
남아 있으므로 hard carve/pruning은 아직 실행하지 않는다.

산출물:

- `results/experiments/exp57_dense_trajfiller_offset4_residual_freeze1000_start650_late2_pgbacut1120_len1253_strict15x`
- `results/experiments/exp57_dense_trajfiller_offset4_residual_freeze1050_start650_late2_pgbacut1120_len1253_strict15x`
- `results/experiments/exp57_dense_trajfiller_offset4_residual_freeze1050_repeat_start650_late2_pgbacut1120_len1253_strict15x`
- `results/experiments/exp57_dense_trajfiller_offset4_residual_freeze1075_start650_late2_pgbacut1120_len1253_strict15x`
- `results/experiments/exp57_dense_trajfiller_offset4_residual_freeze1100_start650_late2_pgbacut1120_len1253_strict15x`

## 2026-07-29 추가 — post-freeze causal RGB 회수, offsets1+4 strict 26.129dB

freeze1050 성공을 해석하며 코드 경로를 다시 확인한 결과, 직전 절의 “freeze 뒤에도
late view supervision을 유지한다”는 설명은 부정확했다. 기본 scheduler는 frozen
map과 같은 coordinate state만 쓰려는 guard로 background `max_frame_idx`를
1049에 고정했고, 실제로는 frame1050 이후 도착 RGB를 학습하지 않았다.

한편 freeze 뒤 mapping packet은 완전히 버려지는 것이 아니라 `frozen_pose_only`로
PGBA의 pose/scale transform을 기존 Gaussian과 camera에 계속 적용한다. 따라서
post-freeze RGB도 현재 좌표계에서 causal하게 사용할 수 있다. 이를 명시적 opt-in
`--background_polish_allow_postfreeze_views`로 구현했다. 플래그가 없으면 기존
guard와 결과가 그대로 유지된다. 플래그가 있어도 아직 도착하지 않은 frame,
MPS pose/depth/point cloud, 종료 뒤 optimizer tail은 사용하지 않는다.

| freeze1050 strict 1.5× | pre-freeze offset4 | post-freeze offset4 | **post-freeze offsets1+4** |
|---|---:|---:|---:|
| held-out PSNR | 25.435 | 25.616 | **26.129** |
| keyframe PSNR | **27.548** | 27.019 | 27.152 |
| SSIM | 0.80113 | 0.81326 | **0.82804** |
| LPIPS | 0.34930 | 0.35349 | **0.33335** |
| background update | 5,748 | **5,720** | 5,576 |
| final Gaussian | 68,970 | 69,146 | 70,510 |
| online wall | **97.283s** | 97.258s | 97.309s |
| deadline margin | 0.367s | **0.392s** | 0.341s |

post-freeze offset4만으로 held-out +0.181dB를 얻었다. 더 중요한 변화는 offsets1+4다.
growing-map 600-frame 실험에서는 두 optical phase 혼합이 단일 offset4보다
−1.514dB였지만, topology를 1050에서 고정하고 post-freeze RGB까지 받는 현재
조건에서는 단일 offset4보다 **+0.513dB** 높았다. 충분한 geometry를 먼저 만든 뒤
topology 변화를 멈추면 추가 phase의 view-direction coverage가 pose-gradient
충돌보다 커지는 구간이 존재한다.

offsets1–4 전체도 동일 조건으로 실행했으나 frame1077 부근 background render에서
CUDA device-side assert가 발생했다. 평가까지 완주하지 못했으므로 PSNR 성공으로
간주하지 않고 판정 제외한다. 프로세스 종료 뒤 `nvidia-smi`에서 별도 GPU
프로세스가 없고 장치 상태가 정상임을 확인했다.

새 strict best는 held-out **26.129dB**, keyframe 27.152dB다. RGB+IMU-only,
MPS 입력 0, 평가용 offset0 supervision 제외, fixed 1.5×, post-stream update
0회를 모두 지켰다. 27dB까지 **0.871dB**가 남았으므로 hard carve/pruning은
아직 실행하지 않는다.

산출물:

- `results/experiments/exp57_dense_trajfiller_offset4_residual_freeze1050_postviews_start650_late2_pgbacut1120_len1253_strict15x`
- `results/experiments/exp57_dense_trajfiller_offsets14_residual_freeze1050_postviews_start650_late2_pgbacut1120_len1253_strict15x`
- 실패·판정 제외:
  `results/experiments/exp57_dense_trajfiller_offsets1234_residual_freeze1050_postviews_start650_late2_pgbacut1120_len1253_strict15x`

## 2026-07-29 추가 — dense-only maturity700, strict 최고 26.396dB

post-freeze offsets1+4의 random pool은 dense RGB 약 459장뿐 아니라 tracked
keyframe 약 106장도 함께 포함했다. keyframe PSNR은 이미 27dB대이고 frontier
mapper가 별도로 계속 학습하므로, idle background step만 causal dense RGB에
집중하는 `--background_polish_dense_only`를 추가했다.

| strict 1.5× | held-out / kf | SSIM / LPIPS | update | GS | online |
|---|---:|---:|---:|---:|---:|
| start650 mixed pool | 26.129 / 27.152 | 0.82804 / 0.33335 | 5,576 | 70,510 | 97.309s |
| start650 **dense-only** | **26.229 / 26.962** | **0.83428 / 0.32526** | 5,446 | 70,343 | 97.309s |
| dense-only start500 | 26.125 / 26.958 | 0.83063 / 0.32559 | 6,526 | 70,743 | 97.266s |
| **dense-only start700** | **26.396 / 27.299** | **0.83888 / 0.31609** | 5,112 | 70,320 | 97.290s |
| dense-only start750 | 26.328 / 27.041 | 0.83396 / 0.33055 | 4,445 | 70,230 | 97.298s |
| start700 반복 | 26.083 / 27.077 | 0.82774 / 0.32015 | 5,415 | 70,347 | 97.285s |

start500은 update를 1,414회 더 했지만 start700보다 −0.271dB였다. dense replay는
횟수보다 growing map maturity가 중요하며 start700이 현재 최고 경계다. 다만 동일
seed여도 wall-time idle scheduler와 candidate 도착 시점이 달라 반복 run은
26.083dB로 원 run보다 −0.313dB였다. 따라서 **단일 strict 최고는 26.396dB**로
기록하되 재현 가능한 범위가 26.08~26.40dB임을 숨기지 않는다.

주변 축도 다음과 같이 분리했다.

| start700 계열 | held-out / kf | 판정 |
|---|---:|---|
| random, late-iters2 | **26.396 / 27.299** | 채택 |
| random, late-iters1 | 26.304 / 27.102 | 기각 |
| round-robin | 22.754 / 23.276 | 강한 기각 |
| dense camera `full` pose/exposure | 25.452 / 26.274 | 기각 |
| post-freeze LR 1.25(start650) | 25.894 / 26.754 | 기각 |
| endpoint confidence 0.25(start650) | 25.800 / 26.966 | 기각 |
| freeze1000 + post-view(start650) | 25.729 / 27.072 | 기각 |

추가 phase에서 발생한 late CUDA assert도 조사했다. offsets1+2+4 및 1–4를 모두
trajectory-filler로 처리하면 keyframe 약 89/frame1077 부근에서 device-side
assert가 재현됐다. filler chunk 16→8, endpoint gate, Gaussian lock 직렬화로도
해결되지 않아 단순 batch 크기·rasterizer 동시성 가설은 기각했다. optical
trajectory-filler를 검증된 offsets1+4에만 적용하고 추가 offset은 causal endpoint
interpolation으로 남기는 `--background_dense_optical_offsets`를 구현하자 끝까지
안정적으로 완주했다. 그러나 offset2 추가는 25.737dB였다.

추가 interpolation offsets2+3이 geometry를 끌지 않도록
`--background_untrusted_dense_scope appearance_opacity`와 sampling fraction
0.2도 구현·검증했다. 안정적으로 913 dense view를 등록했지만 결과는
25.916/26.700dB로 기각했다. 추가 view는 geometry gradient를 막아도 제한된
optimizer step의 trusted optical supervision을 희석했다.

현재 채택 recipe는 Gaussian-only, optical offsets1+4, dense-only random,
start700, late-iters2, freeze1050, post-freeze causal RGB, PGBA cutoff1120이다.
최고 run과 반복 모두 RGB+IMU-only, MPS 입력 0, evaluator offset0 supervision
제외, fixed 1.5×, post-stream optimizer update 0을 지켰다. 27dB까지 단일
최고값 기준 **0.604dB**가 남아 hard carve/pruning은 계속 보류한다.

주요 산출물:

- 채택 최고:
  `results/experiments/exp57_dense_trajfiller_offsets14_denseonly_residual_freeze1050_postviews_start700_late2_pgbacut1120_len1253_strict15x`
- 반복:
  `results/experiments/exp57_dense_trajfiller_offsets14_denseonly_residual_freeze1050_postviews_start700_late2_repeat_pgbacut1120_len1253_strict15x`
- maturity:
  `results/experiments/exp57_dense_trajfiller_offsets14_denseonly_residual_freeze1050_postviews_start{500,750}_late2_pgbacut1120_len1253_strict15x`
- 기각:
  `results/experiments/exp57_dense_trajfiller_offsets14_denseonly_roundrobin_residual_freeze1050_postviews_start700_late2_pgbacut1120_len1253_strict15x`,
  `results/experiments/exp57_dense_trajfiller_offsets14_denseonly_full_residual_freeze1050_postviews_start700_late2_pgbacut1120_len1253_strict15x`,
  `results/experiments/exp57_dense_offsets1234_optical14_untrustedappop020_denseonly_freeze1050_postviews_start700_late2_pgbacut1120_len1253_strict15x`

## 2026-07-29 추가 — offset weighting·SH·camera 분해, 전부 기각

start700 Gaussian-only 채택점의 남은 0.604dB를 줄이기 위해 supervision phase,
view-dependent appearance, camera nuisance parameter를 각각 분리했다.

| strict 1.5× start700 계열 | held-out / kf PSNR | update | GS | online | 판정 |
|---|---:|---:|---:|---:|---|
| 채택점 원 run | **26.396 / 27.299** | 5,112 | 70,320 | 97.290s | 최고 |
| 채택점 반복 | 26.083 / 27.077 | 5,415 | 70,347 | 97.285s | 재현 범위 |
| offset weight 1:0.3, 4:0.7 | 26.133 / - | - | - | strict 통과 | 개선 없음 |
| SH degree 1 | 26.099 / - | - | - | strict 통과 | 기각 |
| SH degree 1 + `f_rest` LR 4× | 26.133 / - | - | - | strict 통과 | 기각 |
| per-view exposure-only + Gaussian | 25.650 / 26.471 | 4,926 | 70,214 | **97.282s** | 기각 |
| bounded pose-only + Gaussian | 25.724 / 26.592 | 3,633 | 70,279 | **97.258s** | 기각 |

offset4에 더 높은 sampling weight를 줘도 26.13dB였으므로 두 optical phase의 단순
비율 문제가 아니었다. SH degree 1을 즉시 활성화하고 `f_rest` 학습률까지 4배
올려도 degree 0보다 개선되지 않았다. 현재 view coverage와 step 예산에서는
추가 view-dependent coefficient가 일반화를 만들 만큼 수렴하지 않는다.

기존 camera `full`은 pose와 exposure를 동시에 움직여 25.452dB였기 때문에 두
요인을 별도로 구현해 재검증했다. per-view exposure-only는 25.650dB였다. 학습
뷰마다 별도 광도 자유도를 주면 Gaussian이 공통 appearance를 설명해야 할 압력이
약해지고, exposure parameter가 없는 held-out frame에 일반화되지 않았다.
pose-only는 exposure를 고정하고 view당 1mm/0.057도 이하의 bounded Adam step만
허용했지만 25.724dB였다. 추가 camera update 비용으로 Gaussian update가
3,633회까지 감소했고, photometric pose가 map residual을 따라가는 방향도
held-out geometry 개선으로 이어지지 않았다.

다섯 run 모두 RGB+IMU-only, MPS 입력 0, timestamp-causal replay, fixed 1.5×,
post-stream update 0을 유지했다. 따라서 offset weighting, SH1, background
camera pose/exposure refinement 축을 종료하고 Gaussian-only dense random
채택점을 유지한다. hard carve/pruning은 held-out 27dB 전까지 계속 보류한다.

추가 산출물:

- `results/experiments/exp57_dense_trajfiller_offsets14_w030070_denseonly_residual_freeze1050_postviews_start700_late2_pgbacut1120_len1253_strict15x`
- `results/experiments/exp57_sh1_dense_trajfiller_offsets14_denseonly_residual_freeze1050_postviews_start700_late2_pgbacut1120_len1253_strict15x`
- `results/experiments/exp57_sh1_frest4_dense_trajfiller_offsets14_denseonly_residual_freeze1050_postviews_start700_late2_pgbacut1120_len1253_strict15x`
- `results/experiments/exp57_exposure_dense_trajfiller_offsets14_denseonly_residual_freeze1050_postviews_start700_late2_pgbacut1120_len1253_strict15x`
- `results/experiments/exp57_poseonly_dense_trajfiller_offsets14_denseonly_residual_freeze1050_postviews_start700_late2_pgbacut1120_len1253_strict15x`

## 2026-07-29 추가 — background DSSIM weight 대칭 스캔, 0.2 유지

평가 목표가 held-out PSNR이므로 추가 연산 없이 background RGB loss의
`lambda_dssim`만 기존 0.2에서 0.1/0.3으로 바꿨다. frontier mapping과 evaluator는
수정하지 않았다.

| background `lambda_dssim` | held-out / kf | SSIM / LPIPS | update | GS | online |
|---:|---:|---:|---:|---:|---:|
| **0.2 원 run** | **26.396 / 27.299** | 0.83888 / 0.31609 | 5,112 | 70,320 | 97.290s |
| 0.2 반복 | 26.083 / 27.077 | 0.82774 / 0.32015 | 5,415 | 70,347 | 97.285s |
| 0.1 | 26.003 / 26.884 | 0.81913 / 0.34175 | 5,130 | 70,536 | **97.268s** |
| 0.3 | 26.232 / 27.148 | **0.83896 / 0.30885** | 5,100 | 70,357 | **97.271s** |

0.1은 모든 영상 지표가 나빠졌다. 0.3은 perceptual 지표는 좋았지만 목표 지표인
held-out PSNR이 원 run보다 −0.164dB였고, 0.2 반복 범위 안이었다. 따라서
background DSSIM weight는 기존 0.2를 유지하고 이 축을 닫는다. 두 run 모두 strict
RGB+IMU-only/MPS 없음/fixed 1.5×/zero-tail 계약을 통과했다.

산출물:

- `results/experiments/exp57_dssim010_dense_trajfiller_offsets14_denseonly_residual_freeze1050_postviews_start700_late2_pgbacut1120_len1253_strict15x`
- `results/experiments/exp57_dssim030_dense_trajfiller_offsets14_denseonly_residual_freeze1050_postviews_start700_late2_pgbacut1120_len1253_strict15x`

## 2026-07-29 추가 — grayscale geometry/RGB appearance 교대 기각

사용자 제안대로 causal dense RGB supervision의 gradient 역할을 분리했다. 실시간
예산을 유지하기 위해 한 render에서 두 번 backward하지 않고 background step을
1:1로 교대했다.

- geometry step: RGB를 luminance로 바꾸고 `xyz/scaling/rotation`만 갱신
- appearance step: RGB loss로 `opacity/f_dc/f_rest`만 갱신
- camera pose/exposure는 고정

full strict 결과는 held-out **25.439dB**, keyframe **26.314dB**, SSIM
0.81866, LPIPS 0.36650, 5,026 update, 70,225GS, **97.282s**였다. 동일한
약 5k update를 수행했는데도 joint Gaussian gradient 최고 26.396dB보다
−0.957dB였다. geometry와 opacity/color가 한 compositing residual에서 함께
움직여야 하며, 역할 분리는 각 parameter group의 유효 update를 절반으로 줄이는
손해를 상쇄하지 못했다. RGB+IMU-only/MPS 없음/fixed 1.5×/zero-tail 계약은
통과했지만 품질 기준으로 기각한다.

산출물:

- `results/experiments/exp57_splitgraygeom2_rgbapp_dense_trajfiller_offsets14_denseonly_residual_freeze1050_postviews_start700_late2_pgbacut1120_len1253_strict15x`

## 2026-07-29 추가 — per-view 진단과 post-freeze append-only PPM birth

평균 PSNR만으로 남은 갭의 위치를 추측하지 않도록 evaluator JSON에 per-view
frame/PSNR/SSIM/LPIPS/keyframe 여부를 추가했다. PNG를 저장하지 않는
`eval_metrics_only`에서도 지표만 남으므로 online loop 시간과 map update는
변하지 않는다. 채택 recipe를 다시 실행한 paired diagnostic control은
26.122/26.976dB, 5,141 update, 70,324GS, 97.279s였다.

| frame 구간 | paired control mean PSNR |
|---|---:|
| 0–199 | 26.353 |
| 200–399 | 27.699 |
| 400–599 | **28.474** |
| 600–799 | 27.323 |
| 800–999 | 26.444 |
| 1000–1199 | **22.782** |
| 1200–1252 | **18.884** |

freeze1050 이전 구간은 이미 26.4~28.5dB인데, 이후 신규 시야 coverage가
22.8→18.9dB로 무너지는 것이 전체 27dB의 직접 병목이었다. 이를 겨냥해
`--mapping_freeze_allow_births`를 구현했다.

- frame1050 이전 동작은 채택 recipe와 동일
- 이후 regular map/densify/prune는 계속 정지
- 새 tracked keyframe의 online depth에서 PPM-sampled Gaussian birth만 허용
- PGBA 좌표 갱신과 도착 dense RGB background replay는 유지
- MPS와 post-stream tail은 사용하지 않음

| strict 1.5× | held-out / kf | update | GS | online | 판정 |
|---|---:|---:|---:|---:|---|
| paired control | 26.122 / **26.976** | 5,141 | 70,324 | 97.279s | 기준 |
| append birth 1× | **26.312** / 26.106 | 4,969 | 92,043 | 97.277s | paired +0.190 |
| append birth 0.5× budget | 26.269 / 26.098 | 5,072 | 79,781 | 97.293s | 1×보다 미달 |
| append + recent 50% | 25.375 / 25.318 | 4,888 | 92,394 | 97.271s | 기각 |
| append + recent 15% | 26.142 / 26.007 | 5,057 | 91,973 | 97.265s | 기각 |

append 1×는 1000–1199 구간을 **22.782→23.386dB(+0.604)**로 올려 late
birth 방향의 인과 효과를 확인했다. 그러나 1200–1252는 18.884→18.949dB로
거의 변하지 않았다. 마지막 tracked keyframe 이후에는 online depth가 있는 신규
birth source가 없기 때문이다. PPM birth 예산을 절반으로 낮추면 전체도
−0.043dB라 과밀만이 병목은 아니었다.

post-freeze RGB를 강제 표집하면 recent50에서 1000–1199가 24.465dB,
1200–1252가 22.256dB로 크게 회복됐지만, 0–399와 800–999가 무너져 전체는
25.375dB였다. 약한 recent15도 26.142dB로 uniform append보다 낮았다. 제한된
step을 late view로 옮기는 방식은 신규 영역과 기존 영역의 전역 compositing 균형을
깨므로 종료한다.

append-only 1×는 paired control보다 낫지만 기존 단일 최고 26.396dB와 반복 범위
26.083~26.396dB를 확실히 넘지 못했고 keyframe 지표도 낮다. 따라서 아직 새
strict best로 채택하지 않는다. 다만 per-view 진단으로 남은 병목이 마지막
200-frame coverage임을 확정했으며, 다음 후보는 final non-keyframe에도 RGB-only로
online depth/birth evidence를 만드는 구조여야 한다. hard carve는 27dB 전까지
계속 보류한다.

산출물:

- paired control:
  `results/experiments/exp57_bestcontrol_perview_dense_trajfiller_offsets14_denseonly_residual_freeze1050_postviews_start700_late2_pgbacut1120_len1253_strict15x`
- append:
  `results/experiments/exp57_freeze1050_appendbirths_perview_dense_trajfiller_offsets14_denseonly_residual_postviews_start700_late2_pgbacut1120_len1253_strict15x`
- birth budget 절반:
  `results/experiments/exp57_freeze1050_appendbirths_ds2_perview_dense_trajfiller_offsets14_denseonly_residual_postviews_start700_late2_pgbacut1120_len1253_strict15x`
- recent:
  `results/experiments/exp57_freeze1050_appendbirths_recent050_perview_dense_trajfiller_offsets14_denseonly_residual_postviews_start700_late2_pgbacut1120_len1253_strict15x`,
  `results/experiments/exp57_freeze1050_appendbirths_recent015_perview_dense_trajfiller_offsets14_denseonly_residual_postviews_start700_late2_pgbacut1120_len1253_strict15x`

## 2026-07-29 추가 — final RGB 강제 keyframe, 단일 26.426dB·반복 미재현

마지막 tracked keyframe 뒤 frame1200–1252 coverage가 18.9dB에 머문 원인을 직접
겨냥했다. 기존 motion filter는 `is_last`여도 flow threshold를 넘지 않으면 마지막
RGB를 keyframe으로 만들지 않았다. `--force_final_keyframe` opt-in을 추가해 마지막
센서 프레임 도착 시 VIGS의 기존 online 경로인 Omnidata prior→frontend BA
depth→append-only PPM birth를 반드시 실행했다. 외부/MPS depth는 사용하지 않았다.

| strict 1.5× append birth | held-out / kf | update | GS | online |
|---|---:|---:|---:|---:|
| force-final 원 run | **26.426 / 26.304** | 5,395 | 92,201 | **97.370s** |
| force-final 반복 | **26.321 / 26.203** | 4,996 | 92,038 | **97.392s** |
| append-only 비교 | 26.312 / 26.106 | 4,969 | 92,043 | 97.277s |

원 run은 기존 단일 최고 26.396dB를 **+0.030dB** 경신했다. frame1200–1252도
append-only 18.949→**19.427dB**로 +0.478dB 개선됐고, 추가 keyframe 처리까지
deadline 97.65s를 0.280초 남기고 통과했다. 그러나 동일 설정 반복은
26.321dB로 append-only와 사실상 같은 범위였다. 개선폭이 실시간 scheduler와
frontend keyframe 변동보다 작으므로 **단일 최고 숫자는 26.426dB로 기록하되
recipe 개선으로 채택하지 않는다**.

두 run 모두 timestamp 순 RGB+IMU-only, MPS 입력 0, fixed 1.5×,
post-stream optimizer update 0을 지켰다. final keyframe 한 장은 마지막 endpoint
근처만 보강할 뿐, 200-frame 구간 전체의 다양한 시점을 채우지 못한다. 27dB까지
단일 최고 기준 0.574dB가 남았으며 hard carve는 계속 보류한다.

산출물:

- `results/experiments/exp57_freeze1050_appendbirths_forcefinalkf_perview_dense_trajfiller_offsets14_denseonly_residual_postviews_start700_late2_pgbacut1120_len1253_strict15x`
- `results/experiments/exp57_freeze1050_appendbirths_forcefinalkf_repeat_perview_dense_trajfiller_offsets14_denseonly_residual_postviews_start700_late2_pgbacut1120_len1253_strict15x`

## 2026-07-29 정정 — force-final 신기록은 held-out 누수로 판정 제외

직전 절을 평가 계약 관점에서 다시 감사한 결과, evaluator는 `idx%5==0`뿐 아니라
마지막 frame도 항상 평가한다. `--force_final_keyframe`은 바로 그 마지막 RGB를
Gaussian supervision/PPM birth에 사용했다. 따라서 26.426/26.321dB run은
RGB+IMU-only, 1.5×, zero-tail이라는 실행 계약은 지켰지만 **평가 이미지를 직접
학습했으므로 held-out 품질 기록으로는 무효**다. strict best를 26.396dB로
되돌리고 force-final 두 run을 판정 제외한다.

평가 프레임과 겹치지 않는 offset2의 1102/1152/1202만 강제 keyframe으로 만든
대체 run도 실행했다. legacy union mean은 **26.195dB**, fixed offset0 252-view
mean은 **26.317dB**, keyframe 26.043dB, 5,012 update, 92,128GS,
**97.378s**였다. 일부 forced keyframe은 frontend redundancy 제거로 남지 않았고,
품질도 append-only보다 낮아 기각한다.

### evaluator 지표 정의 추가 정정

`eval_rendering()`의 기존 `mean_psnr`은 고정 평가 frame뿐 아니라 모든 tracked
keyframe을 union으로 포함한다. 별도 `mean_psnr_kf`를 출력하면서도 union 값을
문서에서 “held-out”이라고 부른 것은 엄밀하지 않았다. 앞으로 JSON에 다음을
추가한다.

- `fixed_eval_mean_{psnr,ssim,lpips}`: frame `idx%5==0` + 마지막 frame,
  항상 동일한 252장
- `fixed_eval_keyframe_overlap_count`: 그 252장 중 tracker keyframe과 겹쳐
  Gaussian supervision에 들어갈 가능성이 있는 수
- per-view `is_fixed_eval_view`

기존 결과의 legacy union 값은 비교 연속성을 위해 보존하되, 진짜 held-out 성공
주장은 fixed evaluator frame을 Gaussian mapping supervision에서도 완전히 제외한
run으로만 한다. 현재 최신 run에서는 fixed 252장 중 keyframe overlap이 26장이라,
새 guard가 구현되기 전 수치는 **strict-disjoint held-out 증거가 아니다**.

## 2026-07-29 추가 — recent newborn-only gradient도 강한 기각

late RGB 강제 표집이 기존 지도를 직접 끌어 망치는 문제를 막기 위해, recent50
step에서는 `unique_kfIDs>=1050`인 append-only 신규 Gaussian만 별도 Adam으로
갱신했다. 나머지 uniform step은 기존처럼 전체 map을 학습했다.

결과는 legacy union **24.516/24.387dB**, fixed offset0 **24.612dB**,
SSIM 0.81305, LPIPS 0.36609, 4,777 update, 91,813GS, **97.272s**였다.
기존 Gaussian의 gradient/momentum을 막아도 신규 Gaussian 자체의 opacity와
geometry가 기존 표면 앞을 가려 0–999 구간까지 무너졌다. 따라서 row-wise gradient
격리만으로 visibility/compositing 충돌을 해결할 수 없으며 이 축을 종료한다.

산출물:

- non-evaluator forced keyframes:
  `results/experiments/exp57_freeze1050_appendbirths_forcekf1102_1152_1202_perview_dense_trajfiller_offsets14_denseonly_residual_postviews_start700_late2_pgbacut1120_len1253_strict15x`
- newborn-only recent:
  `results/experiments/exp57_freeze1050_appendbirths_recent050_newbornonly_perview_dense_trajfiller_offsets14_denseonly_residual_postviews_start700_late2_pgbacut1120_len1253_strict15x`

## 2026-07-29 추가 — mapping-side fixed-eval 제외, strict-disjoint 기준선 26.069dB

기존 evaluator union/keyframe overlap 문제를 끝내기 위해
`--mapping_exclude_fixed_eval_views`를 추가했다. fixed evaluator set인
frame `idx%5==0`과 마지막 frame은 tracker 입력과 최종 렌더 평가에는 남기되,
Gaussian 초기화·PPM birth·current/global window·background polish 후보에서는
전부 제외한다. frame0 제외 시 첫 trainable keyframe의 origin/depth가 여전히
`0`/`depth_packet[0]`을 쓰던 초기화 버그도 발견해 실제 `idx`와
`depth_packet[i]`를 사용하도록 수정했다.

기존 append-only PPM birth 채택점과 같은 설정을 이 guard로 재실행했다.

| strict-disjoint 1.5× | 결과 |
|---|---:|
| **fixed 252-view PSNR** | **26.0686dB** |
| fixed SSIM / LPIPS | 0.83314 / 0.33314 |
| legacy union / keyframe PSNR | 26.0062 / 25.8954dB |
| Gaussian update | 4,715 |
| Gaussian 수 | 78,534 |
| sensor loop | **97.238s / 97.65s** |
| post-stream update | **0** |
| fixed-eval mapping excluded | **true** |
| fixed-eval/keyframe 표기 overlap | 26 / 252 |

overlap 26장은 tracker가 keyframe으로 분류한 사실만 뜻하며, 새 guard 때문에
Gaussian supervision에는 들어가지 않았다. provenance도
`strict_aria_rgb_imu_only`, `mps_inputs=[]`,
`post_stream_refinement=false`를 확인했다. 따라서 **26.069dB를 최초의 유효한
strict-disjoint 기준선**으로 채택한다. 기존 legacy 최고 26.396dB는 비교 이력으로만
남기며 held-out best로 사용하지 않는다.

고정 평가 뷰의 200-frame 구간별 PSNR은 다음과 같다.

| frame | PSNR |
|---|---:|
| 0–199 | 26.033 |
| 200–399 | 27.615 |
| 400–599 | 27.743 |
| 600–799 | 26.812 |
| 800–999 | 26.206 |
| 1000–1199 | **23.723** |
| 1200–1252 | **20.334** |

27dB까지 **0.931dB**가 남았고, evaluation leakage를 제거해도 병목은 마지막
253-frame coverage다. 다음 품질 축은 평가 frame RGB를 직접 학습하지 않으면서
late non-eval RGB의 online depth/birth와 기존 map의 compositing 균형을 개선하는
것이다. 27dB 전 hard carve/floater pruning 보류 원칙은 유지한다.

산출물:

- `results/experiments/exp57_disjoint_eval5_freeze1050_appendbirths_v2_perview_dense_trajfiller_offsets14_denseonly_residual_postviews_start700_late2_pgbacut1120_len1253_strict15x`

## 2026-07-29 추가 — late appearance+opacity 전용 recent50 기각

late recent50의 전역 joint gradient가 기존 지도를 망친 원인을 geometry와
appearance로 분리했다. post-freeze recent step에만 xyz/scale/rotation gradient를
막고 color/SH/opacity만 갱신하는
`--background_postfreeze_recent_scope appearance_opacity`를 추가했다. 일반 random
step은 기존 all-Gaussian joint gradient를 유지했다.

strict-disjoint fixed 252-view 결과는 **25.4427dB**, SSIM/LPIPS
0.82323/0.35432, 4,743 update, 79,524GS, **97.268s**, tail update 0이었다.
기준선 26.0686dB보다 **−0.626dB**다. 마지막 frame1200–1252는
20.334→**21.192dB(+0.857)**로 회복했지만, 0–199는
26.033→**24.105dB(−1.928)**, 800–999는 −1.325dB,
1000–1199도 −0.406dB였다.

따라서 late-view 편향의 전역 손상은 geometry gradient가 주원인이 아니다.
같은 Gaussian의 color/opacity가 여러 시점의 compositing을 공유하므로 appearance만
허용해도 초기 영역이 무너진다. newborn-only와 appearance+opacity 격리를 모두
기각하고 recent forced-sampling 계열을 종료한다. 다음은 late view를 편향 표집하지
않고 정상 frontier joint update에 남기되 topology만 고정하는 방식이다.

산출물:

- `results/experiments/exp57_disjoint_recent050_appopacity_freeze1050_appendbirths_perview_dense_trajfiller_offsets14_denseonly_residual_postviews_start700_late2_pgbacut1120_len1253_strict15x`

## 2026-07-29 추가 — topology-only freeze1050 full 재확인도 기각

late view를 편향 표집하지 않고 regular mapping은 계속하되 frame1050부터
Gaussian birth/densify/prune만 막는 `--mapping_topology_freeze_after_frame 1050`을
full strict-disjoint로 실행했다. fixed 252-view 결과는 **25.4721dB**,
SSIM/LPIPS 0.81788/0.35779, 4,630 update, 66,588GS, **97.266s**, tail update
0이었다. 기준선 26.0686dB보다 **−0.597dB**다.

구간별 PSNR은 0–199부터 순서대로 25.731, 26.454, 28.111, 26.635,
25.637, **22.458**, **18.165dB**였다. frame1050 이후에도 기존 topology를
계속 움직이는 것만으로는 late coverage를 만들지 못하고 마지막 두 구간이 기준선보다
각각 −1.265/−2.169dB 악화됐다. 이는 앞서 600-frame에서 topology-freeze450이
22.461→17.135dB로 실패한 결과를 full에서도 재확인한 것이다. 같은 축을 다시
반복하지 않고, 채택 구조인 regular freeze1050 + append-only PPM birth를 유지한다.

provenance는 `strict_aria_rgb_imu_only`, `mps_inputs=[]`,
`fixed_eval_mapping_excluded=true`, `post_stream_refinement=false`를 모두
확인했다. 27dB 전 hard carve/floater pruning은 계속 보류한다.

산출물:

- `results/experiments/exp57_disjoint_topologyfreeze1050_perview_dense_trajfiller_offsets14_denseonly_residual_start700_late2_pgbacut1120_len1253_strict15x`

## 2026-07-29 추가 — non-eval final endpoint frame1249 강제 keyframe 기각

trajectory-filler가 오른쪽 tracked keyframe을 기다리기 때문에 마지막 미완료 구간의
dense RGB가 등록되지 않는 문제를 겨냥했다. evaluator의 마지막 frame1252 대신
고정 평가셋이 아닌 frame1249(`1249%5=4`)만 online keyframe으로 강제해 causal
interval을 닫고 append-only PPM birth를 추가했다.

frame1249는 실제 keyframe으로 승격됐고 causal dense 등록 수도 기준선 약 448장에서
**454장**으로 늘었다. strict-disjoint fixed 252-view는 **25.1443dB**,
SSIM/LPIPS 0.83141/0.32388, 4,621 update, 75,966GS, **97.298s**, tail update
0이었다. 기준선보다 전체 −0.924dB다.

| frame | 기준선 | force1249 | 변화 |
|---|---:|---:|---:|
| 0–199 | 26.033 | 25.198 | −0.834 |
| 200–399 | 27.615 | 26.283 | −1.332 |
| 400–599 | 27.743 | 26.173 | −1.570 |
| 600–799 | 26.812 | 25.759 | −1.053 |
| 800–999 | 26.206 | 24.990 | −1.216 |
| 1000–1199 | 23.723 | 23.582 | −0.141 |
| 1200–1252 | 20.334 | **21.413** | **+1.078** |

frame1249 intervention 전에 형성된 0–999까지 달라진 것은 parallel tracking/mapping의
run-to-run scheduler 분산이며 강제 endpoint의 인과 효과일 수 없다. 반면 마지막
구간 +1.078dB와 dense view +6장은 의도한 tail 보강 신호와 일치한다. 그래도
fixed eval 252장 중 마지막 bin은 12장뿐이라 좋은 baseline state에 결합해도 단순
가중 기대 이득은 약 **+0.051dB**에 불과하다. 0.931dB 갭의 주축으로는 부족하므로
recipe로 채택하거나 유리한 scheduler run을 골라내지 않는다.

provenance는 RGB+IMU-only, MPS 입력 0, fixed-eval mapping exclusion, fixed 1.5×,
zero-tail을 모두 통과했다. 다음은 endpoint 수보다 freeze 뒤 append된 PPM newborn을
도착 시점의 RGBD frontier supervision으로 안정적으로 정착시키는 방법을 검토한다.

산출물:

- `results/experiments/exp57_disjoint_forcekf1249_freeze1050_appendbirths_perview_dense_trajfiller_offsets14_denseonly_residual_postviews_start700_late2_pgbacut1120_len1253_strict15x`

## 2026-07-29 추가 — post-freeze PPM newborn RGBD 1-step, 미재현 신기록

freeze 이후 기존 코드를 감사한 결과 append-only PPM Gaussian은
`add_next_kf()`로 생성된 직후 `frozen_birth_only` return을 타며, 자신을 만든
keyframe의 BA depth/normal/RGB로 한 번도 frontier 최적화되지 않았다. 이를 해결하려고
`--mapping_freeze_birth_refine_iters`를 추가했다.

각 birth 직후 전체 map과 함께 렌더하되 fresh Adam과 exact appended-row mask를 사용해
방금 태어난 Gaussian만 ordinary frontier RGBD+normal+soft-carve loss로 1회 갱신한다.
기존 row는 zero-gradient뿐 아니라 fresh Adam이라 과거 momentum 이동도 없고,
camera/topology/densify/prune도 고정된다. 300-frame smoke에서 7개 birth를 정상
처리한 뒤 full strict-disjoint로 승격했다.

| strict-disjoint 1.5× | 기준선 | birth RGBD 1-step | 변화 |
|---|---:|---:|---:|
| **fixed 252-view PSNR** | 26.0686 | **26.3318** | **+0.2632dB** |
| fixed SSIM | 0.83314 | 0.83420 | +0.00106 |
| fixed LPIPS | 0.33314 | **0.29921** | −0.03393 |
| background update | 4,715 | 4,998 | +283 |
| Gaussian 수 | 78,534 | 75,068 | −3,466 |
| online loop | 97.238s | **97.267s** | +0.029s |
| post-stream update | 0 | 0 | 동일 |

13개 append-only keyframe birth에 각각 1-step이 실행됐다. provenance는
RGB+IMU-only, MPS 0, fixed-eval mapping exclusion, 1.5×, zero-tail을 모두
통과했다. 따라서 **26.332dB를 유효한 새 단일-run strict best**로 기록한다.

다만 intervention은 frame1050 이후인데 구간별 PSNR은
25.801/28.814/29.130/27.351/26.875/**22.279/18.801dB**였다. 상승은 주로
200–999에서 나왔고 직접 영향을 받는 1000–1252는 기준선보다 오히려 낮다.
즉 이 run의 +0.263dB를 newborn refine의 인과 효과로 아직 귀속할 수 없고 parallel
scheduler 분산이 크게 섞였다. 같은 설정 반복에서 전체와 late bin이 함께 유지되는지
확인하기 전에는 recipe로 채택하지 않는다. 27dB까지 단일-run 기준 0.668dB이며
hard carve/pruning은 계속 보류한다.

산출물:

- smoke: `results/experiments/exp57_disjoint_birthrefine1_freeze250_appendbirths_smoke300`
- full: `results/experiments/exp57_disjoint_birthrefine1_freeze1050_appendbirths_perview_dense_trajfiller_offsets14_denseonly_residual_postviews_start700_late2_pgbacut1120_len1253_strict15x`

## 2026-07-29 정정 — newborn RGBD 1-step은 paired control보다 낮아 기각

동일 refine=1 반복은 fixed **26.3604dB**, SSIM/LPIPS
0.84036/0.30014, 4,689 update, 75,164GS, **97.265s**, tail 0으로 첫
26.3318dB를 수치상 재현했다. 그러나 두 run 모두 intervention 전 구간이 과거
26.069 기준선보다 높아, 현재 코드/환경에서 `refine_iters=0` paired control을
추가 실행했다.

| 동일 시점 full | refine=1 원 run | refine=1 반복 | **paired refine=0** |
|---|---:|---:|---:|
| fixed PSNR | 26.3318 | 26.3604 | **26.4503** |
| fixed SSIM | 0.83420 | 0.84036 | **0.84346** |
| fixed LPIPS | 0.29921 | 0.30014 | **0.29784** |
| background update | 4,998 | 4,689 | 4,830 |
| GS | 75,068 | 75,164 | 75,003 |
| online | 97.267s | 97.265s | 97.287s |

refine=1은 paired control보다 각각 **−0.118/−0.090dB** 낮다. late bin도
paired control의 1000–1199/1200–1252 **23.274/19.124dB**보다 두 refine
run 평균이 낮았다. noisy online depth로 newborn geometry를 한 번 더 움직이는 것이
도움되지 않았다는 증거다. 따라서 기능 코드는 opt-in/default 0 자산으로 남기되
recipe에는 채택하지 않는다.

paired control은 모든 strict-disjoint 계약을 통과한 유효 run이므로 같은 기존 recipe의
새 단일 최고 **26.450dB**로 기록한다. 하지만 같은 recipe 분산 범위가
26.069~26.450dB이므로 27dB 성공은 단일 favorable run이 아니라 반복에서
재현되어야 한다. 현재 단일 최고 기준 갭은 0.550dB다.

산출물:

- refine repeat:
  `results/experiments/exp57_disjoint_birthrefine1_repeat_freeze1050_appendbirths_perview_dense_trajfiller_offsets14_denseonly_residual_postviews_start700_late2_pgbacut1120_len1253_strict15x`
- paired control:
  `results/experiments/exp57_disjoint_birthrefine0_paired_freeze1050_appendbirths_perview_dense_trajfiller_offsets14_denseonly_residual_postviews_start700_late2_pgbacut1120_len1253_strict15x`
