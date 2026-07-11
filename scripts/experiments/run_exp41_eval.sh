#!/bin/bash
# exp41: held-out(novel view) 평가 — baseline vs 챔피언. train PSNR 기생충 가설의 최종 검증.
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
ORB_DATA=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full
RESULTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments
run_one() {
    local name=$1; local cfg=$2
    local ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"
    local extra=()
    [ -n "$cfg" ] && extra=(--carve_loss_config "$cfg")
    mkdir -p "$outdir"
    echo "=== START: $name ($(date)) ==="
    cd "$REPO"
    conda run -n 3dgs python train.py \
        --source_path "$ORB_DATA" --iterations 30000 --eval \
        --densification_interval 200 --densify_grad_threshold 0.0004 \
        --densify_until_iter 7000 --scaling_lr 0.0025 \
        --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations 7000 30000 --save_iterations 30000 \
        --disable_viewer --quiet --model_path "$outdir" \
        "${extra[@]}" 2>&1 | tee "$RESULTS/${name}_${ts}.log" | tail -1
    echo "=== DONE: $name ($(date)) ==="
}
run_one "exp41c_orbeval_seg_baseline" ""
run_one "exp41d_orbeval_seg_champion" "$REPO/configs/carve_loss/exp40b_force_soft.yaml"
