# W&B Metric Guide

이 문서는 custom 3DGS floater 실험에서 W&B에 기록되는 metric을 해석하기 위한 가이드입니다.

## 로깅 주기

기본 로깅 주기:

- `ambiguity_log_interval`: 2000 iteration마다 기록
- `gaussian_metrics_log_interval`: 2000 iteration마다 기록, 마지막 iteration에도 한 번 더 기록

기본 threshold:

- `low_opacity_threshold`: `0.1`
- `large_scale_threshold`: `0.1`
- `softmax_depth_beta`: `5.0`

현재 실험 스크립트가 사용하는 full OpenMAVIS 301_1253 dataset:

```text
/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253
```

## Ambiguity Metrics

이 metric들은 SparseGS의 아이디어를 가져온 것입니다. floater는 한 픽셀 안에서 여러 depth가 섞일 때 자주 나타난다고 보고, 렌더러에서 다음 값을 뽑습니다.

- `alpha_depth`: 해당 픽셀에 기여한 Gaussian depth의 alpha-weighted 평균
- `modes`: 해당 픽셀에서 가장 강하게 기여한 Gaussian 하나의 depth

ambiguity map은 다음처럼 계산합니다.

```text
diff = (alpha_depth - modes) / normalized_depth_denominator
```

이 중 `diff > 0`인 픽셀만 ambiguity 후보로 봅니다.

### `ambiguity/mean_positive`

`diff > 0`인 픽셀들만 모아서 평균낸 값입니다.

해석:

- 낮을수록 대체로 좋습니다.
- 값이 높으면 ambiguity가 생긴 픽셀들에서 depth 불일치가 크다는 뜻입니다.
- 평균적인 floater severity를 볼 때 가장 먼저 확인할 수 있는 값입니다.

### `ambiguity/p95`

positive ambiguity 값의 95 percentile입니다.

해석:

- 낮을수록 대체로 좋습니다.
- `ambiguity/max`보다 outlier에 덜 민감합니다.
- 실험 간 floater severity를 비교할 때 유용합니다.

### `ambiguity/max`

positive ambiguity 중 최댓값입니다.

해석:

- 낮을수록 대체로 좋습니다.
- 단 하나의 나쁜 픽셀이나 numerical outlier에 매우 민감합니다.
- 이 값만 보고 실험을 판단하면 위험합니다.

### `ambiguity/positive_ratio`

전체 유효 픽셀 중 `diff > 0`인 픽셀 비율입니다.

해석:

- 낮을수록 대체로 좋습니다.
- 값이 높으면 ambiguity가 화면 전반에 넓게 퍼져 있다는 뜻입니다.
- 이 값은 높지만 `p95`가 낮다면, 심한 floater라기보다 약한 depth mixing이 넓게 있는 상황일 수 있습니다.

### `ambiguity/dip`

positive ambiguity 분포에 대한 Hartigan dip statistic입니다.

해석:

- 값이 높을수록 ambiguity 분포가 여러 peak를 가진다는 뜻입니다.
- 정상 픽셀 분포와 floater 픽셀 분포가 분리되면 이 값이 커질 수 있습니다.
- 주 판단 metric보다는 보조 진단 metric으로 보는 것이 좋습니다.

### `ambiguity/map`

positive ambiguity를 정규화해서 이미지로 저장한 것입니다.

해석:

- 밝은 영역일수록 depth disagreement가 큰 픽셀입니다.
- foreground/background 경계 근처가 밝은 것은 어느 정도 자연스러울 수 있습니다.
- 빈 공간이나 벽 앞에 독립적인 밝은 blob이 보이면 floater 후보로 의심할 수 있습니다.

## Train Image Metrics

### `train/psnr`

로깅 iteration에서 샘플된 training view 하나에 대한 PSNR입니다.

해석:

- 높을수록 RGB 재구성이 좋습니다.
- 전체 validation score가 아니라 현재 샘플된 train view 기준입니다.
- 단일 값보다 추세를 보는 것이 좋습니다.

### `train/ssim`

로깅 iteration에서 샘플된 training view 하나에 대한 SSIM입니다.

해석:

- 높을수록 좋습니다.
- PSNR과 같이 봐야 합니다.
- floater가 줄어도 RGB metric 변화는 작을 수 있습니다.

### `train/l1_loss`

현재 training view의 RGB L1 reconstruction loss입니다.

해석:

- 낮을수록 좋습니다.

### `train/total_loss`

해당 iteration에서 실제 optimization에 사용된 전체 loss입니다.

해석:

- 낮을수록 대체로 좋습니다.
- 다만 depth loss나 다른 regularization term이 포함될 수 있습니다.
- loss 구성이 같은 실험끼리만 직접 비교하는 것이 안전합니다.

## Gaussian Structure Metrics

이 metric들은 현재 Gaussian set 자체의 구조를 요약합니다.

### `gaussian/count`

현재 Gaussian 총 개수입니다.

해석:

- 낮다고 무조건 좋은 것은 아닙니다.
- 너무 높으면 densification이 과도하게 일어났을 가능성이 있습니다.
- 너무 낮으면 scene을 충분히 표현하지 못할 수 있습니다.

### `gaussian/low_opacity_count`

opacity가 `low_opacity_threshold`보다 작은 Gaussian 개수입니다.

기본 기준:

```text
opacity < 0.1
```

해석:

- reconstruction 품질이 유지된다는 전제에서는 낮을수록 좋습니다.
- low opacity Gaussian이 많으면 약하게 남아 있는 floater 또는 거의 쓰이지 않는 Gaussian이 많다는 신호일 수 있습니다.

### `gaussian/low_opacity_ratio`

전체 Gaussian 중 low opacity Gaussian의 비율입니다.

```text
low_opacity_count / gaussian_count
```

해석:

- 낮을수록 대체로 좋습니다.
- raw count보다 실험 간 비교에 적합합니다.
- 이전 표에서 `dens_sparse_s5`가 유망해 보였던 이유 중 하나가 이 비율이 크게 낮아진 점입니다.

### `gaussian/large_scale_count`

가장 큰 scale 축이 `large_scale_threshold`보다 큰 Gaussian 개수입니다.

기본 기준:

```text
max(scale_x, scale_y, scale_z) > 0.1
```

해석:

- 낮을수록 좋은 경우가 많지만, 항상 그렇지는 않습니다.
- 넓은 벽이나 바닥 같은 영역에서는 큰 Gaussian이 정상적으로 필요할 수 있습니다.
- 값이 높고 동시에 render에서 blob/haze가 보이면 over-spread floater 가능성이 있습니다.

### `gaussian/large_scale_ratio`

전체 Gaussian 중 large scale Gaussian의 비율입니다.

```text
large_scale_count / gaussian_count
```

해석:

- raw count보다 실험 간 비교에 적합합니다.
- 반드시 `gaussian/count`와 같이 봐야 합니다.
- sparse한 run은 전체 Gaussian 수가 적어서 large scale ratio가 상대적으로 높게 나올 수 있습니다.

### `gaussian/opacity_median`

활성화된 opacity의 median입니다.

해석:

- 높을수록 typical Gaussian이 더 불투명하다는 뜻입니다.
- 너무 낮으면 약한 Gaussian이 많다는 신호일 수 있습니다.
- 너무 높으면 opacity reset이나 densification 동작이 크게 바뀐 것일 수 있습니다.

### `gaussian/scale_median`

각 Gaussian의 3축 scale 중 가장 큰 값의 median입니다.

해석:

- 낮을수록 typical Gaussian이 작다는 뜻입니다.
- sparse model에서는 값이 조금 높아도 정상일 수 있습니다.
- `large_scale_ratio`와 같이 봐야 합니다.

### `gaussian/nearest_orb_median`

각 Gaussian 중심에서 가장 가까운 `sparse/0/points3D` point까지의 거리 median입니다.

해석:

- 낮을수록 Gaussian들이 sparse reconstruction support 근처에 머문다는 뜻입니다.
- 높을수록 Gaussian들이 ORB/COLMAP sparse geometry에서 멀리 drift했다는 뜻입니다.
- 아주 초기 smoke test에서는 Gaussian이 sparse point에서 시작하므로 `0.0`이 나올 수 있습니다.

## 실험 판단 순서

floater 감소 실험을 볼 때는 다음 순서로 보는 것이 좋습니다.

1. `train/psnr`, `train/ssim`이 무너지지 않았는지 확인합니다.
2. `ambiguity/p95`, `ambiguity/mean_positive`를 비교합니다.
3. `gaussian/low_opacity_ratio`를 비교합니다.
4. `gaussian/count`로 densification이 얼마나 일어났는지 확인합니다.
5. `gaussian/large_scale_ratio`, `gaussian/scale_median`, `gaussian/nearest_orb_median`을 보조 진단으로 봅니다.
6. 최종 판단 전에는 반드시 `ambiguity/map`과 render 결과를 눈으로 확인합니다.

## 주의할 점

- Gaussian 수가 적다고 무조건 좋은 것은 아닙니다.
- ambiguity가 낮아도 PSNR/SSIM이 무너지면 좋은 실험이 아닙니다.
- `dens_sparse` 계열은 low-opacity floater를 줄이면서도 `large_scale_ratio`가 올라갈 수 있으므로 visual 확인이 필요합니다.
- 실험 비교는 같은 dataset, 같은 iteration 수, 같은 threshold 기준에서 해야 합니다.
