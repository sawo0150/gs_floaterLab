#!/bin/bash
# exp46 축2b: 12F hybrid init + carve — 축2의 +3.41dB가 진짜 기하개선인지(먼지 청소 후 유지되나) 판별
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
SPD=/tmp/claude-1000/-home-wosas-Desktop-Incremental-mapping-test-gs-floaterLab/a18dbc8f-4cce-4ad0-a1ea-8f9bb38b1ea6/scratchpad
until grep -q AX2AX7-DONE $SPD/ax2ax7_chain.log 2>/dev/null; do sleep 60; done
until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 20; done
ts=$(date +%Y%m%d_%H%M%S); outdir="$RESULTS/exp46_ax2b_12Fhybcarve_30k_${ts}"; mkdir -p "$outdir"; cd "$REPO"
conda run -n 3dgs python train.py \
    --source_path "$LAB/data/scenes/301_12F/03_rgb_3dgs_hyb" \
    --iterations 30000 --densify_until_iter 7000 \
    --densification_interval 200 --densify_grad_threshold 0.0004 \
    --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
    --data_device cpu --test_iterations 30000 --save_iterations 30000 \
    --disable_viewer --quiet --model_path "$outdir" \
    --carve_loss_config "$REPO/configs/carve_loss/exp43_12F_ctrl.yaml" \
    2>&1 | tee "$RESULTS/exp46_ax2b_12Fhybcarve_30k_${ts}.log" | tail -1
echo AX2B-DONE
