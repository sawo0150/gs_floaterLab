#!/bin/bash
# ORB(OpenMAVIS) 트랙 — 새 데이터셋 data/03_rgb_3dgs_full (OpenMAVIS pose 1303장, ORB 7,205 init)
#   anchor는 같은 세션에서 native로 재생성한 것 (scripts/anchors/build_native_anchors_neworb.py)
#   → 세션 간 변환(Umeyama) 불필요, 검증: slam anchor -> dataset points3D NN median 0.000000m
#   exp30: baseline (plateau 없음, ORB init 그대로) — 이 트랙의 기준선
#   exp31: native anchor 7,108 pts를 init으로 (exp27c의 ORB판)
#   exp32: plateau 기본 tau + λ0.01 (exp19 설정) + native anchor
#   exp33: plateau enlarged tau + λ 0.10→0.03 (exp25 설정) + native anchor
# 하이퍼파라미터는 exp08과 동일. 결과는 exp08(MPS 트랙)과 직접 비교 금지 — exp30 기준으로 비교.
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
ORB_DATA=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full
ANCHOR_SCENE=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/datasets/orb_native_anchorinit_scene
RESULTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments

run_one() {
    local name=$1; local src=$2; local cfg=$3
    local ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"
    local logfile="$RESULTS/${name}_${ts}.log"
    local extra=()
    [ -n "$cfg" ] && extra=(--plateau_loss_config "$cfg")
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

run_one "exp30_orbfull_baseline"        "$ORB_DATA"     ""
run_one "exp31_orbfull_anchorinit"      "$ANCHOR_SCENE" ""
run_one "exp32_orbfull_plateau_basetau" "$ORB_DATA"     "$REPO/configs/plateau_loss/orb_depthpro_v4_native.yaml"
run_one "exp33_orbfull_plateau_bigtau"  "$ORB_DATA"     "$REPO/configs/plateau_loss/orb_depthpro_tau_enlarged_native.yaml"
