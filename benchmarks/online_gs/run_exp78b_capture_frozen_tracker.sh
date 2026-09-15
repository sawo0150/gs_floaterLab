#!/usr/bin/env bash
# Capture one mapper-independent official VIGS tracker trace for exp78 Lane B.
set -euo pipefail

if [ "$#" -ne 4 ]; then
    echo "usage: $0 <rpng|utmm> <sequence> <seed> <output-dir>" >&2
    exit 2
fi

workspace_root='/home/intern/gs_floaterLab'
official_root='/home/intern/VIGS-SLAM-official-exp78'
python_env='/home/colin/miniconda3/envs/vigs-slam-5090'
expected_commit='22ffe24c6df81d0bf63bd20057565c00c51d2996'
runtime_root=${EXP78_TRT_RUNTIME_ROOT:-$official_root}
dataset=$1
sequence=$2
seed=$3
output_dir=$(realpath -m "$4")

case "$dataset" in
    rpng)
        sequence_root="$workspace_root/data/benchmarks/rpng/prepared/rpngar/$sequence"
        image_dir="$sequence_root/rgb"
        imu_file="$sequence_root/imu.txt"
        calibration="$official_root/calib/rpngar.txt"
        config="$official_root/config/rpng.yaml"
        heldout="$workspace_root/context/experiments/exp78/b_strict_fair_comparison/manifests/rpng_${sequence}.json"
        buffer=700
        imu_init=20
        ;;
    utmm)
        sequence_root="$workspace_root/data/benchmarks/utmm/prepared/UTMM_Dataset/$sequence"
        image_dir="$sequence_root/rgb_timestamp"
        imu_file="$sequence_root/imu_ours.txt"
        calibration="$sequence_root/intrinsics_ours.txt"
        config="$official_root/config/utmm.yaml"
        heldout="$workspace_root/context/experiments/exp78/b_strict_fair_comparison/manifests/utmm_${sequence}.json"
        buffer=1200
        imu_init=15
        ;;
    *)
        echo "dataset must be rpng or utmm" >&2
        exit 2
        ;;
esac

actual_commit=$(git -C "$official_root" rev-parse HEAD)
if [ "$actual_commit" != "$expected_commit" ]; then
    echo "official source commit mismatch: $actual_commit" >&2
    exit 2
fi
git -C "$official_root" diff --quiet --ignore-submodules=dirty
git -C "$official_root" diff --cached --quiet --ignore-submodules=dirty

for path in "$image_dir" "$imu_file" "$calibration" "$config" "$heldout" \
            "$official_root/pretrained_models/droid.pth"; do
    if [ ! -e "$path" ]; then
        echo "missing required input: $path" >&2
        exit 2
    fi
done

if [ "$runtime_root" != "$official_root" ]; then
    runtime_root=$(realpath "$runtime_root")
    for engine in \
        omnidata_depth_512_simplified_fp16.engine \
        omnidata_normal_512_simplified_fp16.engine \
        droidnet_fnet_fp16.engine \
        update_module_partial_fp16.engine \
        update_module_partial_pgba_fp16.engine; do
        test -f "$runtime_root/pretrained_models/$engine"
    done
fi

mkdir -p "$output_dir"
export PYTHONUNBUFFERED=1
export PYTHONPATH="$official_root:$official_root/thirdparty/diff-gaussian-rasterization:$official_root/thirdparty/simple-knn:$official_root/thirdparty/lietorch_5090:$official_root/vigs${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH="$python_env/lib/python3.11/site-packages/torch/lib:$python_env/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

{
    echo "protocol=exp78b_frozen_tracker_v3_split_geometry"
    echo "dataset=$dataset"
    echo "sequence=$sequence"
    echo "seed=$seed"
    echo "official_commit=$actual_commit"
    echo "runtime_root=$runtime_root"
    echo "tensorrt=$([ "$runtime_root" = "$official_root" ] && echo off || echo on)"
    echo "gaussian_mapping=archive_sink_no_optimizer"
    sha256sum \
        "$workspace_root/benchmarks/online_gs/exp78b_capture_frozen_tracker.py" \
        "$config" "$calibration" "$imu_file" "$heldout" \
        "$official_root/pretrained_models/droid.pth"
    find "$image_dir" -maxdepth 1 -type f -printf '%f %s\n' | sort | sha256sum
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
} > "$output_dir/source_manifest.txt"

cd "$runtime_root"
exec "$python_env/bin/python" \
    "$workspace_root/benchmarks/online_gs/exp78b_capture_frozen_tracker.py" \
    --dataset "$dataset" \
    --sequence "$sequence" \
    --imagedir "$image_dir" \
    --imufile "$imu_file" \
    --calib "$calibration" \
    --config "$config" \
    --weights "$official_root/pretrained_models/droid.pth" \
    --heldout-manifest "$heldout" \
    --output "$output_dir" \
    --buffer "$buffer" \
    --IMU_poseinit_after "$imu_init" \
    --undistort \
    --seed "$seed" \
    2>&1 | tee "$output_dir/run.log"
