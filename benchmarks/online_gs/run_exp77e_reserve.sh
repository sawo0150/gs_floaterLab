#!/usr/bin/env bash
# exp70 paired runner on the final exp69 v7 RTX 5090 execution profile at
# original timestamp pacing.  The legacy v6/v7 causal-carve opacity loss and
# prox mutation are absent; terminal dust-GC remains part of the final v7
# pipeline.  Only the exp70 detached-opacity action differs between arms.
set -euo pipefail

if [ "$#" -lt 3 ]; then
    echo "usage: $0 <dataset-dir-name> <output-dir> <control|alpha|nll> [--length N]" >&2
    exit 2
fi

repo_root='/home/intern/VIGS-SLAM-main-integration-20260828'
dataset_name=$1
output_dir=$2
arm=$3
shift 3

if [ "$#" -ne 0 ]; then
    if [ "$#" -ne 2 ] || [ "$1" != "--length" ] || ! [[ "$2" =~ ^[1-9][0-9]*$ ]]; then
        echo "optional arguments must be --length N" >&2
        exit 2
    fi
fi

case "$arm" in
    control|baseline)
        export EXP70_DETACHED_OPACITY_MODE=off
        ;;
    alpha|nll)
        export EXP70_DETACHED_OPACITY_MODE=$arm
        ;;
    *)
        echo "unknown exp70 arm: $arm" >&2
        exit 2
        ;;
esac

# Load the validated final-v7 RTX 5090 execution recipe.
# shellcheck source=exp69_axes/hardware_profiles.sh
source "$repo_root/exp69_axes/hardware_profiles.sh"
exp69_apply_hardware_profile rtx5090
case "${EXP77E_RESERVE_MS:?missing EXP77E_RESERVE_MS}" in
    40|20|0) ;;
    *) echo "reserve must be 40, 20 or 0" >&2; exit 2 ;;
esac
export EXP69_REPLAY_TRACKING_RESERVE_MS=$EXP77E_RESERVE_MS
export EXP72_REPLAY_COUNT_SOFTMAX_BETA=off
export EXP72_REPLAY_COUNT_SOFTMAX_BLOCK_SIZE=1
export EXP72_REPLAY_COUNT_SOFTMAX_ACTIVE_BONUS=0
echo "EXP77E_RESERVE effective_ms=$EXP69_REPLAY_TRACKING_RESERVE_MS"
export EXP69_REPLAY_TIME_SCALE=1

# Replace, rather than stack with, the legacy carve opacity action.  The
# causal-carve flag itself is omitted, while terminal dust-GC and every
# scheduler/hardware setting from final v7 remain identical across arms.
export EXP69_LEGACY_CARVE_ENABLED=0

conda_env=${EXP69_CONDA_ENV:-$EXP69_DEFAULT_CONDA_ENV}
if [ ! -x "$conda_env/bin/python" ]; then
    echo "missing VIGS conda environment: $conda_env" >&2
    exit 1
fi
conda_root=${conda_env%%/envs/*}
source "$conda_root/etc/profile.d/conda.sh"
conda activate "$conda_env"

echo "EXP70_V7_1X_RUN profile=rtx5090 scale=1 legacy_carve_enabled=0 arm=$arm detached_mode=$EXP70_DETACHED_OPACITY_MODE detached_lambda=${EXP70_DETACHED_OPACITY_LAMBDA:-0.002}"
exec bash "$repo_root/exp69_axes/run_decoupled_geometry.sh" \
    "$dataset_name" "$output_dir" v7 "$@"
