# exp57 — 실시간 품질 도약: causal background polishing + 정보량 기반 global replay

- 상태: **Phase 0 완료, Phase 1 1차 구현 기각/보류 (2026-07-29)**
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
