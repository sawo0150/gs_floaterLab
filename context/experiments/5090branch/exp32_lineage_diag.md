# exp32_lineage_diag — 계보 및 Gradient 분리 진단 실험
- 날짜: 2026-07-11
- result dir: `results/experiments/exp32_lineage_diag`
- W&B run: (local run, W&B disabled)
- 목적: 30k 완주 후 ray-density 기반 자동 floater(Pop 2) 및 수동(SuperSplat) floater의 탄생 계보 및 gradient 히스토리(RGB vs Plateau)를 정량 비교 분석

## 설정
- `exp32` (plateau 기본 tau + λ0.01 + native anchor) 설정을 베이스라인으로 삼음.
- 학습 코드(`scene/gaussian_model.py`, `train.py`)를 수정하여 **Lineage tracking 속성** 및 **Double Backward decoupled gradient(L_rgb 및 L_plateau 개별 캡처) 누적** 기능을 탑재하고 30,000 이터레이션 완주.
- `train.py` 내 3000 step `reset_opacity` 시 non-xyz gradient가 소실되어 momentum state 유실로 터지던 버그를 긴급 픽스 (`gaussians._xyz.grad.zero_()`를 사용하여 해결).

---

## 1. 자동 분석 결과 (Ray-unseen Voxel & Opacity > 0.5)
- **명시적 floater**: 76개 (0.05%)
- **RGB (Photometric) Grad**: `1.4132e-01` vs `5.4983e-01` (비율: **`0.2570x`**)
  - *해석*: 완전히 ray가 통과하지 않는 unseen space에 박혀있어 photometric gradient를 표면 대비 **1/4 수준**으로만 매우 약하게 받았음을 확인.
- **Plateau Loss Grad**: `1.5321e-02` vs `1.5592e-03` (비율: **`9.8263x`**)
  - *해석*: 표면 대비 **약 10배** 더 강력한 복구력이 가해졌으나 30k까지 생존.
- **주범 조상**: Seed index `7015` -> 41개 floater 유발 (53.9%)

---

## 2. 수동 분석 결과 (사용자가 SuperSplat으로 직접 정밀 삭제한 결과)
- **삭제된 수동 floater**: **2,817개** (전체 가우시안 149,202개 중 **`1.89%`**)
- **남은 표면 가우시안**: 146,383개 (98.11%)

### 1) Decoupled Gradient Profile (Floater Mean vs Surface Mean)
- **RGB (Photometric) Grad**: `7.2938e-01` vs `3.2684e-01` (비율: **`2.2316x`**)
  - *해석*: 사용자가 지운 2,817개의 floater들은 카메라 시야 내에 위치하여 오차 역전파의 영향을 많이 받아 표면보다 **2.23배** 더 큰 RGB gradient를 받음.
  - **⚠ 정정 (07-11 후속 분석)**: opacity 중앙값은 **0.044** (표면 0.194), op>0.5는 2,817개 중 **48개**, op>0.3은 142개뿐. 즉 수동 floater 대부분은 "고opacity 생존자"가 아니라 **prune 임계(0.01) 바로 위에서 간신히 버티는 저opacity 먼지 무리**이며, 다수가 겹쳐 시각적 artifact로 보인 것. 이 성질이 carve loss 설계의 핵심 leverage가 됨 → [round8_carve_loss_design](../rounds/round8_carve_loss_design.md)
- **Plateau Loss Grad**: `8.1433e-04` vs `1.3975e-03` (비율: **`0.5827x`**)
  - *해석*: Plateau loss gradient를 표면 대비 **`0.58배`** 수준으로 적게 받음. 이는 사용자가 지운 가우시안들이 **실제 anchor가 있는 바닥/표면 구조물로부터 물리적으로 꽤 멀리 떨어진 Outlier 허공 영역**에 둥둥 떠 있었음을 증명함.

### 2) Plateau 영역(Boundary) 진입 비율 분석 🎯
가장 가까운 3D Anchor(SLAM 포인트 7,205개)까지의 최단 거리 $d_{\text{min}}$ 분석:
- **최소 거리**: `0.0134m` (1.3cm)
- **평균 거리**: `0.5639m` (56.4cm)
- **중간값 (Median)**: `0.5634m` (56.3cm)
- **최대 거리**: `1.3171m` (1.32m)

#### 임계값 $\tau$ 기준 내부 비율 (Inside Ratio):
- **$\tau = 0.05$m (현재 베이스라인 설정)**:
  - **Floaters Inside: `0.39%`** (2,817개 중 단 11개만 5cm 이내 존재)
  - Surface Inside: `17.19%`
  - *해석*: **수동 floater의 `99.61%`가 Plateau loss의 유효 제어 범위를 벗어난 아웃라이어 상태**였음.
- **$\tau = 0.25$m (Enlarged Tau 설정)**:
  - **Floaters Inside: `11.82%`**
  - Surface Inside: `85.80%`
- **$\tau = 0.50$m (극단적 광역 설정)**:
  - **Floaters Inside: `40.93%`**
  - Surface Inside: `96.68%`

### 3) Lineage & Densification Profile (탄생 및 계보)
- **세대(Generation) 및 증식**:
  - 평균 `7.07`대 (주로 `5.73회 Split`과 `1.34회 Clone`을 통해 분할 증식됨).
- **탄생 단계 (Birth Step Histogram)**:
  - `[11, 863, 961, 982, 0, 0]` (0-1k: 11, 1-3k: 863, 3-5k: 961, 5-7k: 982, 7-15k: 0, 15k-30k: 0)
  - *해석*: 1k step 이후 densification 기간 동안 지속적으로 대량 복제 및 분할되었으며, 특히 **3,000 ~ 7,000 step 사이의 후반부에 `69.0%`가 집중 생성**됨.

### 4) 가시성 및 관측 Profile
- **누적 관측 횟수 (accum_visibility)**: 평균 **`575.8`회**
  - *해석*: 1,303장 이미지 중 평균 575회나 카메라 뷰 프러스텀에 걸려 렌더링되면서 씬 전체의 시각적인 먼지(Artifact)로 작용했음이 뷰 카운트로 입증됨.

### 5) 주범 조상 (Top Floater Ancestors)
- **Rank 1**: Seed index **`5061`** (좌표: `[1.332, -2.148, 1.251]`) -> **282개** floater 생산 (**10.0%**)
- **Rank 2**: Seed index **`3571`** (좌표: `[0.672, -1.984, 1.011]`) -> **171개** floater 생산 (**6.1%**)
- **Rank 3**: Seed index **`5811`** (좌표: `[0.894, -2.312, 1.109]`) -> **118개** floater 생산 (**4.2%**)

---

## 3. Plateau 해결 가능성 검증 (2026-07-11, 학습 없이 분석만)

> 스크립트: `scripts/analysis/verify_plateau_capability.py` → `results/experiments/exp32_lineage_diag/plateau_capability_report.json`
> **⚠ §2-2의 inside-ratio 분석은 SLAM 7,205pts + 고정 spherical tau 기준이었음.** 실제 학습에 쓰인 field(DepthPro virtual anchor 7,108 + ellipsoidal 적응형 tau)로 재계산하면 결론이 반전된다.

**질문**: 현재 plateau loss가 수동 floater 2,817개를 원리적으로 해결할 수 있는가? → **불가능 (4중 구조적 실패)**

1. **사각지대 (지향 실패)**: 실제 field 기준 floater의 **66.2%가 plateau 안(D≤1)** → gradient가 수학적으로 0. 교차검증: inside 판정 floater의 90.4%가 30k 학습 내내 `accum_plateau_grad ≡ 0` (outside는 0%). enlarged tau(exp33 설정)는 **99.4% inside** — 사실상 완전 실명.
2. **판별 실패**: 정규화 거리 D_min의 floater vs 표면 판별 AUC = **0.511 (무작위 수준)**. D>1 기준 floater 검출 33.8% vs 표면 오검출 31.2% — λ·kernel·opacity_weight 등 어떤 증폭도 floater와 표면을 같은 비율로 때림 (exp20~22/26 PSNR 하락의 구조적 원인).
3. **작용 대상 실패**: base 설정은 opacity로의 gradient 경로가 없음 — floater를 **삭제 못 하고 이동만** 시키며, 경계(D=1)에서 gradient가 소멸해 경계에 멈춘 dust로 남음. outside floater 952개의 경계까지 gap은 p50 5.8cm에 불과 — 이동시켜봤자 시각적 artifact는 거의 그대로.
4. **타이밍 실패**: floater 100%가 densify 종료(7k) 전 출생, 65.1%는 plateau 시작(5k) 전 출생. split 생성은 RGB viewspace grad가 주도 — plateau는 출생 자체를 막을 수 없음.

**크기(λ)는 문제가 아니었음**: outside floater가 경계 도달에 필요한 λ는 p50 0.034, p90 0.18 (현행 0.01 대비 ~3–18배). Adam 이동량 상한(5k→30k lr 적분 = 3.72m) 대비 gap p90 0.20m로 물리적 도달은 쉬움. 문제는 오직 지향·판별·작용 대상.

**진단 — 신호는 있는데 tau가 죽인다**:
| 판별 기준 | AUC |
|---|---:|
| raw 유클리드 거리 → SLAM 7,205pts | **0.930** |
| raw 유클리드 거리 → DepthPro anchor | 0.876 |
| plateau 정규화 D_min (적응형 tau) | 0.511 |

per-anchor 적응형 tau(τ ∝ kNN spacing, tau_t 최대 0.6m)가 anchor 희소 지역의 plateau를 부풀려 floater가 사는 공간을 그대로 삼킴. 또한 floater는 DepthPro virtual anchor에 SLAM 포인트보다 훨씬 가깝게(median 0.325m vs 0.563m) 붙어 있음 — monodepth 기반 virtual anchor 생성이 floater 서식 공간을 일부 채워버린 것도 실명에 기여.


**최종 확인 완료**
사용자가 직접 시각적으로 인지하여 지운 2,817개의 진짜 floater들은 표면 대비 **Plateau gradient는 절반 수준(0.58x)으로 적게 받으며 허공(outlier)으로 삐져나갔고**, **RGB gradient는 2.23배나 많이 받으며 오차가 집중되었으나 소멸하지 않고 버틴 끈질긴 성질**을 띰. 이들의 대부분(69.0%)은 densification 종료 직전(3k-7k)에 split 분할을 7대 이상 겪으며 발생하였고, 상위 극소수 seed points(5061, 3571 등)가 split을 통해 대량 유발했음을 사후 정량 증명함.
