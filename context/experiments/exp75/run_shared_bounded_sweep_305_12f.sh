#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_data_root=/home/intern/gs_floaterLab/data/exp74_causal_offline
task_root=/home/intern/gs_floaterLab/context/experiments/exp75/evidence/shared_branch

cd "$task_repo"

run_branch () {
    local task_scene=$1
    local task_label=$2
    local task_gamma=$3
    local task_checkpoint=$4
    local task_output="$task_root/${task_scene}_shared_bounded_${task_label}_K32_r4_45k_s0"
    if [[ -e "$task_output" ]]; then
        echo "Refusing to overwrite existing output: $task_output" >&2
        exit 2
    fi
    "$task_python" train.py \
        -s "$task_data_root/$task_scene" -m "$task_output" -r 4 --eval \
        --iterations 45000 --test_iterations 999999 \
        --save_iterations 30000 45000 \
        --start_checkpoint "$task_checkpoint" \
        --view_schedule "$task_data_root/$task_scene/causal_arrivals.json" \
        --view_scheduler staged_bounded_interval_size_softmax_rr \
        --scheduler_seed 0 --scheduler_beta "$task_gamma" \
        --scheduler_block_size 32 --quiet --disable_viewer \
        > "$task_output.log" 2>&1
}

for task_scene in aria305 aria12F; do
    task_checkpoint="$task_root/${task_scene}_common_rr_r4_15k_s0/chkpnt14999.pth"
    if [[ ! -f "$task_checkpoint" ]]; then
        echo "Missing shared checkpoint: $task_checkpoint" >&2
        exit 2
    fi
    run_branch "$task_scene" odds2 0.6931471805599453 "$task_checkpoint"
    run_branch "$task_scene" odds4 1.3862943611198906 "$task_checkpoint"
    run_branch "$task_scene" odds8 2.0794415416798357 "$task_checkpoint"
done
