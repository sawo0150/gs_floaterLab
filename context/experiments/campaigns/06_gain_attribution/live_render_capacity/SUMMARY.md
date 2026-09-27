# RTX 5090에서 tracking을 포함한 렌더링 예산과 바닐라 비교

2026-09-25 · RTX 5090 32GB + Intel i9-12900 · driver 580.173.02 · seed0

**15회/KF를 모든 장면에서 보장되는 실시간 예산으로 채택할 근거는 아직 없다.** 실제 tracker를 붙이면 우리 추가 KF/dense 학습이 충분히 실행되지 않으며, 이전 고정 렌더링 실험의 품질 이득도 세 장면 모두에서 유지되지 않았다.

## 비교 조건

- 입력 timestamp 그대로 1× 속도로 RGB+IMU를 전달하고 tracking, depth 추정, PGBA, mapping을 함께 실행했다. Aria 1303frames/20Hz, RPNG table_06 약30Hz, UTMM square-1 약30Hz. 영상 크기(H×W)는 각각464×464,344×616,328×648.
- 양쪽 frontend 반복은4/2로 맞췄다. IMU pose prediction 시작 KF는 공식 RPNG20/UTMM15 및 기존 Aria live20을 적용했다. 설정파일과 소스를 각 실행 결과에 보존했다.
- **바닐라:** 공식 VIGS-SLAM mapper의 최근 window+과거 global KF2 구조. 원본 mapper 소스는 변경하지 않았다.
- **우리 구조:** native 최근 window, 추가 학습은 full-pool KF/dense 교대 ERVS. 추가 학습은 현재 구현의 tracking idle 시간에 실행한다. 실행 시 native global KF는0이다.
- 초기화·재초기화·native·추가 학습이 모두 **KF admission당15 camera training renders 상한**을 공유한다. Window 여러 장을 한 optimizer step에 쓰면 카메라 수만큼 센다. 15 optimizer iterations가 아니다.
- 입력 종료 시각 이후 Gaussian optimizer update는0회다. 지연된 tracking은 끝까지 처리해 그 시간을 숨기지 않았다. 모델/engine 로딩 약1초와 지도 저장 후 평가만 입력 clock 밖이다.

## 실제 학습량과 품질

아래 KF 분모는 map generation별 admission 수다. Reset 뒤 재등록도 포함하므로 고유 KF 수나 최종 tracker KF 수와 다르다. 수치는 **실제로 optimizer에 반영된 학습 렌더** 기준이다.

| 장면 | 학습 렌더/KF: 바닐라 → 우리 | Held-out PSNR: 바닐라 → 우리 | 우리−바닐라 | Tracking 완료시간: 바닐라 → 우리 / 입력길이 |
|---|---:|---:|---:|---:|
| Aria | 15.00 → 14.79 | 19.15 → 19.37 dB | +0.22 dB | 65.12 → 67.13 / 65.10 s |
| RPNG table_06 | 15.00 → 12.43 | 19.39 → 17.92 dB | -1.48 dB | 143.90 → 115.06 / 92.24 s |
| UTMM square-1 | 14.81 → 9.73 | 15.77 → 11.33 dB | -4.44 dB | 54.22 → 54.23 / 53.81 s |

양쪽에 같은 **상한과 입력 시간**을 줬지만 실제 총 렌더링 수·pose·KF history는 다르다. 이 표는 전체 시스템 동작 비교이며, sampler만 바꾼 동일 총연산량 ablation이 아니다. Seed0 각1회 실행이고 저장된 결과를2회 평가한 것이므로 학습 재현성/통계적 유의성을 주장하지 않는다.

## 예산이 실제로 쓰인 곳과 지연

| 장면 | 우리 native / 추가 KF / 추가 dense | 우리 예산 사용률 | 입력 시작 지연 p95: 바닐라 → 우리 | 최종 학습 가능 tracker KF 중 map에 들어온 수: 바닐라 / 우리 |
|---|---:|---:|---:|---:|
| Aria | 976 / 267 / 266 | 98.6% | 1.152 → 2.917 s | 91/92 / 88/92 |
| RPNG | 1815 / 0 / 0 | 82.9% | 54.613 → 24.732 s | 103/187 / 134/170 |
| UTMM | 591 / 6 / 6 | 64.8% | 2.271 → 0.898 s | 70/71 / 51/52 |

- Aria는 추가 학습이 실행됐지만, 입력65.10초 대비 우리 처리시간67.13초이고 p95입력지연2.92초다. 평균 처리량과 낮은 지연은 구분해야 한다.
- RPNG는 추가 KF/dense 학습이 모두0회였다. 이 결과로 ERVS 또는 dense의 학습 효과를 평가할 수 없다.
- UTMM은 추가 KF/dense 각각6회에 그쳤다. 총 예산이 남았어도 현재 스케줄이 추가 학습에 충분히 사용하지 않았다.
- `online_mapper_runtime.py`는 tracking 중 추가 학습을 실행하지 않고, `online_photometric.py`는 다음 입력 전까지 예상 step 시간이 확보되지 않으면 시작하지 않는다. 이것이 코드상 추가 학습 기회를 제한하는 조건이다. 개별 gate의 거절 횟수는 따로 측정하지 않았으므로 UTMM의 단독 원인까지 확정하지 않는다.
- Online pose/depth, map geometry, PGBA history도 실행마다 달라진다. 품질 하락 전체를 추가 학습 부족 하나로 설명하지 않는다.

## 보조 렌더까지 포함한 작업량

15회 상한은 학습용 렌더 기준이다. No-grad 보조 렌더와 deadline 직전 optimizer 반영 전에 중단된 forward도 실제 시간을 소비하므로 원시 카운터에 보존했다.

| 장면 | 완료 학습 렌더: 바닐라 / 우리 | 전체 camera forward: 바닐라 / 우리 | 전체 forward/KF: 바닐라 / 우리 |
|---|---:|---:|---:|
| Aria | 1575 / 1509 | 1678 / 1609 | 15.98 / 15.77 |
| RPNG | 1965 / 1815 | 2093 / 1959 | 15.98 / 13.42 |
| UTMM | 1185 / 603 | 1276 / 663 | 15.95 / 10.69 |

## Tracking만 실행한 대조

같은 integration frontend4/2·IMU pose prediction20으로 RPNG mapping을 끈 결과, 학습 렌더0회에서도 입력92.245초를 처리하는 데 **111.477초**가 걸렸다. 입력 시작 지연p95는21.848초였다. Mapping 포함 우리 실행115.056초와 비교하면, 이 설정에서1× 입력을 따라가지 못하는 문제는 mapping을 제거해도 남는다. 단일 실행의 시간 차이를 정확한 mapping 비용으로 해석하지 않는다.

이 대조는 우리 integration tracker를 사용했다. 공식 VIGS source만의 tracker-only 결과는 아니다. 결과: `results/campaigns/gain_attribution/live_render_capacity/tracking_controls/rpng_imu20/`.

## 이전 고정 렌더링 실험과의 관계

같은 causal tracker packet과 총 렌더링 수를 정확히 맞춘 이전15/KF 실험에서는 우리 구조가 Aria +1.82, RPNG +1.05, UTMM +2.54dB 높았다. 그 runner는 각 입력 이후 남은 credit을 추가 학습으로 모두 소비했다. 실제 tracking을 동시에 실행한 이번 runtime은 idle 시간이 부족하면 그 작업을 생략한다. **기존 결과는 mapper-only 품질 근거로 남지만, 실시간 실행의 품질 근거로 대체할 수 없다.**

다음 구현 과제는 총 예산 안에서 추가 KF/dense 학습 몫을 확보하는 것이다. 현재처럼 남는 idle 시간에만 맡기면 논문에서 검증한 학습 구성 자체가 실행되지 않는 장면이 생긴다. 이 기록을 위해 production mapper나 논문은 수정하지 않았다.

## 설정 정정 및 제한

- 앞선 `comparison15_v1`, `current_frontend`, `v3`–`v6`, `tracking_controls/rpng_official`은 mapper setup에서 CLI 기본값 `IMU_poseinit_after=100000`을 상속했다. IMU preintegration/BA는 실행됐지만 IMU pose prediction은 사실상 비활성이었다. 그 수치는 진단 기록으로 보존하고 위 최종 표에는 사용하지 않았다. `current_frontend`라는 과거 폴더명은 정상 배포 설정을 보증하지 않는다.
- 상한 없는 Aria16.69 renders/KF probe도 위 과거 설정이며 지연이 발생했다. 5090의 최대 성능 또는 안전한 실시간 예산으로 채택하지 않는다. 이번 측정은15/KF 후보를 검사한 것이며 최대치 탐색이 아니다.
- 바닐라 비교용 adapter는 held-out 제외, packet-local index, 동일 reciprocal loss numerical 보정, 예산/deadline, IMU metric 초기화 이후 mapping 시작, reset lock을 적용한다. 공식 소스 그대로의 기본예산 재현을 뜻하지 않는다.
- Optimizer 완료 계측에 CUDA synchronization이 포함된다. 수치는 계측과 deadline guard가 포함된 runtime 성능이며 순수 GPU 최대 처리량이 아니다. CPU와 장면 복잡도, 해상도에도 의존한다.
- 6run 모두 인과적 입력 순서·렌더/commit 계수·source snapshot·zero-tail 독립 검증을 통과했고 held-out 평가2회가 일치했다. 이는 실행 기록의 검증이며 실시간 또는 품질개선 통과 판정이 아니다.
- 원본 trajectory/depth 또는 MPS를 replay하지 않았다. 평가용 trajectory filling은 지도 저장 후 각 실행의 자기 tracker에서 수행하고 학습에 사용하지 않았다.
- 이번1× 입력률 측정은 기존 strict27의1.5× 시간 계약과 별도다.

## 결과 파일

- [원시/검증 결과 CSV](../../../../../results/campaigns/gain_attribution/live_render_capacity/comparison15_imu_v2/summary.csv)
- [독립 검증 JSON](../../../../../results/campaigns/gain_attribution/live_render_capacity/comparison15_imu_v2/verified_summary.json)
- [전체 실행과 평가 결과](../../../../../results/campaigns/gain_attribution/live_render_capacity/comparison15_imu_v2/summary.json)
- [실험 카드와 재실행 명령](README.md)
