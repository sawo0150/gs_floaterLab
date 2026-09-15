#!/usr/bin/env bash
# Run one clean official VIGS sequence in the paper-native, pre-final lane.
set -euo pipefail

if [ "$#" -ne 4 ]; then
    echo "usage: $0 <rpng|utmm> <sequence> <seed> <output-dir>" >&2
    exit 2
fi

workspace_root='/home/intern/gs_floaterLab'
official_root='/home/intern/VIGS-SLAM-official-exp78'
python_env='/home/colin/miniconda3/envs/vigs-slam-5090'
expected_commit='22ffe24c6df81d0bf63bd20057565c00c51d2996'
dataset=$1
sequence=$2
seed=$3
output_dir=$(realpath -m "$4")
runtime_root=${EXP78_TRT_RUNTIME_ROOT:-$official_root}
tensorrt=off

if ! [[ "$seed" =~ ^[0-9]+$ ]]; then
    echo "seed must be a non-negative integer" >&2
    exit 2
fi

case "$dataset" in
    rpng)
        sequence_root="$workspace_root/data/benchmarks/rpng/prepared/rpngar/$sequence"
        image_dir="$sequence_root/rgb"
        imu_file="$sequence_root/imu.txt"
        ground_truth="$sequence_root/gt.txt"
        calibration="$official_root/calib/rpngar.txt"
        config="$official_root/config/rpng.yaml"
        buffer=700
        imu_init=20
        ;;
    utmm)
        sequence_root="$workspace_root/data/benchmarks/utmm/prepared/UTMM_Dataset/$sequence"
        image_dir="$sequence_root/rgb_timestamp"
        imu_file="$sequence_root/imu_ours.txt"
        ground_truth="$sequence_root/groundtruth.txt"
        calibration="$sequence_root/intrinsics_ours.txt"
        config="$official_root/config/utmm.yaml"
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
if [ "$runtime_root" = "$official_root" ]; then
    if find "$official_root/pretrained_models" -maxdepth 1 -type f -name '*.engine' -print -quit | grep -q .; then
        echo "paper-native PyTorch arm refuses top-level TensorRT engines" >&2
        exit 2
    fi
else
    runtime_root=$(realpath "$runtime_root")
    tensorrt=on
    for engine in \
        omnidata_depth_512_simplified_fp16.engine \
        omnidata_normal_512_simplified_fp16.engine \
        droidnet_fnet_fp16.engine \
        update_module_partial_fp16.engine \
        update_module_partial_pgba_fp16.engine; do
        if [ ! -f "$runtime_root/pretrained_models/$engine" ]; then
            echo "missing TensorRT engine: $runtime_root/pretrained_models/$engine" >&2
            exit 2
        fi
    done
fi

weights="$official_root/pretrained_models/droid.pth"
depth_weights="$official_root/pretrained_models/omnidata_dpt_depth_v2.ckpt"
normal_weights="$official_root/pretrained_models/omnidata_dpt_normal_v2.ckpt"
driver="$workspace_root/benchmarks/online_gs/exp78_vigs_native_driver.py"
evaluator="$workspace_root/benchmarks/online_gs/exp78_evaluate_vigs_ply.py"
for path in "$image_dir" "$imu_file" "$ground_truth" "$calibration" "$config" \
            "$weights" "$depth_weights" "$normal_weights" "$driver" "$evaluator"; do
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
    echo "dataset=$dataset"
    echo "sequence=$sequence"
    echo "seed=$seed"
    echo "official_commit=$actual_commit"
    echo "driver=$driver"
    echo "evaluator=$evaluator"
    echo "runtime_root=$runtime_root"
    echo "tensorrt=$tensorrt"
    echo "final_ba=off"
    echo "final_color_refinement=off"
    echo "buffer=$buffer"
    echo "imu_init_keyframes=$imu_init"
    echo "official_prefinal_inprocess_eval=${EXP78_OFFICIAL_PREFINAL_EVAL:-0}"
    echo "diagnose_after_ba_before_color=${EXP78_DIAGNOSE_AFTER_BA_BEFORE_COLOR:-0}"
    sha256sum "$driver" "$evaluator" "$config" "$calibration" "$imu_file" \
        "$ground_truth" "$weights" "$depth_weights" "$normal_weights" \
        "$official_root/vigs_backends.cpython-311-x86_64-linux-gnu.so" \
        "$official_root/thirdparty/lietorch_5090/lietorch_backends.cpython-311-x86_64-linux-gnu.so" \
        "$official_root/thirdparty/diff-gaussian-rasterization/diff_gaussian_rasterization/_C.cpython-311-x86_64-linux-gnu.so" \
        "$official_root/thirdparty/simple-knn/simple_knn/_C.cpython-311-x86_64-linux-gnu.so" \
        "$official_root/vigs/imu_cpp/build/imu_integrator_cpp.cpython-311-x86_64-linux-gnu.so"
    if [ "$tensorrt" = "on" ]; then
        sha256sum \
            "$runtime_root/pretrained_models/omnidata_depth_512_simplified_fp16.engine" \
            "$runtime_root/pretrained_models/omnidata_normal_512_simplified_fp16.engine" \
            "$runtime_root/pretrained_models/droidnet_fnet_fp16.engine" \
            "$runtime_root/pretrained_models/update_module_partial_fp16.engine" \
            "$runtime_root/pretrained_models/update_module_partial_pgba_fp16.engine"
    fi
    find "$image_dir" -maxdepth 1 -type f -printf '%f %s\n' | sort | sha256sum
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    lscpu | grep -E '^(CPU\(s\)|Model name|Thread\(s\) per core|Core\(s\) per socket|Socket\(s\)):'
    "$python_env/bin/python" -c "import cv2,numpy,torch,torchmetrics; print('software', torch.__version__, torch.version.cuda, torchmetrics.__version__, cv2.__version__, numpy.__version__)"
} > "$output_dir/source_manifest.txt"

cd "$runtime_root"
official_prefinal_eval_args=()
if [ "${EXP78_OFFICIAL_PREFINAL_EVAL:-0}" = "1" ]; then
    official_prefinal_eval_args+=(--official-prefinal-eval)
fi
after_ba_before_color_args=()
if [ "${EXP78_DIAGNOSE_AFTER_BA_BEFORE_COLOR:-0}" = "1" ]; then
    after_ba_before_color_args+=(--diagnose-after-ba-before-color)
fi
exec "$python_env/bin/python" "$driver" \
    --imagedir "$image_dir" \
    --imufile "$imu_file" \
    --calib "$calibration" \
    --config "$config" \
    --weights "$weights" \
    --output "$output_dir" \
    --buffer "$buffer" \
    --IMU_poseinit_after "$imu_init" \
    --undistort \
    --seed "$seed" \
    "${official_prefinal_eval_args[@]}" \
    "${after_ba_before_color_args[@]}" \
    2>&1 | tee "$output_dir/run.log"
