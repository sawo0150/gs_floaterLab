# ERCB ablation — RPNG-AR / UTMM external transfer

> 날짜: 2026-09-11  
> 범위: 새 exp 번호를 만들지 않는 ERCB 전용 누적 트랙  
> 판정: **대표 2-scene fixed-pose/init transfer에서 count/lower-tail은 개선했지만 overall PSNR은 재현 실패.**

## 질문

exp75의 `relative_floor_interval_softmax_rr(K=8, rho=.5, gamma=log3)`와
exp76의 threshold-free `normalized_interval_size_softmax_rr(K=8,
gamma=log1.25)`를 외부 RPNG-AR/UTMM 데이터에도 같은 zero-tail 계약으로 적용했을 때,
causal RR보다 held-out 품질이 좋아지는가?

## 실험 계약

| 항목 | RPNG-AR | UTMM |
|---|---|---|
| 대표 구간 | `table_01` 처음 1,000 RGB | `square-1` 처음 1,000 RGB |
| train / held-out | 875 / 125 | 875 / 125 |
| split | 정렬된 전체 frame의 index `% 8 == 0`을 held-out | 동일 |
| causal interval | 연속 RGB 8장 | 동일 |
| update/event | 60 | 60 |
| 마지막 arrival / 총 update | 7,441 / 7,441 | 7,441 / 7,441 |
| post-arrival update | 0 (zero-tail) | 0 (zero-tail) |
| 해상도 | 3DGS `-r 4` | 동일 |
| seed | 0, 1 | 0, 1 |

세 arm은 다음과 같다.

1. `causal_rr`
2. `normalized_interval_size_softmax_rr(K=8, gamma=log1.25)` (exp76)
3. `relative_floor_interval_softmax_rr(K=8, rho=.5, gamma=log3)` (exp75)

모든 arm은 같은 COLMAP text camera model과 같은 초기 point scaffold를 읽는다.
RPNG 이미지는 고정 calibration으로 undistort했고, UTMM은 MM3DGS와 같은 camera-optical
rotation을 적용했다.

## Gaussian initialization

이번 첫 외부 transfer는 scheduler 효과를 빠르게 분리하기 위한 offline harness다.

- ground-truth pose를 고정한다.
- held-out을 제외한 매 16번째 train frame에서 24-pixel grid ray를 만든다.
- RPNG는 depth `{0.75, 1.5, 3, 5}m`의 176,400 colored points,
  UTMM은 `{2, 5, 10, 20}m`의 360,612 colored points로 시작한다.
- 모든 arm/seed가 동일한 point set을 공유한다.

중요한 한계가 있다. 전체 1,000-frame train slice의 미래 RGB ray를 initialization에
사용했으므로 **strict-causal RGB+IMU 결과가 아니다.** RPNG GT는 이 1차 harness에서
camera/IMU extrinsic을 별도 합성하지 않고 camera pose로 근사했다. 또한 UTMM의 제공
depth나 VIGS/COLMAP map seed를 사용하지 않았다. 따라서 절대 PSNR과 외부 transfer 실패를
strict 시스템의 최종 결론으로 확대해석하면 안 된다.

## 결과

표의 PSNR, worst-Q1, RR-hard-Q1, late는 두 seed 평균이다. Delta는 같은 seed의
causal RR 대비 candidate 차이이다.

| Scene | Scheduler | PSNR | Delta | worst-Q1 Delta | RR-hard-Q1 Delta | late Delta | count CV |
|---|---|---:|---:|---:|---:|---:|---:|
| RPNG table01-1000 | causal RR | 26.7416 | — | — | — | — | .9247 |
|  | normalized | 26.6613 | **-.0803** | +.3194 | +.9616 | -.1304 | **.8516** |
|  | relative-floor | 26.6058 | **-.1358** | **+.4411** | +.8107 | **+.4283** | .8610 |
| UTMM square1-1000 | causal RR | 24.8525 | — | — | — | — | .9247 |
|  | normalized | 24.7923 | **-.0602** | **+.1882** | **+.3124** | -.2506 | **.8516** |
|  | relative-floor | 24.7773 | **-.0752** | +.0599 | +.1471 | -.3902 | .8610 |

개별 held-out PSNR은 다음과 같다.

| Scene | seed | RR | normalized | Delta | relative-floor | Delta |
|---|---:|---:|---:|---:|---:|---:|
| RPNG | 0 | 26.7487 | 26.6876 | -.0610 | 26.6159 | -.1327 |
| RPNG | 1 | 26.7345 | 26.6349 | -.0996 | 26.5956 | -.1388 |
| UTMM | 0 | 25.0642 | 24.7128 | -.3514 | 24.7404 | -.3239 |
| UTMM | 1 | 24.6408 | 24.8718 | +.2311 | 24.8143 | +.1735 |

두 scene×두 seed를 동일 가중하면 normalized는 overall `-.0702dB`(1/4 승),
relative-floor는 `-.1055dB`(1/4 승)다. 반면 worst-Q1은 각각 `+.2538/+.2505dB`,
RR-hard-Q1은 `+.6370/+.4789dB`다. Count CV도 RR `.9247`에서 `.8516/.8610`으로
일관되게 줄었다. 최종 Gaussian 수는 RR 대비 normalized/relative-floor가 RPNG에서
약 `+1.2%/+3.7%`, UTMM에서 `+3.8%/+3.6%`여서 topology 경로가 포함된 end-to-end
scheduler 효과다.

## 판정

- **overall held-out PSNR transfer: NO-GO.** exp75의 기존 305/12F/3F 6/6 양수 결과는
  이 RPNG/UTMM representative harness에서 재현되지 않았다.
- **fairness/lower-tail: 재현.** 두 candidate 모두 count CV와 두 lower-tail 지표를
  평균적으로 개선했다. RPNG relative-floor는 late도 `+.4283dB` 개선했다.
- 현재 두 장면 모두 27dB 미만이므로 프로젝트 원칙대로 carve/pruning을 붙이지 않는다.
- 다음 유효 검증은 artificial ray scaffold가 아니라 dataset-native depth(UTMM)와
  VIGS/COLMAP 또는 causal point admission(RPNG)을 사용해 initialization 축을 분리하는 것이다.

## 재현 및 evidence

- 3dgs-custom GitHub main: `db035da`
- dataset builder: `scripts/incremental/build_benchmark_causal_dataset.py`
- runner: `scripts/incremental/run_ercb_benchmark_ablation.sh`
- summarizer: `scripts/incremental/summarize_ercb_benchmark.py`
- compact result: [`evidence/representative_1000_summary.json`](evidence/representative_1000_summary.json)
- full run artifacts (fastMRI only):
  `/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/context/experiments/ERCB_ablation/evidence/runs/`
