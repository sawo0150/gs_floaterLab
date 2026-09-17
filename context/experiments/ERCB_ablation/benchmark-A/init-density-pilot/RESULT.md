# benchmark-A initialization-density pilot result

## 판정

**두 장면·두 scheduler의 4/4 pair에서 stride20 dense initialization이 held-out
PSNR을 높였다.** RR 장면 평균은 **+0.8480dB**,
ERCB 장면 평균은 **+0.7345dB**다.
따라서 sparse fixed initialization이 benchmark-A의 낮은 절대 PSNR에 기여한다는 가설은
pilot gate를 통과했다. 다만 2장면·seed0 fixed replay 결과이므로 전체 benchmark나 strict
VIGS end-to-end의 일반 결론은 아니다.

## 통제

- 한 번의 strict VIGS source run에서 동일 BA-refined depth/pose를 stride40과 stride20으로
  동시에 export했다. 복제·jitter·다른 run point cloud는 쓰지 않았다.
- RGB, camera, full trajectory, keyframe boundary, causal arrival schedule, Adam update 수,
  seed, RGB-only loss, fixed topology, llffhold-8 held-out evaluator가 pair별로 동일하다.
- 저예산은 event당 15 update이며 optimizer tail은 0이다. 모든 run의 최종 평가는 마지막
  update 뒤 기록됐고 manifest는 8/8 complete, 0 failed다.

| scene | stride40 points | stride20 points | density |
|---|---:|---:|---:|
| utmm/square-1 | 8,554 | 31,185 | 3.646× |
| rpng/table_01 | 25,762 | 100,157 | 3.888× |

## Held-out PSNR와 비용

| scene | scheduler | stride40 | stride20 | dense Δ | train GPU ratio | wall ratio |
|---|---|---:|---:|---:|---:|---:|
| utmm/square-1 | rr | 16.1907 | 17.6182 | +1.4275 | 1.167× | 1.010× |
| utmm/square-1 | ercb | 16.8367 | 17.7581 | +0.9215 | 1.176× | 1.024× |
| rpng/table_01 | rr | 21.3951 | 21.6636 | +0.2685 | 1.695× | 1.218× |
| rpng/table_01 | ercb | 22.1870 | 22.7345 | +0.5474 | 1.693× | 1.219× |

Gaussian topology는 고정돼 최종 Gaussian 수가 초기점 수와 같다. Dense init의 비용은
square-1에서 training GPU time **1.17×**, table_01에서 **1.69–1.71×**였다. Wall time은
각각 약 **1.01–1.02×**, **1.22×**다. 따라서 이는 같은 update 수에서의 품질 개선이지,
같은 wall-time budget에서 공짜로 얻은 개선은 아니다.

## ERCB 상호작용

| scene | density | ERCB − RR |
|---|---|---:|
| utmm/square-1 | stride40 | +0.6459 |
| utmm/square-1 | stride20 | +0.1399 |
| rpng/table_01 | stride40 | +0.7919 |
| rpng/table_01 | stride20 | +1.0708 |

초기점을 촘촘히 해도 ERCB의 저예산 이득은 4/4 조건에서 양수다. 다만 square-1에서는
ERCB 이득이 +0.6459→+0.1399dB로 줄고 table_01에서는 +0.7919→+1.0708dB로 늘어,
단 두 장면만으로 일관된 interaction을 주장할 수 없다.

## 다음 판정

**GO는 “조금 더 넓게 검증할 가치가 있다”는 뜻이다.** 바로 production 설정으로 채택하지
않는다. 다음 최소 실험은 같은 paired exporter를 몇 개 추가 장면에 적용하고, fixed-update와
matched-wall-time을 함께 보고 dense init이 실제 strict mapping budget에서도 이득인지
확인하는 것이다. 전체 13-scene sweep나 density knob 장면별 튜닝은 아직 하지 않는다.
