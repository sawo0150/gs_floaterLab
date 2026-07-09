#!/bin/bash
# exp27c: exp27 재실행 — anchor를 Atlas→MPS Umeyama 변환(scale 0.950, rmse 2cm)으로 정렬한 init
#   init = plateau_ellipsoid_v4 anchors_all_depth_pro.npy (SLAM 6,492 + DepthPro virtual 846 = 7,338 pts)
#   images/poses = 기존 MPS full 1311 dataset (exp08과 동일)
#   하이퍼파라미터 = exp08 (plateau loss 없음)
#   비교 기준: exp08 (626k MPS init, PSNR 33.012)
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
SOURCE=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/datasets/mps_anchorinit_aligned_scene
RESULTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments

name="exp27c_mps_anchorinit_aligned"
ts=$(date +%Y%m%d_%H%M%S)
outdir="$RESULTS/${name}_${ts}"
logfile="$RESULTS/${name}_${ts}.log"
mkdir -p "$outdir"

echo "=============================="
echo "  START: $name"
echo "  output: $outdir"
echo "  time:   $(date)"
echo "=============================="

cd "$REPO"
conda run -n 3dgs python train.py \
    --source_path "$SOURCE" \
    --iterations 30000 \
    --densification_interval 200 \
    --densify_grad_threshold 0.0004 \
    --densify_until_iter 7000 \
    --scaling_lr 0.0025 \
    --min_opacity_prune_threshold 0.01 \
    --optimizer_beta1 0.85 \
    --data_device cpu \
    --test_iterations 7000 30000 \
    --save_iterations 7000 30000 \
    --disable_viewer \
    --quiet \
    --model_path "$outdir" \
    2>&1 | tee "$logfile"

echo "=============================="
echo "  DONE: $name  ($(date))"
echo "=============================="
