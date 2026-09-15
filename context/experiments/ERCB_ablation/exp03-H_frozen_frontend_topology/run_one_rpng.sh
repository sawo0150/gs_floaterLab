#!/usr/bin/env bash
set -euo pipefail

frontend_mode=${1:?usage: run_one_rpng.sh FRONTEND_MODE TOPOLOGY_MODE SELECTOR OUTPUT_DIR}
topology_mode=${2:?usage: run_one_rpng.sh FRONTEND_MODE TOPOLOGY_MODE SELECTOR OUTPUT_DIR}
selector=${3:?usage: run_one_rpng.sh FRONTEND_MODE TOPOLOGY_MODE SELECTOR OUTPUT_DIR}
output=${4:?usage: run_one_rpng.sh FRONTEND_MODE TOPOLOGY_MODE SELECTOR OUTPUT_DIR}
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
common="$lab_root/context/experiments/benchmark_custom/5070ti_vanilla_matched_time/run_one.sh"
trace_root="$lab_root/results/ERCB_ablation/exp03-H_frozen_frontend_topology/rpng/table_07/q3"
frontend_trace_dir="$trace_root/frontend_trace_v3_s0"
topology_trace_dir="$trace_root/topology_trace_v3_s0"

export VIGS_REPO_ROOT=/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-main-integration-20260828
export MATCHED_ADMISSION=arrival
export MAPPING_REPLAY_SCALE_OVERRIDE=1.5
export MAPPING_STEPS_PER_PACKET=3
export MAPPING_SEED=0
export MAPPING_DENSE_POSE_SOURCE=gt_absolute
export MAPPING_GT_TRAJECTORY="$lab_root/data/benchmarks/rpng/prepared/rpngar/table_07/gt.txt"
export MAPPING_GT_CAMERA_FRAME=camera
export MAPPING_DENSE_GRADIENT_SCOPE=appearance_opacity
export MAPPING_FRONTEND_TRACE_MODE="$frontend_mode"
export MAPPING_FRONTEND_TRACE_DIR="$frontend_trace_dir"
export MAPPING_TOPOLOGY_TRACE_MODE="$topology_mode"
export MAPPING_TOPOLOGY_TRACE_DIR="$topology_trace_dir"
if [ "$topology_mode" = off ]; then
    export MAPPING_TRACE_PACKET_DRIVEN_TOPOLOGY=0
else
    export MAPPING_TRACE_PACKET_DRIVEN_TOPOLOGY=1
fi
export MAPPING_CONFIG_OVERRIDE="$script_dir/config/rpng_trace.yaml"

exec "$common" rpng table_07 "$selector" "$output"
