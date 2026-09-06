# 4. Experiments

latex 대상: `latex/sec/4_experiments.tex`

> 2.2 p. **번호 붙은 소절은 3개.** Setup은 번호를 주지 않고 §4 도입 문단에 run-in 볼드로 둔다.

## 근거 — 해부 5편의 §4/§5

| 논문 | Setup에 번호? | 번호 붙은 소절 | 수 |
|---|---|---|---|
| chen2026cover | ✗ (§5 도입 문단) | 5.1 Comparisons / 5.2 Ablations / 5.3 Compute Time | 3 |
| lmrs | ✗ (§5 도입 문단) | 5.1 Comparison / 5.2 Ablation Studies | 2 |
| vigsslam | ✗ (run-in 볼드) | 4.1 Mapping·Tracking·Rendering / 4.2 Tracking Robustness / 4.3 Ablation Study | 3 |
| mallick2024taming3dgs | ✓ | 5.1 Datasets·Metrics / 5.2 Results / 5.3 Ablations | 3 |
| cartgs | ✓ | A Setup / B Results | 2 |

**5편 중 3편이 Setup에 번호를 안 준다.** 공통 골격:

```
(번호 없는 Setup) → 주결과 → ablation → 하나만 더
```

그 "하나만 더" 자리를 chen은 Compute Time, vigsslam은 Robustness로 썼다.
**우리는 Rate Robustness를 택했다** — C1을 정의하는 성질(완료가 박자를 만든다)을 검증하는
유일한 실험이라 표 안의 열로 대신할 수 없다. compute time은 대신할 수 있다.

## 구성

| 소절 | 분량 | 무엇 | 산출물 |
|---|---|---|---|
| [(도입) Setup](4-0_setup/) | 0.35 p | run-in 4개: `Datasets.` `Streaming contract.` `Metrics.` `Baselines.` | — |
| [4.1 Main Results](4-1_main_results/) | 0.65 p | Results pointer → 같은 예산에서 품질 → 같은 품질에서 예산 → 장면 일반화 → run-in `Compute and latency.` | **Table 1, Table 2** |
| [4.2 Rate Robustness](4-2_rate_robustness/) | 0.35 p | pace × 하드웨어 | **Fig.4** |
| [4.3 Ablations](4-3_ablations/) | 0.85 p | run-in 3개: `View growth.` `Count balancing.` `Carving.` | **Table 3**, Fig.5 |

## §3과의 대칭

§4.3의 run-in 항목 이름 = §3 소절 이름 = §3.0에서 붙인 문제 이름. **순서도 같다.**

```
§3.0 문제 3개  →  §3.1/3.2/3.3  →  §4.3 run-in 3개  →  §1 bullet 3개
```

| §3 | §4.3 항목 |
|---|---|
| 3.1 Compute-Paced View Growth | `View growth.` |
| 3.2 Entropy-Regularized Count Balancing | `Count balancing.` |
| 3.3 Causal Free-Space Carving | `Carving.` |

## 표·그림 (4표 5그림)

옛 계획은 5표 6그림. 같은 조판(CVPR 9쪽)인 chen2026cover가 **2표 3그림**이라 줄였다.
Table 1은 taming3dgs처럼 상/하단으로 갈라 두 시나리오를 담는다.

| 산출물 | 내용 | 어디 | 실험 |
|---|---|---|---|
| Fig.1 | teaser | §1 | — |
| Fig.2 | system diagram | §3.0 | — |
| Fig.3 | view-growth trace (법칙 대 실측) | **§3.1 안** (in-method evidence) | P01 |
| **Fig.4** | rate invariance | §4.2 | **P02** |
| Fig.5 | floater 정성 비교 | §4.3 | P04 |
| **Table 1** | 주결과. 품질+자원 한 표, 상단=같은 예산/하단=같은 품질 | §4.1 | P03, P06 |
| Table 2 | 장면 일반화 (config 고정, mean±std) | §4.1 | P05 |
| **Table 3** | ablation 3블록 한 표, 예산 봉인 문장 | §4.3 | P01, P03, P04 |
| Table 4 | compute·latency | §4.1 (run-in) | P02, P06 |

전체 지도는 [`../README.md`](../README.md), 실험 ↔ claim 매핑은
[`../../plan/experiment_table/CURRENT.md`](../../plan/experiment_table/CURRENT.md).
