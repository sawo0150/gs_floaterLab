#!/bin/bash
# exp45c: progressive resolution 2단계 — 절반 해상도 8k(densify 전부 포함) → 원해상도 재개 15k
# 목표: 44d fast(15k, 8분, train 32.35) 대비 시간 단축, PSNR 동급
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
DATA=$LAB/results/datasets/orb_hybrid_roma_ppm_scene
until grep -q 305-DONE /tmp/claude-1000/-home-wosas-Desktop-Incremental-mapping-test-gs-floaterLab/a18dbc8f-4cce-4ad0-a1ea-8f9bb38b1ea6/scratchpad/305_retry_chain.log 2>/dev/null; do sleep 60; done
until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 30; done
ts=$(date +%Y%m%d_%H%M%S)
outdir="$RESULTS/exp45c_prog_15k_${ts}"
mkdir -p "$outdir"; cd "$REPO"
SECONDS=0
# 1단계: 해상도 1/2, 8k (densify 0-7k 전부 저해상도에서)
conda run -n 3dgs python train.py \
    --source_path "$DATA" -r 2 \
    --iterations 8000 --densify_until_iter 7000 \
    --densification_interval 200 --densify_grad_threshold 0.0004 \
    --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
    --data_device cpu --test_iterations 8000 --save_iterations 8000 \
    --checkpoint_iterations 8000 \
    --disable_viewer --quiet --model_path "$outdir" \
    --carve_loss_config "$REPO/configs/carve_loss/exp40b_force_soft.yaml" \
    2>&1 | tee "$RESULTS/exp45c_prog_15k_${ts}_stage1.log" | tail -1
echo "stage1 ${SECONDS}s"
# 2단계: 원해상도 재개 → 15k
conda run -n 3dgs python train.py \
    --source_path "$DATA" -r 1 \
    --start_checkpoint "$outdir/chkpnt8000.pth" \
    --iterations 15000 --densify_until_iter 0 \
    --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
    --data_device cpu --test_iterations 15000 --save_iterations 15000 \
    --disable_viewer --quiet --model_path "$outdir" \
    --carve_loss_config "$REPO/configs/carve_loss/exp40b_force_soft.yaml" \
    2>&1 | tee "$RESULTS/exp45c_prog_15k_${ts}_stage2.log" | tail -1
echo "total ${SECONDS}s"
echo 45C-DONE
