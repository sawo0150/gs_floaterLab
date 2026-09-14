# 5070ti_1.5x_streaming — original VIGS execution baseline

날짜: 2026-09-14
상태: **완료 (16/16)**

## 계약

- GPU: RTX 5070 Ti
- code: original VIGS-SLAM `origin/main@22ffe24c`
- 입력: source RGB timestamp 간격을 1.5배로 재생
- frame ingress: queue size 8, full이면 producer가 기다려 모든 frame을 보존
- 실행: 원본 `Training.parallel` GS worker, queue size 2
- unchanged: tracking, frontend, PGBA, Gaussian mapping iteration/loss/topology
- disabled: final global BA, final color refinement
- 평가: 종료 뒤 map optimizer 없이 trajectory interpolation + PSNR/SSIM/LPIPS
- random seed: upstream 실행 기본값(명시적으로 고정하지 않음)

기존 결과 디렉터리 suffix의 `seed0`와 초기 run header의 `seed=0`은 관례상 붙은
잘못된 label이다. upstream `safe_state()`는 이 실행 경로에서 호출되지 않으므로
실제로 고정 seed를 보장하지 않는다. raw 결과는 provenance 보존을 위해 이름을 바꾸지 않는다.

`parallel=true`만 dataset config overlay로 켠다. 원본 worker는 queue가 찼을 때
가장 오래된 pending GS packet을 버리지만, 이미 시작한 map packet 내부 iteration은
중단하지 않는다. 마지막 packet 뒤 pending worker를 drain하며,
`stream_contract.json`에 producer/tracking timing과 map tail/drain 시간을 각각 남긴다.
map tail은 실시간성 진단값이지 품질 결과의 실패 조건은 아니다. 이 결과는
`1.5x paced streaming + bounded queue + bounded final drain` baseline이며,
`strict_zero_tail_proven=false`인 한 North Star의 strict zero-tail 성과로 부르지 않는다.

frame ingress는 drop하지 않고 backpressure를 허용한다. 따라서 `track @1.5x=LATE`인
장면은 1.5x timestamp를 목표로 시작했지만 실제 재생 wall-clock이 늘어난 경우다.
품질 baseline으로는 보존하되 literal 1.5x throughput 성공으로 해석하지 않는다.

첫 `fast-straight` pilot은 upstream async worker와 IMU map reset 사이의 lock 누락으로
실패했다. 원본 `rescale()`이 이미 쓰는 Gaussian lock을 같은 lifecycle reset에도
적용하고, Torch Queue producer lifetime 및 worker exception propagation만 adapter에서
보완했다. 실패 출력은 `_failed_pilot_race_20260914`,
`_failed_pilot_interrupt_20260914` suffix로 보존한다.

## 범위

- UTMM 8 scenes
- RPNG `table_01`–`table_08` full sequence

## 결과

16/16 장면이 final PLY, trajectory, per-view PSNR/SSIM/LPIPS 및 stream timing을
남기고 완료됐다. 장면별 비가중 평균은 다음과 같다.

| family | scenes | PSNR | synchronous/unbounded 대비 | SSIM | LPIPS |
|---|---:|---:|---:|---:|---:|
| UTMM | 8 | 19.1263 | -0.0862 dB | 0.65048 | 0.42119 |
| RPNG | 8 | 22.4195 | -0.0512 dB | 0.74358 | 0.24333 |
| 전체 | 16 | 20.7729 | -0.0687 dB | 0.69703 | 0.33226 |

최종 mapper drain은 평균 1.32초, 최대 5.46초로 작았다. 반면 모든 frame을 보존하는
ingress backpressure 때문에 16/16 모두 tracking 종료가 literal 1.5x deadline보다
늦었다(평균 252.43초, 최댓값 974.05초). 따라서 품질은 synchronous 결과와 거의
같았지만, 이 결과 자체가 fixed-wall-clock 실시간 처리율을 입증하지는 않는다.

장면별 값은 [`summary.md`](summary.md), machine-readable 결과는
[`evidence/summary.csv`](evidence/summary.csv)와
[`evidence/summary.json`](evidence/summary.json)에 있다.

## 파일

- `streaming_demo.py`: 외부 timestamp producer와 lifecycle/계측
- `config/*_parallel.yaml`: upstream config를 상속하고 parallel mode만 활성화
- `run_one.sh FAMILY SCENE`: 단일 장면
- `run_all.sh`: 16개 장면 직렬/resume-safe 실행
- `collect_metrics.py`: 실행 결과 + 논문 Table 18/19 참고값 집계
