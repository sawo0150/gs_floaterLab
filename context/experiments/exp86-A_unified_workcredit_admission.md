# exp86-A — unified-pool work-credit admission

날짜: 2026-09-14
상태: **짧은 장면 pilot 완료; `r=4` 전이 후보, 최종 채택 전**

> 명칭 정정: 이 카드에서 `ERCB`라고 줄여 쓴 arm은 original view-count ERCB가
> 아니라 **interval relative-floor**다. Original `exp(-beta*n_i)` ERCB와의 직접
> 비교는 [exp86-B](exp86-B_workcredit_selector_families.md)에 기록한다.

## 질문

하나의 KF+dense mapping loop에서 dense pool membership도 고정 stride가 아니라
완료된 GPU work로 열고, RR/ERCB는 같은 pool 위의 selector로만 비교할 수 있는가?

## 코드 감사와 수정

- 기존 matched-time RR/ERCB 주 결과는 work-credit가 아니었다. dense membership은
  `stride=5`, interval당 최대 1장이었다.
- 기존 `--mapping_work_credit_admission`은 backend가 완료한 mature dense update를
  credit로 사용하지만, frontend polling 사이에 쌓인 과거 surplus를 한 번에 여러
  admission으로 바꿀 수 있었다.
- unified 경로만 `global bootstrap 1장 → pool 전체 r회 이상 → paid 1장 → 실제 GS
  registration 확인 → 새 pool 전체 r회 이상`의 cycle로 제한했다. Final-v7 legacy
  동작과 RR/ERCB score는 바꾸지 않았다.
- 절대 frame/iteration/stream fraction/topology freeze는 사용하지 않았다.

## 실험 계약

- scene: UTMM `fast-straight`, matched vanilla map-done budget 30.905821s
- physical batch 1, single unified KF+dense loop, background polish 0, zero-tail
- dense: IMU rotation bridge, RGB appearance+opacity update
- 평가: vanilla와 공통인 non-keyframe 61장 held-out PSNR

## 결과

| admission / selector | physical Adam | KF / dense update | active dense pool | dense min / p10 | PSNR delta vs vanilla |
|---|---:|---:|---:|---:|---:|
| fixed arrival / RR | 611 | 259 / 352 | telemetry 이전 run | - | +0.215843 |
| fixed arrival / interval relative-floor | 673 | 277 / 396 | telemetry 이전 run | - | **+0.323652** |
| old work-credit r4 / RR | 615 | 420 / 195 | 11 | 1 / 1.0 | +0.201476 |
| old work-credit r4 / interval relative-floor | 578 | 381 / 197 | 12 | 2 / 6.0 | +0.209007 |
| cycle work-credit r4 / RR | 612 | 426 / 186 | 10 | 0 / 3.6 | +0.205783 |
| cycle work-credit r4 / interval relative-floor | 610 | 405 / 205 | 11 | 0 / 4.0 | **+0.224825** |
| cycle work-credit r2 / RR | 646 | 349 / 297 | 14 | 9 / 12.6 | +0.090926 |
| cycle work-credit r2 / interval relative-floor | 634 | 347 / 287 | 14 | 8 / 11.9 | +0.098665 |

모든 신규 run은 matched budget/counter/zero-tail 계약을 통과했다. Cycle r4의 0회
view는 stream 끝에 마지막으로 등록되어 stable active set에 들어오기 전 종료된 한
장이다. Unknown horizon에서 자연스러운 terminal debt이며, phase cutoff로 숨기지 않는다.

## 판정

- work-credit admission 방향은 유지한다.
- `r=2`는 더 많은 dense update/pool에도 PSNR이 내려가 기각한다.
- 현재 전이 후보는 `r=4 + ERCB`다. 다만 짧은 장면에서는 fixed-arrival ERCB보다
  0.098827dB 낮으므로 최종 채택은 긴 대표 장면 무재튜닝 전이 뒤 결정한다.
- 마지막 cohort의 낮은 service 자체는 실패가 아니다. ERCB의 역할은 admission 후
  주어진 pool에서 그 debt를 우선 상환하는 것이고, admission은 pool 성장률만 정한다.

## 증거

- 집계: `benchmark_custom/5070ti_vanilla_matched_time/evidence/summary.json`
- raw: `results/benchmarks/benchmark_custom/5070ti_vanilla_matched_time/utmm/fast-straight/`
- runner: `benchmark_custom/5070ti_vanilla_matched_time/run_one.sh`
