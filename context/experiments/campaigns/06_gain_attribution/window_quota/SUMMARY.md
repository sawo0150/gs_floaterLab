# Recent KF 할당량과 full-history pool — 2026-09-28

## 결론

채택한 **3:3:6을 유지**한다. 최근 KF 전용 몫을 1:5:6으로 줄이면 세 장면의
평균 PSNR 차이는 −0.025dB였지만, 0:6:6으로 없애면 −0.154dB였다.
Aria에서는 window 전용 몫이 없어도 거의 같았고, RPNG와 UTMM에서는 낮아졌다.
따라서 window를 모든 장면에 필수라고 주장할 수는 없지만, 현재 공통 설정에서
없애도 성능이 보존된다고 할 근거도 없다. 1:5:6은 후속 대안으로 남긴다.

**Full-history pool은 과거 관측을 보관하는 범위이고, window quota는 학습량을
배분하는 정책이다.** 현재 구조는 과거 영상을 window 밖이라는 이유로 버리지
않으면서, 최근 KF에도 학습량 일부를 예약한다. 두 선택은 양립한다.

## 비교 조건

비율 순서는 **최근 KF window / 전체 KF ERVS / 전체 admitted dense ERVS**다.
3:3:6은 직전 채택 실험을 재사용했고, 1:5:6과 0:6:6을 각 세 장면에서 실행했다.
사전 계획한 신규 GPU 실행 6회만 수행했다.

- 40 training renders/KF, 영상당 Adam 1회, seed 0, 동일 causal tracker replay.
- PPM/Sobel birth, downsample multiplier 0.8: init 51.2 / regular 204.8.
- Opacity <0.1 pruning, 300 training renders마다 packet 경계에서 실행.
- 최근 10개 nonempty KF birth batch 보호. Densify/Carve/blur filter OFF.
- Growth κ=16, ERVS τ₀=4, 각 pool의 entropy weight 4/N, 누적 선택 횟수 사용.
- 동일 입력·held-out cohort·admission·생성점·pruning 시점. Zero-tail.
- Tracker를 함께 실행한 실시간 deadline 실험이 아니라 **fixed-work mapper 비교**다.

## Held-out PSNR

괄호는 같은 장면의 3:3:6 대비 차이(dB)다.

| 장면 | 3:3:6 | 1:5:6 | 0:6:6 |
|---|---:|---:|---:|
| Aria1253 | 25.783 | 25.807 (+0.025) | 25.779 (−0.004) |
| RPNG table_06 | 25.225 | 25.183 (−0.042) | 24.932 (−0.293) |
| UTMM square-1 | 22.272 | 22.214 (−0.058) | 22.106 (−0.166) |
| 장면별 차이의 단순 평균 | — | −0.025 | −0.154 |

단일 seed 결과이므로 작은 차이를 통계적으로 유의한 개선이나 동등성으로
해석하지 않는다. 저장한 각 지도의 held-out 평가는 두 번 수행했지만, 이는
학습 seed 반복과 다르다.

## 실제로 최근 KF 학습이 줄었는가?

0:6:6에서도 최근 KF는 전체 KF pool에 남아 ERVS로 선택될 수 있다.
아래는 IMU reset 이후 **최종 map generation**에서, KF 학습 중 당시 recent
window에 속한 KF를 선택한 비중이다. Window 역할뿐 아니라 full-KF 역할의
선택도 포함한다.

| 장면 | 3:3:6 | 1:5:6 | 0:6:6 | 최종 KF / admitted dense 수 |
|---|---:|---:|---:|---:|
| Aria1253 | 65.62% | 44.70% | 39.41% | 91 / 227 |
| RPNG table_06 | 59.63% | 34.03% | 24.45% | 186 / 465 |
| UTMM square-1 | 69.33% | 53.07% | 47.28% | 71 / 177 |

최종 pool membership은 세 조건에서 동일하다. 0:6:6은 recent KF를 제외하는
실험도, tracking frontend의 window를 없애는 실험도 아니다. Pruning의 최근
birth 보호도 그대로 유지했다.

## Gaussian 수와 mapper 시간

| 장면 | 조건 | 최종 Gaussian | Mapper 시간(s) |
|---|---|---:|---:|
| Aria1253 | 3:3:6 | 195,316 | 34.654 |
| | 1:5:6 | 194,674 | 35.002 |
| | 0:6:6 | 193,307 | 34.306 |
| RPNG table_06 | 3:3:6 | 202,838 | 105.465 |
| | 1:5:6 | 199,189 | 110.113 |
| | 0:6:6 | 193,157 | 102.302 |
| UTMM square-1 | 3:3:6 | 121,363 | 36.529 |
| | 1:5:6 | 121,702 | 37.410 |
| | 0:6:6 | 121,305 | 36.123 |

생성점 수는 같지만 선택 영상이 달라지면 opacity와 pruning 결과도 바뀐다.
이번 비교는 pruning을 포함한 현재 시스템의 sampling 비율 비교이며,
Gaussian 수까지 고정한 순수 sampling 효과 분해는 아니다. 시간 역시 단일
실행으로 측정했으므로 작은 차이를 안정적인 속도 개선이라고 주장하지 않는다.

## 공정성 및 구현 검증

- CPU 검사 44개 PASS, 신규 6회 실행 모두 독립 audit PASS.
- Training render와 Adam 총수는 각각 Aria 4,760 / RPNG 9,080 / UTMM 3,600으로
  조건 간 동일하다. Arrival별 누적 render, pose, 평가 cohort도 동일하다.
- Admission, pool membership, birth CSV, pruning 시점이 control과 일치한다.
  보호 대상 삭제 0개, optimizer state 정렬 및 최종 map 점수 회계 PASS.
- Window KF와 full-pool KF는 모두 동일한 RGB-D/normal loss를 쓴다.
  Dense만 RGB-only다. Window만 geometry를 학습한다고 설명하면 안 된다.
- 대부분 조건의 KF/dense 총횟수는 같지만 bootstrap·quota 잔여 처리 때문에
  RPNG 0:6:6은 KF +1 / dense −1, UTMM 0:6:6은 KF −1 / dense +1이다.
  Loss 종류가 달라지는 render 위치는 0–9개이며 LR 위치는 모두 같다.
- 실험 종료 시 source 228개 및 snapshot checksum을 확인했다. 이후 standalone
  `run_selected_mapping.py`의 subprocess 환경만 기존 실험 runner와 일치하도록
  보완했다. Worker, recipe, 실험 결과는 바꾸지 않았다. 후속 quota 테스트 3개와
  launcher command/environment mock 검증 PASS; 추가 GPU 실행은 하지 않았다.

## Window의 역할을 어떻게 설명할 것인가?

누적 ERVS count는 **영상이 과거에 몇 번 선택됐는지**를 나타낸다. 지도에
새로 추가된 Gaussian이 그 영상으로 얼마나 학습됐는지를 나타내지는 않는다.
따라서 이미 여러 번 선택된 인접 KF라도 지도 확장 뒤에는 다시 유용할 수 있다.
작은 recent quota는 새 영역의 적시 정제를 지원하고, full-history ERVS는 과거
관측 재방문과 영상 간 누적 학습량 배분을 담당한다는 설계가 가능하다.

이는 코드 구조와 일치하는 **설계 근거/가설**이다. 이번 최종 RGB PSNR 비교만으로
새 Gaussian의 수렴이나 geometry 개선을 직접 입증한 것은 아니다. Region GT나
시간별 수렴을 측정하지 않았으며, Carve 효과도 검증하지 않았다.

논문용 표현 후보:

> We retain all admitted views for revisiting and reserve a small fraction of
> mapping updates for recent keyframes to support timely refinement of newly
> mapped regions. The remaining updates sample the full keyframe and dense-view
> pools using ERVS.

ERVS는 두 pool에서 각각 적용되며, window 선택도 누적 횟수에 포함된다.
`unlimited pool`보다는 `full-history training pools`가 정확하다. 이는 현재 map
generation 안에서 age/window에 따라 관측을 제거하지 않는다는 뜻이다.
모든 입력 영상을 즉시 admission하거나, 무한 메모리를 제공하거나, 모든 선택을
하나의 global ERVS로 수행한다는 뜻은 아니다.

`paper/latex/sec/4_method.tex`의 예전 native/flexible service 설명과 현재 unified
sampling은 일치하지 않는 부분이 있다. 논문을 갱신할 때 실제 mixture와 ERVS 적용
범위를 명시해야 한다. 이번에는 tex를 수정하지 않았다.

## 재현 자료

- [사전 계획 및 실행 카드](README.md)
- [결과와 감사 요약 JSON](../../../../../results/campaigns/gain_attribution/window_quota/gpu40_v1/comparison.json)
- [채택 recipe](../../../../../benchmarks/online_gs/campaigns/gain_attribution/selected_mapping_recipe.json)
- [비교 runner](../../../../../benchmarks/online_gs/campaigns/gain_attribution/run_window_quota_comparison.py)
- [직전 init/pruning 대조군](../protected_prune/init_increase/SUMMARY.md)
