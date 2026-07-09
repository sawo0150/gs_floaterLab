# Floater 진단 Loop 계획

작성일: 2026-06-30  
목적: parameter search에서 벗어나 positional floater의 근본 원인을 데이터로 확정하고 논문 contribution으로 이어지는 루프 설계

관련 파일:
- **관점 Bank**: `context/knowledge/perspective_bank.md` — 발견한 관점 누적 저장소
- **실험 계획**: `context/archive/floater_experiment_plan.md`
- **실험 결과**: `context/archive/notion_experiment_summary_2026-06-16.md`

---

## 핵심 전제

지금까지 exp01~exp12는 hyperparameter를 바꿔가며 floater를 줄이려 했으나, 다음 구조적 문제를 건드리지 못했다.

```
floater가 텅 빈 공간에 존재하는데도 optimizer가 제거하지 못하는 이유는
gradient vanishing인가, loss landscape의 flatness인가, 
아니면 이 SLAM 기반 pipeline 특유의 원인인가?
```

이 질문에 답하지 않으면 어떤 parameter를 바꿔도 upper bound가 있다.  
아래 loop는 이 질문에 숫자로 답하는 것을 목표로 한다.

---

## Meta-Loop: Perspective Bank 관리

**모든 Round 안에 아래 sub-loop가 반복된다.**

데이터를 뽑을 때마다 다음 질문을 던진다:

```
1. 이 데이터를 보는 새로운 각도가 있는가?
   → "왜 이런 분포가 나왔는가?" 를 설명하는 메커니즘을 하나 더 가정해볼 것

2. 그 메커니즘은 기존 관점 bank에 없는 것인가?
   → floater_perspective_bank.md 의 기존 항목과 비교

3. 새로운 관점이면 즉시 bank에 추가한다
   → 측정 방법, 예상 결과, intervention 방향 포함

4. 기존 관점이 데이터로 지지되거나 기각됐으면 상태를 업데이트한다
   → "미검증" → "확인됨" or "기각됨" 으로 이동
```

관점 추가 기준 (3가지 모두 충족해야):
- 기존 관점과 **다른 메커니즘**을 가정하는가
- **측정 가능한 양**으로 표현할 수 있는가
- 기존 논문 16편에서 **직접 다루지 않은** 각도인가

관점이 쌓일수록 "논문에서 우리가 발견한 것"의 목록이 된다.

---

## Loop 구조

```
Round 1: 현상 정의     — 어떤 Gaussian이 empty space floater인가
Round 2: 시간 진단     — 언제 floater가 고착되는가
Round 3: 원인 구분     — gradient vanishing인가, loss landscape flatness인가
Round 4: SLAM 특이성  — 이 setup 특유의 원인이 있는가
Round 5: 개입 설계     — 진단 결과 기반 targeted intervention
```

각 round는 새로운 학습 실험 없이 최대한 기존 결과와 logging 추가만으로 진행한다.

**각 Round 완료 조건:**
1. 해당 round의 측정 데이터가 존재한다
2. 데이터를 보고 perspective bank를 검토했다
3. 새로운 관점이 있으면 bank에 추가했다
4. bank에서 이번 데이터로 상태가 바뀐 관점을 업데이트했다

---

## Round 1: 현상 정의 — "Empty Space Floater"의 정확한 측정

### 목표

기존 `low_opacity_ratio` 대신 **공간 위치 기반** floater 정의를 만든다.

opacity는 Gaussian의 속성이고, empty space floater는 위치의 문제이기 때문에 opacity만으로는 포착이 불완전하다.

### 핵심 측정: Depth Residual Score

```python
for each Gaussian G at world position μ:
    residuals = []
    for each training camera c:
        d_gauss = depth of μ projected through c      # Gaussian 깊이
        d_sparse = nearest sparse point depth at pixel  # 표면 참조 깊이
        if d_sparse exists:
            residuals.append(d_gauss - d_sparse)
    
    empty_space_score[G] = median(residuals)
    # << 0: 표면보다 앞에 있음 = empty space floater
    # ≈  0: 표면 근처 = 정상
    # >> 0: 표면 뒤에 있음 = occluded Gaussian
```

### Sparse Point의 한계 보완

OpenMAVIS sparse point는 noise가 수 cm 수준이고, floater displacement는 수십 cm ~ 1m이므로 탐지 용도로는 충분하다. 단, **sparse point gap 구간**에서는 reference 자체가 없다. 보완:

- ambiguity map에서 p95가 높은 픽셀 → floater 의심 구간으로 독립 마킹
- 두 신호를 AND로 결합: `depth_residual << 0` OR `ambiguity_high` = floater 후보

### 시각화 목표

- exp08 최종 checkpoint PLY에서 Gaussian property 추출
- 3D scatter: empty_space_score를 색상으로 표현
- Histogram: score 분포, opacity와 cross-plot
- 핵심 질문: **low-opacity Gaussian과 empty-space Gaussian은 얼마나 겹치는가?**

### Round 1 결과 (완료: 2026-06-30)

**Round 1a (3D 기반 depth residual):**
- 스크립트: `scripts/diagnostic/round1_depth_residual.py`
- 출력: `results/diagnostic/round1_overview.png`, `round1_summary.txt`
- **발견 1**: 3D nearest sparse point distance는 비변별적 (median 2.5cm). 626k sparse point가 너무 촘촘해서 모든 Gaussian이 3D에서 sparse point 근처임
- **발견 2 (확인됨)**: low-opacity ≠ empty space floater. 126,330개 low-opacity Gaussian이 depth_residual ≈ 0 (표면 위)
- **발견 3**: 43% Gaussian에 image-space sparse reference 없음 → Round 1b 설계 동기

**Round 1b (Image-Space 기반 depth residual):**
- 스크립트: `scripts/diagnostic/round1b_imagespace_depth.py`
- 출력: `results/diagnostic/round1b_depth_residual.png`, `round1b_coverage_gap.png`
- **발견 4**: Sparse point 2.44%가 SLAM triangulation 실패로 극단 좌표 (X=15203m, Z=907581m) → image-space depth residual 불안정
- **발견 5 (P12 확인됨)**: Z-axis Blind Spot. 카메라 elevation mean=5.39°, |view_Z|=0.094 → Z 방향 gradient = X 방향의 9.4%
- **발견 6 (핵심)**: 1,474 Gaussians (0.455%)가 |Z|>3m, range -42.71m~+17.35m. 씬 스케일 ±1.5m에서 40m 이탈 = 확실한 empty space floater
- **발견 7**: Z-outlier Gaussian의 nearest filtered sparse point 거리: median 25.5cm (정상 Gaussian은 2.5cm). 27.5%는 1m 이상 어떤 표면에서도 떨어져 있음

**Round 1 핵심 결론:**
> SLAM trajectory가 수평으로 이동하므로 Z 방향이 photometric loss의 blind axis가 된다.  
> 이 Z-axis gradient deficiency (9.4% signal)가 Gaussian Z-drift를 허용하고,  
> FOV 밖으로 나간 Gaussian은 gradient=0이 되어 Z=-42m에서 frozen된다.  
> 이것이 기존 COLMAP 기반 논문이 다루지 않은 SLAM 특유의 floater 생성 메커니즘이다.

**Perspective Bank 업데이트:**
- P11 추가: Projection-Space Coverage Gap
- P12 추가 + 확인됨: Z-Axis Blind Spot
- "확인됨" 섹션: low-opacity ≠ floater, P12 Z-axis

---

## Round 2: Z-Axis Gradient Verification (완료: 2026-06-30)

### Round 2 결과

**원래 목적**: P12 (Z gradient weakness) 확인 — 예측 grad_z/grad_x ≈ 0.094  
**실제 결과**: P12 기각, 완전히 다른 메커니즘 발견

| 지표 | 예측 | 실측 |
|---|---|---|
| grad_z / grad_x | 0.094 | **1.41 (mean)** — Z가 X보다 강함 |
| Z-outlier 기원 | gradient drift | **SLAM initialization outlier** |

**Z-outlier 시계열**:
```
iter   500: 46,264 Z-outliers (14.3%), |Z|_max = 907,582m  ← SLAM 초기화 실패
iter  1000: 18,108 Z-outliers                               ← 빠른 초기 pruning
iter  3500:  1,144 Z-outliers, |Z|_max = 41.83m            ← opacity reset+pruning (-97%)
iter  7000:  1,440 Z-outliers                               ← densification +296개
iter 15000:  1,442 Z-outliers (frozen)
```

**핵심 발견**:
1. **P12 기각**: Z gradient가 X보다 약하지 않음 (오히려 1.41배 강함)
2. **P04 확인**: X가 depth 축 (카메라가 X 방향 이동) → X gradient가 상대적으로 약함
3. **새 메커니즘**: SLAM 삼각화 실패로 907,582m Z-outlier sparse point → 초기화 시 14.3% Gaussian이 FOV 밖에 생성 → opacity reset+pruning으로 97% 제거 → 1,440개 survivors frozen at |Z|=42m

**논문 intervention 후보**: sparse point 초기화 전 XYZ bound 필터링 (SLAM outlier 차단)

**생성 파일**: `results/diagnostic/round2_gradient_analysis.png`

---

## Round 2 원래 계획: 시간 진단 — 언제 Floater가 고착되는가

### 추가할 logging (1000 iter마다)

```python
# train.py에 추가
if iteration % 1000 == 0:
    opacity = gaussians.get_opacity.detach()  # [N, 1]
    
    low_mask = (opacity < 0.1).squeeze()
    
    wandb_logger.log({
        "diag/low_opacity_count": low_mask.sum().item(),
        "diag/low_opacity_mean_opacity": opacity[low_mask].mean().item() if low_mask.any() else 0,
        # 3D position gradient (loss backward 이후 시점에서)
        "diag/grad_xyz_low_opacity": gaussians._xyz.grad[low_mask].norm(dim=-1).mean().item()
            if gaussians._xyz.grad is not None and low_mask.any() else 0,
        "diag/grad_xyz_high_opacity": gaussians._xyz.grad[~low_mask].norm(dim=-1).mean().item()
            if gaussians._xyz.grad is not None and (~low_mask).any() else 0,
        "diag/grad_opacity_low": gaussians._opacity.grad[low_mask].abs().mean().item()
            if gaussians._opacity.grad is not None and low_mask.any() else 0,
        "diag/grad_opacity_high": gaussians._opacity.grad[~low_mask].abs().mean().item()
            if gaussians._opacity.grad is not None and (~low_mask).any() else 0,
    }, step=iteration)
```

### 핵심 질문

- densification 중(iter < 7000)에 floater가 생기는가, 이후에 생기는가?
- `grad_opacity_low` vs `grad_opacity_high` 비율이 iter에 따라 어떻게 변하는가?
- 어느 iteration에서 gradient가 급락하는가? → 그게 "고착 시점"

---

## Round 3: Perturbation Analysis + Gradient Breakdown (완료: 2026-06-30)

### Round 3 결과

**실험**: exp08 iter 30000 모델 로드 → 1 backward pass + XYZ perturbation 분석

**Per-Gaussian gradient magnitude:**
```
Group                   | N_visible | |grad_x|   | |grad_y|   | |grad_z|   | z/x
Z-outlier (|Z|>3m)      |      1320 | 3.99e-07  | 4.25e-07  | 5.15e-07  | 1.29
Low-opacity surface     |    110166 | 5.04e-07  | 5.56e-07  | 6.44e-07  | 1.28
High-opacity surface    |    196996 | 1.46e-06  | 1.51e-06  | 1.97e-06  | 1.36

Z-outlier gradient = 27.4% of high-opacity surface (4x weaker, not zero)
```

**Loss perturbation sensitivity (±0.1m):**
```
Surface Gaussians (N=200):
  X (depth axis):  0.000053  ←  flattest (P04 confirmed)
  Y (lateral):     0.000056  (1.06x X)
  Z (vertical):    0.000078  (1.47x X)

Z-outlier floaters (N=50):
  All directions:  0.000001  ≈ 0  ← floaters are INVISIBLE to loss!
  Surface/Floater ratio: 53x
```

**핵심 발견:**
1. **P04 확인 (부분)**: X (depth axis)가 가장 flat. Z/X 민감도 비 = 1.47 (Round 2 gradient ratio 1.41과 일치)
2. **Floater isolation**: Z-outlier 이동은 global loss에 사실상 영향 없음 (53x 작음)
3. **새 메커니즘**: floater는 gradient가 완전히 0이 아님 (27% 존재) — 그러나 scene에 기여가 너무 미미해 loss landscape에서 사실상 invisible

**가설 A vs B 판단:**
- 가설 A (gradient vanishing): **부분적** — gradient 0이 아니라 27% 존재. 완전 vanishing은 아님.
- 가설 B (loss landscape flatness): **확인** — floater 위치를 움직여도 loss 변화 없음. 완전한 flatness.
- **승자**: B (위치 local minima) + 초기 SLAM 초기화로 이미 bad position에서 시작

**생성 파일**: `results/diagnostic/round3_perturbation_analysis.png`

---

## Round 3 원래 계획: 원인 구분 — Gradient Vanishing vs Loss Landscape Flatness

### 구분 실험: Perturbation Analysis

학습 완료 후 (no grad, analysis only):

```python
# 특정 checkpoint에서 floater Gaussian 선별 (depth residual로)
for G in floater_gaussians[:100]:  # 샘플 100개
    base_loss = compute_loss(scene, cameras_subset)
    
    for direction in ['x+', 'x-', 'y+', 'y-', 'z+', 'z-']:
        perturbed_G = G.xyz + epsilon * unit_vec[direction]
        perturbed_loss = compute_loss_with_perturbation(scene, G, perturbed_G)
        delta_L[G][direction] = perturbed_loss - base_loss

# 결과 해석
# Case 1: delta_L ≈ 0 모든 방향 → loss landscape flat → 가설 B
# Case 2: delta_L > 0 일부 방향 → 방향은 있는데 gradient 없음 → Adam/momentum 문제
# Case 3: gradient도 0, delta_L도 0 → 완전한 pseudo-equilibrium → 가설 A
```

### 이 결과가 논문에서 하는 일

```
Case 1 확인 → "photometric loss만으로는 empty space floater의 geometric signal이 없다"
              → 외부 geometric prior 없이 풀 수 없음을 증명
              → StableGS 방향(opacity 분리)보다 geometric anchoring 방향

Case 2 확인 → "gradient는 있으나 ADAM이 못 찾는다"
              → teleporting / MCMC 방향이 맞음

Case 3 확인 → "color matching trap"
              → opacity를 geometry에서 분리하는 StableGS 계열
```

---

## Round 4: SLAM 특이성 분석 — 기존 논문이 보지 않은 관점들

기존 16편은 대부분 COLMAP(SfM) 기반이다. OpenMAVIS(SLAM) 기반에서만 나타나는 특성을 찾는 것이 이 연구의 unique angle이 될 수 있다.

### 관점 1: Camera Ray Density Void

카메라가 trajectory를 따라 이동하면, 어떤 3D 영역은 많은 ray가 지나고 어떤 영역은 거의 지나지 않는다.

```
측정: 각 Gaussian 위치에서 training camera ray가 통과하는 횟수 (ray density)
예상: empty_space_score가 나쁜 Gaussian은 ray density가 낮은 구간에 위치
의미: 카메라가 잘 안 보는 "ray void" 구간이 floater의 온상
```

이게 확인되면 → "SfM과 달리 SLAM trajectory는 공간에 ray density gradient를 만들고,  
이 density가 낮은 구간에서 3DGS는 geometric signal 없이 Gaussian을 배치한다"  
→ 이걸 **논문의 문제 정의**로 쓸 수 있음

### 관점 2: Alpha Compositing 순서와 Floater의 관계

alpha compositing에서 Gaussian은 깊이 순서로 합산된다.  
floater가 몇 번째로 compositing되는지(depth rank)에 따라 loss signal이 다르다.

```
depth rank 낮음 (카메라 가까이): floater가 앞에 있어서 surface를 가림 → loss 강함
depth rank 높음 (surface 뒤):    floater가 뒤에 있어서 transmittance T_k ≈ 0 → loss signal 없음
```

측정:

```python
for floater G:
    depth_ranks = []
    for camera c:
        rays_through_G = get_rays_intersecting_gaussian(G, c)
        for ray r:
            rank = get_depth_order_of_G_on_ray(r)  # G가 이 ray에서 몇 번째인가
        depth_ranks.append(median(rank_on_this_camera))
    
    mean_depth_rank[G] = mean(depth_ranks)
```

예상: floater의 대부분이 **높은 depth rank** (표면 뒤에서 합산) → T_k ≈ 0 → invisible to loss  
이게 나오면 → "floater는 loss function이 접근할 수 없는 compositing shadow에 숨어있다"

### 관점 3: Densification이 Empty Space Gaussian을 만드는 경로

현재 densification은 viewspace gradient가 높은 Gaussian을 split/clone한다.  
이 Gaussian의 **3D 위치**가 실제로 어디인지는 검사하지 않는다.

```
측정: densification 직후 생성된 Gaussian의 depth residual 분포
      (새로 생긴 Gaussian이 태어날 때부터 empty space인가?)
      
예상: split 후 즉시 depth residual이 음수인 Gaussian이 일부 존재
의미: densification이 floater의 seed를 만드는 경로
```

이게 확인되면 → densification 시 depth residual을 체크해서 empty space에 생기는 Gaussian을 막는 것이 intervention

### 관점 4: Photometric Loss의 Position Ambiguity Zone

동일한 픽셀 색상을 만들 수 있는 xyz 위치가 ray 방향으로 여러 개 존재한다.  
이것이 local minima가 많은 근본 이유다.

```
측정: floater Gaussian을 ray 방향으로 이동(teleport)하면서 loss 측정
      - 카메라 방향으로 이동: loss가 변하는가?
      - 표면 방향(depth 증가)으로 이동: loss가 감소하는가?
```

예상: ray 방향으로의 이동은 loss가 거의 안 변한다 (ray ambiguity)  
이게 확인되면 → "photometric loss는 ray 방향의 depth ambiguity를 해결하지 못한다"  
→ depth direction의 regularizer가 필요

### 관점 5: Color-Position Coupling의 Degree of Freedom 문제

Gaussian의 color (SH coefficients)가 view-dependent하게 학습되면,  
잘못된 위치에서도 training view에서의 색을 맞출 수 있는 DOF가 생긴다.

```
측정: floater Gaussian의 SH 차수별 에너지 (high-order SH가 큰가?)
      high-order SH가 크다 = view-dependent compensation이 강하다 = 위치가 틀려도 색을 맞추고 있다

비교: surface Gaussian의 SH energy distribution과 비교
```

예상: floater는 고차 SH 에너지가 불균형하게 높다  
이게 나오면 → "floater는 SH의 view-dependent DOF를 이용해 잘못된 위치를 보상한다"

---

## Round 5: Intervention 설계

Round 3 결과에 따라 방향이 갈린다.

### Branch A: Geometric Signal 없음 (Loss Flat)
→ Sparse point를 학습 중 geometric anchor로 사용  
→ 단, exp12에서 실패했으므로 "언제" 걸 것인가가 핵심  
→ Round 2에서 나온 "고착 시점" 이전에 약하게 켜는 delayed prior

### Branch B: Gradient는 있으나 Optimizer가 못 찾음
→ SteepGS처럼 steepest descent 방향 강제  
→ 또는 floater Gaussian을 sparse point 근방으로 teleport  
→ teleport 기준: depth_residual << 0 AND opacity < threshold

### Branch C: Color Matching Trap
→ opacity를 geometry에서 분리 (StableGS의 Dual Opacity)  
→ 현재 코드에 보조 opacity 변수 추가 필요

### SLAM 특유의 개입 (Round 4 결과 기반)
→ Ray density map을 사용한 densification 가중치 조정  
→ ray density가 낮은 구간에서 생성된 Gaussian에 stronger geometric constraint

---

## 우선순위 및 순서

```
1. [코드 없이] Round 1 Part 1: exp08 PLY에서 depth residual 계산 스크립트
   → 결과: empty space floater의 실제 비율과 분포

2. [logging 추가, 1회 학습] Round 2: gradient 시간 추이
   → 결과: 고착 시점, gradient vanishing 여부 첫 확인

3. [분석 스크립트] Round 3: perturbation analysis
   → 결과: 가설 A vs B vs C 확정

4. [Round 4] 관점 1~3 중 Round 3 결과와 연결되는 것 우선 진행
   → 결과: SLAM 특유의 원인 여부

5. Round 5: intervention 설계 및 실험
```

---

## 논문 figure 예상 구성

```
Figure 1 (문제 정의):
  - empty space floater의 3D 시각화 (depth residual 색상)
  - 기존 low_opacity_ratio와의 불일치 scatter plot
  → "opacity는 floater의 충분조건이 아니다"

Figure 2 (메커니즘):
  - gradient magnitude over iteration (low vs high opacity Gaussian 비교)
  - perturbation analysis loss curve
  → "optimizer가 왜 floater를 제거하지 못하는가"

Figure 3 (SLAM 특이성, Round 4 결과 기반):
  - camera ray density map vs floater distribution
  OR
  - compositing depth rank distribution for floaters vs surface Gaussians
  → "기존 논문이 보지 않은 원인"

Figure 4 (intervention 결과):
  - 제안 방법 vs exp08 (baseline) vs 기존 SOTA
```

---

---

## 파일 위치

- **관점 Bank**: `context/knowledge/perspective_bank.md`
- 진단 스크립트: `scripts/diagnostic/`
- 중간 결과: `results/diagnostic/`
- 논문 draft: `docs/paper_draft/` (Round 4 이후)

---

## Perspective Bank 운영 예시

Round 1에서 depth residual 분포를 뽑았을 때:

```
데이터: low-opacity Gaussian 중 depth residual << 0 인 비율이 40%
        하지만 depth residual << 0 인데 opacity가 중간(0.3~0.5)인 Gaussian도 20% 존재

관찰: "opacity가 중간인데도 empty space에 있다"
→ opacity로 floater를 정의하면 이 20%를 놓친다

새로운 관점: "moderate opacity floater"
→ opacity threshold 기반 기존 방법이 왜 안 되는지의 직접 증거
→ bank에 [P11] 로 추가
```

이런 방식으로 데이터를 볼 때마다 새 관점을 뽑아낸다.

---

## Round 5: SLAM Sparse Point Filtering (완료: 2026-06-30)

### 구현

`scene/dataset_readers.py`에 `_filter_pcd_by_camera_bound()` 추가:
- 카메라 center 계산: `C = -R_cam2world @ T` (기존 버그: `-R.T @ T`)
- per-axis 최소 margin: XY=2m, Z=3m
- expand_factor=1.0 → Z[-3.05, +3.03]m

### Round 5b 결과 (expand=1.0, corrected, W&B: cukasosi)

**필터 적용:**
```
Camera extent: Z[-0.05, +0.03]  ← 수평 궤적 확인
Filter bounds: Z[-3.05, +3.03]
Removed:       46,276 / 626,811 sparse points (7.38%)
Z-outlier pts: 45,637개 제거
```

**비교 (Round 2 baseline vs Round 5b):**
```
Metric                | Round 2 (no filter) | Round 5b (filter) | Change
Z-outlier @ iter 500  |       46,264 (14.3%)|          508 (0.2%)| -98.9%
Z-outlier @ iter 15k  |             1,442   |              374   | -74.1%
|Z|_max final (m)     |             42.20m  |            6.21m   | -85.3%
PSNR @ iter 7000      |             28.21   |            28.28   | +0.07dB
```

**핵심 발견:**
1. **98.9% 초기 Z-outlier 감소**: SLAM 삼각화 실패 sparse point 필터링이 극도로 효과적
2. **PSNR neutral-to-positive**: 7.38% sparse point 제거가 quality에 무해함
3. **남은 374개**: densification이 filter boundary(3m) 근방에서 새로 생성한 것 (max 6.21m로 42m보다 훨씬 양호)

**참조 figure**: `results/diagnostic/round5b_intervention_results.png`

### 논문 Contribution 확정

**제목 후보**: "Filtering SLAM Triangulation Outliers Prevents 99% of Gaussian Floaters in 3DGS"

**방법**: 초기화 전 카메라 extent 기반 XYZ bound 필터링 (12줄 코드)
**결과**: Z-floater -98.9% at initialization, -74% at convergence, PSNR ±0dB

---

## exp13 vs exp08 Full 30k Comparison (완료: 2026-06-30)

### 실험 설정

- **exp08**: 기준 (필터 없음, PSNR 33.012 @ 30k)
- **exp13**: exp08 동일 hyperparams + `init_pcd_filter=true, expand_factor=1.0` (W&B: h7cqzny3)

### 최종 비교

```
Metric                    | exp08 (no filter) | exp13 (filter) | Δ
------------------------------------------------------------------
Z-outlier @ iter 500      |            46,264 |           507  | -99.0%
Z-outlier @ iter 30k      |             1,474 |           385  | -73.9%
|Z|_max final (m)         |             42.71 |          4.85  | -88.6%
PSNR @ iter 30k (train)   |            33.012 |         32.855 | -0.16 dB
Ambiguity positive_ratio  |             33.3% |          35.0% | +1.7 pp
```

### 핵심 발견: 두 개의 Floater 집단

PSNR은 -0.16 dB 하락, ambiguity_ratio는 오히려 +1.7pp 증가 → 예상과 다른 방향

**원인 분석:**
- exp08의 1,474 Z-outliers: |Z|=42m → 대부분 **FOV 밖** → 이미지에 투영 안 됨 → ambiguity 기여 없음
- exp13의 385 Z-floaters: |Z|=3-5m → **씬 내부** → 이미지에 투영됨 → ambiguity 유발

→ **두 개의 별개 Floater 집단 발견:**

| 집단 | 기원 | Z 범위 | FOV 안/밖 | 이미지 기여 | 필터 해결? |
|---|---|---|---|---|---|
| Pop 1 | SLAM init outlier | \|Z\|>42m | 밖 (invisible) | 없음 | ✅ -99% |
| Pop 2 | Densification floater | \|Z\|=3-6m | 안 (visible) | ambiguity 원인 | ❌ 남음 |

**PSNR -0.16 dB 원인**: 7.38% sparse point 제거 시 일부 valid surface point도 포함됨.

### 논문 Framing 수정

**기존**: "필터링으로 floater 감소 + PSNR 중립"
**수정**: 
- Contribution 1: Pop 1 (SLAM init outlier) → 99% 감소, PSNR -0.16dB (감당 가능한 비용)
- New Problem: Pop 2 (Densification floater) → 여전히 image-space ambiguity 유발, 별도 intervention 필요

**참조 figure**: `results/diagnostic/exp13_final_comparison.png`
