#!/bin/bash
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
# rot 2연전 완료 신호 대기 (ALL-DONE)
until grep -q ALL-DONE /tmp/claude-1000/-home-wosas-Desktop-Incremental-mapping-test-gs-floaterLab/a18dbc8f-4cce-4ad0-a1ea-8f9bb38b1ea6/scratchpad/rot_2run_chain.log 2>/dev/null; do sleep 60; done
until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 30; done
ts=$(date +%Y%m%d_%H%M%S)
outdir="$RESULTS/exp43_305_depthcarve_30k_${ts}"
mkdir -p "$outdir"; cd "$REPO"
conda run -n 3dgs python train.py \
    --source_path "$LAB/data/scenes/301_305/03_rgb_3dgs" \
    --iterations 30000 --densify_until_iter 7000 \
    --densification_interval 200 --densify_grad_threshold 0.0004 \
    --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
    --data_device cpu --test_iterations 30000 --save_iterations 30000 \
    --disable_viewer --quiet --model_path "$outdir" \
    --carve_loss_config "$REPO/configs/carve_loss/exp43_305_depth.yaml" \
    2>&1 | tee "$RESULTS/exp43_305_depthcarve_30k_${ts}.log" | tail -1
echo 305-DONE
