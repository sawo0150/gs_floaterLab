# Ablation 수렴 지표 검토 — 2026-09-20

사용자 요청에 따라 `ERCB_ablation`과 `VIGS_ERCB_ablation`을 기준으로 검토했다.
신규 학습·GPU 평가를 수행하지 않은 원본 집계/평가 코드 검토다. TeX와 기존 실험 기록은 변경하지 않았다.
별도 exp 번호의 시스템 비교를 이 ablation의 근거로 섞지 않는다.

## 결론

현재 표는 **주어진 예산에서 얻는 품질**을 보여준다. 빠른 수렴을 주 주장으로 삼으려면
동일 실행 중 held-out 품질 곡선과 **양쪽의 동일 목표 품질 도달 비용**이 필요하다.
PSNR을 다른 지표로 교체하기보다 PSNR을 비교하는 축/시점을 바꾸는 것이 우선이다.
새 metric으로 기존 이득을 확대해서 표현하지 않는다.

## 1. 실제 자료와 사용 범위

| 자료 | 확인한 내용 | 한계 |
|---|---|---|
| `benchmark-B/evidence/summary.json` | 152 run의 장면별 endpoint PSNR, update 수, training GPU seconds, wall seconds | 19-scene 표의 원본 수치가 있으나 checkpoint PSNR 전체는 이 JSON에 없음 |
| `benchmark-B/prepare_manifest.py` | RR 대 `relative_floor_interval_softmax_rr`, K=8, gamma=log(3), stride20, fixed topology | 현재 Method의 normalized per-view Gibbs sampler가 아님 |
| `dense-supervision/evidence/manifest_curve.json` | event60, 19 scene × 2 arm, 24 checkpoint, 38 complete | manifest는 평가 시점·실행 상태이며 PSNR 곡선 자체가 아님 |
| `dense-supervision/figure_convergence.png`, `plot_convergence.py` | KF-only 대 KF+dense iteration 곡선, baseline endpoint에 대한 최초 crossing | ERCB/growth 전체 방법의 비교가 아니며 actual time-to-quality도 아님 |
| `dense-supervision/evidence/manifest_budget.json` | event120, 38 complete, 5 checkpoint | event60 곡선과 event120 최종 표를 하나의 실행으로 합칠 수 없음 |
| `dense-supervision/evidence/manifest_ercb.json` | 파일에 기록된 완료 7/19 | 현재 파일만으로 완성된 19-scene 비교라고 판단할 수 없음 |
| `dense-supervision/evidence/manifest_k4.json` | 파일에 기록된 완료 11/19 | 현재 파일만으로 완성된 19-scene 비교라고 판단할 수 없음 |
| `ERCB_ablation/exp03/evidence/summary.json` | 14 pair의 양쪽 3-point PSNR 곡선 | ablation 내부 선행 재현 실험이며 장면/방법이 제한적; 19-scene 곡선 대체 불가 |
| `VIGS_ERCB_ablation/evidence/transfer/*summary.json` | 시스템 변경 후 endpoint/shared-view 품질과 서비스 통계 | 순수 sampler on/off 또는 품질 수렴 곡선이 아님 |

`manifest_curve.json`이 가리키는 38개 `evaluation_curve.jsonl`은 원래 절대경로와
현재 workspace로 재매핑한 경로 모두 **0/38 존재**했다. `context/experiments`와
현재 `results`에도 해당 이름의 로그를 찾지 못했다. 따라서 아래 검토는
21.4%를 원시 곡선으로 재계산한 것이 아니다. 그림 좌표를 역산해 원본으로 취급하지 않는다.

## 2. benchmark-B 원본 JSON에서 직접 재집계

조건: `runs` 중 `stride == 20`; (family, scene, budget, arm)로 pair.
scene 산술평균, 승리는 ERCB PSNR > RR PSNR. 단일 seed 결과이며 통계적 유의성 판정이 아니다.

| updates/interval | RR PSNR | ERCB PSNR | 평균 차이 | ERCB 승리 |
|---:|---:|---:|---:|---:|
| 15 | 20.772348 | 21.387752 | +0.615404 | 16/19 |
| 30 | 22.220308 | 22.333985 | +0.113678 | 7/19 |
| 60 | 22.881246 | 23.112572 | +0.231326 | 9/19 |

같은 예산에서 training-GPU-time ERCB/RR 비의 scene 중앙값은 각각
1.004715 / 0.998737 / 0.999684다. 이는 거의 같은 기록된 GPU 연산시간에서
저예산 품질이 개선되는 자료이며, 목표 품질 도달 시간이 기록된 것은 아니다.

절반 예산으로 더 큰 예산의 RR endpoint에 도달하는지 비교하면:

| 비교 | ERCB endpoint >= RR endpoint | 평균 PSNR 차이 |
|---|---:|---:|
| ERCB@15 vs RR@30 | 1/19 | -0.832556 dB |
| ERCB@30 vs RR@60 | 4/19 | -0.547261 dB |

첫 비교 통과: RPNG table_05. 둘째: RPNG table_03/04/05/06.
이는 사후 budget-efficiency 진단이다. 서로 다른 실행·arrival-to-update 매핑·LR horizon을
비교하므로 동일 실행의 time-to-quality나 인과적인 수렴 가속률로 해석하지 않는다.
2배 가속을 일반적으로 주장할 근거는 없지만, 더 작은 가속 가능성까지 부정하지도 않는다.

## 3. 기존 21.4%의 정확한 의미

`plot_convergence.py`는 q = KF-only의 최종 PSNR로 놓고
`1 - first_crossing_dense(q) / total_iterations_KF`를 계산한다.
이는 baseline의 최종 품질을 전체 예산 종료 전에 달성했다는 뜻이다.
baseline 자신도 q에 일찍 도달할 수 있으므로 **두 방법의 도달 속도 비교와 다르다.**

교정 비교는 같은 q에 대해 양쪽 모두 first crossing을 계산한다:

`saving(q) = 1 - crossing_ours(q) / crossing_baseline(q)`.

추가 점검:

- 최초 crossing 뒤 하락할 수 있다. 예를 들어 그림의 table_05는 마지막에 크게 하락한다.
- 24 checkpoint 사이의 실제 crossing은 관측되지 않았다. 관측 구간과 선형 보간 추정을 구분한다.
- 첫 checkpoint에서 이미 목표 이상이면 좌측 censoring이며 정확한 도달 시점이 아니다.
- 미달은 미달로 남긴다. 도달한 장면만 평균내면 성공률이 가려진다.
- 기존 표와 curve 재실행의 endpoint 차이를 감사한다. 그림의 aria1253rot Δ +1.11과
  TABLE_X의 +0.99, ego-drive +0.89와 +0.74는 단순 같은 수치로 취급할 수 없다.
  원시 로그 확보 후 평가 집계(per-view mean vs logged PSNR), seed/source/init를 확인해야 한다.

## 4. 권장 평가안

### A. 지금 가진 결과를 살리는 순서

1. 먼저 기존 event60 원시 로그를 확보한다. 필요한 것은 run별 `evaluation_curve.jsonl`,
   `training_timing.jsonl`(있다면), `view_scheduler_summary.json`, arrival schedule,
   실행 provenance다. 현재 저장된 그림을 수작업으로 digitize하지 않는다.
2. 두 arm의 held-out UID, checkpoint update 수, completed-update reporting을 대조하고,
   24-point 재실행과 기존 5-point run의 endpoint 차이를 확인한다.
3. 같은 q에 대한 **양쪽 first crossing**, 목표 도달 scene 비율, 도달 후 유지 여부를 산출한다.
   여러 목표에서 민감도를 보고한다. 기존 baseline endpoint를 목표로 쓰는 경우 명시적으로
   retrospective endpoint-matching으로 표시한다. 최종 평가의 목표/유지 규칙은 개발 세트에서 고정한다.
4. KF-only 대 KF+dense 결과는 dense supervision의 동기로 사용한다. κ-growth 및 최신
   normalized sampler의 단독 실증으로 바꾸어 쓰지 않는다.

### B. 추가 ablation이 필요할 때

완료된 최신 recipe에서 먼저 한 요소만 바꾸는 비교를 한다:

- growth: 동일 sampler에서 KF-only / arrived dense / κ-growth.
- sampling: 동일 admitted-view UID·시점에서 RR / **현재 normalized sampler**.

공통 causal packet/pose, init 정책, resolution, loss, held-out, seed 집합을 유지한다.
새 실험은 장면별 또는 전체 horizon 비율로 topology를 닫는 과거 replay recipe를 복제하지 않는다.
기존 fixed-topology 또는 densification-horizon 결과는 진단 자료로 범위를 표시한다.

한 실행 중 공통 work checkpoint에서 다음을 저장한다:

`sensor_timestamp, last_arrived_uid, completed_updates, physical_training_renders,
mapping_elapsed_seconds, evaluation_overhead_seconds, gaussian_count,
heldout_uid, heldout_psnr`.

실제 mapper에서 update당 처리 view 수가 달라지면 iteration만 비교하지 말고 physical
training render도 기록한다. GPU-only 시간, mapper wall time, 실시간 sensor-to-map latency는
서로 다르다. 평가·저장 overhead를 포함한 실행 전체 wall_seconds를 비례 배분해 시간 곡선을
만들지 않는다. 저장 map 사후 평가나 별도 계측 run으로 평가 overhead를 통제한다.

### C. 논문에 둘 지표와 그림

주 지표: **동일 목표 held-out 품질까지 필요한 work/time**, 목표 도달 비율.
주 그림: PSNR–work/time 곡선과 두 방법의 같은 목표 crossing 사이의 수평 화살표.
안정성: 사전 고정한 실제 시간/work 구간 동안 목표를 유지하는지 확인한다. checkpoint가
불균등하므로 단순히 몇 점 연속 통과하는지만으로 서로 다른 유지 시간을 같게 취급하지 않는다.
확인 구간이 EOS를 넘어가면 미확인으로 남기고 추가 optimizer update를 하지 않는다.
보조 지표: 공통 관측 구간의 quality-curve area와 final PSNR. Area는 전체 과정의 품질이지
도달 속도 자체가 아니므로 주 가속률을 대체하지 않는다.

온라인에서는 관측 범위 증가와 관측된 영역의 학습 속도가 섞인다. 기존 전체 held-out
곡선은 그대로 명시해서 보고하되, 새 영역의 빠른 refinement를 주장하려면 공통 causal
관측으로 정의한 영역/held-out cohort를 고정하고 최초 관측 이후의 품질·지연을 추가 측정한다.
매 checkpoint마다 평가 집합을 조용히 바꾼 평균은 동일 대상의 수렴 곡선이 아니다.

Geometry 가속은 독립 region GT 및 surface 보존 지표의 시간 추이가 있을 때만 주장한다.
PSNR, selection-count variance/entropy, 첫 service delay만으로 geometric convergence를
판정하지 않는다. 이 검토에서는 geometry의 신규 시간별 GT 결과를 확인하지 않았다.

## 논문 구성 권고

기존 endpoint 표를 버릴 필요는 없다. `Final quality`로 유지하고,
`Convergence efficiency` 그림/작은 표를 추가한다. 낮은 예산에서 특히 효과가 난다는 결과와
중간·높은 예산에서 장면별 승률이 낮아진다는 결과를 함께 설명한다.
원시 곡선 검증 전에는 21.4%를 실제 speedup으로 승격하지 않는다.
