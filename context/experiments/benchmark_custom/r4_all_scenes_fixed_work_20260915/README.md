# exp78 R4 all-local-scene fixed-work B-track

날짜: 2026-09-15
상태: **완료 — 사용자 지시에 따라 이 결과에서 tuning/run loop 중단**

## 결론

고정한 R4 Full과 native vanilla VIGS mapper를 local RPNG 8개, UTMM 8개,
Aria 2개에 적용했다. 계획한 18개 중 tracker가 metric initialization에 도달하지
못한 UTMM `slow-straight-1`을 제외한 **17개 pair가 모두 10/10 fairness verifier를
통과했고, 17/17에서 R4의 held-out PSNR이 높았다.**

- 유효 scene 산술평균: R4 **22.2592**, vanilla **20.9983**, delta **+1.2609 dB**
- view-weighted delta(보조 지표): **+1.4903 dB**
- scene-mean SSIM delta: **+0.04125**
- scene-mean LPIPS delta: **-0.04619**(낮을수록 좋음)
- 사용자와 합의한 prospective all-scene 기준인 평균 `>= +0.5 dB`, strict
  majority positive, 모든 pair fairness PASS를 충족한다.

이 결과는 **B-track mapping-only fixed-work 결과**다. `time_scale=unbounded`이므로
C-track strict live-time 통과나 27 dB milestone 달성을 의미하지 않는다. Aria의
절대 PSNR도 25.7274/25.1420 dB로 아직 27 dB 미만이다.

## 집계

Scene 수가 긴 RPNG에 결과가 종속되지 않도록 primary는 scene arithmetic mean이고,
view-weighted mean은 보조로만 기록한다.

| dataset | 계획 | 유효 | R4 승리 | R4 PSNR mean | vanilla PSNR mean | delta PSNR | delta SSIM | delta LPIPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RPNG | 8 | 8 | 8/8 | 24.0945 | 22.4954 | **+1.5991** | +0.05940 | -0.06411 |
| UTMM | 8 | 7 | 7/7 | 19.2545 | 18.7135 | **+0.5411** | +0.01827 | -0.00784 |
| Aria | 2 | 2 | 2/2 | 25.4347 | 23.0073 | **+2.4274** | +0.04907 | -0.10873 |
| 전체 | 18 | 17 | 17/17 | 22.2592 | 20.9983 | **+1.2609** | +0.04125 | -0.04619 |

## Scene별 결과

PSNR/SSIM은 높을수록, LPIPS는 낮을수록 좋다. `renders`는 각 arm이 소비한
동일한 physical training render 수다.

| dataset | scene | role | views | R4 PSNR | vanilla PSNR | ΔPSNR | ΔSSIM | ΔLPIPS | renders | verifier |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RPNG | `table_01` | development | 502 | 25.6243 | 23.9294 | **+1.6949** | +0.0548 | -0.0458 | 38,302 | 10/10 |
| RPNG | `table_02` | previously exposed | 584 | 23.2957 | 21.1408 | **+2.1548** | +0.0876 | -0.0632 | 53,669 | 10/10 |
| RPNG | `table_03` | confirmation | 1,402 | 23.5045 | 21.8338 | **+1.6707** | +0.0783 | -0.0793 | 85,029 | 10/10 |
| RPNG | `table_04` | confirmation | 1,215 | 22.3651 | 21.2403 | **+1.1248** | +0.0455 | -0.0439 | 67,793 | 10/10 |
| RPNG | `table_05` | confirmation | 1,234 | 22.7780 | 21.7007 | **+1.0773** | +0.0421 | -0.0553 | 52,480 | 10/10 |
| RPNG | `table_06` | development | 555 | 24.4876 | 22.7171 | **+1.7705** | +0.0666 | -0.0823 | 34,437 | 10/10 |
| RPNG | `table_07` | confirmation | 958 | 26.8400 | 25.3018 | **+1.5382** | +0.0453 | -0.0515 | 33,422 | 10/10 |
| RPNG | `table_08` | confirmation | 1,698 | 23.8604 | 22.0988 | **+1.7616** | +0.0550 | -0.0914 | 94,283 | 10/10 |
| UTMM | `ego-centric-1` | confirmation | 308 | 17.7558 | 17.2178 | **+0.5380** | +0.0367 | -0.0010 | 5,676 | 10/10 |
| UTMM | `ego-centric-2` | confirmation | 261 | 19.4944 | 19.2419 | **+0.2525** | +0.0168 | +0.0055 | 6,655 | 10/10 |
| UTMM | `ego-drive` | development | 281 | 21.2489 | 20.5567 | **+0.6922** | +0.0282 | -0.0322 | 11,226 | 10/10 |
| UTMM | `fast-straight` | confirmation | 68 | 16.3792 | 16.0215 | **+0.3577** | +0.0017 | -0.0027 | 1,348 | 10/10 |
| UTMM | `slow-straight-1` | confirmation | 80 | N/A | N/A | N/A | N/A | N/A | N/A | tracker-ineligible |
| UTMM | `slow-straight-2` | confirmation | 121 | 17.2476 | 17.0858 | **+0.1618** | -0.0064 | +0.0171 | 1,888 | 10/10 |
| UTMM | `square-1` | confirmation | 324 | 21.2397 | 20.2063 | **+1.0334** | +0.0350 | -0.0292 | 9,345 | 10/10 |
| UTMM | `square-2` | development | 245 | 21.4160 | 20.6642 | **+0.7518** | +0.0159 | -0.0123 | 8,277 | 10/10 |
| Aria | `aria1253` | development | 262 | 25.7274 | 24.0403 | **+1.6872** | +0.0433 | -0.0835 | 13,620 | 10/10 |
| Aria | `aria301_305` | transfer | 539 | 25.1420 | 21.9743 | **+3.1677** | +0.0548 | -0.1340 | 17,620 | 10/10 |

`slow-straight-1`의 tracker archive는 393프레임에서 final keyframe 12개와
keyframe-update event 3개를 만들었지만 IMU initialization 및 metric-rescale event는
0이었다. 공통 `mapping-after-metric-init` gate 아래 두 mapper 모두 map을 만들 수 없으므로
실패 PSNR로 임의 치환하지 않고 N/A로 남겼다.

## 고정 비교 계약

- 같은 official VIGS tracker seed-0 frozen archive를 양 mapper가 재생한다.
- tracker packet, pose correction, tracking keyframe UID, mapping service trace가 같다.
- R4가 실제 commit한 총 physical training render 수에 vanilla의 native mapper를
  맞춘다. Vanilla에 dense update 경로를 새로 넣지 않는다.
- 평가 뷰는 사전에 고정한 `zero-based idx % 5 == 0 OR final`이며 mapper의
  supervision/birth에서 제외한다. Tracker가 평가 RGB를 보는 것은 허용하되 양 arm이 같다.
- 마지막 packet 뒤 optimizer update 0회, final BA/color refinement/background polish 0회다.
- 평가 pose fill은 EOS 이후 별도 evaluation-only artifact이며 mapping에 들어가지 않는다.
- hard carve는 사용하지 않았다(`carve_lambda=0`).
- 모든 유효 pair가 exact render, same archive/KF/service, mapping-disjoint,
  zero-tail을 포함한 verifier 10/10을 통과했다.

R4 Full은 다음 고정 묶음이다.

- D1 native frontier와 별도 causal dense appearance update
- causal online-rank PPM birth(mean 2.5, span 2, base 256/64)
- 관측 기반 unknown-horizon topology gate
- eligible packet당 dense C1 service 1회와 별도 keyframe appearance service 1회
- global-residue C2 ERCB 및 native historical BALANCED/REPLAY keyframe ERCB
- `dense_rr_imu`, PGBA pose refresh, zero-tail

Scene 이름, 절대 frame/iteration, stream fraction, Gaussian-count cutoff,
topology freeze를 recipe에 넣지 않았다.

## 원래 X4 gate와의 관계

결과를 보고 X4의 사전 기준을 바꾸지 않았다. 원래 confirmation X4는 11개 계획 중
10개가 유효했고 `slow-straight-1`이 N/A였다. 유효 10개 평균은 **+0.951601 dB**,
RPNG confirmation 5개 평균은 **+1.434527 dB**, UTMM confirmation 5개 평균은
**+0.468676 dB**다. 따라서 당시의 `모든 11개 valid` 및 family `>= +0.9 dB`
조건은 그대로 실패/HOLD다.

이번 PASS는 그 기준을 사후 변경한 것이 아니라, 사용자가 이후 정한 전체 local-scene
판정인 **유효 scene 평균 +0.5 dB 이상 + strict majority positive + fairness valid**를
prospective하게 적용한 결과다.

## 과적합 감사

- 최종 선택 뒤 열린 confirmation 10개는 모두 양수이고 평균 **+0.9516 dB**다.
  다만 UTMM confirmation만 보면 평균 +0.4687 dB라 RPNG보다 이득이 작다.
- Aria 개발 scene `aria1253`은 +1.6872 dB이고 별도 transfer `aria301_305`는
  +3.1677 dB다. 적어도 Aria1253에만 맞춘 density 동작으로 transfer 이득을
  설명하기는 어렵다.
- R4 runtime은 YAML에 과거 Aria fitted curve 경로가 남은 RPNG/UTMM에서도
  backend 생성 전에 `exp78b://causal-online-rank`로 덮어쓴다. 새 Aria custom
  config에는 fitted curve 경로 자체를 넣지 않았다.
- Aria tracker의 `motion_filter.thresh=3.6`은 이번 결과를 보고 선택하지 않고
  exp66에서 이미 사용한 dataset-level operational adapter다. 그러나 upstream paper의
  공식 Aria benchmark 설정은 아니므로 **dataset adaptation 가능성은 공개해야 한다.**
  같은 frozen tracker를 두 mapper가 써 B-track mapper 비교는 유지되지만, 이 결과를
  official VIGS 논문의 Aria 숫자 복원으로 부르면 안 된다.
- `table_01`, `table_06`, `ego-drive`, `square-2`, `aria1253`은 development,
  `table_02`는 previously exposed로 표시했다. 전체 평균을 untouched-only
  generalization 평균으로 표현하지 않는다.
- mapper seed 0 한 번뿐이다. Seed variance와 독립적인 외부 dataset은 후속 검증 사항이다.

보조 지표에서는 UTMM `ego-centric-2`의 LPIPS와 `slow-straight-2`의 SSIM/LPIPS가
악화했다. 따라서 모든 scene에서 모든 metric이 개선됐다고 주장하지 않는다.

## 범위 밖 / 다음 마일스톤

- B-track은 mapping algorithm을 같은 work로 격리한 비교다. Tracking과 mapping이
  실제 GPU에서 경쟁하는 C-track strict live-time 증거는 아니다.
- Aria held-out 27 dB는 아직 미달이고, 마지막 프레임까지 1.5x deadline을 지킨
  strict pass/drop/lag도 이 카드에서는 판정하지 않는다.
- Region-GT/floater metric을 실행하지 않았으므로 geometry/floater 개선 주장도 하지 않는다.
- 사용자 지시에 따라 이 all-scene 결과 뒤에는 추가 tuning, seed loop, scene rerun을
  시작하지 않았다.

## Artifact와 재생성

- 정규화 전체 행: [`summary.csv`](summary.csv)
- 기계 판독 결과와 acceptance: [`summary.json`](summary.json)
- 각 verifier/source manifest SHA와 raw run: [`provenance.json`](provenance.json)
- 집계기: [`build_summary.py`](build_summary.py)
- RPNG/UTMM raw confirmation:
  [`stage6rx4_cross_sequence_confirmation`](../../../../results/experiments/exp78/paper_full_staged_v1/stage6rx4_cross_sequence_confirmation)
- 추가 RPNG/UTMM 및 Aria raw:
  [`stage6r_all_scenes_fixed_work`](../../../../results/experiments/exp78/paper_full_staged_v1/stage6r_all_scenes_fixed_work)
- 재사용한 `table_01` raw:
  [`stage6r_r4_native_global_keyframe`](../../../../results/experiments/exp78/paper_full_staged_v1/stage6r_r4_native_global_keyframe)

집계 재생성:

```bash
python context/experiments/benchmark_custom/r4_all_scenes_fixed_work_20260915/build_summary.py
```

실행 source commit은 RPNG/UTMM 확장 `d9a5dc9`, Aria `a883104`, paper mapper
`07a09aa7`, official vanilla `22ffe24`다. 세부 파일 SHA는 `provenance.json`에 있다.
