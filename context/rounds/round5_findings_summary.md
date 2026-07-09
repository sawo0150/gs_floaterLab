# Round 5 Findings Summary

작성일: 2026-06-30  
관련 W&B runs: Round 5b (cukasosi), exp13 (h7cqzny3)

---

## 요약

SLAM 삼각화 실패 sparse point를 초기화 전에 카메라 extent 기반으로 필터링하면 Z-floater의 99%를 초기화 시점에서 제거할 수 있다. 단, Z-floater에는 두 개의 별개 집단이 존재하며, 이 필터는 집단 1(SLAM init outlier)만 해결하고 집단 2(densification floater)는 남긴다.

---

## 실험 설계

### 기반 진단 (Round 1+2+3 → Round 5 동기)

| Round | 핵심 발견 |
|---|---|
| 1b | 1,474 Gaussians이 |Z|>3m, 최대 -42.71m |
| 2 | iter 500에 46,264개(14.3%)가 FOV 밖에서 초기화 → 97% pruning → 1,442 frozen at |Z|=42m |
| 3 | Z-outlier는 loss에 53배 덜 민감 (FOV 밖 → gradient~0) |

**진단 결론**: Z-floater 생성의 근본 원인 = SLAM triangulation failure → extreme sparse point → bad initialization.

### 방법

`scene/dataset_readers.py`에 `_filter_pcd_by_camera_bound()` 추가:

```python
def _filter_pcd_by_camera_bound(pcd, cam_infos, expand_factor=3.0):
    cam_centers = []
    for ci in cam_infos:
        C = -ci.R @ ci.T  # R_cam2world already; NOT -R.T @ T
        cam_centers.append(C)
    cam_min = cam_centers.min(axis=0)
    cam_max = cam_centers.max(axis=0)
    cam_span = cam_max - cam_min
    min_margin = np.array([2.0, 2.0, 3.0])  # Z 3m floor-to-ceiling minimum
    margin = np.maximum(cam_span * expand_factor, min_margin)
    lo = cam_min - margin
    hi = cam_max + margin
    # filter points outside [lo, hi] per axis
    ...
```

**핵심 버그 수정** (Round 5a → 5b): `ci.R`은 이미 `R_cam2world`이므로 카메라 center = `-R @ T`. (잘못된 공식 `-R.T @ T`는 오히려 Z-outlier를 2,144개로 증가시킴)

**적용 파라미터**: `init_pcd_filter=true, init_pcd_expand_factor=1.0`  
→ Filter bounds: Z[-3.05, +3.03]m (카메라 elevation mean=5.39°이므로 수평 궤적 반영)  
→ 제거: 46,276 / 626,811 sparse points (**7.38%**)

---

## Round 5b 결과 (7k iter, early validation)

```
Z-outlier @ iter 500:  46,264 → 508  (-98.9%)  ← 핵심: 초기화 시점 제거
Z-outlier @ iter 15k:   1,442 → 374  (-74.1%)
|Z|_max final:          42.20 → 6.21m (-85.3%)
PSNR @ iter 7k:         28.21 → 28.28 (+0.07 dB)
```

→ PSNR neutral-to-positive에서 Z-floater -99% 달성 확인.

---

## exp13 결과 (30k iter, full comparison vs exp08 best)

```
Metric                    | exp08 (baseline) | exp13 (filter) | Δ
------------------------------------------------------------------
Z-outlier @ iter 500      |           46,264 |           507  | -99.0%
Z-outlier @ iter 30k      |            1,474 |           385  | -73.9%
|Z|_max final (m)         |            42.71 |          4.85  | -88.6%
PSNR @ iter 30k (train)   |           33.012 |         32.855 | -0.16 dB
Ambiguity positive_ratio  |            33.3% |          35.0% | +1.7 pp
```

### 예상 외 발견: Ambiguity 악화

필터 적용 후 ambiguity_positive_ratio가 **33.3% → 35.0%로 증가**.

**원인 분석**: Z-floater는 두 개의 서로 다른 집단으로 구성됨.

| | Pop 1: SLAM Init Outlier | Pop 2: Densification Floater |
|---|---|---|
| 기원 | SLAM 삼각화 실패 | 3DGS densification 중 |
| |Z| 범위 | >42m (극단) | 3-6m (씬 경계부) |
| FOV 위치 | **밖** (rendering에 안 나타남) | **안** (이미지에 투영됨) |
| Ambiguity 기여 | **없음** | **있음** |
| 이번 필터 효과 | **-99%** | **없음** |

exp08에서 ambiguity를 만드는 것은 Pop 2 (3-6m)이고, Pop 1 (42m)은 image-space에 나타나지 않았다. 따라서 Pop 1을 제거해도 ambiguity는 개선되지 않았고, 오히려 Pop 2만 남아 상대적으로 비율이 올라갔다.

---

## 수정된 논문 스토리

### Contribution 1 (확정): Pop 1 Elimination

> **"SLAM 삼각화 실패로 생기는 극단 sparse point를 카메라 extent 기반으로 필터링하면, 3DGS 초기화 시점에서 Z-floater의 99%를 -0.16 dB PSNR 비용으로 제거할 수 있다."**

코드: 12줄, 추가 학습 비용 없음, hyperparameter 최소화.

### Open Problem (Round 6 목표): Pop 2 Intervention

Pop 2 densification floater 특성:
- iter 100~7000 사이 densification으로 생성
- |Z| = 3-6m (filter boundary 근처에서 파생)
- FOV 안에 존재 → photometric loss에 보임 → 그럼에도 불구하고 남는 이유?
  - P03 가설: Z-axis elongated Gaussian이 densification 후 Z 방향으로 분리됨
  - P01 가설: Ray density void 구간에서 optimization이 수렴하지 않음

**Round 6 후보 방향**:
1. Z-elongation pruning: `scale_z / scale_xy_max > threshold` → pruning target
2. Ambiguity-guided densification: ambiguity map 기반으로 densification 억제
3. camera-extent-aware gradient threshold: FOV 경계부 Gaussian에 더 높은 densification 기준

---

## 생성된 파일

- `results/diagnostic/round5b_intervention_results.png` — Round 5b Z-outlier 시계열 비교
- `results/diagnostic/exp13_final_comparison.png` — exp08 vs exp13 전체 비교
- `repos/main/3dgs-custom/scene/dataset_readers.py` — `_filter_pcd_by_camera_bound()` 추가
- `repos/main/3dgs-custom/scene/__init__.py` — filter 파라미터 전달
- `repos/main/3dgs-custom/core/config_bridge.py` — Hydra config 매핑
- `repos/main/3dgs-custom/configs/dataset/mavis_301_1253_full.yaml` — 기본값 추가
- `scripts/diagnostic/run_round5_pcd_filter.sh` — Round 5 학습 스크립트
- `scripts/experiments/run_exp13_pcd_filter_full.sh` — exp13 full 30k 학습 스크립트
