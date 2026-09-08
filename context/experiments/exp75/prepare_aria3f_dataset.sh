#!/usr/bin/env bash
set -euo pipefail

task_aria_python=/home/intern/VIGS-SLAM-main-integration-20260828/extensions/aria_gen2_live/.source-envs/gen2/bin/python
task_3dgs_python=/home/colin/miniconda3/envs/3dgs/bin/python
task_converter=/home/intern/gs_floaterLab/repos/main/3dgs-custom/aria_to_3dgs.py
task_scheduler=/home/intern/gs_floaterLab/context/experiments/exp75/make_pseudo_kf_schedule.py
task_raw=/home/intern/aria_data/0416_Data/0416_301-3F-002
task_mps="$task_raw/mps_0416_301-3F_vrs/slam"
task_output=/home/intern/gs_floaterLab/data/exp75_causal_offline/aria3F

if [[ -e "$task_output" ]]; then
    echo "Refusing to overwrite existing output: $task_output" >&2
    exit 2
fi

"$task_aria_python" "$task_converter" \
    --aria_dir "$task_raw" \
    --output_dir "$task_output" \
    --vrs_file "$task_raw/0416_301-3F.vrs" \
    --trajectory_csv "$task_mps/closed_loop_trajectory.csv" \
    --points_csv "$task_mps/semidense_points.csv.gz" \
    --width 1024 \
    --height 1024 \
    --frame_stride 1 \
    --max_points 50000 \
    --point_seed 0

"$task_3dgs_python" "$task_scheduler" \
    --dataset "$task_output" \
    --rgb-per-interval 8 \
    --iters-per-interval 60 \
    --tail-iters 3000
