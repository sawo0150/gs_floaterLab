# 실험 테이블 v03 (2026-09-06) — §3/§4 구조 확정 반영

> 각 실험이 **어떤 claim을 세우기 위한 것인지**와 **논문의 어느 표/그림이 되는지**를 1:1로 묶는다.
> claim 번호는 [`plan/claims/CURRENT.md`](../claims/CURRENT.md) 기준.
> 실험 카드 본체는 `paper/experiments/Pnn_*/`.

## v03에서 바뀐 것

§3/§4 구조가 확정되어 산출물 매핑을 전면 개정했다. **실험 자체(P01–P06)는 그대로다.**

- §3 = 3.0 + **3.1 Compute-Paced View Growth / 3.2 ERCB / 3.3 Causal Free-Space Carving**
- §4 = (번호 없는 Setup) + **4.1 Main Results / 4.2 Ablations**
- 표 5→4, 그림 6→5
- 근거: `notes/naming/CURRENT.md`, `sections/04_experiments/README.md`

## 크리티컬 패스

```
P01(partial) ──┬──→ P02 (rate-invariance)
 (token law)   └──→ P03 (C2 재검증) ──┐
P04 (carve 이식, 팀원) ────────────────┼──→ P05 ──→ P06 ──→ 집필
```

exp73으로 token-only/no-prepurchase law 자체와 poll-level 일치는 확인했다. 따라서 P03는
`κ=22` token-only admission 위에서 진행할 수 있다. 다만 P01의 carry arm·순수 gate-removal
대조와 P02의 hardware-rate 검증은 남아 있으며, 이를 끝내기 전 C1을 일반화해 말하지 않는다.

## 실험 목록

| ID | 목적 (어떤 claim을 세우나) | 비교 arm | 핵심 지표 | 장면 | 머신 | 산출물 | 상태 |
|---|---|---|---|---|---|---|---|
| **P01** | C1 구현 + 이론식 대조 → **B1, B4, B5** | 완료: baseline vs token/no-prepurchase; 남음: token/carry와 순수 gate-removal | `A_paid(u)` vs `⌊u/κ⌋`, admission poll 오차, 최종 pool 크기 | aria1253, 301_305 | 5090 (exp73); 5070Ti 남음 | **Fig.3** view-growth trace | **부분 완료** — 7 run·526 poll |
| **P02** | 하드웨어 속도에 view growth가 비례하는가 → **B2** | 같은 trace × {5090, 5070Ti} × pace {0.75, 1.0, 1.5, 2.0}× | S(t)당 admission 수, held-out PSNR range, topology drop | aria1253, rot | **양쪽 동시** | **Fig.4** rate invariance | 미착수 |
| **P03** | C1 위에서 ERCB 재검증 → **C6**(실패 뒤집기), C2·C4 재확인 | ① token만 ② token+ERCB(K=128,β=0.02) ③ K/β sweep {1,32,128}×{0,0.02} | held-out PSNR, ρ_H, lifetime count middle/first, 최종 pool 크기 | aria1253, rot | 5090 | **Table 1** + **Table 3** 블록2 | 미착수 |
| **P04** | carve의 incremental 이식 → **D3** | ① carve off ② 현 v7-64 ③ 이식판 | region GT AUC/AP, precision@0.75% budget, held-out ΔPSNR, score-age p95 | aria1253, 301_305 | 5070Ti | **Table 3** 블록3 + **Fig.5** | 팀원, 진행중 |
| **P05** | 장면별 재튜닝 없이 일반화되는가 → **A4** | 최종 config 고정, 장면만 변경 | held-out PSNR/SSIM/LPIPS, late temporal bins, run-to-run mean±std (3회) | aria1253, rot, 301_305, 12F | 양쪽 | **Table 2** | 미착수 |
| **P06** | baseline 대비 우위 → **A4** | fixed-FPS dense / random full-pool / MonoGS-style covisibility window / novelty-first / residual-first / **clustering-based batch sampler** (lmrs §4.3) | 동일 wall-time에서 held-out PSNR, selection-count spread | aria1253, rot | 양쪽 | **Table 1** 상단 | 미착수 |

### P01에서 이미 확인한 것과 남은 것

- 확인: gate-free token-only/no-prepurchase 구현, 526개 poll의 token-law 오차 0,
  `κ=22`에서 1253 2회 평균 `+0.003 dB`, 305 `−0.119 dB`.
- 확인하지 못함: carry와의 비교 우위, 동일 interval bootstrap을 유지한 순수 gate-removal 효과,
  5070Ti 전이 및 slowdown에 대한 rate invariance.
- 해석 주의: 1253 pool `−34.8%`는 maturity gate 제거만의 효과가 아니라 interval별 무료
  bootstrap을 1개의 global seed로 교체한 효과까지 포함한다.

## 표·그림 ↔ 실험 매핑 (v03에서 전면 개정)

**5표 6그림 → 4표 5그림.** 같은 조판(CVPR 9쪽)인 chen2026cover가 2표 3그림이다.

| 산출물 | 내용 | 나오는 실험 | 어느 절 |
|---|---|---|---|
| Fig.1 | teaser | P02, P03 | `sections/00_teaser/` |
| Fig.2 | system diagram | (도식) | `sections/03_method/3-0_overview/` |
| **Fig.3** | view-growth trace (법칙 대 실측) | **P01** | **`3-1_compute_paced_view_growth/`** ← §3 안 |
| **Fig.4** | rate invariance | **P02** | `04_experiments/4-1_main_results/` (run-in `Rate robustness.`) |
| Fig.5 | floater 정성 비교 | P04 | `04_experiments/4-2_ablations/` (`Carving.`) |
| **Table 1** | 주결과. 품질+자원 **한 표**, 상단=같은 예산/하단=같은 품질 | P03, P06 | `4-1_main_results/` |
| Table 2 | 장면 일반화 (config 고정, 3회 mean±std) | P05 | `4-1_main_results/` |
| **Table 3** | ablation **3블록 한 표**, 예산 봉인 문장 | P01, P03, P04 | `4-2_ablations/` |
| Table 4 | compute·latency | P02, P06 | `4-1_main_results/` (run-in `Compute and latency.`) |

### 폐기·병합된 것

| v02 | v03 |
|---|---|
| Table 1(main) + Table 2(baselines) | **Table 1 하나로.** taming3dgs처럼 상/하단 두 시나리오 |
| Table 3(ordering) + Table 4(carve) | **Table 3 하나로.** 3블록 |
| Table 5(system/latency) | Table 4로 번호만 이동 |
| Fig.5 entropy & count spread | **Table 3의 열로 흡수** (`ρ_H`, `selection CV`, `lifetime mid/first`) |
| Fig.6 floater | Fig.5로 번호 이동 |

## Table 1 설계 — 품질과 자원을 한 표에

cartgs가 `ATE | FPS | IPF | PSNR | Points`를, taming3dgs가 `품질 | Train time | #G | Peak #G`를
한 표에 놓은 것과 같은 설계. `streaming updates`가 cartgs **IPF의 자리**다.
"품질이 좋아졌다"가 아니라 **"같은 계산량에서"**를 표 하나로 보인다.

```
Method | PSNR SSIM LPIPS | wall-time  streaming-updates  admissions  peak-pool  final-pool
─────────────────────────────────────────────────────────────────────────────────────────
[상단] 같은 예산에서 품질 — 1.5× budget 고정, baseline들 vs Ours
[하단] 같은 품질에서 예산 — VIGS-SLAM의 update 수에 정확히 맞춘 Ours
```

- **캡션에 출처 표기** (vigsslam Table 1 방식): 인용 수치 / 재현 수치 / 실패(F) 구분.
  → "MonoGS를 직접 구현할지 인용만 할지" 미결이 이 규칙으로 해소된다
- **캡션에 admission 법칙 일치**를 한 줄로: 최대 정수 오차, 장면·run·poll 수

## Table 3 설계 — 교란변수를 같은 표에

lmrs Table 2가 `sampler × batch size`를 한 표에 놓아 **자기 기여가 배치 크기보다 작다는 것을
표 스스로 드러낸** 형식. 표 앞에 **예산 봉인 문장**을 반드시 둔다 (taming3dgs):

> All configurations receive the same admission budget and the same wall-clock budget;
> only the policy under test differs.

```
블록 1  View growth.     gate 제거 / κ 스윕(κ=16 이상치 포함) / Slot placement(+0.35%)
블록 2  Count balancing. K × β 격자 — K를 세로로 늘어놓아 K가 지배적임을 드러냄
                         열: PSNR | ρ_H | selection CV | lifetime mid/first | pool
블록 3  Carving.         carve off / v7-64 / 이식판
```

## ⚠ 계측 항목 추가 (protocol에도 반영 필요)

| 항목 | 왜 |
|---|---|
| **peak pool** | taming3dgs가 `Peak #G`로 Mini-Splatting을 잡은 논리. final만 보면 "왕창 받고 줄이는" 방식과 "처음부터 예산 안에서 받는" 우리 방식이 표에서 구별되지 않는다 |
| **총 admission 수** | Table 1의 열. 법칙 일치를 캡션이 아니라 표로 |

## ⚠ P06 baseline 추가

현재 목록(fixed-FPS dense / random full-pool / covisibility window / novelty-first /
residual-first)에 **"우리와 같은 문제를 다르게 푼" 방법이 없다.**
→ **clustering-based batch sampler** (lmrs §4.3: 카메라 위치·시선 K-Means → 클러스터당 1개)를
추가한다. 리뷰어가 가장 먼저 물을 자리다.

## 이미 확보된 근거 (재실험 불필요)

논문에 그대로 쓸 수 있는 기존 숫자. 출처는 `context/`.

| 사실 | 숫자 | 출처 |
|---|---|---|
| token law 실제 일치 | 2개 장면·7 run·526 admission poll에서 정수 오차 0 | exp73 카드 |
| `κ=22` 품질 보존 후보 | 1253 평균 +0.003dB(2회), 305 −0.119dB(1회) | exp73 카드 |
| gate-free만으로 count 균등화 실패 | selection CV: 1253 0.373→0.951, 305 0.470→0.942 | exp73 카드 |
| ERCB 품질 보존 | 1253 −0.084dB / rot +0.362dB, wall +0.04% 미만 | exp72 카드 |
| conditional entropy 유지 | ρ_H 0.99869 / 0.99842 | exp72 카드 |
| 짧은 block은 무너짐 | K=1,β=0 −2.863dB / K=32 −2.082dB | exp72 카드 |
| **ERCB lifetime 균등화 실패** | rot middle/first 0.758→0.520 | exp72 카드 |
| priority ordering이 shuffle보다 나쁨 | novelty/residual-first AUC MSE +10–11%, with-replacement +1.7% | exp66 Stage C |
| membership 이득이 작음 | interval 내 representative selection +0.35% | 초안 §4 |
| coverage-only selection이 오히려 나쁨 | temporal baseline 대비 AUC −3.88%, residual −1.64% | 초안 §4 |
| 단일 장면 튜닝은 전이 실패 | rot −1.85dB, 305 16.95dB | exp59 |
| ray를 늘리면 품질 붕괴 | verified ray 64→256: PSNR 27.016→25.466dB | mission brief §2.3 |
| batch carve 성과 | exp39b 가시먼지 96→0 (−0.10dB), exp44d2 33.799dB | STATUS.md |

## 공통 규칙

- **모든 비교는 같은 sensor trace · seed · wall-time budget.** → `experiments/protocol/CURRENT.md`
- 품질 판정은 **held-out PSNR + region GT**로만. train/KF PSNR 단독 판정 금지.
- 각 run은 `results/runs/<run_id>/manifest.json` 에 **protocol 버전**을 기록한다.
- 최종 표에 들어갈 숫자는 반복 3회 mean±std. 단일 run 최고치를 대표값으로 쓰지 않는다
  (exp57에서 단일 최고 27.0039 vs 평균 26.8419로 어긋난 전례).

## 아직 안 정한 것

- ~~P04를 §3.4 독립 contribution으로 낼지~~ → **종결.** §3.3 독립 contribution (2026-09-06 제목 확정)
- ~~P06의 MonoGS-style baseline을 직접 구현할지, 인용만 할지~~ → **종결.** 캡션에 출처를 구분 표기하면(vigsslam Table 1 방식) 섞어도 된다. 남은 건 "얼마나 돌릴 여유가 있나"뿐
- 12F 장면을 P05에 넣을지 (라벨 정합 오차 이슈 있음)
