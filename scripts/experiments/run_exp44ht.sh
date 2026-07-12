#!/bin/bash
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
ts=$(date +%Y%m%d_%H%M%S)
outdir="$RESULTS/exp44ht_snapdens_tuned_15k_${ts}"
mkdir -p "$outdir"; cd "$REPO"
conda run -n 3dgs python train.py \
    --source_path "$LAB/results/datasets/orb_dense_confmono_snap_refilt_scene" \
    --iterations 15000 --densify_until_iter 3000 \
    --densification_interval 200 --densify_grad_threshold 0.0004 \
    --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
    --data_device cpu --test_iterations 15000 --save_iterations 15000 \
    --disable_viewer --quiet --model_path "$outdir" \
    --carve_loss_config "$REPO/configs/carve_loss/exp44h_tuned.yaml" \
    2>&1 | tee "$RESULTS/exp44ht_snapdens_tuned_15k_${ts}.log" | tail -1
echo DONE
