# exp57 — 실시간 품질 도약: causal background polishing + 정보량 기반 global replay

- 상태: **계획 (2026-07-28)**
- 기준선: exp56 Phase 11, `kernel_batch_render=true`
  - 순수 온라인 held-out/keyframe PSNR: **23.46 / 23.98dB**
  - 온라인 루프: **44.00s / 녹화 65.1s = 실시간 배수 0.68배**
  - 종료 후 26k 색정제 포함: exp56 유사 레시피 기준 held-out/keyframe **26.53 / 30.33dB**
- 목적: kernel micro-optimization만으로 몇 %를 더 줄이는 대신, 현재 확보한 실시간 여유를
  **프론티어를 방해하지 않는 인과적 전역 정제**에 재투자하여 순수 온라인 품질을 크게 올린다.
- 번호 변경: exp56 Phase 9~11에서 `exp57`로 부르던 CUDA 내부 visibility/
  `BACKWARD::preprocess` 후속은 [exp58](exp58_cuda_visibility_backward_plan.md)로 이동.

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
