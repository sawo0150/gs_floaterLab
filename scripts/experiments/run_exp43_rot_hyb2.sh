#!/bin/bash
# exp43: rot hybrid v2 — 시차 보장 쌍(min-baseline 0.2m) RoMA로 init 재구축 후 champion carve 학습
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
# noforce 학습 종료 대기 (결과 저장물 기준)
until ls $RESULTS/exp43rot_noforce_30k_*/point_cloud/iteration_30000/point_cloud.ply >/dev/null 2>&1; do sleep 60; done
until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 30; done
rm -rf $LAB/data/scenes/301_1253_rot/03_rgb_3dgs_hyb
cd $LAB
/home/wosas/miniconda3/envs/3dgs/bin/python scripts/anchors/build_hybrid_init_scene.py --scene 301_1253_rot --min-baseline 0.2
ts=$(date +%Y%m%d_%H%M%S)
outdir="$RESULTS/exp43rot_hyb2_30k_${ts}"
mkdir -p "$outdir"; cd "$REPO"
conda run -n 3dgs python train.py \
    --source_path "$LAB/data/scenes/301_1253_rot/03_rgb_3dgs_hyb" \
    --iterations 30000 --densify_until_iter 7000 \
    --densification_interval 200 --densify_grad_threshold 0.0004 \
    --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
    --data_device cpu --test_iterations 30000 --save_iterations 30000 \
    --disable_viewer --quiet --model_path "$outdir" \
    --carve_loss_config "$REPO/configs/carve_loss/exp43rot_static.yaml" \
    2>&1 | tee "$RESULTS/exp43rot_hyb2_30k_${ts}.log" | tail -1
echo HYB2-DONE
