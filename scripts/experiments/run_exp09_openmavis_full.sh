#!/usr/bin/env bash
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
  echo "[setup] Building modified diff_gaussian_rasterization extension"
  (cd "${RASTERIZER}" && "${PYTHON}" setup.py build_ext --inplace)
fi

EXP_ID="exp09"
RUN_NAME="openmavis_full_dens_until5000_prune001_beta1_low"
FULL_NAME="${EXP_ID}_${RUN_NAME}_${RUN_SUFFIX}"
RUN_DIR="${RESULTS}/${FULL_NAME}"
mkdir -p "${RUN_DIR}"

echo "[run] ${FULL_NAME}"
"${PYTHON}" app/train_hydra.py \
  dataset=mavis_301_1253_full \
  dataset.data_device=cpu \
  train=quality \
  logging=wandb \
  project.output_root="${RESULTS}" \
  project.run_name="${FULL_NAME}" \
  logging.name="${FULL_NAME}" \
  logging.tags="[openmavis,full,${EXP_ID},dens_until5000,prune001,beta1_low]" \
  train.densification_interval=200 \
  train.densify_grad_threshold=0.0004 \
  train.densify_until_iter=5000 \
  train.scaling_lr=0.0025 \
  train.min_opacity_prune_threshold=0.01 \
  train.optimizer_beta1=0.85 \
  2>&1 | tee "${RUN_DIR}/train.log"
