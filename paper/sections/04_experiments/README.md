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

## §4.3 Ablations — 2026-09-08 코퍼스 재조사 후 개정

코퍼스 8편 실측: taming 5.3 · lmrs 5.2 · sparsegs 4.3 · vigsslam 4.3 · chen 5.2 ·
comapgs 4.3 · edgs 4.5 · tidigs F.

### 분량 (본문 words, 표·그림 제외 근사)

| | words |
|---|---:|
| vigsslam 4.3 | 77 |
| comapgs 4.3 | 183 |
| taming 5.3 | 218 |
| edgs 4.5 | 245 |
| chen 5.2 | 277 |
| **우리 4.3** | **~365** (43 slot 줄) |
| sparsegs 4.3 | 385 |
| lmrs 5.2 | 442 |

→ **길이는 이미 적정.** 고친 것은 구조다.

### 코퍼스가 실제로 하는 것 6가지

**1. 여는 문단은 2~3문장에 네 가지 일을 한다** — 무엇을 바꾸는지 / 어느 데이터로 /
무엇을 붙잡아 뒀는지(seal) / 어디를 보라(표·그림 지목).
seal 은 taming 만의 습관이 아니다 — tidigs 도 한다:
*"We disabled individual mechanisms while keeping the training budget and camera paths identical
across all runs."* (taming: *"all configurations yield the same number of Gaussians"*)
⚠ 이전 우리 버전은 seal 만 있고 나머지 셋이 없었다 → 한 슬롯으로 합침. 우리는 봉인할 교란이
셋(스트림·실시간 예산·시드, 그리고 장면별 재튜닝 없음)이므로 셋 다 이름을 부른다.

**2. run-in 은 4/8 이 쓰고, 쓸 때는 "끌 수 있는 것 하나 = run-in 하나"** — 이름과 순서가
§3 소절과 같다. lmrs 는 절 번호를 본문에 박는다 (*"in Sec. 4.3"*, *"in Sec. 4.4"*, *"(Sec. 4.5)"*).
→ 우리 `View growth.` / `Count balancing.` / `Carving.` 은 이미 맞다. **유지.**

**3. 항목 문단의 꼴 (lmrs 가 가장 정확)**
(a) 목적 재진술 + §역참조 → (b) 표 지목 → (c) 행을 이름 대며 순서대로 → (d) **숫자 하나로 닫음.**
sparsegs 는 (d)를 세 항목 전부에서 지킨다 (1.37dB / 0.33dB / 0.28dB).
→ 우리 세 항목도 각각 숫자 하나로 끝난다.

**4. 표 전체를 한 문장으로 읽는 종합 문장이 따로 있다**
vigsslam: *"Table 6 demonstrates that removing any component will degrade tracking accuracy as
well as robustness, while our full system achieves the best results."*
tidigs: *"These ablations trace a clear causal chain."* + 한 문단.
→ **우리에겐 이게 §3 도입의 '한 원인, 세 결과'를 회수하는 자리다.** 세 정책이 **서로 다른
방식으로** 품질을 잃어야 세 소절이 한 문제의 세 얼굴이라는 주장이 증거를 얻는다. 끝에 3줄 신설.

**5. 자기보다 나은 행을 지우지 않는다**
| 논문 | 실물 |
|---|---|
| taming Tab.2 | `-reduce SH frequency` 가 PSNR **25.39 > 우리 25.20**. 그대로 싣고 "속도 50% 손해"로 답함 |
| lmrs Tab.2 | `Random, MBS=32` (21.68) 가 `Clustering, MBS=16` (21.37) 을 이김 — **교란축이 기여축을 이기는 표를 스스로 실음** |
| lmrs Tab.3 | 자기가 고른 N=32 가 품질에서 N=64 에 열세 (28.59 vs 28.66), 시간으로 정당화 |
| chen | *"only as good as the random baseline in very sparse initialization regimes"* |
→ **κ=16 이상치와 K=128,β=0 부재를 표 안 `\pend` 로 숨기지 않는다.** 본문에 자리를 준다.
빈 셀만 두면 실수로 읽힌다.

**6. ★ 표 형태 — 이전 Table 3 의 진짜 결함**
코퍼스의 ablation 표는 두 종류뿐이다.
- **(i) 제거축 한 개** — 행 = "무엇을 뺐나". taming · edgs · tidigs · vigsslam · sparsegs
- **(ii) setting × method** — chen Tab.2 (+ oracle 상한 행)

**세 개의 독립 축을 `\multirow` 로 한 표에 겹친 예는 8편 중 0편이다.**
항목이 3개인 lmrs 는 **표를 3개로 나눠 각 문단 옆에 둔다.**
이전 우리 Table 3 은 growth/ordering/carve 세 축을 겹쳐 놓고 `ρ_H`·`sel. CV`·`life mid/first`
열을 공유시켰는데, **그 세 열은 ordering 축에만 정의된다** — 셀의 2/3 이 무의미해진다.

### 그래서 바꾼 것

| 이전 | 지금 | 근거 |
|---|---|---|
| 봉인 문장 1개 (5줄) | **OPENER**: 범위+데이터+봉인+지목 (5줄) | 코퍼스 여는 문단의 네 가지 일 |
| Table 3 하나에 3블록 13행, `ρ_H` 등 공유 | **Table 3**: 제거축 8행, **전 행에 정의되는 열만** (PSNR/SSIM/LPIPS/updates/final) | taming·edgs 꼴 |
| — | **Table 4 신설**: ordering 축 전용 진단 (`ρ_H`/`sel. CV`/lifetime), **K 를 행으로 내려 β 옆에** | lmrs Tab.2 (교란축 동거) |
| κ sweep 이 Table 3 행 | **본문 숫자 + 보충자료** | 코퍼스에서 하이퍼파라미터 sweep 은 ablation 표 밖 (taming Fig.1, tidigs Tab.II) |
| clustering sampler 행 | 보충자료 | lmrs App E (rejected alternatives) |
| 종합 문장 없음 | **CLOSING 3줄** | vigsslam · tidigs |

### 남은 부채

- `sel. CV` 와 `life mid/first` 가 **§4.1 Metrics 에 정의돼 있지 않다** (`ρ_H` 만 정의됨).
  표에 쓰려면 Setup 에서 정의하거나 표에서 빼야 한다.
- `K=128, β=0` arm 미측정 → β 단독 효과가 아직 없음.
- κ=16 이상치 (22.163 dB, −5.545) 를 실을 문장이 아직 없음.

## 표·그림 (4표 4그림)

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
| **Table 3** | ablation **제거축 8행** (2026-09-08: 3블록 `\multirow` 폐기) | §4.3 |
| **Table 4** | ordering 축 전용 진단 `K×β` (2026-09-08 신설) | §4.3 |

★ **Table 1 과 Table 3 의 역할이 다르다.** Photo-SLAM·MonoGS·CaRtGS·VIGS-SLAM 은 *시스템* baseline
이고, fixed-FPS·random full-pool·covisibility·novelty-first·residual-first·clustering sampler 는
*scheduler* arm 이다. 이전에는 둘이 Table 1 에 섞여 있었다.

전체 지도는 [`../README.md`](../README.md), 실험 ↔ claim 매핑은
[`../../plan/experiment_table/CURRENT.md`](../../plan/experiment_table/CURRENT.md).
