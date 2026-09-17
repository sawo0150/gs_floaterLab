#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_data_root=/home/intern/gs_floaterLab/data/exp74_causal_offline
task_output_root=/home/intern/gs_floaterLab/context/experiments/exp75/evidence/interval_runs

mkdir -p "$task_output_root"
cd "$task_repo"

for task_scene in aria305 aria12F; do
    task_data="$task_data_root/$task_scene"
    task_output="$task_output_root/${task_scene}_interval_size_K32_b002_r4_45k_s0"
    if [[ -e "$task_output" ]]; then
        echo "Refusing to overwrite existing output: $task_output" >&2
        exit 2
    fi
    "$task_python" train.py \
        -s "$task_data" \
        -m "$task_output" \
        -r 4 \
        --eval \
        --iterations 45000 \
        --test_iterations 45000 \
        --save_iterations 30000 45000 \
        --view_schedule "$task_data/causal_arrivals.json" \
        --view_scheduler interval_size_softmax_rr \
        --scheduler_seed 0 \
        --scheduler_beta 0.02 \
        --scheduler_block_size 32 \
        --quiet \
        --disable_viewer \
        > "$task_output.log" 2>&1
done
