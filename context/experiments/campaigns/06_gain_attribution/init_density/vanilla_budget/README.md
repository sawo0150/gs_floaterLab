# 바닐라 개수 수준 비교 — PPM 유지 (2026-09-27)

사용자 요청: “그냥 대충 … init 개수만 맞춰주고 … ppm 그대로 방식은 바꾸지 않는 방향”. 바닐라의 sampling 공식으로 바꾸려던 준비안은 실행하지 않고 폐기했다. **현재 PPM, Sobel weights, causal content-adaptive 생성량 배분과 나머지 초기화 방식은 유지하고, 생성량 배율만 조정한다.**

- 기존 공식 40회 예산 비교의 최종 Gaussian 수를 근사 목표로 사용한다: Aria 190,533 / RPNG 234,218 / UTMM 162,663.
- 현재 기본 개수 192,623 / 357,071 / 141,545에 대해 downsample denominator 배율 1.01 / 1.52 / 0.87을 각각 적용한다. 첫 지도와 이후 모든 KF birth에 같은 상수를 적용한다. 목표의 ±1% 내인지 확인하며, UTMM은 바닐라 개수가 더 많아 소폭 증가하는 조건이다.
- ERVS, κ=16, τ₀=4, 3:3:6, dense RGB, 영상별 Adam을 유지한다. 15/40 renders/KF × 세 장면 = 6회. 비교 기준은 이번 init_density의 fresh `b15_d1`, `b40_d1`이다.
- Densify/prune/Carve/blur OFF, scale projection ON. Held-out 분할, causal 입력, zero-tail 계약이 동일하다. 절대 시점 freeze, 강제 prune, 최종 개수 cap은 사용하지 않는다.
- 장면별 상수는 사용자가 요청한 개수 대조군을 위해 기존 바닐라 결과에서 사전 지정했다. 배포 정책이나 장면 공통 튜닝 결과로 채택하지 않는다. 학습에 미래 pose/depth 또는 held-out 이미지를 넣지 않는다.
- 공식 원본은 init 1/32, regular 1/64의 uniform sampling을 쓴다. **이 방식 자체를 이식하지 않는다.** 바닐라의 최종 개수에는 densify/prune 영향도 있으므로, 원본과 초기 생성량 자체를 동일하게 맞춘 실험이라고 주장하지 않는다. 요청대로 대략적인 지도 개수 수준만 맞춘다.

## 실행 기록

**2026-09-27 init density budget15 b15_vanilla_count / aria:** execution=True, audit=True, PSNR=23.243475120486195, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/vanilla_count_gpu15_40_v1/b15_vanilla_count/aria.

**2026-09-27 init density budget15 b15_vanilla_count / rpng:** execution=True, audit=True, PSNR=23.915152496475358, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/vanilla_count_gpu15_40_v1/b15_vanilla_count/rpng.

**2026-09-27 init density budget15 b15_vanilla_count / utmm:** execution=True, audit=True, PSNR=20.996181264335725, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/vanilla_count_gpu15_40_v1/b15_vanilla_count/utmm.

**2026-09-27 init density budget40 b40_vanilla_count / aria:** execution=True, audit=True, PSNR=25.876509426204304, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/vanilla_count_gpu15_40_v1/b40_vanilla_count/aria.

## 2026-09-27 — 범위 확대 중단, 완료된 비교만 보고

사용자가 성능 향상 탐색이 아닌 단순 비교를 요청했음을 재차 명확히 했다. 절반/1/4 등으로 실험을 과도하게 확장한 것을 인정하고 실행 중인 추가 실험을 중단했다. 바닐라 개수 근사 조건은 15회 세 장면과 40회 Aria만 완료했으며, 40회 RPNG는 중단, UTMM은 미실행이다. 미완료 결과를 성능 값으로 사용하지 않는다. 추가 튜닝·preset 변경은 하지 않는다.

| 예산 | 장면 | 기존 PSNR | 개수 근사 PSNR | ΔPSNR | 최종 Gaussian 수 |
|---:|---|---:|---:|---:|---:|
| 15 | aria | 23.255 | 23.243 | -0.011 | 190,787 |
| 15 | rpng | 24.024 | 23.915 | -0.109 | 235,025 |
| 15 | utmm | 20.874 | 20.996 | +0.122 | 162,697 |
| 40 | aria | 25.911 | 25.877 | -0.034 | 190,787 |

PPM과 학습 구조를 유지하고 생성량 배율만 바꿨다. 완료된 4개 실행의 held-out 평가와 동일 work/선택 감사는 통과했다. 바닐라의 **최종 개수 수준**을 근사한 대조군이지 바닐라 구현으로 교체한 결과는 아니다. 단일 seed, causal tracker replay 결과다. 실행 중단 기록: `results/campaigns/gain_attribution/init_density/vanilla_count_gpu15_40_v1/stop_record.json`.

## 2026-09-27 — 사용자 정정: 공통 파라미터가 비교 대상

사용자는 장면별 개수 동등화를 요청한 것이 아니라, PPM을 유지하면서 모든 장면에 적용할 하나의 생성량 파라미터를 원했다. 따라서 앞의 Aria/RPNG/UTMM별 1.01/1.52/0.87 배율은 요청 해석 오류로 기록하며 공통 설정 후보로 채택하지 않는다. 추가 실행은 하지 않는다.

또한 앞선 목표 개수는 vanilla **40 renders/KF**의 최종 개수였다. 15회 vanilla의 실제 최종 개수는 Aria 263186 / RPNG 198630 / UTMM 177634로 다르므로, 앞의 15회 장면별 배율 조건도 동일 예산 vanilla의 개수 동등 실험으로 부르면 안 된다. 기존 실행 수치는 보존하되 이 해석 정정을 우선한다.

하나의 후보로 downsample denominator 공통 배율 1.25(init64→80, regular256→320; 생성량 약20% 감소)를 제안할 수 있다. 이는 아직 미측정이며 성능 최적값으로 주장하거나 preset에 채택하지 않는다. 이미 측정한 공통 배율2는 세 장면 모두에 동일하게 적용됐으나 일부 장면 품질 하락이 컸다.
