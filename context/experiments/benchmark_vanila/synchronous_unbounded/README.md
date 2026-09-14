# synchronous_unbounded — original VIGS-SLAM pure-online baseline

날짜: 2026-09-13
상태: **완료 (18/18)**

## 목적

공개 VIGS-SLAM `origin/main@22ffe24c`의 원래 tracking/mapping/loss를 사용해
로컬에 준비된 전체 benchmark와 두 Aria 장면의 영상 품질 기준선을 만든다.
최종 BA와 26k color refinement 같은 offline polish는 실행하지 않는다.

## 고정 계약

- code: `/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-vanilla-check`
- commit: `22ffe24c6df81d0bf63bd20057565c00c51d2996`
- 공통: `--gsmapping --pure_online`, synchronous/unbounded vanilla online map
- 종료 뒤 `VIGS_EVAL_PURE_ONLINE=1` 계측은 map/pose optimizer update 없이 렌더
  metric만 기록한다. 렌더용 full trajectory는 online keyframe trajectory를
  `PoseTrajectoryFiller`로 보간한다.
- standalone 영상 품질: evaluator가 남긴 `idx % 5 == 0 OR keyframe` union에서
  `is_keyframe=true`를 제거한 vanilla-only held-out PSNR/SSIM/LPIPS 산술평균
- 참고용으로 원본 evaluator union 평균도 함께 보존한다.
- random seed: upstream 실행 기본값(명시적으로 고정하지 않음), GPU: RTX 5070 Ti

결과 경로 suffix와 초기 run header의 `seed0`/`seed=0`은 관례상 붙은 잘못된
label이다. upstream `safe_state()`는 이 실행 경로에서 호출되지 않는다. provenance
보존을 위해 기존 raw 경로명은 바꾸지 않는다.

2026-09-13 재감사에서 worktree는 detached HEAD가 위 commit과 정확히 일치했다.
tracked diff는 (1) RTX 5070 Ti 빌드용 `<cstdint>` include 1줄, (2) pure-online 종료
뒤 optimizer update 없이 렌더 평가를 호출하는 6줄, (3) 기존 metric에 frame index와
keyframe 여부를 기록하는 14줄뿐이다. `config/rpng.yaml`, `config/utmm.yaml`과
tracking/frontend/PGBA/mapping/loss 코드는 HEAD 그대로다. TensorRT engine은 없어 원본
PyTorch fallback을 사용한다.

dataset adapter만 아래처럼 다르다.

| family | scenes | config / sensor options |
|---|---:|---|
| UTMM | 8 | `config/utmm.yaml`, `IMU_poseinit_after=15`, undistort, default buffer 1200 |
| RPNG | 8 | `config/rpng.yaml`, `IMU_poseinit_after=20`, undistort, official eval buffer 700 |
| Aria | 2 | original Aria calibration/config, config late-init 20, default buffer 1200 |

## 범위

- UTMM: `ego-centric-1`, `ego-centric-2`, `ego-drive`, `fast-straight`,
  `slow-straight-1`, `slow-straight-2`, `square-1`, `square-2`
- RPNG: `table_01`–`table_08` full sequence
- Aria: `aria1253`, `aria301_305`

동일 계약으로 이미 완료되어 per-view metric이 있는 exp81/82 결과는 provenance를
유지해 재사용한다. `ego-drive`의 과거 결과는 per-view 배열이 없어서 다시 실행한다.
RPNG `table_01` first-1000 결과는 exp83-R 진단으로만 보존하고 full-sequence 표에는
사용하지 않는다.

### 해석 주의

이 held-out은 논문이 정의한 “모든 비교 방법이 mapping에 쓰지 않은 공통 view”의
공개 고정 split이 아니다. Vanilla가 쓴 keyframe만 제외한 프로젝트용 stride-5
standalone 기준선이다. 논문 Table 18의 `table_01` PSNR은 final color refinement 전
23.41dB이며, 이 카드의 full-sequence 24.2268dB와는 split·공개 코드 시점·종료 처리가
같지 않아 직접 재현 오차로 계산하지 않는다. 향후 custom 비교 때는 두 방법의 mapping
view union을 모두 제외한 shared subset을 별도로 계산해야 한다.

또한 exp77의 RPNG “ERCB +1.027dB”는 fixed-final-pose/cumulative-init
3dgs-custom scheduler isolation에서 low-budget ERCB와 RR을 비교한 결과다. 실제 VIGS
custom 대 original vanilla 비교가 아니며, 이 카드의 절대값과 섞지 않는다.

## 결과

장면별 결과와 논문 before-refinement 참고값은 [`summary.md`](summary.md),
machine-readable 값은 `evidence/summary.csv`, `evidence/summary.json`에 기록했다.
raw 신규 실행은 `results/benchmarks/benchmark_vanila/synchronous_unbounded/`에 있다.

## 재현 도구

- `run_one.sh FAMILY SCENE [OUTPUT_DIR]`: 단일 장면 실행
- `run_missing.sh`: 기존 유효 결과를 재사용하고 빠진 장면만 GPU 순차 실행
- `collect_metrics.py`: keyframe 제외 held-out 및 union metric 집계
