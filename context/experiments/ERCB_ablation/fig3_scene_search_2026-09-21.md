# Fig.3 전체 trajectory 곡선의 다른 장면 탐색

## 요청

Aria301_305/1180 도판의 그래프 내부 inset 구성을 유지하면서 후반 급상승보다
점진적인 상승과 지속적인 Ours 우위가 나타나는 dataset/scene을 찾는다.

## 탐색 범위와 사전 실행 선택

기존 exp94 normalized ERCB vs official vanilla 17-scene 전체의 최종 지표와
frozen tracker 이벤트를 조사했다. 원본은 모두 final PLY 하나만 있어 중간 PSNR을
새로 측정해야 했다. KF-only/KF+dense의 별도 ablation 곡선은 overall-system 비교로
대체하지 않았다.

- UTMM square-1: pose correction 0회; no-correction UTMM 중 endpoint gain이 가장 큼.
- RPNG table_01: endpoint +1.65 dB; frame330 테이블 천 무늬 후보가 있음.
- RPNG table_06: endpoint +1.79 dB; frame1420 포스터 문자 후보가 있음.

이는 illustration 목적의 사후 후보 탐색이다. 17개 모두의 수렴 곡선을 검증한
실험이 아니며 평균적 대표성이나 수렴 가속 일반화를 주장하지 않는다.

## 측정

기존 exp94 seed0의 native recipe를 보존하고 외부 wrapper가 PLY를 저장했다.
Square-1은 50 step, RPNG는 200 step 간격과 마지막 map을 저장한다.
이 숫자는 저장 간격이며 phase/topology/학습 schedule cutoff가 아니다.
기존 `capture_convergence.py`에 기본값50의 선택적 interval 인자만 추가했다.

동일 frozen causal tracker, fixed held-out, distortion-aware preprocessing,
전체 trajectory의 post-EOS evaluator pose(평가 전용), Carve off, zero-tail,
총 render-matched native pair를 유지한다. 각 Adam iteration의 입력 prefix와
렌더 작업량은 다를 수 있으므로 순수 sampler/동일-work 가속 근거와 구분한다.

- 실행: `results/figure03_scene_search_20260921/`
- 사전 후보 및 계약: `plan.json`
- Active source hash 검증: `source_audit.json`
- 학습 전 GPU compute 점유 확인. 순차 실행하며 타 프로세스 종료 없음.

## 결과

6/6 run, 92/92 checkpoint, 41,972 view 평가 완료. Square-1/table01/table06의
고정 held-out은 324/502/555뷰이며 전체 원본 집합을 그대로 사용했다.
모든 arm의 endpoint는 원본 대비 절댓값0.011 dB 이내, 총 training renders 원본과 일치.

| Scene | 30–80% iteration 구간 평균 gap | 최종 gap | 판단 |
|---|---:|---:|---|
| table_06 | +0.7542 | +1.7751 | 완만한 상승과 frame1420 포스터 inset 조합으로 우선 추천 |
| table_01 | +0.9078 | +1.6594 | 초기 상승 후 plateau, 중반 gap이 더 큰 대안 |
| square-1 | −0.1071 | +1.0513 | 초·중반 Ours 우위가 없어 그림 목적상 후순위 |
| 기존 Aria301_305 | +0.7033 | +3.2383 | 후반 pose correction 점프가 커서 새 후보보다 해석이 어려움 |

중반 기술통계만 공통 iteration 범위에서 보간했으며 곡선 자체는 smoothing 없이
모든 실측점을 연결한다. 새 후보 모두 초반부터 큰 격차가 있는 것은 아니다.
Table06/01 모두 pose correction이 반복돼 순수 optimizer 효과로 분리한 결과는 아니다.

실제 도판은 table06 frame1420 800/1400/2600 step,
table01 frame330 800/1600/3000 step. 시점은 렌더 결과 검토 후 illustrative selection이며
전체 곡선 점은 빠짐없이 유지했다. 두 arm/모든 시점에서 동일 crop.
`Same PSNR*`은 baseline endpoint 이상을 처음 기록한 저장점 비교로,
table06 Ours1200/baseline2000, table01 Ours1200/baseline1800이다. 정확한 crossing,
지속 도달이나 native iteration 기반의 wall-time/동일-work 가속률을 뜻하지 않는다.

→ [도판·CSV·전체 비교](../../../humanteck/sections/02_method/figure03/analysis/scene_search/README.md)

## 실행 중단 기록

최초 실행 관리 프로세스가 exit143으로 종료됐다. traceback/학습 오류는 없었고
table_06 Ours까지 capture manifest와 runtime이 완성됐으며 baseline은 미시작 상태였다.
GPU compute process가 없음을 확인하고 완료된 capture를 재사용해 남은 baseline부터 재개했다.
완료된 결과를 삭제하거나 원본 run을 변경하지 않았다.

Table06의 최초 crop은 원본 너비616px를 초과해 검증에서 중단됐으며,
실제 GT를 확인해 `(365,30,610,162)`로 수정했다. 학습·평가 지표에는 영향이 없다.
