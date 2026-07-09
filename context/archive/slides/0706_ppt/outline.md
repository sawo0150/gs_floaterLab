# PPT 구상안 v2: 3DGS Floater 제거 연구 (2026-07-04 ~ 07-06)

> 핵심 내러티브:
> "Photometric loss만으로는 floater를 이동시킬 수 없다 → 왜 그런지 데이터로 증명 →
>  Plateau Loss로 3D 공간 regularizer를 설계 → 실험 결과 → 앞으로 할 일"

---

## 전체 구성 (~38 slides)

```
[Section 1] 타이틀 + 배경           2 slides   (1-2)
[Section 2] Baseline & VGGT 비교    2 slides   (3-4)
[Section 3] 문제의식: Photometric   4 slides   (5-8)
             Loss의 한계
[Section 4] 증거 1: Ray Density     5 slides   (9-13)
             Z-layer 분석
[Section 5] 증거 2: ORB-SLAM        9 slides   (14-22)
             Sparse Points Z-layer
[Section 6] 증거 3: MPS Sparse      9 slides   (23-31)
             Points Z-layer
[Section 7] Plateau Loss 설계       5 slides   (32-36)
[Section 8] 실험 결과               3 slides   (37-39)
[Section 9] 향후 연구               3 slides   (40-42)
```

---

## Slide-by-Slide 설계

---

### [Section 1] 타이틀 + 배경

---

#### Slide 1 — 타이틀

**제목**: 3DGS Floater 제거 연구  
**부제**: Photometric Loss의 한계와 Sparse Support Plateau Loss 접근  
**날짜**: 2026-07-04 ~ 07-06

---

#### Slide 2 — 연구 배경 & 목표

**레이아웃**: 좌(문제 사진 / 렌더 결과) / 우(정의)

**문제 정의**:
- OpenMAVIS 기반 3DGS 학습 시 공중에 떠 있는 Gaussian(floater) 다수 발생
- 단순 학습 파라미터 조정으로는 해결 한계

**현재 best baseline**:
| 항목 | exp08 |
|---|---:|
| PSNR@30k | **33.012 dB** |
| Gaussian count | 323,864 |
| 핵심 설정 | sparse densification, until_iter=7000, beta1=0.85 |

**연구 질문**: Photometric loss가 닿지 않는 floater를 어떻게 제거할 수 있는가?

---

### [Section 2] Baseline & VGGT 비교

---

#### Slide 3 — PLY 렌더링: Baseline 결과

**레이아웃**: 전체 화면 이미지 (camera trajectory를 내부에서 렌더링)

**내용**:
- exp08 30k PLY를 카메라 경로 내부 시점에서 렌더링한 이미지
- floater가 어디에 위치하는지 시각적으로 확인
- 캡션: "붉은 원 = Pop2 floater 위치 (Z = +2~3m, 천장 방향)"

> **[제작 시 주의]**: `results/exp08_openmavis_full.../point_cloud/iteration_30000/point_cloud.ply`를
> Open3D 또는 SIBR viewer로 카메라 경로 내부 시점에서 렌더링해서 스크린샷

---

#### Slide 4 — VGGT vs OpenMAVIS 비교 + EVO

**레이아웃**: 2열 비교표 + EVO 차트

**64-frame 3DGS 비교**:
| 항목 | VGGT64 | OpenMAVIS64 |
|---|---:|---:|
| Test PSNR @7k | 17.04 | **18.65** |
| Train PSNR @7k | 30.26 | **34.25** |
| Gaussian count | 557k | 792k |
| Large scale ratio | 0.00018 | 0.02987 |

**EVO 궤적 정확도 (MPS 기준)**:
| | OpenMAVIS ORB | VGGT64 |
|---|---:|---:|
| APE RMSE | **0.56 m** | 2.68 m |
| APE median | **0.40 m** | 1.23 m |

**결론 박스**: "VGGT는 compact하지만 render 품질과 경로 정확도 모두 OpenMAVIS 열세. 현재 대체 불가."

---

### [Section 3] 문제의식: Photometric Loss의 한계

---

#### Slide 5 — Photometric Loss가 Floater를 못 잡는 이유 (1): Ray Trigger

**레이아웃**: 좌(다이어그램) / 우(핵심 설명)

**다이어그램**: 카메라 → ray → Gaussian 위치
- 표면 Gaussian: 많은 ray 통과 → strong gradient ✓
- Floater: 거의 ray 없음 → weak/no gradient ✗

**핵심 설명**:
> "Photometric loss는 rendered pixel에 기여하는 Gaussian에만 gradient를 준다.
> 즉, 어떤 카메라에서도 잘 보이지 않는 floater는 이동 신호 자체가 없다."

**문제 1**: Ray 분포가 Z layer별로 완전히 다름 → 증거는 다음 슬라이드

---

#### Slide 6 — Photometric Loss의 한계 (2): Spatial Blindspot

**레이아웃**: 수식 + 설명

**핵심 포인트**:

1. **Ray density 불균일**: 카메라가 수평 이동 → 천장(Z=+2~3m)을 올려보는 ray가 극히 적음

2. **Depth regularization도 2D loss**: 이미지 평면에서 계산 → 깊이 방향 외에는 직접 제약 없음

3. **Photometric gradient의 이동 범위가 매우 좁음**:
   - Photometric loss는 픽셀 색상만 맞추면 됨 → 공간적 이동은 최소화
   - Floater가 photometric하게 설명 가능한 위치라면 절대 이동하지 않음

4. **결론**:
   > "Floater가 rendered image에 조금이라도 기여하는 한, photometric loss는 그것을 그 자리에 놔두는 것이 최선이다. 공간적 제약이 없기 때문."

---

#### Slide 7 — Photometric Loss의 한계 (3): 왜 3D loss가 필요한가

**레이아웃**: 대비 다이어그램

**Photometric Loss** (2D):
```
카메라 → 렌더 → 픽셀 비교
gradient는 ray를 통해서만 전파
공간적 의미 없음 (어디 있어도 색이 맞으면 OK)
```

**Depth Regularization** (2.5D):
```
2D 이미지 depth map 기반
표면 구조 일부 반영하나 역시 ray-triggered
```

**필요한 것: 3D Loss**:
```
Gaussian의 3D 위치 자체에 직접 gradient
ray와 무관하게 모든 Gaussian에 작용
표면(앵커) 주변은 보호, 표면 밖은 당김
→ Plateau Loss
```

**오른쪽 강조박스**:
> "핵심 아이디어: 표면 근처(plateau 내부)는 3D gradient = 0 → photometric optimization 자유.
>  표면 밖(floater 구간)은 강한 gradient → 표면으로 유도."

---

#### Slide 8 — 문제의식 요약: 두 가지 증거 데이터

**레이아웃**: 티저 슬라이드 (다음 섹션 예고)

**왜 Ray Density 분석을 했는가**:
- Photometric gradient가 Z layer별로 얼마나 다른지 정량화
- "천장 방향 floater는 애초에 gradient가 올 수 없다"는 것을 수치로 보이기 위해

**왜 Z-layer Sparse Point 분석을 했는가**:
- Plateau Loss의 앵커(anchor)가 어느 Z 구간에 존재하는지 파악
- "Pop2 floater 구간(Z=+2~3m)에는 앵커 자체가 없다"는 문제를 확인하기 위해

> 다음 섹션: 3개 분석 결과 전체 페이지 →

---

### [Section 4] 증거 1: Photometric Ray Density Z-layer 분석

*각 페이지 = PDF 원본 임베딩 (전체 크기, 제목+설명 오버레이)*

---

#### Slide 9 — [PDF] Ray Density 커버: 분석 개요
**소스**: `ray_density_zlayers_20260705_005831/ray_density_zlayers.pdf` — p.1

**하단 인사이트 박스**:
- 총 1,300,500 rays (500 카메라 × 2,601 rays)
- 8개 Z 슬랩, 각 ≈ 0.76m 두께
- Log scale 공유 → 층간 직접 비교 가능

---

#### Slide 10 — [PDF] Ray Density Layer 1/8: Z ∈ [-3.02, -2.27) m
**소스**: p.2 | 바닥 아래 — 총 372,687 rays

**인사이트**: 씬 하한. 카메라 ray가 거의 도달하지 않음.
→ 이 구간에 Gaussian이 있어도 photometric gradient 거의 없음.

---

#### Slide 11 — [PDF] Ray Density Layer 2/8: Z ∈ [-2.27, -1.51) m
**소스**: p.3 | 바닥면 부근 — 총 465,245 rays

**인사이트**: 바닥 슬라브. 아래 방향 ray만 통과.
카메라 경로(오렌지) 근처에서 ray 집중 시작.

---

#### Slide 12 — [PDF] Ray Density Layer 3/8: Z ∈ [-1.51, -0.75) m
**소스**: p.4 | 바닥/하부 벽 — 총 560,711 rays

**인사이트**: 씬 핵심 구조. photometric loss 집중.
카메라 이동 경로 주변 진한 적색 = gradient 풍부.

---

#### Slide 13 — [PDF] Ray Density Layer 4/8: Z ∈ [-0.75, 0.00) m
**소스**: p.5 | 카메라 눈높이 아래 — 총 813,594 rays

**인사이트**: **가장 많은 ray 통과. loss gradient 최강.**
→ 이 층의 Gaussian은 photometric loss로 충분히 제어 가능.
→ 반대로, Z > +1.5m 구간은 ray 자체가 급감.

> **[주목]**: Layer 1~4 비교 → Z가 높아질수록(천장 방향) ray 밀도 급감.
>  Ray density PDF에서 Layer 5~8은 천장/천장위 구간. 별도 슬라이드 불필요.
>  핵심 메시지: "천장 방향은 photometric gradient가 구조적으로 약하다"

---

### [Section 5] 증거 2: ORB-SLAM Sparse Points Z-layer 분석

*ORB-SLAM map points = plateau 앵커 후보. 어느 Z 구간에 얼마나 있는가?*

---

#### Slide 14 — [PDF] ORB-SLAM Sparse: 커버
**소스**: `orb_zlayers_v1_20260705_014758/orb_zlayer_annotated.pdf` — p.1

**하단 인사이트 박스**:
- 총 7,182 ORB-SLAM map points
- 고confidence (obs≥10): 835개 (11.6%)
- MPS semi-dense(626,811 pts)와 완전히 다른 출처

---

#### Slide 15 — [PDF] ORB Layer 1/8: Z ∈ [-3.06, -2.30) m
**소스**: p.2 | 바닥 아래 — 3 pts (obs≥10: 0)

**인사이트**: 사실상 비어있음. ORB-SLAM이 이 구간을 삼각화하지 못함.

---

#### Slide 16 — [PDF] ORB Layer 2/8: Z ∈ [-2.30, -1.54) m
**소스**: p.3 | 바닥면 부근 — 185 pts (obs≥10: 19)

**인사이트**: 바닥 슬라브. 고confidence 점 생기기 시작.

---

#### Slide 17 — [PDF] ORB Layer 3/8: Z ∈ [-1.54, -0.78) m
**소스**: p.4 | 바닥/하부 벽 — 1,645 pts (obs≥10: 157)

**인사이트**: 카메라 통과 높이 직상. 고confidence 점 집중.

---

#### Slide 18 — [PDF] ORB Layer 4/8: Z ∈ [-0.78, -0.02) m
**소스**: p.5 | 카메라 눈높이 아래 — 2,007 pts (obs≥10: 232)

**인사이트**: **가장 잘 관측되는 표면. 고obs 점 최다.**

---

#### Slide 19 — [PDF] ORB Layer 5/8: Z ∈ [-0.02, +0.74) m
**소스**: p.6 | 카메라 눈높이 위 — 1,440 pts (obs≥10: 194)

**인사이트**: 카메라 통과 높이 직상. 비슷하게 충분.

---

#### Slide 20 — [PDF] ORB Layer 6/8: Z ∈ [+0.74, +1.50) m
**소스**: p.7 | 상부 벽/천장 — 1,481 pts (obs≥10: 204)

**인사이트**: 천장+상부 벽. 관측 수 급감 시작.
카메라가 올려보는 각도가 작아지며 삼각화 어려워짐.

---

#### Slide 21 — [PDF] ORB Layer 7/8: Z ∈ [+1.50, +2.26) m
**소스**: p.8 | 천장 위 — 380 pts (obs≥10: 22)

**인사이트**: **Pop2 floater 시작 구간. sparse 부족 시작.**
ORB-SLAM 삼각화 각도 부족으로 점 급감.

---

#### Slide 22 — [PDF] ORB Layer 8/8: Z ∈ [+2.26, +3.02) m
**소스**: p.9 | Pop2 floater 위험 구간 — 30 pts (obs≥10: **7**)

**인사이트 강조박스 (빨간색)**:
> "ORB-SLAM 고confidence 점 **사실상 0개**.
>  이 구간에 plateau를 만들 수 없다 → ORB 앵커로는 Pop2 floater 제거 불가."

---

### [Section 6] 증거 3: MPS Sparse Points Z-layer 분석

*MPS semi-dense = 실제 3DGS init에 쓰이는 626,811 pts. 앵커 보완 가능성?*

---

#### Slide 23 — [PDF] MPS Sparse: 커버
**소스**: `real_MPSzlayers_v2_20260705_003737/zlayer_annotated.pdf` — p.1

**하단 인사이트 박스**:
- 총 626,811 pts (ORB 7,182의 87배)
- SLAM outlier: 46,276 (7.4%) → camera-bound filter로 제거
- 8개 Z layer, 각 ≈ 0.76m

---

#### Slide 24 — [PDF] MPS Layer 1/8: Z ∈ [-3.05, -2.29) m
**소스**: p.2 | 바닥 아래 — 1,193 pts (0.2%)

**인사이트**: ORB와 달리 MPS는 이 구간에도 점 존재.
단, 산재되어 있고 outlier 혼재.

---

#### Slide 25 — [PDF] MPS Layer 2/8: Z ∈ [-2.29, -1.53) m
**소스**: p.3 | 바닥면 부근 — 11,562 pts (2.0%)

**인사이트**: 바닥 슬라브 구조 보임. 밀도 증가.

---

#### Slide 26 — [PDF] MPS Layer 3/8: Z ∈ [-1.53, -0.77) m
**소스**: p.4 | 바닥/하부 벽 — 118,243 pts (20.4%)

**인사이트**: 핵심 구조면. MPS dense하게 커버.

---

#### Slide 27 — [PDF] MPS Layer 4/8: Z ∈ [-0.77, -0.01) m
**소스**: p.5 | 카메라 눈높이 아래 — 133,581 pts (23.0%)

**인사이트**: 가장 잘 보이는 표면. 최고 밀도.

---

#### Slide 28 — [PDF] MPS Layer 5/8: Z ∈ [-0.01, +0.75) m
**소스**: p.6 | 카메라 눈높이 위 — 114,665 pts (19.8%)

**인사이트**: 동일하게 충분. 카메라 통과 높이 직상.

---

#### Slide 29 — [PDF] MPS Layer 6/8: Z ∈ [+0.75, +1.51) m
**소스**: p.7 | 상부 벽/천장 — 127,379 pts (21.9%)

**인사이트**: MPS는 천장/상부 벽도 여전히 충분. ORB 대비 큰 차이.

---

#### Slide 30 — [PDF] MPS Layer 7/8: Z ∈ [+1.51, +2.27) m
**소스**: p.8 | 천장 위 — 59,174 pts (10.2%)

**인사이트**: ORB(380pts)와 달리 MPS는 59,174pts. **Pop2 구간 시작에서도 큰 차이.**
단, dist_std ≈ 0.4~1m (절대 위치 불확실 → 앵커 정밀도 낮음).

---

#### Slide 31 — [PDF] MPS Layer 8/8: Z ∈ [+2.27, +3.03) m
**소스**: p.9 | Pop2 floater 위험 구간 — 14,738 pts (2.5%)

**인사이트 박스**:
- ORB: 30pts (고confidence 7) vs **MPS: 14,738pts**
- MPS는 이 구간도 커버 → **좌표계를 MPS로 통일하면 DepthPro 앵커 사용 가능**

> "ORB-SLAM에서 MPS로 전환하는 근거: 앵커 좌표계 정합 + Pop2 구간 커버."

---

### [Section 7] Plateau Loss 설계

---

#### Slide 32 — Plateau Loss: 핵심 아이디어

**레이아웃**: 그림(plateau 단면) + 수식

**설계 원칙**:
```
Plateau 내부 (D ≤ 1):   gradient = 0
                         → photometric loss가 자유롭게 Gaussian 이동
Plateau 외부 (D > 1):   gradient > 0
                         → Gaussian을 surface(앵커) 쪽으로 당김
```

**Loss 수식**:
```
L_plateau = mean( max(D_min - 1, 0)^2 )

D_min(x) = min_j  ||x - p_j|| / τ_j        (구형)
         = min_j  sqrt((Δ·u_t/τ_t)² + (Δ·u_n/τ_n)²)   (타원체)
```

**학습 통합**:
```
loss = L_photo + λ × L_plateau
```
- `λ = 0`일 때: 기존 3DGS와 동일
- `λ > 0` + plateau 밖: floater에 geometric gradient

---

#### Slide 33 — 앵커 소스: DepthPro v4

**레이아웃**: 파이프라인 다이어그램

**생성 파이프라인**:
```
57 MPS 키프레임
    ↓ DepthPro (metric depth estimation)
    ↓ back-projection (MPS intrinsics + extrinsics)
    ↓ Poisson-disk sampling (간격 0.5m)
7,338 virtual anchors  (MPS world 좌표계)
```

**MPS 학습과 좌표계 정합**:
```
MPS semi-dense init  →  MPS world 좌표계 ✓
DepthPro anchors     →  MPS world 좌표계 ✓
                          동일 → plateau 작동
```

**ORB 학습의 문제 (교훈)**:
```
ORB 학습          →  ORB world 좌표계
DepthPro anchors  →  MPS world 좌표계
        → 완전히 다른 공간 → exp15-18 사실상 무효
```

---

#### Slide 34 — 구형 vs 타원체 Plateau

**레이아웃**: 나란히 비교 (수식 + 그림)

| | 구형 (Spherical) | 타원체 (Ellipsoidal) |
|---|---|---|
| 거리 | `‖x-p‖ / τ` | kNN PCA로 surface normal u_n 추정 |
| τ | `clip(0.6·h_j, 0.05, 0.60)` | τ_n=`clip(0.4·h_j, 0.03, 0.30)` (tight) |
|   |                              | τ_t=`clip(0.9·h_j, 0.03, 0.60)` (loose) |
| Coverage (Layer 4) | **11.9%** | **14.0%** (+2.1%) |
| 실험 결과 (vs ORB baseline) | -1.11 dB | **-0.10 dB** |

**핵심 차이**:
- 타원체: 표면 방향(tangent)은 넓게, 법선 방향(normal)은 좁게
- 벽면 Gaussian이 벽을 따라 자유롭게 이동 가능 → 과밀집 방지

---

#### Slide 35 — Pop2 구간 문제: Layer 8 Coverage = 0%

**레이아웃**: Coverage 테이블 + 해결 방법

**Z-layer별 Coverage (ORB 앵커 기준)**:

| Layer | Z 범위 | 앵커 수 | Sphere | Ellipsoid |
|---|---|---:|---:|---:|
| 3 | [-1.54,-0.78) | 1,540 | 9.7% | 11.9% |
| 4 | [-0.78,-0.02) | 1,896 | 11.9% | 14.0% |
| 6 | [+0.74,+1.50) | 1,316 | 10.6% | 11.9% |
| **8** | **[+2.26,+3.02)** | **9** | **0%** | **0%** |

**Pop2 구간 대응 전략**:
1. ✅ **pop2_zclip**: Z ≥ 2.0m Gaussian 주기 hard pruning (매 1000 iter, start=7000)
2. ✅ **DepthPro anchors**: MPS 좌표계에서 이 구간도 커버
3. ⬜ (검토 중) tau 확대 → enlarged tau로 인접 앵커 influence 확장

---

#### Slide 36 — 주요 실험 비교: 핵심 결과

**레이아웃**: 가로 바 차트 (PSNR 비교) + 실험 표

**기준: exp08 = 33.012 dB**

| 실험 | 핵심 설정 | PSNR@30k | Δ |
|---|---|---:|---:|
| exp08 | MPS baseline (no plateau) | 33.012 | — |
| exp19 | DepthPro, λ=0.01 (conservative) | 32.753 | -0.26 |
| exp20 | scheduled λ (densification 중 시작) | 31.693 | -1.32 |
| exp21 | opacity-weighted, λ=0.10 | 30.770 | -2.24 |
| **exp25** | **enlarged tau + schedule (λ:0.10→0.03)** | **32.969** | **-0.04** |
| exp26 | enlarged tau + λ=1→decay | 32.674 | -0.34 |

**컬러 코딩**: 초록(-0.00~-0.30) / 노랑(-0.30~-1.00) / 빨강(<-1.00)

---

### [Section 8] 실험 결과 분석

---

#### Slide 37 — 핵심 발견 1: Enlarged Tau가 효과적

**레이아웃**: 좌(tau 비교) / 우(결과)

**exp25 설정**:
```
alpha_n: 0.4 → 0.8  (+100%)
alpha_t: 0.9 → 1.8  (+100%)
tau_n_max: 0.30 → 0.80 m
tau_t_max: 0.60 → 2.00 m
lambda: 0.10 (iter 7k~15k) → 0.03 (iter 15k~30k)
```

**결과**: PSNR 32.969 (-0.04 dB) — **지금까지 최선**

**해석**:
- Tau 확대 → plateau 내부 surface Gaussian 비율 증가
- 더 많은 Gaussian이 "안전 구간"에 있어 loss 영향 최소화
- Lambda schedule: 초반 강하게 당기고 후반 안정화

---

#### Slide 38 — 핵심 발견 2: Loss 강화보다 Tau 설계가 중요

**레이아웃**: 3개 카드 + 결론

**exp20 (-1.32 dB)**: Scheduled λ — densification 중 강한 loss
- **실패 원인**: λ=0.10이 iter 1k-7k densification과 충돌 → Gaussian 수 감소

**exp22 (-3.10 dB)**: Exp-loss + opacity-weight
- **실패 원인**: exp 커널이 작은 D에서도 gradient 폭발 → 수렴 불안정

**exp23 (-6.36 dB)**: Adaptive pruning (d_euc > 1.5m)
- **실패 원인**: 앵커와 멀지만 정상인 Gaussian까지 제거 (threshold 너무 보수적)

**결론 강조박스**:
> "Loss 함수를 강화하거나 pruning을 추가하는 것보다,
>  plateau의 범위(tau)를 표면 구조에 맞게 정확히 설정하는 것이 더 중요하다."

---

#### Slide 39 — 현재 상태 & 남은 문제

**레이아웃**: 진행 상황 + 미해결 문제

**완료**:
- Pop1 (SLAM outlier) → camera-bound filter로 해결 (-0.16 dB 비용)
- Plateau Loss 구현 및 MPS 좌표계 정합
- exp25: PSNR -0.04 dB (거의 baseline과 동등)

**미해결**:
- Pop2 floater (Z=+2~3m) 실제 시각적 감소 미확인
- Plateau 내부 Gaussian % 여전히 ~10% (이상적으로는 40%+)
- Lambda가 강할수록 PSNR이 떨어지는 tension

---

### [Section 9] 향후 연구

---

#### Slide 40 — 관련 연구: SplatFace & CoMapGS

**레이아웃**: 2개 논문 카드

**SplatFace (CVPR 2025)**:
- Splat-to-surface distance loss: 표면(mesh) 기준 Gaussian 거리 loss
- 유사점: "plateau 밖 force" 아이디어와 동일
- 차이점: 얼굴 mesh 기준, dead-zone(gradient=0 구간) 없음 — 항상 당기는 방향
- **읽어볼 이유**: explicit distance loss의 실제 구현/효과 참고

**CoMapGS (CVPR 2025)**:
- proximity loss / proximity MLP classifier
- Gaussian이 초기 geometry(point)에 얼마나 가까운지 MLP로 예측
- covisibility(관측 신뢰도)에 따라 loss weight 차등 적용
- 유사점: "confidence-weighted attraction" 아이디어 이미 존재
- 차이점: 학습된 classifier 기반, plateau(무손실 구간) 개념 없음
- **읽어볼 이유**: sparse point confidence를 loss weight에 반영하는 접근 참고

---

#### Slide 41 — 향후 실험: Gradient Tracking 분석

**레이아웃**: 계획 다이어그램

**동기**:
> "Floater가 photometric loss로 이동하지 않는다는 것은 알지만,
>  실제로 gradient 크기가 얼마나 작은지는 아직 측정하지 않았다."

**계획**: 3DGS 학습 중 floater별 gradient 추적 도구 개발

**구현 방향**:
```python
# 각 iteration에서:
1. floater 후보 식별 (d_euc > threshold OR Z > 2m)
2. loss.backward() 이후 get_xyz.grad 캡처
3. floater vs surface Gaussian의 |grad_xyz| 비교
4. W&B에 "floater_grad_ratio" 로깅
```

**기대 분석 질문**:
- Floater의 photometric gradient가 surface Gaussian 대비 얼마나 약한가?
- Lambda를 어느 수준으로 올려야 photometric gradient를 이길 수 있는가?
- Plateau Loss gradient가 실제로 floater에 dominant하게 작용하는가?

---

#### Slide 42 — 향후 방향 종합

**레이아웃**: 단기/중기/장기 로드맵

**단기 (진행 중)**:
- exp24 결과 분석
- exp25 기반 floater 실제 감소 PLY 시각화 비교
- Gradient tracking 도구 개발

**중기**:
- SplatFace / CoMapGS 논문 review → 아이디어 통합
- Pop2 구간 전용 앵커 보강 (DepthPro 추가 키프레임, Z=2-4m 타겟)
- Tau 확대 + opacity-weight 조합 실험
- MPS confidence(dist_std)를 plateau λ 가중치로 활용

**장기**:
- Gradient tracking 결과 기반 adaptive λ 설계
- Plateau Loss와 depth prior 동시 적용 (exp12 실패 원인 분석 후 재설계)
- Floater 제거율을 직접 측정하는 새 metric 도입

---

## 디자인 가이드

### 테마
- 배경: 다크 네이비 (#0D1B2A)
- 강조: 파이어 오렌지 (#FF6B35)
- 보조: 스카이 블루 (#4ECDC4)
- 텍스트: 화이트 (#FFFFFF) / 서브 (#B0BEC5)
- 코드 블록: (#1A2332)
- 성공(초록): #66BB6A / 경고(노랑): #FFA726 / 실패(빨강): #EF5350

### PDF 임베딩 슬라이드 (Slide 9-31)
- PDF 원본 이미지를 전체 슬라이드 크기로 배치
- 상단: 슬라이드 번호 + 섹션 제목 (반투명 오버레이 배너)
- 하단: 핵심 인사이트 2-3줄 (오렌지 강조박스)
- 원본 제목/주석은 그대로 유지

### Slide 3 (PLY 렌더링) 제작
- `results/exp08_openmavis.../point_cloud/iteration_30000/point_cloud.ply`
- Open3D로 카메라 경로 내부 시점 렌더링
- floater가 보이는 각도 선택
- 별도 스크립트 필요: `scripts/render_ply_camera_view.py`

---

## 폴더 구조

```
0706_ppt/
├── outline.md              ← 이 파일
├── imgs/                   ← 생성할 이미지들
│   ├── slide03_ply_render.png     ← PLY 카메라뷰 렌더
│   └── slide36_psnr_chart.png    ← PSNR 바 차트
└── make_ppt.py             ← python-pptx 생성 스크립트
    (PDF 페이지 자동 이미지 변환 + 슬라이드 임베딩)
```
