#!/bin/bash
# exp43-12F: carve(ctrl) vs carve+vr 페어 — fog 장면에서 vr 채널 효과 검증
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
run_one () {
    until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 30; done
    ts=$(date +%Y%m%d_%H%M%S)
    outdir="$RESULTS/${1}_${ts}"
    mkdir -p "$outdir"; cd "$REPO"
    conda run -n 3dgs python train.py \
        --source_path "$LAB/data/scenes/301_12F/03_rgb_3dgs" \
        --iterations 30000 --densify_until_iter 7000 \
        --densification_interval 200 --densify_grad_threshold 0.0004 \
        --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations 30000 --save_iterations 30000 \
        --disable_viewer --quiet --model_path "$outdir" \
        --carve_loss_config "$REPO/configs/carve_loss/$2" \
        2>&1 | tee "$RESULTS/${1}_${ts}.log" | tail -1
    sleep 20
}
run_one exp43_12F_ctrl_30k exp43_12F_ctrl.yaml
run_one exp43_12F_vr_30k   exp43_12F_vr.yaml
echo 12F-PAIR-DONE
