#!/bin/bash
# exp44a'': carve-filtered(w<=0.9) + 이미지 색 입힌 init × no-densify × carve, 7k
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 20; done
ts=$(date +%Y%m%d_%H%M%S)
outdir="$RESULTS/exp44app_cf90color_7k_${ts}"
mkdir -p "$outdir"
cd "$REPO"
conda run -n 3dgs python train.py \
    --source_path "$LAB/results/datasets/orb_dense_confmono_cf90colored_scene" \
    --iterations 7000 --densify_until_iter 0 \
    --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
    --data_device cpu --test_iterations 7000 --save_iterations 7000 \
    --disable_viewer --quiet --model_path "$outdir" \
    --carve_loss_config "$REPO/configs/carve_loss/exp44a_nodensify.yaml" \
    2>&1 | tee "$RESULTS/exp44app_cf90color_7k_${ts}.log" | tail -1
echo "DONE exp44app"
