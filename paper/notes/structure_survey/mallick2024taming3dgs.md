# mallick2024taming3dgs — 구조 해부 (§3, §4, §5)

## 기본 정보

| | |
|---|---|
| 논문 | Taming 3DGS: High-Quality Radiance Fields with Limited Resources |
| venue | SIGGRAPH Asia 2024 (여기 PDF는 arXiv **1단 조판** — 분량 감각은 우리와 다름) |
| 전체 | 13쪽 |
| 절 구성 | 1 Intro / 2 Related / **3 Method** / **4 3DGS Runtime Analysis and Optimization** / 5 Evaluation and Discussion |
| 왜 보나 | **사용자가 예산을 주면 정확히 그 예산에 도달하는 최적화.** 우리 C1(token admission)과 문제가 같다 |

---

## ★ 발견 1 — Method를 **알고리즘(§3)과 시스템(§4)으로 절을 갈랐다**

```
3. Method                                    ← 알고리즘 기여
   3.1 3DGS Background
   3.2 Predictable Model Growth              ← 예산 스케줄
   3.3 Steerable Densification with Sampling ← 무엇을 뽑을지
   3.4 High-Opacity Gaussians
4. 3DGS Runtime Analysis and Optimization    ← 시스템/CUDA 기여
   4.1 Backpropagation with Per-Splat Parallelization
   4.2 Accelerated SH and Differentiable Loss Computation
5. Evaluation and Discussion
```

기여 성격이 다르면 절을 나눈다. §4는 **프로파일링으로 시작**한다:

> *"To better understand the performance challenges of 3DGS, we benchmark the original training pipeline...
> We provide a breakdown of the time taken by the high-level steps in each iteration ... in Fig. 3a.
> **We note that, throughout the training routine, backpropagation of gradients is the dominating bottleneck**,
> closely followed by ADAM optimizer updates as the number of Gaussians increases.
> **With these insights, we propose targeted solutions.**"*

= **측정 → 병목 지목 → 표적 해결**. Diagnosis를 주장이 아니라 프로파일로 세운다.

→ 우리 C1도 근본적으로 "GPU가 실제로 감당한 service를 측정해서 admission으로 바꾼다"이므로
**§3.1을 이 형식으로 열 수 있다**: 고정 FPS·maturity gate 하의 실측 → 무엇이 병목인지 → token law.

## ★ 발견 2 — §3.2가 우리 §3.1과 **거의 같은 구조**다 (가장 중요)

§3.2 Predictable Model Growth, 4문단:

| 문단 | move | 내용 |
|---|---|---|
| 1 | **Diagnosis** | *"the number of added primitives at each stage is decided based on a simple thresholding operation, **with no control over the progressive or final count.** This evolutionary automaton—although effective—leads to **hard-to-predict, often exorbitant model sizes and fluctuating training times.**"* |
| 2 | **Empirical law** | *"we investigate the densification behavior ... across the outdoor scenes in MipNeRF360. Fig. 2b plots the development in the number of total Gaussians ... **We find that the number of Gaussians added in each step follows a trend of quadratic decrease.**"* |
| 3 | **Mechanism** | 그 관찰을 포물선 스케줄로 고정: `A(x) = ((B−S−2N²)/N²)x² + 2x + B` (N=densification step 수, B=최종 예산, S=SfM 초기점) |
| 4 | **Correction rule** | *"Since 3DGS prunes low-opacity Gaussians over time, following an additive schedule directly may produce fewer primitives than the given target. To avoid this, we instead compute **the difference between our current and accumulated target count** and densify the corresponding number."* + **Forward pointer**: *"Sec. 5 demonstrates the effectiveness of this scheme and the graceful quality degradation resulting from lower budget limits."* |

우리 §3.1과 대응:

| Taming3DGS §3.2 | 우리 §3.1 |
|---|---|
| threshold densification은 최종 개수를 통제 못 함 | maturity gate는 admission을 pool 크기에 종속시킴 |
| Gaussian 증가가 quadratic decrease (관찰) | 완료된 GPU service `S(t)` (측정) |
| `A(x)` 포물선 스케줄 | `A*(t) = min(M(t), A₀ + ⌊(B₀+γS(t))/κ⌋)` |
| pruning 때문에 목표에 못 미침 → **누적 목표 대비 차이로 보정** | prune/소멸 후 `Q_t = min(\|C_t\|, [A*(t) − \|A_{t⁻}\|]₊)` — **같은 형태의 보정** |
| "Sec. 5가 낮은 예산에서의 graceful degradation을 보인다" | κ 스윕이 그 자리 |

★ **4번째 문단(누적 목표 보정 규칙)이 우리 carry vs no-prepurchase 미결정과 정확히 같은 자리다.**
Taming3DGS는 그것을 **한 문장으로 정의하고 이유(pruning)를 붙여 끝낸다.**
우리도 그 정도 분량이면 충분하다는 뜻 — 지금 열려 있는 결정을 §3.1에서 두 문장으로 닫을 수 있다.

## ★ 발견 3 — §5.2가 **"budgeted scenario 2개"**로 나뉜다

```
Scenario 1 (top half of Table 1)   : 장면별로 합리적 예산을 정함
    → 비교 대상 = 압축·경량화 계열 (C3DGS, R-VQ, Mini-Splatting, INGP-Big)
    → 논지 = "같은 품질을 훨씬 적은 자원으로"
Scenario 2 (bottom half, same table): 3DGS와 **정확히 같은 모델 크기**로 맞춤
    → 비교 대상 = 고품질 계열 (3DGS, MipNeRF360, Zip-NeRF, Plenoxels)
    → 논지 = "같은 자원에서 더 좋은 품질"
```

**표 하나를 위아래로 갈라 두 시나리오를 담는다.** 그리고 두 번째 시나리오의 존재 자체가
기여를 증명한다 — *"we demonstrate that our budgeting mechanism allows to **match their model size exactly**."*

★ **예산의 정확성이 곧 헤드라인 결과다.** 각주가 아니다.
→ 우리 exp73의 "526개 admission poll 전부 정수 오차 0"은 **Table 1의 한 열 또는 §3.1의 Fig가 되어야지,
"검증했다" 한 줄로 흘리면 안 된다.** 지금 계획에선 Fig.3에만 있고 표에 없다.

또 예산 산정 근거를 숨기지 않는다 — MipNeRF360 실내 2×, Deep Blending 5×, 야외 15×, T&T 2×
(SfM 점 수 대비). 그리고 바로 한계를 인정: *"Note that this parameterization could be automatized
by providing scenes in real-world coordinates."*
→ 우리 `κ=22`도 같은 식으로 **"어떻게 정했고, 자동화되지 않았다"**를 붙여야 한다 (금지 문장 #3 대응).

## ★ 발견 4 — Ablation이 **예산 고정 하에서** 이루어진다

Table 2(Tanks&Temples) 앞 문장:

> *"**Note that all configurations yield the same number of Gaussians.**
> However, omitting the consideration of image loss (or our score-based sampling altogether) from
> densification significantly harms quality."*

교란변수를 먼저 봉인하고 시작한다. 표는 `Ours / −score-based sampling / −image loss / −high opacity /
−reduce SH frequency / −per splat backward`의 6행이고 각 장면마다 `PSNR | LPIPS | Time`을 준다.

- **품질이 좋아지는 ablation도 싣는다**: `−reduce SH frequency`는 PSNR 25.39로 Ours 25.20보다 **높다.**
  대신 시간이 7m→9m로 는다. 숨기지 않고 trade-off로 설명한다.
- **품질이 동일한 ablation도 싣는다**: `−per splat backward`는 품질 동일(25.20/0.165), 시간만 7m→14m.
  = 순수 시스템 최적화임을 표로 증명.

→ ★ **우리 ERCB ablation은 반드시 "동일 admission 예산·동일 wall-time" 문장을 표 앞에 붙여야 한다.**
안 그러면 β 효과와 pool 크기 변화가 섞인다.
→ 그리고 exp72의 1253 −0.084 dB(손해)도 이 형식이면 그대로 실을 수 있다.

## ★ 발견 5 — 예산 스윕은 **한 장면 case study**로 (Fig. 1)

> *"As an additional case study, Fig. 1 ablates the quantitative effect on GARDEN when varying the
> available budget. We see a consistent improvement as budget increases, showing a clear correlation
> between provided budget and achieved image quality."*

전 장면 스윕이 아니라 대표 1장면. 지면 대비 효율이 좋다.
→ 우리 κ 스윕(κ=16 이상치 포함)도 aria1253 한 장면 case study로 충분하다.

## §5.1 Datasets and Metrics — 지표를 **품질과 자원 두 묶음**으로 선언

> *"In addition to common quality metrics (PSNR, SSIM, LPIPS), **an important focus of our work is
> resource efficiency**... We assess these qualities by timing the optimization (Train time), counting the
> final number of Gaussians (#G), as well as **recording the peak number (Peak #G) during training.**"*

★ **Peak #G를 따로 재는 것**이 핵심이다. 최종 크기만 보면 "일단 왕창 만들고 잘라내는" 방법과
"처음부터 예산 안에서 짓는" 방법이 구별되지 않는다. §5.2에서 이걸로 Mini-Splatting을 잡는다 —
peak/final 격차가 최대 10×인 반면 *"our method uses a purely constructive optimization that only adds
Gaussians towards an exact target budget."*

→ ★ **우리도 `final pool` 하나로는 부족하다. `peak pool`과 `총 admission 수`를 같이 재야
"pool-independent"가 무슨 뜻인지 표에서 보인다.** 현재 experiment_table에는 `최종 pool 크기`만 있다.

---

## ★ 훔칠 것

1. **§3.2의 4문단 형식** (Diagnosis → 경험 법칙/측정 → 스케줄 식 → 보정 규칙 + forward pointer) → **우리 §3.1에 그대로**
2. **예산 정확성을 헤드라인 결과로** — exp73 정수 오차 0을 표에 열로
3. **budgeted scenario 2개**: (a) 같은 예산에서 품질, (b) 같은 품질에서 예산 — 표 상/하단
4. **ablation 앞 "모든 config가 동일 예산" 봉인 문장**
5. **불리하거나 동률인 ablation 행도 그대로 싣고 trade-off로 설명**
6. **peak vs final 이중 계측** — 우리 peak pool / 총 admission 수
7. **예산 산정 근거 공개 + 자동화 안 됐음 인정** → κ=22 서술
8. **프로파일 먼저(§4 도입)** — 측정으로 병목을 지목하고 표적 해결

## ✗ 우리와 다른 점

- **1단 13쪽.** 문단이 길고 여유롭다. CVPR 2단 8쪽에서 이 밀도로 쓰면 못 들어간다.
- **offline batch 최적화.** 전 view가 처음부터 있고 순서 제약이 없다. 우리 causal 계약이 여기 없다.
- **유도가 없다.** `A(x)`는 곡선 적합이지 최적화 해가 아니다 → §3.3은 chen2026cover/lmrs를 봐야 한다.
- **실패한 시도를 안 싣는다.**

## 없는 move

| 이 논문에 없는 것 | 우리에게 필요한가 |
|---|---|
| 인과/스트리밍 계약 | **필요** |
| 유도 | **필요** (§3.3) |
| 하드웨어 전이 실험 | **필요** (P02: 5090 vs 5070Ti) — 이 논문은 A4500 1대뿐 |
| 실패 기록 | **필요** |
| mean±std | **필요** — 이 논문은 단일 수치만 보고. 우리 protocol이 더 엄격하다 |
