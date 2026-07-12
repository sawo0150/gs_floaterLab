#!/bin/bash
# exp43-rot: 1253_rot에서 carve 레시피 재현 (native carve field는 CarveLoss가 자체 빌드)
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 20; done
ts=$(date +%Y%m%d_%H%M%S)
outdir="$RESULTS/exp43rot_noforce_30k_${ts}"
mkdir -p "$outdir"; cd "$REPO"
# rot 장면 전용 config (points_txt 미지정 → 자기 points3D 사용, dynamic carve 포함)
sed 's|^points_txt:.*||' configs/carve_loss/exp45b_dynamic.yaml > configs/carve_loss/exp43rot_noforce.yaml
conda run -n 3dgs python train.py \
    --source_path "$LAB/data/scenes/301_1253_rot/03_rgb_3dgs" \
    --iterations 30000 --densify_until_iter 7000 \
    --densification_interval 200 --densify_grad_threshold 0.0004 \
    --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
    --data_device cpu --test_iterations 30000 --save_iterations 30000 \
    --disable_viewer --quiet --model_path "$outdir" \
    --carve_loss_config "$REPO/configs/carve_loss/exp43rot_noforce.yaml" \
    2>&1 | tee "$RESULTS/exp43rot_noforce_30k_${ts}.log" | tail -1
echo DONE
