#!/bin/bash
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
run_one() {
    local name=$1; local src=$2; local iters=$3
    local ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"
    mkdir -p "$outdir"; cd "$REPO"
    echo "=== START: $name ==="
    conda run -n 3dgs python train.py \
        --source_path "$src" --iterations $iters --densify_until_iter 0 \
        --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations $iters --save_iterations $iters \
        --disable_viewer --quiet --model_path "$outdir" \
        --carve_loss_config "$REPO/configs/carve_loss/exp44a_nodensify.yaml" \
        2>&1 | tee "$RESULTS/${name}_${ts}.log" | tail -1
    echo "=== DONE: $name ==="
}
run_one "exp44app50_cf50color_7k" "$LAB/results/datasets/orb_dense_confmono_cf50colored_scene" 7000
run_one "exp44app_cf90color_15k"  "$LAB/results/datasets/orb_dense_confmono_cf90colored_scene" 15000
