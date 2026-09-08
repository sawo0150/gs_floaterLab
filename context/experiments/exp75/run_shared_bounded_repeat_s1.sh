#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_data_root=/home/intern/gs_floaterLab/data/exp74_causal_offline
task_root=/home/intern/gs_floaterLab/context/experiments/exp75/evidence/shared_branch
task_gamma=0.6931471805599453

cd "$task_repo"

for task_scene in aria305 aria12F; do
    task_data="$task_data_root/$task_scene"
    task_common="$task_root/${task_scene}_common_rr_r4_15k_s1"
    if [[ -e "$task_common" ]]; then
        echo "Refusing to overwrite existing output: $task_common" >&2
        exit 2
    fi
    "$task_python" train.py \
        -s "$task_data" -m "$task_common" -r 4 --eval \
        --iterations 15000 --test_iterations 999999 \
        --checkpoint_iterations 14999 \
        --view_schedule "$task_data/causal_arrivals.json" \
        --view_scheduler causal_rr --scheduler_seed 1 \
        --quiet --disable_viewer > "$task_common.log" 2>&1

    for task_arm in rr bounded_odds2; do
        if [[ "$task_arm" == rr ]]; then
            task_scheduler=causal_rr
            task_beta=0
        else
            task_scheduler=staged_bounded_interval_size_softmax_rr
            task_beta=$task_gamma
        fi
        task_output="$task_root/${task_scene}_shared_${task_arm}_K32_r4_45k_s1"
        if [[ -e "$task_output" ]]; then
            echo "Refusing to overwrite existing output: $task_output" >&2
            exit 2
        fi
        "$task_python" train.py \
            -s "$task_data" -m "$task_output" -r 4 --eval \
            --iterations 45000 --test_iterations 999999 \
            --save_iterations 30000 45000 \
            --start_checkpoint "$task_common/chkpnt14999.pth" \
            --view_schedule "$task_data/causal_arrivals.json" \
            --view_scheduler "$task_scheduler" --scheduler_seed 1 \
            --scheduler_beta "$task_beta" --scheduler_block_size 32 \
            --quiet --disable_viewer > "$task_output.log" 2>&1
    done
done
