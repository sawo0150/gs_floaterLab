#!/bin/bash
# 5개 Plateau Loss 실험 순차 실행
# Data: rgb_3dgs_openmavis_orb_full_301_1253
#   - trajectory: ORB-SLAM (656 frames, 홀수 프레임)
#   - init:       ORB-SLAM sparse 7,182 pts
#   - anchor:     ORB-SLAM filtered 6,492 pts (YAML에 명시)
#
# 실험:
#   exp_orb_baseline  — plateau 없음 (기준선)
#   exp15_orb_spher   — spherical plateau
#   exp16_orb_ellip   — ellipsoidal plateau
#   exp17_orb_metric3d — monodepth Metric3D v4
#   exp18_orb_depthpro — monodepth Depth Pro v4

set -e

# ─── 경로 설정 ────────────────────────────────────────────────────────────────
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
SOURCE=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/data/rgb_3dgs_openmavis_orb_full_301_1253
RESULTS=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments
PLATEAU_CFG=$REPO/configs/plateau_loss

# ─── 공통 학습 파라미터 (exp08 best 설정 기반) ────────────────────────────────
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

# ─── 실행 함수 ────────────────────────────────────────────────────────────────
run_exp() {
    local name=$1
    local plateau_cfg=$2   # "" = 없음
    local ts
    ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"

    echo ""
    echo "══════════════════════════════════════════════"
    echo "  START: $name"
    echo "  output: $outdir"
    echo "  time:   $(date)"
    echo "══════════════════════════════════════════════"

    local args=("${COMMON_ARGS[@]}" --model_path "$outdir")
    if [[ -n "$plateau_cfg" ]]; then
        args+=(--plateau_loss_config "$plateau_cfg")
    fi

    cd "$REPO"
    conda run -n 3dgs python train.py "${args[@]}" 2>&1 | tee "$outdir/../${name}_${ts}.log" || true

    echo ""
    echo "  DONE:  $name  ($(date))"
}

mkdir -p "$RESULTS"

# ─── 실험 1: baseline (plateau 없음) ──────────────────────────────────────────
run_exp "exp_orb_baseline" ""

# ─── 실험 2: spherical plateau ────────────────────────────────────────────────
run_exp "exp15_orb_spherical" "$PLATEAU_CFG/spherical.yaml"

# ─── 실험 3: ellipsoidal plateau ──────────────────────────────────────────────
run_exp "exp16_orb_ellipsoidal" "$PLATEAU_CFG/ellipsoidal.yaml"

# ─── 실험 4: monodepth Metric3D v4 ───────────────────────────────────────────
run_exp "exp17_orb_metric3d" "$PLATEAU_CFG/monodepth_metric3d_v4.yaml"

# ─── 실험 5: monodepth Depth Pro v4 ──────────────────────────────────────────
run_exp "exp18_orb_depthpro" "$PLATEAU_CFG/monodepth_depthpro_v4.yaml"

echo ""
echo "════════ 전체 완료 ════════"
echo "결과 위치: $RESULTS"
ls -lhd $RESULTS/exp_orb_* $RESULTS/exp1[5678]_orb_* 2>/dev/null | awk '{print $NF, $5}'
