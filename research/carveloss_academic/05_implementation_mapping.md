# 05 — 구현 매핑: 모형의 각 항이 코드 어디로 가는가

> [03](03_probabilistic_model.md)이 수식이라면, 이 문서는 그 수식이 앉을 자리다.
> **아직 코드를 쓰지 않았다** — 이 문서는 "어디를 건드려야 하는가"의 지도이며,
> [04](04_validation_plan.md)의 P0~P5를 실행할 때 참조한다.
>
> 대상: `VIGS-SLAM-main-integration-20260828` HEAD `2c61d0ef`

---

## 0. 좋은 소식 먼저 — 인프라의 70%는 이미 있다

이 제안은 새 서브시스템을 만들지 않는다. `causal_carve.py`의 **골격은 그대로 두고
각 슬롯이 담는 수치를 바꾼다.** 특히 다음은 재사용된다:

| 기존 자산 | 재사용 여부 | 비고 |
|---|---|---|
| sparse voxel dict + 21bit key packing (`_encode_voxels`) | **그대로** | 자료구조 변경 없음 |
| `observe()`의 ray 행진 (ray_step=0.06) | **그대로** (누적값만 변경) | 같은 패스 |
| `score_ellipsoid_support()` 밀도 가중 구적 (line 758) | **승격** | §03의 `Â_j`가 정확히 이것 |
| `visible_lazy_refresh` 점진 갱신 | **그대로** | 무엇을 갱신할지는 불변 |
| PGBA pending queue, 안정 ID 관리 | **그대로** | |
| `add_gradient()`의 수동 gradient 주입 | **그대로** (가중치만 변경) | 실시간에 중요한 최적화 |
| `maybe_budget_prune()`의 이벤트 클록 | **골격 유지, 규칙 교체** | |

**삭제되는 것:** `_FISHER_QUALITY_LUT`(line 52-71, 8192 entry), `anchor_tau` 감쇠,
`prune_persistence`, `fisher_min` / `continuous_fisher_floor` / `soft_fisher_min` /
`gate_fisher_min`, `prune_budget_total` / `opacity_prox_budget_total`.

---

## 1. 항 → 코드 위치 대응

### 1.1 Layer 2 통계량 (`CausalCarveField`)

| 모형 항 (§03) | 현재 코드 | 변경 |
|---|---|---|
| `F_v` (soft 자유 카운트) | `self._transit` dict, `observe()` L483-510 | 하드 count++ → `Pr[t < z_r − kσ_r]` 가중 누적 |
| `O_v` (soft 점유 카운트) | `self._terminal` | 하드 → `N(t; z_r, σ_r²)` 가중 |
| `S_v = Σ d dᵀ` (ESS용) | `_direction_bins()` + LUT | **신규**: voxel당 float 6개 누적, 방향 양자화 제거 |
| `Δ_r = k·σ_r` | `surface_margin=0.20` 상수 | ray별 값 — **`observe()` 시그니처에 `sigma` 추가 필요** |
| Beta 사후 `(α_v, β_v)` | 없음 (`ρ` 나눗셈만) | `score()` L822-867 교체 |
| `Pr[p_free > p*]` | `ρ · min(d/τ,1)` L854-860 | 정규화 불완전 베타 (2D LUT 또는 근사) |

**가장 침습적인 변경:** `observe()`가 `σ_r`을 받아야 한다. 이게 없으면
§03의 절반이 성립하지 않는다 → **[04](04_validation_plan.md) P0의 최대 리스크**로 명시해 둔 이유.

### 1.2 Layer 1 (신규 — `slam_utils.py` 쪽)

| 모형 항 | 자리 |
|---|---|
| `L_free(r) = ∫₀^{z−Δ} σ dt` | 렌더 패스에서 누적 투과율 필요. `get_loss_carve_depth_violation()`(L317) 자리를 대체 |
| `L_surf(r)` 종료분포 KL | 동상. 기존 `get_loss_mapping_rgbd`의 depth L1(L313)과 **통합**되어야 함 |
| `w_r` outlier responsibility | keyframe별 `π` 상태 필요 (작은 신규 상태) |

> ⚠ **rasterizer 제약.** `L_free`를 정확히 계산하려면 ray별 **표면 앞 누적 광학두께**가
> 필요하다. 현재 rasterizer가 이를 노출하는지 미확인이다. exp65 M2에서
> "rasterizer가 픽셀별 blending weight를 노출 안 해서 근사할 수밖에 없었고,
> CUDA 수정은 범위 밖(exp56 전례로 고위험)"이라는 **정확히 같은 벽**에 부딪힌 기록이 있다.
>
> **대응:** Layer 1은 **선택적**이다. §03의 Layer 2만으로도 결함 A~E, G는 전부 해결되고,
> [04](04_validation_plan.md) P1~P4는 Layer 1 없이 전부 수행 가능하다.
> **Layer 1은 P5 이후로 미루는 것을 권장한다** — 이 프로젝트에서 CUDA 래스터라이저
> 내부에 손대는 건 반복적으로 비싼 길이었다.

### 1.3 Layer 3 결정 규칙

| 모형 항 | 현재 코드 | 변경 |
|---|---|---|
| `P_j` (Gaussian이 floater일 사후확률) | `self._score` 텐서 | 의미만 교체, 자료형 동일 |
| 삭제 규칙 `P_j > p_threshold` | `maybe_budget_prune()` L1966-2041 (top-K + 예산) | 임계값 비교로 단순화 |
| birth gate | `gate_newborn()` L1948 (`score>0.95`) | **같은 규칙**의 다른 적용 시점 |
| `p_threshold` | `prune_budget_total=0.0075` | [04](04_validation_plan.md) P4 실측값 |

> **단순화 이득:** 지금은 birth gate와 budget prune이 서로 다른 임계값·다른 회계
> (`_harm_spent`, `_opacity_harm_spent`)를 쓰는 별개 기제다. Bayes 규칙 하나로
> 합치면 **누적 예산 회계 상태가 통째로 사라진다**(L894, 897, 941, 944, 1979, 1997, 2041, ...).

---

## 2. 단계별 착수 순서 (04의 사다리와 정렬)

```
S1  ray 덤프 (P0)          : observe() 호출부에 덤프 훅. σ_r 노출 여부 조사가 본체.
                             → VIGS 알고리즘 무변경, opt-in env var. 위험 없음.
S2  오프라인 통계 (P1,P2)  : 순수 numpy 스크립트. 저장소 밖(research/ 또는 scripts/analysis/).
                             → VIGS 코드 아예 안 건드림.
S3  score() 교체 (P3)      : CausalCarveField에 Beta 경로 추가. 기존 ρ 경로는 남겨서
                             config로 전환 → ablation R1~R6이 그대로 스위치가 됨.
S4  결정 규칙 교체 (P4)    : maybe_budget_prune / gate_newborn 통합.
S5  Layer 1 (P5 이후)      : rasterizer 조사 결과에 따라 판단. 선택적.
```

**S1·S2는 VIGS 코드를 사실상 건드리지 않는다** — 즉 [04](04_validation_plan.md)의
P1/P2(가장 결정적인 반증 실험)를 **회귀 위험 0으로** 수행할 수 있다.
이게 이 순서의 가장 큰 장점이다.

---

## 3. 성능 회계 (실시간 1.5× 예산)

§03 §9의 표를 코드 단위로 다시 쓴다.

| 변경 | 비용 방향 | 근거 |
|---|---|---|
| `observe()` soft 가중 누적 | +상수배 (같은 루프) | 행진 횟수 불변 |
| `S_v` 누적 (6 float) | +메모리, +미미한 연산 | sparse dict 값 확장 |
| LUT 제거 → 3×3 고유값 | **−** (조회 → 폐형, 캐시 미스 감소) | 8192-entry LUT 제거 |
| Beta 꼬리확률 | +연산 (LUT 또는 근사 필요) | 나눗셈 1회보다 비쌈 |
| `Â_j` 밀도 가중 | **+가장 큼** | 단, `score_ellipsoid_support()`로 **이미 측정 가능** |
| 예산 회계 상태 제거 | **−** | `_harm_spent` 등 소멸 |

> **먼저 재야 할 것:** `score_ellipsoid_support()`를 기본 경로로 켰을 때의
> map() 시간 증가. 이건 **지금 당장, 새 코드 없이** 측정할 수 있다.
> 이 수치가 1.5× 예산을 깨면 §03의 `Â_j`는 근사(예: Gaussian당 소수 샘플점)로
> 후퇴해야 하며, 그건 설계 단계에서 알아야 할 정보다.
> → **S1보다도 먼저 할 수 있는 30분짜리 측정.**

---

## 4. 미확인 항목 (추정으로 넘기지 않고 조사할 목록)

이 프로젝트의 memory 교훈("미계측 항목은 실험으로 검증")에 따라 명시한다.

| # | 질문 | 어떻게 확인 | 막히면 |
|---|---|---|---|
| U1 | VIGS 경로에서 depth 불확실성 `σ_r`을 얻을 수 있는가 | DROID `disps`/BA Hessian 코드 추적 | inverse-depth 잔차 국소 분산으로 경험적 추정 |
| U2 | rasterizer가 표면 앞 누적 광학두께를 노출하는가 | `diff-gaussian-rasterization` 조사 | Layer 1 보류 (§1.2) |
| U3 | `score_ellipsoid_support()`의 실제 시간 비용 | 기존 코드로 즉시 측정 | 샘플점 근사로 후퇴 |
| U4 | VIGS 장면용 floater 라벨 GT가 있는가 | 없음(배치 전용) 확인됨 | P3를 배치 장면에서 수행 (04 P3 참조) |
| U5 | `terminal` 누적이 이미 soft인가 하드인가 | `observe()` 정독 | — |

---

이전: [04 — 검증 계획](04_validation_plan.md) · 처음: [README](README.md)
