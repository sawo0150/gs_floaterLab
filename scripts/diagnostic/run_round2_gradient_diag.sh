#!/usr/bin/env bash
# Round 2 Diagnostic Training
# 목적: Z-axis gradient deficiency (P12) 직접 확인
#   - diag/grad_z_vs_x_ratio (예측: ~0.094)
#   - diag/z_outlier_count_3m (Z-drift 진화 추적)
#   - diag/z_abs_p99 (iter별 Z drift 정도)
# exp08과 동일한 hyperparameter, 15000 iterations (진단 목적)
set -euo pipefail

ROOT="/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab"
REPO="${ROOT}/repos/main/3dgs-custom"
RESULTS="${ROOT}/results/rounds"
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

EXP_ID="round2_grad_diag"
RUN_NAME="z_axis_gradient_verification"
FULL_NAME="${EXP_ID}_${RUN_NAME}_${RUN_SUFFIX}"
RUN_DIR="${RESULTS}/${FULL_NAME}"
mkdir -p "${RUN_DIR}"

echo "[run] ${FULL_NAME}"
echo "[purpose] Verify: diag/grad_z_vs_x_ratio predicted ~0.094 (P12 Z-axis blind spot)"
"${PYTHON}" app/train_hydra.py \
  dataset=mavis_301_1253_full \
  dataset.data_device=cpu \
  train=quality \
  logging=wandb \
  project.output_root="${RESULTS}" \
  project.run_name="${FULL_NAME}" \
  logging.name="${FULL_NAME}" \
  logging.tags="[round2,gradient_diag,z_axis_blindspot,P12]" \
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

echo "[done] Check W&B for:"
echo "  diag/grad_z_vs_x_ratio   - should be ~0.094 (P12 prediction)"
echo "  diag/z_outlier_count_3m  - when does Z drift start?"
echo "  diag/z_abs_p99           - Z drift progression"
