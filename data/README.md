# data/ — OpenMAVIS 3DGS 학습 데이터 파이프라인

2026-07-07 전면 재구축. 번호 = 파이프라인 순서. 각 단계는 이전 단계에서만 생성된다.

```
00_raw_aria_301_1253/        (symlink, 읽기 전용 원본)
   └─ 0416_301-1253.vrs      Aria 원본 녹화 (실제 위치: 26-1_RPM/Datas/CustomData/0416_Data/)
        │
        ▼  scripts/pipeline/run_full_pipeline.sh stage1
01_euroc_openmavis_input/    VRS → EuRoC 형식 변환 (OpenMAVIS 입력)
   ├─ Aria.yaml              카메라/IMU 캘리브레이션 (Fisheye624, Tbc 포함)
   ├─ timestamps.txt         1311 frames
   └─ mav0/{cam0,cam1}/data  SLAM 스테레오 fisheye 이미지 각 1311장, imu0/data.csv
        │
        ▼  stage2 (stereo_inertial_euroc)
02_openmavis_output/         OpenMAVIS SLAM 실행 결과
   ├─ orb_output/f_aria_301_1253_rebuild.txt    전체 프레임 body pose (첫 KF 재원점화 world)
   ├─ orb_output/kf_aria_301_1253_rebuild.txt   keyframe trajectory
   ├─ orb_export/            keyframes.jsonl(Tcw, raw world) + map_points.jsonl + observations.jsonl
   └─ logs/
        │
        ▼  stage3 (scripts/pipeline/full_traj_to_rgb_3dgs.py)
03_rgb_3dgs_full/            ★ 3DGS 학습 데이터 (COLMAP text 형식)
   ├─ images/                undistorted RGB 1024×1024 PINHOLE f=500, 전체 프레임
   ├─ sparse/0/              cameras.txt / images.txt(OpenMAVIS pose) / points3D.txt(ORB map points)
   └─ pose_sanity.json       프레임 수, 보간 gap, world 정렬 잔차
```

## 좌표계 주의 (stage3가 처리함)

- `f_*.txt`는 **첫 keyframe body 기준으로 재원점화**된 world, `map_points.jsonl`은 raw Atlas world.
- stage3가 timestamp 매칭된 keyframe들로 정렬 변환을 계산·검증(잔차 mm 단위 확인) 후 raw world로 통일한다.
- RGB 프레임 pose는 SLAM 프레임 pose의 SE3 보간 (slerp + lerp).

## 재현

```bash
scripts/pipeline/run_full_pipeline.sh            # 전체 (stage1→2→3)
scripts/pipeline/run_full_pipeline.sh stage3     # 특정 단계만
```

## 이전 데이터

2026-07-07 이전의 심링크 무더기(batch/smoke/full/keyframes 등)는 제거했다.
실제 파일이었던 `depth_maps/`(monodepth 출력)와 `rgb_3dgs_openmavis_orb_full_301_1253/`은
`../data_trash_20260707/`에 있다. 확인 후 필요 없으면 통째로 삭제하면 된다.
