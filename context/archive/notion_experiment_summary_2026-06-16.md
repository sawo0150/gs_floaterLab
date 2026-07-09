# 3DGS Floater Reduction 실험 정리

작성일: 2026-06-16  
대상 데이터셋: `0416_Data__0416_301-1253` full OpenMAVIS trajectory, 1311 images  
W&B project: [`geekseek/3dgs-keyframe`](https://wandb.ai/geekseek/3dgs-keyframe)

## 목적

OpenMAVIS 301_1253 trajectory를 3DGS로 학습할 때 생기는 floater를 줄이면서 RGB 품질을 최대한 유지하는 학습 설정을 찾는다.

이번 라운드에서는 다음 축을 순서대로 검증했다.

- densification 빈도와 threshold
- scale learning rate
- opacity pruning threshold
- Adam beta1 momentum
- densification 종료 시점
- position learning rate
- sparse depth prior

## 현재 결론

현재까지 가장 좋은 균형 후보는 `exp08_openmavis_full_dens_until7000_prune001_beta1_low`다.

`exp08`은 PSNR 33.012를 유지하면서 Gaussian 수와 low-opacity Gaussian을 크게 줄였다. `exp10`, `exp11`은 구조 metric은 더 좋아졌지만 position LR 감소 때문에 PSNR이 0.33-0.44 dB 떨어져 최종 후보로는 보류한다.

`exp12`에서 sparse depth prior를 실제 loss로 연결했지만, 현재 weight 설정(`0.01 -> 0.002`)은 exp08보다 PSNR과 floater 구조 metric이 모두 나빠졌다. 따라서 sparse prior 아이디어 자체는 유지하되, 현재 강도와 적용 방식은 비추천이다.

다음 가설은 sparse prior를 더 약하게 쓰거나, 초반부터 강하게 거는 대신 densification 이후에 약하게 켜는 delayed sparse prior 방식이다.

## 핵심 실험 표

| Exp | W&B | 가설 | 주요 설정 | 상태 | PSNR | Gaussian 수 | Low opacity 비율 | Large scale 비율 | Opacity median | Scale median | Nearest ORB median | 판단 |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| exp01 | - | full baseline 기준선 | default full dataset | 완료 | 기록 유실 | 886,441 | 0.5191 | 0.0584 | 0.0942 | 0.0319 | 0.1264 | 기준선. train log가 중복 실행으로 덮여 PSNR은 현재 비교 불가 |
| exp02 | [`985e50q9`](https://wandb.ai/geekseek/3dgs-keyframe/runs/985e50q9) | densification이 너무 자주/쉽게 일어나 floater를 만든다 | `densification_interval=200`, `densify_grad_threshold=0.0004` | 완료 | 33.377 | 477,601 | 0.4827 | 0.0931 | 0.1062 | 0.0297 | 0.0250 | PSNR 최고. Gaussian 수 감소. large-scale 증가가 큼 |
| exp03 | [`3vhmsw7l`](https://wandb.ai/geekseek/3dgs-keyframe/runs/3vhmsw7l) | scale LR을 낮추면 large Gaussian floater가 줄어든다 | exp02 + `scaling_lr=0.0025` | 완료 | 33.052 | 441,709 | 0.4871 | 0.0819 | 0.1048 | 0.0282 | 0.0246 | large-scale 개선. PSNR은 exp02보다 하락 |
| exp04 | [`4oqp1dps`](https://wandb.ai/geekseek/3dgs-keyframe/runs/4oqp1dps) | stronger opacity pruning이 투명 floater를 줄인다 | exp03 + `min_opacity_prune_threshold=0.01` | 완료 | 32.831 | 356,668 | 0.4032 | 0.0580 | 0.1382 | 0.0270 | 0.0231 | 구조 크게 개선. PSNR 손실 발생 |
| exp06 | [`8l0b5ecw`](https://wandb.ai/geekseek/3dgs-keyframe/runs/8l0b5ecw) | Adam beta1을 낮추면 inertia가 줄어 local minima가 완화된다 | exp04 + `optimizer_beta1=0.85` | 완료 | 32.879 | 350,094 | 0.3951 | 0.0581 | 0.1424 | 0.0270 | 0.0230 | exp04보다 약간 개선. 구조 후보 |
| exp08 | [`qd2nqxji`](https://wandb.ai/geekseek/3dgs-keyframe/runs/qd2nqxji) | late densification이 후반 floater를 만든다 | exp06 + `densify_until_iter=7000` | 완료 | 33.012 | 323,864 | 0.3902 | 0.0578 | 0.1522 | 0.0265 | 0.0247 | 현재 최고 균형. PSNR 회복 + Gaussian/opacity 구조 개선 |
| exp10 | [`iecr7mvq`](https://wandb.ai/geekseek/3dgs-keyframe/runs/iecr7mvq) | position LR을 낮추면 geometry drift와 ORB 거리 악화가 줄어든다 | exp08 + `position_lr_init=0.00012`, `position_lr_final=0.0000012` | 완료 | 32.574 | 323,991 | 0.3835 | 0.0562 | 0.1542 | 0.0255 | 0.0231 | 구조는 더 좋지만 PSNR 손실이 큼 |
| exp11 | [`uc9833a8`](https://wandb.ai/geekseek/3dgs-keyframe/runs/uc9833a8) | position LR 감소를 완화하면 구조 개선과 PSNR을 같이 얻을 수 있다 | exp08 + `position_lr_init=0.00014`, `position_lr_final=0.0000014` | 완료 | 32.682 | 324,339 | 0.3863 | 0.0564 | 0.1527 | 0.0261 | 0.0239 | exp10보다 완화됐지만 PSNR 회복 부족 |
| exp12 | [`xfmp51m8`](https://wandb.ai/geekseek/3dgs-keyframe/runs/xfmp51m8) | sparse point prior를 depth loss로 쓰면 position LR을 낮추지 않고 geometry를 보강할 수 있다 | exp08 + `sparse_depth_weight_init=0.01`, `sparse_depth_weight_final=0.002` | 완료 | 32.587 | 326,039 | 0.4042 | 0.0581 | 0.1423 | 0.0265 | 0.0248 | 비추천. prior는 동작하지만 현재 weight는 PSNR과 floater metric 모두 손해 |

## 조기 중단 실험

| Exp | W&B | 가설 | 주요 설정 | 중단 지점 | 관찰 | 판단 |
| --- | --- | --- | --- | ---: | --- | --- |
| exp05 | [`yplu9pb2`](https://wandb.ai/geekseek/3dgs-keyframe/runs/yplu9pb2) | beta1을 높이면 momentum으로 local minima를 안정적으로 넘을 수 있다 | exp04 + `optimizer_beta1=0.95` | 10k | low-opacity ratio 0.6099로 exp06보다 나쁨 | 비추천. 높은 momentum은 투명 floater 정리를 늦추는 방향 |
| exp07 | [`iy9ex2nz`](https://wandb.ai/geekseek/3dgs-keyframe/runs/iy9ex2nz) | pruning threshold를 0.01에서 0.0075로 완화하면 PSNR 회복 가능 | exp06 + `min_opacity_prune_threshold=0.0075` | 10k | low-opacity ratio 0.6339, large-scale ratio 0.0740 | 비추천. pruning 완화가 floater를 다시 늘림 |
| exp09 | [`bmaidewk`](https://wandb.ai/geekseek/3dgs-keyframe/runs/bmaidewk) | densification을 5000에서 더 일찍 끊으면 late floater가 더 줄어든다 | exp08에서 `densify_until_iter=5000` | 12k | Gaussian 수는 줄었지만 ORB median과 low-opacity ratio가 exp08보다 나쁨. 7k PSNR 28.546 | 비추천. 너무 이른 종료는 geometry/detail 부족 신호 |

## Ambiguity Metric 비교

W&B summary 기준으로 비교 가능한 실험만 정리했다. 이 값은 렌더된 depth ambiguity를 보는 보조 지표이며, Gaussian 구조 metric 및 PSNR과 함께 봐야 한다.

| Exp | W&B | `mean_positive` | `p95` | `max` | `positive_ratio` | `dip` | 해석 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| exp04 | [`4oqp1dps`](https://wandb.ai/geekseek/3dgs-keyframe/runs/4oqp1dps) | 0.3166 | 0.6706 | 0.8903 | 0.3114 | 0.0329 | ambiguity는 낮지만 PSNR 손실 |
| exp06 | [`8l0b5ecw`](https://wandb.ai/geekseek/3dgs-keyframe/runs/8l0b5ecw) | 0.3641 | 0.7435 | 0.9117 | 0.3173 | 0.0157 | exp04보다 PSNR/구조 약간 개선, ambiguity는 악화 |
| exp08 | [`qd2nqxji`](https://wandb.ai/geekseek/3dgs-keyframe/runs/qd2nqxji) | 0.4326 | 0.8586 | 0.9177 | 0.3332 | 0.0129 | PSNR과 Gaussian 구조는 좋지만 ambiguity는 높음 |
| exp10 | [`iecr7mvq`](https://wandb.ai/geekseek/3dgs-keyframe/runs/iecr7mvq) | 0.5313 | 0.8769 | 0.9228 | 0.3662 | 0.0178 | ORB/opacity 구조는 개선됐지만 ambiguity와 PSNR은 나쁨 |
| exp11 | [`uc9833a8`](https://wandb.ai/geekseek/3dgs-keyframe/runs/uc9833a8) | 0.4617 | 0.8615 | 0.9255 | 0.3662 | 0.0076 | exp10보다 완화됐지만 exp08 대비 뚜렷한 우위 없음 |
| exp12 | [`xfmp51m8`](https://wandb.ai/geekseek/3dgs-keyframe/runs/xfmp51m8) | 0.4147 | 0.7961 | 0.9400 | 0.3021 | 0.0426 | ambiguity 평균/p95는 exp08보다 낮지만 PSNR과 low-opacity 구조가 악화되어 단독 개선으로 보기 어려움 |

## 가설별 정리

### 1. Sparse densification

`exp02`에서 Gaussian 수가 줄고 PSNR은 가장 높았다. 다만 large-scale ratio가 크게 증가했다. 이 결과 때문에 scale LR과 pruning을 후속 실험으로 분리했다.

결론: 유망하지만 단독으로는 large Gaussian floater 위험이 있다.

### 2. Scale LR 감소

`exp03`에서 large-scale ratio가 0.0931에서 0.0819로 개선됐다. PSNR은 33.377에서 33.052로 하락했다.

결론: large-scale 제어에는 유효하지만 품질 손실이 있다.

### 3. Opacity pruning 강화

`exp04`에서 low-opacity ratio와 large-scale ratio가 크게 개선됐다. PSNR은 32.831까지 떨어졌다.

결론: floater 구조 제거에는 강하게 유효하나, 너무 세게 쓰면 품질 손실이 생긴다. 이후 실험의 기본 pruning 값은 `0.01`로 유지했다.

### 4. Adam beta1 조정

`beta1=0.95`는 중간 metric이 나빠서 중단했다. `beta1=0.85`는 exp04보다 약간 더 좋은 결과를 냈다.

결론: 높은 momentum은 비추천. 낮은 beta1은 현재 기본값으로 채택할 만하다.

### 5. Densification 종료 시점

`densify_until_iter=7000`인 `exp08`이 가장 좋은 균형을 만들었다. 반대로 `densify_until_iter=5000`인 `exp09`는 geometry/detail 부족 신호가 보여 중단했다.

결론: 7000은 유망한 종료점이고, 5000은 너무 이르다.

### 6. Position LR 감소

`exp10`, `exp11`에서 ORB median, low-opacity ratio, large-scale ratio는 exp08보다 개선됐다. 하지만 PSNR이 32.57-32.68로 떨어졌다.

결론: position LR 감소는 geometry metric에는 유효하지만 RGB 품질 손실이 크다. 단순 LR 감소보다 sparse/depth prior로 geometry를 보강하는 방향이 다음 가설로 더 적합하다.

### 7. Sparse depth prior

데이터셋에는 dense depth 폴더가 없고, `sparse/0/images.txt`와 `points3D.txt`에도 안정적으로 쓸 수 있는 2D track 정보가 없었다. 그래서 sparse 3D point를 매 train camera에 직접 projection해서 sparse inverse depth target을 만들었다.

구현 방식:

- `points3D`의 sparse point를 카메라 좌표로 변환
- 화면 안에 들어오고 `z > sparse_depth_min_depth`인 point만 선택
- projected pixel의 target을 `1 / z_cam`으로 계산
- rasterizer의 `render_pkg["depth"]`와 smooth L1 loss 계산
- W&B에 `train/sparse_depth_loss`, `train/sparse_depth_raw`, `train/sparse_depth_abs`, `train/sparse_depth_points`, `train/sparse_depth_weight` 로깅

실험:

```text
exp12 = exp08
  + train.sparse_depth_weight_init=0.01
  + train.sparse_depth_weight_final=0.002
  + train.sparse_depth_max_points=2048
  + train.sparse_depth_global_max_points=100000
  + train.sparse_depth_min_depth=0.2
  + train.sparse_depth_require_rendered=true
```

관찰:

- smoke test와 full 30k 학습 모두 정상 완료
- sparse depth loss는 초반 `0.02`대에서 후반 `0.0004~0.0006`대까지 감소
- W&B sync 정상 완료
- 하지만 최종 PSNR은 exp08의 33.012에서 32.587로 하락
- low-opacity ratio는 0.3902에서 0.4042로 증가
- nearest ORB median은 0.02470에서 0.02479로 거의 개선 없음
- ambiguity mean/p95는 낮아졌지만 RGB 품질과 Gaussian 구조 metric 악화를 상쇄하지 못함

결론:

현재 sparse depth prior weight `0.01 -> 0.002`는 너무 강하거나 적용 타이밍이 좋지 않다. sparse prior 자체는 구현상 정상 동작하므로 버릴 필요는 없지만, 다음에는 약한 weight 또는 delayed schedule로 다시 검증한다.

추천 후속 실험:

| 후보 | 가설 | 설정 | 기대 | 리스크 |
| --- | --- | --- | --- | --- |
| exp13 | sparse prior가 너무 강해서 RGB 최적화를 방해했다 | exp08 + `sparse_depth_weight_init=0.002`, `sparse_depth_weight_final=0.0005` | exp12보다 PSNR 손실 완화 | geometry 보강 효과가 약할 수 있음 |
| exp14 | 초반 geometry가 불안정할 때 sparse prior를 걸어 local minima를 고정했다 | exp08 + sparse prior를 7000iter 이후 약하게 적용 | densification 이후 구조 drift만 억제 | 구현에 start iteration 옵션 추가 필요 |
| exp15 | rendered pixel이 있는 sparse target만 쓰는 것이 supervision을 너무 좁혔다 | exp13 + `sparse_depth_require_rendered=false` | 더 많은 sparse point가 gradient 제공 | 빈 영역을 억지로 채우며 artifact 가능 |

## 현재 추천 설정

현재까지의 best trade-off:

```bash
dataset=mavis_301_1253_full
dataset.data_device=cpu
train=quality
logging=wandb
train.densification_interval=200
train.densify_grad_threshold=0.0004
train.densify_until_iter=7000
train.scaling_lr=0.0025
train.min_opacity_prune_threshold=0.01
train.optimizer_beta1=0.85
```

해당 설정의 run:

- W&B: [`exp08_openmavis_full_dens_until7000_prune001_beta1_low_20260616_124504`](https://wandb.ai/geekseek/3dgs-keyframe/runs/qd2nqxji)
- Local result: `results/experiments/exp08_openmavis_full_dens_until7000_prune001_beta1_low_20260616_124504`

## 다음 실험 제안

### exp13 후보: 약한 sparse depth prior

`exp12`는 sparse depth loss가 정상 동작했지만 weight가 강해 RGB 품질과 low-opacity 구조가 악화됐다. 다음은 동일한 exp08 base에서 sparse prior weight만 약하게 낮춰서 sparse prior의 이득/손실 곡선을 본다.

설정 후보:

```bash
train.densification_interval=200
train.densify_grad_threshold=0.0004
train.densify_until_iter=7000
train.scaling_lr=0.0025
train.min_opacity_prune_threshold=0.01
train.optimizer_beta1=0.85
train.sparse_depth_weight_init=0.002
train.sparse_depth_weight_final=0.0005
```

판정 기준:

- PSNR이 exp08 대비 0.1 dB 이내로 유지되는지
- low-opacity ratio가 exp12처럼 증가하지 않는지
- ORB median 또는 ambiguity가 exp08보다 개선되는지

### exp14 후보: delayed sparse depth prior

초반 densification 중에는 RGB loss와 densification이 장면 구조를 잡도록 두고, `densify_until_iter=7000` 이후부터 sparse prior를 약하게 켜는 실험이다. 이를 위해 `sparse_depth_start_iter` 옵션 추가가 필요하다.

가설:

- sparse prior를 초반부터 강하게 걸면 잘못 projection된 sparse point 또는 초기 geometry noise가 local minima를 만들 수 있다.
- densification 종료 후 약하게 걸면 RGB 품질을 덜 해치면서 geometry drift만 줄일 수 있다.

검증 기준은 exp13과 동일하다.

## 참고 문서

- metric 해석: `docs/wandb_metric_guide.md`
- 실험 계획: `docs/floater_experiment_plan.md`
- 실행 스크립트:
  - `scripts/experiments/run_exp09_openmavis_full.sh`
  - `scripts/experiments/run_exp10_openmavis_full.sh`
  - `scripts/experiments/run_exp11_openmavis_full.sh`
  - `scripts/experiments/run_exp12_openmavis_full_sparse_depth_prior.sh`
