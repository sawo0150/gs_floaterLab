#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_data_root=/home/intern/gs_floaterLab/data/exp74_causal_offline
task_output_root=/home/intern/gs_floaterLab/context/experiments/exp75/evidence/anytime_runs
task_checkpoints=(15000 20000 25000 30000 35000 40000 45000)

mkdir -p "$task_output_root"
cd "$task_repo"

for task_scene in aria1253 aria305 aria12F; do
    task_data="$task_data_root/$task_scene"
    for task_arm in rr efloor_r035; do
        if [[ "$task_arm" == rr ]]; then
            task_scheduler=causal_rr
            task_rho=0
        else
            task_scheduler=entropy_floor_rr
            task_rho=0.35
        fi

        task_output="$task_output_root/${task_scene}_${task_arm}_r4_45k_s1"
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
            --save_iterations "${task_checkpoints[@]}" \
            --view_schedule "$task_data/causal_arrivals.json" \
            --view_scheduler "$task_scheduler" \
            --scheduler_seed 1 \
            --scheduler_beta "$task_rho" \
            --scheduler_block_size 128 \
            --quiet \
            --disable_viewer \
            > "$task_output.log" 2>&1
    done
done
