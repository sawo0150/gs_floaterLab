# Experiment Timeline

## Phase 0: Metric/logging 기반 만들기

목표는 floater를 W&B에서 계속 추적할 수 있게 만드는 것이었다.

추가/수정된 축:

- Gaussian stats:
  - `gaussian/count`
  - `gaussian/low_opacity_count`
  - `gaussian/low_opacity_ratio`
  - `gaussian/large_scale_count`
  - `gaussian/large_scale_ratio`
  - `gaussian/opacity_median`
  - `gaussian/scale_median`
  - `gaussian/nearest_orb_median`
- depth ambiguity:
  - `ambiguity/mean_positive`
  - `ambiguity/p95`
  - `ambiguity/max`
  - `ambiguity/positive_ratio`
  - `ambiguity/dip`
- renderer output compatibility:
  - `alpha_depth`
  - `modes`
- W&B logging 주기: 기본 2000 iterations.

자세한 용어 설명은 [`docs/wandb_metric_guide.md`](../docs/wandb_metric_guide.md)를 본다.

## Phase 1: 기본 density/SH/opacity 실험

| 실험 | 목적 | 핵심 설정 | 판단 |
| --- | --- | --- | --- |
| `base_s5` | 기준 모델 | default | 기준 |
| `sh1_s5` | SH 자유도 제한이 floater를 줄이는지 확인 | `--sh_degree 1` | 비추천 |
| `dens_late_s5` | 초반 densification이 floater를 만드는지 확인 | `--densify_from_iter 1500` | 약간 유망 |
| `dens_sparse_s5` | densification이 너무 자주/쉽게 발생하는지 확인 | `--densification_interval 200 --densify_grad_threshold 0.0004` | 가장 유망한 초기 후보 |
| `dens_short_s5` | 후반 densification이 floater를 만드는지 확인 | `--densify_until_iter 7000` | 보조 후보 |
| `opreset_slow_s5` | opacity reset 빈도 감소 | `--opacity_reset_interval 6000` | 비추천 |
| `dens_sparse_orbdepth_s5` | sparse densification + ORB sparse depth prior | sparse depth weight `0.01 -> 0.002` | visual 확인 필요였으나 이후 full에서는 악화 |

초기 결론:

- SH를 줄이는 것은 floater 개선보다 품질/표현력 손실 쪽이 컸다.
- densification을 덜 자주, 더 까다롭게 하는 방향이 가장 유망했다.

## Phase 2: Full 1311 image OpenMAVIS 실험

full 기준 dataset은 `0416_Data__0416_301-1253`, 1311 images이다.

| 실험 | 핵심 | 결과 요약 |
| --- | --- | --- |
| `exp01_openmavis_full_baseline` | full baseline | 비교 기준 |
| `exp02/03...` | density/pruning/LR variations | sparse densification 계열이 유망 |
| `exp08_openmavis_full_dens_until7000_prune001_beta1_low_20260616_124504` | exp best 후보 | PSNR 약 33.012, W&B `qd2nqxji` |
| `exp12_openmavis_full_dens_until7000_prune001_beta1_low_sparse_depth_20260616_141814` | exp08 + sparse depth prior | PSNR 32.587, W&B `xfmp51m8`, 현재 weight에서는 악화 |

exp08 핵심 설정:

```text
--densification_interval 200
--densify_grad_threshold 0.0004
--densify_until_iter 7000
--scaling_lr 0.0025
--min_opacity_prune_threshold 0.01
--optimizer_beta1 0.85
```

## Phase 3: Floater diagnostic loop

처음에는 Z-gradient blind spot, local minima, density control 문제를 같이 의심했다.

검증 결과:

- Z-gradient blind spot 단독 가설은 약하다.
- 실제로는 sparse init point cloud에 매우 큰 outlier가 포함되어 있었고, 이것이 early Gaussian outlier를 만든다.
- iter 500에 이미 극단적 Z outlier가 많고, pruning 이후에도 일부 survivor가 남는다.

핵심 수치:

```text
iter 500 Z outlier: 46,264
초기 |Z|max: 약 907,582m
후반 survivor |Z|max: 약 42m
```

자세한 정리는 [`docs/floater_diagnostic_loop.md`](../docs/floater_diagnostic_loop.md), [`docs/round5_findings_summary.md`](../docs/round5_findings_summary.md)를 본다.

## Phase 4: Camera-bound sparse point filtering

SLAM sparse init outlier를 줄이기 위해 camera frustum/bounds 기반 point filtering을 추가했다.

대표 결과:

| 항목 | 값 |
| --- | ---: |
| 제거된 sparse point | 46,276 / 626,811 |
| 제거 비율 | 7.38% |
| Z-outlier @500 before -> after | 46,264 -> 508 |
| Z-outlier @30k before -> after | 1,474 -> 385 |
| `abs(Z)` max @30k before -> after | 42.71m -> 4.85m |
| PSNR @30k before -> after | 33.012 -> 32.855 |

결론:

- Pop1 sparse init outlier는 크게 줄었다.
- 그러나 densification 이후 생기는 Pop2 floater는 여전히 남는다.

## Phase 5: VGGT 연결 및 smoke

VGGT repo:

```text
/home/wosas/Desktop/26-1_RPM/gsProjects/vggt
```

`repos/main/vggt`에 연결했다. Python version 문제 때문에 `3dgs` conda env에 editable install은 하지 않고 `PYTHONPATH`로 실행했다.

frame count 결과:

| frames | 결과 |
| ---: | --- |
| 16 | 성공 |
| 32 | 성공 |
| 64 | 성공, 현재 best smoke |
| 80 | 성공하지만 64보다 NN 비교 악화 |
| 96 | CUDA OOM |
| 128 | CUDA OOM |

VGGT는 RAM보다 VRAM이 병목이다. frame 수를 늘리려면 chunking/lower resolution/attention memory 절감이 필요하다.

## Phase 6: VGGT64 vs OpenMAVIS64 3DGS

64-frame scene:

```text
results/datasets/vggt64_3dgs_scene
results/datasets/openmavis64_3dgs_scene
```

3DGS 7k 결과:

| 항목 | VGGT64 | OpenMAVIS64/MPS |
| --- | ---: | ---: |
| result dir | `exp13_vggt64_3dgs_7k_retry_20260630_112335` | `exp14_openmavis64_3dgs_7k_20260630_112820` |
| Test PSNR | 17.04 | 18.65 |
| Train PSNR | 30.26 | 34.25 |
| Gaussian count | 557,481 | 791,532 |
| Large scale ratio | 0.00018 | 0.02987 |
| Low opacity ratio | 0.5575 | 0.7309 |

결론:

- VGGT64는 compact한 Gaussian을 만들지만 render 품질이 낮다.
- OpenMAVIS64/MPS 쪽이 3DGS 학습 품질은 낫다.

## Phase 7: EVO camera report

MPS 기준 camera comparison report를 만들었다.

중요 output:

```text
results/evo_camparam_mps_vggt_openmavis_64_20260630/report.md
results/evo_camparam_mps_vggt_openmavis_64_20260630/evo_mps_openmavis_vs_vggt_64_summary_grid.pdf
results/evo_camparam_mps_vggt_openmavis_64_20260630/summary_metrics.json
```

주의:

- `openmavis64_*` 초기 EVO output은 invalid이다.
- 올바른 OpenMAVIS trajectory는 `openmavis_orb_64.*` 이름으로 된 파일이다.

