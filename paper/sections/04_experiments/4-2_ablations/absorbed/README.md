# absorbed/ — 이 소절에 흡수된 것

2026-09-06 구조 개편에서 **소절을 잃고 run-in 볼드 항목이 된** 내용. 지우지 않고 보관한다.

| 폴더 | 원래 위치 | 본문에서 |
|---|---|---|
| `geometry_carve/` | `sections/04_experiments/4-5_geometry_carve/` | §4.4의 `\textbf{Carving.}` 항목 |

## 왜 합쳤나

해부한 5편 **전부** ablation을 **한 소절**에 몰고 run-in 볼드로 항목을 나눈다.
기여마다 ablation 소절을 따로 준 논문은 없었다.

| 논문 | §4/§5 소절 구성 | 소절 수 |
|---|---|---|
| cartgs | A Setup / B Results (ablation은 B 안 레이더 차트) | 2 |
| chen2026cover | 5.1 Comparisons / 5.2 **Ablations** / 5.3 Compute Time | 3 |
| mallick2024taming3dgs | 5.1 Datasets and Metrics / 5.2 Results / 5.3 **Ablations** | 3 |
| lmrs | 5.1 Comparison / 5.2 **Ablation Studies** (run-in `View Sampling.`) | 2 |
| vigsslam | 4.1 Mapping·Tracking·Rendering / 4.2 Tracking Robustness / 4.3 **Ablation Study** | 3 |

평균 2.6개다. 우리 옛 구성은 6개였고 2.2쪽에 넣으면 소절당 0.37쪽이라 파편화된다.

## Rate Robustness만 따로 뺀 이유

vigsslam이 `4.2 Tracking Robustness`를 `4.3 Ablation Study`와 **분리한** 선례가 있다.
강건성 연구는 구성요소 제거가 아니라 **입력 조건을 바꾸는** 것이라 성격이 다르다.
게다가 P02는 C1을 정의하는 성질(완료가 박자를 만든다)을 검증하는 유일한 실험이다.
