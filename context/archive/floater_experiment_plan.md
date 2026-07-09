# Floater Reduction Experiment Plan

## 목표

OpenMAVIS 기반 301_1253 trajectory로 3DGS를 학습하면서, floater를 줄이되 RGB 품질을 유지하거나 개선하는 학습 설정을 찾는다.

최종 목표는 단일 metric 최적화가 아니라 다음 조건을 동시에 만족하는 설정을 찾는 것이다.

1. render 품질이 유지된다.
2. floater가 시각적으로 줄어든다.
3. Gaussian 구조 metric이 악화되지 않는다.
4. 학습이 재현 가능하다.

## 현재 사용 가능한 자원

### Main repo

```text
/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/repos/main/3dgs-custom
```

### Reference repo

```text
/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/repos/reference/SparseGS
```

SparseGS reference에는 다음 아이디어가 구현되어 있다.

- softmax/depth mode 기반 floater ambiguity
- `alpha_depth`와 `modes`의 차이를 이용한 floater 후보 탐지
- depth ambiguity 기반 pruning

현재 main repo에는 metric 로깅용으로 필요한 최소 기능만 이식되어 있다.

### Dataset

현재 full dataset 후보:

```text
/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253
```

확인된 규모:

```text
images: 1311
sparse/0/images.txt entries: 1311
```

기존에 잘못 사용했던 57장 batch dataset:

```text
/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/rgb_3dgs_openmavis_batch_301_1253
```

이 경로는 full 실험에는 사용하지 않는다.

## 현재 W&B Metric

자세한 해석은 다음 문서를 따른다.

```text
docs/wandb_metric_guide.md
```

주요 판단 metric:

- `train/psnr`
- `train/ssim`
- `ambiguity/mean_positive`
- `ambiguity/p95`
- `ambiguity/positive_ratio`
- `gaussian/count`
- `gaussian/low_opacity_ratio`
- `gaussian/large_scale_ratio`
- `gaussian/opacity_median`
- `gaussian/scale_median`
- `gaussian/nearest_orb_median`

## 기본 판정 원칙

### 품질 유지 조건

baseline 대비 다음을 확인한다.

- `train/psnr`이 크게 하락하지 않을 것
- `train/ssim`이 크게 하락하지 않을 것
- render 결과에서 blur, hole, underfit이 심해지지 않을 것

PSNR/SSIM은 현재 train sample 기준이므로 절대값보다 추세와 비교를 우선한다.

### floater 감소 조건

다음이 좋아지는지 본다.

- `ambiguity/p95` 감소
- `ambiguity/mean_positive` 감소
- `gaussian/low_opacity_ratio` 감소
- `ambiguity/map`에서 독립적인 blob 감소

### 구조 안정성 조건

다음이 과하게 악화되지 않아야 한다.

- `gaussian/large_scale_ratio` 과도 증가
- `gaussian/nearest_orb_median` 과도 증가
- `gaussian/count` 폭증

`dens_sparse`류 실험은 Gaussian 수가 줄면서 `large_scale_ratio`가 증가할 수 있으므로 render 확인이 필수다.

## 실험 루프

각 loop는 다음 순서로 진행한다.

1. 이전 실험 결과 요약
2. 다음 가설 1개 선택
3. 실험 설정 1-3개 생성
4. 학습 실행
5. W&B metric 및 local result 확인
6. render/ambiguity map 시각 확인
7. 결론 작성
8. 다음 가설 갱신

한 loop에서 너무 많은 변수를 동시에 바꾸지 않는다. 기본 원칙은 one-factor-at-a-time이다.

## Baseline

### `exp01_openmavis_full_baseline`

목적:

- full OpenMAVIS 301_1253 dataset 기준점 생성

설정:

```text
dataset=mavis_301_1253_full
train=quality
logging=wandb
iterations=30000
```

판정:

- 이후 모든 실험의 기준선
- metric뿐 아니라 render 결과와 point cloud 상태를 저장

## 1차 가설: Densification이 floater를 만든다

### 배경

기존 stride-5 실험에서 `dens_sparse_s5`가 가장 유망했다.

기존 설정:

```text
--densification_interval 200
--densify_grad_threshold 0.0004
```

관찰:

- Gaussian 수가 크게 감소
- low opacity 비율 감소
- large scale 비율 증가
- visual 확인 필요

### 실험 1

#### `exp02_openmavis_full_dens_sparse`

목적:

- full dataset에서도 sparse densification이 floater를 줄이는지 확인

설정:

```text
dataset=mavis_301_1253_full
train=quality
train.densification_interval=200
train.densify_grad_threshold=0.0004
```

기대:

- `gaussian/count` 감소
- `gaussian/low_opacity_ratio` 감소
- `ambiguity/p95` 감소

리스크:

- underfit
- large Gaussian 증가
- thin structure 손실

## 2차 가설: Densification 시작/종료 시점이 floater에 영향 준다

### 실험 후보

#### `exp03_dens_late`

목적:

- 초반 geometry가 불안정할 때 densification이 floater seed를 만드는지 확인

설정:

```text
train.densify_from_iter=1500
```

기대:

- 초기 floater seed 감소
- 품질 하락은 작을 가능성

#### `exp04_dens_short`

목적:

- 후반 densification이 늦게 생기는 floater를 만드는지 확인

설정:

```text
train.densify_until_iter=7000
```

기대:

- 후반 floater 감소

리스크:

- detail 부족
- PSNR/SSIM 하락

#### `exp05_dens_late_sparse`

목적:

- sparse densification과 늦은 densification 시작의 조합 확인

설정:

```text
train.densify_from_iter=1500
train.densification_interval=200
train.densify_grad_threshold=0.0004
```

주의:

- 조합 실험이므로 `exp02`, `exp03` 결과를 본 뒤 실행한다.

## 3차 가설: Pruning threshold가 floater 제거를 충분히 못 한다

### 배경

현재 기본 pruning은 opacity 기반이 강하다.

관련 코드:

```text
gaussians.densify_and_prune(opt.densify_grad_threshold, 0.005, ...)
```

여기서 `0.005`는 min opacity threshold 역할을 한다.

### 필요한 코드 개선

현재 min opacity threshold가 config로 노출되어 있지 않다면 다음을 추가한다.

```text
train.min_opacity_prune_threshold
```

기본값:

```text
0.005
```

### 실험 후보

#### `exp06_prune_opacity_001`

설정:

```text
train.min_opacity_prune_threshold=0.01
```

기대:

- low opacity floater 감소

리스크:

- valid weak Gaussian 제거
- thin region 품질 저하

#### `exp07_prune_opacity_002`

설정:

```text
train.min_opacity_prune_threshold=0.02
```

주의:

- aggressive pruning
- `exp06` 결과가 유망할 때만 실행

## 4차 가설: Opacity reset 정책이 local minima에 영향 준다

### 배경

opacity reset은 Gaussian이 다시 경쟁하도록 만드는 역할을 한다. 너무 잦으면 학습이 흔들리고, 너무 드물면 floater가 굳어질 수 있다.

### 실험 후보

#### `exp08_opreset_slow`

설정:

```text
train.opacity_reset_interval=6000
```

기존 stride-5에서는 비추천이었으나 full dataset에서 재확인할 가치가 있다.

#### `exp09_opreset_fast`

설정:

```text
train.opacity_reset_interval=1500
```

목적:

- floater가 early local minima로 굳기 전에 reset을 더 자주 걸면 개선되는지 확인

리스크:

- 수렴 불안정
- PSNR/SSIM 하락

## 5차 가설: LR/Optimizer가 floater local minima에 영향 준다

### 배경

floater는 geometry/opacity/scale이 잘못된 local minima에 빠진 결과일 수 있다.

우선적으로 볼 파라미터:

- `position_lr_init`
- `position_lr_final`
- `scaling_lr`
- `opacity_lr`
- `optimizer_type`

### 실험 후보

#### `exp10_pos_lr_low`

목적:

- xyz가 너무 크게 움직여 sparse prior에서 벗어나는지 확인

설정:

```text
train.position_lr_init=0.00008
train.position_lr_final=0.0000008
```

기대:

- `nearest_orb_median` 감소
- floater 감소 가능

리스크:

- geometry refinement 부족
- PSNR 하락

#### `exp11_scale_lr_low`

목적:

- scale이 커지며 floater blob을 만드는지 확인

설정:

```text
train.scaling_lr=0.0025
```

기대:

- `large_scale_ratio` 감소

리스크:

- coverage 부족

#### `exp12_opacity_lr_low`

목적:

- opacity가 불안정하게 커지거나 reset 후 회복 과정에서 floater가 생기는지 확인

설정:

```text
train.opacity_lr=0.0125
```

기대:

- opacity 변화 안정화

리스크:

- 수렴 느려짐

#### `exp13_sparse_adam`

목적:

- SparseGaussianAdam 사용 시 visible Gaussian 중심 업데이트가 floater에 영향을 주는지 확인

설정:

```text
train.optimizer_type=sparse_adam
```

주의:

- 현재 수정된 rasterizer와 SparseAdam 호환 여부를 smoke test로 먼저 확인해야 한다.

## 6차 가설: Sparse point prior를 쓰면 geometry drift가 줄어든다

### 배경

OpenMAVIS/ORB sparse points는 완벽한 GT는 아니지만, Gaussian이 sparse geometry에서 크게 벗어나는 것을 막는 prior로 쓸 수 있다.

현재 metric:

```text
gaussian/nearest_orb_median
```

이 값은 사후 진단용이다. 다음 단계는 이를 loss 또는 pruning 기준으로 활용하는 것이다.

### 구현 후보

#### Sparse point distance regularization

개념:

```text
loss_sparse_prior = median_or_mean_distance_to_nearest_sparse_point
```

실제 구현에서는 모든 Gaussian에 대해 매 iteration KD-tree query를 하면 비싸므로 다음 방식을 고려한다.

- N iteration마다 일부 Gaussian sample만 사용
- CUDA `torch.cdist` chunking
- sparse points를 GPU tensor로 유지

설정 후보:

```text
train.sparse_prior_weight_init=0.01
train.sparse_prior_weight_final=0.002
train.sparse_prior_sample_count=8192
train.sparse_prior_interval=10
```

주의:

- sparse points 자체에 noise가 있으면 잘못된 geometry로 끌릴 수 있다.
- final RGB 품질과 visual 결과를 반드시 확인해야 한다.

#### Sparse support pruning

개념:

```text
nearest_sparse_distance가 너무 큰 low-opacity Gaussian 제거
```

초기 후보 조건:

```text
opacity < 0.1
nearest_sparse_distance > percentile threshold
```

이 방식은 직접 loss보다 더 공격적이므로, metric 분석 후 후순위로 진행한다.

## 7차 가설: SparseGS pruning을 main으로 이식하면 직접 floater 제거가 가능하다

### 배경

현재 main에는 SparseGS ambiguity metric만 들어와 있다. SparseGS reference에는 ambiguity 기반으로 실제 Gaussian을 선택하고 prune하는 로직이 있다.

참고 위치:

```text
repos/reference/SparseGS/train.py
repos/reference/SparseGS/utils/prune_utils.py
```

### 필요한 출력

metric만으로는 부족하고, 실제 pruning에는 다음 출력이 필요하다.

- `mode_id`
- `point_list`
- `means2D`
- `conic_opacity`

현재 main은 metric용으로 `alpha_depth`, `modes`만 사용한다.

### 단계

1. SparseGS pruning 로직을 더 읽고 main rasterizer 출력 확장 범위를 확정한다.
2. pruning을 바로 학습 loop에 넣지 말고 offline diagnostic으로 먼저 구현한다.
3. 특정 checkpoint에서 ambiguity mask와 prune 후보 Gaussian을 저장한다.
4. visual 결과가 맞으면 학습 중 pruning으로 확장한다.

## 실험 결과 기록 형식

각 실험이 끝나면 다음 형식으로 docs 또는 results에 요약한다.

```text
실험 이름:
목적:
설정:
W&B run:
최종 PSNR:
최종 SSIM:
ambiguity/p95:
ambiguity/mean_positive:
gaussian/count:
gaussian/low_opacity_ratio:
gaussian/large_scale_ratio:
gaussian/nearest_orb_median:
visual 판단:
다음 액션:
```

## 당장 실행할 1차 실험 큐

현재 바로 실행할 실험:

1. `exp01_openmavis_full_baseline`
2. `exp02_openmavis_full_dens_sparse`

스크립트:

```text
scripts/experiments/run_exp01_exp02_openmavis_full.sh
```

이 두 실험이 끝나면 먼저 다음을 비교한다.

- PSNR/SSIM
- ambiguity metric
- Gaussian 구조 metric
- rendered output
- ambiguity map

그 결과에 따라 다음 중 하나로 진행한다.

- `dens_sparse`가 유망하면 densification/pruning 세부 sweep
- 품질이 무너지면 LR/optimizer 안정화 실험
- ambiguity는 낮지만 visual이 나쁘면 scale/pruning control 실험
- `nearest_orb_median`이 크게 증가하면 sparse prior 실험

## 확정된 운영 기준

2026-06-16 기준으로 다음 사항을 확정했다.

### Dataset

full 기준 dataset은 1311장짜리 `0416_Data__0416_301-1253`를 사용한다.

```text
/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253
```

### Iteration 운영

모든 실험을 무조건 30000 iteration까지 돌리지 않는다.

운영 방식:

1. 중요한 기준 실험은 30000까지 돌린다.
2. 후보 실험은 중간 metric을 보고 계속 돌릴지 판단한다.
3. 명백히 품질이 무너지거나 floater metric이 악화되면 조기 중단 후보로 본다.
4. 유망한 실험만 30000까지 밀고 간다.

중간 판단에 사용할 주요 checkpoint:

```text
7000
15000
30000
```

### Visual 평가

visual 평가는 trajectory에서 약간 offset을 둔 view set을 만들어 고정한다.

구현 방향:

1. train camera trajectory에서 일정 간격으로 anchor frame을 고른다.
2. 각 anchor pose에 작은 translation/rotation offset을 준다.
3. 같은 offset view set으로 모든 실험을 렌더링한다.
4. train view 재구성뿐 아니라 novel-ish view에서 floater가 보이는지 확인한다.

이 view set 생성/렌더링 유틸은 1차 실험 이후 추가한다.

### Threshold

초기 기준은 기존 표와 맞춰 다음 값을 유지한다.

```text
low_opacity_threshold=0.1
large_scale_threshold=0.1
```

다만 metric 분포가 full dataset에서 다르게 보이면 중간에 기준을 재검토한다.

### 자동 루프

별도 시간 제한은 두지 않는다. 사용자가 필요하다고 판단하면 중단한다.

실험 루프는 다음 원칙으로 계속 진행한다.

1. 한 번에 너무 많은 변수를 바꾸지 않는다.
2. W&B metric, local JSON, render 결과를 보고 다음 가설을 고른다.
3. 실험 결과가 명확히 나쁘면 해당 방향은 중단한다.
4. 좋은 후보는 30000 iteration까지 검증한다.
