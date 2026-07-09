#!/bin/bash
# exp37: confidence + monodepth 기반 dense init (anchor 아님)
#   scripts/anchors/build_dense_init_neworb.py 로 생성
#   init = SLAM core(obs>=3, 6,543) + dense monodepth virtual(high-conf fit, voxel 5cm/stride 4px, 142,021)
#         = 148,564 pts (exp08의 626k 대비 24%, raw ORB init 7,205의 20배)
#   비교 기준: exp30(raw ORB init baseline), exp31/34(sparse anchor init)
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
SOURCE=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/datasets/orb_dense_confmono_init_scene
RESULTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments

name="exp37_orbfull_dense_confmono_init"
ts=$(date +%Y%m%d_%H%M%S)
outdir="$RESULTS/${name}_${ts}"
logfile="$RESULTS/${name}_${ts}.log"
mkdir -p "$outdir"

echo "=============================="
echo "  START: $name  ($(date))"
echo "  output: $outdir"
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

echo "  DONE: $name  ($(date))"
