#!/bin/bash
# exp15-18 재실행 (tmp_radii None 버그 수정 후)
# Baseline (exp_orb_baseline_20260705_050503) 완료: PSNR@30k = 29.0226
set -e

REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
SOURCE=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/rgb_3dgs_openmavis_orb_full_301_1253
RESULTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments
PLATEAU_CFG=$REPO/configs/plateau_loss

COMMON_ARGS=(
  --source_path "$SOURCE"
  --iterations 30000
  --densification_interval 200
  --densify_grad_threshold 0.0004
  --densify_until_iter 7000
  --scaling_lr 0.0025
  --min_opacity_prune_threshold 0.01
  --optimizer_beta1 0.85
  --data_device cpu
  --test_iterations 7000 30000
  --save_iterations 7000 30000
  --disable_viewer
  --quiet
)

run_exp() {
    local name=$1
    local plateau_cfg=$2
    local ts
    ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"
    local logfile="$RESULTS/${name}_${ts}.log"

    echo ""
    echo "══════════════════════════════════════════════"
    echo "  START: $name"
    echo "  output: $outdir"
    echo "  time:   $(date)"
    echo "══════════════════════════════════════════════"

    local args=("${COMMON_ARGS[@]}" --model_path "$outdir")
    [[ -n "$plateau_cfg" ]] && args+=(--plateau_loss_config "$plateau_cfg")

    mkdir -p "$outdir"
    cd "$REPO"
    conda run -n 3dgs python train.py "${args[@]}" 2>&1 | tee "$logfile"
    echo "  DONE:  $name  ($(date))"
}

mkdir -p "$RESULTS"

run_exp "exp15_orb_spherical"    "$PLATEAU_CFG/spherical.yaml"
run_exp "exp16_orb_ellipsoidal"  "$PLATEAU_CFG/ellipsoidal.yaml"
run_exp "exp17_orb_metric3d"     "$PLATEAU_CFG/monodepth_metric3d_v4.yaml"
run_exp "exp18_orb_depthpro"     "$PLATEAU_CFG/monodepth_depthpro_v4.yaml"

echo ""
echo "════════ 전체 완료 ════════"
echo "결과 위치: $RESULTS"
ls -lhd $RESULTS/exp1[5678]_orb_*_2026* 2>/dev/null | awk '{print $NF, $5}'
