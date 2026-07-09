#!/usr/bin/env bash
# exp13: Full 30k training with SLAM sparse point filtering
# 목적: exp08 (best baseline, PSNR 33.012) vs exp13 (same + pcd filter) 직접 비교
# exp08 hyperparams + init_pcd_filter=true
set -euo pipefail

ROOT="/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab"
REPO="${ROOT}/repos/main/3dgs-custom"
RESULTS="${ROOT}/results/experiments"
PYTHON="/home/wosas/miniconda3/envs/3dgs/bin/python"
ENV_ROOT="/home/wosas/miniconda3/envs/3dgs"
RASTERIZER="${REPO}/submodules/diff-gaussian-rasterization"
RUN_SUFFIX="${RUN_SUFFIX:-$(date +%Y%m%d_%H%M%S)}"

export CUDA_HOME="${ENV_ROOT}"
export PATH="${ENV_ROOT}/bin:${PATH}"
export PYTHONPATH="${RASTERIZER}:${PYTHONPATH:-}"
export WANDB_DIR="${RESULTS}"

cd "${REPO}"

if [[ ! -f "${RASTERIZER}/diff_gaussian_rasterization/_C.cpython-39-x86_64-linux-gnu.so" ]]; then
  echo "[setup] Building diff_gaussian_rasterization extension"
  (cd "${RASTERIZER}" && "${PYTHON}" setup.py build_ext --inplace)
fi

EXP_ID="exp13"
RUN_NAME="pcd_filter_full30k"
FULL_NAME="${EXP_ID}_${RUN_NAME}_${RUN_SUFFIX}"
RUN_DIR="${RESULTS}/${FULL_NAME}"
mkdir -p "${RUN_DIR}"

echo "[run] ${FULL_NAME}"
echo "[purpose] exp08 hyperparams + SLAM sparse point filtering. Compare PSNR vs exp08=33.012"

"${PYTHON}" app/train_hydra.py \
  dataset=mavis_301_1253_full \
  dataset.data_device=cpu \
  dataset.init_pcd_filter=true \
  dataset.init_pcd_expand_factor=1.0 \
  train=quality \
  logging=wandb \
  project.output_root="${RESULTS}" \
  project.run_name="${FULL_NAME}" \
  logging.name="${FULL_NAME}" \
  logging.tags="[exp13,pcd_filter,slam_outlier,full30k,baseline_comparison]" \
  train.densification_interval=200 \
  train.densify_grad_threshold=0.0004 \
  train.densify_until_iter=7000 \
  train.scaling_lr=0.0025 \
  train.min_opacity_prune_threshold=0.01 \
  train.optimizer_beta1=0.85 \
  train.iterations=30000 \
  logging.diag_grad_interval=500 \
  logging.gaussian_metrics_log_interval=2000 \
  logging.ambiguity_log_interval=2000 \
  2>&1 | tee "${RUN_DIR}/train.log"

echo "[done] Compare with exp08:"
echo "  exp08 PSNR @ 30k: 33.012"
echo "  exp13 PSNR @ 30k: check W&B"
echo "  exp13 Z-outlier @ 30k: expected ~374 (vs exp08: 1474)"
