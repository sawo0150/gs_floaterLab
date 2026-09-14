#!/usr/bin/env bash
# Run one original-VIGS scene with a fixed 1.5x deadline and no map tail.
set -euo pipefail

family=${1:?usage: run_one.sh FAMILY SCENE [OUTPUT_DIR]}
scene=${2:?usage: run_one.sh FAMILY SCENE [OUTPUT_DIR]}
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
vanilla_repo=/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-vanilla-check
sensor_repo=/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-main-integration-20260828
expected_commit=22ffe24c6df81d0bf63bd20057565c00c51d2996
conda_env=/home/wosas/miniconda3/envs/vigs-slam-5090
output_dir=${3:-"$lab_root/results/benchmarks/benchmark_vanila/5070ti_1.5x_strict/$family/$scene/origin22ffe24_pure_online_strict15x"}

case "$family:$scene" in
    aria:aria1253|aria:aria1253rot|aria:aria301_12F|aria:aria301_305)
        dataset_root="$sensor_repo/data/$scene"
        image_dir="$dataset_root/rgb"
        imu_file="$dataset_root/imu.txt"
        calib_file="$sensor_repo/calib/$scene.txt"
        config_file="$script_dir/config/aria_parallel.yaml"
        extra_args=(--IMU_poseinit_after 20 --buffer -1)
        ;;
    utmm:*)
        dataset_root="$lab_root/data/benchmarks/utmm/prepared/UTMM_Dataset/$scene"
        image_dir="$dataset_root/rgb_timestamp"
        imu_file="$dataset_root/imu_ours.txt"
        calib_file="$dataset_root/intrinsics_ours.txt"
        config_file="$script_dir/config/utmm_parallel.yaml"
        extra_args=(--undistort --IMU_poseinit_after 15 --buffer -1)
        ;;
    rpng:table_0[1-8])
        dataset_root="$lab_root/data/benchmarks/rpng/prepared/rpngar/$scene"
        image_dir="$dataset_root/rgb"
        imu_file="$dataset_root/imu.txt"
        calib_file="$vanilla_repo/calib/rpngar.txt"
        config_file="$script_dir/config/rpng_parallel.yaml"
        extra_args=(--undistort --IMU_poseinit_after 20 --buffer 700)
        ;;
    *)
        echo "unsupported strict vanilla scene: $family/$scene" >&2
        exit 2
        ;;
esac

for required in "$image_dir" "$imu_file" "$calib_file" "$config_file" "$conda_env/bin/python"; do
    if [ ! -e "$required" ]; then
        echo "missing required input: $required" >&2
        exit 2
    fi
done

actual_commit=$(git -C "$vanilla_repo" rev-parse HEAD)
if [ "$actual_commit" != "$expected_commit" ]; then
    echo "unexpected vanilla commit: $actual_commit (expected $expected_commit)" >&2
    exit 2
fi

result_file="$output_dir/psnr/after_opt/final_result.json"
if [ -f "$result_file" ] && [ -f "$output_dir/sensor_eos_audit.json" ]; then
    echo "completed result already exists; refusing to overwrite: $output_dir" >&2
    exit 2
fi
if [ -d "$output_dir" ] && [ -n "$(find "$output_dir" -mindepth 1 -print -quit)" ]; then
    echo "non-empty incomplete output exists; refusing to overwrite: $output_dir" >&2
    exit 2
fi

gpu_jobs=$(nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader || true)
if [ -n "$gpu_jobs" ]; then
    echo "GPU already has compute work; leaving it untouched:" >&2
    echo "$gpu_jobs" >&2
    exit 3
fi

mkdir -p "$output_dir"
exec > >(tee "$output_dir/run.log") 2>&1

conda_root=${conda_env%%/envs/*}
source "$conda_root/etc/profile.d/conda.sh"
conda activate "$conda_env"

export VIGS_VANILLA_REPO="$vanilla_repo"
export PYTHONPATH="$vanilla_repo/thirdparty/diff-gaussian-rasterization${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1

frame_count=$(find -L "$image_dir" -maxdepth 1 -type f | wc -l)
length_args=()
if [ -n "${STRICT_LENGTH:-}" ]; then
    length_args=(--length "$STRICT_LENGTH")
fi
echo "BENCHMARK_VANILLA_STRICT_CONTRACT family=$family scene=$scene frames=$frame_count commit=$actual_commit gpu=RTX5070Ti replay_time_scale=1.5 fixed_deadline=1 zero_tail=1 pending_queue_discard=1 physical_adam_counter=1 pure_online=1 final_ba=0 color_refinement=0 seed=upstream_default_not_explicitly_set"
echo "BENCHMARK_VANILLA_STRICT_ADAPTER config=$config_file calib=$calib_file args=${extra_args[*]} length=${STRICT_LENGTH:-all}"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader

cd "$vanilla_repo"
exec /usr/bin/time -v python "$script_dir/streaming_demo.py" \
    --imagedir "$image_dir" \
    --imufile "$imu_file" \
    --calib "$calib_file" \
    --config "$config_file" \
    --output "$output_dir" \
    --gsmapping \
    --pure_online \
    --replay_time_scale 1.5 \
    --strict_zero_tail \
    --strict_margin_seconds "${STRICT_MARGIN_SECONDS:-0.05}" \
    "${length_args[@]}" \
    "${extra_args[@]}"
