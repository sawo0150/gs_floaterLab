#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_data_root=/home/intern/gs_floaterLab/data/exp74_causal_offline
task_root=/home/intern/gs_floaterLab/context/experiments/exp75/evidence/shared_branch

cd "$task_repo"

for task_scene in aria305 aria12F; do
    task_data="$task_data_root/$task_scene"
    task_checkpoint="$task_root/${task_scene}_common_rr_r4_15k_s1/chkpnt14999.pth"
    if [[ ! -f "$task_checkpoint" ]]; then
        echo "Missing shared checkpoint: $task_checkpoint" >&2
        exit 2
    fi
    for task_spec in odds2:0.6931471805599453 odds4:1.3862943611198906 odds8:2.0794415416798357; do
        task_label=${task_spec%%:*}
        task_gamma=${task_spec#*:}
        task_output="$task_root/${task_scene}_shared_two_pass_${task_label}_K32_r4_45k_s1"
        if [[ ! -e "$task_output" ]]; then
            "$task_python" train.py \
                -s "$task_data" -m "$task_output" -r 4 --eval \
                --iterations 45000 --test_iterations 999999 \
                --save_iterations 30000 45000 \
                --start_checkpoint "$task_checkpoint" \
                --view_schedule "$task_data/causal_arrivals.json" \
                --view_scheduler staged_two_pass_interval_size_softmax_rr \
                --scheduler_seed 1 --scheduler_beta "$task_gamma" \
                --scheduler_block_size 32 --quiet --disable_viewer \
                > "$task_output.log" 2>&1
        fi
        for task_iteration in 30000 45000; do
            if [[ ! -d "$task_output/test/ours_${task_iteration}/renders" ]]; then
                "$task_python" render.py \
                    -s "$task_data" -m "$task_output" -r 4 --eval \
                    --iteration "$task_iteration" --skip_train --quiet \
                    > "$task_output.render${task_iteration}.log" 2>&1
            fi
        done
    done
done
