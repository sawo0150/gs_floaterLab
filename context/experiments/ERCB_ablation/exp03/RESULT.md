# exp03 — RTX 5070 Ti exp77 budget interaction reproduction

날짜: 2026-09-15
상태: **28/28 완료; 저예산 이득과 full-budget 소멸 모두 재현**

## 질문

RTX 3070 Laptop에서 관측한 exp77의 핵심 결과, 즉 interval relative-floor ERCB가
작은 mapping budget에서는 causal RR보다 높지만 budget이 커지면 이득이 감소하거나
역전되는 현상을 RTX 5070 Ti에서 재현할 수 있는가?

## 사전 고정 계약

- 원본 코드: `3dgs-custom@da1dbda` + 보존된 exp77 patch
- 별도 worktree: `/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom-exp77-budget-5070ti-repro`
- 데이터: corrected `ercb_vigs_replay_v2`의 UTMM `square-1`, RPNG `table_01`
- 비교: causal RR vs exp75 interval relative-floor ERCB
  (`K=8`, `rho=.5`, `gamma=log(3)`)
- budget: keyframe arrival event당 `15/30/60` update
- seed: budget15/60은 `0/1/2`, budget30은 `0`
- 총 28 run; 각 pair는 동일 RGB, arrival, pose, init, update, LR horizon, 평가 frame 사용
- resolution 4, RGB loss, fixed topology(`densify_until_iter=0`), llffhold-8
- 마지막 arrival과 마지막 optimizer update가 같고 이후 update는 0(zero-tail)
- primary metric: final held-out PSNR의 paired `ERCB - RR`

절대 수치는 GPU뿐 아니라 PyTorch/CUDA가 달라질 수 있다. 재현 판정은 budget15의 두
장면 3-seed 평균 delta가 모두 양수인지, seed0에서 budget 증가에 따라 ERCB delta가
감소하는지, 그리고 full budget60의 3-seed 평균 이득이 저예산보다 작은지를 본다.
Budget30은 interaction 위치 확인용 seed0이며 일반화 근거로 사용하지 않는다.

## 결과

### 낮은 예산 15: 3-seed

최종 llffhold-8 held-out PSNR이다. Delta는 같은 seed의 `ERCB - RR`이다.

| Scene | Seed | RR | ERCB | Delta | exp77(3070) Delta |
|---|---:|---:|---:|---:|---:|
| UTMM square-1 | 0 | 16.4891 | 16.8022 | **+0.3131** | +0.4446 |
|  | 1 | 16.5055 | 16.7432 | **+0.2377** | +0.1308 |
|  | 2 | 16.5616 | 16.7894 | **+0.2279** | +0.1476 |
| **UTMM 평균** | — | — | — | **+0.2595 (3/3 승)** | **+0.2410** |
| RPNG table_01 | 0 | 22.0110 | 23.1977 | **+1.1867** | +1.1765 |
|  | 1 | 22.1339 | 23.1463 | **+1.0125** | +1.0080 |
|  | 2 | 22.1189 | 23.0093 | **+0.8904** | +0.8975 |
| **RPNG 평균** | — | — | — | **+1.0298 (3/3 승)** | **+1.0273** |

RPNG의 seed별 delta와 평균은 3070 결과와 `0.011dB` 이내다. UTMM은 seed별
수치가 달라졌지만 평균은 `+0.0185dB` 차이이고, 두 장면 모두 3/3 양수라는 핵심
결론을 재현했다.

### 예산 증가: seed0

| Scene | Update/event | RR | ERCB | Delta | exp77(3070) Delta |
|---|---:|---:|---:|---:|---:|
| UTMM | 15 | 16.4891 | 16.8022 | **+0.3131** | +0.4446 |
|  | 30 | 17.6099 | 17.7311 | **+0.1213** | +0.1345 |
|  | 60 | 18.8062 | 18.7581 | **-0.0481** | -0.0358 |
| RPNG | 15 | 22.0110 | 23.1977 | **+1.1867** | +1.1765 |
|  | 30 | 23.7296 | 23.7142 | **-0.0154** | -0.0229 |
|  | 60 | 24.0338 | 23.8268 | **-0.2069** | -0.1988 |

두 장면 모두 `15 > 30 > 60`으로 ERCB delta가 엄격히 감소했고, 큰 예산에서는
음수로 역전됐다. 따라서 **ERCB가 RR보다 유리한 것은 optimizer service가 부족한
저예산 영역이며, 예산이 충분하면 이득이 사라진다**는 exp77의 interaction을 5070 Ti에서
재현했다. Budget30은 원 실험처럼 seed0 하나뿐이므로 그 지점의 분산을 주장하지 않는다.

### Full budget 60: 3-seed 확장

사용자 요청에 따라 exp77의 seed0-only였던 full budget을 3 seeds로 확장했다.

| Scene | Seed | RR | ERCB | Delta |
|---|---:|---:|---:|---:|
| UTMM square-1 | 0 | 18.8062 | 18.7581 | -0.0481 |
|  | 1 | 18.6739 | 18.6730 | -0.0009 |
|  | 2 | 18.6185 | 18.6804 | +0.0620 |
| **UTMM 평균** | — | — | — | **+0.0043 (1/3 승)** |
| RPNG table_01 | 0 | 24.0338 | 23.8268 | -0.2069 |
|  | 1 | 23.8345 | 23.9085 | +0.0740 |
|  | 2 | 23.8887 | 23.8097 | -0.0789 |
| **RPNG 평균** | — | — | — | **-0.0706 (1/3 승)** |

UTMM은 평균 `+0.0043dB`로 실질적 동률, RPNG는 `-0.0706dB`로 소폭 음수다.
두 장면 모두 저예산 평균 `+0.2595/+1.0298dB`보다 크게 작다. 따라서 ERCB는
full budget에서 계속 누적 우위를 만드는 방식이 아니라, **부족한 update를 더 가치 있는
interval에 배분해 저예산 수렴을 앞당기는 방식**으로 해석하는 것이 맞다.

### 실행 계약 검증

- 28/28 run에서 요청 optimizer update 수와 실제 완료 수가 일치했다.
- 각 pair의 RGB membership, arrival schedule, pose/init, LR horizon, 평가 view가 같다.
- 마지막 arrival iteration이 마지막 update와 같아 EOS 뒤 optimizer update는 0이다.
- held-out view는 UTMM 202장, RPNG 314장이고 모든 PSNR이 유한하다.
- 저예산 seed0 zero-service도 RR/ERCB가 UTMM `398/567`, RPNG `269/501`로
  exp77과 정확히 같다. 즉 선택 sequence/service 통계가 같은 구현이다.
- 환경: RTX 5070 Ti, Python 3.9.25, PyTorch 2.8.0+cu128, CUDA runtime 12.8.

Machine-readable 결과는 [`evidence/summary.json`](evidence/summary.json), 전체 실행
계약과 argv는 [`evidence/manifest.json`](evidence/manifest.json)에 있다. 원본 run
artifact는 `results/ERCB_ablation/exp03_5070ti_budget_reproduction/`에 보존했다.

## 판정

**REPRODUCED.** 저예산 두 장면 평균 양수, 저예산 6/6 seed 승리, 두 장면 seed0
delta의 예산 증가별 단조 감소, full-budget 평균 이득의 저예산 대비 감소까지 네 gate를
모두 통과했다. 다만 이는
`relative_floor_interval_softmax_rr(K=8, rho=.5, gamma=log3)`의 고정 replay 결과다.
현재 unified VIGS의 original view-level ERCB나 exp01의 `rho=.75/gamma=log1.5`
bundle recipe와 혼동하지 않는다.

## 한계

이 실험은 fixed final VIGS pose와 누적 geometry initialization을 쓰는
scheduler-isolation replay다. 실제 strict VIGS, online pose, live wall-clock 또는
현재 unified KF+dense mapping loop의 성공으로 해석하지 않는다.

또한 fixed topology와 RGB-only 조건이라 Gaussian birth/prune 및 geometry loss와의
상호작용은 포함하지 않는다. GPU별 절대 처리량 비교가 아니라 동일 장비 안의 paired
quality-budget 관계를 검증한 실험이다.
