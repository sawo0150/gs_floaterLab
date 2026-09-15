#!/usr/bin/env bash
# Strict fixed-scale wrapper using causal fixed-arrival dense membership.
set -euo pipefail

family=${1:?usage: run_one.sh FAMILY SCENE SELECTOR SCALE SEED [OUTPUT_DIR]}
scene=${2:?usage: run_one.sh FAMILY SCENE SELECTOR SCALE SEED [OUTPUT_DIR]}
selector=${3:?usage: run_one.sh FAMILY SCENE SELECTOR SCALE SEED [OUTPUT_DIR]}
scale=${4:?usage: run_one.sh FAMILY SCENE SELECTOR SCALE SEED [OUTPUT_DIR]}
seed=${5:?usage: run_one.sh FAMILY SCENE SELECTOR SCALE SEED [OUTPUT_DIR]}
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
common="$lab_root/context/experiments/benchmark_custom/5070ti_vanilla_matched_time/run_one.sh"
scale_tag=${scale/./p}x
output=${6:-"$lab_root/results/ERCB_ablation/exp03-B_strict_fixed_arrival/$family/$scene/${scale_tag}/${selector}_arrival_s${seed}"}

export MATCHED_ADMISSION=arrival
export MAPPING_REPLAY_SCALE_OVERRIDE="$scale"
export MAPPING_SEED="$seed"
exec "$common" "$family" "$scene" "$selector" "$output"
