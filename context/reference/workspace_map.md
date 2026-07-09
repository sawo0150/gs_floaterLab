# Workspace Map

## Root

- 현재 workspace: `/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab`
- 실험 결과: `results/experiments/` (폴더 규칙은 `results/README.md`)
- 스크립트: `scripts/{pipeline,experiments,diagnostic,analysis,anchors}/` (규칙은 `scripts/README.md`)
- 문서(knowledge base): `context/` (규칙은 `context/README.md`; 구 `docs/`는 2026-07-07 context로 흡수)

## Repos

`repos/main` 아래는 실제 repo로 연결되어 있다.

| 이름 | 경로 | 역할 |
| --- | --- | --- |
| `3dgs-custom` | `/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom` | main 3DGS repo. floater metric, sparse prior, renderer compatibility 수정이 들어간 곳 |
| `OpenMAVIS` | `/home/wosas/Desktop/SLAM_custom/OpenMAVIS` | OpenMAVIS reference/output 확인용 |
| `vggt` | `/home/wosas/Desktop/26-1_RPM/gsProjects/vggt` | VGGT camera/point cloud 비교용 |

## Data (`gs_floaterLab/data/` — 2026-07-07 전면 재구축)

> **구조와 재현 방법은 `data/README.md`가 단일 진실 소스.** 번호 = 파이프라인 순서.

```
data/00_raw_aria_301_1253/       # symlink → 26-1_RPM/Datas/CustomData/0416_Data/0416_301-1253 (VRS+MPS 원본)
data/01_euroc_openmavis_input/   # VRS → EuRoC (1311 스테레오 페어 + IMU + Aria.yaml)
data/02_openmavis_output/        # SLAM 결과: f/kf trajectory + orb_export (57 KF, 7,205 map points)
data/03_rgb_3dgs_full/           # ★ 3DGS 학습 데이터: 1303장 RGB (전체 프레임, OpenMAVIS pose 보간) + ORB points
```

재현: `scripts/pipeline/run_full_pipeline.sh` (stage1/2/3). 핵심 변환: `scripts/pipeline/full_traj_to_rgb_3dgs.py`.

검증 (2026-07-07 빌드): world 정렬 잔차 0.003mm/0.04°, reprojection inside_ratio 0.20 (구 검증 데이터셋 0.25와 동등), 오버레이 시각 확인 완료 → `data/02_openmavis_output/logs/rgb_reprojection_check/`.

구 데이터 (batch/smoke/full/keyframes 심링크들)는 제거. 실제 파일이었던 depth_maps 등은 `data_trash_20260707/`에 보관 중.

---

### 원본 Aria + MPS 처리 결과 (`data/00_raw_aria_301_1253/`)

```
00_raw_aria_301_1253/
├── 0416_301-1253.vrs          # Aria 안경 원본 녹화 (센서 전체 스트림)
├── 0416_301-1253_vrs/         # VRS 메타데이터
└── mps_0416_301-1253_vrs/
    └── slam/
        ├── closed_loop_trajectory.csv     # MPS 폐루프 카메라 궤적
        ├── semidense_points.csv.gz        # ★ MPS semi-dense 포인트 (626,811개)
        ├── semidense_observations.csv.gz  # 포인트별 관측 프레임
        └── summary.json
```

**출처**: Meta Project Aria MPS (Machine Perception Services) — proprietary semi-dense SLAM  
**궤적 정보** (summary.json): 총 길이 32.67m, 65.6초, Vision correction p50=0.34mm (고정밀)

**`semidense_points.csv.gz` confidence 필드** (현재 3DGS 변환 시 버려짐):

| 필드 | 의미 | 분포 (301-1253) |
|---|---|---|
| `inv_dist_std` | 역거리 표준편차. **낮을수록 고정밀** | p50=0.0023, p90=0.0375 |
| `dist_std` | 절대 거리 표준편차(미터). 먼 점일수록 급증 | p50=0.008m, p90=0.222m |

Z-layer별 커버리지 (inv_dist_std < 0.05 기준):
```
Z[-1.00,-0.25)  165,106 pts → 161,002 고confidence  avg dist_std 0.025m
Z[-0.25,+0.50)  102,887 pts →  87,536 고confidence  avg dist_std 0.044m
Z[+0.50,+1.25)  112,816 pts → 103,010 고confidence  avg dist_std 0.073m
Z[+1.25,+2.00)  103,881 pts →  99,670 고confidence  avg dist_std 0.086m
Z[+2.00,+2.75)   20,077 pts →  18,085 고confidence  avg dist_std 0.365m  ← 오차 큼
Z[+2.75,+3.50)    8,783 pts →   7,523 고confidence  avg dist_std 0.968m  ← ~1m 오차
```

> **주의**: 변환 스크립트 `3dgs-custom/aria_to_3dgs.py`는 xyz만 dump, confidence 무시.
> 필터링 적용 시 해당 스크립트 수정 필요.

---

### 기존 MPS 기반 메인 학습 데이터 (exp08~exp26에서 사용)

기존 실험(exp08, exp13, exp19~26)의 학습 소스는 `data/`가 아닌 별도 경로:

```
/home/wosas/Desktop/Incremental_mapping_test/orb_gs_bridge/repos/2dgs/datasets/
  aria_mps_2dgs/0416_Data__0416_301-1253/
    images/       # 1311장 RGB (MPS closed-loop pose 기준)
    sparse/0/
      points3D.txt  # 626,811pts (MPS semidense, confidence 무시하고 전량)
```

→ `semidense_points.csv.gz`를 `3dgs-custom/aria_to_3dgs.py`로 변환한 결과 (xyz만, confidence 버림).

**새 `data/03_rgb_3dgs_full/`과의 차이**: pose가 MPS(proprietary) vs OpenMAVIS(우리 SLAM), init points가 MPS semidense 626k vs ORB map points 7.2k. 두 데이터셋의 실험 결과는 직접 비교하면 안 되고 각자의 baseline과 비교해야 한다.

---

### ORB-SLAM confidence 필드 (map_points.jsonl)

`data/03_rgb_3dgs_full/sparse/0/points3D.txt`에는 confidence 정보가 없다.
원본 `data/02_openmavis_output/orb_export/map_points.jsonl`에만 있음:

| 필드 | 의미 | 분포 (301-1253 orb_export 기준, 11,928pts) |
|---|---|---|
| `observations` | keyframe 관측 수 (nObs) | p50=4, p90=9 |
| `found_ratio` | mnFound/mnVisible (>1.0 가능: 스테레오 double-count) | p50=0.578 |
| `octave` | feature scale level (낮을수록 fine) | observations.jsonl에 per-관측 저장 |

고confidence (obs≥10, found_ratio≥0.5): 861 pts (7.2%) — Pop 2 구간(Z>+2m)은 사실상 0개.

## 주요 Results

| 경로 | 의미 |
| --- | --- |
| `results/experiments/exp01_openmavis_full_baseline*` - `results/experiments/exp12_*` | full OpenMAVIS 기반 3DGS floater 실험 |
| `results/experiments/exp13_pcd_filter_full30k_20260630_140634` | camera-bound sparse point filtering full 30k |
| `results/rounds/round2_grad_diag_z_axis_gradient_verification_20260630_132024` | Z-gradient 가설 검증 |
| `results/rounds/round5_pcd_filter_slam_outlier_filter_x1.0_20260630_135742_fixed` | point-cloud outlier filtering 7k 검증 |
| `results/archive/vggt_smoke_*` | VGGT frame count smoke 결과 |
| `results/datasets/vggt64_3dgs_scene` | VGGT64 기반 3DGS scene |
| `results/datasets/openmavis64_3dgs_scene` | MPS/OpenMAVIS 비교용 64-frame 3DGS scene |
| `results/archive/exp13_vggt64_3dgs_7k_retry_20260630_112335` | VGGT64 3DGS 7k |
| `results/archive/exp14_openmavis64_3dgs_7k_20260630_112820` | OpenMAVIS64/MPS scene 3DGS 7k |
| `results/archive/evo_camparam_mps_vggt_openmavis_64_20260630` | MPS 기준 OpenMAVIS ORB vs VGGT camera EVO report |

중요 PDF:

```text
results/archive/evo_camparam_mps_vggt_openmavis_64_20260630/evo_mps_openmavis_vs_vggt_64_summary_grid.pdf
```

## Environment

- 주요 conda env: `3dgs`
- VGGT는 Python `>=3.10` 요구가 있지만 `3dgs` env는 Python 3.9라서 editable install 대신 `PYTHONPATH`로 사용했다.
- VGGT Python 3.9 compatibility patch:
  - `/home/wosas/Desktop/26-1_RPM/gsProjects/vggt/vggt/dependency/projection.py`
  - `/home/wosas/Desktop/26-1_RPM/gsProjects/vggt/vggt/models/aggregator.py`
- GPU memory 제약 때문에 VGGT는 64 frames가 안정적인 기준이다. 80 frames는 성공했지만, 96/128 frames는 CUDA OOM.

## Dirty Worktree 주의

`3dgs-custom`에는 floater metric, sparse prior, renderer compatibility 관련 수정이 많이 들어가 있다. 다음 agent는 절대 임의로 revert하지 말아야 한다.

특히 `gaussian_renderer/__init__.py`에는 installed `diff_gaussian_rasterization`이 `beta`를 받지 않거나 `alpha_depth/modes`를 반환하지 않는 경우를 위한 compatibility fallback이 들어갔다.

## EVO 주의

`results/archive/evo_camparam_mps_vggt_openmavis_64_20260630/openmavis64_*` 이름의 초기 EVO 결과는 실제 OpenMAVIS SLAM pose가 아니라 MPS-based subset에서 만들어져 APE 0에 가까운 invalid 결과다.

올바른 OpenMAVIS 비교는 아래 파일을 기준으로 봐야 한다.

```text
results/archive/evo_camparam_mps_vggt_openmavis_64_20260630/openmavis_orb_64.tum
results/archive/evo_camparam_mps_vggt_openmavis_64_20260630/vggt64_colmap_cam.tum
results/archive/evo_camparam_mps_vggt_openmavis_64_20260630/mps_rgb_64.tum
```

