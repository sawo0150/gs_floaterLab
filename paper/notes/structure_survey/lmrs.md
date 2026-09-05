# lmrs — 구조 해부 (§4, §5, 부록)

## 기본 정보

| | |
|---|---|
| 논문 | LM-RS: Levenberg-Marquardt + Residual Sampling으로 3DGS 2차 최적화 |
| venue | CVPR 계열 2단 조판, 17쪽 (본문 8쪽 + 참고문헌 + 부록 A–F) |
| 절 구성 | 1 Intro / 2 Related / **3 Background - 3D Gaussian Splatting** / **4 Method (4.1–4.5)** / 5 Results / 6 Discussion and Conclusion / 부록 A–F |
| 왜 보나 | **소절 5개짜리 유도형 §4를 8쪽 안에 넣은 실물.** 그리고 §4.3이 우리 C2와 같은 문제(view sampling)를 다룬다 |

---

## ★ 발견 1 — Roadmap이 **"앞 소절이 만든 문제를 뒤 소절이 푼다"는 사슬**이다

§4 도입 문단 전문(요지):

> *"We **first** introduce the LM optimizer in Sec. 4.1, which we adopt in this work.
> **Then, we derive why a naive implementation is not feasible** for Gaussian splatting.
> **To resolve this issue**, in Sec. 4.2, we discuss our matrix-free approach...
> **Next**, in Sec. 4.3, we introduce a new view sampling strategy to effectively approximate the full
> normal equation...
> In Sec. 4.4, we present our residual sampling, providing an approximate loss function, which results in
> significantly faster convergence.
> **Lastly**, in Sec. 4.5, we introduce a heuristic to automatically determine the learning rate,
> **which eliminates the need for line search** algorithms that are commonly used..."*

chen2026cover의 Roadmap이 "유도 3단계"를 열거했다면, 이쪽은 **각 소절에 존재 이유를 붙인다.**
소절이 5개나 되는데도 독자가 길을 잃지 않는 이유가 이 한 문단이다.

→ **우리 §3 도입 문단은 이 형식이어야 한다.** 우리 outline의 "절 간 논리 흐름" 화살표
(`§3.0 → §3.1 → §3.2 → §3.3 → §3.4`)가 이미 사슬 형태다. **그 화살표를 그대로 산문 한 문단으로 옮기면 된다.**

## ★ 발견 2 — **자기 중간 설계의 실패를 §4 안에서 보고한다**

§4.2 후반:

> *"**Although this optimizer is able to converge to the final solution in a limited number of steps,
> it is 4× slower than our final method, as shown in Tab. 3.** The main reason for this is that the
> conjugate gradient algorithm needs to run several iterations, therefore, we need to repeatedly compute
> the JᵀJp product arising on line 10 of Alg. 1."*

- 자기가 방금 제안한 것을 스스로 "4배 느리다"고 말한다
- **Forward pointer로 표를 지목**해서 주관이 아님을 보인다
- 원인을 알고리즘의 특정 줄(line 10)까지 짚는다
- 그리고 그것이 §4.4(residual sampling)가 존재하는 이유가 된다

★ **CaRtGS·Taming3DGS·CONVERGE 셋 다 없던 "실패 보고"가 여기 있다.**
그것도 §6 Limitations가 아니라 **§4 Method 본문 안**이다. 실패가 다음 소절의 동기가 되기 때문이다.

→ **exp72의 lifetime 균등화 실패(rot middle/first 0.758→0.520)가 정확히 이 자리에 들어갈 수 있다.**
"ERCB는 selection count를 균등화하지만 lifetime은 균등화하지 못한다"를 §3.3 안에서 말하고,
그것이 왜 count만을 목적함수로 두는지의 근거가 된다.

또 §4.2에는 **가정을 반증하는 그림**도 있다:
*"We observe that the Hessian approximation JᵀJ in 3DGS **does not exhibit a dominant diagonal or
block-diagonal structure, as illustrated in Fig. 3.**"* → 흔한 근사(대각/블록대각)를 쓸 수 없음을
그림 하나로 못박고 다른 길로 간다. **In-method evidence의 반증형 용례.**

## ★ 발견 3 — §4.3 View Sampling: 우리 C2의 **직접 경쟁자이자 서술 템플릿**

전체가 4문단이고 짧다. 구조:

| 문단 | move |
|---|---|
| 1 | **Diagnosis.** *"Second-order methods like LM are typically used in deterministic settings where the full objective is evaluated at every iteration. If this is not the case, estimating local curvature can be problematic and become unreliable [9]. This poses a challenge in the 3DGS setting, where the number of views can exceed hundreds, as incorporating all of them at the same time is infeasible."* |
| 2 | **Aim.** *"Yet, to compute meaningful gradients, we must find an effective way to approximate the full normal equation in Eq. 8."* |
| 3 | **Mechanism.** 카메라마다 특징벡터 `f_i = [x̃,ỹ,z̃,dx,dy,dz]` → K-Means로 batch size 개 클러스터 → 클러스터마다 1개 무작위 선택 |
| 4 | **Evidence pointer.** *"As evidenced by Tab. 2, this method converges to higher scores compared to the random sampling of the cameras."* |

★ **내용상 우리와 겹친다.** 둘 다 "무작위 배치보다 나은 배치 구성"을 푼다.
차이를 분명히 해야 한다:

| | LM-RS §4.3 | 우리 C2 (ERCB) |
|---|---|---|
| 목적 | batch 안의 **기하적 다양성** (곡률 추정용) | **선택 횟수 균형** (`Φ(n)=½Σ(n_i−n̄)²`) |
| 수단 | 카메라 위치·시선 K-Means 클러스터링 | count-Gibbs `p ∝ exp(−βn_i)` + K-view 비복원 |
| 근거 | 휴리스틱 + 표 | Lagrangian 유도 |
| 풀 | 고정 (offline) | **성장하는 pool (online)** |
| 무작위 대비 | 개선 | β=0에서 **K ≥ N_t일 때만** 동일 |

→ **§2 Related Work의 "view/batch 구성" 소절에 반드시 들어가야 하는 논문이고,
가능하면 P06 baseline에 "clustering-based batch sampler"를 넣어야 한다.**
현재 P06 baseline 목록(fixed-FPS dense / random full-pool / MonoGS covisibility / novelty-first /
residual-first)에는 **"우리와 같은 문제를 다르게 푼" 방법이 없다.** 이건 빈 구멍이다.

## ★ 발견 4 — Ablation 표가 **교란변수를 같은 표에 넣는다**

Table 2 (View Sampler):

| View Sampler | LPIPS↓ | SSIM↑ | PSNR↑ |
|---|---|---|---|
| Clustering-Based, MBS=8 | 0.363 | 0.640 | 19.18 |
| Clustering-Based, MBS=16 | 0.271 | 0.719 | 21.37 |
| **Random, MBS=32** | 0.276 | 0.722 | 21.68 |
| **Clustering-Based, MBS=32** | **0.253** | **0.731** | **21.83** |

축이 둘이다: sampler 종류 × 최대 배치 크기(MBS).
- MBS=32 두 행을 나란히 놓아 **sampler만의 효과**를 분리 (21.68 → 21.83)
- MBS=8/16 행이 **배치 크기가 더 큰 요인**임을 보여준다 (19.18 → 21.83)
- 즉 자기 기여가 배치 크기보다 작다는 것을 **표 스스로 드러낸다**

★ **이것이 우리 exp72 K/β 스윕의 정확한 형식이다.**
우리도 `K ∈ {1,32,128} × β ∈ {0, 0.02}`인데, 지금 experiment_table에는 스윕만 있고
**"K가 지배적이고 β는 그 위에서 작동한다"는 해석을 표로 드러내는 배치**가 없다.
K=1,β=0에서 −2.863 dB, K=32에서 −2.082 dB인 숫자가 이미 있으니 그대로 이 배치로 놓으면 된다.

## ★ 발견 5 — **부록 E: 시도했다 버린 확률분포를 전부 기록한다**

`E. Alternative Probability Distributions for Residual Sampling`

| 분포 | 정의 | 결과 |
|---|---|---|
| uniform `1/M` | — | SSIM 0.859 / PSNR 28.65 |
| `q_residual` | `softmax(\|r_p\|)` — 잔차가 큰 픽셀 우대 | 0.857 / 28.49 |
| `q_Gaussian` | `G_p / Σ G_k` — 그 픽셀에 기여한 Gaussian 수 | 0.859 / 28.59 |

**직관적으로 그럴듯한 대안들(잔차 우대·밀도 우대)이 균등분포보다 나을 게 없었다**는 것을 표로 남긴다.
본문에서는 자리를 안 쓰고 부록으로 뺀다.

★ 우리에겐 이 형식이 **여러 군데** 필요하다:
- exp66 Stage C: novelty-first / residual-first가 shuffle보다 **나쁨** (AUC MSE +10–11%),
  with-replacement +1.7% — **정확히 같은 성격의 표다**
- 초안 §4: coverage-only selection이 temporal baseline 대비 AUC −3.88%
- ERCB의 β 이외 대안 (lifetime 기반, loss 기반)

→ **부록 "Rejected alternatives" 표 하나로 묶으면 본문 지면을 안 쓰고 성실성을 얻는다.**

## ★ 발견 6 — **부록 F: 끈 기능을 왜 껐는지 밝힌다**

> *"3DGS proposes a densification algorithm to increase the number of Gaussians, **which is disabled in
> this work.** The reason is that densification algorithms typically rely on statistics collected over many
> iterations and complement the dynamics of the Adam optimizer. However, second-order optimizers require
> far fewer iterations, making it difficult to integrate such algorithms directly. **Because of similar
> reasons, densification is also disabled in 3DGS-LM.** We believe that combining ... would be an
> interesting research direction."*

- 무엇을 껐는지
- 왜 껐는지 (설계상 충돌, 취향 아님)
- **선행 연구도 같은 이유로 껐다** (자기만의 편의가 아님을 입증)
- 향후 과제로 넘김

→ 우리도 끄고 돌린 것이 있다 (MPS 후처리 미사용, 최종 global refinement 없음=zero-tail,
held-out을 supervision에서 제외). 지금은 **계약 S1–S6이 protocol 문서에만** 있는데,
이 형식이면 부록 한 문단으로 논문에 실을 수 있다.

## §5 Results 골격

```
5. Results
  5.1 Comparison        — 정량 비교
  5.2 Ablation Studies  — run-in 볼드로 항목화: "View Sampling. ... " 
6. Discussion and Conclusion   ← Limitations를 Conclusion에 흡수
부록 A CUDA 구현 / B,C 추가 결과 / D LR 스케줄러 상세 / E 버린 분포 / F 껐던 기능
```

§5.2는 **소절을 더 안 쪼개고 run-in 볼드**로만 나눈다(`View Sampling.`, `...`). 2단 8쪽의 압축 방식.
Table 4(learning rate)는 **속도까지 같이 준다** (`PSNR | Time(s)`): 27.91@188s vs 28.59@... —
품질만 놓고 고르지 않는다.

→ 우리 outline에서 미결인 "§6 Limitations 독립 절 vs §5 흡수"의 두 실물 사례:
**CONVERGE = 독립 절, LM-RS = Conclusion 흡수.** 둘 다 CVPR 조판에서 통과했다. 분량으로 결정하면 된다.

---

## ★ 훔칠 것

1. **사슬형 Roadmap** — 소절마다 "앞이 만든 문제를 푼다"는 이유를 붙임 → 우리 §3 도입 문단
2. **§4 안에서의 실패 보고 + forward pointer** → exp72 lifetime 실패를 §3.3 안에
3. **가정 반증 그림** (Fig. 3으로 대각 근사 불가를 보임) → 우리도 "고정 FPS로는 왜 안 되는가"를 그림으로
4. **교란변수를 같은 표에** (sampler × batch size) → 우리 K × β 표 배치를 이렇게
5. **부록 E 형식의 "버린 대안" 표** → exp66 Stage C + coverage-only + β 대안 묶기
6. **부록 F 형식의 "껐던 기능과 이유"** → strict 계약 S1–S6의 논문 내 서식
7. **품질과 시간을 같은 표에** (Table 4)

## ✗ 우리와 다른 점

- **offline batch.** 전 view 고정, causal 제약 없음.
- **densification을 껐다.** 우리는 pool이 성장하는 것 자체가 문제 설정이다 → 우리가 더 어려운 조건.
- **Limitations를 독립 절로 안 둠.** CVPR 최근 관행상 우리는 두는 쪽이 안전하다.
- **mean±std 없음.** 단일 수치 보고.

## 없는 move

| 이 논문에 없는 것 | 우리에게 필요한가 |
|---|---|
| 인과/스트리밍 계약 | **필요** |
| 하드웨어 전이 (rate invariance) | **필요** (P02) |
| 반복 실행 mean±std | **필요** — 우리 protocol이 더 엄격 |
| 예산 고정 하의 비교 | **필요** — taming3dgs 참조 |
