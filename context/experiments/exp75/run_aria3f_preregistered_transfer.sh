#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_data=/home/intern/gs_floaterLab/data/exp75_causal_offline/aria3F
task_output_root=/home/intern/gs_floaterLab/context/experiments/exp75/evidence/external_runs

mkdir -p "$task_output_root"
cd "$task_repo"

for task_arm in rr interval_size; do
    if [[ "$task_arm" == rr ]]; then
        task_scheduler=causal_rr
        task_beta=0
        task_block_size=32
    else
        task_scheduler=interval_size_softmax_rr
        task_beta=0.02
        task_block_size=32
    fi
    task_output="$task_output_root/aria3F_${task_arm}_K32_b002_r4_79081_s0"
    if [[ -e "$task_output" ]]; then
        echo "Refusing to overwrite existing output: $task_output" >&2
        exit 2
    fi
    "$task_python" train.py \
        -s "$task_data" \
        -m "$task_output" \
        -r 4 \
        --eval \
        --iterations 79081 \
        --test_iterations 79081 \
        --save_iterations 45000 79081 \
        --view_schedule "$task_data/causal_arrivals.json" \
        --view_scheduler "$task_scheduler" \
        --scheduler_seed 0 \
        --scheduler_beta "$task_beta" \
        --scheduler_block_size "$task_block_size" \
        --quiet \
        --disable_viewer \
        > "$task_output.log" 2>&1
done
