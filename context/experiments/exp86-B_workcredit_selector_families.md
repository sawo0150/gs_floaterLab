# exp86-B — work-credit admission 위 selector family 비교

날짜: 2026-09-14
상태: **2-scene pilot 완료; original ERCB의 count 보정은 유효하지만 RR 대체 NO-GO**

## 질문

동일한 single KF+dense mapping loop와 cycle work-credit admission(`r=4`) 위에서
다음 scheduler를 공정하게 비교하면 무엇이 빠르게 수렴하는가?

1. view RR
2. view uniform statistical block, `K=128, beta=0`
3. original view-count ERCB, `exp(-beta*n_i)`, `beta=0.02`
4. interval population base / relative-floor / coverage1

`K=128`이 growing pool에 느리다는 가설은 UTMM `ego-centric-1`에서 original
ERCB의 `K=32/8`도 추가해 확인했다. Admission, loss, physical B1, seed, matched-time
budget은 고정했으며 selector가 maturity 도달 시점과 다음 admission을 바꾸는 것은
의도한 closed-loop 비교에 포함한다.

## 계약

- UTMM `fast-straight`: vanilla map-done matched budget 30.905821s, 공통 non-KF 61장
- UTMM `ego-centric-1`: matched budget 91.405114s, 공통 non-KF 297장
- single unified KF+dense loop, physical batch 1, background polish 0
- KF RGBD+normal+native topology, dense RGB appearance+opacity
- cycle work-credit `r=4`, fixed seed 0, no phase/frame/fraction/topology cutoff
- 모든 유효 run: matched budget/counter/zero-tail 통과

## 결과

### Held-out PSNR

| selector | fast PSNR / delta | ego-centric PSNR / delta | original-vs-RR |
|---|---:|---:|---:|
| RR | 17.6317 / +0.2058 | **19.7320 / +2.5641** | 기준 |
| view uniform K128 | 17.8132 / +0.3873 | 19.1895 / +2.0216 | +0.1815 / -0.5424 |
| **original ERCB K128, beta=.02** | **17.8506 / +0.4247** | 19.5074 / +2.3396 | **+0.2189 / -0.2245** |
| interval base | 17.7321 / +0.3062 | - | +0.1004 / - |
| interval relative-floor | 17.6508 / +0.2248 | 19.3168 / +2.1489 | +0.0190 / -0.4152 |
| interval coverage1 | 17.8005 / +0.3745 | 19.2421 / +2.0742 | +0.1688 / -0.4898 |

Original ERCB와 RR의 scene별 delta 평균 차이는 `-0.0028dB`로 사실상 동률이나,
부호가 장면마다 반대여서 production 교체 근거는 아니다. 반면 같은 K128에서
`beta=0 -> .02`의 순효과는 fast `+0.0374dB`, ego-centric `+0.3179dB`로 2/2
양수다. 따라서 count 보정 신호 자체는 유효하고, 문제는 K128 block과 growing-pool
상호작용이다.

### K 감소 진단 (`ego-centric-1`, beta=.02)

| K | PSNR | RR 대비 | Adam | KF/dense | dense pool | count CV | dense min/p10 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 128 | 19.5074 | -0.2245 | 3894 | 2890/1004 | 22 | 0.4886 | 3/11.4 |
| 32 | 18.4489 | -1.2831 | 4069 | 2829/1240 | 27 | 0.4092 | 1/12.8 |
| 8 | 18.8705 | -0.8615 | 4023 | 2559/1464 | 34 | **0.3908** | 3/12.3 |

K를 낮추면 lifetime count는 더 균등하고 dense pool/service는 늘지만 held-out PSNR은
악화했다. K32는 RR보다 Adam step도 많으므로 계산량 부족으로 설명할 수 없다.
K8에서는 topology event가 RR 19회에서 17회로 바뀌었다. 더 공격적인 fairness와
admission이 KF full/topology service를 바꿔 수렴 경로를 흔드는 closed-loop tradeoff다.

## 판정

- **original ERCB 구현은 유지:** 고정 K에서 `beta=.02` count 보정은 2/2 양수다.
- **K128 production 교체 NO-GO:** fast에서는 승리하지만 ego-centric에서는 RR보다
  0.2245dB 낮다.
- **K32/K8 기각:** fairness 향상이 PSNR 향상을 뜻하지 않는다. 추가 K 숫자 sweep을
  중단한다.
- **interval family production 교체 NO-GO:** 짧은 장면 이득이 ego-centric에서
  0.42--0.49dB 손실로 전이됐다.
- 현재 두 장면에서 가장 안전한 selector는 RR이다. 다음 구조 단계는 K 튜닝이 아니라
  admission maturity가 dense service만 보고도 KF topology 기회를 과도하게 치환하지
  않도록 service 계약을 분리 계측하는 것이다.

## 구현 및 증거

- runner: `benchmark_custom/5070ti_vanilla_matched_time/run_one.sh`
- panel: `benchmark_custom/5070ti_vanilla_matched_time/run_selector_family_pilot.sh`
- 집계: `benchmark_custom/5070ti_vanilla_matched_time/evidence/summary.json`
- raw: `results/benchmarks/benchmark_custom/5070ti_vanilla_matched_time/utmm/{fast-straight,ego-centric-1}/`
- 상대 output path 즉시실패 1건은 학습 전 실패이며 `.failed_relative_path_20260914`로
  보존했다. Runner는 이후 output을 절대경로로 정규화한다.
