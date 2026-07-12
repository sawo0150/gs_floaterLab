#!/bin/bash
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
run_one() {
    local name=$1; local src=$2; local iters=$3; local duntil=$4
    local ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"
    mkdir -p "$outdir"; cd "$REPO"
    conda run -n 3dgs python train.py \
        --source_path "$src" --iterations $iters --densify_until_iter $duntil \
        --densification_interval 200 --densify_grad_threshold 0.0004 \
        --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations $iters --save_iterations $iters \
        --disable_viewer --quiet --model_path "$outdir" \
        --carve_loss_config "$REPO/configs/carve_loss/exp44f_full.yaml" \
        2>&1 | tee "$RESULTS/${name}_${ts}.log" | tail -1
    echo "DONE $name"
}
# 44h: 짧은 densify(3k) + 총 7k / 15k — snap-refilt init 기반
run_one "exp44ht_tuned_15k_A"  "$LAB/results/datasets/orb_dense_confmono_snap_refilt_scene" 15000 3000
run_one "exp44ht_tuned_15k_B_dummy" "$LAB/results/datasets/orb_dense_confmono_snap_refilt_scene" 15000 3000
