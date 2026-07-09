#!/usr/bin/env bash
# 원본 Aria VRS → OpenMAVIS SLAM → 전체 프레임 RGB 3DGS 학습 데이터
# 사용: run_full_pipeline.sh [stage1|stage2|stage3]   (인자 없으면 전체 실행)
set -euo pipefail

LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
OPENMAVIS=/home/wosas/Desktop/SLAM_custom/OpenMAVIS
VRS=/home/wosas/Desktop/26-1_RPM/Datas/CustomData/0416_Data/0416_301-1253/0416_301-1253.vrs

EUROC=$LAB/data/01_euroc_openmavis_input
SLAM_OUT=$LAB/data/02_openmavis_output
GS_DATA=$LAB/data/03_rgb_3dgs_full
RUN_NAME=aria_301_1253_rebuild

stage1() {
  echo "== stage1: VRS -> EuRoC =="
  conda run -n aria python "$OPENMAVIS/tools/aria_to_orbslam3_euroc.py" \
    --input "$VRS" --output "$EUROC" \
    --mode stereo-aria-fisheye \
    --left camera-slam-left --right camera-slam-right --imu imu-right \
    --viewer 0 --overwrite
}

stage2() {
  echo "== stage2: OpenMAVIS stereo-inertial SLAM =="
  mkdir -p "$SLAM_OUT/orb_output" "$SLAM_OUT/orb_export" "$SLAM_OUT/logs"
  cd "$SLAM_OUT/orb_output"
  ORB_GS_EXPORT_DIR="$SLAM_OUT/orb_export" \
    "$OPENMAVIS/Examples/Stereo-Inertial/stereo_inertial_euroc" \
    "$OPENMAVIS/Vocabulary/ORBvoc.txt" \
    "$EUROC/Aria.yaml" "$EUROC" "$EUROC/timestamps.txt" \
    "$RUN_NAME" 0 2>&1 | tee "$SLAM_OUT/logs/stage2_slam.log"
}

stage3() {
  echo "== stage3: full-frame RGB 3DGS dataset =="
  conda run -n aria python "$LAB/scripts/pipeline/full_traj_to_rgb_3dgs.py" \
    --frame-traj "$SLAM_OUT/orb_output/f_${RUN_NAME}.txt" \
    --orb-export "$SLAM_OUT/orb_export" \
    --aria-yaml "$EUROC/Aria.yaml" \
    --vrs "$VRS" \
    --output "$GS_DATA"
}

case "${1:-all}" in
  stage1) stage1 ;;
  stage2) stage2 ;;
  stage3) stage3 ;;
  all) stage1; stage2; stage3 ;;
  *) echo "usage: $0 [stage1|stage2|stage3]" >&2; exit 1 ;;
esac
