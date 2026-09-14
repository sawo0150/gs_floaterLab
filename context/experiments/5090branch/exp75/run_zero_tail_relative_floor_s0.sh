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
    for task_spec in odds2:0.6931471805599453 odds4:1.3862943611198906; do
        task_label=${task_spec%%:*}
        task_gamma=${task_spec#*:}
        task_output="$task_root/${task_scene}_zerotail_relative_half_${task_label}_K8_r4_s0"
        if [[ ! -e "$task_output" ]]; then
            "$task_python" train.py \
                -s "$task_data" -m "$task_output" -r 4 --eval \
                --iterations "$task_final" --test_iterations 999999 \
                --save_iterations "$task_mid1" "$task_mid2" "$task_final" \
                --view_schedule "$task_data/causal_arrivals.json" \
                --view_scheduler relative_floor_interval_softmax_rr \
                --scheduler_seed 0 --scheduler_beta "$task_gamma" \
                --scheduler_block_size 8 --quiet --disable_viewer \
                > "$task_output.log" 2>&1
        elif [[ ! -f "$task_output/point_cloud/iteration_${task_final}/point_cloud.ply" ]]; then
            echo "Refusing to reuse incomplete output: $task_output" >&2
            exit 2
        fi
        if [[ ! -d "$task_output/test/ours_${task_final}/renders" ]]; then
            "$task_python" render.py \
                -s "$task_data" -m "$task_output" -r 4 --eval \
                --iteration "$task_final" --skip_train --quiet \
                > "$task_output.render${task_final}.log" 2>&1
        fi
    done
}

run_scene aria305 /home/intern/gs_floaterLab/data/exp74_causal_offline/aria305 10000 15000 18661
run_scene aria12F /home/intern/gs_floaterLab/data/exp74_causal_offline/aria12F 12000 18000 24421
