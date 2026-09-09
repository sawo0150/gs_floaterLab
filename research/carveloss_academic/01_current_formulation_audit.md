# 01 — 현재 carve loss 식의 감사(audit)

> 목적: "근본이 없다"는 문제제기를 **감정이 아니라 식 단위로** 확정한다.
> 코드에 실제로 있는 수식을 그대로 적고, 각 항이 **암묵적으로 무엇을 가정하고 있는지**를
> 드러낸다. 여기서 밝혀진 암묵 가정이 곧 [03](03_probabilistic_model.md)에서 명시적
> 확률모형으로 대체할 대상이다.
>
> 대상 코드: `VIGS-SLAM-main-integration-20260828` (HEAD `2c61d0ef`)
> - `vigs/gaussian/utils/causal_carve.py` (2243줄) — causal carve, 기본 OFF
> - `vigs/gaussian/utils/slam_utils.py:317` — frontier carve, 기본 ON

---

## 0. 지금 돌아가는 게 두 개다

혼동을 먼저 제거한다. "carve loss"라는 이름이 두 개의 완전히 다른 것에 붙어 있다.

| | frontier carve | causal carve |
|---|---|---|
| 위치 | `slam_utils.py:317` | `causal_carve.py` 전체 |
| 상태 | **기본 ON** (`carve_lambda=0.05`, `config/aria1253.yaml`) | **기본 OFF** (opt-in YAML 키) |
| 상태량 | 없음 (매 프레임 단발) | 영구 voxel field |
| 규모 | 4줄 | 2243줄 |

이 문서의 비판 대상은 주로 **causal carve**다. frontier carve는 §4에서 따로 다룬다
(짧지만 그쪽도 근거가 없기는 마찬가지고, 오히려 더 쉽게 고칠 수 있다).

---

## 1. Evidence score — 실제 식

`causal_carve.py:854-860`:

```
ρ(v)     = transit(v) / ( transit(v) + w_t · terminal(v) + ε )      # w_t = 3.0, ε = 1e-6
score(x) = ρ(v(x)) · min( d_anchor(x) / τ , 1 )                     # τ = 0.25 m
```

- `transit(v)`: voxel `v`를 **통과한** SLAM depth ray 샘플 수 (`observe()`, ray_step=0.06m로 행진)
- `terminal(v)`: voxel `v`에서 **끝난**(= 측정 표면이 거기 있었던) ray 수
- `d_anchor(x)`: 가장 가까운 SLAM anchor point까지 거리 (5-NN 평균, `distance5.mean(1)`)
- `w_t = 3.0` (`config.terminal_weight`, line 358), `τ = 0.25` (`anchor_tau`, line 359)

### 1.1 이 식은 사실 "이름 없는 알려진 추정량"이다

`ρ`를 다시 본다. Bernoulli 시행 — 각 ray 교차를 "이 voxel은 비었다(transit)" 대
"차 있다(terminal)"의 관측이라고 보면,

```
ρ = α / (α + β),   α = transit,   β = w_t · terminal
```

이건 **Beta-Bernoulli 모형의 사후 평균(posterior mean)** 그 자체다.
즉 식이 틀렸다기보다, **문헌에 이름이 있는 모형(Beta 사후 = 점유격자의 표준)의
퇴화된 특수 케이스를 이름 없이 재발명해 놓고, 그 모형이 원래 같이 주는 것들을 전부
버린 상태**다. 버려진 것이 정확히 세 가지다:

| Beta-Bernoulli가 원래 주는 것 | 현재 코드 상태 |
|---|---|
| 사전분포 Beta(α₀,β₀) — 미관측 voxel의 기본 믿음 | `ε=1e-6`으로 뭉갬. transit=terminal=0이면 score=0 (= "확실히 점유") — **미관측과 확실한 점유를 구분 못 함** |
| 사후 **분산** — 이 추정이 얼마나 못 믿을 값인지 | 전혀 안 씀. transit=1,terminal=0 (ρ=1.0)과 transit=100,terminal=0 (ρ=1.0)이 **완전히 동일 취급** |
| 관측 **독립성** 가정의 검증 | 위반됨 (§2) |

`w_t = 3.0`도 마찬가지다. 이건 자유롭게 튜닝된 상수가 아니라, 점유격자 문헌에서
**inverse sensor model의 log-odds 비**에 해당하는 물리량이다. OctoMap 기본값
(`l_occ=0.85`, `l_free=−0.4`)의 비가 약 2.1이니 `w_t=3.0`은 그 자리를 손으로 채운 값이다.
**측정할 수 있는 양을 튜닝 상수로 바꿔놓은 것**이 문제의 전형이다.

### 1.2 `min(d_anchor/τ, 1)` 항은 모형이 아니라 안전장치다

이 항의 역할은 "SLAM anchor 근처면 score를 깎아라"이다. 의도는 이해되지만
(anchor 근처 = 진짜 표면일 가능성), 이건 **evidence가 아니라 evidence에 대한 불신**이다.
확률모형에서 그런 불신은 **사전분포나 관측 노이즈**로 들어가야 하며, 사후확률에
곱하는 임의 감쇠 계수로 들어가면 결과가 더 이상 확률이 아니다 — 실제로
`ρ·min(d/τ,1)`은 어떤 확률도 아니며, 그래서 `gate_score=0.95`, `prune_score_min=0.50`,
`opacity_prox_score_min=0.50` 같은 임계값들이 **해석 불가능한 눈금 위의 숫자**가 된다.
0.95가 "95% 확신"이 아니라는 게 핵심 문제다.

---

## 2. 진짜 통계적 결함: 관측 독립성 위반

Beta-Bernoulli의 `α = transit`은 **transit 하나하나가 독립 시행**일 때만 유효하다.
그런데 우리 입력은 스트리밍 SLAM 카메라다:

- 30fps로 거의 같은 위치에서 같은 voxel을 수십 번 관통한다.
- 같은 keyframe 안 인접 픽셀들의 ray도 거의 평행하다.
- 즉 `transit=100`은 **독립 관측 100개가 아니라, 상관된 관측 100개 ≈ 유효 관측 3~5개**다.

결과: `ρ`는 체계적으로 **과신(over-confident)**한다. 사후 분산이 실제보다 수십 배
작게 나온다 — 그런데 §1.1에서 봤듯 분산은 애초에 쓰이지도 않으니, 과신은 조용히
score를 1.0에 붙여놓는 방식으로만 드러난다.

**그리고 코드는 이미 이 문제를 알고 있다 — 다만 임시방편으로 두 번 우회한다:**

### 2.1 우회 1 — Fisher quality LUT (`causal_carve.py:52-71`)

```python
_FISHER_LINES = [13개 고정 방향]              # 방향을 13개 비트로 양자화
factors  = [I − d·dᵀ for d in _FISHER_LINES]
info     = factors[관측된 방향들].sum()
quality  = λ_min(info) / (trace(info)/3)      # 조건수 비슷한 것
```

의미: "이 voxel을 여러 **방향**에서 봤는가". 이게 바로 상관 보정 시도다.
그러나 (a) 방향을 13개 고정 직선으로 양자화하고 (b) 비트마스크로 유무만 보고
(c) 결과를 `[0,1]`로 clip해서 score에 곱하는 순간, 이건 더 이상 Fisher 정보량이 아니라
**"Fisher처럼 생긴 가중치"**다. 진짜 Fisher 정보 행렬은 그냥 `Σ dᵢdᵢᵀ`를 6개 float로
누적하면 정확히 얻을 수 있는데, 양자화할 이유가 없다.

### 2.2 우회 2 — `prune_persistence` (`causal_carve.py:379, 2007`)

```python
required = prune_persistence * (2.0 − quality)      # prune_persistence = 3
```

"score가 높아도 3번(품질 나쁘면 최대 6번)은 반복 확인하고 지워라". 이건
**유효표본수(effective sample size)를 손으로 3이라고 박아 넣은 것**이다.
§2의 상관 문제에 대한 정확한 정공법이 ESS 보정인데, 그걸 상수로 대체했다.

> **감사 결론 1:** Fisher LUT와 prune_persistence는 독립적인 두 개의 아이디어가 아니라,
> **하나의 통계적 결함(상관 관측)에 대한 두 개의 임시 패치**다. 모형을 제대로 세우면
> 둘 다 하나의 항(ESS로 보정된 Beta 사후)으로 흡수된다.

---

## 3. Loss / 결정 규칙 — 실제 식

### 3.1 Soft opacity 압력 (`add_gradient`, line ~1908)

주석에 명시된 대로 이 gradient는

```
L_soft = λ_soft · mean_j ( score_j · σ(o_j) )      # λ_soft = 0.02, σ = sigmoid
∂L/∂o_j = λ_soft · score_j · σ(o_j)(1−σ(o_j)) / N
```

즉 **score로 가중된 opacity L1 페널티**. MAP 관점에서 보면 opacity에 대한
Laplace 사전분포이므로 완전히 근거가 없지는 않다. 문제는 **가중치가 왜 score여야
하는지**에 대한 유도가 없다는 것이다. 뒤에서 보겠지만(03 §3), 볼륨 렌더링
가능도로부터 유도하면 올바른 가중치는 `score`가 아니라
**"이 Gaussian이 자유공간 ray들에 기여한 광학두께의 기댓값"**이고, 그건
Gaussian 자신의 scale/방향에 의존한다. 현재 식은 그 의존성을 통째로 버렸다 —
그래서 **큰 splat과 작은 splat이 같은 score면 같은 압력**을 받는다.
(exp69에서 관측된 giant-splat 관련 실패 모드와 무관하지 않다.)

### 3.2 Budget prune (`maybe_budget_prune`, line ~1966)

```
contribution_j = opacity_j · scale_mid_j · scale_max_j · n_obs_j
누적 기여도 상위부터 지우되 Σ contribution ≤ prune_budget_total (= 0.0075)
조건: score_j > 0.50, 그리고 §2.2의 persistence 횟수 충족
```

`prune_budget_total = 0.0075` = "전체 시각적 기여도의 0.75%까지만 지워도 된다".
이건 배치 트랙 exp40에서 **경험적으로 안전했던 숫자**를 그대로 가져온 것이다.
문제:

- 0.75%는 **어떤 장면에서, 어떤 floater 비율에서 안전한 값인지에 대한 진술이 없다.**
  exp59에서 이미 겪은 실패 패턴(절대 상수를 다른 장면에 옮기면 깨짐)과 정확히 같은 형태다.
- 삭제는 **되돌릴 수 없는 결정**인데, 그 결정에 **오류율(false deletion rate)이
  명시돼 있지 않다.** "0.75%만 지운다"는 위험 통제가 아니라 위험 **한도**일 뿐이다.
  진짜 표면을 몇 % 지우는지는 아무도 모른다.

### 3.3 Birth gate (`gate_newborn`, line ~1948)

```
newborn ∧ (score > 0.95) → 즉시 삭제
```

§1.2에서 말했듯 `0.95`는 확률이 아니다. 따라서 이 게이트의 동작점은
**해석 불가능**하고, 장면이 바뀌면 같은 0.95가 전혀 다른 엄격도가 된다.

---

## 4. frontier carve (기본 ON) 도 같은 병을 앓는다

`slam_utils.py:317`:

```
L_frontier = mean( relu( D_gt − D_render − margin ) ),   margin = 0.05,  λ = 0.05
```

"렌더 depth가 tracked depth보다 5cm 이상 카메라 쪽이면 벌점". 한쪽 방향만 보는
hinge loss다. 이 식의 암묵 가정:

1. `D_gt`(BA-refined tracked depth)는 **노이즈가 없다** — hinge에 노이즈 모형이 없다.
   실제로는 monocular DROID depth라 상대오차가 크고 거리에 따라 커진다.
2. 오차 척도가 **거리에 무관하게 5cm 상수**다. 스테레오/depth 센서 오차는
   `σ ∝ z²`인데 이걸 무시한다. → 가까운 곳에선 너무 느슨하고 먼 곳에선 너무 빡빡하다.
3. `relu`는 **outlier에 선형으로 무한 반응**한다. depth outlier 한 픽셀이 무한정
   당길 수 있다 → robust 추정이 아니다.
4. `D_render`는 alpha-composited **기댓값 depth**다. 다봉(multi-modal) 분포에서
   기댓값은 어느 mode도 아니므로, floater가 있으면 기댓값이 중간에 뜨고 hinge는
   **floater가 아니라 진짜 표면까지 같이** 민다.

4번이 특히 중요하다. 이건 DS-NeRF 계열이 **기댓값 depth의 L1 대신 ray termination
분포에 대한 KL을 쓰는 이유** 그 자체다([02](02_literature_review.md) §3).

---

## 5. 감사 요약 — 고칠 목록

| # | 결함 | 현재 | 대체될 곳 |
|---|---|---|---|
| A | 사전분포 없음 → 미관측 ≠ 점유 구분 불가 | `ε=1e-6` | 03 §2 Beta 사전 |
| B | 불확실성 미사용 → 1회 관측과 100회 관측 동일 | `ρ`만 사용 | 03 §2 사후 분산 |
| C | 관측 독립성 위반 → 과신 | Fisher LUT + persistence 패치 | 03 §2.3 ESS 보정 |
| D | `w_t=3.0`이 측정가능량인데 상수 | 하드코딩 | 03 §2.2 inverse sensor model |
| E | score가 확률이 아님 → 임계값 0.95/0.50 해석 불가 | anchor 감쇠 곱 | 03 §2 (사후확률로 복원) |
| F | opacity 압력 가중치가 미유도, Gaussian 크기 무시 | `score·σ(o)` | 03 §3 볼륨 렌더링 NLL |
| G | 삭제 결정에 오류율 없음, 예산 상수는 장면 의존 | `0.0075` top-K | 03 §4 Bayes 위험 |
| H | frontier carve: 노이즈/거리의존/robust/다봉 전부 무시 | hinge 5cm | 03 §3.2 (동일 가능도로 흡수) |

**그리고 전부를 관통하는 메타 결함:** 위 A~H 어느 것도 **틀렸음을 보일 수 있는 형태로
쓰여 있지 않다.** 지금 검증 방법은 "끝까지 돌려서 PSNR이 오르나 본다" 하나뿐이고,
그건 exp69에서 봤듯 노이즈와 구분이 안 된다. 확률모형으로 다시 쓰는 진짜 이득은
품질 향상보다도 **중간 단계에서 검증 가능해진다**는 데 있다 —
[04](04_validation_plan.md)가 그 부분이다.

---

다음: [02 — 문헌 조사](02_literature_review.md)
