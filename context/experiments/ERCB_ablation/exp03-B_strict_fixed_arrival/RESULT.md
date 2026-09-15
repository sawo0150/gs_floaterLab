# exp03-B — strict VIGS fixed-arrival ERCB selector isolation

날짜: 2026-09-15
상태: **완료 — 3-seed 평균 동률, topology/service feedback로 부호 불안정**

## 질문

strict VIGS 1.5x에서 dense admission을 selector의 과거 service와 분리해 동일하게
고정하면, relative-floor ERCB의 저예산 이득이 RR 대비 실제로 관측되는가?

## 고정 계약

- `exp03-A`와 같은 single unified KF+dense loop, physical B1, online pose/topology
- fixed replay scale `1.5`, sensor EOS zero-tail, fixed held-out mapping 제외
- causal interval arrival: dense stride 5, offset 2, interval당 최대 1장
- KF RGBD+normal+full topology, dense RGB appearance+opacity
- RR vs interval relative-floor ERCB(`K=8`, `rho=.5`, `gamma=log3`)
- background polish/final BA/color refinement/topology freeze/phase cutoff 없음
- primary: 동일 scene/seed의 fixed held-out `ERCB - RR`
- audit: Adam 수, KF/dense update, candidate membership, topology event도 함께 비교

첫 pair는 UTMM `square-1`, seed 0이다. 첫 pair가 양수이고 membership이 동일해
seed 1/2까지 확장했다.

## 결과

고정 evaluator 324장의 held-out 결과다.

| Seed | RR PSNR | ERCB PSNR | Delta | RR/ERCB Adam | RR/ERCB dense update | RR/ERCB late-cohort mean |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 19.8751 | 20.2169 | **+0.3418** | 4067 / 3906 | 2497 / 2380 | 3.54 / 5.64 |
| 1 | 20.3422 | 19.6924 | **-0.6498** | 3839 / 3249 | 2339 / 1973 | 3.18 / 3.93 |
| 2 | 19.8982 | 20.1976 | **+0.2994** | 2320 / 3242 | 1381 / 1998 | 1.71 / 5.04 |
| **평균** | **20.0385** | **20.0356** | **-0.0029** | — | — | — |

- 3/3 pair 모두 keyframe 71장+dense 112장으로 membership은 같다.
- ERCB는 모든 seed에서 마지막 dense cohort 평균 service를 높였다.
- 하지만 strict wall-clock 안의 실제 Adam 수는 selector/topology feedback 때문에 pair별
  `-161/-590/+922`회로 크게 달랐고 PSNR도 2승1패, 평균 동률이었다.
- fixed SSIM/LPIPS는 seed 0/2에서 ERCB가 동시 개선했지만 seed 1에서는 동시 악화했다.
- 6/6 run 모두 deadline/EOS 뒤 update 0이다.

## 판정

**UTMM strict end-to-end의 일관된 ERCB 우위는 아직 재현되지 않았다.** ERCB가 late
cohort starvation을 줄이는 선택 동작 자체는 3/3 확인됐지만, 그 선택이 native topology와
per-step 비용을 바꾸며 남은 Adam service까지 변화시킨다. 따라서 fixed replay의 저예산
우위를 그대로 strict 최종 성능 우위로 옮길 수 없다. K sweep은 하지 않고 `exp03-C`에서
같은 고정 계약을 RPNG에 무재튜닝 전이한다.

원본 artifact는
`results/ERCB_ablation/exp03-B_strict_fixed_arrival/utmm/square-1/1p5x/`에 보존한다.
