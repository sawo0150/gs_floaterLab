#!/bin/bash
# exp40: carve-potential force 검증 (A안). a=prune+gate+force, b=softlite+prune+gate+force
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
ORB_DATA=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full
RESULTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments
run_one() {
    local name=$1; local cfg=$2
    local ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"
    mkdir -p "$outdir"
    echo "=== START: $name ($(date)) ==="
    cd "$REPO"
    conda run -n 3dgs python train.py \
        --source_path "$ORB_DATA" --iterations 30000 \
        --densification_interval 200 --densify_grad_threshold 0.0004 \
        --densify_until_iter 7000 --scaling_lr 0.0025 \
        --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations 7000 30000 --save_iterations 30000 \
        --disable_viewer --quiet --model_path "$outdir" \
        --carve_loss_config "$cfg" 2>&1 | tee "$RESULTS/${name}_${ts}.log" | tail -1
    echo "=== DONE: $name ($(date)) ==="
}
run_one "exp40a_orbfull_carve_force"      "$REPO/configs/carve_loss/exp40_force.yaml"
run_one "exp40b_orbfull_force_softlite"   "$REPO/configs/carve_loss/exp40b_force_soft.yaml"
