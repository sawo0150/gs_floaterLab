# absorbed/ — 이 소절에 흡수된 것

| 폴더 | 원래 | 본문에서 |
|---|---|---|
| `compute_latency/` | `4-6_system_analysis/` → `4-5_compute_latency/` | §4.1 마지막 run-in `\textbf{Compute and latency.}` 한 문단 |

## 왜 없앴나

Table 1이 이미 `wall-time | streaming updates | admissions | peak pool | final pool`을 들고 있어
독립 소절이 낼 것이 문단 하나뿐이었다.

그리고 §4의 **번호 붙은 소절은 3개까지**로 잡았다. 해부 5편 기준:

| 논문 | Setup에 번호? | 번호 붙은 소절 수 |
|---|---|---|
| chen2026cover | ✗ | 3 |
| lmrs | ✗ | 2 |
| vigsslam | ✗ | 3 |
| mallick2024taming3dgs | ✓ | 3 |
| cartgs | ✓ | 2 |

5편 중 3편이 Setup에 번호를 안 준다. 공통 골격은 **(번호 없는 Setup) → 주결과 → ablation
→ 하나만 더**이며, 그 "하나만 더" 자리를 chen은 Compute Time, vigsslam은 Robustness로 썼다.

**우리는 Rate Robustness를 택했다.** C1을 정의하는 성질(완료가 박자를 만든다)을 검증하는
유일한 실험이라 표 안의 열로 대신할 수 없다. compute time은 대신할 수 있다.
