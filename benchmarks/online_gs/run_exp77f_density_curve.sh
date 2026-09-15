#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "usage: $0 <aria_curve|neutral_density> <output-dir>" >&2
    exit 2
fi

workspace_root='/home/intern/gs_floaterLab'
arm=$1
output_dir=$2

case "$arm" in
    aria_curve)
        config="$workspace_root/benchmarks/online_gs/config/vigs_final_v7_rpng.yaml"
        ;;
    neutral_density)
        config="$workspace_root/benchmarks/online_gs/config/vigs_final_v7_rpng_neutral_density.yaml"
        ;;
    *)
        echo "unknown arm: $arm" >&2
        exit 2
        ;;
esac

mkdir -p "$output_dir"
output_dir=$(realpath "$output_dir")
export EXP69_CONFIG_FILE="$config"
export EXP69_IMAGE_DIR="$workspace_root/data/benchmarks/rpng/prepared/rpngar/table_06/rgb"
export EXP69_IMU_FILE="$workspace_root/data/benchmarks/rpng/prepared/rpngar/table_06/imu.txt"
export EXP69_CALIBRATION='/home/intern/VIGS-SLAM-main-integration-20260828/calib/rpngar.txt'
export EXP69_IMU_POSEINIT_AFTER=20
export EXP69_BUFFER_SIZE=700
export EXP77E_RESERVE_MS=0
export VIGS_DISABLE_FNET_TRT=1
export VIGS_DISABLE_UPDATE_TRT=1
export VIGS_KF_CONTENT_LOG="$output_dir/kf_content.csv"
export VIGS_SENSOR_EOS_ZERO_TAIL=1

echo "EXP77F_DENSITY arm=$arm config=$config reserve_ms=0 trt_fnet=off trt_update=off"
exec bash "$workspace_root/benchmarks/online_gs/run_exp77e_reserve.sh" \
    benchmark_rpng_table_06 "$output_dir" baseline
