#!/bin/bash
# exp44a': carve-filtered init × no-densify × carve (필터 강도 2종)
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
run_one() {
    local name=$1; local src=$2
    local ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"
    mkdir -p "$outdir"
    echo "=== START: $name ($(date)) ==="
    cd "$REPO"
    conda run -n 3dgs python train.py \
        --source_path "$src" --iterations 7000 --densify_until_iter 0 \
        --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations 7000 --save_iterations 7000 \
        --disable_viewer --quiet --model_path "$outdir" \
        --carve_loss_config "$REPO/configs/carve_loss/exp44a_nodensify.yaml" \
        2>&1 | tee "$RESULTS/${name}_${ts}.log" | tail -1
    echo "=== DONE: $name ($(date)) ==="
}
run_one "exp44ap50_carvefilt_7k" "$LAB/results/datasets/orb_dense_confmono_carvefiltered_scene"
run_one "exp44ap90_carvefilt_7k" "$LAB/results/datasets/orb_dense_confmono_carvefiltered90_scene"
