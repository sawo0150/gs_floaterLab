#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_data=/home/intern/gs_floaterLab/data/exp74_causal_offline/aria1253
task_output_root=/home/intern/gs_floaterLab/context/experiments/exp75/evidence/interval_runs

mkdir -p "$task_output_root"
cd "$task_repo"

for task_beta_tag in 0 00025 0005 001; do
    case "$task_beta_tag" in
        0) task_beta=0 ;;
        00025) task_beta=0.0025 ;;
        0005) task_beta=0.005 ;;
        001) task_beta=0.01 ;;
    esac
    task_output="$task_output_root/aria1253_interval_K32_b${task_beta_tag}_r4_45k_s0"
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
        --view_scheduler interval_softmax_rr \
        --scheduler_seed 0 \
        --scheduler_beta "$task_beta" \
        --scheduler_block_size 32 \
        --quiet \
        --disable_viewer \
        > "$task_output.log" 2>&1
done
