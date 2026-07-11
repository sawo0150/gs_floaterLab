#!/bin/bash
# 야간 배치 2: exp38c(soft 완화) + exp30r(baseline 재현, 지표 노이즈) + exp39(MPS carve)
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
ORB_DATA=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full
MPS_DATA=/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253
RESULTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments

run_one() {
    local name=$1; local src=$2; local carve_cfg=$3
    local ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"
    local extra=()
    [ -n "$carve_cfg" ] && extra=(--carve_loss_config "$carve_cfg")
    mkdir -p "$outdir"
    echo "=== START: $name ($(date)) ==="
    cd "$REPO"
    conda run -n 3dgs python train.py \
        --source_path "$src" --iterations 30000 \
        --densification_interval 200 --densify_grad_threshold 0.0004 \
        --densify_until_iter 7000 --scaling_lr 0.0025 \
        --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations 7000 30000 --save_iterations 30000 \
        --disable_viewer --quiet --model_path "$outdir" \
        "${extra[@]}" 2>&1 | tee "$RESULTS/${name}_${ts}.log" | tail -1
    echo "=== DONE: $name ($(date)) ==="
}
run_one "exp38c_orbfull_carve_softlite" "$ORB_DATA" "$REPO/configs/carve_loss/exp38c_softlite.yaml"
run_one "exp30r_orbfull_baseline_rerun" "$ORB_DATA" ""
run_one "exp39_mps_carve"               "$MPS_DATA" "$REPO/configs/carve_loss/exp39_carve_mps.yaml"
