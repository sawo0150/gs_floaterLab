#!/usr/bin/env bash
# Frozen original-VIGS comparator for the preregistered UTMM transfer panel.
set -euo pipefail

scene=${1:?usage: run_original_vanilla_transfer.sh SCENE [OUTPUT_DIR]}
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
vanilla_repo=/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-vanilla-check
dataset_root="$lab_root/data/benchmarks/utmm/prepared/UTMM_Dataset/$scene"
output_dir=${2:-"$lab_root/results/benchmarks/exp81_vigs_vanilla5070/utmm/$scene/origin22ffe24_pytorch_transfer_seed0"}
expected_commit=22ffe24c6df81d0bf63bd20057565c00c51d2996
conda_env=/home/wosas/miniconda3/envs/vigs-slam-5090

for required in \
    "$dataset_root/rgb_timestamp" \
    "$dataset_root/imu_ours.txt" \
    "$dataset_root/intrinsics_ours.txt" \
    "$vanilla_repo/config/utmm.yaml" \
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

if [ -f "$output_dir/psnr/after_opt/final_result.json" ]; then
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

echo "VANILLA_TRANSFER_CONTRACT scene=$scene commit=$actual_commit config=config/utmm.yaml gsmapping=1 pure_online=1 synchronous_unbounded=1 imu_poseinit_after=15 buffer=-1 eval_only_hook=1 per_view_eval_instrumentation=1"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader

cd "$vanilla_repo"
exec /usr/bin/time -v python demo.py \
    --imagedir "$dataset_root/rgb_timestamp" \
    --imufile "$dataset_root/imu_ours.txt" \
    --calib "$dataset_root/intrinsics_ours.txt" \
    --config config/utmm.yaml \
    --output "$output_dir" \
    --gsmapping \
    --pure_online \
    --undistort \
    --IMU_poseinit_after 15 \
    --buffer -1
