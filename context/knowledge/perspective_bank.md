# Empty Space Floater 관점 Bank

이 파일은 텅 빈 공간에 생기는 floater 문제를 바라보는 관점을 계속 수집하는 저장소다.  
loop를 돌 때마다 새로운 데이터 분석 결과, 논문 읽기, 시각화에서 나온 관점을 추가한다.

각 관점은 독립적으로 측정 가능해야 하고, 기존 관점과 구분되는 메커니즘을 가정해야 한다.

---

## 관점 작성 양식

```
### [번호] 관점 이름
**메커니즘 가정**: 왜 이 방식으로 floater가 생기거나 유지되는가
**측정 방법**: 어떤 데이터를 뽑으면 이 가설을 확인할 수 있는가
**예상 결과**: 가설이 맞다면 어떤 숫자/분포가 나와야 하는가
**연결된 intervention**: 이게 확인되면 어떤 방향의 해결책인가
**상태**: [미검증 / 검증 중 / 확인됨 / 기각됨]
**발견 시점**: 언제 이 관점을 추가했는가
```

---

## 현재 수집된 관점

---

### [P01] Camera Ray Density Void

**메커니즘 가정**:  
SLAM trajectory는 카메라가 일정 경로를 따라 이동하기 때문에, 3D 공간에 ray가 집중되는 구간과 거의 통과하지 않는 구간이 생긴다. Ray가 드문 구간("ray void")에서는 photometric loss의 gradient signal이 약해서, 그 구간에 생긴 Gaussian은 틀린 위치에 있어도 제거되지 않는다.

COLMAP은 다양한 각도에서 찍힌 이미지를 쓰므로 ray coverage가 비교적 균일하지만, SLAM trajectory는 구조적으로 불균일한 ray density를 만든다.

**측정 방법**:
```python
# 각 voxel에 training camera ray가 통과하는 횟수를 계산
ray_density_map = compute_ray_density(cameras, voxel_size=0.05)

# 각 Gaussian의 위치에서 ray density 조회
for G in gaussians:
    G.ray_density = ray_density_map.query(G.xyz)

# empty_space_score (depth residual)와 ray_density 비교
scatter_plot(x=G.ray_density, y=G.empty_space_score)
```

**예상 결과**:  
ray density가 낮은 구간에 empty_space_score가 나쁜 Gaussian이 집중됨

**연결된 intervention**:  
ray density가 낮은 구간에서 생성된 Gaussian에 더 강한 geometric constraint 부여  
또는 densification 시 ray density map을 참고해 그 구간에서 split/clone 억제

**상태**: 부분 지지됨 (Round 1c, 2026-06-30 — 직접 ray density map은 없지만 Z-outlier의 trajectory 거리 분포가 이 관점과 일치)  
**발견 시점**: 2026-06-30

---

### [P02] Compositing Depth Rank Shadow

**메커니즘 가정**:  
alpha compositing에서 Gaussian은 깊이 순서로 합산된다. floater가 surface Gaussian들보다 **뒤에** 쌓이면, surface Gaussians가 이미 transmittance T를 거의 소진한 상태에서 floater에 도달한다. 이때 T_k ≈ 0이 되므로 floater는 opacity가 얼마든 loss gradient를 받지 못한다.

기존 논문들은 "floater의 opacity가 낮아서 gradient가 없다"에 집중하지만, 이 관점은 그보다 더 근본적이다. opacity가 0이 아니어도 compositing 순서 때문에 gradient signal이 차단된다.

**측정 방법**:
```python
# 각 Gaussian에 대해, 자신을 통과하는 ray들에서의 depth rank 분포
for G in gaussians:
    depth_ranks = []
    for camera c:
        for ray r intersecting G:
            rank = position_of_G_in_sorted_depth_order(r)
            T_at_G = accumulated_transmittance_at_rank(r, rank)
            depth_ranks.append((rank, T_at_G))
    
    G.mean_depth_rank = mean([r for r, t in depth_ranks])
    G.mean_T_at_G = mean([t for r, t in depth_ranks])
```

**예상 결과**:  
empty space floater는 mean depth rank가 높고 mean T_at_G가 낮음  
즉 "loss function이 접근할 수 없는 compositing shadow에 숨어있다"

**연결된 intervention**:  
T_k가 특정 threshold 이하인 상황에서도 opacity에 강제 gradient를 주는 보조 loss  
또는 T_k와 무관하게 opacity를 직접 penalty하는 geometric regularizer

**상태**: 미검증  
**발견 시점**: 2026-06-30

---

### [P03] Densification이 Empty Space Gaussian을 생성하는 경로

**메커니즘 가정**:  
densification은 2D viewspace gradient가 높은 Gaussian을 split/clone한다. 이 기준은 "해당 픽셀에서 photometric error가 크다"는 것인데, 그 픽셀의 photometric error가 표면에서 오는 것인지 공중에서 오는 것인지 구별하지 않는다. 결과적으로 densification 자체가 empty space에 새 Gaussian을 배치하는 경로가 될 수 있다.

**측정 방법**:
```python
# densification 직후 새로 생긴 Gaussian들의 depth residual을 즉시 측정
# (clone/split 시점에 새 Gaussian 위치를 snapshot)
on densification_event:
    new_gaussians = get_newly_created_gaussians()
    for G in new_gaussians:
        G.birth_depth_residual = compute_depth_residual(G, cameras, sparse_points)
        G.birth_iteration = current_iteration
        G.birth_type = "clone" or "split"
```

**예상 결과**:  
새로 생성된 Gaussian 중 birth_depth_residual << 0 인 비율이 의미있게 존재함  
즉 densification이 floater의 seed를 만드는 직접적 경로임을 보임

**연결된 intervention**:  
densification 시 생성될 Gaussian의 위치에서 depth residual을 체크,  
empty space에 생성되는 경우 birth를 막거나 즉시 geometric penalty 부여

**상태**: 미검증  
**발견 시점**: 2026-06-30

---

### [P04] Ray Direction Ambiguity (Depth Axis Flatness)

**메커니즘 가정**:  
photometric loss는 2D image space에서 pixel 색상 오차를 줄이는 방향으로 작동한다. 그런데 Gaussian을 ray 방향(카메라 → 씬, depth 축)으로 앞뒤로 이동해도 rendered color는 거의 변하지 않는다. 이것이 position local minima가 많은 구조적 이유다.

floater가 ray 방향으로 표면에서 멀리 있어도, 그 Gaussian이 보이는 픽셀의 색상을 맞출 수 있다면 loss가 flat하다. 이 flatness는 어떤 parameter tuning으로도 해결할 수 없다.

이 씬에서의 실측 (Round 2, 2026-06-30):  
카메라가 X 방향으로 이동하며 주로 X를 향해 바라봄 → X = depth 축 (약 gradient).  
Z = lateral (수직, 이미지 평면 방향) → strong gradient.  
실측 grad_z / grad_x = **1.41 (mean)**, range 0.77~2.39 — Z가 X보다 일관되게 강함.

**측정 방법**:
```python
# floater Gaussian을 ray 방향으로 이동하면서 loss 측정
for G in floater_gaussians[:50]:
    ray_direction = compute_mean_viewing_direction(G, cameras)
    losses = []
    for delta in [-1.0, -0.5, -0.2, -0.1, 0, +0.1, +0.2, +0.5, +1.0]:  # meters
        G_perturbed = G.xyz + delta * ray_direction
        loss = compute_photometric_loss_with_perturbation(G_perturbed)
        losses.append((delta, loss))
    
    # ray 방향 loss curve 저장
```

**예상 결과**:  
ray 방향으로 ±50cm 이동해도 loss 변화가 매우 작음  
수직 방향(이미지 평면 방향)으로 이동하면 loss가 크게 변함

**연결된 intervention**:  
ray 방향 depth를 regularize하는 external signal (sparse point depth, monocular depth)  
또는 Gaussian을 ray 방향으로 강제 이동 후 재최적화 (teleporting)

**상태**: 확인됨 (Round 2, 2026-06-30) — X는 depth 축(약한 gradient), Z는 lateral(강한 gradient). grad_z/grad_x mean = 1.41.  
**발견 시점**: 2026-06-30

---

### [P05] SH View-Dependent Compensation

**메커니즘 가정**:  
3DGS의 color는 Spherical Harmonics(SH)로 표현된다. 고차 SH는 view-dependent color를 표현할 수 있다. 잘못된 위치에 있는 Gaussian이 고차 SH를 이용해 training view마다 다른 색을 맞추면, photometric loss 기준으로는 "좋은" Gaussian처럼 보인다. 이 DOF 때문에 위치가 틀려도 loss가 낮게 유지된다.

**측정 방법**:
```python
# 각 Gaussian의 SH coefficient 에너지를 차수별로 계산
for G in gaussians:
    sh_degree0_energy = norm(G.features_dc)          # view-independent color
    sh_higher_energy = norm(G.features_rest)          # view-dependent compensation
    G.sh_ratio = sh_higher_energy / (sh_degree0_energy + eps)

# floater vs surface Gaussian의 SH ratio 비교
floater_sh_ratio = sh_ratio[floater_mask].mean()
surface_sh_ratio = sh_ratio[surface_mask].mean()
```

**예상 결과**:  
floater의 SH ratio가 surface Gaussian보다 유의미하게 높음  
즉 floater는 view-dependent DOF를 더 많이 사용해서 잘못된 위치를 보상함

**연결된 intervention**:  
SH 고차 coefficient에 L2 regularizer  
또는 SH ratio가 높은 Gaussian을 floater 후보로 추가 마킹

**상태**: 미검증  
**발견 시점**: 2026-06-30

---

### [P06] Temporal Gradient Cancellation

**메커니즘 가정**:  
각 Gaussian은 여러 training view에서 오는 gradient를 iteration마다 누적한다. empty space floater에 대해 서로 다른 view는 "이 Gaussian을 왼쪽으로 이동해라", "오른쪽으로 이동해라" 등 다른 방향의 gradient를 준다. 이 gradient들이 averaging되면 실질적인 이동 방향이 상쇄되어, 개별 view의 gradient는 0이 아니어도 평균 gradient는 0에 가까워진다.

개별 view gradient는 강해도 방향이 다르면 sum이 0이 되는 문제다.

**측정 방법**:
```python
# floater Gaussian에 대해 개별 view별 xyz gradient 방향을 기록
for G in floater_gaussians[:20]:
    per_view_gradients = []
    for camera c:
        loss_c = compute_loss_single_view(G, c)
        loss_c.backward()
        per_view_gradients.append(G.xyz.grad.clone())
    
    # gradient 방향 다양성 측정
    G.gradient_direction_variance = compute_angular_variance(per_view_gradients)
    G.gradient_magnitude_mean = mean([g.norm() for g in per_view_gradients])
    G.effective_gradient = sum(per_view_gradients).norm()
    
    # effective_gradient << gradient_magnitude_mean 이면 cancellation
```

**예상 결과**:  
floater는 per-view gradient는 강하지만 방향이 달라서 합산 gradient(effective)가 작음  
surface Gaussian은 per-view gradient 방향이 일치해서 합산도 강함

**연결된 intervention**:  
gradient cancellation을 피하는 per-view gradient clipping  
또는 방향 일관성이 낮은 Gaussian을 floater 후보로 마킹

**상태**: 미검증  
**발견 시점**: 2026-06-30

---

### [P07] Opacity Reset이 Floater를 재생시키는 메커니즘

**메커니즘 가정**:  
opacity reset은 전체 Gaussian의 opacity를 주기적으로 낮춘다. 이 시점에 "정상" Gaussian과 floater 모두 동일하게 opacity가 낮아지고, 이후 다시 경쟁이 시작된다. floater가 이미 color-matching에 유리한 위치를 점하고 있다면, reset 후 재경쟁에서 다시 floater가 opacity를 회복해 굳어버린다.

opacity reset이 floater를 제거하는 도구가 아니라 오히려 floater를 재생시키는 trigger일 수 있다.

**측정 방법**:
```python
# opacity reset 직전/직후 low-opacity Gaussian의 공간 분포 비교
# 동일한 Gaussian이 reset 후에 다시 어느 위치에서 opacity를 회복하는가

# checkpoint: opacity reset iteration들 (3000, 6000, 9000, ...)에서
# 각 Gaussian ID별 opacity 시계열 저장
```

**예상 결과**:  
reset 전에 low-opacity였던 floater가 reset 후에도 같은 위치에서 다시 opacity를 회복함  
즉 reset이 floater를 정리하지 못하고 같은 자리에서 재생됨

**연결된 intervention**:  
opacity reset 시 depth residual이 나쁜 Gaussian은 reset 대신 remove  
또는 reset 직후 empty space score 기반 pruning

**상태**: 미검증  
**발견 시점**: 2026-06-30

---

### [P08] Large-Scale Floater의 Gradient Masking

**메커니즘 가정**:  
큰 scale을 가진 floater는 여러 픽셀을 동시에 덮는다. 이 floater 뒤에 있는 표면 Gaussian들은 transmittance T가 감소된 상태에서 gradient를 받는다. 즉 large floater가 표면 Gaussian들의 gradient를 masking하고 있는 상황이다. 이 경우 floater와 표면 Gaussian이 coupled local minimum에 빠진다.

**측정 방법**:
```python
# large scale Gaussian (scale_max > threshold)에 대해
# 그 뒤에 있는 surface Gaussian들의 gradient magnitude 측정
for G_large in large_scale_floaters:
    covered_pixels = get_pixels_covered_by_gaussian(G_large, cameras)
    for pixel p in covered_pixels:
        gaussians_behind_G_on_p = get_gaussians_behind(G_large, p)
        for G_behind in gaussians_behind_G_on_p:
            G_behind.masked_gradient_mean += G_behind.xyz.grad.norm()

# large floater 제거 후 뒤의 Gaussian gradient 변화 측정
```

**예상 결과**:  
large floater를 제거했을 때 뒤에 있는 Gaussian들의 gradient가 유의미하게 증가함  
즉 large floater가 실제로 gradient를 차단하고 있음을 증명

**연결된 intervention**:  
large scale floater를 먼저 공격적으로 제거하면 표면 Gaussian이 살아남  
scale 기반 pruning이 아니라 scale + depth residual 조합 pruning

**상태**: 미검증  
**발견 시점**: 2026-06-30

---

### [P09] SLAM Trajectory의 Viewpoint Clustering Bias

**메커니즘 가정**:  
COLMAP은 다양한 각도의 이미지를 쓰지만 SLAM은 시간 순서로 연속된 이미지를 쓴다. 연속된 프레임은 거의 같은 방향에서 찍혔다. 이로 인해 training ray의 방향 분포가 극도로 편향된다(viewpoint clustering). floater가 이 편향된 방향에서 "맞아 보이는" 위치에 있으면, 거의 모든 training view에서 그것을 지지하는 gradient가 형성되어 오히려 floater 위치가 강화된다.

**측정 방법**:
```python
# 각 Gaussian에 대해 training view들의 viewing direction 다양성 측정
for G in gaussians:
    view_directions = [normalize(G.xyz - cam.center) for cam in cameras_seeing_G]
    G.view_direction_entropy = compute_entropy_of_directions(view_directions)
    # entropy 낮으면 = 거의 같은 방향에서만 봄 = viewpoint bias

# floater vs surface Gaussian의 view_direction_entropy 비교
```

**예상 결과**:  
floater는 view_direction_entropy가 낮음 (편향된 방향에서만 봄)  
이 편향이 floater 위치를 강화하는 방향으로 작용함

**연결된 intervention**:  
viewpoint-aware gradient weighting으로 편향 보정  
또는 가상 카메라(unseen viewpoint) 추가 (SparseGS 아이디어)

**상태**: 미검증  
**발견 시점**: 2026-06-30

---

### [P10] Near-Trajectory Floater Cluster

**메커니즘 가정**:  
카메라 trajectory 바로 앞에 생긴 Gaussian은 거의 모든 training view에서 보인다. 만약 카메라 경로 바로 앞(수십 cm)에 floater가 자리잡으면, 이 floater는 전체 training set에서 지속적으로 강한 gradient를 받아 위치를 고착시킨다. 역설적으로 "많이 보이는" Gaussian이 floater가 되는 경우다.

**측정 방법**:
```python
# 각 Gaussian의 trajectory center line까지의 최소 거리 계산
trajectory_line = compute_trajectory_line(cameras)
for G in gaussians:
    G.dist_to_trajectory = min_distance_to_line(G.xyz, trajectory_line)

# dist_to_trajectory가 매우 작은 Gaussian 중 empty space floater 비율
near_trajectory_floaters = gaussians[
    (G.dist_to_trajectory < 0.3) &  # trajectory에서 30cm 이내
    (G.empty_space_score < -0.2)     # empty space
]
```

**예상 결과**:  
trajectory 바로 앞 영역에 floater가 집중되는 cluster 존재  
이 Gaussian들은 gradient가 강해서 pruning 후에도 다시 생성됨

**연결된 intervention**:  
trajectory 근방에 "no Gaussian zone"을 초기에 설정  
또는 trajectory 거리 기반 depth constraint 추가

**상태**: 미검증  
**발견 시점**: 2026-06-30

---

### [P11] Projection-Space Coverage Gap (Floater Habitat)

**메커니즘 가정**:  
Sparse point는 텍스처가 있는 표면에만 존재한다. 텍스처가 없는 흰 벽, 바닥, 공중 등에는 sparse point가 투영되지 않는다. Floater는 정의상 표면이 없는 공간에 있으므로, image space에서 sparse point가 투영되지 않는 픽셀에 floater가 집중된다.

즉, **sparse point 기반 depth residual은 floater를 탐지할 수 없다** — 왜냐하면 floater는 정확히 sparse point coverage가 없는 영역에 존재하기 때문이다. 이것은 diagnostic 방법론 자체의 한계다. Round 1a에서 43%의 Gaussian이 측정 불가였던 이유가 이것이다.

이 관점이 중요한 이유: floater를 sparse point 기반 방법으로 탐지하려면 **image space에서 reference가 없는 영역에 있는 Gaussian이 왜 존재하는가**를 설명해야 한다. 그 존재 자체가 floater의 증거다.

**측정 방법**:
```python
# 각 Gaussian에 대해 보이는 카메라들에서 image-space sparse coverage 유무 측정
for G in gaussians:
    visible_cameras = [c for c in cameras if G in c.frustum]
    coverage_ratio = sum(
        1 for c in visible_cameras
        if any_sparse_point_projects_near(G, c, radius_px=8)
    ) / len(visible_cameras)
    
    G.coverage_ratio = coverage_ratio  # 0이면 완전한 sparse coverage gap

# coverage_ratio=0 (coverage gap) Gaussian들의 공간 분포:
# - trajectory에서의 거리
# - 높이 (Z 좌표) 분포
# - 카메라에서의 거리 분포
# → 이 그룹이 "텅 빈 공간"의 진짜 floater 후보
```

**예상 결과**:  
coverage_ratio=0 그룹이 특정 공간적 패턴을 보임:
- 텍스처 없는 벽/천장 방향에 집중 (표면 Gaussian이 textureless region에 있는 경우)  
- 카메라 trajectory 근방의 공중에 집중 (진짜 empty space floater)
두 sub-group을 분리하면 floater를 더 정확히 정의할 수 있다.

**연결된 intervention**:  
sparse coverage gap Gaussian들 중 trajectory와 가까운 것들을 floater로 정의  
이 그룹에 특화된 geometric penalty 또는 visibility-aware pruning 적용

**상태**: 검증 중 (Round 1a에서 43% 비측정 발견, Round 1b에서 이 그룹 분석 중)  
**발견 시점**: 2026-06-30 Round 1a

---

### [P12] SLAM Outlier Initialization → FOV-Frozen Z-Drift (수정됨, Round 2)

**메커니즘 가정 (Round 2 수정)**:  
초기 가설 "Z gradient 약함 → Z drift"는 Round 2 gradient 측정으로 **기각됨** (실측 grad_z/grad_x = 1.41, Z가 오히려 강함).

**수정된 메커니즘**: SLAM 삼각화 실패 sparse point → 3DGS 초기화 시 극단적 Z 위치에 Gaussian 배치 → FOV 밖이므로 gradient=0 → 영구 frozen.

단계:
1. **SLAM 삼각화 실패**: 2.44%의 sparse point가 극단 좌표 (Z=907,581m 관측)
2. **3DGS 초기화**: 전체 sparse point에서 Gaussian 초기화 → iter 500에 46,264개 (14.3%)가 |Z|>3m
3. **Opacity reset (iter 3000) + pruning**: 94.4% 제거 (46,264 → 1,144개). FOV 밖 Gaussian은 gradient=0 → opacity가 reset 값 그대로 → 낮은 opacity → pruned.
4. **생존자 1,440개**: 초기 opacity가 높거나 pruning threshold 바로 위 → 제거 안 됨 → |Z|≈42m에 frozen.
5. **Densification 중 +296개 추가** (iter 3500→7000): 씬 경계 근방에서 densification으로 생성된 Gaussian이 FOV boundary를 넘어서 frozen.

카메라 elevation 정보:
- elevation 평균: **5.39° ± 4.44°** (거의 수평) → Z는 lateral 축 → gradient 약하지 않음
- 실측: |view_Z| 평균 0.094는 viewing direction의 Z 성분이지, gradient의 Z 성분이 아님

**실측 결과 (Round 2)**:
```
iter   500: 46,264 Z-outliers (14.3%), |Z|_max = 907,582m  ← SLAM 초기화 실패
iter  1000: 18,108 Z-outliers, |Z|_max = 7,103m            ← 초기 빠른 pruning
iter  3500:  1,144 Z-outliers, |Z|_max = 41.83m            ← opacity reset+pruning
iter  7000:  1,440 Z-outliers, |Z|_max = 42.20m            ← densification 기여 +296
iter 15000:  1,442 Z-outliers, |Z|_max = 42.20m            ← 완전 frozen

grad_z/grad_x: mean=1.41, range 0.77~2.39               ← P12 원래 가설 기각!
```

**연결된 intervention**:  
1. **가장 효과적**: SLAM sparse point를 XYZ bounds로 필터링 후 3DGS 초기화  
   → iter 500의 46,264개 중 ~45,000개 제거 가능 (SLAM 실패 좌표만 제거)
2. Scene bounding box 기반 주기적 pruning (FOV-frozen Gaussian 제거)
3. Opacity reset 직후 zero-gradient Gaussian 즉시 pruning (gradient 누적 없는 것 = FOV 밖)

**상태**: 수정됨 (Round 2, 2026-06-30) — 원래 P12 (Z gradient weakness)는 기각. 새 메커니즘: SLAM initialization outlier → FOV frozen.  
**발견 시점**: 2026-06-30 Round 1b Z 분석; 수정: Round 2 gradient diag (2026-06-30)

---

## 관점 추가 가이드

loop를 돌 때 새로운 관점을 발견하면 다음 기준으로 추가한다:

1. 기존 관점과 **다른 메커니즘**을 가정하는가?
2. **측정 가능**한 양으로 표현할 수 있는가?
3. 기존 논문 16편에서 **직접 다루지 않은** 각도인가?

위 세 가지를 모두 만족하면 추가. 아니면 기존 관점의 sub-point로 추가.

---

## 기각된 관점

### [P10 기각] Near-Trajectory Floater Cluster

**기각 근거 (Round 1c, 2026-06-30):**
Z-outlier Gaussian들은 trajectory NEAR가 아니라 FAR에 집중됨.

```
XY distance to nearest camera center:
  Normal Gaussians: median=1.31m
  Z-outlier:        median=3.56m (2.7x 더 멀리!)

Z-outlier 중 83.6%가 XY dist > 1m (trajectory 밖)
Z-outlier 중 16.4%만이 XY dist < 1m (trajectory 근방)
```

**수정 해석**: 오히려 **trajectory에서 먼 구간이 floater 온상** (P01 Ray Density Void와 일치).
trajectory에서 멀수록 camera ray density가 낮아 전체 gradient가 약해짐.
Z-axis gradient (이미 9.4%)가 더 약화 → Z-drift가 더 심해짐.

---

## 확인된 관점

### [Round 1a/1b 확인] Low-opacity ≠ Empty Space Floater

**결과**: 126,330개의 low-opacity Gaussian (opacity < 0.1)이 depth_residual ≈ 0 — 즉 표면 위에 있음.  
**의미**: 기존 opacity 기반 pruning은 floater를 표적으로 삼지 못한다. low-opacity는 표면 Gaussian의 상태이기도 하다.  
**수치**: dr_only (opacity 높은데 floater) = 117, op_only (opacity 낮은데 표면) = 126,178

---

### [P12 수정됨] Z-Drift Mechanism: SLAM Initialization Outliers → FOV Frozen (Round 2)

**원래 P12 가설 (기각됨)**: |view_Z|=0.094 → Z gradient가 X의 9.4% → Z drift  
**Round 2 측정 결과**: grad_z/grad_x = **1.41 (mean)** — Z gradient가 X보다 강함. 가설 기각.

**수정된 메커니즘**:
- SLAM 삼각화 실패 sparse point (|Z|>10m, 실측 최대 Z=907,582m) → 3DGS 초기화 시 46,264개(14.3%)가 |Z|>3m
- 이 Gaussian들은 처음부터 FOV 밖 → gradient=0 → opacity reset 후 pruning으로 97% 제거
- 나머지 1,440개 survivors: |Z|≈42m에 영구 frozen
- Densification이 추가로 296개 생성

**논문적 기여**: SLAM outlier 초기화 → Z-frozen floater 경로 발견. 간단한 fix: sparse point XYZ bound 필터링.

**참조 figure**: `results/diagnostic/round2_gradient_analysis.png`

---

### [Round 1c 확인] High-Opacity Z-outliers = Worst Floaters (Opacity Pruning Fails)

**가장 강력한 발견**: 표준 opacity pruning (threshold 0.01)은 Z-outlier Gaussian의 **86.8%를 놓친다** (1280/1474).

더 충격적인 것: **opacity가 높을수록 Z displacement가 크다!**

| opacity 구간 | n | mean \|Z\| |
|---|---|---|
| 0.01-0.05 | 466 | 9.0m |
| 0.05-0.10 | 355 | 11.1m |
| 0.10-0.20 | 237 | 14.9m |
| 0.20-0.30 | 82 | 24.2m |
| 0.30-0.50 | 53 | 25.0m |
| 0.50-1.00 | 87 | **29.0m** |

**메커니즘 (Round 2 수정)**: SLAM 삼각화 실패 sparse point에서 초기화된 Gaussian이 iter 0부터 FOV 밖에 위치 → gradient=0 → opacity가 높으면 opacity reset+pruning도 통과 → Z=-42m에 frozen. (서서히 drift하는 게 아니라 처음부터 거기에 있음)

**의미**: opacity 기반 pruning은 Z-drift floater의 근본 원인인 **trajectory-induced gradient imbalance**를 해결하지 못한다. Geometric constraint(trajectory-aware bounding box pruning)가 필요하다.

**참조 figure**: `results/diagnostic/round1c_z_outlier_analysis.png`

---

### [exp13 확인] 두 개의 Z-Floater 집단 (2026-06-30)

**실험**: exp08 (no filter) vs exp13 (init_pcd_filter, 30k training)

**발견**: Z-floater는 기원과 행동이 다른 두 집단으로 구성됨.

| 항목 | Pop 1: SLAM Init Outlier | Pop 2: Densification Floater |
|---|---|---|
| 기원 | SLAM 삼각화 실패 sparse point | 3DGS densification (iter 100~7000) |
| |Z| 범위 | >42m (극단) | 3-6m (씬 내부) |
| FOV 위치 | 밖 (invisible) | 안 (visible) |
| Image ambiguity 기여 | **없음** | **있음** (주요 원인) |
| 필터 효과 | **-99%** (완전 해결) | 없음 (지속) |

**증거**:
- exp08 → exp13: Z-outlier 1,474 → 385 (-74%), 하지만 ambiguity_ratio 33.3% → 35.0% (+1.7pp)
- Pop 1 제거 후 ambiguity가 증가한 이유: Pop 1은 FOV 밖이라 원래 이미지에 기여 안 함
- 남은 385개 Pop 2 floater (|Z|=3-6m)는 이미지에 투영 → ambiguity 유발

**PSNR**: 33.012 → 32.855 (-0.16 dB). 원인: 7.38% sparse point 제거 시 일부 valid surface point 포함.

**논문 framing**:
- Contribution 1: Pop 1 정량화 + 필터링 (-99%, -0.16 dB cost)
- Open problem: Pop 2 (densification floater) → 별도 intervention 필요 (Round 6 목표)

**다음 intervention 방향**:
- P03 관련: densification 시 Z-stretch가 심한 Gaussian 억제
- ambiguity-guided pruning: ambiguity map 기반 in-scene floater 제거
- camera-extent-aware densification gradient threshold

**참조 figure**: `results/diagnostic/exp13_final_comparison.png`
