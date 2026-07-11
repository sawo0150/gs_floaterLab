#!/bin/bash
# exp38: Carve Loss 첫 학습 검증 (ORB 트랙, exp30과 동일 하이퍼 + carve loss)
#   설계·라벨 검증: context/experiments/carve_loss_design.md
#   비교 기준: exp30 (32.906, run-to-run 노이즈 ±0.24dB)
#   평가: PSNR + 챔피언 score 부하(score>0.5 & op>0.3) + 수동 라벨 recall
#         (라벨은 exp32 run 기준이므로 이 run에는 score 부하 지표만 직접 적용 가능)
#   변형: exp38a = soft+prune+gate 전부, exp38b = prune+gate만 (soft 분리 검증)
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
ORB_DATA=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full
RESULTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments

run_one() {
    local name=$1; local src=$2; local carve_cfg=$3
    local ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"
    local logfile="$RESULTS/${name}_${ts}.log"
    local extra=()
    [ -n "$carve_cfg" ] && extra=(--carve_loss_config "$carve_cfg")
    mkdir -p "$outdir"
    echo "=============================="
    echo "  START: $name  ($(date))"
    echo "  output: $outdir"
    echo "=============================="
    cd "$REPO"
    conda run -n 3dgs python train.py \
        --source_path "$src" \
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
        "${extra[@]}" \
        2>&1 | tee "$logfile"
    echo "  DONE: $name  ($(date))"
}

run_one "exp38a_orbfull_carve_full"      "$ORB_DATA" "$REPO/configs/carve_loss/exp38_carve.yaml"
run_one "exp38b_orbfull_carve_prunegate" "$ORB_DATA" "$REPO/configs/carve_loss/exp38_prunegate_only.yaml"
