#!/usr/bin/env bash
# Paper-native VIGS reproduction gate. Runs clean official modules without a
# realtime deadline and stops before final BA / color refinement.
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <output-dir>" >&2
    exit 2
fi

workspace_root='/home/intern/gs_floaterLab'
official_root='/home/intern/VIGS-SLAM-official-exp78'
python_env='/home/colin/miniconda3/envs/vigs-slam-5090'
expected_commit='22ffe24c6df81d0bf63bd20057565c00c51d2996'
output_dir=$(realpath -m "$1")
image_dir="$workspace_root/data/benchmarks/rpng/prepared/rpngar/table_06/rgb"
imu_file="$workspace_root/data/benchmarks/rpng/prepared/rpngar/table_06/imu.txt"
calibration="$official_root/calib/rpngar.txt"
config="$official_root/config/rpng.yaml"
weights="$official_root/pretrained_models/droid.pth"

actual_commit=$(git -C "$official_root" rev-parse HEAD)
if [ "$actual_commit" != "$expected_commit" ]; then
    echo "official source commit mismatch: $actual_commit" >&2
    exit 2
fi
git -C "$official_root" diff --quiet --ignore-submodules=dirty
git -C "$official_root" diff --cached --quiet --ignore-submodules=dirty
if find "$official_root/pretrained_models" -maxdepth 1 -type f -name '*.engine' -print -quit | grep -q .; then
    echo "paper-native PyTorch arm refuses top-level TensorRT engines" >&2
    exit 2
fi
for path in "$image_dir" "$imu_file" "$calibration" "$config" "$weights" \
            "$official_root/pretrained_models/omnidata_dpt_depth_v2.ckpt" \
            "$official_root/pretrained_models/omnidata_dpt_normal_v2.ckpt"; do
    if [ ! -e "$path" ]; then
        echo "missing required input: $path" >&2
        exit 2
    fi
done

mkdir -p "$output_dir"
export PYTHONUNBUFFERED=1
export PYTHONPATH="$official_root:$official_root/thirdparty/diff-gaussian-rasterization:$official_root/thirdparty/simple-knn:$official_root/thirdparty/lietorch_5090:$official_root/vigs${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH="$python_env/lib/python3.11/site-packages/torch/lib:$python_env/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

{
    echo "official_commit=$actual_commit"
    echo "driver=$workspace_root/benchmarks/online_gs/exp78_vigs_native_driver.py"
    echo "tensorrt=off"
    echo "final_ba=off"
    echo "final_color_refinement=off"
    sha256sum "$config" "$calibration" "$weights" \
        "$official_root/pretrained_models/omnidata_dpt_depth_v2.ckpt" \
        "$official_root/pretrained_models/omnidata_dpt_normal_v2.ckpt" \
        "$official_root/vigs_backends.cpython-311-x86_64-linux-gnu.so" \
        "$official_root/thirdparty/lietorch_5090/lietorch_backends.cpython-311-x86_64-linux-gnu.so" \
        "$official_root/thirdparty/diff-gaussian-rasterization/diff_gaussian_rasterization/_C.cpython-311-x86_64-linux-gnu.so" \
        "$official_root/thirdparty/simple-knn/simple_knn/_C.cpython-311-x86_64-linux-gnu.so" \
        "$official_root/vigs/imu_cpp/build/imu_integrator_cpp.cpython-311-x86_64-linux-gnu.so"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
} > "$output_dir/source_manifest.txt"

cd "$official_root"
exec "$python_env/bin/python" "$workspace_root/benchmarks/online_gs/exp78_vigs_native_driver.py" \
    --imagedir "$image_dir" \
    --imufile "$imu_file" \
    --calib "$calibration" \
    --config "$config" \
    --weights "$weights" \
    --output "$output_dir" \
    --buffer 700 \
    --IMU_poseinit_after 20 \
    --undistort \
    --seed 0 \
    2>&1 | tee "$output_dir/run.log"
