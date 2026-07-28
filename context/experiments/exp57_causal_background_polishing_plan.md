# exp57 — 실시간 품질 도약: causal background polishing + 정보량 기반 global replay

- 상태: **고정-map 30dB 상한 확인 / strict photo+IMU-only rolling·same-tensor freeze 모두 기각 (2026-07-29)**
- 기준선: exp56 Phase 11, `kernel_batch_render=true`
  - 순수 온라인 held-out/keyframe PSNR: **23.46 / 23.98dB**
  - 온라인 루프: **44.00s / 녹화 65.1s = 실시간 배수 0.68배**
  - 종료 후 26k 색정제 포함: exp56 유사 레시피 기준 held-out/keyframe **26.53 / 30.33dB**
- 목적: kernel micro-optimization만으로 몇 %를 더 줄이는 대신, 현재 확보한 실시간 여유를
  **프론티어를 방해하지 않는 인과적 전역 정제**에 재투자하여 순수 온라인 품질을 크게 올린다.
- 번호 변경: exp56 Phase 9~11에서 `exp57`로 부르던 CUDA 내부 visibility/
  `BACKWARD::preprocess` 후속은 [exp58](exp58_cuda_visibility_backward_plan.md)로 이동.

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

- 실시간 배수 **<1.0 유지**
- exp56 대비 held-out PSNR **+1.0dB 이상**
- keyframe PSNR만 상승하고 held-out이 정체하는 과적합이 아닐 것
- frontier map() 성사 횟수와 queue drop이 exp56보다 유의하게 악화되지 않을 것
- floater 지표/시각 품질 악화 없음

최종 목표:

- causal online 상태에서 held-out **26dB 이상**
- 후속 geometry 축과 결합해 배치급 30dB 방향으로 접근

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
