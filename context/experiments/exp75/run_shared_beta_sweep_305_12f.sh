#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_data_root=/home/intern/gs_floaterLab/data/exp74_causal_offline
task_root=/home/intern/gs_floaterLab/context/experiments/exp75/evidence/shared_branch

mkdir -p "$task_root"
cd "$task_repo"

run_branch () {
    local task_scene=$1
    local task_label=$2
    local task_scheduler=$3
    local task_beta=$4
    local task_checkpoint=$5
    local task_data="$task_data_root/$task_scene"
    local task_output="$task_root/${task_scene}_shared_${task_label}_K32_r4_45k_s0"
    if [[ -e "$task_output" ]]; then
        echo "Refusing to overwrite existing output: $task_output" >&2
        exit 2
    fi
    "$task_python" train.py \
        -s "$task_data" -m "$task_output" -r 4 --eval \
        --iterations 45000 --test_iterations 999999 \
        --save_iterations 30000 45000 \
        --start_checkpoint "$task_checkpoint" \
        --view_schedule "$task_data/causal_arrivals.json" \
        --view_scheduler "$task_scheduler" --scheduler_seed 0 \
        --scheduler_beta "$task_beta" --scheduler_block_size 32 \
        --quiet --disable_viewer \
        > "$task_output.log" 2>&1
}

task_305_checkpoint="$task_root/aria305_common_rr_r4_15k_s0/chkpnt14999.pth"
if [[ ! -f "$task_305_checkpoint" ]]; then
    echo "Missing 305 shared checkpoint: $task_305_checkpoint" >&2
    exit 2
fi
run_branch aria305 interval_size_b005 staged_interval_size_softmax_rr 0.05 "$task_305_checkpoint"
run_branch aria305 interval_size_b01 staged_interval_size_softmax_rr 0.1 "$task_305_checkpoint"

task_12f_data="$task_data_root/aria12F"
task_12f_common="$task_root/aria12F_common_rr_r4_15k_s0"
if [[ -e "$task_12f_common" ]]; then
    echo "Refusing to overwrite existing output: $task_12f_common" >&2
    exit 2
fi
"$task_python" train.py \
    -s "$task_12f_data" -m "$task_12f_common" -r 4 --eval \
    --iterations 15000 --test_iterations 999999 \
    --checkpoint_iterations 14999 \
    --view_schedule "$task_12f_data/causal_arrivals.json" \
    --view_scheduler causal_rr --scheduler_seed 0 --quiet --disable_viewer \
    > "$task_12f_common.log" 2>&1
task_12f_checkpoint="$task_12f_common/chkpnt14999.pth"

run_branch aria12F rr causal_rr 0 "$task_12f_checkpoint"
run_branch aria12F interval_size_b002 staged_interval_size_softmax_rr 0.02 "$task_12f_checkpoint"
run_branch aria12F interval_size_b005 staged_interval_size_softmax_rr 0.05 "$task_12f_checkpoint"
run_branch aria12F interval_size_b01 staged_interval_size_softmax_rr 0.1 "$task_12f_checkpoint"
