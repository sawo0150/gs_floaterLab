#!/usr/bin/env bash
# Run one original-VIGS scene with no final BA or offline color refinement.
set -euo pipefail

family=${1:?usage: run_one.sh FAMILY SCENE [OUTPUT_DIR]}
scene=${2:?usage: run_one.sh FAMILY SCENE [OUTPUT_DIR]}
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
source_repo=/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM
vanilla_repo=/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-vanilla-check
expected_commit=22ffe24c6df81d0bf63bd20057565c00c51d2996
conda_env=/home/wosas/miniconda3/envs/vigs-slam-5090
output_dir=${3:-"$lab_root/results/benchmarks/benchmark_vanila/synchronous_unbounded/$family/$scene/origin22ffe24_pure_online_seed0"}

case "$family:$scene" in
    utmm:*)
        dataset_root="$lab_root/data/benchmarks/utmm/prepared/UTMM_Dataset/$scene"
        image_dir="$dataset_root/rgb_timestamp"
        imu_file="$dataset_root/imu_ours.txt"
        calib_file="$dataset_root/intrinsics_ours.txt"
        config_file="$vanilla_repo/config/utmm.yaml"
        extra_args=(--undistort --IMU_poseinit_after 15 --buffer -1)
        ;;
    rpng:table_0[1-8])
        dataset_root="$lab_root/data/benchmarks/rpng/prepared/rpngar/$scene"
        image_dir="$dataset_root/rgb"
        imu_file="$dataset_root/imu.txt"
        calib_file="$vanilla_repo/calib/rpngar.txt"
        config_file="$vanilla_repo/config/rpng.yaml"
        extra_args=(--undistort --IMU_poseinit_after 20 --buffer 700)
        ;;
    aria:aria1253)
        dataset_root="$source_repo/data/aria1253"
        image_dir="$dataset_root/rgb"
        imu_file="$dataset_root/imu.txt"
        calib_file="$vanilla_repo/calib/aria1253.txt"
        config_file="$vanilla_repo/config/exp_depth_normal_ablation/aria1253_both_on.yaml"
        extra_args=(--buffer -1)
        ;;
    aria:aria301_305)
        dataset_root="$source_repo/data/aria301_305"
        image_dir="$dataset_root/rgb"
        imu_file="$dataset_root/imu.txt"
        calib_file="$source_repo/calib/aria301_305.txt"
        config_file="$vanilla_repo/config/aria301_305_vanilla.yaml"
        extra_args=(--buffer -1)
        ;;
    *)
        echo "unsupported family/scene: $family/$scene" >&2
        exit 2
        ;;
esac

for required in \
    "$image_dir" \
    "$imu_file" \
    "$calib_file" \
    "$config_file" \
    "$conda_env/bin/python"; do
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
if [ -f "$result_file" ]; then
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

export VIGS_EVAL_PURE_ONLINE=1
export PYTHONPATH="$vanilla_repo/thirdparty/diff-gaussian-rasterization${PYTHONPATH:+:$PYTHONPATH}"

frame_count=$(find -L "$image_dir" -maxdepth 1 -type f | wc -l)
echo "BENCHMARK_VANILA_CONTRACT family=$family scene=$scene frames=$frame_count commit=$actual_commit gsmapping=1 pure_online=1 final_ba=0 color_refinement=0 synchronous_unbounded=1 eval_only_hook=1 seed=upstream_default_not_explicitly_set"
echo "BENCHMARK_VANILA_ADAPTER config=$config_file calib=$calib_file args=${extra_args[*]}"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader

cd "$vanilla_repo"
exec /usr/bin/time -v python demo.py \
    --imagedir "$image_dir" \
    --imufile "$imu_file" \
    --calib "$calib_file" \
    --config "$config_file" \
    --output "$output_dir" \
    --gsmapping \
    --pure_online \
    "${extra_args[@]}"
