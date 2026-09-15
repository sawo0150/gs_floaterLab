# exp03-F — reliable-keyframe ERCB low-budget pilot

날짜: 2026-09-15  
판정: **NO-GO — 두 장면 모두 RR보다 낮아 seed 확장 중단**

## 질문과 계약

exp03-E의 dense-role ERCB 실패가 보간 dense pose의 낮은 신뢰도 때문인지 보기 위해,
동일한 unified B1 mapping loop에서 ERCB를 tracked keyframe 역할 안에만 적용했다.
Dense 역할은 RR로 유지했다. `K=8`, `rho=.5`, `gamma=log(3)`, native online
topology, fixed 1.5x sensor budget, zero-tail은 그대로이며 장면별 숫자 튜닝은 없다.

사전 gate는 RPNG table_07 q3와 UTMM square-1 q15 seed0이 모두 양수일 때만
seed1/2로 확장하는 것이었다.

## 결과 (primary: mapping-excluded fixed held-out)

| Scene / budget | RR PSNR | KF-ERCB PSNR | ERCB-RR | RR/ERCB Adam | KF/dense | topology | final GS RR/ERCB |
|---|---:|---:|---:|---:|---:|---:|---:|
| RPNG table_07 q3 | 22.8164 | 21.5779 | **-1.2385** | 612/612 | 306/306 | 2/2 | 499,521/480,353 |
| UTMM square-1 q15 | 19.1389 | 19.0651 | **-0.0738** | 1009/1009 | 433/576 | 3/3 | 152,351/152,167 |

RPNG SSIM은 `.75746→.72523`, LPIPS는 `.34123→.38452`로 둘 다 악화했다.
UTMM도 SSIM `.63439→.63361`, LPIPS `.50394→.50401`로 동률 내 음수다.
네 run 모두 sensor EOS 뒤 optimizer/topology update가 0임을 감사했다.

## 해석

- 신뢰 가능한 keyframe에 coverage를 옮겨도 저예산 PSNR 이득은 나타나지 않았다.
  따라서 exp03-E 실패를 dense pose noise 하나로 설명할 수 없다.
- UTMM에서는 keyframe under-4 후보가 `14→10`으로 줄었지만 PSNR은
  `-0.0738dB`였다. 즉 service fairness 자체는 학습 한계이득이 아니다.
- RPNG에서는 keyframe 최대 반복이 `9→6`으로 줄었지만 under-4는 오히려
  `92→104`, 최종 Gaussian은 3.84% 감소했다. 선택한 keyframe이 densification
  통계와 pending birth 시점을 함께 소유하므로, scheduler 순서가 native topology에
  강하게 되먹임된 결과다.
- 역할별 RNG는 분리돼 있지만 strict end-to-end에서는 optimizer 실행 시점의 causal
  가용 집합이 scheduler/runtime feedback으로 달라질 수 있다. 그래서 dense RR의 최종
  service histogram도 완전히 같지는 않았다. 이는 “KF ordering만 고정적으로 바뀐
  scheduler-isolation pair”로 해석하면 안 되며, 실제 폐루프 시스템 비교로만 유효하다.

사전 gate가 0/2로 실패했으므로 seed1/2와 K/rho/q sweep은 실행하지 않는다.
현재 production selector는 RR을 유지한다. 다음 ERCB 축을 계속 본다면 coverage-only가
아니라, 이미 계산한 loss에서 얻는 causal marginal utility와 service deficit을 결합하고
native topology feedback을 별도 계측해야 한다.

## 재현

- VIGS: `a3c04e43`
- 실행: `run_pilot.sh`
- raw output: `results/ERCB_ablation/exp03-F_keyframe_role/`
- CPU selector contract test: `12 passed`
