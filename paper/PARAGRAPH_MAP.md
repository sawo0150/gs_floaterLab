# §3 · §4 문단·표 배치도 (2026-09-09)

> **한눈에 보는 용도.** 소절을 어떻게 나눴고, 문단을 어떻게 배분했고, 어떤 설명이 어디에
> 사는지. 근거와 코퍼스 실측은 각 `sections/*/README.md` 와 `notes/structure_survey/` 에 있다.
> 실물은 `latex/sec/4_method.tex`(=§3) · `latex/sec/5_results.tex`(=§4).
> 한 쪽 ≈ 110줄. 본문 8쪽(references 제외).

---

## 0. 전체 지도

```
§3 Method                                                   3.0p
├─ ROADMAP  (무제목, 7문장)                                  19줄
├─ 3.1 Compute-Paced View Growth                             95줄  0.86p
│   ├─ [Fig.3]  in-method evidence: 법칙 vs 실측
│   ├─ P1  왜 학습 집합이 자라나, 왜 상한을 못 두나            16
│   ├─ P2  왜 keyframe 규칙이 틀린 답인가                      12
│   ├─ P3  ★ 무엇을 계량할 것인가 (기여)                       16
│   ├─ P4  불변식 → 상한            [eq.1][eq.2]              10
│   ├─ P5  실현 quota · discard · 정책  [eq.3]                 12
│   └─ run-in `Slot placement.`  (기여 아님, +0.35%)            6
├─ 3.2 Entropy-Regularized Count Balancing                   93줄  0.85p
│   ├─ P1  이상적 스케줄이 원하는 두 가지 (a)mixing (b)spread   16
│   ├─ P2  (b)를 퍼텐셜로     [eq.4 Φ]                         10
│   ├─ P3  ★ 유도 + 등식 감사  [eq.5 objective][eq.6 Gibbs]    20
│   ├─ P4  K-뷰 확장 (Plackett–Luce) + 언제 정확한가           22
│   └─ P5  proxy 와 goal 이 갈리는 곳 (실패 보고)              16
└─ 3.3 Causal Free-Space Carving  [팀원]                      40줄

§4 Experiments                                              2.0p
├─ 4.1 Setup                                                 35줄  0.32p
│   ├─ run-in `Datasets.`                                      9
│   ├─ run-in `Metrics.`            (ρ_H 정의가 여기)          10
│   ├─ run-in `Implementation details.`  (계약이 여기)          9
│   └─ run-in `Baselines.`          (목록 아닌 선정 기준)       7
├─ 4.2 Main Results                                          50줄  0.45p
│   ├─ [Table 1] 주결과 · 시스템 baseline (2단 table*)
│   ├─ P1  결과 지목 + 출처 표기 규칙                           7
│   ├─ P2  ★ 같은 스트림, 같은 시간 (계약 회수)                18
│   ├─ [Table 2] 한 설정, 모든 시퀀스
│   ├─ P3  장면이 갈리는 곳과 그 이유                          14
│   └─ P4  우리가 지는 곳                                      11
└─ 4.3 Ablations                                             43줄  0.39p
    ├─ OPENER  범위 + 데이터 + 봉인 + 지목                      5
    ├─ [Table 3] 제거축 8행
    ├─ run-in `View growth.`                                  11
    ├─ [Table 4] ordering 전용 K×β
    ├─ run-in `Count balancing.`                              15
    ├─ [Fig.4] carve 정성 비교
    ├─ run-in `Carving.`  [팀원]                               9
    └─ CLOSING  표 전체를 한 번에 읽음                          3
```

---

## 1. 소절을 이렇게 나눈 이유

### §3 — 문제 소절을 따로 두지 않는다

진단(문제 서술)을 **독립 소절**로 뺀 것은 코퍼스 11편 중 **cartgs 1편뿐**이다
(Taming3DGS · LM-RS · chen2026cover · MonoGS · Point-SLAM · EDGS · SparseGS · CoMapGS 전부 없음).
지배적 패턴은 **진단을 각 소절 첫 문단에 분산**하는 것이고 우리는 그쪽을 따른다.
→ §3.1 은 P1·P2 가 진단, §3.2 는 P1 이 진단이다.

**Preliminaries 소절도 없다.** 표기 블록을 한 번 만들었다가 지웠다 —
`eq:splat`·`eq:maploss` 를 본문에서 **한 번도 참조하지 않았기** 때문이다.
쓰이지 않는 표기는 지면만 먹는다.

소절이 셋인 것은 §1 이 세운 묶는 논리에서 나온다:

> 온라인 매핑은 **아직 도착 중인** 데이터셋에 모델을 맞춘다. 이 하나의 사실이 offline 3DGS 가
> 딛고 선 세 가정을 각각 깨뜨린다.

| 깨지는 offline 가정 | 소절 |
|---|---|
| 고정 집합 위의 고정 예산 | §3.1 |
| 유한 고정합 위의 셔플링 | §3.2 |
| 가진 뷰로 결정되는 기하 | §3.3 |

### §4 — 번호 붙은 소절 3개

Setup 을 번호 없는 도입으로 뒀다가 바꿨다. 표본을 5편→8편으로 늘리니
**번호 있음 5편**(MonoGS·SparseGS·CoMapGS·CaRtGS·Taming) : **없음 3편**(chen·lmrs·vigsslam).
길이도 15~37줄로 번호 유무와 무관했다.

---

## 2. 문단 배분 — 균등하게 주지 않는다

cartgs 는 해법 소절에 5 / 3 / 1 문단을 준다. 새롭거나 설명이 필요한 것에 지면을 몰아준다.

| 어디 | 줄 | 왜 그만큼 |
|---|---:|---|
| §3.1 P3 | 16 | **이 절의 기여.** 후보 셋(wall-clock / iteration / completed service)을 비교하고 계보(RFC 2212)를 밝혀야 한다 |
| §3.1 P4 | 10 | 계량이 정해지면 장부는 짧다. 불변식 하나 → 상한이 따라옴 |
| §3.2 P3 | 20 | 유도 + 등식 감사. β=0 이 random reshuffling 과 **언제** 같은지를 조건까지 |
| §3.2 P4 | 22 | 도구 명명 + block freeze 가 **왜** 성립하는지. 여기가 §3 최장 |
| §3.3 | 40 | 팀원. 위 두 소절과 같은 꼴로 |
| §4.2 P2 | 18 | 품질 열을 자원 열 **against** 로 읽고, 계약을 회수 |
| §4.3 `Count balancing.` | 15 | 여기서만 세 가지 — regime 인정 → K vs β → proxy/goal 괴리 |
| §4.3 `Carving.` | 9 | 표 한 행 + 그림 하나. 짧아도 된다 |
| §4.3 CLOSING | 3 | 한 문장이면 되는 것에 문단을 주지 않는다 |

**§3.2 를 §3.1 과 대등하게(0.85p vs 0.86p) 맞춘 이유**는 코퍼스가 아니다.
P3·P4 가 각각 다섯 가지를 해야 하는데 16/14줄이면 항목당 3줄이라 **선언만 하고 근거를 못 단다**.
그리고 §3 에서 유도가 있는 소절이 제일 짧은 건 뒤집힌 배치다.

---

## 3. ★ 설명이 어디 사는가 (기능 분배)

같은 종류의 설명이 두 곳에 흩어지면 독자가 되돌아가야 한다. 한 종류 = 한 자리.

| 설명 | 사는 곳 | 근거 |
|---|---|---|
| **문제 진단** | 각 소절 첫 문단 (§3.1 P1·P2, §3.2 P1) | 진단 소절은 코퍼스 11편 중 1편 |
| **배경 표기·수식** | 없음 (Notation 블록 삭제) | 본문 참조 0회였다 |
| **유도 전개** (Lagrangian) | **보충자료.** 본문은 결과와 성립 조건만 | chen2026cover 가 *"automatic by Rayleigh quotients"* 반 구절로 처리 |
| **도구 계보** (RFC 2212 token bucket, Plackett–Luce) | **도구를 도입하는 그 문장 안** | 이름을 먼저 주면 독자가 기존 지식을 붙인다 |
| **선행 연구 소개** (experience replay 등) | §2 Related Work | §3 이 아니다 |
| **지표 정의** (ρ_H) | **§4.1 `Metrics.`** | 방법이 아니라 평가. cartgs 가 IPF 를 Setup 에서 정의 |
| **평가 계약** (zero-tail, online pose, 예산=스트림 길이) | **§4.1 `Implementation details.` 한 문장** | `Streaming contract.` run-in 을 따로 둔 선례가 코퍼스에 없다. vigsslam 은 `Baselines.` 안 한 문장으로 처리 |
| **계약의 회수** | **§4.2 P2 마지막 문장** | 선언만 하고 안 쓰면 계약이 값을 못 한다. MonoGS *"without requiring any deep priors"* |
| **in-method 증거** | **Fig.3 (§3.1 안)** | cartgs 가 Fig.2·4b 를 §3 안에 둔다. §4 를 기다리지 않는다 |
| **실패·이상치** | §3.2 P5 (proxy≠goal) · §4.2 P4 (지는 곳) · §4.3 본문 (κ=16, 미측정 arm) | lmrs·taming·chen 이 자기보다 나은 행을 그대로 싣는다 |
| **기여가 아닌 것** | run-in 으로 강등 (`Slot placement.`, +0.35%) | 약하다는 사실 자체가 P2 의 논거를 되받는다 |
| **하이퍼파라미터 sweep** | 본문 숫자 + 보충자료 | 코퍼스에서 sweep 은 ablation 표 **밖** (taming Fig.1, tidigs Tab.II) |
| **버린 대안** (clustering sampler 등) | 보충자료 | lmrs App E |
| **비교 불가 선언** | §4.1 `Metrics.` 끝 | vigsslam *"are not directly comparable to ours"* |
| **출처 표기 규칙** (재현/인용/실패) | §4.1 `Baselines.` 에서 규칙, 표에서 기호 | CoMapGS `†`, vigsslam `F` |

---

## 4. 문단 하나하나가 하는 일

### §3 도입 ROADMAP — 7문장 19줄

| # | 하는 일 |
|---|---|
| 1 | **전제.** 온라인 매핑은 아직 도착 중인 데이터셋에 모델을 맞춘다 |
| 2 | **대비.** offline 3DGS 의 세 가정이 그 하나에 깨진다. 기존 온라인 시스템은 셋을 keyframe 규칙 하나로 물려받는다 |
| 3 | **세 지점을 절 번호 없이 평범한 말로** — 얼마나 들어오나 / 어떤 순서로 다시 보나 / 아직 결정 안 된 기하를 무엇이 붙잡나 |
| 4 | **§3.1** — 고정 집합 위 고정 예산이 안 통한다 → 완료된 GPU service 가 속도를 정한다 |
| 5 | **§3.2** — 셔플링 전제가 안 통한다 |
| 6 | **§3.3** — 기하가 아직 안 정해진다 |
| 7 | **Fig.2** 로 한 원인의 세 결과를 그림 하나에 |

### §3.1 — 논증 사슬

```
더 쓰면 좋다(A2)  →  공짜가 아니다, 최적 밀도가 예산 따라 움직인다(A3)
   → 그러면 속도를 정해야 한다.  baseline 의 답 = keyframe.
     그건 속도를 집합 크기에 용접한다
   → 무엇이 속도를 정해야 하나  →  ★완료된 service (P3, 기여)
   → 계량이 정해지면 나머지는 장부 (P4 불변식→상한, P5 quota→discard→정책)
   → 어디에 둘지는 +0.35%  (run-in, P2 로 회귀)
```

### §3.2 — 유도 사슬

```
P1  이상적 스케줄은 (a)mixing 과 (b)낮은 early-to-late spread 둘 다 원한다.
    ★ 둘은 서로 당긴다 — uniform 은 (a)최대·(b)최악, least-count 는 (b)최적·(a)파괴.
    → "두 휴리스틱의 혼합"이 아니라 "둘 사이의 원리적 손잡이"를 만들 자리
P2  (b)를 퍼텐셜 Φ 로. greedy step = 최소선택 뷰 = 결정론적 = (a)의 손실
P3  ★ (a)를 패치가 아니라 항으로 되돌린다.  min Σp·ΔΦ − τH(p)
    counts 가 스텝 내 고정 → 단체 위 강볼록 → 유일해 Gibbs.
    우리 몫은 소거: ΔΦ 가 n_i 와 상수만큼 다르고 정규화에서 떨어진다
    + 등식 감사: β=0 은 K≥N_t 일 때만 random reshuffling 과 정확히 같다
P4  K개 무복원 = Plackett–Luce(=Gumbel-Top-k).  블록 시작에 counts 를 얼려 draw
P5  ★ counts 는 proxy 다. lifetime 비 0.758→0.520 로 나빠졌는데 PSNR 은 +0.362dB.
    일반화 주장을 하지 않는다 + 가설임을 라벨링
```

### §4.2 — 문단마다 같은 꼴

`[표 지목] → [결과] → [무엇을 안 쓰고 얻었는지] → [어디까지만] → [그래서 무슨 뜻인가]`

| 문단 | 하는 일 |
|---|---|
| P1 | Table 1·2 를 **한 번에** 지목 + 강조 규칙 + 출처 표기 |
| P2 | 품질 열을 자원 열 **against** 로 읽는다. "더 잘 그린다"가 아니라 "**같은 스트림에서 같은 시간에** 더 잘 그린다". peak/final 격차가 oversample-후-prune 을 드러낸다. 후처리 궤적 없이 · depth 센서 없이 · 스트림 종료 후 최적화 없이로 닫는다 |
| P3 | Table 2 — 한 설정, 모든 시퀀스. 자체 Aria 와 공개 데이터가 **어디서 왜** 갈리는지 |
| P4 | **지는 곳을 리뷰어보다 먼저 이름 부른다.** 이기는 방법이 쓰는 것 중 우리가 계약상 안 쓰는 것을 댄다 |

### §4.3 — 세 항목이 전부 같은 꼴 (lmrs)

`(a) 목적 재진술 + \S 역참조를 문장 안에 → (b) 표 지목 → (c) 행을 이름 대며 순서대로 → (d) 숫자 하나로 닫음`

sparsegs 는 (d)를 세 항목 전부에서 지킨다 (1.37 / 0.33 / 0.28 dB).

---

## 5. 표·그림 — 4표 4그림

| 산출물 | 축 / 내용 | 어디 | 형태 근거 |
|---|---|---|---|
| **Fig.1** teaser | | §1 | |
| **Fig.2** system diagram | 한 원인의 세 결과 | §3 도입 | ROADMAP 7번 문장이 지목 |
| **Fig.3** view-growth trace | 법칙 vs 실측 vs baseline gate | **§3.1 안** | cartgs 의 in-method evidence |
| **Fig.4** floater 정성 비교 | carve off / v7-64 / ported | §4.3 | sparsegs 가 floater pruning 행에 Fig.7 을 붙인다 |
| **Table 1** 주결과 | 시스템 baseline 5행 × (PSNR·SSIM·LPIPS ∥ wall-time·updates·peak·final) | §4.2 · 2단 `table*` | **품질+자원 한 표** — cartgs Table I(IPF), taming(train time·Peak #G) |
| **Table 2** 장면 일반화 | 시퀀스 × 품질 | §4.2 | CoMapGS 가 평균 대신 데이터셋별로 |
| **Table 3** ablation | **제거축 8행** × (PSNR·SSIM·LPIPS ∥ updates·final) | §4.3 | taming·edgs·tidigs·vigsslam·sparsegs |
| **Table 4** ordering 진단 | **K × β** × (PSNR·ρ_H·sel.CV·lifetime) | §4.3 | lmrs Tab.2 — 교란축을 기여축 옆에 |

### 표를 둘로 쪼갠 이유

코퍼스 ablation 표는 **(i) 제거축 한 개** 또는 **(ii) setting×method** 둘뿐이고,
**독립 축 여럿을 `\multirow` 로 겹친 예는 8편 중 0편**이다. 항목이 셋인 lmrs 는 표를 셋으로 나눈다.

이전 Table 3 은 growth / ordering / carve 세 축을 겹쳐놓고 `ρ_H`·`sel.CV`·`lifetime` 열을
공유시켰는데 **그 세 열은 ordering 축에만 정의된다** — 셀의 2/3 이 무의미했다.

- **Table 3** = 전 행에 정의되는 열만. 위에서 아래로 그냥 읽힌다
- **Table 4** = ordering 전용 진단. K 를 행으로 내려 β 옆에 → **교란축이 기여축보다 클 수 있음을 표가 스스로 드러낸다**
- **표 밖으로**: κ sweep(본문+보충), clustering sampler(보충)

### 각 표가 답하는 질문

| 표 | 질문 |
|---|---|
| Table 1 | 같은 스트림·같은 시간에 우리가 더 나은가 |
| Table 2 | 한 설정으로 여러 장면에서 되는가 |
| Table 3 | 셋 중 하나를 빼면 얼마나 잃는가 |
| Table 4 | ordering 안에서 β 와 K 중 무엇이 큰 효과인가 |

---

## 6. §3 ↔ §4 대칭

이름과 순서가 세 곳에서 같다.

| §3 도입 3번 문장 | §3 소절 | §4.3 run-in | Table 3 행 |
|---|---|---|---|
| 얼마나 들어오나 | 3.1 Compute-Paced View Growth | `View growth.` | `−growth: …` |
| 어떤 순서로 다시 보나 | 3.2 Entropy-Regularized Count Balancing | `Count balancing.` | `−order: …` |
| 무엇이 기하를 붙잡나 | 3.3 Causal Free-Space Carving | `Carving.` | `−carving` |

**§4.3 CLOSING 이 §3 도입을 회수한다.** 코퍼스의 종합 문장은 대개 "다 빼면 나빠진다"로 끝나는데
우리는 "**서로 다른 방식으로** 나빠진다"로 끝낸다 — 세 소절이 한 문제의 세 얼굴이라는 §3 의 주장은
그래야 증거를 얻는다. tidigs 의 인과사슬 문단이 가장 가까운 선례.

---

## 7. 분량 회계

| 절 | 계획 | 실제 |
|---|---:|---:|
| 1 Introduction | 1.00 | 1.0 |
| 2 Related Work | 1.15 | 1.0 |
| 3 Method | 2.70 | 3.0 |
| 4 Experiments | 2.20 | 2.0 |
| 5 Limitations | 0.20 | 0.5 |
| 6 Conclusion | 0.20 | 0.5 |

본문 8쪽 안 (References p8). `./scripts/pagemap.sh` 로 재확인.

---

## 8. 아직 안 맞는 것

| | 어디 |
|---|---|
| `sel. CV` 와 `life mid/first` 가 **§4.1 `Metrics.` 에 정의돼 있지 않다** (ρ_H 만) — Table 4 에 쓰려면 정의하거나 열을 빼야 | §4.1 / Table 4 |
| §1 이 아직 "한 원인의 세 결과"를 안 들고 있다 (삼분법을 §3→§1 로 옮긴 결과) | §1 |
| §3.2 P4 block freeze 가 **근사가 아니라 정확**일 수 있다 — exp72 코드 확인 전 | §3.2 P4 `\pend` |
| eq.(2) 가 누적 S(t) 위인지, discard 후 잔여 credit 위인지 미결 | §3.1 P4 `\pend` |
| `K=128, β=0` arm 미측정 → β 단독 효과 없음 | Table 4 |
| κ=16 이상치(22.163dB, −5.545)를 실을 문장 미작성 | §4.3 `View growth.` |
| §3.3 · §4.3 `Carving.` 은 팀원 확정 대기 | §3.3 |
| 데이터셋 미확정 — 후보 12개 | `notes/datasets/CURRENT.md` |

---

## 관련 문서

- 절 내부 상세: `sections/03_method/README.md` · `sections/04_experiments/README.md`
- 코퍼스 해부: `notes/structure_survey/` (`_framework_moves.md` 가 move 어휘)
- 섹션 간 흐름: `plan/outline/CURRENT.md`
- 주장 ↔ 실험: `plan/claims/CURRENT.md` · `plan/experiment_table/CURRENT.md`
- Overleaf 동기화: `latex/SYNC.md`
