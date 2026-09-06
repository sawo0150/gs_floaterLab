# 4. Experiments

latex 대상: `latex/sec/4_experiments.tex`

> 2.2 p. **소절 5개.** 해부한 5편의 §4/§5 소절 수가 평균 2.6개라, 옛 구성(6개)은
> 소절당 0.37쪽으로 파편화됐다. 근거는 `4-4_ablations/absorbed/README.md`.

| 소절 | 분량 | 무엇 | 산출물 |
|---|---|---|---|
| [4.1 Experimental Setup](4-1_setup/) | 0.35 p | run-in 볼드 4개: `Datasets.` `Streaming contract.` `Metrics.` `Baselines.` | — |
| [4.2 Main Results](4-2_main_results/) | 0.60 p | Results pointer → 같은 예산에서 품질 → 같은 품질에서 예산 → 장면 일반화 | **Table 1, Table 2** |
| [4.3 Rate Robustness](4-3_rate_robustness/) | 0.35 p | pace × 하드웨어. **C1을 정의하는 성질의 유일한 검증** | **Fig.4** |
| [4.4 Ablations](4-4_ablations/) | 0.75 p | run-in 볼드 3개: `View growth.` `Count balancing.` `Carving.` | **Table 3**, Fig.5 |
| [4.5 Compute and Latency](4-5_compute_latency/) | 0.15 p | wall-time·update 수·peak/final 크기 | **Table 4** |

## 소절 순서의 근거

vigsslam과 같다 — **주결과 → 강건성 → ablation**. 강건성은 구성요소 제거가 아니라
입력 조건 변경이라 ablation과 성격이 다르고, vigsslam도 `4.2 Tracking Robustness`를
`4.3 Ablation Study`와 분리했다.

## §3과의 대칭

§4.4의 run-in 볼드 항목 이름은 §3 소절 이름과 **같은 순서**여야 한다.

| §3 | §4.4 항목 |
|---|---|
| 3.1 Compute-Paced View Growth | `View growth.` |
| 3.2 Entropy-Regularized Count Balancing | `Count balancing.` |
| 3.3 Causal Free-Space Carving | `Carving.` |

## 표·그림 (4표 5그림)

옛 계획은 5표 6그림이었다. 같은 조판(CVPR 9쪽)인 chen2026cover가 **2표 3그림**이라
줄였다. Table 1은 taming3dgs처럼 상/하단으로 갈라 두 시나리오를 담는다.

| 산출물 | 내용 | 어디 | 실험 |
|---|---|---|---|
| Fig.1 | teaser | §1 | — |
| Fig.2 | system diagram | §3.0 | — |
| Fig.3 | view-growth trace (법칙 대 실측) | **§3.1 안** (in-method evidence) | P01 |
| **Fig.4** | rate invariance | §4.3 | **P02** |
| Fig.5 | floater 정성 비교 | §4.4 | P04 |
| **Table 1** | 주결과. 품질+자원 한 표, 상단=같은 예산/하단=같은 품질 | §4.2 | P03, P06 |
| Table 2 | 장면 일반화 (config 고정, mean±std) | §4.2 | P05 |
| **Table 3** | ablation 3블록 한 표, 예산 봉인 | §4.4 | P01, P03, P04 |
| Table 4 | compute·latency | §4.5 | P02, P06 |

전체 지도는 [`../README.md`](../README.md), 실험 ↔ claim 매핑은
[`../../plan/experiment_table/CURRENT.md`](../../plan/experiment_table/CURRENT.md).
