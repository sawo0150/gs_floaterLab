#!/bin/bash
# exp45a: 노출 모델링 — 챔피언(44d2) 레시피 + train_test_exp
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 30; done
ts=$(date +%Y%m%d_%H%M%S)
outdir="$RESULTS/exp45a_exposure_hybrid_30k_${ts}"
mkdir -p "$outdir"; cd "$REPO"
conda run -n 3dgs python train.py \
    --source_path "$LAB/results/datasets/orb_hybrid_roma_ppm_scene" \
    --iterations 30000 --densify_until_iter 7000 --train_test_exp \
    --densification_interval 200 --densify_grad_threshold 0.0004 \
    --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
    --data_device cpu --test_iterations 30000 --save_iterations 30000 \
    --disable_viewer --quiet --model_path "$outdir" \
    --carve_loss_config "$REPO/configs/carve_loss/exp44f_full.yaml" \
    2>&1 | tee "$RESULTS/exp45a_exposure_hybrid_30k_${ts}.log" | tail -1
echo DONE
