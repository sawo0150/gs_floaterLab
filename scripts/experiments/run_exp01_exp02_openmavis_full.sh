#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab"
REPO="${ROOT}/repos/main/3dgs-custom"
RESULTS="${ROOT}/results/experiments"
PYTHON="/home/wosas/miniconda3/envs/3dgs/bin/python"
ENV_ROOT="/home/wosas/miniconda3/envs/3dgs"
RASTERIZER="${REPO}/submodules/diff-gaussian-rasterization"
RUN_SUFFIX="${RUN_SUFFIX:-$(date +%Y%m%d_%H%M%S)}"
RUN_ONLY="${RUN_ONLY:-all}"

export CUDA_HOME="${ENV_ROOT}"
export PATH="${ENV_ROOT}/bin:${PATH}"
export PYTHONPATH="${RASTERIZER}:${PYTHONPATH:-}"
export WANDB_DIR="${RESULTS}"

cd "${REPO}"

if [[ ! -f "${RASTERIZER}/diff_gaussian_rasterization/_C.cpython-39-x86_64-linux-gnu.so" ]]; then
  echo "[setup] Building modified diff_gaussian_rasterization extension"
  (cd "${RASTERIZER}" && "${PYTHON}" setup.py build_ext --inplace)
fi

run_exp() {
  local exp_id="$1"
  local run_name="$2"
  shift 2

  local full_name="${exp_id}_${run_name}_${RUN_SUFFIX}"
  local run_dir="${RESULTS}/${full_name}"
  mkdir -p "${run_dir}"

  echo "[run] ${full_name}"
  "${PYTHON}" app/train_hydra.py \
    dataset=mavis_301_1253_full \
    dataset.data_device=cpu \
    train=quality \
    logging=wandb \
    project.output_root="${RESULTS}" \
    project.run_name="${full_name}" \
    logging.name="${full_name}" \
    logging.tags="[openmavis,full,${exp_id}]" \
    "$@" \
    2>&1 | tee "${run_dir}/train.log"
}

if [[ "${RUN_ONLY}" == "all" || "${RUN_ONLY}" == "exp01" ]]; then
  run_exp \
    "exp01" \
    "openmavis_full_baseline"
fi

if [[ "${RUN_ONLY}" == "all" || "${RUN_ONLY}" == "exp02" ]]; then
  run_exp \
    "exp02" \
    "openmavis_full_dens_sparse" \
    train.densification_interval=200 \
    train.densify_grad_threshold=0.0004
fi
