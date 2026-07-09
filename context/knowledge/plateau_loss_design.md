# Sparse Support Potential Field Toy Study

## 목적

이 문서는 3D Gaussian Splatting에서 photometric loss의 ray-triggered gradient 한계를 보완하기 위한 3D sparse support potential field 아이디어를 정리한다. 현재 단계의 목표는 3DGS 학습 코드에 바로 loss를 넣는 것이 아니라, 2D toy visualization으로 plateau 정의와 potential field shape이 타당한지 먼저 검토하는 것이다.

## 문제의식

3DGS의 photometric loss는 Gaussian이 rendered pixel에 기여할 때만 gradient를 준다. 따라서 sparse-view, 초기 reconstruction, incremental reconstruction에서는 다음 문제가 생길 수 있다.

- 어떤 Gaussian은 충분한 camera ray를 받지 못해 photometric gradient가 약하다.
- 잘못된 위치에 있는 Gaussian이 rendered pixel에 거의 기여하지 않으면 움직일 신호가 부족하다.
- floater나 잘못된 geometry가 photometric gradient만으로는 local minimum에 남을 수 있다.

이 문제를 dense depth, monocular depth foundation model, semantic prior로 해결하려는 것이 아니다. 현재 사용할 수 있는 init sparse 3D map, images, camera poses, feature observation 정보만으로 conservative한 3D support field를 만들 수 있는지 보는 것이 핵심이다.

## 핵심 아이디어

Sparse init map을 `P = {p_j}`라고 하자. 각 sparse point 주변에 radius `tau_j`를 두고 normalized distance를 정의한다.

```text
D(x) = min_j ||x - p_j|| / tau_j
```

Plateau는 다음 영역이다.

```text
D(x) <= 1
```

Potential은 scalar field 하나로 둔다.

```text
Phi(x) = rho(D(x))
```

`rho`는 아래 조건을 만족해야 한다.

```text
rho(r) = 0,       if r <= 1
rho'(r) > 0,      if r > 1
```

즉 plateau 내부에서는 potential과 gradient가 0이다. 이 영역에서는 기존 photometric optimization이 Gaussian을 자유롭게 움직인다. 반대로 plateau 밖에서는 potential gradient가 생겨 Gaussian center를 sparse surface support 쪽으로 당긴다.

## 중요한 설계 지점

Potential 함수 자체보다 plateau region을 어떻게 정의하느냐가 더 중요하다.

### Fixed radius

모든 sparse point에 같은 radius를 준다.

장점:

- 단순하고 해석이 쉽다.
- hyperparameter가 하나다.

위험:

- sparse point가 조밀한 곳에서는 plateau가 너무 넓어질 수 있다.
- sparse point가 드문 곳에서는 point 사이에 구멍이 생긴다.

### Adaptive local spacing radius

각 sparse point의 local spacing `h_j`를 k-nearest neighbor 거리로 추정하고, `tau_j = alpha * h_j`로 둔다.

장점:

- dense region에서는 작은 plateau, sparse region에서는 큰 plateau를 만들 수 있다.
- point density가 불균일한 init map에 더 자연스럽다.

위험:

- outlier 주변에서는 `h_j`가 커져 잘못된 plateau가 생길 수 있다.
- 따라서 실제 3D 적용 전에는 sparse init outlier filtering과 같이 써야 한다.

## 비교할 potential shape

같은 plateau에 대해 세 가지를 비교한다.

| 이름 | 형태 | 기대 효과 | 위험 |
| --- | --- | --- | --- |
| quadratic hinge | `[D-1]_+^2` | 먼 floater를 강하게 당김 | unknown region까지 과하게 제약 |
| Huber-like | small residual은 quadratic, large residual은 linear | robust한 중간안 | delta 선택 필요 |
| saturating | 멀어질수록 gradient가 약해짐 | 매우 먼 unknown/outlier에 둔감 | 먼 floater correction이 약함 |

## 2D toy에서 확인할 것

1. Sparse init point distribution과 local spacing `h_j`.
2. Fixed `tau`와 adaptive `tau_j`의 plateau 차이.
3. Camera/ray distribution이 공간 어디에 집중되는지.
4. Potential heatmap과 force field `-grad Phi`.
5. Potential shape별 force strength 차이.
6. Photometric gradient가 없다고 가정한 Gaussian center dynamics.
7. Ray coverage와 potential coverage의 차이.

## 현재 toy 구현

실행 스크립트:

```text
scripts/diagnostic/toy_sparse_support_potential.py
```

기본 실행:

```bash
python scripts/diagnostic/toy_sparse_support_potential.py
```

출력:

```text
results/diagnostic/toy_sparse_support_potential_<timestamp>/
```

대표 output:

- `toy_sparse_support_potential_report.pdf`
- `summary.json`
- 개별 PNG figure들

## 해석 기준

이 접근이 유망하려면 다음이 보여야 한다.

- adaptive plateau가 sparse point 사이의 구멍을 줄이면서도 과도하게 넓어지지 않는다.
- plateau 내부 force가 0이라서 surface 근처 Gaussian을 photometric loss가 자유롭게 조정할 수 있다.
- plateau 밖 force가 가까운 support 쪽으로 안정적으로 향한다.
- ray coverage가 약한 영역에서도 sparse support potential은 gradient를 줄 수 있다.
- saturating/Huber-like potential이 너무 먼 unknown region을 quadratic보다 덜 과하게 끈다.

## 3DGS 적용 전 주의

- 이 아이디어는 free-space loss나 dense depth regularization이 아니다.
- 하나의 scalar potential field로 plateau와 force를 동시에 표현하는 접근이다.
- 실제 3D 적용 시에는 sparse init outlier가 plateau를 오염시키지 않도록 먼저 filtering해야 한다.
- Gaussian center에만 적용할지, scale/opacity와 결합할지는 아직 별도 문제다.
- potential gradient가 photometric optimization을 방해하지 않도록 plateau 내부 gradient 0 조건을 유지하는 것이 핵심이다.

---

## 실제 목표: OpenMAVIS ORB-SLAM 포인트로 Pop 2 floater 억제

**목표**: OpenMAVIS ORB-SLAM이 생성한 sparse map points를 plateau 앵커로 써서 densification 과정에서 생기는 Pop 2 floater(Z=+2~3m)를 potential field로 잡는다.

### 사용 데이터

```text
data/rgb_3dgs_openmavis_batch_301_1253/sparse/0/points3D.txt
  — 7,182 pts (xyz, ORB-SLAM map points를 RGB camera 좌표계로 변환)

data/rgb_3dgs_openmavis_smoke_301_1253/sparse/0/points3D.txt
  — 8,150 pts (동일한 방식, smoke run)

confidence 필드는 원본 jsonl에 있음 (points3D.txt에는 없음):
  orb_gs_bridge/.../orb_export/map_points.jsonl
  컬럼: map_point_id, xyz, observations, found_ratio
  orb_gs_bridge/.../orb_export/observations.jsonl
  컬럼: map_point_id, keypoint_idx, camera_id, u, v, octave
```

### OpenMAVIS confidence 필드 설명

ORB-SLAM3 내부에서 각 map point는 두 가지 지표로 품질을 추적한다:

| 필드 | 의미 | 분포 (301-1253, 11,928 pts) |
|---|---|---|
| `observations` | 몇 개 keyframe에서 관측됐는가 (nObs) | p50=4, p90=9, p99=15 |
| `found_ratio` | mnFound/mnVisible — 예측 가시 대비 실제 매칭 비율 | p50=0.578, p90=0.952 |
| `octave` | feature scale level (낮을수록 fine feature, 높을수록 coarse) | per-관측 저장, p50=2.5 |

`found_ratio > 1.0` (약 6%)은 스테레오 카메라에서 left/right 양쪽이 매칭될 때 발생하는 정상 현상.

**고confidence 기준별 점 수:**
- `observations >= 10 & found_ratio >= 0.5`: **861 pts** (7.2%)
- `observations >= 8 & found_ratio >= 0.6 & octave <= 5`: **1,268 pts** (10.6%)

### confidence를 tau 설계에 반영

단순 fixed/adaptive tau 대신, ORB-SLAM confidence로 tau를 제어한다.

**기본 방향 — confidence-weighted tau:**

```text
tau_j = tau_base / confidence_score_j
```

- 고confidence 점 (many observations, high found_ratio): 좁은 plateau → Gaussian을 정확한 표면 근처에 고정
- 저confidence 점: 넓은 plateau → rough 인력장만 제공

또는 고confidence 점만 선별해서 사용하는 단순한 방법:

```text
앵커 = { p_j | observations_j >= 8 AND found_ratio_j >= 0.5 }
tau = fixed (e.g. adaptive kNN-based)
```

### Pop 2 구간의 한계

**핵심 문제**: Z=+2~3m 구간(Pop 2 floater 서식지)에서 OpenMAVIS 고confidence 점이 사실상 0개다.

| Z 구간 | 전체 pts | 고confidence (obs≥10, fr≥0.5) |
|---|---|---|
| Z[+1.25, +2.00)m | 1,573 | 176개 |
| Z[+2.00, +2.75)m | 108 | 6개 |
| Z[+2.75, +3.50)m | 25 | **0개** |

이유: 카메라가 Z≈0에서 수평 이동하므로, 천장(Z=+2~3m)을 올려다보는 ray angle이 작아 삼각화 각도 부족 → ORB-SLAM이 해당 구간 점을 거의 못 찍음.

**대응 방향 (현재 논의 중):**
- OpenMAVIS 점이 없는 구간은 plateau가 생기지 않으므로 potential이 작동하지 않음
- 이 구간을 보완하는 별도 제약(hard Z-bound pruning, ray density 기반 penalty 등)과 병행 필요
- 또는 MPS semi-dense 포인트(해당 구간 28,860개 존재)를 보조 앵커로 추가 — 단, dist_std ~1m으로 정밀도 낮음

### 필터링 전략

points3D.txt(7,182~8,150개)는 이미 소규모이므로 전량 사용 가능.
confidence 기반 선별 시 map_points.jsonl에서 읽어서 xyz와 join:

1. `map_points.jsonl` 로드 → observations, found_ratio 기준 필터링
2. 필터링된 map_point_id에 해당하는 xyz 사용
3. (선택) 카메라 bound 필터 적용 — `_filter_pcd_by_camera_bound()` 기준

### 다음 구현 단계

1. `map_points.jsonl`에서 고confidence 점 추출 → 2D XZ/XY 단면 plateau potential 시각화
2. Z-layer별 plateau 커버리지 확인 (Pop 2 구간 공백 정량화)
3. Pop 2 구간 공백 대응 전략 결정 (MPS 보조 앵커 vs hard pruning 병행)
4. 3DGS 학습 루프 연결: Gaussian center와 nearest anchor 거리 → potential loss
5. exp13 대비 Pop 2 floater 수 및 PSNR 비교

---

## Filtering Pipeline 확정 (2026-07-05)

### 4단계 누적 필터링

| Stage | 필터 기준 | 제거 수 | 남은 pts |
|---|---|---|---|
| 0 Raw | 없음 | — | 7,182 |
| 1 Z-bound | 카메라 extent × 1.0 밖 | 11 | 7,171 |
| 2 + obs≥3 | obs≤2 저confidence 제거 | 67 | 7,104 |
| 3 + kNN isolation | kNN5_dist > 3× median(=0.433m) | 612 | **6,492** |

**Stage 3이 최종 앵커 후보** (6,492 pts). kNN isolation은 threshold=0.433m, median kNN=0.144m 기준.

구현 스크립트:
```
scripts/diagnostic/filtering_stages_plateau.py
```

단계별 PDF 결과 (각 stage × 2개: zlayer + plateau):
```
results/diagnostic/filtering_stages_20260705_021252/   (8 PDFs)
```

---

## Plateau 설계 후보 (3DGS loss 연결 전 확정 필요)

### Candidate A — 구형 (Spherical v1)

```
tau_j = clip(0.6 × h_j,  0.05m, 0.60m)
h_j   = 5-NN 거리 (3D)
```

**특성:**
- 방향 무관, 구현 단순
- layer 4 (eye level) XY coverage: **11.9%**
- 잠재력: 전 방향 동일 인력

**potential 함수 (3DGS loss 후보):**
```python
D_j = ||x - p_j|| / tau_j
Phi(x) = min_j rho(D_j)

rho(r) = 0              if r <= 1       # plateau 내부: gradient 0
rho(r) = (r-1)^2        if r > 1        # 외부: quadratic hinge
```

### Candidate B — 타원체 (Ellipsoidal v2)

```
tau_n_j = clip(0.4 × h_j,  0.03m, 0.30m)   # normal 방향 (tight)
tau_t_j = clip(0.9 × h_j,  0.03m, 0.60m)   # tangent 방향 (loose)
u_n     = kNN-5 PCA 최소 고유벡터 (표면 법선)
```

**특성:**
- 표면 법선 추정 필요 (kNN PCA, k=5)
- 벽면 앵커: depth 방향 tight, 벽면 방향 loose
- 바닥/천장 앵커: Z 방향 tight, XY 방향 loose
- layer 4 XY coverage: **14.0%** (+2.1% vs 구형)
- planarity median: 0.186 (k=5 로는 법선 노이즈 많음)

**potential 함수:**
```python
D_aniso_j(x) = sqrt(
    ((x-p_j)·u_t1 / tau_t_j)^2 +
    ((x-p_j)·u_t2 / tau_t_j)^2 +
    ((x-p_j)·u_n  / tau_n_j)^2
)
Phi(x) = min_j rho(D_aniso_j(x))
```

구현 스크립트:
```
scripts/diagnostic/plateau_ellipsoid_v2.py
```

결과 PDF:
```
results/diagnostic/plateau_ellipsoid_v2_20260705_023632/ellipsoid_plateau.pdf
```

### Layer별 Coverage 비교 (Stage 3 기준)

| Layer | Z 범위 | 앵커 수 | Sphere XY% | Ellipsoid XY% | Δ |
|---|---|---|---|---|---|
| 2 | [-2.30,-1.54) | 134 | 2.1% | 2.5% | +0.4% |
| 3 | [-1.54,-0.78) | 1,540 | 9.7% | 11.9% | +2.2% |
| 4 | [-0.78,-0.02) | 1,896 | 11.9% | 14.0% | +2.1% |
| 5 | [-0.02,+0.74) | 1,334 | 7.8% | 8.9% | +1.1% |
| 6 | [+0.74,+1.50) | 1,316 | 10.6% | 11.9% | +1.4% |
| 7 | [+1.50,+2.26) | 263 | 5.4% | 6.5% | +1.2% |
| **8** | **[+2.26,+3.02)** | **9** | **0%** | **0%** | **—** |

> **핵심**: Layer 8 (Pop 2 floater 위험 구간)은 양쪽 모두 coverage 0%. 
> 구형/타원체 모두 Pop 2 구간에서는 앵커가 사실상 없어 plateau가 작동하지 않음.
> **→ 반드시 hard Z-clip 또는 별도 penalty와 병행해야 함.**

---

## 3DGS Loss 연결 설계 (미구현)

### 구현 위치

```
repos/main/3dgs-custom/train.py
repos/main/3dgs-custom/scene/gaussian_model.py
```

### loss 수식

```python
# Gaussian center position: gaussians.get_xyz  → (N, 3) tensor
# Anchor points: torch.tensor(anchor_pts)       → (M, 3)

def plateau_loss(xyz_gaussians, anchor_pts, tau_j):
    # xyz_gaussians: (N, 3)
    # anchor_pts:    (M, 3)
    # tau_j:         (M,)
    
    # pairwise distance (N×M) — 메모리 이슈 시 chunk 처리
    D = torch.cdist(xyz_gaussians, anchor_pts)           # (N, M)
    D_norm = D / tau_j.unsqueeze(0)                      # (N, M), normalize by tau
    D_min, _ = D_norm.min(dim=1)                         # (N,) nearest anchor's norm dist
    
    hinge = torch.clamp(D_min - 1.0, min=0.0)           # 0 inside plateau, >0 outside
    return (hinge ** 2).mean()                           # quadratic hinge

# train.py에 추가:
lambda_plateau = 0.01   # weight (photometric loss 대비 작게 시작)
loss_plateau = plateau_loss(gaussians.get_xyz, anchor_pts_tensor, tau_tensor)
loss = loss_photo + lambda_plateau * loss_plateau
```

**타원체(v2) 버전은 D_norm 계산만 교체:**
```python
delta = xyz_gaussians.unsqueeze(1) - anchor_pts.unsqueeze(0)  # (N, M, 3)
# frame_t: (M, 3, 3), tau_n: (M,), tau_t: (M,)
c = torch.einsum('mjk,nmj->nmk', frame_t, delta)              # (N, M, 3) local coords
D_aniso = torch.sqrt(
    (c[...,0]/tau_t)**2 + (c[...,1]/tau_t)**2 + (c[...,2]/tau_n)**2
)   # (N, M)
D_min, _ = D_aniso.min(dim=1)
```

### 실험 계획

| 실험명 | Candidate | lambda | Z-clip 병행 | 비교 기준 |
|---|---|---|---|---|
| exp15_spher_plateau | Candidate A (구형) | 0.01 | yes (Z>+2m pruning) | exp13 (PSNR 32.855) |
| exp16_ellip_plateau | Candidate B (타원체) | 0.01 | yes | exp13 |
| exp17_ellip_lambda | Candidate B | 0.005 | yes | exp16 |

**평가 지표:**
- PSNR @ 30k (target: ≥ exp08 = 33.012)
- Pop 2 floater 수: Z > +2m Gaussian 수 @ 30k
- low_opacity_ratio, large_scale_ratio

### Pop 2 구간 hard Z-clip 구현 (필수 병행)

```python
# train.py densification 후 주기적으로:
def prune_pop2_floaters(gaussians, z_threshold=2.0, start_iter=5000, interval=1000):
    if iteration > start_iter and iteration % interval == 0:
        z = gaussians.get_xyz[:, 2]
        mask_keep = z < z_threshold    # Z > 2m Gaussian 제거
        gaussians.prune_points(~mask_keep)

---

## 3D-Uniform Mono-Depth Anchor Completion & Pinhole 2D Quadratic Fitting (2026-07-05)

기존 Layer 1, 2, 7, 8 구간의 SLAM 포인트 부족으로 인한 0% 커버리지 공백과 단안 깊이(Monocular Depth) 고유의 3차원 절대 스케일/원근 왜곡 한계를 극복하기 위해 설계된 **최종 기하학적 보완 알고리즘**입니다.

이 알고리즘은 단안 깊이의 로컬 상대 구조를 정밀 캘리브레이션하여, 3D 공간 상에 중복 없이 균등하고 효율적으로 스파스 가상 앵커를 추가 배치합니다.

### 1. Pinhole 2D Quadratic Polynomial Fitting (단안 깊이 공간 정렬)

단안 깊이 모델($D_i^{mono}$)의 핀홀 카메라 원근 및 경사면 왜곡(perspective tilt drift & radial corner warp)을 각 키프레임 $i$ 단위로 개별 정정합니다.

픽셀 좌표를 이미지 중심 $(u_c, v_c)$와 크기 $(w, h)$ 기준 $[-1, 1]$로 규격화합니다:
$$\tilde{u} = \frac{u - u_c}{w/2}, \quad \tilde{v} = \frac{v - v_c}{h/2}$$

스케일 $s(\tilde{u}, \tilde{v})$와 쉬프트 $t(\tilde{u}, \tilde{v})$ 곡면을 2차 다항식으로 최적화합니다:
$$s(\tilde{u}, \tilde{v}) = s_0 + s_1 \tilde{u} + s_2 \tilde{v} + s_3 \tilde{u}^2 + s_4 \tilde{v}^2 + s_5 \tilde{u}\tilde{v}$$
$$t(\tilde{u}, \tilde{v}) = t_0 + t_1 \tilde{u} + t_2 \tilde{v} + t_3 \tilde{u}^2 + t_4 \tilde{v}^2 + t_5 \tilde{u}\tilde{v}$$

* **피팅 방식**: 고신뢰성 SLAM 점($P_{conf}$, observations $\ge 10$)들의 3D 실제 깊이와 단안 깊이 예측값을 대응시켜 RANSAC 또는 Huber Regressor 선형 최소자승법(Linear Least Squares)으로 매 iteration 혹은 주기적으로 피팅하여 계수 $x = [s_0..s_5, t_0..t_5]^T$를 도출합니다.
* **장점**: 왜곡이 없는 핀홀 환경에서 원근 Skew 및 이미지 네 귀퉁이(Corners) 왜곡을 수학적으로 완전히 정정하며, 외곽으로 갈수록 함수가 급격히 튀지 않고 스무스하게 보외(extrapolation)됩니다.

### 2. Object-Aware/Segmented Alignment (깊이 불연속성 보존)

배경과 기하학적으로 완전히 격리되어 돌출된 전경 물체(Foreground object)가 존재할 경우, 단일 스무스 다항식에 의한 경계면 깊이 뭉개짐(depth discontinuity smoothing)을 방지합니다.

* **동작**: 단안 깊이 맵의 에지 검출(Sobel/Canny) 또는 K-Means 히스토그램 군집화를 통해 이미지를 다중 뎁스 레이어($M_m$)로 분할합니다.
* **피팅**: 각 독립 레이어 마스크 내에 속한 SLAM 점들로만 로컬 스케일-쉬프트 파라미터($s_m, t_m$)를 따로 피팅하여 경계면의 날카로운 수직 깊이 절벽(depth step)을 보존합니다. SLAM 점이 부족한 텍스처리스 전경 물체는 인접한 배경 파라미터를 상속받되 상대적 뎁스 단차가 3D로 스케일링되어 유지됩니다.

### 3. 3D-Uniform Spatial Voxel Seeding Algorithm (공간 균등 복셀 시딩)

정렬이 완료된 키프레임 뎁스 맵들을 바탕으로 3D 공간 상에 중복 없이 균일하게 스파스 가상 앵커 포인트를 스폰합니다.

* **복셀 그리드 활용**: 3D 공간을 타겟 앵커 해상도 $V_s$ (예: 30cm) 간격의 3D Occupancy Grid ($G_{occ}$)로 조각내고 고신뢰성 SLAM 점들로 초기 점유 상태를 채웁니다.
* **Strided Scanning**: 각 키프레임의 뎁스 맵을 Stride $S=16$픽셀 단위로 스파스하게 스캔(250배 이상 연산 속도 단축)하고, 픽셀 좌표를 3D 월드 좌표 $x_{world}$로 역투영합니다.
* **Early Exit**: $x_{world}$가 위치한 복셀이 이미 점유되어 있으면(`key in G_occ`) 연산을 조기 스킵하여 프레임이 축적될 때 발생하는 중복 생성을 원천 차단합니다.
* **Multi-view Consistency**: 단발성 노이즈 뎁스를 배제하기 위해 후보 그리드($G_{cand}$)의 히트 카운터가 $N_{min}$(예: 2회 이상 서로 다른 뷰)을 만족한 3D 복셀에만 평균 좌표값으로 최종 가상 앵커를 심습니다.

### 4. 확장 설정 및 기대값
* **Total Anchors**: $P_{total} = P_{sparse} \cup P_{virtual}$은 씬 전체 표면을 약 30cm 간격으로 고르게 정렬된 3D-Uniform 스파스 분포를 가집니다.
* **알파 조정**: 스파스한 분포이므로 **$\alpha = 0.8 \sim 1.0$**으로 넓게 주어 개별 앵커 반경 $\tau_j = \alpha \times h_j \approx V_s$가 물리적으로 중첩되게 만듭니다. 
* **효과**: 연산 속도 부담을 완전히 덜어내는 동시에, 구멍 없이 매끄럽게 씬 전체 표면(벽, 천장, 바닥)을 감싸는 3D Plateau 껍질을 형성하여 Pop 2 floater를 공간적으로 철저히 격리 차단합니다.
```

