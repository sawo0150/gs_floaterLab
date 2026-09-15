# ERCB ablation — UTMM bundle tuning, latency reformulation, and transfer

> 날짜: 2026-09-15
> 범위: ERCB 전용 누적 트랙
> 최신 판정: **GT pose+exact frontend packet+shared packet-driven topology까지 통제해도 UTMM/RPNG fixed ERCB−RR은 +0.0614/−0.0614dB로 평균 0이었다. 과거 fixed replay 이득은 현재 VIGS의 dynamic singleton dense admission과 heterogeneous KF/dense loss로 전이되지 않는다. Production selector는 RR을 유지한다.**

## 최신 결과 — exp03-H frozen frontend + topology

RR/ERCB가 같은 mapper packet과 stable-ID topology 결정을 사용하도록 진단 trace를
구현했다. UTMM 70 packet/3 event, RPNG 204/1을 exact replay했고 final GS도 pair별로
동일했다. Fixed held-out delta는 `+0.0614/-0.0614dB`로 이득이 복구되지 않았다.
상세 결과는 [`exp03-H/RESULT.md`](exp03-H_frozen_frontend_topology/RESULT.md)에 있다.

## 이전 결과 — exp03-G frozen tracking pose

GT pose만 고정했을 때 RPNG/UTMM 3-seed 평균은 `+0.2546/+0.0588dB`로 모두 양수였다.
그러나 native topology가 arm마다 달랐으므로 H에서 추가 통제했다. 상세 결과는
[`exp03-G/RESULT.md`](exp03-G_frozen_tracking_pose/RESULT.md)에 있다.

## 최신 결과 — exp03-F reliable-keyframe role pilot

보간 pose가 불확실한 dense 대신 tracked keyframe 안에서만 같은 interval ERCB를
적용했다. RPNG table_07 q3 exact-step pair는 `-1.2385dB`, UTMM square-1 q15는
`-0.0738dB`로 0/2였다. RPNG는 같은 Adam/KF-dense/topology event 수에도 최종 GS가
499,521→480,353으로 달라져, selected KF가 densification 통계를 소유하는 native
topology feedback도 확인됐다. 사전 gate에 따라 추가 seed와 숫자 sweep은 중단했다.
상세 결과는 [`exp03-F/RESULT.md`](exp03-F_keyframe_role/RESULT.md)에 있다.

## 최신 결과 — exp03-E strict end-to-end packet budget

Causal mapping packet마다 physical Adam credit을 해제하고, KF/dense 역할을 두 arm에서
맞춘 뒤 dense 내부 RR/ERCB 순서만 비교했다. UTMM square-1 q15 3-seed delta는
`-0.1005/+0.0720/+0.0107dB`(평균 `-0.0059dB`)였고, RPNG table_07 q3의
Adam612/612·KF/dense306/306 exact-service pair는 `-0.7943dB`였다. ERCB는 late dense
service를 개선했지만 held-out PSNR 수렴 가속으로 이어지지 않았다. 상세 결과는
[`exp03-E/RESULT.md`](exp03-E_packet_budget_interaction/RESULT.md)에 있다.

## 이전 결과 — exp03 RTX 5070 Ti fixed-replay budget reproduction

Corrected full VIGS replay의 UTMM `square-1`과 RPNG `table_01`에서 causal RR과
`relative_floor_interval_softmax_rr(K=8,rho=.5,gamma=log3)`를 비교했다. 동일
pose/init/RGB/arrival/update/LR horizon, fixed topology, llffhold-8, zero-tail 계약이다.

| Budget (updates/event) | UTMM ERCB−RR | RPNG ERCB−RR | Seeds |
|---:|---:|---:|---:|
| 15 | **+0.2595dB** | **+1.0298dB** | 3 |
| 30 | +0.1213dB | −0.0154dB | 1 |
| 60 | **+0.0043dB** | **−0.0706dB** | 3 |

총 28/28 run의 update/arrival/held-out 계약을 검증했다. 이는 scheduler-isolation
replay이며 strict online VIGS 성과는 아니다. 상세 결과는
[`exp03/RESULT.md`](exp03/RESULT.md), compact evidence는
[`exp03/evidence/summary.json`](exp03/evidence/summary.json)에 있다.

## 최신 결과 — exp02 service-latency 재정식화

연구 폴더의 7개 방법론을 전부 구현하여 `slow-straight-2`와 `ego-drive`에서
1차 선별하고, 파라미터를 `ego-drive`에서 조정한 뒤 Debt–Utility A와 Service
Field만 6-scene에 고정 transfer했다. Latency 시작은 물리 RGB 촬영 시각,
완료는 실제 optimizer update 적용 시각이며 EOS 이후 update는 0이다.

최종 6-scene held-out PSNR은 RR 19.025dB, Debt A 18.548dB(−.477), Service
Field 18.471dB(−.555)였고 각각 1/6, 2/6 scene에서만 이겼다. 반면 처리용량이
충분한 4개 scene의 p95 latency는 RR 25.988초에서 Debt 18.526초, Service Field
18.540초로 줄었다. 따라서 신규 frame direct-service latency는 제어할 수 있지만
그것이 최종 품질의 주 병목이라는 강한 가설은 기각한다. 구현 결함으로 ticket
quota를 지키지 않은 Prefix의 일시적 +0.056dB 결과는 무효로 분리했다.

상세 계약·전 방법 결과·수정 이력은 [`exp02/RESULT.md`](exp02/RESULT.md),
machine summary는 [`exp02/evidence/final_v3_summary.json`](exp02/evidence/final_v3_summary.json)에 있다.

## 최신 결과 — UTMM bundle-wide module ablation

논문용 binary module ablation은 UTMM 묶음 하나를 validation set으로 정하고, 장면별로
다른 값을 쓰지 않고 bundle-wide 파라미터 하나를 선택했다. Tracking gate를 통과한 6개
시퀀스에서 seed 0으로 grid search한 뒤 선택값을 고정하여 seed 1, 2를 추가 검증했다.

- 선택값: `K=8`, `rho=0.75`, `gamma=log(1.5)`
- 비교: causal RR vs 동일 시스템의 ERCB on/off
- 계약: llffhold-8, 60 updates/keyframe event, sensor-EOS 도착, zero-tail,
  동일 pose/init/update budget
- 규모: 6 scenes × 3 seeds = 18 paired comparisons

| Metric | RR | ERCB | Paired delta |
|---|---:|---:|---:|
| held-out PSNR | 21.9148 | **21.9845** | **+0.0698dB** |
| worst-Q1 PSNR | 17.9054 | **18.0117** | **+0.1062dB** |
| RR-hard-Q1 PSNR | — | — | **+0.3321dB** |
| selection-count CV | **0.8030** | 0.9389 | +0.1359 |

PSNR은 18쌍 중 11쌍에서 이겼고 seed별 6-scene 평균 delta도
`+0.1343/+0.0484/+0.0265dB`로 모두 양수였다. 반면 `fast-straight`는
3 seed 평균 `-0.2957dB`, `square-1`은 `-0.0200dB`였고 selection-count CV도
악화했다. 따라서 논문에서 허용되는 결론은 **“UTMM validation ablation에서 ERCB가
평균 및 RR-hard frame 품질을 소폭 개선했다”**까지다. 보편적 우월성, 통계적 유의성,
global count equalization은 주장하지 않는다.

이 실험은 exp80의 final-online VIGS pose와 누적 geometry initialization을 arm 사이에
고정한 scheduler-isolation ablation이다. View arrival과 EOS는 인과적이지만 pose/init는
strict online localization 근거가 아니다. 또한 같은 UTMM bundle에서 튜닝하고 평가했으므로
독립 test-set generalization 결과로 중복 사용하지 않는다. 상세 protocol과 scene별 결과는
[`exp01/UTMM_TUNING_PROTOCOL.md`](exp01/UTMM_TUNING_PROTOCOL.md), compact evidence는
[`exp01/evidence/utmm_tuning_v1_compact.json`](exp01/evidence/utmm_tuning_v1_compact.json)에 있다.

## 이전 진단 — RPNG-AR / UTMM representative transfer

아래 결과는 dataset-native VIGS initialization을 쓰기 전, 기존 파라미터를 대표 2개
slice에 그대로 옮긴 선행 진단이다. 최신 UTMM bundle-tuned 결과와 섞어 평균하지 않는다.

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

- 3dgs-custom GitHub main: `8568fd6`
- dataset builder: `scripts/incremental/build_benchmark_causal_dataset.py`
- VIGS replay builder: `scripts/incremental/build_vigs_benchmark_causal_dataset.py`
- runner: `scripts/incremental/run_ercb_benchmark_ablation.sh`
- summarizer: `scripts/incremental/summarize_ercb_benchmark.py`
- corrected VIGS replay 재개 지점: [`exp01/HANDOFF_5070TI.md`](exp01/HANDOFF_5070TI.md)
- compact result: [`exp01/evidence/representative_1000_summary.json`](exp01/evidence/representative_1000_summary.json)
- full run artifacts (fastMRI only):
  `/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/context/experiments/ERCB_ablation/evidence/runs/`
