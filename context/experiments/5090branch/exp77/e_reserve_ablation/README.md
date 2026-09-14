# exp77 E — 소수 시퀀스에서 최적화 부족 원인 검증

시작: 2026-09-11. 이전 exp78(Aria 재현)은 [exp77 단계 B](../b_aria_reproduction/exp78_aria_final_v7_reproduction.md)로 통합됐다. 현재 작업은 exp77 E에 통합한다. **사용자가 명시적으로 exp78로 넘어가라고 하기 전까지 모든 후속 작업은 exp77 하위 단계로 기록한다.**

[기존 Aria와 RPNG/UT-MM 데이터·실행량 비교표](dataset_comparison.md)

## A. RPNG table_06 tracking reserve 단일 요인 비교

가설: 30fps 입력에서 40ms tracking reserve가 concurrent replay를 막아 학습량을 제한한다. reserve를 20ms로 낮추었을 때 실제 gate 허용·학습량·held-out PSNR이 회복되는지 검증한다. 20ms는 진단 후보이며 기본값으로 채택한 것이 아니다.

- baseline 40ms와 candidate 20ms를 각각 2회, 40→20→20→40 순서로 실행한다. 기존 runner와 같은 seed 0을 유지한 반복이며 비동기 실행 변동을 확인한다.
- final-v7 clean RTX5090, fixed 1×, sensor-EOS optimizer zero-tail, terminal 추가 학습/pruning off, native benchmark 해상도, 동일 held-out split을 유지한다.
- 프로파일 적용 **뒤에** reserve를 덮어쓰며 실행 로그의 유효값을 확인한다. 원본 VIGS 소스는 수정하지 않는다.
- PSNR·ATE·Recall·completed Adam·gate 허용 수·timing·EOS audit를 기록한다. 업데이트 수 증가만으로 품질 개선을 판정하지 않는다.
- 전체 16개를 다시 돌리지 않는다. 우선 table_06만 비교한 뒤 결과에 따라 Aria 회귀·fast-straight 초기화 문제를 같은 exp77의 후속 단계로 진행한다.

상태: table_06 40→20→20→40ms 비교 4회 완료. 아래 결과 참조.

원본 결과: `results/experiments/exp78_reserve_ablation_20260911/`.
[통합된 기준 실험 exp77](../README.md)

원본 결과 경로와 실행 스크립트의 `exp78` 문자열은 번호 정정 이전 실행 ID로 보존하며, 새 exp78 실험을 뜻하지 않는다.

## E1 결과

| Run | Reserve (ms) | Held-out PSNR (dB) | ATE (cm) | Completed Adam | Tail update |
|---|---:|---:|---:|---:|---:|
| run0_reserve40 | 40 | 21.002 | 2.764 | 2247 | 0 |
| run1_reserve20 | 20 | 21.352 | 2.784 | 2402 | 0 |
| run2_reserve20 | 20 | 21.431 | 2.725 | 2466 | 0 |
| run3_reserve40 | 40 | 21.232 | 2.752 | 2273 | 0 |

40ms 평균 **21.117 dB**, 20ms 평균 **21.391 dB**, 차이 **+0.274 dB**. 4회 모두 deadline/EOS 이후 완료 update 0회다. 단일 장면·각 2회 결과로, 27dB 격차를 해결하거나 다른 장면에 일반화했다고 판정하지 않는다. 후속 분석·검증도 exp77 안에서 진행한다.

[결과 JSON](evidence/summary.json)

## E2 — reserve 20ms↔0ms

[Dense replay 병목 분석](replay_analysis.md)을 바탕으로 table_06에서 20→0→0→20ms 비교를 진행한다. 1×·zero-tail·seed0·동일 split 유지. 결과 경로: `results/experiments/exp77e2_reserve_zero_20260911/`.

상태: 4회 모두 완료·평가 성공. deadline 및 sensor-EOS 뒤 optimizer update는 4/4 모두 0회다.

| Run | Reserve (ms) | Held-out PSNR (dB) | SSIM | LPIPS | ATE (cm) | Dense replay | Completed Adam | Tracking gate 허용 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| run0_reserve20 | 20 | 21.004 | 0.6898 | 0.3414 | 2.746 | 1,875 | 2,256 | 326 |
| run1_reserve0 | 0 | 21.483 | 0.7046 | 0.3241 | 2.727 | 2,105 | 2,484 | 635 |
| run2_reserve0 | 0 | 21.369 | 0.6976 | 0.3322 | 2.752 | 2,105 | 2,486 | 634 |
| run3_reserve20 | 20 | 20.991 | 0.6940 | 0.3426 | 2.752 | 1,872 | 2,233 | 324 |

20ms 평균 **20.998dB**, 0ms 평균 **21.426dB**, 차이 **+0.428dB**다. 0ms에서 dense replay는 평균 1,873.5→2,105회(**+12.36%**), 전체 Adam은 2,244.5→2,485회(**+10.72%**) 늘었다. 반면 ATE 평균은 2.749→2.739cm로 사실상 동일하다. 실행 순서를 20→0→0→20으로 감쌌는데 양 끝 20ms가 모두 낮아 단순 warm-up/drift 설명도 약하다.

판정: RPNG 전이 실패의 전부를 해결한 것은 아니지만, **tracking geometry 변화 없이 온라인 RGB 학습 기회가 줄어드는 실행 병목이 실제 PSNR 손실을 만든다**는 인과 증거다. 0ms도 목표 수준과는 큰 격차가 있으므로 reserve만 더 튜닝하지 않고, TensorRT로 tracking/update 비용을 줄여 같은 zero-tail 예산 안에서 학습량이 늘어나는지 matched 비교한 뒤 initialization·coverage 축으로 넘어간다.

[E2 결과 JSON](evidence/e2_summary.json)

## RPNG TensorRT 준비 (품질 실험 전 인프라)

RPNG 전처리 입력 `344x616`/feature `43x77`에 맞춘 DroidNet fnet·update·PGBA FP16 엔진을 RTX 5090/TensorRT 10.13에서 빌드하고 PyTorch 대비 수치·shape·finite 검증을 통과했다. 기존 Aria 고정 `464x464` 엔진은 덮어쓰지 않았고 `VIGS_DROID_TRT_ENGINE_DIR` opt-in 선택 경로를 추가했다. 엔진과 재빌드 방법은 VIGS repo의 `pretrained_models/rpng_344x616_rtx5090/README.md`에 기록했다. 아직 이 엔진을 켠 strict table_06 held-out 비교는 실행하지 않았으므로 PSNR 개선으로 기록하지 않는다.
