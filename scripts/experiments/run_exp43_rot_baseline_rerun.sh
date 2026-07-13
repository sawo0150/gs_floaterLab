#!/bin/bash
# 대조군: rot baseline 재실행 (carve 없음) — 가시 먼지 106이 재현되는지 (run-to-run 분산 판정)
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
until grep -q HYB2-DONE /tmp/claude-1000/-home-wosas-Desktop-Incremental-mapping-test-gs-floaterLab/a18dbc8f-4cce-4ad0-a1ea-8f9bb38b1ea6/scratchpad/rot_hyb2_chain.log 2>/dev/null; do sleep 60; done
until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 30; done
ts=$(date +%Y%m%d_%H%M%S)
outdir="$RESULTS/exp43rot_baseline_rerun_30k_${ts}"
mkdir -p "$outdir"; cd "$REPO"
conda run -n 3dgs python train.py \
    --source_path "$LAB/data/scenes/301_1253_rot/03_rgb_3dgs" \
    --iterations 30000 --densify_until_iter 7000 \
    --densification_interval 200 --densify_grad_threshold 0.0004 \
    --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
    --data_device cpu --test_iterations 30000 --save_iterations 30000 \
    --disable_viewer --quiet --model_path "$outdir" \
    2>&1 | tee "$RESULTS/exp43rot_baseline_rerun_30k_${ts}.log" | tail -1
echo RERUN-DONE
