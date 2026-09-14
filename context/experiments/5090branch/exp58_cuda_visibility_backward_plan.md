# exp58 — CUDA 내부 visibility skip + `BACKWARD::preprocess` 최적화

- 상태: **진행 중 (2026-07-29), 첫 저위험 가지 기각**
- 이전 번호: exp56 Phase 9~11에서 `exp57` 후속으로 언급되던 구상을 **exp58로 이동**
- 선행: [exp57](exp57_causal_background_polishing_plan.md)에서 품질을 올리는 update
  구조를 먼저 검증한다. exp58은 그 update를 더 싸게 만들어 실시간 budget을 확보하는 속도 축이다.
- 기준선: exp56 Phase 11
  - `vigs_track_total`: 44.00s
  - held-out/keyframe PSNR: 23.46 / 23.98dB
  - rasterize avg/call: 66.8ms
  - backward avg/call: 368.5ms

## 배경

Phase 9 단일-view microbenchmark에서 gaussian 수 N의 영향은 forward 56.4%,
backward 84.6%로 확인됐다. 특히 backward의 N-slope이 forward보다 3.3배 커서
보이지 않는 gaussian을 backward에서 건너뛸 잠재 ROI가 크다.

하지만 Phase 10의 host-side `frustum_prefilter()`는 실패했다.

| | baseline | host-side filter |
|---|---:|---:|
| rasterize | 139.4ms | 290.5ms |
| backward | 348.9ms | 439.4ms |
| loss_compute | 434.9ms | 420.0ms |

원인은 gaussian tensor 5종을 view마다 boolean-indexing하면서 forward gather와
backward scatter 커널을 추가로 launch했기 때문이다. 따라서 **N을 줄이는 것**은
유효하지만 **Python/PyTorch에서 N을 줄이는 행위**는 공짜가 아니다.

Phase 11은 `renderCUDA`만 `grid.z=camera`로 batch화해 rasterize를 52.1% 줄였지만,
전체 이득은 3.9%였다. `loss_mapping.backward()` 안에서 지배적인
`BACKWARD::preprocess`와 SE3 pose gradient `dL_dtau`는 의도적으로 건드리지 않았다.

## 목표

추가 gather/scatter나 kernel launch 없이 visibility 판정을 기존 CUDA
`preprocessCUDA`/`BACKWARD::preprocess` 안에 융합하여:

1. 보이지 않는 gaussian의 forward/backward 연산을 skip한다.
2. `BACKWARD::preprocess`의 카메라별 반복과 launch 비용을 줄인다.
3. `dL_dtau`를 포함한 SE3 pose gradient 정확성을 보존한다.

## Phase 0 — 정확한 범위와 상한 재측정

- Phase 11 기준으로 CUDA event/wall-clock을 사용해 다음을 분리 계측:
  - forward preprocess/sort/render
  - backward render/computeCov2D/preprocess
  - `dL_dtau` 관련 구간
- profiler wrapper의 중복 합산을 피하고 `torch.cuda.synchronize()` wall-clock으로 교차검증.
- visibility 비율과 N을 함께 기록해 skip의 실측 상한을 계산.

### Phase 0a — fixed background view의 pose-gradient 생략 (기각)

strict exp57의 background polishing view는 pose를 optimizer로 갱신하지 않으므로,
`dL_dtau` 계산만 생략하면 `BACKWARD::preprocess`를 싸게 만들 수 있는지 먼저
마이크로벤치마크했다. rasterizer binding에 `compute_pose_grad` opt-in을 임시로
추가하고 false일 때 `dL_dtau=nullptr`를 넘겨 SE3 pose-gradient 수식을 건너뛰었다.

90,770 Gaussian, 1024² 고정 카메라에서 L1 RGB+depth backward를 비교한 결과:

| 항목 | 결과 |
|---|---:|
| forward image/depth | bit-exact |
| Gaussian grad 상대오차(xyz/fdc/opacity/scaling/rotation) | 1.82e-6 / 1.55e-7 / 8.76e-8 / 1.39e-6 / 3.65e-6 |
| full pose-grad | 3.0617ms/step |
| pose-grad 생략 | 3.1216ms/step |
| 절감률 | **−1.96% (오히려 느림)** |

즉 pose-gradient 계산만으로는 커널 구조/launch를 줄이지 못하고 분기만 추가되어
측정 잡음 이상의 이득이 없었다. 성공 기준에 크게 못 미쳐 1253 full replay 전에
중단했다. 임시 source patch를 전부 되돌리고 baseline extension을 재빌드했으며,
90,770 Gaussian 실제 render+backward에서 finite Gaussian gradient와 카메라
rotation/translation gradient가 다시 생성되는 것까지 확인했다.

**판정:** fixed-camera pose-gradient skip 단독 축은 기각. Phase 2의 가치는
여전히 카메라별 `BACKWARD::preprocess` 전체 launch/batch 구조를 바꾸는 데 있지,
SE3 산술 몇 줄만 조건부 생략하는 데 있지 않다.

## Phase 1 — 커널 내부 coarse visibility skip

- host-side tensor slicing 금지.
- full-N tensor와 full-N gradient index space를 유지.
- 기존 forward preprocess 안에서 camera frustum/near-plane 조건을 판정하고 invisible
  gaussian은 후속 covariance/SH/tile 작업을 즉시 return.
- margin sweep은 Phase 9 ROI 측정의 3.0을 출발점으로 하되, 기존 rasterizer의
  실제 visible 판정 대비 recall을 먼저 검증한다.

검증:

1. skip off vs 모든 점 keep에서 bit-exact
2. 실제 skip에서 forward image/depth 오차
3. visible gaussian parameter gradient와 full-N excluded gradient=0 확인
4. densification 통계의 index-space 정합성 확인

## Phase 2 — `BACKWARD::preprocess` batch/skip

가장 위험한 단계. `computeCov2DCUDA`/`BACKWARD::preprocess`의 `dL_dtau`를 직접 다룬다.

- 카메라별 intermediate는 유지하되 batch dimension으로 한 번에 launch할 수 있는지 검토.
- gaussian parameter gradient는 카메라 축으로 합산.
- pose gradient `dL_dtau`는 카메라별 독립 결과를 보존.
- atomic 합산 순서 변화에 따른 float32 비결정성을 별도 기준선으로 측정.

## 정확성 게이트

Phase 11보다 강한 검증이 필요하다.

1. raw binding forward/backward 단위 테스트
2. `render()` 반복 호출 자체의 atomic noise 기준선 측정
3. gaussian gradient:
   - xyz, opacity, scaling, rotation, SH
4. camera/pose gradient:
   - `dL_dtau` 카메라별 비교
   - finite-difference 또는 central-difference 교차검증
5. Python 통합 loss:
   - RGB, depth, normal을 모두 포함
   - 반환 tensor shape/leaf grad 확인
6. length=300 라이브 스모크
7. 1253 전체 held-out/시간/evo/floater 평가

어느 단계든 shape 오류, silent loss skip, pose gradient 불일치가 나오면 전체 런 전에 중단한다.

## 성공 기준

- backward avg/call **20% 이상 감소**
- 전체 온라인 루프 **10% 이상 추가 감소** 또는 exp57 polishing step을 유의미하게 늘릴 budget 확보
- held-out/keyframe PSNR 변화가 run-to-run noise 이내
- evo APE와 IMU 초기화 동작 악화 없음
- map() 성사 횟수 감소 없음

## 정지 조건

- visibility 판정 비용이 절감분을 상쇄
- `dL_dtau` 정확성을 finite-difference로 확인하지 못함
- backward 감소가 10% 미만이고 전체 루프 개선이 잡음 수준
- exp57이 품질 개선을 만들지 못해 추가 update budget 자체의 가치가 없음
