# refs/ — 참고 논문 목록

> **PDF 파일 자체는 git에 없습니다.** 저작권 자료이고 파일당 최대 50MB, 합계 521MB라
> GitHub에 올릴 수 없습니다. 이 `INDEX.md`만 추적하며, 바이트는 로컬에만 둡니다.
> 다른 컴퓨터에서 작업하려면 아래 목록을 보고 각자 내려받으세요.

## 규칙

- **파일명 = bibkey.** `latex/main.bib`의 키와 1:1로 맞춥니다. 그러면 네 곳이 한 줄로 꿰입니다:
  ```
  main.bib 의 \cite{cartgs}
    ↔ refs/05_budget_system/cartgs.pdf
    ↔ notes/related_work/cartgs.md        (무슨 내용인가)
    ↔ notes/structure_survey/cartgs.md    (어떻게 썼는가 — 구조 해부)
  ```
- **하위 폴더 = `sections/02_related/`의 소절 구조.** 논문이 어느 폴더에 있는지가
  곧 Related Work의 어느 소절에서 인용될지를 뜻합니다.
- 새 논문을 넣으면 **이 표에 한 줄 추가**합니다. 그게 이 폴더의 유일한 관리 비용입니다.

## 00_writing — 논문 작성법 (SNU 과학기술글쓰기)

현재 작업 방법론의 근거 자료. `plan/checklist/`가 여기서 파생됩니다.

| 파일 | 쪽 | 무엇 |
|---|---:|---|
| `snu_writing_guide_1.pdf` | 19 | 서론 4-move 구조(Field→Map→Gap→Aim), Discussion이 그 역순 대칭이라는 원칙, 학부생 보고서 예시 |
| `snu_writing_guide_2.pdf` | 6 | Methods(Materials/Equipments/Procedures)와 Results(General statement→Figure/Table) 구성, 그림·표 캡션 규칙 |
| `snu_paper_analysis_example.pdf` | 9 | ★ **구조 해부의 완성 예시.** 게재 논문 위에 구간을 표시하고 move 이름을 붙인 자료. `notes/structure_survey/`가 이 방식을 마크다운으로 옮긴 것 |

⚠ 이 자료는 **IMRaD 실험과학 논문** 기준입니다. CVPR과의 매핑은 `plan/checklist/CURRENT.md` 참조.

## 01_gs_slam — §2.1 같은 문제영역

| 파일 | 쪽 | 우리 쓰임 |
|---|---:|---|
| `vigsslam.pdf` | 31 | **우리 baseline 그 자체.** arXiv 2512.02293 |

**받아야 할 것:** MonoGS(`matsuki2024monogs`), SplaTAM, Photo-SLAM(`huang2024photoslam`)

## 02_view_selection — §2.2 view 선택 / active vision

| 파일 | 쪽 | 우리 쓰임 |
|---|---:|---|
| `chen2026cover.pdf` | 9 | CVF Open Access **게재판 = 정본**. view 선택을 coverage 최적화로 |
| `chen2026cover_extended13p.pdf` | 13 | 같은 논문 확장판. 유도 세부가 더 있을 때 참조 |
| `comapgs.pdf` | 15 | covisibility map 기반. §3.2 membership과 대비 |

**받아야 할 것:** FisherRF(`jiang2024fisherrf`)

## 03_shuffling_theory — §2.3 without-replacement SGD

(비어 있음) **전부 받아야 함:** `mishchenko2020random`, `shamir2016without`, `ahn2020shuffling`

§3.3 ERCB의 이론 배경이고, **"보장을 가져오지 않는다"는 선을 정확히 긋기 위해** 필요합니다.

## 04_geometry_floater — §2.4 floater / geometry 정규화

C3(carve)의 관련연구. 여기가 가장 두껍습니다.

| 파일 | 쪽 | 우리 쓰임 |
|---|---:|---|
| `sparsegs.pdf` | 14 | sparse view에서의 floater 억제 |
| `tidigs.pdf` | 15 | geometry 개선 계열 |
| `chen2024pgsr.pdf` | 20 | **PGSR** (planar-based). ⚠ 원본 파일명이 `PDGR.pdf`였는데 내용은 PGSR이라 정정함 |
| `splatface.pdf` | 10 | 보조 |
| `ko_report_floater_local_minima.pdf` | 7 | 한글 리포트. ⚠ 원본 파일명이 `3dgs_survey_paper.pdf`였으나 survey 논문이 아니라 국소최적점 리포트라 정정함 |

**받아야 할 것:** TrimGS(`fan2024trimgs`), StableGS(`stablegs`), 2DGS, GOF

## 05_budget_system — §3 서술법을 배울 대상

★ **가장 중요한 카테고리.** 우리 §3은 Lagrangian 유도 + deterministic controller라
보통의 3DGS 논문과 서술 결이 다릅니다. "제한된 자원 / 스케줄링 / 시스템" 논문이
§3을 어떻게 쓰는지를 여기서 배웁니다.

| 파일 | 쪽 | 우리 쓰임 |
|---|---:|---|
| `cartgs.pdf` | 8 | ★ **1순위 해부 대상.** IEEE RA-L. GS-SLAM의 계산 정렬(computational alignment) — 우리 문제의식과 가장 가까움 |
| `mallick2024taming3dgs.pdf` | 13 | ★ 제한된 자원에서의 3DGS. 예산 제약 서술의 표준 |
| `mallick2024taming3dgs_ko.pdf` | 18 | 위 논문의 한글 번역본. 구조 해부 시 원문과 대조하면 빠름 |
| `lmrs.pdf` | 17 | matrix-free 2차 최적화. 최적화 논문의 유도 서술 방식 참조 |
| `edgs.pdf` | 20 | densification 제거로 수렴 효율화. 예산 관점 보조 |

## 06_ours — 우리 시스템 구성요소

| 파일 | 쪽 | 우리 쓰임 |
|---|---:|---|
| `teed2021droid.pdf` | 15 | DROID-SLAM. §3.2 dense correspondence trajectory filling의 근거 |

## 별도 위치에 둔 것 (옮기지 않음)

용량이 크고 당장 안 쓰므로 원래 자리에 둡니다. 필요해지면 그때 정리합니다.

| 파일 | 위치 | 무엇 |
|---|---|---|
| `merged_original.pdf` | `context/reference/papers/` | **241MB / 255쪽.** floater·local minima 논문 10편 안팎의 합본(StableGS로 시작). 논문 한 편이 아니라 묶음집 |
| `merged_translation.pdf` | 〃 | **431쪽 한글 전문 번역집.** 위 묶음집 전체 번역. C3 관련연구 조사 시 큰 자산 |
| `merged_translation (1).pdf` | 〃 | ⚠ 이름과 달리 번역집이 아니라 **11쪽 연구흐름 리포트** |

## 옮겨온 곳 (2026-09-05)

`~/Documents/논문/`, `~/Documents/논문 작성법/`, `Incremental_mapping/reference/paper/`,
`gs_floaterLab/repos/reference/`, `gs_floaterLab/context/reference/papers/` 에 흩어져 있던 것을
여기로 통합했습니다. 중복 2쌍(vigs-slam 31MB, Taming3DGS 40MB)은 제거했습니다.

이 중 154MB는 **git에 추적되고 있었고**, 이번에 추적을 해제했습니다.
⚠ 다만 **git 히스토리에는 그대로 남아 있어 repo 크기(350MB)는 줄지 않습니다.**
줄이려면 `git filter-repo`로 히스토리를 다시 써야 하는데, 원격과 다른 worktree가 있어
별도 결정 사항으로 둡니다.

---

# 2026-09-06 추가 — 도구의 출처를 밝히기 위한 문헌

우리 C1/C2가 쓰는 도구는 **이미 다른 커뮤니티에 이름이 있다.** 발명했다고 쓰면 안 되고,
"이 도구를 online GS-SLAM supervision scheduling에 붙였다"로 좁혀야 한다.
아래는 그 좁히기를 문장으로 쓰기 위해 받은 것들이다. 근거는
[`../notes/naming/`](../notes/naming/).

## 03_shuffling_theory — 비복원 SGD (C2의 β→0 극한)

| 파일 | 무엇 | 어디에 쓰나 |
|---|---|---|
| `mishchenko2020random_reshuffling.pdf` | Random Reshuffling: Simple Analysis with Vast Improvements (NeurIPS 2020) | **β=0 ≡ random reshuffling** 주장의 인용처 |
| `mishchenko2021proxrr.pdf` | Proximal and Federated Random Reshuffling | **importance sampling의 RR 변형은 제안·분석된 바 없다**고 명시. unbiasedness가 RR에서 깨지기 때문 — 우리 위치를 정당화하는 유일한 긍정적 근거 |
| `desa2020rr_not_always_better.pdf` | Random Reshuffling is Not Always Better (NeurIPS 2020) | RR이 항상 낫지 않다는 반례. 우리가 보장을 안 가져오는 이유 |
| `safran2020how_good_shuffling.pdf` | How Good is SGD with Random Shuffling? | |
| `haochen2019shuffling_beats_sgd.pdf` | Random Shuffling Beats SGD after Finite Epochs | |
| `gurbuzbalaban2015why_rr_beats_sgd.pdf` | Why Random Reshuffling Beats SGD | |
| `rajput2020closing_gap_without_replacement.pdf` | Closing the convergence gap of SGD without replacement | |

## 07_sampling_ranking — K-view 비복원 순차 추출 (C2의 절차)

| 파일 | 무엇 | 어디에 쓰나 |
|---|---|---|
| `kool2019gumbel_top_k.pdf` | Stochastic Beams / Gumbel-Top-k (ICML 2019) | 우리 K-view 순차 가중 비복원 추출 = **Plackett–Luce 추출**. 이름을 먼저 밝히지 않으면 "그거 PL인데요" 한 줄로 끝난다 |
| `efraimidis2010weighted_reservoir.pdf` | Weighted Random Sampling over Data Streams | 가중 비복원 추출의 스트리밍 구현 |

> Plackett(1975), Luce(1959), Yellott(1977)은 유료라 받지 못했다. 인용만 한다.

## 08_rl_replay — count 기반 우선순위 (C2와 직접 충돌)

| 파일 | 무엇 | 어디에 쓰나 |
|---|---|---|
| `kauvar2023curious_replay.pdf` | Curious Replay (ICML 2023) | **visit count `v_i`로 `p_i = β^{v_i}`.** 우리 `p ∝ exp(−βn_i)`와 같은 형태 — 반드시 먼저 밝힐 것 |
| `jiang2021prioritized_level_replay.pdf` | Prioritized Level Replay | count 대신 staleness `c − C_i`에 비례 |
| `schaul2015prioritized_experience_replay.pdf` | Prioritized Experience Replay | 계보의 원형 |
| `haarnoja2018sac.pdf` | Soft Actor-Critic | entropy 정규화 → 지수형 정책의 딥러닝 판 |

## 09_data_selection — score 기반 지수 감쇠 선택 (수식 구조가 동일, 목적은 정반대)

| 파일 | 무엇 |
|---|---|
| `loshchilov2015online_batch_selection.pdf` | Online Batch Selection — rank의 지수 함수로 선택 확률. 원형 |
| `katharopoulos2018importance_sampling.pdf` | Not All Samples Are Created Equal |
| `mindermann2022rho_loss.pdf` | Prioritized Training (RHO-Loss) |

> 이들은 **어려운 것을 더 자주** 보고 우리는 **고르게** 본다. 목적이 반대인데 파라미터화는 같다.
> 그래서 "우리는 반대 방향을 택했고 그 이유는 …"이라고 명시해야 한다.

## 10_maxent_control — entropy 정규화 → Gibbs 해 (C2의 유도)

| 파일 | 무엇 |
|---|---|
| `kappen2005path_integral_control.pdf` | Path integrals and symmetry breaking for optimal control |

> Todorov(2007) linearly-solvable MDP, Ziebart(2010)은 arXiv에 없어 받지 못했다. 인용만 한다.

## 11_admission_control — token bucket (C1의 메커니즘)

| 파일 | 무엇 | 어디에 쓰나 |
|---|---|---|
| `rfc2212.txt` | Guaranteed QoS — **token bucket (r, b) 규격** | 우리 `B_t = B_0 + γS(t) − κ(\|A_t\|−A_0) ≥ 0` 이 정확히 token bucket이다 |
| `rfc2215.txt` | Integrated Services 특성 파라미터 | |

> ★ 다만 표준 token bucket은 **시간에 비례해** 토큰이 찬다. 우리는 **완료된 GPU service에
> 비례해** 찬다 → 이건 rate-based가 아니라 **credit-based flow control**(수신자가 처리를
> 마치면 credit을 돌려주는 방식)에 해당한다. 이 차이가 곧 C1의 기여다.
> Kung & Morris(1995) credit-based flow control은 유료라 인용만 한다.

## 기존 폴더 보강 (2026-09-06)

| 파일 | 폴더 | 왜 |
|---|---|---|
| `matsuki2024monogs.pdf` | 01_gs_slam | baseline 비교군 |
| `keetha2024splatam.pdf` | 01_gs_slam | |
| `huang2024photoslam.pdf` | 01_gs_slam | |
| `wang2023coslam.pdf` | 01_gs_slam | |
| `sucar2021imap.pdf` | 01_gs_slam | **keyframe replay 없으면 catastrophic forgetting** — 왜 pool을 계속 replay해야 하는가의 근거 |
| `sandstrom2023pointslam.pdf` | 01_gs_slam | 국소 표현도 global decoder 때문에 forgetting |
| `jiang2024fisherrf.pdf` | 02_view_selection | C2를 information-gain 계열과 **구별**하기 위해 필요 |
| `fan2024trimgs.pdf` | 04_geometry_floater | C3 |
| `mallick2025multiview_training.pdf` | 05_budget_system | 3DGS multi-view mini-batch — **K(배치 뷰 수)의 효과**를 다룬 선행 |
| `zhao2024scaling_up_3dgs.pdf` | 05_budget_system | 3DGS 학습 스케일업 |
