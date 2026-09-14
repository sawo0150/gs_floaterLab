#!/usr/bin/env bash
set -euo pipefail

task_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_repo=/home/intern/gs_floaterLab/repos/main/3dgs-custom
task_data=/home/intern/gs_floaterLab/data/exp74_causal_offline/aria305
task_schedule="$task_data/causal_arrivals.json"
task_root=/home/intern/gs_floaterLab/context/experiments/exp75/evidence/shared_branch
task_common="$task_root/aria305_common_rr_r4_15k_s0"

mkdir -p "$task_root"
cd "$task_repo"
if [[ -e "$task_common" ]]; then
    echo "Refusing to overwrite existing output: $task_common" >&2
    exit 2
fi
"$task_python" train.py \
    -s "$task_data" -m "$task_common" -r 4 --eval \
    --iterations 15000 --test_iterations 999999 \
    --checkpoint_iterations 14999 \
    --view_schedule "$task_schedule" --view_scheduler causal_rr \
    --scheduler_seed 0 --quiet --disable_viewer \
    > "$task_common.log" 2>&1

task_checkpoint="$task_common/chkpnt14999.pth"
for task_arm in rr interval_size; do
    if [[ "$task_arm" == rr ]]; then
        task_scheduler=causal_rr
        task_beta=0
    else
        task_scheduler=staged_interval_size_softmax_rr
        task_beta=0.02
    fi
    task_output="$task_root/aria305_shared_${task_arm}_K32_b002_r4_45k_s0"
    if [[ -e "$task_output" ]]; then
        echo "Refusing to overwrite existing output: $task_output" >&2
        exit 2
    fi
    "$task_python" train.py \
        -s "$task_data" -m "$task_output" -r 4 --eval \
        --iterations 45000 --test_iterations 999999 \
        --save_iterations 30000 45000 \
        --start_checkpoint "$task_checkpoint" \
        --view_schedule "$task_schedule" --view_scheduler "$task_scheduler" \
        --scheduler_seed 0 --scheduler_beta "$task_beta" --scheduler_block_size 32 \
        --quiet --disable_viewer \
        > "$task_output.log" 2>&1
done
