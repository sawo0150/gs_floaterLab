#!/bin/bash
# exp44: dense init × no-densify × carve — 고속 geometry 트랙 1차
#   44a0 = 대조군 (carve 없음), 44a = +carve. iterations {7k, 15k} sweep.
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
SOURCE=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/datasets/orb_dense_confmono_init_scene
RESULTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments
run_one() {
    local name=$1; local iters=$2; local cfg=$3
    local ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"
    local extra=(); [ -n "$cfg" ] && extra=(--carve_loss_config "$cfg")
    mkdir -p "$outdir"
    echo "=== START: $name ($(date)) ==="
    cd "$REPO"
    conda run -n 3dgs python train.py \
        --source_path "$SOURCE" --iterations $iters \
        --densify_until_iter 0 \
        --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations $iters --save_iterations $iters \
        --disable_viewer --quiet --model_path "$outdir" \
        "${extra[@]}" 2>&1 | tee "$RESULTS/${name}_${ts}.log" | tail -1
    echo "=== DONE: $name ($(date)) ==="
}
run_one "exp44a0_nodensify_7k"        7000  ""
run_one "exp44a_nodensify_carve_7k"   7000  "$REPO/configs/carve_loss/exp44a_nodensify.yaml"
run_one "exp44a_nodensify_carve_15k"  15000 "$REPO/configs/carve_loss/exp44a_nodensify.yaml"
