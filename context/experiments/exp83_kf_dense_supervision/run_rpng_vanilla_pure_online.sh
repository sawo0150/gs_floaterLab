#!/usr/bin/env bash
# exp83-R: original VIGS RPNG comparator without final BA/color refinement.
set -euo pipefail

lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
vanilla_repo=/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-vanilla-check
dataset_root="$lab_root/data/benchmarks/rpng/prepared/rpngar/table_01"
output_dir=${1:-"$lab_root/results/benchmarks/exp83_vigs_vanilla5070/rpng/table_01/origin22ffe24_pure_online_first1000_seed0"}
expected_commit=22ffe24c6df81d0bf63bd20057565c00c51d2996
conda_env=/home/wosas/miniconda3/envs/vigs-slam-5090

for required in \
    "$dataset_root/rgb" \
    "$dataset_root/imu.txt" \
    "$vanilla_repo/calib/rpngar.txt" \
    "$vanilla_repo/config/rpng.yaml" \
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
if [ -d "$output_dir" ] && [ -n "$(rg --files -uu "$output_dir" | head -n 1)" ]; then
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

echo "EXP83_R_VANILLA_RPNG contract=pure_online_no_final_ba_no_color_refinement frames=1000 synchronous_unbounded=1 commit=$actual_commit"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader

cd "$vanilla_repo"
exec /usr/bin/time -v python demo.py \
    --imagedir "$dataset_root/rgb" \
    --imufile "$dataset_root/imu.txt" \
    --calib calib/rpngar.txt \
    --config config/rpng.yaml \
    --output "$output_dir" \
    --gsmapping \
    --pure_online \
    --undistort \
    --length 1000 \
    --IMU_poseinit_after 20 \
    --buffer -1
