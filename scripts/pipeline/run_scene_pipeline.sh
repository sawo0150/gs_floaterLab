#!/usr/bin/env bash
# 임의 장면용 파이프라인: VRS → EuRoC → OpenMAVIS → RGB 3DGS
# 사용: run_scene_pipeline.sh <scene_name> <vrs_path>
set -euo pipefail
SCENE=$1; VRS=$2
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
OPENMAVIS=/home/wosas/Desktop/SLAM_custom/OpenMAVIS
BASE=$LAB/data/scenes/$SCENE
EUROC=$BASE/01_euroc; SLAM_OUT=$BASE/02_slam; GS_DATA=$BASE/03_rgb_3dgs
RUN_NAME=aria_$SCENE
mkdir -p "$BASE"

echo "== [$SCENE] stage1: VRS -> EuRoC =="
conda run -n aria python "$OPENMAVIS/tools/aria_to_orbslam3_euroc.py" \
  --input "$VRS" --output "$EUROC" --mode stereo-aria-fisheye \
  --left camera-slam-left --right camera-slam-right --imu imu-right \
  --viewer 0 --overwrite

echo "== [$SCENE] stage2: OpenMAVIS SLAM =="
mkdir -p "$SLAM_OUT/orb_output" "$SLAM_OUT/orb_export" "$SLAM_OUT/logs"
cd "$SLAM_OUT/orb_output"
ORB_GS_EXPORT_DIR="$SLAM_OUT/orb_export" \
  "$OPENMAVIS/Examples/Stereo-Inertial/stereo_inertial_euroc" \
  "$OPENMAVIS/Vocabulary/ORBvoc.txt" \
  "$EUROC/Aria.yaml" "$EUROC" "$EUROC/timestamps.txt" \
  "$RUN_NAME" 0 2>&1 | tee "$SLAM_OUT/logs/stage2_slam.log" | tail -3

echo "== [$SCENE] stage3: RGB 3DGS dataset =="
conda run -n aria python "$LAB/scripts/pipeline/full_traj_to_rgb_3dgs.py" \
  --frame-traj "$SLAM_OUT/orb_output/f_${RUN_NAME}.txt" \
  --orb-export "$SLAM_OUT/orb_export" \
  --aria-yaml "$EUROC/Aria.yaml" \
  --vrs "$VRS" \
  --output "$GS_DATA"
echo "== [$SCENE] DONE =="
