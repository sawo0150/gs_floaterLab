# 4. Experiments

latex 대상: `latex/sec/4_experiments.tex` (Overleaf 파일명은 `sec/5_results.tex`)

> 2.2 p. **번호 붙은 소절 3개.**

## 왜 Setup 에 번호를 주나 (2026-09-08 정정)

표본을 5편 → 8편으로 늘리니 결론이 뒤집혔다.

| Setup 에 번호? | 논문 | Setup 줄 수 |
|---|---|---|
| **✓** | MonoGS 31 · SparseGS 37 · CoMapGS 15 · CaRtGS 37 · Taming3DGS | **5편** |
| ✗ | chen2026cover 33 · lmrs 36 · VIGS-SLAM 17 | 3편 |

**다수가 번호를 주고, 길이는 번호 유무와 무관하다** (15~37줄). 이전 "5편 중 3편이 안 준다" 는
표본 부족이었다. → `4.1 Setup / 4.2 Main Results / 4.3 Ablations`.

## 구성

| 소절 | 분량 | 문단 | 산출물 |
|---|---:|---|---|
| [4.1 Setup](4-0_setup/) | 0.32 p | run-in 4: `Datasets.` `Metrics.` `Implementation details.` `Baselines.` | — |
| [4.2 Main Results](4-1_main_results/) | 0.60 p | Results pointer → 같은 스트림·같은 시간 → 장면별 갈림 → **진 곳** | **Table 1, Table 2** |
| [4.3 Ablations](4-2_ablations/) | 0.69 p | 예산 봉인 → run-in 3: `View growth.` `Count balancing.` `Carving.` | **Table 3**, Fig.4 |

## 4.1 Setup 에 무엇이 들어가나 — 코퍼스 8편 항목별

| 항목 | 몇 편 | 실물 |
|---|---:|---|
| 데이터셋 + **분할 규약** | 8/8 | SparseGS *"every eighth image as testing view"* · VIGS-SLAM *"frames not used as keyframes by any method"* |
| 지표 | 8/8 | |
| Baseline 목록 | 7/8 | |
| **Implementation (하드웨어·하이퍼파라미터)** | **6/8** | CaRtGS *"RTX 4090, Ryzen 9 7950X, 128GB RAM"* |
| 출처·공정성 선언 | 4/8 | CoMapGS · VIGS-SLAM · Taming3DGS |
| 제약 + **그 이유** | 4/8 | MonoGS *"Since Replica is designed for RGB-D … we hence use it for RGB-D only"* |
| **새 지표를 Setup 에서 정의** | 3/8 | CaRtGS 의 **IPF** · Taming 의 `Peak #G` · VIGS-SLAM 의 `Recall` |
| 반복 횟수 + mean±std | 2/8 | CaRtGS *"performed all experiments 5 times"* |
| 도구 명시 | 4/8 | CaRtGS *"evo¹, torchmetrics²"* (각주 URL) |

배울 점 셋:
1. **"기본값 유지, 바꾼 것만"** — CaRtGS 는 3DGS 기본값을 유지하고 **차이만** 나열한다
2. **새 지표는 Setup 에서 정의** — CaRtGS 의 IPF. 우리 `ρ_H` 를 §3.2 에서 여기로 옮긴 근거
3. **제약마다 이유를 그 자리에서** — MonoGS

### `Streaming contract.` run-in 은 두지 않는다 (2026-09-08)

코퍼스 어디에도 그런 run-in 이 없다. 그리고 1× 실시간으로 정하면서
논문에 실제로 필요한 것은 **zero-tail 과 online pose 둘**로 줄었다 (예산은 스트림 길이 그 자체).
→ **`Implementation details.` 안 한 문장.** VIGS-SLAM 이 같은 내용을 `Baselines.` 안 한 문장으로
처리한 선례를 따른다.

## 4.2 는 왜 이 네 문단인가 — 코퍼스 결과 소절의 세 축

| 축 | 무엇으로 나누나 | 실물 |
|---|---|---|
| ① 능력별 | 주장하는 능력마다 문단 | **MonoGS 4.2** (`Camera Tracking Accuracy` → `Novel View Rendering`) · VIGS-SLAM 4.1 |
| ② 데이터셋별 | 데이터셋마다 문단 | **CoMapGS 4.2** (`LLFF.` → `Mip-NeRF 360.`) · CaRtGS IV.B |
| ③ 시나리오별 | 표를 상/하로 갈라 두 비교 축 | **Taming3DGS 5.2** (같은 예산→품질 / 같은 품질→예산) |

우리는 **1× 하나뿐이라 ③이 안 맞고, tracking 이 기여가 아니라 ①도 안 맞는다** → **②**로 간다.

### 문단마다 같은 꼴 (MonoGS)

```
[표 지목] → [결과] → [무엇을 안 쓰고 얻었는지] → [어디까지만] → [그래서 무슨 뜻인가]
```

### 코퍼스가 반복해서 하는 것 넷

| | 실물 |
|---|---|
| **무엇을 안 쓰고 얻었는지** | MonoGS *"without requiring any deep priors"* |
| **진 곳을 먼저 인정 + 이유** | CoMapGS *"second only to ReconFusion … likely due to diffusion-based methods"* · chen2026cover *"a random baseline is performant"* |
| **재현 수치임을 밝힘** | CoMapGS + 표에 `†` |
| 부수 지표를 곁들임 | MonoGS *"rendering FPS is hundreds of times faster"* |

★ **P2 의 `without …` 이 §4.1 계약을 회수하는 자리다.** Setup 에서 zero-tail·online pose 를
선언만 하고 결과에서 안 쓰면 계약이 값을 못 한다.
★ **P4(진 곳)를 미리 자리 잡아둔다.** 결과가 나온 뒤 끼워 넣으면 변명처럼 읽힌다.

### 2026-09-08 에 뺀 것

| 뺀 것 | 어디로 |
|---|---|
| `Compute and latency.` 문단 | **P2 에 흡수.** Table 1 이 이미 자원 열을 들고 있어 "풀어 설명"은 표의 반복 |
| "장면별 재튜닝 없음" 문단 | **`Implementation details.` 한 문장.** 어떻게 돌렸는지에 대한 진술이므로. Table 2 는 P3 이 읽는다 |

### 분량 참고

| 소절 | 줄 |
|---|---:|
| lmrs 5.1 Comparison | 41 |
| MonoGS 4.2 | 52 |
| **우리 4.2** | **50 + 표2** |
| CoMapGS 4.2 | 116 |
| Point-SLAM 4.2 | 193 |

## §3 과의 대칭

§4.3 의 run-in 이름 = §3 소절 이름 = §3 도입에서 붙인 문제 이름. **순서도 같다.**

| §3 | §4.3 |
|---|---|
| 3.1 Compute-Paced View Growth | `View growth.` |
| 3.2 Entropy-Regularized Count Balancing | `Count balancing.` |
| 3.3 Causal Free-Space Carving | `Carving.` |

## 표·그림 (3표 4그림)

⚠ **2026-09-08: Fig.4(rate invariance) 폐기** — 단일 GPU·pace 스윕 없음으로 그릴 실험이 사라졌다.
근거: [`../../notes/decisions/2026-09-08_single-gpu-realtime.md`](../../notes/decisions/2026-09-08_single-gpu-realtime.md)

| 산출물 | 내용 | 어디 |
|---|---|---|
| Fig.1 teaser | | §1 |
| Fig.2 system diagram | | §3 도입 |
| Fig.3 view-growth trace | 법칙 대 실측 | **§3.1 안** |
| **Fig.4** floater 정성 비교 | (옛 Fig.5) | §4.3 |
| **Table 1** | 주결과. **시스템 baseline 4개** + 품질·자원 한 표 | §4.2 |
| Table 2 | 장면 일반화 | §4.2 |
| **Table 3** | ablation 3블록. **scheduler arm 6개가 여기로** | §4.3 |

★ **Table 1 과 Table 3 의 역할이 다르다.** Photo-SLAM·MonoGS·CaRtGS·VIGS-SLAM 은 *시스템* baseline
이고, fixed-FPS·random full-pool·covisibility·novelty-first·residual-first·clustering sampler 는
*scheduler* arm 이다. 이전에는 둘이 Table 1 에 섞여 있었다.

전체 지도는 [`../README.md`](../README.md), 실험 ↔ claim 매핑은
[`../../plan/experiment_table/CURRENT.md`](../../plan/experiment_table/CURRENT.md).
