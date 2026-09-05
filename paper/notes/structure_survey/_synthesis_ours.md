# 해부 종합 → 우리 §3 / §4 설계

> 5편(cartgs, chen2026cover, mallick2024taming3dgs, lmrs, vigsslam)의 §3·§4 해부에서
> **우리 논문에 실제로 옮길 수 있는 것만** 뽑아 우리 내용에 붙였다.
> 개별 해부는 같은 폴더의 파일들. 여기는 **결정과 설계**만 적는다.

---

# 1. §3은 어떤 모양이어야 하는가

해부해 보니 §3 골격은 하나가 아니라 **네 가지**였다.

| 모양 | 논문 | 언제 쓰나 | 우리 |
|---|---|---|---|
| **A. 대칭형** — 문제 N개를 이름 붙여 나열하고 해법 N개가 같은 순서로 대응 | cartgs | 기여가 병렬적 부품 여러 개일 때 | ★ **전체 골격** |
| **B. 유도형** — 정확하지만 계산 불가 → 완화 → 실용형 | chen2026cover | 목적함수에서 해를 유도할 때 | ★ **§3.3 내부** |
| **C. 사슬형** — 앞 소절이 만든 문제를 뒤 소절이 푼다 | lmrs | 소절이 4개 이상이고 순서에 필연성이 있을 때 | ★ **소절 간 접속** |
| **D. 모듈형** — 데이터 흐름 순서로 시스템 모듈 나열 | vigsslam | 시스템 전체를 소개할 때 | ✗ **안 씀** |

## 우리 §3 = A(골격) + C(접속) + B(§3.3 내부)

```
3. Method                                     [3.25쪽]
  3.0 Overview                                        0.5쪽
      ├ Preliminaries       (chen: 기여 수식과 배경 수식을 절 번호로 분리)
      ├ Diagnosis ×3        (cartgs: 문제에 이름을 붙여 셋으로 쪼갬)
      └ Roadmap (사슬형)     (lmrs: 소절마다 존재 이유를 붙인 한 문단)
  3.1 GPU-Token Admission   [C1]                      0.75쪽   ← taming §3.2 4문단 형식
  3.2 Slot Placement        [구성요소]                 0.5쪽
  3.3 Count-Balanced Reshuffling [C2]                 0.75쪽   ← chen §4 유도 + lmrs 실패보고
  3.4 Causal Carve Evidence [C3]                      0.75쪽
```

**D를 안 쓰는 이유:** VIGS-SLAM은 시스템 논문이라 §3이 모듈 나열이고 진단이 §1에 있다.
우리는 그 시스템 안의 **한 결정**을 파고드는 논문이므로 진단이 §3에 있어야 하고,
소절이 모듈이 아니라 **결정**이어야 한다.

---

# 2. §3 소절별 문단 계약

각 문단에 **move 이름**과 **출처 논문**을 달았다. 초고를 쓸 때 이 표의 행 = 문단 하나.

## §3.0 Overview (0.5쪽, 4문단)

| # | move | 내용 | 출처 |
|---|---|---|---|
| 1 | **Preliminaries** | 3DGS 표현식 + VIGS-SLAM mapping loop 표기. 첫 문장에 "이 소절은 배경이며 우리 기여가 아니다"를 명시 | chen §3.2 |
| 2 | **Diagnosis (인용형)** | baseline의 실제 문장을 인용: *"For each new keyframe, we run 10 mapping iterations. In each iteration, we randomly sample keyframes from the frontend tracking frame graph E."* → 이 한 문장 안에 **세 결정이 뭉쳐 있다**고 지적 | vigsslam §3.3 |
| 3 | **Diagnosis (분해)** | 세 결정에 이름을 붙인다. `S(t)↦(B_t,Q_t)` cardinality / `(Q_t,C_t)↦A_t` membership / `(A_t,n_t)↦(W_t,p_t,H_t)` ordering. 각각 **왜 지금 방식이 답이 아닌지** 한 문장씩 | cartgs III.A |
| 4 | **Roadmap (사슬형)** | *"먼저 §3.1에서 … 그러나 이는 열린 slot을 어디에 둘지 답하지 않으므로 §3.2에서 … 받아들인 pool의 학습 순서가 남으므로 §3.3에서 … 품질이 확보되어도 free-space 오류가 남으므로 §3.4에서 …"* | lmrs §4 도입 |

★ **문단 4는 이미 `plan/outline/CURRENT.md`의 "절 간 논리 흐름" 화살표에 다 있다.**
그 화살표를 산문 한 문단으로 옮기기만 하면 된다.

## §3.1 GPU-Token Admission [C1] (0.75쪽, 4문단 + 식 3개)

**taming3dgs §3.2 "Predictable Model Growth"와 문단 대응이 1:1이다.** 그대로 쓴다.

| # | move | 우리 내용 | 대응 |
|---|---|---|---|
| 1 | **Diagnosis** | keyframe 개수·고정 FPS·maturity gate는 admission을 **pool 크기와 하드웨어 속도에 종속**시킨다. 결과: 예측 불가한 update 희석 | taming 1문단 ("no control over the progressive or final count") |
| 2 | **Measurement** | 완료된 GPU service `S(t)`를 측정량으로 도입. **왜 wall-clock이나 iteration이 아니라 완료된 service인가**를 여기서 답함 (Fig: 고정 FPS 하 admission이 pool 크기에 끌려가는 실측) | taming 2문단 (경험 법칙) + taming §4 도입 (프로파일 먼저) |
| 3 | **Mechanism** | `A*(t) = min(M(t), A₀ + ⌊(B₀+γS(t))/κ⌋)`, `B_t = B₀ + γS(t) − κ(\|A_t\|−A₀) ≥ 0` | taming 3문단 (`A(x)` 스케줄) |
| 4 | **Correction rule + Forward pointer** | 소멸·prune 후 실제 admission: `Q_t = min(\|C_t\|, [A*(t) − \|A_{t⁻}\|]₊)`. **carry vs no-prepurchase를 여기서 두 문장으로 닫는다.** 끝에 *"§4.3은 이 법칙이 실제 실행에서 정수 오차 없이 성립함과, κ를 낮췄을 때의 graceful degradation을 보인다"* | taming 4문단 (pruning 보정 + "Sec. 5 demonstrates …") |

★ **미결 항목 해소:** `PAPER_STATUS.md`의 "carry vs no-prepurchase"는 taming3dgs가 보여주듯
**§3.1 문단 4에서 두 문장이면 끝난다.** 별도 소절이나 긴 논의가 필요한 결정이 아니다.

★ **가정 원장 (chen §4.4):** `γ`, `κ`, `A₀`, `B₀`가 무엇으로 정해지는지 각각 한 구절씩.
특히 κ는 *"κ = 22 was selected on aria1253 and reused unchanged on the remaining scenes;
we do not claim it is scene-independent"* — 금지문장 #3(단일 장면 임계값을 보편 정책으로) 대응.

## §3.2 Slot Placement (0.5쪽, 2문단)

구성요소이므로 짧게. temporal maximin + interval water filling.
마지막 문장은 **정직한 축소** — 실측 이득 +0.35%임을 여기서 밝히고 §4에서 반복하지 않는다.
(chen이 Sparse에서 random과 동률인 22.80을 표에 그대로 넣은 것과 같은 태도.)

## §3.3 Count-Balanced Reshuffling [C2] (0.75쪽, 5문단 + 식 4개)

**chen2026cover §4의 유도형 + lmrs의 §4 내 실패보고.** 가장 공들여야 할 소절.

| # | move | 우리 내용 | 대응 |
|---|---|---|---|
| 1 | **Roadmap (유도 단계 열거)** | *"유도는 세 단계로 진행된다: (1) 선택 횟수 불균형을 potential Φ로 정의하고, (2) 1회 교체의 Φ 감소를 Lagrangian으로 풀어 유일한 분포를 얻고, (3) 이를 K-view 비복원 block으로 확장한다."* | chen §4 도입 |
| 2 | **Formulating** | `Φ(n)=½Σ(n_i−n̄)²`, `Δ_iΦ = n_i − n̄ + ½(1−1/N)`. **마지막 항이 모든 i에 공통이라 argmax에 영향을 주지 않음**을 명시 | chen §4.1 |
| 3 | **Deriving** | entropy 정규화 Lagrangian → `p_t(i) = exp(−βn_i)/Σ_j exp(−βn_j)`, `β = 1/τ`. **"이것이 유일한 해"**라는 문장 | chen §4.1 |
| 4 | **Extension + 가정 원장** | K-view 순차 가중 비복원 추출, snapshot `n_i^(b)`를 block 내 고정. **여기에 근사 조건을 붙인다** — snapshot 고정은 block 내 1차 근사, `ρ_H = ΣH(p_{b,k})/Σlog\|W_b^(k)\|`로 조건부 엔트로피 손실을 계측 | chen §4.4 (가정마다 조건) |
| 5 | **Scope guard + In-method 실패** | ★ 두 문장이 반드시 들어간다:<br>(a) **등식→부등식 감사**: *"β=0에서 이 절차는 full-pool random reshuffling과 일치한다 — **단 K ≥ N_t일 때에 한한다.** 그보다 짧은 block에서는 일치가 깨지며, §4.4가 그 대가를 정량화한다."*<br>(b) **실패 보고**: *"이 목적함수는 selection count를 균등화하지만 **lifetime은 균등화하지 못한다** (§4.4, rot에서 middle/first 0.758→0.520). count만을 potential로 둔 것은 설계 선택이며 그 한계다."* | (a) chen §4.1 Cauchy-Schwarz 문장 / (b) lmrs §4.2 "4× slower, as shown in Tab. 3" |

★★ **금지문장 → 허용문장 전환이 여기서 일어난다.**
`plan/claims/CURRENT.md` §E의 금지 목록은 "쓰지 마라"인데, chen2026cover는
**"이렇게 쓰면 된다"의 실물**을 준다: 등식이 깨지는 지점을 지목 + 대신 성립하는 것 + 여전히 주장 가능한 것.
→ **claims 다음 버전에서 §E를 "금지문장 / 대응 허용문장" 2열 표로 바꿔야 한다.**

## §3.4 Causal Carve Evidence [C3] (0.75쪽)

팀원 작업. 형식만 맞춘다: Diagnosis → Mechanism → **가정 원장**(어떤 조건에서 carve가 유효한지)
→ Forward pointer(§4.5). 그리고 §3.0 Diagnosis에서 예고한 이름과 **같은 이름**을 쓸 것.

---

# 3. §4는 어떻게 구성하는가

## 3.1 골격 (2.2쪽)

```
4. Experiments
  4.1 Setup                          0.35쪽  ← 계약 선언이 여기 산다
  4.2 Main Results                   0.6쪽   ← budgeted scenario 2개
  4.3 Admission (C1)                 0.45쪽  ← 정확성 + κ 스윕 + rate robustness
  4.4 Ordering (C2)                  0.45쪽  ← K×β + 레짐 서술
  4.5 Geometry / Carve (C3)          0.25쪽
  4.6 System Analysis                0.1쪽
6. Limitations                       0.2쪽   ← §3 가정 원장과 짝
부록  Rejected alternatives / Disabled features / 유도 전문
```

## 3.2 §4.1 Setup — **계약 문장이 논문의 핵심 차별점을 나른다**

vigsslam이 online 계약을 §4 Baselines 한 문장으로 처리한 형식을 그대로 쓴다:
**이름 + 제외 항목 + 제외 크기(수치) + 적용 대상 + 제외본은 supplementary.**

우리 S1–S6 → Setup 3문단:

1. **Contract.** *"To evaluate the strict streaming setting, every method receives the same sensor trace
   (RGB + IMU only, no MPS post-processing), the same 1.5× wall-clock budget (97.65 s for aria1253),
   and performs **zero optimizer updates after the last sensor frame**. Poses and depths are the
   online-estimated ones. Results with a post-stream refinement tail are in the supplementary material."*
2. **Comparability guard.** *"Held-out views are excluded from all supervision for every method.
   Consequently, numbers reported by X under a post-processed-pose protocol **are not directly comparable
   to ours.**"* — ★ 특히 **exp73은 strict zero-tail run이 아니다.** 그 수치를 실으려면 이 문장이 함께 가야 한다.
3. **Metrics (두 묶음).** taming3dgs 방식으로 **품질과 자원을 명시적으로 나눈다**:
   - 품질: held-out PSNR / SSIM / LPIPS, region GT AUC·AP
   - 자원: wall-time, **streaming updates**, **총 admission 수**, **peak pool**, **final pool**
   - 모든 수치는 3회 반복 **mean ± std**

★ **`peak pool`은 지금 계획에 없다.** taming3dgs가 `Peak #G`로 Mini-Splatting을 잡은 논리가
우리에게 그대로 적용된다 — final pool만 보면 "일단 왕창 받고 나중에 줄이는" 방식과
"처음부터 예산 안에서 받는" 우리 방식이 표에서 구별되지 않는다. **계측 항목 추가 필요.**

## 3.3 Table 1 설계 — 품질과 자원을 **한 표에**

cartgs가 `ATE | FPS | IPF | PSNR | Points`를 한 표에 놓은 것, taming3dgs가 `품질 | Train time | #G | Peak #G`를
한 표에 놓은 것이 같은 설계다. 우리 버전:

| Method | PSNR↑ | SSIM↑ | LPIPS↓ | wall-time | streaming updates | admissions | peak pool | final pool |
|---|---|---|---|---|---|---|---|---|

- `streaming updates`가 cartgs **IPF의 자리**다. "품질이 좋아졌다"가 아니라 **"같은 계산량에서"**를 표 하나로.
- **행 배치는 taming3dgs의 2 시나리오**:
  - **상단 — 같은 예산에서 품질:** 1.5× budget 고정, baseline(fixed-FPS dense / random full-pool /
    covisibility window / novelty-first / residual-first / **clustering-based batch sampler**) vs Ours
  - **하단 — 같은 품질에서 예산:** VIGS-SLAM baseline의 update 수에 정확히 맞춘 Ours
- 캡션에 **출처 표기** (vigsslam): 인용 수치 / 재현 수치 / 실패(F) 구분

★ **P06 baseline 목록에 빈 구멍이 있다.** 현재 5개 중 **"우리와 같은 문제를 다르게 푼" 방법이 없다.**
lmrs §4.3의 **clustering-based camera sampler**(카메라 위치·시선 K-Means → 클러스터당 1개)가
ERCB의 직접 경쟁자다. 추가해야 한다.

## 3.4 §4.3 Admission — **정확성 자체가 결과다**

taming3dgs가 *"our budgeting mechanism allows to match their model size **exactly**"*를
헤드라인 결과로 쓴 것과 같이, exp73의 **526 poll 정수 오차 0**은 각주가 아니라 결과다.

| 산출물 | 내용 | 출처 형식 |
|---|---|---|
| **Fig.3** admission trace | `A_paid(u)` vs `⌊u/κ⌋` 중첩. 오차 0을 눈으로 | taming Fig.2b |
| **Table 1 열** | `admissions` 열 + 캡션에 "law와의 최대 정수 오차 = 0 (2 scenes, 7 runs, 526 polls)" | taming "exactly" |
| **κ 스윕 case study** | aria1253 한 장면. graceful degradation + **κ=16 이상치(22.163 dB, −5.545) 그대로 표기** | taming Fig.1 (GARDEN 1장면) |
| **`4.3.x Rate Robustness`** | pace {0.75,1.0,1.5,2.0}× × {5090, 5070Ti}. **독립 서브헤드 이름을 줌** | vigsslam §4.2 Strided Evaluation |

★ **κ=16 이상치는 지금 어디에도 기록돼 있지 않다.** taming3dgs가 `−reduce SH frequency`에서
자기보다 높은 PSNR을 그대로 실은 것처럼, 스윕의 비단조 지점은 숨기지 않고 싣는다.

★ **`4.3.x Rate Robustness`라는 이름을 줄 근거가 생겼다.** 지금 P02는 Fig.4로만 잡혀 있는데,
vigsslam이 `Strided Evaluation`으로 독립 소절을 만든 선례가 있다. **C1의 "pool-independent"를
증명하는 유일한 실험이므로 그림 하나로 흘리면 안 된다.**

## 3.5 §4.4 Ordering — **"random이 강하다"를 먼저 인정한다**

★ 이 소절의 서술 뼈대는 **chen2026cover §5.1**에서 통째로 가져온다.

chen은 *"We observe that a random baseline is performant for view selection on a fixed dataset"*로
시작해 → **이유를 설명**(사람이 찍은 데이터셋은 원래 잘 분포되어 있다) → **gap이 벌어지는 레짐을 찾는다**
(Embodied+Sparse에서 1.5 PSNR). Sparse에서 random과 동률인 22.80을 표에 그대로 남긴다.

우리 상황이 정확히 같다:
- β=0은 K ≥ N_t에서 full-pool random과 **동일하다** (설계상)
- exp72에서 1253은 **−0.084 dB (손해)**, rot은 **+0.362 dB**

지금 계획엔 이 비대칭을 설명할 자리가 없다. chen 방식이면 **약점이 아니라 레짐 분석**이 된다:
*"짧은 block이 강제되지 않는 레짐에서는 random reshuffling이 이미 강하다. ERCB의 이득은
block이 짧아지거나 pool이 빠르게 성장해 K ≪ N_t가 되는 레짐에서 나타난다."*

**Table 3 (ordering ablation) 설계 — 교란변수를 같은 표에** (lmrs Table 2 형식):

| Sampler | K | β | PSNR↑ | ρ_H | selection CV | lifetime mid/first | pool |
|---|---|---|---|---|---|---|---|
| random | 1 | — | | | | | |
| random | 32 | — | | | | | |
| random | 128 | — | | | | | |
| ERCB | 128 | 0.02 | | | | | |

- K를 세로로 늘어놓아 **K가 지배적 요인**임을 표 스스로 드러내게 한다
  (이미 있는 숫자: K=1,β=0 −2.863 dB / K=32 −2.082 dB)
- 같은 K=128 두 행이 **β만의 효과**를 분리
- 표 앞에 **봉인 문장** (taming): *"All configurations receive the same admission budget and the same
  wall-clock budget; only the ordering policy differs."*
- `lifetime mid/first` 열에 **실패가 그대로 보인다** (rot 0.758→0.520) — 숨기지 않고 §3.3의 scope guard와 연결

## 3.6 부록 두 개 — **지면을 안 쓰고 성실성을 얻는다**

lmrs 부록 E/F 형식.

**부록: Rejected alternatives** (lmrs App E). 이미 숫자가 다 있다:

| 대안 | 결과 | 출처 |
|---|---|---|
| novelty-first ordering | AUC MSE +10% | exp66 Stage C |
| residual-first ordering | AUC MSE +11% | exp66 Stage C |
| with-replacement sampling | +1.7% | exp66 Stage C |
| coverage-only selection | temporal 대비 AUC −3.88% | 초안 §4 |
| ray 64 → 256 | PSNR 27.016 → 25.466 | mission brief §2.3 |
| 단일 장면 튜닝 전이 | rot −1.85 dB, 305 16.95 dB | exp59 |

**부록: Disabled features and why** (lmrs App F). S1–S6 계약 중 §4.1에 다 못 넣는 것 —
MPS 후처리 미사용, post-stream refinement 미수행, held-out 제외 — 을 **무엇을/왜/선행연구도 그런가**
형식으로. lmrs가 *"Because of similar reasons, densification is also disabled in 3DGS-LM"*으로
자기만의 편의가 아님을 보인 것을 따라, **vigsslam 자신이 "before the final global BA and color
refinement"를 인정한 것**을 인용한다.

## 3.7 §6 Limitations — §3 가정 원장과 **짝을 맞춘다**

chen §6이 §4에서 붙인 근사를 그대로 회수한 형식:
*"CONVERGE is derived from a set of approximations that trade off fidelity for scalability… though we
have not observed this behavior in commonly used datasets."*

우리 §6은 §3에서 붙인 가정을 순서대로 감사한다:
- κ=22는 단일 장면에서 정해졌고 자동화되지 않았다 (§3.1 가정)
- count-Gibbs는 lifetime을 균등화하지 못한다 (§3.3 실패)
- β=0 ≡ random은 K ≥ N_t에서만 (§3.3 등식 조건)
- carve는 … (§3.4 가정)

**독립 절 vs Conclusion 흡수**는 둘 다 CVPR 조판 선례가 있다 —
**chen2026cover = 독립 §6, lmrs = §6 Discussion and Conclusion에 흡수.**
분량 보고 결정하면 되고, 지금 미결로 둬도 위험이 없다.

---

# 4. 기존 계획 문서에 반영해야 할 것

해부에서 나온 것 중 **현재 계획에 없거나 어긋나는** 항목만.

| # | 무엇 | 어디 | 근거 |
|---|---|---|---|
| 1 | 계측에 **`peak pool`**과 **`총 admission 수`** 추가 | `experiments/protocol/`, `plan/experiment_table/` | taming `Peak #G` |
| 2 | **Table 1을 품질+자원 단일 표**로 확정 (지금은 지표만 있고 묶는 결정이 없음) | `plan/experiment_table/` | cartgs IPF / taming |
| 3 | Table 1을 **budgeted scenario 2개**(같은 예산→품질 / 같은 품질→예산)로 상하 분할 | `plan/experiment_table/` | taming §5.2 |
| 4 | P06 baseline에 **clustering-based batch sampler** 추가 (같은 문제를 다르게 푼 방법이 없음) | `plan/experiment_table/` P06 | lmrs §4.3 |
| 5 | P02를 **`4.3.x Rate Robustness` 독립 소절**로 승격 (지금은 Fig.4뿐) | `plan/outline/`, `sections/04_experiments/` | vigsslam §4.2 |
| 6 | claims §E를 **"금지문장 / 대응 허용문장" 2열**로 개편 | `plan/claims/` v03 | chen §4.1 Cauchy-Schwarz |
| 7 | **exp73은 strict zero-tail run이 아님**을 comparability guard 문장으로 명문화 | `plan/claims/` v03, `sections/04_experiments/4-1_setup/` | vigsslam Metrics |
| 8 | **κ=16 이상치(22.163 dB, −5.545)** 기록 및 κ 스윕 case study에 포함 | `plan/claims/` v03, `plan/experiment_table/` | taming ablation 정직성 |
| 9 | 부록 **Rejected alternatives** 표 신설 (숫자는 이미 다 있음) | `sections/` 신규 + `plan/outline/` | lmrs App E |
| 10 | 부록 **Disabled features** 신설 — S1–S6의 논문 서식 | `sections/` 신규 | lmrs App F |
| 11 | 표 캡션 **출처 표기 규칙**(인용/재현/실패) 확정 → "MonoGS를 구현할지 인용할지" 미결 해소 | `plan/experiment_table/` | vigsslam Table 1 캡션 |
| 12 | **carry vs no-prepurchase**는 §3.1 문단 4에서 두 문장으로 종결 — 별도 논의 불필요 | `PAPER_STATUS.md` 미결 해소 | taming §3.2 4문단 |
| 13 | 모든 ablation 표 앞에 **예산 봉인 문장** 의무화 | `sections/*/plan/` 템플릿 | taming Table 2 |
| 14 | 문단 계약에 **가정 원장**·**Forward pointer** 항목 추가 | `sections/*/plan/` 템플릿 | chen §4.4 / taming §3.2 |

## 남은 미결 (해부로 안 풀림)

- §6 Limitations 독립 절 vs 흡수 → **선례가 양쪽 다 있음. 분량으로 결정. 위험 없음**
- §3.2 Fisher tie-break를 본문에 남길지 → 분량 문제
- exp72 실패를 §4 전면에 낼지 §6로 내릴지 → ★ **해부 결과 §3.3 안(문단 5)이 가장 강하다.**
  lmrs가 자기 중간 설계의 4× 저하를 §4 본문에 실은 형식. 실패가 **다음 설계의 근거**가 되기 때문
