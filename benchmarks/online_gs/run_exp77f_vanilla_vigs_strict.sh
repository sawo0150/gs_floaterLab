#!/usr/bin/env bash
# Run the official VIGS mapper recipe inside the same fixed-1x, sensor-EOS,
# zero-tail and fixed-held-out harness used by exp77.  This is a strict-runtime
# comparison arm, not a claim of reproducing the paper's native offline timing
# or its unpublished union-of-non-keyframe rendering split.
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <output-dir>" >&2
    exit 2
fi

workspace_root='/home/intern/gs_floaterLab'
vigs_root='/home/intern/VIGS-SLAM-main-integration-20260828'
output_dir=$1
mkdir -p "$output_dir"
output_dir=$(realpath "$output_dir")

image_dir="$workspace_root/data/benchmarks/rpng/prepared/rpngar/table_06/rgb"
imu_file="$workspace_root/data/benchmarks/rpng/prepared/rpngar/table_06/imu.txt"
calibration="$vigs_root/calib/rpngar.txt"
config="$vigs_root/config/rpng.yaml"
conda_env='/home/colin/miniconda3/envs/vigs-slam-5090'

for path in "$image_dir" "$imu_file" "$calibration" "$config"; do
    if [ ! -e "$path" ]; then
        echo "missing required input: $path" >&2
        exit 2
    fi
done

export PYTHONPATH="$vigs_root/thirdparty/diff-gaussian-rasterization${PYTHONPATH:+:$PYTHONPATH}"
export VIGS_DISABLE_FNET_TRT=1
export VIGS_DISABLE_UPDATE_TRT=1
export VIGS_SENSOR_EOS_ZERO_TAIL=1
export VIGS_DEPTH_ANCHOR_LOG="$output_dir/points3D.txt"
export VIGS_DEPTH_ANCHOR_CAM_LOG="$output_dir/images.txt"

strict_harness_commit=$(git -C "$vigs_root" rev-parse --short HEAD)
echo "EXP77F_VANILLA_STRICT vanilla_reference_commit=3deb6ee2 strict_harness_commit=$strict_harness_commit config=$config scale=1 zero_tail=1 trt_fnet=off trt_update=off"
cd "$vigs_root"
exec "$conda_env/bin/python" demo.py \
    --imagedir "$image_dir" \
    --imufile "$imu_file" \
    --calib "$calibration" \
    --config "$config" \
    --output "$output_dir" \
    --gsmapping \
    --pure_online \
    --realtime_replay \
    --replay_time_scale 1 \
    --eval_online_final \
    --eval_metrics_only \
    --mapping_exclude_fixed_eval_views \
    --frontend_iters1 4 \
    --frontend_iters2 2 \
    --IMU_poseinit_after 20 \
    --buffer 700 \
    --mapping_idle_replay_batch_size 1 \
    --late_mapping_start_frame 0 \
    --late_mapping_iters 10 \
    --enable_isotropic_loss \
    2>&1 | tee "$output_dir/run.log"
