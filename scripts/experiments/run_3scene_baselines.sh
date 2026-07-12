#!/bin/bash
# 새 3장면 baseline (exp30 하이퍼 동일)
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
# GPU 유휴 대기 (exp44 재실행 종료 후)
until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 20; done
for s in snu_floor2_1; do
    ts=$(date +%Y%m%d_%H%M%S)
    outdir="$RESULTS/scene_${s}_baseline_${ts}"
    mkdir -p "$outdir"
    echo "=== START: $s baseline ($(date)) ==="
    cd "$REPO"
    conda run -n 3dgs python train.py \
        --source_path "$LAB/data/scenes/$s/03_rgb_3dgs" --iterations 30000 \
        --densification_interval 200 --densify_grad_threshold 0.0004 \
        --densify_until_iter 7000 --scaling_lr 0.0025 \
        --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations 7000 30000 --save_iterations 30000 \
        --disable_viewer --quiet --model_path "$outdir" \
        2>&1 | tee "$RESULTS/scene_${s}_baseline_${ts}.log" | tail -1
    echo "=== DONE: $s baseline ($(date)) ==="
done
