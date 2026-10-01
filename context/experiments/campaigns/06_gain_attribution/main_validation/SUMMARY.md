# 병합 main 실제 GPU 검증 — 2026-09-29

**네 장면 모두 official vanilla 대비 held-out PSNR 이득이 유지됐다.** Main commit `5fa8c76e`에서 ours/vanilla를 각각 새로 실행했다. 총8회, seed0, 동일40 training renders/KF. 추가 튜닝 없음.

| 장면 | Vanilla PSNR | Main PSNR | 이득(dB) | 병합 전 대비 main 차이 |
|---|---:|---:|---:|---:|
| Aria1253 | 20.743 | 25.776 | +5.033 | -0.0066dB |
| RPNG table_06 | 22.473 | 25.224 | +2.750 | -0.0016dB |
| UTMM square-1 | 18.882 | 22.285 | +3.403 | +0.0131dB |
| Aria1253_rot | 21.801 | 25.018 | +3.217 | 새 transfer 장면 |

장면별 차이의 단순 평균은 **+3.601dB**. 기존 세 장면은 병합 전 대비 최대 절대 차이 **0.0131dB**로 작았다. 단일 seed이며 통계적 동등성을 검증한 것은 아니다.

## 실행·공정성 검사

- 모든8실행과 저장지도별2회 평가 PASS. 각 pair의 causal tracker archive/pose/depth, arrival별 render 예산, 평가 trajectory/cohort가 일치한다.
- Ours의 선택정책336·κ16·τ₀4·누적count·영상별Adam·init0.8·보호prune0.1/300을 유지했다. 모든 pruning에서 보호 대상 삭제0, source checksum 불변.
- 공식 vanilla commit22ffe24의 mapper에 동일prefix render예산을 적용했다. 기존 공통 invalid-depth reciprocal 보정은 유지했다. Vanilla의 native loss/grouping/topology를 우리 방식으로 교체하지 않았다.
- 원본 입력 도착 순서와 zero-tail을 검사했다. 평가용 post-EOS trajectory는 두 방법의 평가에만 사용했다.
- 기존 세 장면은 main 공개 launcher를 사용했다. Rot는 같은 main worker/recipe를 실행하되 별도 scene-path adapter로 추가 입력을 연결했다. 공개 launcher의 기본 scene 목록은 여전히 기존3개다.

## Gaussian 수와 mapper 시간

| 장면 | GS vanilla → main | Mapper초 vanilla → main | Training render(각각) / Main Adam |
|---|---:|---:|---:|
| Aria1253 | 190,135 → 195,157 | 27.08 → 37.96 | 4,760 / 4,760 |
| RPNG table_06 | 234,140 → 203,113 | 81.20 → 114.82 | 9,080 / 9,080 |
| UTMM square-1 | 163,083 → 121,351 | 34.64 → 38.33 | 3,600 / 3,600 |
| Aria1253_rot | 257,723 → 201,506 | 43.29 → 61.13 | 6,120 / 6,120 |

동일render이지 동일Adam/시간 비교는 아니다. 시간은 단일실행이고 입력 변환 CPU 작업 일부가 다른 장면 실행과 겹쳤으므로 엄격한 speed benchmark로 해석하지 않는다. Dense/ERVS 단독효과, geometry/floater 개선, 실제 tracking 동시실행 실시간성은 이 비교로 입증하지 않는다.

## Aria1253_rot 입력

기존 공통 archive가 없어서 원본 `0416_301-1253-2_rot/0416_301-1253-2.vrs`의 **전체1521 RGB**와 imu-right75917개를 새로 추출했다. skip-head0, MPS trajectory/depth/point cloud 사용0. VRS 고정Tcb는 기존 Aria adapter와 일치했다. 기존1498프레임 실험과 다른 구간이므로 과거rot수치를 재사용하지 않았다.

Held-out은 다른 세 장면과 같은 `index%5==0 또는 마지막` 규칙으로 학습 전 **305장** 고정했다. 공식 tracker 기록은176KF·183event·mapper reset1이며 validator `valid=true`, violations0, capture Gaussian update0. 두 mapper는 같은 archive를 사용했다.

## 재현 자료

- 결과 JSON: `results/campaigns/gain_attribution/main_validation/comparison.json`
- 기존3scene 원본: `results/campaigns/gain_attribution/main_validation/gpu40_v1/{aria,rpng,utmm}/{ours,vanilla}`
- Rot 원본: `results/campaigns/gain_attribution/main_validation/rot_gpu40_v1/{ours,vanilla}`
- Rot VRS/input/source provenance: `results/campaigns/gain_attribution/main_validation/rot_inputs/input_provenance.json`
- Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_main_validation.py` 및 `run_main_rot_validation.py`; rot경로adapter는 `main_validation_rot_adapter.py`.
- Main 인계 문서에도 결과와 작은 JSON artifact를 추가한다. 위 경로는 gs_floaterLab 기준이며 대용량 raw 결과는 Git 외부에 보존한다.
