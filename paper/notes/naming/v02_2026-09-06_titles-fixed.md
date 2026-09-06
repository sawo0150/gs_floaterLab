# 이름 결정 v02 (2026-09-06) — 확정

> 전제: **우리가 쓰는 도구는 이미 다른 커뮤니티에 이름이 있다.**
> 발명했다고 쓰면 안 되고 "이 도구를 online GS-SLAM supervision scheduling에 붙였다"로 좁힌다.
> 이름이 그 전략을 방해하면 안 된다.

## 근거 1 — 우리 refs 코퍼스 실측 (vision 논문 13편)

`pdftotext` 후 전수 계수. **이 코퍼스는 전부 3D vision 논문**이라, 여기서 0이라는 건
"3D vision에서 안 쓴다"는 뜻이지 "아무도 안 쓴다"는 뜻이 아니다.

| 용어 | 빈도/논문수 | | 용어 | 빈도/논문수 |
|---|---|---|---|---|
| real-time | 118 / 13 | | admission | **0 / 0** |
| coverage | 66 / 7 | | token | **0 / 0** |
| view selection | 49 / 4 | | credit | **0 / 0** |
| budget | **43 / 6** | | quota | **0 / 0** |
| resource | 35 / 7 | | scheduling | **0 / 0** |
| softmax | 33 / 2 | | reshuffling | **0 / 0** |
| information gain | 30 / 2 | | without replacement | **0 / 0** |
| balanced | 13 / 4 | | Gibbs | **0 / 0** |
| view sampling | 10 / 2 | | throughput | **0 / 0** |
| entropy | 7 / 5 | | | |

### ★ 이 분야에서 "shuffle"은 다른 뜻이다

코퍼스의 `shuffl` 3건이 **전부 CUDA warp shuffle**이었다:

- cartgs: *"Warps utilize **intra-warp shuffling** to efficiently construct their segment of the state table"*
- taming3dgs: *"Warps use **intra-warp shuffling** to produce their share of the state table cheaply"*

하필 우리와 가장 가까운 두 논문(둘 다 GPU 예산 논문)에서 GPU 원시연산을 뜻한다.
→ **절 제목에 "Reshuffling"을 쓰지 않는다.** 본문에서 이론 연결을 말할 때만 쓴다.

## 근거 2 — 용어의 실제 소속

| 용어 | 어느 커뮤니티 | 우리에게 |
|---|---|---|
| random reshuffling / without-replacement | 확률적 최적화 이론 (NeurIPS 계열) | β→0 극한의 정확한 이름. **본문에서 밝히되 보장은 안 가져온다** |
| Plackett–Luce / Gumbel-Top-k | 이산 샘플링·랭킹 통계 | 우리 K-view 순차 가중 비복원 추출의 이름 |
| entropy-regularized | 통계물리·convex opt·OT·maxent RL·제어 | **정규화항**을 뜻하는 확립된 관용구 |
| token bucket (r, b) | 네트워크 QoS (RFC 2212) | 우리 `B_t = B_0 + γS(t) − κ(\|A_t\|−A_0) ≥ 0`의 이름 |
| credit-based flow control | 링크 레벨 흐름 제어 | ★ 실제로는 이쪽이다 (아래) |
| view selection | 3D vision | **능동 촬영/추가 선택**을 뜻함 → 우리 뜻과 다르므로 피한다 |
| view sampling | 3D vision (lmrs §4.3, sparsegs) | 배치 구성을 뜻함 → 우리와 맞음 |

---

# 원칙 — 제목은 이 분야 말로, 계보는 본문 첫 문단에서

세 이름 모두 이 규칙을 따른다. 제목에서 빠지고 본문으로 내려가는 단어:
`admission`, `token`, `credit`, `reshuffling`, `Plackett–Luce`, `token bucket`.

---

# C2 — 이름

## 판단: `Entropy-Regularized` 는 안전하다. `Entropy-Based/Guided/Aware` 는 위험하다

- **`Entropy-Regularized X`** = optimal transport, maximum-entropy RL, KL control에서
  **목적함수에 entropy 벌점을 더했다**는 뜻으로 굳어진 관용구다. 무엇을 측정한다는 뜻이 아니다.
- **`Entropy-Based / Entropy-Guided / Entropy-Aware X`** = entropy를 **재서** 뭔가를 고른다는 뜻으로
  읽힌다 → FisherRF·CONVERGE 계열의 information gain과 혼동된다.
  `plan/claims/CURRENT.md` §E의 "exact EIG 계산 주장 금지"와 정면 충돌한다.

즉 **entropy를 제목에 넣되 반드시 `-Regularized`를 붙인다.** 이러면 오히려
"우리는 이게 표준 entropy 정규화 구성임을 안다"는 신호가 되어 강해진다.

## 정한 이름 — 확정

> ### `Entropy-Regularized Count Balancing`
> 약칭 **ERCB**. 표·그림·본문 2회차부터 ERCB.

- `Entropy-Regularized` — **정규화항**임을 명시. information gain 오해 차단.
  `Entropy-Based / Guided / Aware`는 "entropy를 재서 고른다"로 읽혀 금지
- `Count` — 목적함수가 선택 **횟수** 균형(`Φ(n)=½Σ(n_i−n̄)²`)임을 노출.
  `Visit`은 SLAM revisit과, `Exposure`는 카메라 노출과 충돌하므로 쓰지 않는다
- `Balancing` — 3단어로 끝나 절 제목·표 헤더·캡션에 다 들어감
- v01의 `… Count-Balanced (ERCB) View Sampling`(6단어)에서 줄였다. **약자는 그대로 성립**

## 본문에 반드시 넣을 계보 문장 3개

1. **비복원 SGD와의 관계 + 경계**
   > With β = 0 and K ≥ N_t, the procedure reduces to random reshuffling over the admitted pool.
   > We do not inherit its convergence guarantees: our pool grows during training and the objective
   > is non-convex.
2. **추출 절차의 이름을 먼저 밝힌다**
   > The K-view draw is sequential weighted sampling without replacement, i.e. a Plackett–Luce draw.
3. **count 기반 우선순위의 선행을 먼저 밝힌다**
   > Count-based priorities of this form appear in experience replay (Curious Replay uses p_i = β^{v_i}).
   > Our objective is the opposite of loss-prioritized data selection: we equalize exposure rather
   > than concentrate it.

→ 근거 PDF는 `refs/03_shuffling_theory/`, `refs/07_sampling_ranking/`, `refs/08_rl_replay/`,
`refs/09_data_selection/`에 받아뒀다. 목록은 `refs/INDEX.md`.

---

# C1 — 이름

## ★ 메커니즘의 정확한 이름은 credit-based flow control 이다

우리 식은 token bucket 그 자체다:

```
B_t = B_0 + γS(t) − κ(|A_t| − A_0) ≥ 0      ↔   token bucket (r, b), RFC 2212
  B_0 = 초기 버스트(bucket size b)
  γ   = 충전율 (rate r)
  κ   = admission 1회당 소모 토큰
```

**다만 표준 token bucket은 시간에 비례해 찬다.** 우리는 **완료된 GPU service `S(t)`에 비례해**
찬다. 이건 rate-based가 아니라 **credit-based flow control** — 수신자가 처리를 마치면 credit을
돌려주는 방식 — 에 해당한다.

★ **이 차이가 곧 C1의 기여다.** pool 크기와 무관하고 하드웨어 속도에 자동으로 맞춰지는 성질은
"시계가 아니라 완료가 박자를 만든다(completion-clocked)"에서 나온다.
고정 FPS admission은 clock-paced라 그 성질이 없다. **P02(rate invariance)는 문자 그대로
이 성질을 검증하는 실험이다.**

## ⚠ 기존 이름 `GPU-Token Admission`의 문제

`token`은 우리 코퍼스에 0회이고, **2027년 독자에게 "token"은 LLM 토큰으로 먼저 읽힌다.**
GPU + token 조합이면 LLM 서빙의 토큰 예산으로 오독될 소지가 크다. 바꾸는 게 낫다.

## 정한 이름 — 확정

> ### `Compute-Paced View Growth`

사수님이 `admission`이라는 단어에서 혼동하셨다. 측정해 보니 그 단어만 문제가 아니었다 —
**`pool`도 이 분야 말이 아니다.**

### 확대 코퍼스 실측 (vision 논문 25편)

| head noun | 빈도/논문수 | |
|---|---|---|
| **training views** | **74 / 13** | 가장 보편 |
| **supervision** | **59 / 13** | 가장 보편 |
| budget | 79 / 7 | 흔하나 *"미리 정한 상한"* 뜻 |
| resource | 58 / 12 | 막연 |
| growth | 13 / 4 | taming3dgs `Predictable Model Growth` |
| **pool** | ~10 | ⚠ 28회 중 5회가 저자명 `Poole`, 나머지는 `pooling` — **사실상 안 씀** |
| admission / token / intake / metering / pacing | **0 / 0** | 없음 |
| credit | 2 / 1 | 거의 없음 |

### 왜 이 이름인가

- `View Growth` — 이 분야 명사(`training views`) + taming3dgs `Predictable Model Growth` 선례
- `Compute-Paced` — **계산이 박자를 만든다.** 고정 FPS(시계가 박자)와의 대비가 이름에 들어감
- 사수님께 한 문장으로: **"GPU가 실제로 끝낸 일에 맞춰 학습 뷰가 늘어난다"** — `admission` 없이 설명됨

### 탈락한 후보

| 후보 | 탈락 이유 |
|---|---|
| `GPU-Token Admission` (v01 기존 이름) | `token`이 코퍼스 0회이고, **2027년 독자에게 token은 LLM 토큰으로 먼저 읽힌다** |
| `Compute-Credit Admission` (v01 추천) | **`admission`에서 실제로 혼동이 발생했다.** credit도 코퍼스 2회 |
| `GPU-Budgeted View Growth` | `budget`은 79회/7편으로 친숙하나 **"미리 정한 상한"**으로 읽혀 우리와 반대 |
| `Compute-Earned View Budget` | 위와 같은 이유 + 조어 |
| `Throughput-Matched Supervision Growth` | 길고 딱딱 |

---

# C3

`Causal Free-Space Carving` (잠정). **팀원이 정한다** — 2026-09-06 기준 본인 결정 사항 아님.
정해지면 §3.0 Diagnosis의 세 번째 이름도 같이 맞춘다.

---

# ⚠ 이름보다 먼저인 것 — exp72에 `K=128, β=0` arm이 없다

`context/experiments/exp72/exp72_entropy_count_scheduler_real_ablation.md` 실측 확인 결과,
sweep은 이렇게 되어 있다:

| arm | K | β | held-out PSNR | Δ |
|---|---|---|---|---|
| B1 | **1** | 0 | 24.845 | −2.863 |
| B1 | **1** | 0.006 | 27.218 | −0.490 |
| B1 | **1** | 0.02 | 27.457 | −0.251 |
| B1 | **1** | 0.05 | 26.598 | −1.110 |
| — | 32 | 0.02 | 25.626 | −2.082 |
| — | **128** | **0.02** | **27.624** | **−0.084** |

**`K=128, β=0`이 없다.** 그래서 지금 숫자로는:

- `β=0`의 −2.863 dB는 **K=1**에서 잰 값이라 **block 길이 효과와 β 효과가 섞여 있다**
- `K=128, β=0.02`의 −0.084 dB는 **전역 baseline 대비**이지 **같은 block 길이의 무작위 대비가 아니다**
- 즉 **β 자체의 기여가 아직 한 번도 측정되지 않았다**

→ 이름을 `Entropy-Regularized …`로 하든 뭘로 하든, **`K=128, β=0` arm이 없으면 C2의 좁힌 기여마저
근거가 비어 있다.** `plan/experiment_table/`의 P03 sweep `{1,32,128}×{0,0.02}`에 이 칸이 들어 있고
아직 미착수다. **문헌 정리보다 이 실험이 먼저다.**

표 배치는 `notes/structure_survey/lmrs.md`의 Table 2 형식(같은 표에 sampler 축과 batch 축을 같이
놓아 교란변수를 드러냄)을 그대로 쓴다.

---

# 최종 확정 (2026-09-06)

| | 절 제목 | 약칭 |
|---|---|---|
| **C1** | `Compute-Paced View Growth` | — |
| **C2** | `Entropy-Regularized Count Balancing` | **ERCB** |
| **C3** | `Causal Free-Space Carving` (팀원 확정 대기) | — |

# 부수 결정 — Preliminaries는 독립 절로 빼지 않는다

v01 작성 시점에는 chen2026cover를 근거로 독립 절을 검토했으나, 코퍼스 25편을 세어보니
**독립 절은 4편(16%)뿐이고 우리 이웃인 GS-SLAM은 예외 없이 안 뺀다.**

```
MonoGS / SplaTAM / Photo-SLAM / Co-SLAM / iMAP / CaRtGS / VIGS-SLAM
  → 전부  1 Intro | 2 Related | 3 Method | 4 Experiments | 5 Conclusion
```

독립 절로 뺀 4편(chen2026cover, lmrs, mallick2025multiview)은 **전부 유도 중심 논문**이다.
장르가 갈림새다. 우리는 GS-SLAM 트랙에서 읽히므로 5절 구조를 따른다.

→ **절 번호는 계획 문서대로 유지** (§3 Method, §4 Experiments). 고칠 문서 없음.
→ 배경은 §3.0 첫머리 **`Preliminaries.` run-in 볼드**로 (VIGS-SLAM §3.3 방식).
→ 독립 절의 유일한 실익("§3.1 이후 수식은 전부 우리 것")은 문장 하나로 대체한다:

> Equations (1)–(2) are standard 3DGS and VIGS-SLAM formulations, restated here for notation.
> All remaining equations are ours.
