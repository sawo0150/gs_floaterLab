# carve loss를 학술적 근거 위에 다시 세우기

> 작성 2026-09-01. 상태: **설계 문서 (코드 변경 없음).**
> 대상 코드: `VIGS-SLAM-main-integration-20260828` HEAD `2c61d0ef`

---

## 문제 제기 (출발점)

현재 causal carve의 evidence score는

```
score = transit(v) / ( transit(v) + 3.0 · terminal(v) + 1e-6 ) · min( d_anchor / 0.25 , 1 )
```

이고, 여기에 opacity를 곱해 loss를 만들고, 0.95 / 0.50 / 0.0075 같은 임계값으로
Gaussian을 지운다. 이 식은 **어떤 확률모형에서도 유도되지 않았고**, 상수들은
경험적으로 맞춘 값이며, 결과적으로 **최종 PSNR 말고는 검증 수단이 없다** —
그런데 그 PSNR은 run-to-run 노이즈(±0.24~0.33dB)와 구분이 잘 안 된다(exp65, exp69).

---

## 이 폴더의 결론 (미리)

**세 줄 요약:**

1. 현재 식은 **틀린 게 아니라 이름을 잃은 것**이다. `transit/(transit+w·terminal)`은
   점유격자 문헌의 **Beta-Bernoulli 사후 평균** 그 자체이며, 다만 사전분포·불확실성·
   관측 독립성 검증을 전부 버린 퇴화 버전이다.
2. **자유공간 carve loss는 발명할 필요가 없다.** 3DGS 렌더러가 이미
   `−log T(D) = ∫₀^D σ dt`라는 자유공간 음의 로그가능도를 정의한다. 우리가 할 일은
   지나가 버린 ray에 대해 그 적분을 causal하게 추정할 **충분통계량**을 유지하는 것뿐이다.
3. 그렇게 다시 쓰면 **튜닝 상수 13개가 자유 파라미터 1개 + 측정가능량으로** 바뀌고,
   무엇보다 **최종 PSNR을 돌리기 전에 반증할 수 있는 실험**(보정 곡선, 분류 AUC)이 생긴다.
   품질 향상보다 **이쪽이 진짜 이득**이다.

---

## 읽는 순서

| 문서 | 내용 | 언제 읽나 |
|---|---|---|
| **[01 현재 식 감사](01_current_formulation_audit.md)** | 코드에 실제로 있는 수식 + 암묵 가정 폭로. 결함 A~H 확정 | 문제를 정확히 알고 싶을 때 |
| **[02 문헌 조사](02_literature_review.md)** | 결함 A~H 각각에 대한 기존 정본. 점유격자 / 볼륨렌더링 가능도 / depth 감독 / 3DGS floater 계열 | "남들은 어떻게 했나" |
| **[03 제안 확률모형](03_probabilistic_model.md)** | **본 제안.** 하나의 생성모형 → loss와 결정규칙 유도. 3층 구조 | **핵심 문서** |
| **[04 검증 계획](04_validation_plan.md)** | P0~P5 사다리. 앞 4단계는 3DGS 학습 없이 판정 | 실행할 때 |
| **[05 구현 매핑](05_implementation_mapping.md)** | 모형의 각 항이 코드 어디로 가는가, 미확인 항목 | 착수할 때 |

---

## 제안의 뼈대 (03의 요약)

```
Layer 1  측정 가능도   지금 도착한 ray  →  정확한 NLL
                       L_free = ∫₀^{z−kσ} σ dt  = Σ_j o_j·A_j   (Gaussian 크기 자동 반영)
                       L_surf = 종료분포 KL (DS-NeRF 형태, 기댓값 depth 안 씀)
                       + inlier/outlier 혼합으로 robust

Layer 2  지도측 사후   지나간 ray       →  Beta 점유 사후
                       p_free(v) ~ Beta(α₀ + F_v/κ_v , β₀ + γ·O_v/κ_v)
                       κ_v = 유효표본수 (ray 방향 산포 S_v = Σ d dᵀ 에서)
                       → 평균 + 분산 + 진짜 확률인 임계값

Layer 3  결정          삭제/게이트      →  Bayes 위험 최소화
                       삭제 ⟺ P_j > C_del/(C_del+C_keep)     (오류율이 명시됨)
```

**현재 코드는 이 모형의 특수 케이스다** (03 §7의 R1~R8). 따라서 이건 갈아엎기가 아니라
**가정을 하나씩 푸는 작업**이고, 각 R이 독립 ablation 축이 된다.

---

## 무엇이 사라지는가

| 사라지는 상수/기제 | 대체 |
|---|---|
| `terminal_weight=3.0` | inverse sensor model에서 유도 (`γ`) |
| `surface_margin=0.20`, `margin=0.05` | `k·σ_r` (BA 공분산) |
| `anchor_tau=0.25` 감쇠항 | `O_v` 점유 증거가 정식 수행 |
| `_FISHER_QUALITY_LUT` (8192 entry, 13방향 양자화) | `S_v` 6 float — **더 싸다** |
| `prune_persistence=3` | ESS `κ_v` |
| `fisher_min`, `continuous_fisher_floor` 등 | ESS `κ_v` |
| `prune_budget_total=0.0075` + 누적 예산 회계 | Bayes 결정규칙 |
| `gate_score=0.95`의 무의미한 눈금 | 진짜 신뢰수준 |

**13개 상수 → `λ_map` 1개** (그나마도 원리적으로 1.0이며, 벗어난 정도가 근사 오차 지표).

---

## 지금 당장 할 수 있는 두 가지

이 폴더 전체를 실행하지 않고도 **오늘 시작 가능한 최소 작업**:

1. **30분짜리 측정 (05 §3):** `score_ellipsoid_support()`를 켰을 때 map() 시간이
   얼마나 느려지는가. 새 코드 없이 측정 가능하며, 이 값이 §03의 `Â_j`가
   실시간 예산 안에 들어오는지를 결정한다.
2. **반나절짜리 반증 실험 (04 P0+P1):** ray를 덤프해서 순수 numpy로
   **신뢰도 다이어그램 한 장**을 그린다. GPU도 VIGS 수정도 학습도 불필요.
   현재 `score`가 이미 잘 보정돼 있다면 → **이 제안 전체를 싸게 기각**할 수 있다.
   그게 이 순서를 고른 이유다.

---

## 기존 실험 이력과의 관계

- **exp38~44d2 (배치 carve loss):** 원본 `3dgs-custom/eval/carve_loss.py`.
  현재 causal carve는 그 4요소(soft/prune/gate/force)를 스트리밍용으로 재설계한 것이다.
  본 제안은 그 4요소를 **하나의 가능도에서 다시 유도**한다.
- **exp55 / exp57 / exp69:** 스트리밍 carve의 실측 이력. exp69에서 "floater는 일부
  줄었으나 geometry 비열등이 성립하지 않음"으로 opt-in 보존 상태.
  → [04](04_validation_plan.md) P5의 판정 기준은 이 실패를 그대로 사전 등록한 것이다.
- **exp59 (교차 장면 전이 실패):** 절대 상수를 다른 장면에 옮기면 깨진다는 직접 증거.
  → 본 제안의 "상수를 측정가능량으로" 방향이 겨냥하는 바로 그 문제.
- **exp65 M2 (rasterizer가 blending weight 미노출):** Layer 1이 부딪힐 벽과 동일.
  → [05](05_implementation_mapping.md) §1.2에서 Layer 1을 선택적/후순위로 둔 이유.

## 프로젝트 우선순위와의 관계

CLAUDE.md의 1차 목표는 **strict streaming held-out 27dB**이고,
"27dB 미달 지도에 hard carve/floater pruning을 먼저 넣지 않는다"가 명시 원칙이다.

**이 폴더는 그 원칙을 위반하지 않는다.** [04](04_validation_plan.md)의 P0~P4는
production 동작을 전혀 바꾸지 않는 오프라인 분석이며, P5에서도
`p_threshold → 1.0` 극한이 "아무것도 지우지 않음"이라 **연속적으로 후퇴 가능**하다.
carve를 켜는 결정 자체는 여전히 27dB 재현 이후의 별도 판단이다.
