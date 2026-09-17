#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_data=/home/intern/gs_floaterLab/data/exp75_causal_offline/aria3F
task_output=/home/intern/gs_floaterLab/context/experiments/exp75/evidence/external_runs/aria3F_staged_interval_size_K32_b002_r4_79081_s0

if [[ -e "$task_output" ]]; then
    echo "Refusing to overwrite existing output: $task_output" >&2
    exit 2
fi
mkdir -p "$(dirname "$task_output")"
cd "$task_repo"
"$task_python" train.py \
    -s "$task_data" \
    -m "$task_output" \
    -r 4 \
    --eval \
    --iterations 79081 \
    --test_iterations 79081 \
    --save_iterations 45000 79081 \
    --view_schedule "$task_data/causal_arrivals.json" \
    --view_scheduler staged_interval_size_softmax_rr \
    --scheduler_seed 0 \
    --scheduler_beta 0.02 \
    --scheduler_block_size 32 \
    --quiet \
    --disable_viewer \
    > "$task_output.log" 2>&1
