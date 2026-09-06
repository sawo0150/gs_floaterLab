# 3.2 Entropy-Regularized Count Balancing (ERCB) — 무엇을 쓸 것인가 (v02, 2026-09-06)

> 한 줄 claim: **선택 횟수 불균형을 entropy 정규화 문제로 두면 해가 유일하게 정해진다.**
> 5문단, 수식 2개, 90줄 = 0.82 p (§3.1 의 0.83 p 와 대등).

## v01 에서 바뀐 것

| | v01 | v02 |
|---|---|---|
| 분량 | 75줄 0.68p | **90줄 0.82p** |
| 수식 | 3개 | **2개** |
| 구조 | 나열형 | **정확한 대상 → 완화 1·2·3** |
| 등식 감사 | P5 에 몰아둠 | **P3 끝, 깨지는 자리에** |
| Plackett–Luce | P5 에 몰아둠 | **P4 첫 문장, 도입하는 자리에** |
| experience replay 선행 | P5 | **§2.3 Related Work 로** |
| `ρ_H` | 본문 display | **§4 Metrics 로** |

### 왜 늘렸나 — 코퍼스 때문이 아니다

유도가 있는 소절의 코퍼스 실측:

| 소절 | 줄 | 수식 |
|---|---:|---:|
| lmrs 4.3 View Sampling (유도 없음) | 55 | 1 |
| chen2026cover 4.3 Extension | 68 | 3 |
| chen2026cover 4.2 Tractable | 101 | 5 |
| lmrs 4.4 Residual Sampling | 191 | 4 |
| chen2026cover 4.4 Transmittance-Agnostic | 206 | 8 |
| **chen2026cover §4 전체(유도 하나)** | **393 (3.6p)** | **19** |

이걸 근거로 늘리면 안 된다. **우리 유도는 진짜로 짧다** — 4단계이고 chen 은 행렬식 항등식이
20개 넘게 이어진다. 억지로 늘리면 물타기다.

**진짜 이유는 문단 과부하다.** v01 에서 P3 는 5가지(Lagrangian 설정 / Gibbs 해 / "유일" 근거 /
`β=1/τ` 의미 / 등식 감사)를 16줄에, P4 는 5가지를 14줄에 해야 했다. **항목당 3줄**이면
선언만 하고 근거를 못 단다. 그리고 §3 에서 **유도가 있는 소절이 제일 짧은 건 뒤집힌 배치**다.
→ P3·P4 를 24줄씩 주어 항목당 5줄로 만들었다.

## 유도의 뼈대 — 정확한 대상에서 세 번 완화한다

chen2026cover §4 의 "정확 → 완화 → 실용"을 한 소절로 압축한 형태.

```
정확     전체 run 의 최종 count 분산을 최소화하는 선택 시퀀스
         ← 도착 과정이 아직 안 알려진 조합 최적화. 온라인에서 못 푼다
  ↓ 완화 1 (P2)
         한 step greedy: potential Φ 의 즉각 증가량만 최소화
         → 결정론적 "가장 적게 뽑힌 것" 규칙. 무작위성이 사라진다
  ↓ 완화 2 (P3)
         결정론적 argmin 대신 entropy 정규화된 기댓값 최소화
         → Gibbs 해. 유일하다
  ↓ 완화 3 (P4)
         매 선택마다 p 를 다시 계산하지 않고 block 시작 시점 count 를 고정
         → Plackett–Luce 비복원 추출
```

★ 완화 단계를 명시하면 **P4 의 "1차 근사"가 비로소 말이 된다.** v01 은 근사라고만 하고
*무엇의* 근사인지가 없었다.

## 문단 계약

| # | 하는 이야기 | 줄 | 수식 |
|---|---|---:|---|
| **P1** | **ROADMAP + 정확한 대상.** 우리가 정말 풀고 싶은 것은 run 전체의 최종 count 분산인데, 도착 과정이 안 알려진 조합 최적화라 온라인에서 못 푼다. **이걸 먼저 말한다.** 그 다음 완화 3단계 예고 + "전개 전문은 supplement" | 12 | |
| **P2** | **FORMULATING (완화 1).** `Φ` 정의 (4). 선택하면 `Δ_iΦ = n_i − n̄ + ½(1−1/N)` — **inline, display 아님.** 마지막 항이 `i` 에 무관 → greedy 는 **가장 적게 뽑힌 것 고르기**로 환원. **그런데 그건 결정론적이고, 결정론적 순서는 셔플링이 주려던 무작위성을 없앤다.** 이 긴장이 다음 단계의 이유 | 12 | (4) |
| **P3** | **DERIVING (완화 2) + 등식 감사.** argmin 대신 `min_p Σ p_i Δ_iΦ − τH(p)`. `τ→0` 결정론, `τ→∞` 균등. 정상조건 → `p_i ∝ exp(−Δ_iΦ/τ)`, 공통항이 정규화에서 소거 → (5), `β=1/τ`. **"유일하다"와 그 근거**(p 에 대해 선형 + τ×음엔트로피 = 강볼록, 콤팩트 볼록집합 위) . 이어서 **등식 감사**: `β=0` 은 `K ≥ N_t` 일 때만 random reshuffling 과 일치, `K<N_t` 면 block 은 순열이 아니라 부분집합. 그리고 **그때도 수렴 보장은 안 가져온다** (집합이 자라고 비볼록) | 24 | (5) |
| **P4** | **EXTENSION (완화 3) + 가정 원장.** **첫 문장에서 이름을 밝힌다** — 가중치 `exp(−βn_i)` 로 K개를 순차 비복원 추출하는 것은 **Plackett–Luce** 추출(= Gumbel-Top-k). (5)를 정확히 적용하려면 매 선택마다 `p` 재계산이 필요하나, block 시작 count `n_i^(b)` 를 고정해 K개를 뽑는다. **가정 원장**: block 안에서 count 는 최대 1 증가하므로 고정 가중치는 정확한 순차 가중치와 선택 1회당 최대 `e^β` 배 차이 → 작은 `β` 에서 1차 효과. **"근사"라고만 하고 넘어가지 말고 조건을 쓴다.** 남은 무작위성은 `ρ_H` 로 계측(정의는 §4) | 24 | |
| **P5** | **IN-METHOD FAILURE.** 우리가 고른 potential 은 **선택 횟수**를 균등화하지 **노출 기간**을 균등화하지 않는다. 늦게 들어온 view 는 기회 자체가 적고 `n_i` 를 맞춘다고 보정되지 않는다. 실측 middle/first 0.758 → 0.520. **count 만을 potential 로 둔 것은 설계 선택이고 이것이 그 한계다** (§4 forward pointer) | 12 | |

## 수식 — 2개만 display

| | 식 | 왜 display 인가 |
|---|---|---|
| (4) | `Φ(n) = ½Σ(n_i − n̄)²` | 완화 1 의 대상. 이후 전부 여기서 나옴 |
| (5) | `p_t(i) = exp(−βn_i)/Σexp(−βn_j)`, `β=1/τ` | 유도의 **결과**이자 구현 그 자체 |

### 뺀 것과 간 곳

| 뺀 것 | 어디로 | 왜 |
|---|---|---|
| `Δ_iΦ` 전개식 display | **본문 inline** | *"마지막 항이 `i` 에 무관"* 이라 할 거면 display 를 줄 이유가 없다. 결론만 필요 |
| `ρ_H` 정의 | **§4 Metrics** | 방법이 아니라 **평가 지표**다. Table 3 의 열이기도 하다 |
| Lagrangian 전개 | **Supplementary** | 본문은 결과와 조건만. **본문에서 "전문은 supplement" 라고 밝혀야** 유도가 부실한 것으로 안 읽힌다 |
| experience replay 선행 | **§2.3 Related Work** | 선행 소개는 거기가 자리다 (Curious Replay 의 `p_i = β^{v_i}`) |

## 등식 감사를 P3 에 두는 이유

chen2026cover §4.1 은 등식이 깨지는 **바로 그 지점**에서 감사한다:

> *"However, note that with additional constraints, Eq. (7) is **no longer equality**.
> Rather, we have the tight bound by Cauchy--Schwarz ... **Regardless**, minimizing Eq. (8)
> subject to additional constraints still applies upward pressure to the FIG."*

별도 문단으로 빼지 않는다. 뒤로 미루면 **사과처럼** 읽히고, 제자리에 있으면 **유도의 일부**로 읽힌다.

## 말하면 안 되는 것

| 문단 | 금지 | 근거 |
|---|---|---|
| P3 | random reshuffling 의 수렴 보장을 가져오는 것 | claims §E 금지 4 — 성장하는 비볼록 pool |
| P3 | `β=0 ≡ RR` 을 조건 없이 | `K ≥ N_t` 일 때만 |
| P4 | snapshot 고정을 "근사"라고만 하고 조건 없이 | chen §4.4 가정 원장 형식 |
| P5 | lifetime 도 균등화한다 | exp72 실패 |
| 전체 | exact EIG 계산 주장 | claims §E 금지 |

## 열린 질문

- `ρ_H` 를 §4 로 옮기는 것이 §4.1 Metrics 와 Table 3 에 반영되어야 한다
- experience replay 선행을 §2.3 에 넣는 것이 `sections/02_related/2-3_shuffling_theory/` 에 반영되어야 한다
- supplement 의 유도 전문을 누가 언제 쓸지
