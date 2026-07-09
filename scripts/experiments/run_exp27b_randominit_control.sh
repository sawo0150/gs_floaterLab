#!/bin/bash
# exp27b: exp27의 대조군 — MPS semidense 626k에서 랜덤 7,338 pts 추출한 init
#   exp27(anchor init 7,338 pts)과 개수 동일, 위치만 "확실히 표면인" MPS 점
#   → exp27과의 PSNR 차이 = anchor '배치 품질'의 효과 (개수 confound 제거)
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
SOURCE=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/datasets/mps_random7338_scene
RESULTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments

name="exp27b_mps_randominit7338"
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
