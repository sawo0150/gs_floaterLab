#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_data=/home/intern/gs_floaterLab/data/exp75_causal_offline/aria3F
task_root=/home/intern/gs_floaterLab/context/experiments/exp75/evidence/zero_tail_runs
task_output="$task_root/aria3F_zerotail_relative_half_odds4_K8_r4_s0"

cd "$task_repo"
if [[ -e "$task_output" ]]; then
    echo "Refusing to overwrite existing output: $task_output" >&2
    exit 2
fi

"$task_python" train.py \
    -s "$task_data" -m "$task_output" -r 4 --eval \
    --iterations 36481 --test_iterations 999999 \
    --save_iterations 15000 25000 36481 \
    --view_schedule "$task_data/causal_arrivals.json" \
    --view_scheduler relative_floor_interval_softmax_rr \
    --scheduler_seed 0 --scheduler_beta 1.3862943611198906 \
    --scheduler_block_size 8 --quiet --disable_viewer \
    > "$task_output.log" 2>&1

"$task_python" render.py \
    -s "$task_data" -m "$task_output" -r 4 --eval \
    --iteration 36481 --skip_train --quiet \
    > "$task_output.render36481.log" 2>&1
