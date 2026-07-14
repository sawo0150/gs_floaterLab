#!/bin/bash
# exp46 축1: 305 hybrid init(RoMA+PPM) + depth-anchor carve — "init > 압력" 교차장면 확증
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
cd $LAB
# 1) hybrid init 빌드 (GPU RoMA)
/home/wosas/miniconda3/envs/3dgs/bin/python scripts/anchors/build_hybrid_init_scene.py --scene 301_305
# 2) carve 학습 (depth 앵커 field, cam_stride 40)
until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 20; done
ts=$(date +%Y%m%d_%H%M%S)
outdir="$RESULTS/exp46_ax1_305hyb_30k_${ts}"
mkdir -p "$outdir"; cd "$REPO"
conda run -n 3dgs python train.py \
    --source_path "$LAB/data/scenes/301_305/03_rgb_3dgs_hyb" \
    --iterations 30000 --densify_until_iter 7000 \
    --densification_interval 200 --densify_grad_threshold 0.0004 \
    --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
    --data_device cpu --test_iterations 30000 --save_iterations 30000 \
    --disable_viewer --quiet --model_path "$outdir" \
    --carve_loss_config "$REPO/configs/carve_loss/exp43_305_depth.yaml" \
    2>&1 | tee "$RESULTS/exp46_ax1_305hyb_30k_${ts}.log" | tail -1
echo AX1-DONE
