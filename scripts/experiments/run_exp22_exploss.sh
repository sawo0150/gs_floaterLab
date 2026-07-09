#!/bin/bash
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
SOURCE=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/rgb_3dgs_openmavis_full_301_1253
RESULTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments
PLATEAU_CFG=$REPO/configs/plateau_loss/mps_depthpro_exploss.yaml

name="exp22_mps_exploss"
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
    --plateau_loss_config "$PLATEAU_CFG" \
    2>&1 | tee "$logfile"

echo "=============================="
echo "  DONE: $name  ($(date))"
echo "=============================="
