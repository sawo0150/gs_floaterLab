#!/usr/bin/env bash
set -euo pipefail

family=${1:?usage: run_one.sh FAMILY SCENE SELECTOR Q SEED [OUTPUT_DIR]}
scene=${2:?usage: run_one.sh FAMILY SCENE SELECTOR Q SEED [OUTPUT_DIR]}
selector=${3:?usage: run_one.sh FAMILY SCENE SELECTOR Q SEED [OUTPUT_DIR]}
quota=${4:?usage: run_one.sh FAMILY SCENE SELECTOR Q SEED [OUTPUT_DIR]}
seed=${5:?usage: run_one.sh FAMILY SCENE SELECTOR Q SEED [OUTPUT_DIR]}
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
common="$lab_root/context/experiments/benchmark_custom/5070ti_vanilla_matched_time/run_one.sh"
output=${6:-"$lab_root/results/ERCB_ablation/exp03-F_keyframe_role/$family/$scene/q${quota}/${selector}_s${seed}"}

export VIGS_REPO_ROOT=/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-main-integration-20260828
export MATCHED_ADMISSION=arrival
export MAPPING_REPLAY_SCALE_OVERRIDE=1.5
export MAPPING_STEPS_PER_PACKET="$quota"
export MAPPING_SEED="$seed"
exec "$common" "$family" "$scene" "$selector" "$output"
