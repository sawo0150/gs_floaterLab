#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_root=/home/intern/gs_floaterLab/context/experiments/exp75/evidence/zero_tail_runs

cd "$task_repo"

run_scene () {
    local task_scene=$1
    local task_data=$2
    local task_mid1=$3
    local task_mid2=$4
    local task_final=$5
    for task_seed in 0 1; do
        task_output="$task_root/${task_scene}_zerotail_relative_half_odds3_K8_r4_s${task_seed}"
        if [[ -e "$task_output" ]]; then
            echo "Refusing to overwrite existing output: $task_output" >&2
            exit 2
        fi
        "$task_python" train.py \
            -s "$task_data" -m "$task_output" -r 4 --eval \
            --iterations "$task_final" --test_iterations 999999 \
            --save_iterations "$task_mid1" "$task_mid2" "$task_final" \
            --view_schedule "$task_data/causal_arrivals.json" \
            --view_scheduler relative_floor_interval_softmax_rr \
            --scheduler_seed "$task_seed" --scheduler_beta 1.0986122886681098 \
            --scheduler_block_size 8 --quiet --disable_viewer \
            > "$task_output.log" 2>&1
        "$task_python" render.py \
            -s "$task_data" -m "$task_output" -r 4 --eval \
            --iteration "$task_final" --skip_train --quiet \
            > "$task_output.render${task_final}.log" 2>&1
    done
}

run_scene aria305 /home/intern/gs_floaterLab/data/exp74_causal_offline/aria305 10000 15000 18661
run_scene aria3F /home/intern/gs_floaterLab/data/exp75_causal_offline/aria3F 15000 25000 36481
