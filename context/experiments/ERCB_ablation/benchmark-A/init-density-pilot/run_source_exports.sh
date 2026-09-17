#!/usr/bin/env bash
set -euo pipefail

lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
vigs_repo=/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-main-integration-20260828
output_root="$lab_root/results/ERCB_ablation/benchmark-A_init_density_source"
runner="$vigs_repo/exp81_axes/run_utmm_strict15x_baseline.sh"

run_source() {
    local family=$1
    local scene=$2
    local output=$3
    local dataset_root=$4
    local image_dir=$5
    local imu_file=$6
    local calibration=$7
    local config=$8
    local undistort=$9
    local imu_init=${10}

    if [ -e "$output" ]; then
        echo "refusing existing source output: $output" >&2
        return 2
    fi
    if nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q '[0-9]'; then
        echo "GPU compute process active; wait without killing it" >&2
        return 3
    fi
    mkdir -p "$output"
    export VIGS_DEPTH_ANCHOR_SECONDARY_LOG="$output/points3D_stride20.txt"
    export VIGS_DEPTH_ANCHOR_SECONDARY_STRIDE=20
    export EXP81_HARDWARE_PROFILE=rtx5070ti
    export EXP81_REPLAY_TIME_SCALE=1
    export EXP81_STREAM_PROTOCOL=strict_zero_tail
    export EXP81_FRONTEND_RECIPE=quality
    export EXP81_MAPPING_PROFILE=final_v7
    export EXP81_DENSITY_RECIPE=configured
    export EXP81_DATASET_ROOT="$dataset_root"
    export EXP81_IMAGE_DIR="$image_dir"
    export EXP81_IMU_FILE="$imu_file"
    export EXP81_CALIBRATION="$calibration"
    export EXP81_CONFIG_FILE="$config"
    export EXP81_DATASET_LABEL="$family/$scene"
    export EXP81_UNDISTORT="$undistort"
    export EXP81_IMU_POSEINIT_AFTER="$imu_init"
    unset EXP81_LENGTH
    bash "$runner" "$scene" "$output" >"$output/run.log" 2>&1
    test -s "$output/points3D.txt"
    test -s "$output/points3D_stride20.txt"
    test -s "$output/traj_full_online_eval.txt"
    test -s "$output/traj_kf_beforeBA.txt"
}

utmm_root="$lab_root/data/benchmarks/utmm/prepared/UTMM_Dataset/square-1"
run_source \
    utmm square-1 "$output_root/utmm/square-1/seed0" \
    "$utmm_root" "$utmm_root/rgb_timestamp" "$utmm_root/imu_ours.txt" \
    "$utmm_root/intrinsics_ours.txt" "$vigs_repo/config/exp81_utmm_baseline.yaml" 0 15

rpng_root="$lab_root/data/benchmarks/rpng/prepared/rpngar/table_01"
run_source \
    rpng table_01 "$output_root/rpng/table_01/seed0" \
    "$rpng_root" "$rpng_root/rgb" "$rpng_root/imu.txt" \
    "$vigs_repo/calib/rpngar.txt" "$vigs_repo/config/exp83_rpng_baseline.yaml" 1 20
