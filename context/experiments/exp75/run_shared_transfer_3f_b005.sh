#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_data=/home/intern/gs_floaterLab/data/exp75_causal_offline/aria3F
task_root=/home/intern/gs_floaterLab/context/experiments/exp75/evidence/shared_branch
task_common="$task_root/aria3F_common_rr_r4_15k_s0"

mkdir -p "$task_root"
cd "$task_repo"

if [[ ! -f "$task_common/chkpnt14999.pth" ]]; then
    if [[ -e "$task_common" ]]; then
        echo "Incomplete common output already exists: $task_common" >&2
        exit 2
    fi
    "$task_python" train.py \
        -s "$task_data" -m "$task_common" -r 4 --eval \
        --iterations 15000 --test_iterations 999999 \
        --checkpoint_iterations 14999 \
        --view_schedule "$task_data/causal_arrivals.json" \
        --view_scheduler causal_rr --scheduler_seed 0 \
        --quiet --disable_viewer > "$task_common.log" 2>&1
fi

run_branch () {
    local task_label=$1
    local task_scheduler=$2
    local task_beta=$3
    local task_output="$task_root/aria3F_shared_${task_label}_K32_r4_79081_s0"
    if [[ -e "$task_output" ]]; then
        echo "Refusing to overwrite existing output: $task_output" >&2
        exit 2
    fi
    "$task_python" train.py \
        -s "$task_data" -m "$task_output" -r 4 --eval \
        --iterations 79081 --test_iterations 999999 \
        --save_iterations 30000 45000 60000 79081 \
        --start_checkpoint "$task_common/chkpnt14999.pth" \
        --view_schedule "$task_data/causal_arrivals.json" \
        --view_scheduler "$task_scheduler" --scheduler_seed 0 \
        --scheduler_beta "$task_beta" --scheduler_block_size 32 \
        --quiet --disable_viewer > "$task_output.log" 2>&1
}

run_branch rr causal_rr 0
# Experimental harness: exact common causal-RR prehistory, then only the
# frozen-topology replay picker changes at the branch boundary.
run_branch interval_size_b005 staged_interval_size_softmax_rr 0.05
