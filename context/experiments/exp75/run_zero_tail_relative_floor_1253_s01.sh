#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_data=/home/intern/gs_floaterLab/data/exp74_causal_offline/aria1253
task_root=/home/intern/gs_floaterLab/context/experiments/exp75/evidence/zero_tail_runs

cd "$task_repo"

for task_seed in 0 1; do
    for task_arm in rr relative_half_odds4; do
        if [[ "$task_arm" == rr ]]; then
            task_scheduler=causal_rr
            task_beta=0
        else
            task_scheduler=relative_floor_interval_softmax_rr
            task_beta=1.3862943611198906
        fi

        task_output="$task_root/aria1253_zerotail_${task_arm}_K8_r4_s${task_seed}"
        if [[ -e "$task_output" ]]; then
            echo "Refusing to overwrite existing output: $task_output" >&2
            exit 2
        fi

        "$task_python" train.py \
            -s "$task_data" -m "$task_output" -r 4 --eval \
            --iterations 8821 --test_iterations 999999 \
            --save_iterations 4000 6500 8821 \
            --view_schedule "$task_data/causal_arrivals.json" \
            --view_scheduler "$task_scheduler" --scheduler_seed "$task_seed" \
            --scheduler_beta "$task_beta" --scheduler_block_size 8 \
            --quiet --disable_viewer > "$task_output.log" 2>&1

        "$task_python" render.py \
            -s "$task_data" -m "$task_output" -r 4 --eval \
            --iteration 8821 --skip_train --quiet \
            > "$task_output.render8821.log" 2>&1
    done
done
