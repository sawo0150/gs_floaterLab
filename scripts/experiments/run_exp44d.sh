#!/bin/bash
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 30; done
run_one() {
    local name=$1; local iters=$2; local duntil=$3
    local ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"
    mkdir -p "$outdir"; cd "$REPO"
    conda run -n 3dgs python train.py \
        --source_path "$LAB/results/datasets/orb_hybrid_roma_ppm_scene" \
        --iterations $iters --densify_until_iter $duntil \
        --densification_interval 200 --densify_grad_threshold 0.0004 \
        --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations $iters --save_iterations $iters \
        --disable_viewer --quiet --model_path "$outdir" \
        --carve_loss_config "$REPO/configs/carve_loss/exp44f_full.yaml" \
        2>&1 | tee "$RESULTS/${name}_${ts}.log" | tail -1
    echo "DONE $name"
}
run_one "exp44d_hybrid_15k" 15000 3000
run_one "exp44d2_hybrid_densify_30k" 30000 7000
