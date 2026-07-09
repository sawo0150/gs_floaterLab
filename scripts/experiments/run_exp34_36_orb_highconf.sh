#!/bin/bash
# ORB 트랙 — high-confidence anchor 변형 (obs>=10 & found_ratio>=0.5, 원래 설계 문서 기준)
#   scripts/anchors/build_native_anchors_neworb_highconf.py 로 생성
#   plain native anchor(exp30-33, obs>=3, 7,108 pts)와 대조: anchor 646 SLAM + 792 virtual = 1,438 pts
#   exp34: high-confidence anchor init
#   exp35: plateau 기본 tau + λ0.01, high-confidence anchor
#   exp36: plateau enlarged tau + λ0.10→0.03, high-confidence anchor
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
ORB_DATA=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/03_rgb_3dgs_full
ANCHOR_SCENE=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/datasets/orb_native_highconf_anchorinit_scene
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

run_one "exp34_orbfull_highconf_anchorinit"   "$ANCHOR_SCENE" ""
run_one "exp35_orbfull_plateau_highconf_basetau" "$ORB_DATA" "$REPO/configs/plateau_loss/orb_depthpro_v4_highconf.yaml"
run_one "exp36_orbfull_plateau_highconf_bigtau"  "$ORB_DATA" "$REPO/configs/plateau_loss/orb_depthpro_tau_enlarged_highconf.yaml"
