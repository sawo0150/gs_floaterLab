#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_exp=/home/intern/gs_floaterLab/context/experiments/exp75
task_root="$task_exp/evidence/shared_branch"
task_gamma=0.6931471805599453

cd "$task_repo"

run_scene () {
    local task_scene=$1
    local task_data=$2
    local task_t1=$3
    local task_t2=$4
    local task_t4=$5
    local task_checkpoint="$task_root/${task_scene}_common_rr_r4_15k_s0/chkpnt14999.pth"
    if [[ ! -f "$task_checkpoint" ]]; then
        echo "Missing shared checkpoint: $task_checkpoint" >&2
        exit 2
    fi
    for task_arm in rr two_pass_odds2; do
        if [[ "$task_arm" == rr ]]; then
            task_scheduler=causal_rr
            task_beta=0
        else
            task_scheduler=staged_two_pass_interval_size_softmax_rr
            task_beta=$task_gamma
        fi
        task_output="$task_root/${task_scene}_normE_shared_${task_arm}_K32_r4_s0"
        if [[ ! -e "$task_output" ]]; then
            "$task_python" train.py \
                -s "$task_data" -m "$task_output" -r 4 --eval \
                --iterations "$task_t4" --test_iterations 999999 \
                --save_iterations "$task_t1" "$task_t2" "$task_t4" \
                --start_checkpoint "$task_checkpoint" \
                --view_schedule "$task_data/causal_arrivals.json" \
                --view_scheduler "$task_scheduler" --scheduler_seed 0 \
                --scheduler_beta "$task_beta" --scheduler_block_size 32 \
                --quiet --disable_viewer > "$task_output.log" 2>&1
        fi
        for task_iteration in "$task_t1" "$task_t2" "$task_t4"; do
            if [[ ! -d "$task_output/test/ours_${task_iteration}/renders" ]]; then
                "$task_python" render.py \
                    -s "$task_data" -m "$task_output" -r 4 --eval \
                    --iteration "$task_iteration" --skip_train --quiet \
                    > "$task_output.render${task_iteration}.log" 2>&1
            fi
        done
    done
}

# T_E = last_arrival + E * final_train_pool_size, E in {1,2,4}.
run_scene aria305 /home/intern/gs_floaterLab/data/exp74_causal_offline/aria305 21013 23365 28069
run_scene aria12F /home/intern/gs_floaterLab/data/exp74_causal_offline/aria12F 26346 28271 32121
run_scene aria3F /home/intern/gs_floaterLab/data/exp75_causal_offline/aria3F 40741 45001 53521
