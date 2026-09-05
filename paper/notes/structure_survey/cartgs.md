# cartgs — 구조 해부 (§3, §4)

## 기본 정보

| | |
|---|---|
| 논문 | CaRtGS: Computational Alignment for Real-Time Gaussian Splatting SLAM |
| venue | IEEE RA-L (accepted Feb 2025) — **저널 2단 조판, CVPR과 분량 규약 다름** |
| 전체 | 8쪽 (본문 ~7.5쪽 + 참고문헌) |
| §3 Methods | 약 3쪽, 수식 11개, 그림 3개(Fig 2·3·4) |
| §4 Experiments | 약 3쪽, 표 3개 + 그림 3개(Fig 5·6·7) |
| 왜 보나 | **계산 예산과 매핑 품질의 정렬**이 주제라 우리 C1과 문제의식이 가장 가까움 |

---

## §3 골격 — 이 논문의 핵심 구조적 발견

```
III. METHODS
  (무제목 Roadmap 문단)
  A. Computational Misalignment      ← 문제를 3개로 이름 붙여 쪼갬
       1) Insufficient Optimization
       2) Long-Tail Optimization
       3) Weak-constrained Densification
  B. System Overview                 ← 파이프라인 + 표기 + 배경 수식
  C. Adaptive Computational Alignment ← 해법 3개
       1) Fast Splat-wise Backpropagation   ← A.1 대응
       2) Adaptive Optimization             ← A.2 대응
       3) Opacity Regularization            ← A.3 대응
```

### ★ 가장 중요한 관찰: A와 C가 1:1 대칭이다

**§3.A가 문제를 N개로 이름 붙여 나열하고, §3.C가 같은 순서·같은 개수로 해결한다.**
독자는 A를 읽으며 문제 목록을 머리에 넣고, C에서 하나씩 지워나간다.
"이 방법이 왜 3개 부품으로 되어 있는가"를 따로 변명할 필요가 없어진다 — A가 이미 답했다.

우리에게 그대로 적용된다: **§3.0이 cardinality/membership/ordering 세 결정을 나열하고,
§3.1/§3.2/§3.3이 같은 순서·같은 이름으로 답하는 구조**를 이미 잡아뒀다. 이 논문이 그 구조가
실제로 통한다는 증거다.

### §3 문단 단위 해부

| 위치 | 문단 | 하는 일 (move) | 수식·그림 |
|---|---|---|---|
| III 도입 | 1 | **Roadmap.** "먼저 X 현상을 분석하고, 이를 극복할 Y 전략을 제안한다" 3문장 | — |
| A 도입 | 1 | **Diagnosis 예고.** 문제가 정확히 3가지임을 선언하고 이름을 미리 준다 | — |
| A.1 | 2 | [기존 GS-SLAM은 keyframe 기반 수천 iter] → [3DGS의 수만 iter에 못 미침] → [원인: pixel-wise backprop의 thread 경합] → **Bridge:** "In this paper, we utilize …" | — |
| A.2 | 2 | [무작위 keyframe 재최적화] → [오래된 keyframe 과적합/새 것 과소적합] → **In-method evidence: Fig 2** → **Bridge:** 적응적 선택 제안 | **Fig 2** |
| A.3 | 1 | [densification은 저opacity pruning만으로 통제] → [모델 크기 통제에 불충분] → **Bridge:** opacity 정규화 | — |
| B | 2 | **Preliminaries.** front-end/back-end 파이프라인, 표기 정의(p,q,s,σ,SH), α-blending | **Eq (1)**, **Fig 3** |
| C 도입 | 1 | 전략 이름 선언 + 하위 단계 예고 | — |
| C.1 | 5 | **Mechanism.** 기존 pixel-wise의 한계 → splat-wise 전환 → forward/backward 동작 → **In-method evidence** | **Eq (2)(3)(4)**, **Fig 4a/4b** |
| C.2 | 3 | **Mechanism.** pool·잔여 iter·loss 집합 정의 → 갱신 규칙 → 재충전 규칙 | **Eq (5)(6)(7)(8)** |
| C.3 | 1 | **Mechanism.** opacity 정규화 항을 전체 loss에 결합 | **Eq (9)(10)(11)** |

### 배울 점 3가지

**1. 배경 수식과 기여 수식을 절로 분리한다.**
Eq (1)(α-blending)은 §3.B **Preliminaries**에 두고 "3DGS에서 가져온 것"임을 인용으로 명시한다.
기여 수식 (2)–(11)은 전부 §3.C에 있다. 독자가 어디부터가 이 논문의 것인지 헷갈리지 않는다.
→ **우리도 3DGS 표현식과 VIGS-SLAM 배경은 §3.0에 몰고, token law·Gibbs 유도는 §3.1/§3.3에만 둔다.**

**2. 정량 근거를 §3 안에 넣는다.**
Fig 2(34.9→36.4 dB)는 §3.A.2 **문제 서술 안에**, Fig 4b(4.6k→15.4k iter)는 §3.C.1 **해법 서술 안에** 있다.
§4를 기다리지 않는다. 과기글 IMRaD 프레임워크에는 없는 CS 학회 관행이다.
→ **우리도 exp73의 "526 poll 전부에서 정수 오차 0"을 §3.1 안에 Fig로 넣을 수 있다.**
독자가 §3.1을 읽는 시점에 "이게 실제로 성립하는가"를 바로 해소해준다.

**3. 해법마다 문단 수를 다르게 준다.**
C.1은 5문단, C.2는 3문단, C.3은 1문단이다. 균등 배분하지 않는다.
새롭거나 설명이 필요한 것에 지면을 몰아준다.
→ 우리 배분(§3.1 0.75p / §3.2 0.5p / §3.3 0.75p / §3.4 0.75p)도 균등하지 않게 잡아둔 것과 일치.

---

## §4 골격

```
IV. EXPERIMENTS
  A. Setup      — run-in 볼드 소제목 (Dataset. …)
  B. Results    — 표 3개를 한 번에 가리키고 → 데이터셋별 문단 → ablation → 진단 그림
V. LIMITATIONS AND FUTURE WORK   ← 독립 절
VI. CONCLUSION
```

| 위치 | 하는 일 | 산출물 |
|---|---|---|
| A | **Dataset.** 3가지 카메라(mono/RGB-D/stereo) × 3개 데이터셋. 각 데이터셋을 1–2문장으로 소개 | — |
| B 첫 문단 | **Results pointer.** Table I·II·III을 한 문장으로 모두 가리키고 최우수 표기 규칙을 밝힘 | — |
| B | **Per-axis result.** 데이터셋별 문단 | Table I·II·III |
| B | 정성 비교 | Fig 5 |
| B | **Ablation** — 레이더 차트 | Fig 6 |
| B | **Diagnostic figure** — opacity 정규화의 효과(품질 vs 모델 크기) | Fig 7 |
| V | **Limitations** 독립 절 | — |

### §4 지표 설계 — 여기가 우리에게 제일 유용하다

표 하나에 **품질과 시스템 지표를 나란히** 놓는다:

| 지표 | 뜻 | 우리 대응 |
|---|---|---|
| ATE | 궤적 정확도 | (우리는 tracking 기여 아님 — 생략 가능) |
| **FPS** | 실시간성 | 우리 wall-time / 1.5× budget |
| **IPF** | **iterations per frame** | ★ 우리 admission slope·streaming update와 정확히 같은 성격 |
| PSNR | 렌더 품질 | held-out PSNR |
| **Points** | Gaussian 개수 = 모델 크기 | 우리 final pool / Gaussian 수 |

★ **IPF(iterations per frame)를 품질 표에 같이 넣는다**는 게 핵심이다.
"품질이 좋아졌다"가 아니라 "**같은 계산량에서** 품질이 좋아졌다"를 표 하나로 보여준다.
→ 우리 Table 1에도 `held-out PSNR | wall-time | streaming update | final pool`을 함께 넣어야 한다.
지금 `plan/experiment_table/`에 지표는 있지만 **한 표에 묶는다는 결정은 없다.**

★ **모든 수치를 `mean ± std`로 보고한다.** 우리 protocol(3회 반복 mean±std)과 일치 — 좋은 확인.

★ **Limitations를 독립 절로 둔다.** 우리 `sections/06_limitations/`를 살릴 근거.

---

## ★ 훔칠 것 (우선순위 순)

1. **§3.A(문제 N개 명명) ↔ §3.C(해법 N개, 같은 이름·순서) 대칭 구조** — 우리 §3.0↔§3.1-3.3에 이미 있음, 강화할 것
2. **각 Diagnosis 항목을 "In this paper, we …" 한 문장(Bridge)으로 닫기** — 문단 계약에 표준 항목으로 넣기
3. **In-method evidence** — exp73의 token-law 정수 오차 0을 §3.1 안에 배치
4. **배경 수식(§3.0)과 기여 수식(§3.1/3.3) 분리**
5. **품질 + 계산량을 한 표에** (IPF 자리에 streaming update / admission slope)
6. **Limitations 독립 절**

## ✗ 우리와 다른 점 (따라 하면 안 되는 것)

- **저널(RA-L) 규약이다.** CVPR 8쪽 제한과 다르고 §5를 독립 절로 뺄 여유가 우리에겐 적다.
- **인과 계약(causal contract)이 없다.** strict streaming, zero-tail, MPS 미사용 같은 조건 정의가 없다.
  **이건 우리 차별점이므로 반드시 §4.1 Setup에 명시적으로 넣어야 한다.**
- **유도(derivation)가 없다.** 수식이 전부 "정의와 절차"이지 최적화 문제를 풀어 해를 얻는 형태가 아니다.
  우리 §3.3(Lagrangian → Gibbs)은 여기서 배울 게 없다 → **`chen2026cover` 또는 `lmrs` 해부 필요.**
- **실패를 보고하지 않는다.** 우리는 exp72 lifetime 균등화 실패, exp73 κ=16 이상치를 실어야 한다.
  이 논문은 그 선례가 되지 못한다 → **negative result를 실은 논문을 따로 찾아야 함.**

## 없는 move (우리에겐 필요한가?)

| 이 논문에 없는 것 | 우리에게 필요한가 |
|---|---|
| Scope guard (무엇을 주장하지 않는가) | **필요.** claims의 금지 목록이 곧 이 move다 |
| 인과 계약 정의 | **필요.** 우리 핵심 차별점 |
| 수식의 유도 과정 | **필요.** §3.3 |
| 실패·이상치 보고 | **필요.** exp72 실패, exp73 κ=16 |
| 하이퍼파라미터 전이성 논의 | **필요.** κ=22의 2장면 전이 — 이 논문은 `d`를 그냥 상수로 둠 |

→ 없는 move가 5개나 되고 **전부 우리에게 필요하다.** 즉 CaRtGS는 §3의 *뼈대*(문제↔해법 대칭)와
§4의 *지표 설계*를 배울 대상이지, 서술의 엄밀성까지 배울 대상은 아니다.
