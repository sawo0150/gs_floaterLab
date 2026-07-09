# Repro Commands

이 문서는 다음 agent가 주요 실험을 다시 돌릴 때 필요한 기준 커맨드를 모은 것이다. timestamp가 붙는 output dir은 새로 만들면 된다.

## Common paths

```bash
ROOT=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
GS=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
VGGT=/home/wosas/Desktop/26-1_RPM/gsProjects/vggt
DATA=/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253
RESULTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments
PY=/home/wosas/miniconda3/envs/3dgs/bin/python
```

## Full OpenMAVIS best 후보 재학습

exp08 계열:

```bash
cd "$GS"

"$PY" train.py \
  -s "$DATA" \
  -m "$RESULTS/expXX_openmavis_full_exp08_like" \
  --iterations 30000 \
  --test_iterations 7000 15000 30000 \
  --save_iterations 7000 15000 30000 \
  --eval \
  --disable_viewer \
  --densification_interval 200 \
  --densify_grad_threshold 0.0004 \
  --densify_until_iter 7000 \
  --scaling_lr 0.0025 \
  --min_opacity_prune_threshold 0.01 \
  --optimizer_beta1 0.85
```

주의:

- 실제 option 이름은 현재 `3dgs-custom/arguments`와 `train.py` 기준으로 확인한다.
- W&B metric은 2000 iteration 주기로 올라가도록 수정되어 있다.

## Sparse depth prior 재실험 기준

현재 exp12 weight는 악화됐다. 다시 돌릴 때는 더 약하게 시작하는 것이 맞다.

```bash
cd "$GS"

"$PY" train.py \
  -s "$DATA" \
  -m "$RESULTS/expXX_sparse_depth_weak_delayed" \
  --iterations 30000 \
  --test_iterations 7000 15000 30000 \
  --save_iterations 7000 15000 30000 \
  --eval \
  --disable_viewer \
  --densification_interval 200 \
  --densify_grad_threshold 0.0004 \
  --densify_until_iter 7000 \
  --scaling_lr 0.0025 \
  --min_opacity_prune_threshold 0.01 \
  --optimizer_beta1 0.85 \
  --sparse_depth_weight_init 0.001 \
  --sparse_depth_weight_final 0.0002
```

주의:

- 위 weight는 제안값이다. 기존 실패 weight는 `0.01 -> 0.002`.
- 가능하면 camera-bound sparse point filtering 이후의 filtered sparse points에만 prior를 걸어야 한다.

## VGGT 64-frame smoke

VGGT는 editable install 대신 `PYTHONPATH`를 사용한다.

```bash
cd "$VGGT"

PYTHONPATH="$VGGT:$PYTHONPATH" "$PY" demo_colmap.py \
  --scene_dir "$RESULTS/vggt_smoke_64_301_1253_NEW" \
  --conf_thres_value 1.0
```

주의:

- 실제 image list/subset을 넘기는 방식은 현재 만든 wrapper/script를 확인한다.
- `conf_thres_value=5.0`은 너무 strict해서 실패했고, `1.0`에서 성공했다.
- 96/128 frames는 RTX 5070 Ti 16GB 기준 CUDA OOM이었다.

## VGGT64 3DGS 재학습

```bash
cd "$GS"

"$PY" train.py \
  -s "$RESULTS/datasets/vggt64_3dgs_scene" \
  -m "$RESULTS/expXX_vggt64_3dgs_7k" \
  --iterations 7000 \
  --test_iterations 7000 \
  --save_iterations 7000 \
  --eval \
  --disable_viewer \
  --densify_until_iter 7000 \
  --min_opacity_prune_threshold 0.01 \
  --optimizer_beta1 0.5
```

OpenMAVIS64/MPS scene comparison:

```bash
cd "$GS"

"$PY" train.py \
  -s "$RESULTS/datasets/openmavis64_3dgs_scene" \
  -m "$RESULTS/expXX_openmavis64_3dgs_7k" \
  --iterations 7000 \
  --test_iterations 7000 \
  --save_iterations 7000 \
  --eval \
  --disable_viewer \
  --densify_until_iter 7000 \
  --min_opacity_prune_threshold 0.01 \
  --optimizer_beta1 0.5
```

## EVO report 확인

결과 경로:

```bash
cd "$ROOT/results/archive/evo_camparam_mps_vggt_openmavis_64_20260630"

ls -lh \
  evo_mps_openmavis_vs_vggt_64_summary_grid.pdf \
  report.md \
  summary_metrics.json
```

올바른 입력 trajectory:

```text
openmavis_orb_64.tum
vggt64_colmap_cam.tum
mps_rgb_64.tum
```

invalid로 봐야 할 초기 파일:

```text
openmavis64_ape_sim3.*
openmavis64_rpe_trans_sim3.*
```

이 파일들은 실제 OpenMAVIS ORB trajectory가 아니라 MPS-derived subset에 가까워서 APE 0처럼 보인다.

## Rasterizer compatibility 주의

현재 설치된 `diff_gaussian_rasterization`은 일부 SparseGS-style 인자를 지원하지 않을 수 있다.

`3dgs-custom/gaussian_renderer/__init__.py`에는 다음 fallback이 필요하다.

- `GaussianRasterizationSettings`가 `beta`를 받지 않으면 넘기지 않는다.
- rasterizer output이 `alpha_depth/modes`를 주지 않으면:
  - `alpha_depth = depth_image`
  - `modes = zeros_like(depth_image)`

이 fallback을 제거하면 VGGT64/OpenMAVIS64 3DGS smoke가 다시 깨질 수 있다.

## Sparse support potential 2D toy

```bash
cd "$ROOT"

python scripts/diagnostic/toy_sparse_support_potential.py
```

옵션 예시:

```bash
python scripts/diagnostic/toy_sparse_support_potential.py \
  --fixed-tau 0.28 \
  --adaptive-alpha 0.82 \
  --knn 4 \
  --grid-size 220
```

출력:

```text
results/diagnostic/toy_sparse_support_potential_<timestamp>/
```

대표 파일:

```text
toy_sparse_support_potential_report.pdf
summary.json
01_sparse_points_local_spacing.png
02_fixed_vs_adaptive_plateau.png
03_ray_coverage.png
04_normalized_distance_plateau.png
05_potential_shapes_force_fields.png
06_gaussian_center_dynamics.png
07_ray_vs_potential_coverage.png
```
