# 03 — 제안: 하나의 생성모형에서 carve loss를 유도한다

> 이 문서가 본 제안이다. [01](01_current_formulation_audit.md)의 결함 A~H를
> **개별적으로 패치하지 않고**, 하나의 생성모형을 세운 뒤 거기서 loss와 결정규칙을
> **유도**한다. 그 결과 현재 코드의 항들이 대부분 **이 모형의 퇴화된 특수 케이스**로
> 다시 나타난다(§7) — 즉 갈아엎는 게 아니라 **일반화하고 상수를 측정가능량으로
> 되돌리는** 작업이다.

---

## 0. 한 문장 요약

> **"자유공간 carve loss는 새로 발명할 필요가 없다. 3DGS 렌더러 자신이 이미
> `−log T(D) = ∫₀^D σ dt` 라는 자유공간 음의 로그가능도를 정의하고 있고, 우리가 할 일은
> 지나가 버린 ray들에 대해 그 적분을 causal하게 추정할 수 있는 충분통계량을
> 점유격자 사후분포로 유지하는 것뿐이다."**

3층으로 나뉜다:

```
Layer 1  측정 가능도   : 지금 도착한 ray  →  정확한 NLL (근사 없음)          [§2]
Layer 2  지도측 사후   : 지나간 ray       →  Beta 점유 사후 + ESS 보정        [§3]
Layer 3  결정          : 삭제/게이트      →  Bayes 위험 최소화 (오류율 명시)  [§6]
```

현재 구현은 Layer 1이 통째로 없고(frontier carve의 hinge가 그 자리의 조악한 대역),
Layer 2는 사후분포 없이 점추정만 있고, Layer 3는 없다(예산 상수로 대체).

---

## 1. 생성모형

관측: keyframe `i`의 픽셀 `p`가 하나의 ray `r=(o_r, d_r)`와 depth 측정 `z_r`를 준다.

**확률변수와 그 모형:**

| 기호 | 의미 | 모형 |
|---|---|---|
| `σ(x)` | 3DGS 밀도장 = `Σ_j o_j G_j(x)` | 추정 대상 (Gaussian 파라미터) |
| `z_r` | ray `r`의 측정 깊이 | inlier/outlier 혼합 (아래) |
| `σ_r` | 그 측정의 표준편차 | **BA 공분산에서 가져옴** (상수 아님) |
| `π_r` | ray `r`이 outlier일 확률 | Beta 사전, 온라인 추정 |
| `m_v ∈ {free, occ}` | voxel `v`의 점유 | Beta-Bernoulli 사후 |

깊이 측정의 가능도 (Vogiatzis-Hernández 형태, [02](02_literature_review.md) §3.4):

```
p(z_r | σ(·)) = (1 − π_r) · ∫ h_r(t) N(t; z_r, σ_r²) dt   +   π_r · U(t; t_min, t_max)
h_r(t) = T_r(t) σ_r(t),   T_r(t) = exp(−∫₀ᵗ σ(x_r(s)) ds)
```

`h_r`은 3DGS 렌더러가 이미 계산하는 ray 종료 분포다. **모든 loss가 이 한 줄에서 나온다.**

---

## 2. Layer 1 — 지금 도착한 ray의 정확한 loss

가능도의 음의 로그를 두 항으로 분해한다(outlier 항은 §2.3에서 처리).

### 2.1 자유공간 항 = 표면 앞 광학두께

"ray가 표면까지 막히지 않고 도달했다"는 사건의 확률은 정확히 `T_r(z_r)`이고

```
L_free(r) = −log T_r(z_r − Δ_r) = ∫₀^{z_r − Δ_r} σ(x_r(t)) dt ,      Δ_r = k·σ_r
```

여기서 `Δ_r = k·σ_r`(예: k=3)가 **거리 의존 안전 마진**이다. 현재 코드의
`surface_margin = 0.20 m` 고정 상수(그리고 frontier carve의 `margin=0.05 m`)가
바로 이 자리를 상수로 채운 것이다 — **BA가 σ_r을 주므로 상수일 이유가 없다.**

3DGS를 대입하면 `σ = Σ_j o_j G_j`이므로 **loss가 Gaussian별로 정확히 분해된다**:

```
L_free = Σ_r L_free(r) = Σ_j o_j · A_j ,
A_j := Σ_r ∫₀^{z_r−Δ_r} G_j(x_r(t)) dt        ← "Gaussian j가 자유공간에 노출된 총 광학 단면"
```

따라서

```
∂L_free / ∂o_j = A_j                                   (완전히 정확)
```

> **결함 F 해결.** 현재 코드는 `∂L/∂o_j ∝ score_j` 였다. 올바른 가중치는 `A_j`이고,
> `A_j`는 **Gaussian의 크기·방향·자유공간과의 겹침**을 자동으로 포함한다.
> 같은 위치의 거대 splat과 미세 splat이 같은 압력을 받던 문제가 유도 수준에서 사라진다.
> (exp69의 giant-splat 실패 모드와 직접 관련된 축이다.)

또한 `A_j`는 **광학두께 단위**라서 색 loss와 물리적으로 같은 축 위에 있다.
`λ_soft = 0.02` 같은 값이 "왜 하필 0.02인가"를 벗어나, **λ는 이제 단순히
`(픽셀 photometric NLL) vs (기하 NLL)`의 노이즈 비율**이 된다.

### 2.2 표면 항 = 종료 분포의 KL (frontier carve 대체)

DS-NeRF 형태([02](02_literature_review.md) §3.1)를 그대로 쓴다:

```
L_surf(r) = − Σ_k log h_r(t_k) · N(t_k; z_r, σ_r²) · Δt_k
```

이건 **기댓값 depth를 쓰지 않으므로** [01 §4]의 4번 문제(다봉 분포에서 floater 때문에
기댓값이 떠서 진짜 표면까지 밀어버림)가 구조적으로 없다.

> **결함 H 해결.** hinge `relu(D_gt − D_render − 0.05)` → 종료분포 KL.
> 그리고 `L_free`와 `L_surf`는 **같은 가능도의 두 항**이므로 상대 가중치가
> 자유 파라미터가 아니다. 현재 `carve_lambda=0.05`와 depth L1의 `×5`가 서로
> 독립으로 튜닝되던 것이 하나로 묶인다.

### 2.3 Outlier robustness

혼합 가능도의 NLL은 자동으로 **soft redescending** 형태가 된다:

```
w_r = (1−π_r)·L_inlier(r) / [ (1−π_r)·L_inlier(r) + π_r·U ]      (EM의 responsibility)
L(r) ← w_r · [ L_free(r) + L_surf(r) ]
```

`w_r`은 EM E-step이며, outlier ray의 영향이 **선형이 아니라 포화**한다.
현재 hinge는 outlier 하나가 무한정 당길 수 있었다([01 §4] 3번).
`π_r`은 keyframe별로 온라인 갱신한다(Beta 사전, 폐형).

---

## 3. Layer 2 — 지나간 ray를 위한 충분통계량

Layer 1은 정확하지만 **지금 렌더 중인 ray에만** 적용 가능하다. 스트리밍에서는
과거 ray를 다시 못 본다 — causal carve가 voxel field를 만든 이유가 이것이고,
그 동기 자체는 **옳다**. 문제는 그 field에 무엇을 담느냐였다.

### 3.1 담아야 할 것: `A_j`의 causal 추정량

`A_j = Σ_r ∫ G_j dt`를 voxel 구적법으로 쪼개면

```
A_j ≈ Σ_v G_j(x_v) · Φ_v · Vol(v) ,
Φ_v := (voxel v를 지나간 자유공간 ray 교차 밀도)
```

**여기서 결정적인 관찰:** `transit(v)`는 임의 휴리스틱이 아니라 **`Φ_v`의 구적
추정량 그 자체**다(ray_step으로 행진하며 세는 게 곧 선적분의 Riemann 합).
즉 현재 코드의 분자는 원래 맞는 물건이었다.

**틀린 것은 분모다.** 정확한 유도에서 `terminal(v)`는 **분모에 나타나지 않는다** —
적분이 애초에 `z_r − Δ_r`에서 멈추므로 표면과 그 너머는 합에 들어오지 않는다.
`ρ = transit/(transit + w·terminal)`이라는 비율은
**"per-ray 구간 적분을 안 하기 때문에 사후적으로 표면을 걸러내려는 대용품"**이었다.

> **결함 D 해결.** `terminal_weight = 3.0`은 튜닝할 필요가 없어진다.
> 그 자리는 `Δ_r = k σ_r`라는 **측정 노이즈**가 대신한다.

### 3.2 그래도 terminal이 필요한 곳: 점유 사후

`terminal`이 사라지는 건 **loss 가중치**에서다. 여전히 필요한 곳이 있다:
"이 voxel의 자유 판정을 얼마나 믿는가"(Layer 3의 삭제 결정). 여기서
점유격자 정본([02](02_literature_review.md) §1)을 쓴다.

노이즈를 반영한 **연속(soft) 카운트**로 누적한다 — 하드 분류가 아니다:

```
F_v = Σ_r ∫_{v}  Pr[ t < z_r − Δ_r ]  dt        (자유 증거, ≈ 기존 transit의 soft판)
O_v = Σ_r ∫_{v}  N(t; z_r, σ_r²)      dt        (점유 증거, ≈ 기존 terminal의 soft판)
```

Beta 사후:

```
p_free(v) ~ Beta( α_v , β_v ),
α_v = α₀ + F_v / κ_v ,      β_v = β₀ + γ · O_v / κ_v
```

- `α₀, β₀`: 사전분포. 미관측 voxel은 `Beta(α₀,β₀)` = **"모름"**이지
  "확실히 점유"가 아니다. → **결함 A 해결.**
- `γ`: inverse sensor model에서 나오는 log-odds 비. OctoMap 기본값 대응 ≈2.1이며,
  **깊이 노이즈 모형과 outlier율 `π`에서 유도 가능**하다. → **결함 D 해결(2).**
- `κ_v`: 유효표본수 보정 계수. 아래 §3.3.

이제 사후 **평균과 분산이 둘 다 있다**:

```
E[p_free] = α/(α+β) ,      Var[p_free] = αβ / ((α+β)²(α+β+1))
```

→ **결함 B 해결.** `transit=1`(α=1)과 `transit=100`(α=100)이 평균은 같아도
분산이 100배 다르다. 현재 코드는 이 둘을 완전히 동일 취급했다.

### 3.3 ESS 보정 κ — Fisher LUT와 persistence의 통합

[01 §2]에서 확정한 진짜 결함: 30fps 카메라의 ray는 독립이 아니다.
정공법은 voxel별로 **ray 방향 산포 행렬**을 누적하는 것이다 (대칭 3×3 = float 6개):

```
S_v = Σ_r d_r d_rᵀ            (누적, O(1) 갱신)
```

`S_v`의 고유값 `λ₁≥λ₂≥λ₃`가 그 voxel을 본 **방향 다양성**을 정확히 기술한다.
한 방향에서만 본 voxel은 `λ₂,λ₃ ≈ 0`이다. 유효표본수를

```
κ_v = n_v / ESS_v ,    ESS_v = f( λ(S_v) )        예: ESS_v = trace(S_v)² / ‖S_v‖_F²  (참여수 비)
```

로 두면, **한 방향 100회 관측은 ESS≈1**로 자동 축소된다.

> **결함 C 해결, 그리고 두 휴리스틱의 흡수.**
> - `_FISHER_QUALITY_LUT`(13개 직선으로 방향 양자화, 8192-entry 테이블)
>   → `S_v` 6 float. **양자화 없음, 테이블 없음, 더 싸다.**
> - `prune_persistence = 3` ("3번은 반복 확인하고 지워라")
>   → ESS가 그 역할을 한다. 상수 3을 박을 필요가 없다.
>
> 즉 [01 §2]에서 "하나의 결함에 대한 두 개의 임시 패치"라고 진단한 것이
> 실제로 하나의 항으로 합쳐진다.

### 3.4 loss 가중치 복원

Layer 1의 `A_j`를 Layer 2 통계량으로 추정한다:

```
Â_j = Σ_v  G_j(x_v) · Vol(v) · F_v/κ_v · Pr[ p_free(v) > p* ]
                     └──── 기존 score_ellipsoid_support가 이미 하는 밀도 가중 ────┘
```

`Pr[p_free(v) > p*]`는 Beta 꼬리확률(정규화 불완전 베타 함수)로 **폐형**이며,
**진짜 확률이다.** 따라서 `p*`는 해석 가능한 눈금이 된다.

> **결함 E 해결.** `gate_score = 0.95`가 드디어 "95% 신뢰수준"을 뜻하게 된다.
> 현재의 `0.95`는 `ρ·min(d_anchor/0.25, 1)`이라는 **어떤 확률도 아닌 양**의 눈금이었다.
>
> 부수적으로 `min(d_anchor/τ, 1)` 감쇠항([01 §1.2])은 **삭제된다** — 그 항이 하던
> "anchor 근처는 못 믿겠다"는 역할은 이제 `O_v`(그 근처의 점유 증거)가
> 정식으로 수행한다.

**구현상 희소식:** 밀도 가중 구적(`Σ G_j(x_v)·(...)`)은 이미
`causal_carve.py:758 score_ellipsoid_support()`에 존재한다. 즉 **가장 비싼 부품은
이미 만들어져 있고**, 현재는 그게 기본 경로가 아닐 뿐이다.

---

## 4. 두 층을 잇는 항등식

Layer 1(정확)과 Layer 2(추정)가 같은 것을 재는지 확인해 둔다. 로그 오즈에서

```
l_v ← l_v + Δl_r(v) − l₀          (베이즈 갱신, 덧셈)
```

이고, `Δl_r(v)`가 inverse sensor model이다. 한편 Layer 1의 자유공간 NLL은
ray를 따르는 선적분의 합이다. 두 형태가 일치하는 조건은
**"inverse sensor model이 forward 모형(§1의 혼합 가능도)에서 유도된 것"**일 때이며,
이건 점유격자 문헌의 알려진 결과다(그리고 MRFMap 같은 forward-model 계열이
정확히 이 근사 오차를 지적한 지점이다).

**실무적 함의:** 우리는 `Δl_r(v)`를 손으로 고르지 않는다. §1의 `σ_r, π_r`에서
유도한다. **자유 파라미터가 사라지는 게 이 모형의 핵심 이득이다.**

---

## 5. 최종 목적함수

```
L = L_photo
  + Σ_r w_r [ L_free(r) + L_surf(r) ]            ← Layer 1: 현재 렌더 중인 ray (정확)
  + λ_map · Σ_j o_j · Â_j                        ← Layer 2: 지나간 ray (causal 추정)
```

- `w_r`: outlier responsibility (§2.3), EM으로 자동.
- `λ_map`: **유일하게 남는 자유 파라미터**. 그나마도 "Layer 2 추정량이 Layer 1 대비
  얼마나 편향됐는가"라서, §4의 일치성 검사로 **캘리브레이션할 수 있다**
  (04 실험 P2). 원리적으로는 1.0이 옳고, 1.0에서 벗어나는 정도가 곧 근사 오차 지표다.

현재 코드가 독립 튜닝하던 상수들과 비교:
`carve_lambda=0.05`, `terminal_weight=3.0`, `anchor_tau=0.25`, `surface_margin=0.20`,
`margin=0.05`, `lambda_soft=0.02`, `gate_score=0.95`, `score_min=0.50`,
`prune_score_min=0.50`, `prune_budget_total=0.0075`, `prune_persistence=3`,
`fisher_min=0.10`, `continuous_fisher_floor=0.25` → **13개가 `λ_map` 1개 + 측정량으로.**

---

## 6. Layer 3 — 삭제 결정을 Bayes 위험으로

삭제는 **되돌릴 수 없다**. 되돌릴 수 없는 결정에는 오류율이 붙어야 한다.

Gaussian `j`가 floater일 사후확률을, 그 support 위의 voxel 사후를 모아 계산한다:

```
P_j := Pr[ j is floater ]  =  ∫ G_j(x) Pr[p_free(x) > p*] dx  /  ∫ G_j(x) dx
```

비용을 둔다:
- `C_del` = **진짜 표면을 지웠을 때의 손해** (held-out PSNR 하락)
- `C_keep` = **floater를 남겼을 때의 손해** (floater 지표 악화)

기대 손실 최소화 규칙:

```
삭제한다  ⟺  P_j · C_keep  >  (1 − P_j) · C_del
          ⟺  P_j  >  C_del / (C_del + C_keep)  =:  p_threshold
```

> **결함 G 해결.** `prune_budget_total = 0.0075`(장면 의존 상수, exp59가 이미
> 데인 형태)가 **비용비 하나**로 대체된다. 그리고 `C_del`, `C_keep`은
> **실측 가능하다**: 무작위 Gaussian N개를 지우고 held-out PSNR 하락을 재면 `C_del`,
> 라벨된 floater를 지우고 얻는 이득을 재면 `C_keep`. → 04 실험 P4.
>
> 부수 효과: birth gate(§01 3.3)와 budget prune(§01 3.2)이 **같은 규칙의 두 적용
> 시점**이 된다. 지금은 서로 다른 임계값(0.95 / 0.50+예산)을 쓰는 별개 기제다.

**보수성 옵션:** `P_j`의 사후 하한(신용구간)을 쓰면 "95% 확신할 때만 삭제"라는
명시적 false-deletion 제어가 된다. CLAUDE.md의 "27dB 미달 지도에 hard carve를 먼저
넣지 않는다" 원칙과도 잘 맞는다 — **`p_threshold`를 1.0에 가깝게 두면 자동으로
아무것도 안 지우는 안전 모드**가 되고, 이건 별도 플래그가 아니라 같은 규칙의 극한이다.

---

## 7. 환원(reduction): 현재 식은 이 모형의 특수 케이스다

이게 이 제안의 **위험을 낮추는 핵심 논거**다. 아래 가정들을 차례로 넣으면
제안 모형이 현재 코드로 정확히 환원된다:

| # | 가정 | 결과 |
|---|---|---|
| R1 | `Δ_r = k σ_r` → 상수 0.20m | `surface_margin` |
| R2 | soft 카운트 `F,O` → 하드 카운트 | `transit`, `terminal` |
| R3 | `κ_v = 1` (관측 독립 가정) | ESS 보정 소멸 → Fisher LUT/persistence 패치가 필요해짐 |
| R4 | `α₀=β₀=0` | `ε=1e-6`, 미관측=점유 |
| R5 | 꼬리확률 `Pr[p>p*]` → 사후평균 `α/(α+β)` | `ρ = transit/(transit+γ·terminal)` |
| R6 | `Â_j`의 밀도 가중 `G_j` → 중심 delta | `score_j` (크기 무관) |
| R7 | Layer 1 생략, 표면항을 hinge로 | frontier carve |
| R8 | Bayes 위험 → 전역 예산 top-K | `prune_budget_total` |

> **따라서 이건 "기존 걸 버리고 새로 짜기"가 아니라 "R1~R8을 하나씩 푸는 것"이다.**
> 각 R은 **독립적으로 켜고 끌 수 있는 ablation 축**이고, 각각이 [04](04_validation_plan.md)에서
> **개별로 반증 가능한 예측**을 만든다. 이 프로젝트의 memory에 남은 교훈
> ("축 하나씩 진행", "미계측 항목은 실험으로 검증")과 구조가 정확히 맞는다.

---

## 8. 상수 → 측정가능량 대응표

| 현재 상수 | 값 | 대체 | 어떻게 얻나 |
|---|---|---|---|
| `terminal_weight` | 3.0 | `γ` (inverse sensor log-odds 비) | `σ_r, π_r`에서 유도 |
| `surface_margin` | 0.20 m | `k·σ_r` | BA 공분산 |
| `margin` (frontier) | 0.05 m | 동상 | BA 공분산 |
| `anchor_tau` | 0.25 m | (삭제) | `O_v`가 역할 대체 |
| `gate_score` | 0.95 | `p*` + 신용수준 | 확률로 해석됨 |
| `score_min`/`prune_score_min` | 0.50 | `p_threshold` | `C_del/C_keep` 실측 |
| `prune_budget_total` | 0.0075 | (삭제) | Bayes 규칙이 대체 |
| `prune_persistence` | 3 | (삭제) | ESS `κ_v` |
| `fisher_min`, `continuous_fisher_floor` | 0.10, 0.25 | (삭제) | ESS `κ_v` |
| `_FISHER_QUALITY_LUT` | 8192 entry | `S_v` (6 float/voxel) | 누적 |
| `lambda_soft`, `carve_lambda` | 0.02, 0.05 | `λ_map` 1개 | §4 일치성으로 캘리브레이션 |

---

## 9. 실시간 예산 (기각 사유가 되지 않도록)

이 프로젝트의 1차 제약은 strict 1.5× 실시간이므로, 비용을 미리 따진다.

| 항목 | 현재 | 제안 | 판정 |
|---|---|---|---|
| voxel당 메모리 | transit+terminal+방향 비트마스크 ≈ 3 word | `F,O` + `S_v`(6) ≈ 8 word | 증가하지만 sparse dict라 절대량 작음 |
| ray 누적 | 행진하며 counter++ | 행진하며 soft weight 누적 + `d dᵀ` 가산 | **같은 패스**, 상수배 |
| 방향 품질 | 8192-entry LUT 조회 | `S_v` 고유값 (3×3 폐형) | **오히려 단순** |
| score | 나눗셈 1회 | Beta 꼬리확률 | LUT 또는 근사식 필요 (2D 테이블) |
| `Â_j` | 중심 조회 | 밀도 가중 구적 | **가장 비쌈** — 그러나 `score_ellipsoid_support()`로 이미 구현·측정 가능 |
| Layer 1 | 없음 | ray별 KL (렌더 중 계산) | DS-NeRF와 동급, 렌더 패스에 흡수 가능 |

**가장 큰 비용은 Layer 1(§2)이 아니라 `Â_j`의 밀도 가중**이며, 이건 이미 코드에 있다.
그리고 이 프로젝트는 exp55~56에서 visible-lazy refresh / 예산제 점진 갱신 인프라를
이미 만들어 놨다 — **그 인프라는 그대로 재사용된다** (무엇을 언제 갱신할지는
안 바뀌고, 각 항목이 담는 수치만 바뀐다).

---

## 10. 이 모형이 하는 반증 가능한 예측

모형의 값어치는 "그럴듯함"이 아니라 **틀릴 수 있음**에 있다. 아래는 전부
**최종 PSNR을 돌리지 않고도** 확인 가능한 예측이다 —
[04](04_validation_plan.md)에서 실험으로 전개한다.

- **E1 (보정, calibration).** 현재 `score`는 확률이라 주장한 적 없지만 임계값처럼
  쓰인다. 제안 사후확률은 **보정되어야 한다**: `P(free)=0.8`로 예측한 voxel 집단에서
  held-out ray로 재면 실제 자유 비율이 0.8이어야 한다. → **신뢰도 다이어그램으로 직접 검증.**
- **E2 (과신).** `κ_v=1`(R3)로 두면 E1의 곡선이 **대각선 위로 체계적으로 벗어난다**
  (과신). ESS 보정을 켜면 대각선 쪽으로 이동해야 한다. 안 움직이면 **결함 C 진단이 틀린 것.**
- **E3 (분류 성능).** 우리는 이미 수동 라벨 floater GT를 갖고 있다(carve score AUC 0.98 기록).
  제안 사후확률의 AUC가 현재 `score`의 AUC보다 **높거나 최소한 같아야 한다.**
  낮으면 이 제안은 그 자리에서 기각이다.
- **E4 (크기 의존).** `Â_j`가 `score_j`를 대체하면, **큰 splat이 받는 압력이
  체계적으로 커져야 한다.** 커지지 않으면 §2.1 유도가 코드에 제대로 반영되지 않은 것.
- **E5 (비용비).** `C_del/C_keep`이 실측되면, 현재 `prune_budget_total=0.0075`가
  **어떤 `p_threshold`에 대응하는지 역산된다.** 그 값이 0.5 근처면 현재 예산은
  우연히 합리적이었던 것이고, 극단이면 현재 설정이 체계적으로 편향돼 있었다는 뜻이다.
  **어느 쪽이든 지금은 모른다는 게 문제다.**

---

다음: [04 — 검증 계획](04_validation_plan.md) · [05 — 구현 매핑](05_implementation_mapping.md)
