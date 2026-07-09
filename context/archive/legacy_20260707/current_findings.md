# Current Findings

## 1. 현재 best full 30k 후보

현재 가장 좋은 full OpenMAVIS 30k 후보는 `exp08_openmavis_full_dens_until7000_prune001_beta1_low_20260616_124504`이다.

| 항목 | 값 |
| --- | --- |
| 핵심 설정 | sparse densification + densify until 7000 + stronger opacity pruning + lower beta1 |
| W&B run | `qd2nqxji` |
| PSNR | 약 33.012 |
| Gaussian count | 323,864 |
| Low opacity ratio | 0.3902 |
| Large scale ratio | 0.0578 |
| Opacity median | 0.1522 |
| Scale median | 0.0265 |
| Nearest ORB median | 0.0247 |

해석:

- default보다 Gaussian 수와 large-scale proxy를 줄이는 방향이 유효했다.
- `densification_interval=200`, `densify_grad_threshold=0.0004`, `densify_until_iter=7000` 계열이 좋은 출발점이다.
- 너무 많은 late densification은 floater를 계속 만든다는 가설이 현재까지 가장 설득력 있다.

## 2. Sparse depth prior 현재 결과

`exp12_openmavis_full_dens_until7000_prune001_beta1_low_sparse_depth_20260616_141814`

| 항목 | exp08 | exp12 sparse depth |
| --- | ---: | ---: |
| W&B run | `qd2nqxji` | `xfmp51m8` |
| PSNR | 33.012 | 32.587 |
| Gaussian count | 323,864 | 326,039 |
| Low opacity ratio | 0.3902 | 0.4042 |
| Large scale ratio | 0.0578 | 0.0581 |
| Opacity median | 0.1522 | 0.1423 |
| Scale median | 0.0265 | 0.0265 |
| Nearest ORB median | 0.0247 | 0.0248 |

해석:

- 현재 sparse prior weight `0.01 -> 0.002`는 품질과 floater proxy를 모두 악화했다.
- sparse point 자체에 outlier가 포함되어 있어, prior를 강하게 걸면 잘못된 geometry를 고정할 위험이 있다.
- 다시 실험한다면 더 약한 weight, delayed start, filtered sparse points, confidence weighting이 필요하다.

## 3. Floater는 한 종류가 아니다

현재 가장 중요한 결론은 floater population이 최소 두 개라는 점이다.

| 구분 | 원인 | 관측 | 현재 대응 |
| --- | --- | --- | --- |
| Pop1 | SLAM sparse init outlier | iter 500에 극단적 Z outlier가 많음. `abs(Z)`가 수십만 m까지 튐 | camera-bound sparse point filtering으로 대부분 제거 |
| Pop2 | densification 이후 내부에서 생기는 floater | Pop1 제거 후에도 FOV 내부, `abs(Z)` 3-6m 계열 잔존 | 아직 미해결. densification/pruning/ambiguity-guided 제어 필요 |

Round5 filter 효과:

| 항목 | before | after |
| --- | ---: | ---: |
| 제거된 sparse init points | - | 46,276 / 626,811, 7.38% |
| Z-outlier @500 | 46,264 | 508 |
| Z-outlier @30k | 1,474 | 385 |
| `abs(Z)` max @30k | 42.71m | 4.85m |
| PSNR @30k | 33.012 | 32.855 |

해석:

- camera-bound init filtering은 Pop1 제거에는 확실히 효과가 있다.
- 다만 PSNR은 약간 낮아졌고 ambiguity positive ratio는 개선되지 않았다.
- 따라서 Pop2를 겨냥한 학습 중 제어가 다음 핵심이다.

## 4. VGGT는 현재 OpenMAVIS 대체재로 부족

VGGT 16/32/64/80 frame smoke를 돌렸고, 64 frame이 가장 균형이 좋았다. 96/128 frame은 VRAM OOM.

VGGT point cloud normalized NN 비교:

| run | vggt -> openmavis median | openmavis -> vggt median |
| --- | ---: | ---: |
| 16 frames | 0.084856 | 0.387392 |
| 64 frames | 0.079784 | 0.356936 |
| 80 frames | 0.089719 | 0.417794 |

64-frame 3DGS 비교:

| 항목 | VGGT64 | OpenMAVIS64/MPS |
| --- | ---: | ---: |
| Test PSNR @7k | 17.04 | 18.65 |
| Train PSNR @7k | 30.26 | 34.25 |
| Gaussian count | 557,481 | 791,532 |
| Large scale ratio | 0.00018 | 0.02987 |
| Low opacity ratio | 0.5575 | 0.7309 |
| Scale median | 0.00737 | 0.02313 |

해석:

- VGGT64는 scale이 작고 compact하지만 render 품질이 낮다.
- OpenMAVIS64/MPS scene은 Gaussian이 많고 proxy는 거칠지만 render 품질은 낫다.

## 5. MPS 기준 camera EVO

올바른 comparison은 `openmavis_orb_64`와 `vggt64_colmap_cam`을 MPS RGB 64 subset에 맞춘 것이다.

| 항목 | OpenMAVIS ORB | VGGT64 COLMAP |
| --- | ---: | ---: |
| APE RMSE | 0.559743 m | 2.676559 m |
| APE median | 0.404957 m | 1.230784 m |
| RPE RMSE | 1.012331 m | 1.109050 m |
| RPE median | 1.033198 m | 0.167441 m |
| Rotation APE RMSE | 142.732642 deg | 27.860771 deg |

해석:

- OpenMAVIS는 absolute path가 MPS에 훨씬 가깝다.
- VGGT는 local motion median은 작지만 global alignment가 좋지 않다.
- rotation은 frame convention 이슈 가능성이 있어 translation 위주로 판단하는 것이 안전하다.

보고서:

```text
results/evo_camparam_mps_vggt_openmavis_64_20260630/evo_mps_openmavis_vs_vggt_64_summary_grid.pdf
results/evo_camparam_mps_vggt_openmavis_64_20260630/report.md
```

## 8. Plateau Loss 후보 설계 완료 (2026-07-05)

### 앵커 필터링 Pipeline (확정)

Stage 3 필터 = Z-bound + obs≥3 + kNN isolation(k=5, 3×median) → **6,492 앵커 pts**

| 단계 | 제거 수 | 누적 남은 pts |
|---|---|---|
| Z-bound | 11 | 7,171 |
| obs≥3 | 67 | 7,104 |
| kNN isolation (threshold=0.433m) | 612 | **6,492** |

### Candidate A — 구형 Plateau (v1)

```
tau_j = clip(0.6 × h_j,  0.05m, 0.60m)
h_j = kNN-5 3D 거리 (median 0.144m)
tau median = 0.087m
```

- XY coverage (layer 4): **11.9%**
- loss: `L = mean(max(||x-p||/tau - 1, 0)^2)` (quadratic hinge)

### Candidate B — 타원체 Plateau (v2)

```
tau_n = clip(0.4 × h_j,  0.03m, 0.30m)   # 법선 방향 tight
tau_t = clip(0.9 × h_j,  0.03m, 0.60m)   # 접선 방향 loose
법선 u_n = kNN-5 PCA 최소 고유벡터
tau_n median = 0.054m, tau_t median = 0.121m
planarity median = 0.186 (k=5라 노이즈 많음)
```

- XY coverage (layer 4): **14.0%** (+2.1% vs 구형)
- loss: quadratic hinge on `D_aniso = sqrt((Δ·u_t1/τ_t)²+(Δ·u_t2/τ_t)²+(Δ·u_n/τ_n)²)`

### 공통 한계: Pop 2 구간 (Z>+2m)

**두 후보 모두 layer 8 (Z∈[+2.26,+3.02)) coverage = 0%.**
ORB-SLAM 앵커 9개뿐이라 plateau 자체가 작동 안 함.
→ **hard Z-clip pruning 필수 병행** (Z>+2m Gaussian 주기 제거, start_iter=5000, interval=1000)

### 실험 계획

| 실험 | Candidate | lambda | 비교 기준 |
|---|---|---|---|
| exp15 | 구형 (A) + Z-clip | 0.01 | exp13 (32.855) |
| exp16 | 타원체 (B) + Z-clip | 0.01 | exp13 |

상세 설계: `context/sparse_support_potential_field.md` → "3DGS Loss 연결 설계" 섹션

### 관련 스크립트 (모두 실행 가능 상태)

```
scripts/diagnostic/orb_zlayers_v1.py          — ORB-SLAM Z-layer 시각화
scripts/diagnostic/filtering_stages_plateau.py — 4단계 필터링 × zlayer+plateau PDF (각 8개)
scripts/diagnostic/plateau_ellipsoid_v2.py     — 타원체 plateau coverage 시각화
```

### 관련 결과 PDF

```
results/diagnostic/orb_zlayers_v1_20260705_014758/orb_zlayer_annotated.pdf
results/diagnostic/filtering_stages_20260705_021252/   (8 PDFs)
results/diagnostic/plateau_ellipsoid_v2_20260705_023632/ellipsoid_plateau.pdf
```

## 다음으로 볼 가설

1. Pop2 floater 제어:
   - ambiguity positive region에서 densification 제한.
   - large-scale/low-opacity Gaussian pruning schedule 강화.
   - z-elongated Gaussian 또는 camera-ray depth ambiguity 기반 pruning.

2. Sparse prior 재설계:
   - init outlier filtering 이후에만 sparse prior 적용.
   - `0.01 -> 0.002`보다 훨씬 약하게 시작.
   - early geometry lock-in을 피하기 위해 delayed start.

3. Optimizer/LR:
   - beta1을 낮추는 실험은 "momentum으로 local minima 탈출"이 아니라 "잘못된 early momentum 누적을 줄이는" 관점이었다.
   - 다음에는 beta1 단독보다 position/scaling LR schedule, densification timing과 함께 봐야 한다.

4. VGGT 재검토 조건:
   - 더 많은 frame을 쓰려면 RAM이 아니라 VRAM/attention memory가 병목이다.
   - chunked inference, lower resolution, point cap 조정, frame selection 개선 없이는 OpenMAVIS 대체 가능성이 낮다.

## 6. 3DGS 학습 init point cloud의 실제 출처 (2026-07-05 확인)

**핵심 발견**: 626,811개 init points는 OpenMAVIS ORB-SLAM이 아니라 **Aria MPS semi-dense** 출력이다.

변환 파이프라인:
```
semidense_points.csv.gz  →  aria_to_3dgs.py  →  sparse/0/points3D.txt
(MPS 제공, confidence 포함)    (confidence 버림)    (xyz + 128 128 128 0)
```

`aria_to_3dgs.py`는 `inv_dist_std`/`dist_std` 필드를 읽지 않고 xyz만 덤프한다.
즉 **현재 3DGS는 모든 MPS 점을 동등하게 취급하고 있으며, confidence 기반 필터링이 전혀 없다.**

현재 Pop1 filtering (`_filter_pcd_by_camera_bound()`)이 제거하는 7.38% (46,276 pts)는
confidence가 낮아서가 아니라 camera extent 밖에 있어서 제거되는 것이다.

**MPS confidence 특성:**
- inv_dist_std < 0.05 기준으로 이미 92.8%가 고confidence → 단순 필터링으론 큰 변화 없음
- Pop 2 구간(Z=+2~3.5m)도 MPS에서는 28,860pts 존재하나 dist_std ~0.4~1m (절대 위치 불확실)
- ORB-SLAM은 동일 구간에 고confidence 점이 사실상 0개 (삼각화 각도 부족)

**다음 단계 시사점:**
- MPS confidence 필터링 자체는 효과 제한적 (92.8%가 이미 통과)
- 더 유효한 접근: inv_dist_std 대신 dist_std (절대 오차) threshold 활용 → 천장/먼 표면 점 제거
- 또는 confidence를 plateau potential 가중치로 활용 (정밀한 점 주변은 강한 plateau)

자세한 분석: `workspace_map.md` → "Point Cloud Data Sources" 섹션 참조.

## 8. 3D Plateau Loss 구현 및 ORB 실험 결과 (Round 6)

### 8.1 Plateau Loss 구현

**파일**: `/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom/eval/plateau_loss.py`

핵심 설계:
- 전체 Gaussian에 loss가 가는 구조 (photometric loss는 visible Gaussian만)
- Cyclic sampler: `sample_size=8192`, ceil(N/8192)회마다 모든 Gaussian 커버 보장
- `start_iter=5000`부터 `lambda_plateau=0.01`로 적용
- `pop2_zclip=True`: iter 5000부터 Z >= 2.0m Gaussian 매 1000 iter 제거

**3가지 타입**:

| 타입 | anchor | 특징 |
| --- | --- | --- |
| spherical | SLAM filtered 6,492 pts | tau = clip(0.6*h_j, 0.05, 0.60) |
| ellipsoidal | SLAM filtered 6,492 pts | kNN PCA로 surface normal 추정, tau_n tight / tau_t loose |
| monodepth | metric3d 9,110 / depthpro 7,338 pts | virtual anchors |

**YAML toggle**: `configs/plateau_loss/{off,spherical,ellipsoidal,monodepth_metric3d_v4,monodepth_depthpro_v4}.yaml`

### 8.2 발견된 버그 및 수정

**Bug 1**: `gaussian_model.py` line 409

```python
# 수정 전
self.tmp_radii = self.tmp_radii[valid_points_mask]  # None이면 crash

# 수정 후
if self.tmp_radii is not None:
    self.tmp_radii = self.tmp_radii[valid_points_mask]
```

`densify_and_prune` 종료 시 `tmp_radii = None`으로 리셋됨. 이후 Z-clip이 `prune_points` 호출 시 None 인덱싱 오류.

**Bug 2**: `train.py` - `post_backward` 위치 오류

Z-clip을 `densify_and_prune` 이전에 실행하면 `radii` 크기(N) vs Gaussian 배열 크기(N-N_pruned) 불일치 → CUDA device-side assert.

수정: `post_backward` 호출을 densification 블록 이후로 이동.

```python
# 수정 전 (line 323): densification 이전
plateau_metrics.update(plateau_loss.post_backward(gaussians, iteration))

# 수정 후 (line 447): densification 이후
plateau_metrics.update(plateau_loss.post_backward(gaussians, iteration))
```

### 8.3 ORB 실험 데이터

**Dataset**: `rgb_3dgs_openmavis_orb_full_301_1253`
- trajectory: ORB-SLAM (656 frames, odd 1-1311)
- init: ORB-SLAM sparse 7,182 pts (anchor: filtered 6,492 pts)

**속도**: baseline ~68 it/s, plateau loss 적용 시 ~38 it/s (26ms/iter, 약 44% 감소)

### 8.4 실험 결과 (Round 6 완료, ORB init baseline=29.0226)

| 실험 | Plateau 타입 | 앵커 | PSNR@7k | PSNR@30k | vs baseline |
| --- | --- | --- | ---: | ---: | ---: |
| exp_orb_baseline | 없음 | - | 25.3237 | **29.0226** | - |
| exp15_orb_spherical | spherical | ORB 6,492pt | 24.9010 | 27.9082 | -1.10 dB |
| exp16_orb_ellipsoidal | ellipsoidal | ORB 6,492pt | 25.0716 | 28.9239 | -0.10 dB |
| exp17_orb_metric3d | ellipsoidal | Metric3D 9,110pt | 24.5279 | 27.6681 | -1.35 dB |
| exp18_orb_depthpro | ellipsoidal | DepthPro 7,338pt | **25.3857** | 28.9343 | **-0.09 dB** |

**참고**: exp08 (OpenMAVIS MPS, full init) PSNR@30k = 33.012 (비교군 다름, ORB init은 sparse라 4 dB 낮음)

### 8.5 관찰 및 해석

**Round 6 핵심 결론**
- 어떤 plateau 설정도 baseline을 이기지 못함. 최선(exp18)도 -0.09 dB
- **타입**: ellipsoidal >> spherical. 동일 앵커에서 spherical → ellipsoidal만으로 +1.0 dB
- **앵커**: DepthPro ≈ ORB (ellipsoidal) >> Metric3D. 앵커 수가 많다고 좋지 않음
- exp18 PSNR@7k=25.3857이 baseline 25.3237보다 약간 높음 → DepthPro plateau가 초기 수렴을 돕지만 후반에 중립화됨

**exp15 (spherical, -1.10 dB)**
- low_opacity_ratio: 32.0% → 62.6% 급증. ORB 6,492개 앵커에 Gaussian 과밀집 → photometric loss가 투명화
- Z-clip 거의 무효: ORB 좌표계에서 Z>=2.0 조건이 Pop2 floater를 거의 잡지 못함 (12개만 제거)

**exp16 (ellipsoidal ORB, -0.10 dB)**
- α_n=0.4, α_t=0.9: normal 방향 plateau 넓어 tangential로 분산 → 과밀집 완화
- 동일 앵커임에도 spherical 대비 +1.0 dB

**exp17 (metric3d, -1.35 dB — 최악)**
- 앵커 수(9,110)가 가장 많음에도 성능 최악
- knn_iso_mult=0 + 앵커 품질 문제 가능성: Metric3D depth가 이 장면에서 부정확하면 잘못된 surface normal이 plateau를 왜곡
- 또는 9,110개 앵커가 overkill → 너무 넓은 plateau → 유효한 geometry 방향을 막음

**exp18 (depthpro ellipsoidal, -0.09 dB — 최선)**
- DepthPro 7,338pt + ellipsoidal: ORB 앵커보다 dense하면서도 knn_iso_mult=0
- PSNR@7k에서 baseline을 0.06 dB 초과 → 초기 densification에서 floater 억제 효과 있음
- 장기적으로 plateau loss가 PSNR 상한을 약간 눌러 중립

**다음 방향 가설**
- lambda 약화: 현재 0.01 → 0.001-0.005로 줄여 plateau 강도 감소
- 조기 종료: densification 이후(iter>7000) plateau 제거, init 단계만 적용
- OpenMAVIS init + plateau: ORB sparse init 대신 semidense init → 더 좋은 prior
- Z-clip 재설계: ORB 좌표계 Z 기준이 아닌 카메라 거리 기반으로 변경

## 7. 새 연구축: sparse support scalar potential

Photometric loss는 rendered pixel에 기여한 Gaussian에만 gradient를 주기 때문에 ray-triggered gradient 한계가 있다. 이를 보완하기 위해 dense depth 없이 init sparse 3D map만으로 support plateau를 만들고, plateau 밖에서만 gradient가 생기는 scalar potential field를 검토하기 시작했다.

현재 구현은 2D toy 단계다.

```text
context/sparse_support_potential_field.md
scripts/diagnostic/toy_sparse_support_potential.py
results/diagnostic/toy_sparse_support_potential_20260704_182754/toy_sparse_support_potential_report.pdf
```

첫 실행 요약:

| 항목 | 값 |
| --- | ---: |
| sparse points | 64 |
| ray segments | 107 |
| fixed tau | 0.28 |
| adaptive alpha | 0.82 |
| adaptive tau median | 0.1693 |
| fixed plateau area fraction | 0.1437 |
| adaptive plateau area fraction | 0.2215 |
| weak-ray but potential-active fraction | 0.6772 |

초기 해석:

- adaptive radius는 sparse한 구간의 support hole을 줄이지만, outlier 주변 plateau도 키울 수 있다.
- plateau 내부에서 force가 0인 조건은 photometric optimization을 방해하지 않는다는 설계 의도와 맞다.
- ray coverage와 potential coverage는 분명히 다른 공간 신호를 만들기 때문에, Pop2 floater 제어용 regularizer 후보로 더 볼 가치가 있다.
