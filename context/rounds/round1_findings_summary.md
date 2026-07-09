# Round 1 진단 결과 요약 (논문 기여 후보)

작성일: 2026-06-30  
분석 대상: exp08 (PSNR 33.012, 323,864 Gaussians, densify_until=7000)

---

## 핵심 발견 3가지

### 발견 1: Low-opacity ≠ Empty Space Floater (기존 가정 기각)

**기존 가정**: opacity가 낮은 Gaussian = floater, opacity 기반 pruning으로 제거 가능  
**실측**: 126,330개 low-opacity Gaussian (opacity < 0.1)이 표면 위에 존재

```
opacity < 0.1인 Gaussian 총 126,360개 (39.0%)
  → 표면 위 (depth_residual ≈ 0): 126,178개 (99.9%)
  → floater (dr < -0.15m): 127개 (0.1%)
```

**결론**: opacity는 floater의 조건이 아니다. 기존 논문들이 "low-opacity = floater"를 가정하고 설계한 pruning은 이 데이터에서 근본적으로 wrong tool이다.

---

### 발견 2: SLAM Horizontal Trajectory → Z-Axis Blind Spot (신규, 정량화됨)

**메커니즘**: SLAM 카메라가 수평으로 이동할 때 viewing direction의 Z component가 매우 작다 → Z 방향 photometric gradient가 극히 약하다.

**실측 수치:**

| 측정 항목 | 값 |
|---|---|
| 카메라 elevation angle (mean ± std) | 5.39° ± 4.44° |
| elevation range | -1.88° ~ +28.80° |
| \|view_Z\| (Z 방향 viewing 비율) | 0.094 |
| Z-axis gradient sensitivity (vs X) | **9.4%** |
| X-axis gradient sensitivity | 99.1% |

**Z-drift 증거:**

| 조건 | 수치 |
|---|---|
| \|Z\| > 3m Gaussians | 1,474개 (0.455%) |
| \|Z\| > 5m Gaussians | 779개 (0.240%) |
| 최대 Z 이탈 | -42.71m (씬 스케일: ±1.5m) |
| Z-outlier opacity median | 0.059 (low지만 pruning 통과) |

**왜 COLMAP 논문에는 이 문제가 없는가?**  
SfM(COLMAP)은 여러 높이(드론, 핸드헬드 다방향)에서 찍어 Z 방향 gradient가 충분히 존재. SLAM은 구조적으로 수평 이동 → Z blind spot은 SLAM 특유의 문제.

---

### 발견 3: High-Opacity Z-outliers > Low-Opacity Z-outliers (역직관적, 핵심)

**가장 중요한 발견**: Z-drift가 심한 Gaussian일수록 opacity가 오히려 높다.

```
opacity 구간   | n   | mean |Z|
0.01 ~ 0.05   | 466 |  9.0m
0.05 ~ 0.10   | 355 | 11.1m
0.10 ~ 0.20   | 237 | 14.9m
0.20 ~ 0.30   |  82 | 24.2m
0.30 ~ 0.50   |  53 | 25.0m
0.50 ~ 1.00   |  87 | 29.0m ← 가장 먼 Z 이탈
```

**메커니즘 (제안):**
1. 학습 초반(iter < 7000): Gaussian이 표면 근처에서 색상 학습 → opacity 상승
2. 동시에 Z gradient deficiency로 서서히 Z 방향 drift
3. densification 종료(iter 7000) → pruning/reset 없음
4. 고opacity 상태로 Z=-42m까지 계속 drift
5. FOV 밖으로 나간 후: gradient=0, 위치+opacity 둘 다 frozen

**Opacity-based pruning의 근본적 실패:**
- 표준 pruning threshold: 0.01
- Z-outlier Gaussian 중 **86.8%가 pruning threshold를 통과** (1280/1474)
- 특히 가장 문제적인 high-opacity group(0.5-1.0, n=87)은 완전히 놓침

---

## 이 발견이 논문에서 하는 일

### 진단 contribution

> "SLAM trajectory의 수평성이 3DGS에서 Z 방향 geometric constraint 결핍을 야기한다. 이것이 기존 COLMAP 기반 방법에서 관찰되지 않은 SLAM-specific floater 패턴이다."

이 발견으로:
1. **기존 설명 기각**: "floater는 low-opacity" → 데이터로 반박
2. **SLAM-specific mechanism 제시**: Z-axis blind spot (elevation 5.39°, gradient 9.4%)
3. **정량적 증거**: 1474 Gaussians, -42m drift, 87개 high-opacity floaters

### Intervention direction

**발견 2+3으로부터**: 
- Opacity-based pruning은 Z-drift floater를 잡지 못함 (86.8% 생존)
- **필요한 것**: Geometric constraint로 Z-drift 예방 또는 geometric bounding box 기반 pruning

**후보 intervention (Round 5 계획):**
1. **Scene bounding box pruning**: trajectory와 씬 extents에서 bounding box를 정의하고, 그 밖의 Gaussian을 주기적 prune
2. **Z-axis regularizer**: 학습 중 Z 방향 displacement penalty (trajectory Z ± max_z_deviation)
3. **Trajectory-aware densification constraint**: dense camera coverage가 없는 Z 구간에서 densification 억제

---

## 다음 단계 (Round 2)

train.py에 추가된 gradient logging (`diag_grad_interval=500`):
- `diag/grad_z_mean`: Z 방향 평균 gradient magnitude
- `diag/grad_x_mean`: X 방향 평균 gradient magnitude  
- `diag/grad_z_vs_x_ratio`: Z/X gradient ratio (예측: ~0.094)
- `diag/z_outlier_count_3m`: 학습 중 Z-outlier count 진화
- `diag/z_abs_p99`: Z 이탈 99th percentile (drift 진행 추적)

**Round 2 목표**: 학습 중 gradient ratio가 실제로 9.4%인지, Z-drift가 언제(densification 전? 후?) 주로 발생하는지 확인.

---

## 생성된 파일들

| 파일 | 내용 |
|---|---|
| `scripts/diagnostic/round1_depth_residual.py` | Round 1a: 3D 기반 depth residual |
| `scripts/diagnostic/round1b_imagespace_depth.py` | Round 1b: Image-space depth residual |
| `results/diagnostic/round1_overview.png` | Round 1a 9-panel 분석 |
| `results/diagnostic/round1b_depth_residual.png` | Round 1b depth 분석 |
| `results/diagnostic/round1b_coverage_gap.png` | Round 1b coverage gap 분석 |
| `results/diagnostic/round1c_z_outlier_analysis.png` | **Z-outlier 핵심 figure (논문 후보)** |
| `results/diagnostic/round1b_floater_colored.ply` | 3D viewer용 colored PLY |
| `context/knowledge/perspective_bank.md` | 관점 bank (P11, P12 추가, P12 확인됨) |
