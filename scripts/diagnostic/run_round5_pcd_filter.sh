#!/usr/bin/env bash
# Round 5 Intervention: SLAM Sparse Point Filtering
# 목적: 초기화 전 outlier sparse point 제거로 Z-floater 예방
#   - 카메라 extent × expand_factor 범위 밖 sparse point 제거
#   - 예측: iter 500의 46,264 Z-outliers → ~1,000개 (97% 감소)
#   - exp08과 동일 hyperparameter, 15k iterations (빠른 비교)
# 비교 기준: Round 2 (unfiltered) → iter 500 z_outlier=46264, final z_outlier=1442
set -euo pipefail

ROOT="/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab"
REPO="${ROOT}/repos/main/3dgs-custom"
RESULTS="${ROOT}/results/rounds"
PYTHON="/home/wosas/miniconda3/envs/3dgs/bin/python"
ENV_ROOT="/home/wosas/miniconda3/envs/3dgs"
RASTERIZER="${REPO}/submodules/diff-gaussian-rasterization"
RUN_SUFFIX="${RUN_SUFFIX:-$(date +%Y%m%d_%H%M%S)}"
EXPAND="${EXPAND_FACTOR:-3.0}"

export CUDA_HOME="${ENV_ROOT}"
export PATH="${ENV_ROOT}/bin:${PATH}"
export PYTHONPATH="${RASTERIZER}:${PYTHONPATH:-}"
export WANDB_DIR="${RESULTS}"

cd "${REPO}"

if [[ ! -f "${RASTERIZER}/diff_gaussian_rasterization/_C.cpython-39-x86_64-linux-gnu.so" ]]; then
  echo "[setup] Building diff_gaussian_rasterization extension"
  (cd "${RASTERIZER}" && "${PYTHON}" setup.py build_ext --inplace)
fi

EXP_ID="round5_pcd_filter"
RUN_NAME="slam_outlier_filter_x${EXPAND}"
FULL_NAME="${EXP_ID}_${RUN_NAME}_${RUN_SUFFIX}"
RUN_DIR="${RESULTS}/${FULL_NAME}"
mkdir -p "${RUN_DIR}"

echo "[run] ${FULL_NAME}"
echo "[purpose] SLAM sparse point filtering: remove outliers > ${EXPAND}x camera extent"
echo "[prediction] iter-500 Z-outliers: 46264 → ~1000 (97% reduction)"

"${PYTHON}" app/train_hydra.py \
  dataset=mavis_301_1253_full \
  dataset.data_device=cpu \
  dataset.init_pcd_filter=true \
  dataset.init_pcd_expand_factor="${EXPAND}" \
  train=quality \
  logging=wandb \
  project.output_root="${RESULTS}" \
  project.run_name="${FULL_NAME}" \
  logging.name="${FULL_NAME}" \
  logging.tags="[round5,pcd_filter,intervention,slam_outlier,expand${EXPAND}]" \
  train.densification_interval=200 \
  train.densify_grad_threshold=0.0004 \
  train.densify_until_iter=7000 \
  train.scaling_lr=0.0025 \
  train.min_opacity_prune_threshold=0.01 \
  train.optimizer_beta1=0.85 \
  train.iterations=15000 \
  logging.diag_grad_interval=500 \
  logging.gaussian_metrics_log_interval=2000 \
  logging.ambiguity_log_interval=2000 \
  2>&1 | tee "${RUN_DIR}/train.log"

echo "[done] Compare W&B:"
echo "  diag/z_outlier_count_3m @ iter 500  → should be ~1000 (was 46264)"
echo "  diag/z_abs_max           @ iter 500  → should be ~42m  (was 907582m)"
echo "  PSNR @ iter 15000        → should be ≥ Round 2 (28.21)"
