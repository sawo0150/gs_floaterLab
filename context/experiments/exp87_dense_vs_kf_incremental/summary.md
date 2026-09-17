# exp87 — incremental KF-only vs KF+dense supervision

상태: **FINISHED_6_COMPLETE_0_FAILED_OF_6**

## 질문

배치 학습에서 관측된 "dense supervision이 keyframe-only보다 빠르게 수렴한다"(exp66,
aria1253, 26k iteration에서 31.68 vs 28.38dB)를 **causal/incremental 도착 조건에서도**
관측할 수 있는가.

## 계약

두 arm이 공유: dataset, init point cloud, causal arrival schedule, `causal_rr` selector,
seed, 해상도 `-r 4`, RGB-only loss, 표준 3DGS densification(500–15,000, interval 100),
총 optimizer update 수, 그리고 두 arm 모두 한 번도 학습하지 않는 llffhold-8 held-out.
**다른 것은 후보 pool 하나뿐**이다 — `kf_only`는 VIGS keyframe만, `dense_all`은 도착한
모든 train frame.

benchmark-A/B와 달리 `--fixed_topology_step_before_report` / `--densify_until_iter 0`을
쓰지 않는다. 즉 dense view가 필요한 Gaussian을 실제로 만들 수 있다(exp66이 배치에서
"dense frame에 keyframe과 동일한 geometry 편집 권한"을 줬을 때의 조건).

## 결과 — held-out PSNR(dB) vs optimizer update

| scene | arm | pool | @1k | @3k | @7k | @15k | @25k | final | final GS |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| aria/aria1253 | KF-only | 115 | 13.77 | 16.25 | 19.24 | 23.05 | 28.04 | 29.21 | 361554 |
| aria/aria1253 | KF+dense | 1140 | 13.74 | 16.77 | 19.94 | 24.79 | 30.45 | 31.55 | 384474 |
| aria/aria1253 | **Δ (dense−KF)** | | -0.03 | +0.52 | +0.70 | +1.74 | +2.41 | +2.34 | |
| utmm/square-1 | KF-only | 72 | 12.48 | 12.41 | 12.19 | 15.74 | 20.27 | 21.50 | 945645 |
| utmm/square-1 | KF+dense | 1412 | 13.01 | 13.63 | 12.96 | 18.55 | 23.50 | 24.88 | 814060 |
| utmm/square-1 | **Δ (dense−KF)** | | +0.53 | +1.22 | +0.77 | +2.81 | +3.23 | +3.38 | |
| rpng/table_01 | KF-only | 212 | 16.30 | 19.24 | 22.86 | 23.76 | 23.70 | 23.83 | 412098 |
| rpng/table_01 | KF+dense | 2192 | 16.68 | 19.37 | 23.30 | 24.29 | 24.08 | 24.34 | 416402 |
| rpng/table_01 | **Δ (dense−KF)** | | +0.39 | +0.12 | +0.44 | +0.53 | +0.38 | +0.52 | |

## Scene-unweighted 평균 Δ(dense − KF-only)

| @1k | @3k | @7k | @15k | @25k | final |
|---:|---:|---:|---:|---:|---:|
| +0.29 (2/3) | +0.62 (3/3) | +0.64 (3/3) | +1.69 (3/3) | +2.01 (3/3) | +2.08 (3/3) |

## 수렴 속도 — "같은 iteration 수에서 더 빨리 수렴한다"의 직접 근거

KF-only가 **전체 예산을 다 쓰고** 도달한 품질에, KF+dense는 몇 번의 update만에 도달하는가.

| scene | KF-only final | KF-only updates | KF+dense updates to match | speed-up | KF+dense final |
|---|---:|---:|---:|---:|---:|
| aria/aria1253 | 29.21 | 30,013 | 21,171 | **1.42×** | 31.55 |
| utmm/square-1 | 21.50 | 30,021 | 19,571 | **1.53×** | 24.88 |
| rpng/table_01 | 23.83 | 29,885 | 10,132 | **2.95×** | 24.34 |

## 해석 제한

- densification이 켜져 있으므로 두 arm의 최종 Gaussian 수가 다르다. 위 표에 최종
  Gaussian 수를 함께 싣는다. "dense가 단지 Gaussian을 더 많이 만들어서 이긴 것"이라는
  반론을 배제하려면 capacity-matched 후속 통제가 필요하다.
- pose와 init은 사전 VIGS run을 고정 replay한 것이므로 strict online localization
  결과가 아니다. 도착 순서(causality)와 zero-tail은 유지된다.
- held-out은 llffhold-8이라 held-out frame이 dense train frame과 시간적으로 인접한다.
  이 인접성은 dense arm에 유리하게 작용할 수 있으며 두 arm 모두 동일 held-out을 쓴다.
