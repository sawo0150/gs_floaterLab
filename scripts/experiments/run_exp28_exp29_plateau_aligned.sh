#!/bin/bash
# exp28/exp29: Round 7 재검증 — 정렬된 anchor(anchors_all_depth_pro_mpsaligned.npy)로 plateau 재실행
#   exp28 = exp25 설정 (enlarged tau + λ 0.10→0.03)
#   exp29 = exp19 설정 (기본 tau, λ=0.01 고정) — "정렬되면 작은 tau로 충분한가" 검증
#   SOURCE: 옛 심링크(data/rgb_3dgs_openmavis_full_301_1253) 제거로 실경로 직접 사용
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
SOURCE=/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/aria_mps_2dgs/0416_Data__0416_301-1253
RESULTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments

run_one() {
    local name=$1
    local cfg=$2
    local ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"
    local logfile="$RESULTS/${name}_${ts}.log"
    mkdir -p "$outdir"
    echo "=============================="
    echo "  START: $name  ($(date))"
    echo "  output: $outdir"
    echo "=============================="
    cd "$REPO"
    conda run -n 3dgs python train.py \
        --source_path "$SOURCE" \
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
        --plateau_loss_config "$cfg" \
        2>&1 | tee "$logfile"
    echo "  DONE: $name  ($(date))"
}

run_one "exp28_mps_tau_enlarged_aligned" "$REPO/configs/plateau_loss/mps_depthpro_tau_enlarged_aligned.yaml"
run_one "exp29_mps_depthpro_aligned"     "$REPO/configs/plateau_loss/mps_depthpro_v4_aligned.yaml"
