# exp53 — Frontend Tracking 실시간화: dense correspondence 품질 계측 + 반복/윈도우/keyframe 밀도 축 탐색

- 상태: **계획 단계 (2026-07-20). 축A~E 미착수.**
- 배경: [exp52](exp52_vigs_slam_eval.md)에서 `_gs_parallel`(비동기 tracking/mapping 오버랩)로
  온라인 루프 −26.1%를 냈지만 여전히 실시간의 2.04배. 이후 fps 스윕으로 **gs_mapping을 다 빼도
  Frontend Tracking(초록 박스: ConvGRU+Joint Visual-inertial BA) 자체가 이미 실시간 예산을
  초과**함을 확인(5fps까지 낮춰도 66.80초>60초). DROID-SLAM 원 논문도 "2-GPU+다운샘플/스킵"
  조건부로만 실시간을 주장했고 VIGS 저자 공식 RTX 5090 벤치마크도 tracking+mapping 12.02fps로
  목표(30fps) 미달 — **frontend 자체가 이 아키텍처 계열의 근본적인 실시간 병목**임을 원 논문과
  우리 실측 양쪽에서 확인. **exp53은 이 frontend를 실제로 가볍게 만드는 실험 트랙.**
- exp52와의 역할 분담: **exp52는 mapping 쪽 실시간성(gs_parallel, GPU 오버랩, 추후 RTX 5090
  재검증 등)을 계속 다룸 — 종료 아님.** exp53은 frontend(tracking) 쪽만 전담.
- 핵심 발견(exp52에서 이관): keyframe 발생률이 입력 fps와 거의 무관(VIGS −6.6% vs 입력 프레임
  −75%, `motion_filter.thresh` 기반) → **fps를 낮추는 건 이 아키텍처엔 약한 레버**이고, frontend
  자체의 keyframe당 비용(`iters1=4`+`iters2=2` 반복 안의 GRU+BA)과 keyframe 발생 밀도 자체를
  줄이는 게 진짜 레버.

## 측정 기준 (baseline, 축 실험 전에 먼저 확립)

기존 evo APE(Sim3, 형태 정확도)는 결과물 지표라 "왜" 나빠지는지는 안 보여줌 — **dense
correspondence 자체의 품질**을 별도로 계측해서, 축A~E를 돌렸을 때 정확도 저하의 원인이
"correlation 자체가 나빠져서"인지 "반복 부족으로 수렴을 못 해서"인지 구분한다.

| # | 지표 | 계측 위치 | 구현 난이도 | 용도 |
|---|---|---|---|---|
| ① | Confidence weight(`w_ij`) 분포(평균/분위수) | `factor_graph.py::get_network_update()`의 `weight` 텐서 | 낮음(로그 한 줄) | GRU가 correlation에 얼마나 확신하는지 — 낮으면 correlation 자체가 부실 |
| ② | Revision(`delta`) 크기의 iteration별 수렴 추이(1~4회차) | 같은 함수의 `delta` 텐서, iteration 인덱스별로 기록 | 낮음(로그 한 줄) | **축A(iters 축소)의 사전 진단** — 몇 회차부터 delta가 이미 충분히 작아지는지 보면 iters를 몇으로 줄여도 되는지 바로 판단 가능 |
| ③ | BA 가중 재투영 오차(reprojection residual, Eq.4의 E) | BA solve 전후 잔차 | 중간(BA 커널 출력 또는 재계산 필요) | 최종 수렴 후 남은 기하 불일치 — correspondence 품질의 직접 지표 |
| ④(보류) | 다시점 depth 일관성(같은 3D점을 보는 여러 keyframe의 `disps_up` 비교) | edge 쌍 선택 + depth 비교 코드 신규 | 높음 | 매핑 기하 품질과 가장 직결되나 축D~E 즈음 필요, 지금은 범위 밖 |

**순서**: ①②를 baseline(iters1=4/iters2=2, frontend_window=25, 현재 config 그대로)에서 먼저
측정 → 축A(iters 축소) 돌릴 때마다 같이 재서 "iters 줄임 → delta 수렴 전 잘림 → weight/오차
악화"의 인과를 직접 확인. ③은 여유 되면 같이, ④는 이번 라운드 범위 밖.

## 실험축

baseline(현재 config: `iters1=4`, `iters2=2`, `frontend_window=25`, `frontend_radius=2`,
`frontend_nms=1`, `motion_filter.thresh=2.4`) 대비 **한 번에 하나씩** 변경, frontend 총합
시간 + evo APE(Sim3) + ①②(③) dense correspondence 지표로 판정.

| 축 | 내용 | 구현 위치 | 트레이드오프 | 우선순위 |
|---|---|---|---|---|
| **A. `iters1`/`iters2` 축소** | 반복 횟수(4+2)를 줄여서 GRU+BA 콜 수 직접 감소 | `track_frontend.py` 하드코딩 상수 | delta 수렴 전에 멈추면 정확도 저하(①②로 사전 진단) | **1 (가장 직접적, 가장 큼)** |
| **B. `motion_filter.thresh` 상향** | keyframe 발생 밀도 자체를 줄여 총 작업량 감소 | `config/aria1253.yaml` (config만) | keyframe 간 baseline 커짐(축A와 상호작용), 매핑 supervision 밀도도 감소(품질축과 얽힘) | 2 |
| **C. `frontend_window`/`radius`/`nms` 축소** | 로컬 BA 그래프 크기(Hessian 크기) 축소 | `config/aria1253.yaml` (config만) | 장거리 드리프트 억제력 감소 | 3 |
| **D. Correlation 해상도/radius 축소** | `build_corr_volume`/`corr_lookup` 자체를 가볍게 | `factor_graph.py`/`motion_filter.py`의 correlation 설정 | 큰 모션 강건성 저하, 재검증 필요(가장 작은 항목이라 기대효과도 작음) | 4 (낮음) |
| E(보류). custom CUDA 커널 튜닝 / TensorRT 재도전 | bundle_adjust 커널 자체 최적화 | `vigs_backends` CUDA 커널 | 고비용/고위험 엔지니어링. update_module TensorRT는 이미 +8.6%(역효과) 확인됨 — A~D로 부족할 때만 고려 | 5 (최후순위) |

## 성공 기준 (판정 방식)

- **Pass 라인**: frontend 총합(keyframe당 GRU+BA 비용 합)이 실제 녹화 시간 이하로 내려올 것.
- **정확도 하한**: evo APE(Sim3, 형태 정확도)가 **ORB(exp50, 13cm)보다는 항상 나아야 함** —
  안 그러면 dense correspondence의 존재 의의(매핑 기하 우위, exp52 확정)가 없어짐. 현재
  baseline은 1.3cm이므로 여유는 있음.
- 축마다 frontend 총합 / evo APE(SE3+Sim3) / ①②(③) dense correspondence 지표를 표로 남겨
  트레이드오프 커브를 그린다(exp51의 λ 스캔과 같은 방식).

## 다음 단계 (미착수)

1. ①②(③) 계측 코드를 baseline config에 추가하고 1253 전체 시퀀스에서 먼저 측정.
2. 축A(iters1/iters2)부터 순서대로 스캔.
