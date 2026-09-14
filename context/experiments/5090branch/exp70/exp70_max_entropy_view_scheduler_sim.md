# exp70 — Maximum-Entropy Growing-Pool View Scheduler Simulation

## 질문

exp69 v7의 global maturity gate를 제거했을 때도, 무한히 성장하는 causal view pool에서
다음 두 조건을 함께 만족하는 scheduler가 있는가?

1. 선택 gradient의 누적·짧은-window 분포가 uniform full-pool gradient에서 크게
   벗어나지 않는다.
2. 각 view가 자신의 arrival age에 맞는 uniform 학습 기회를 받는다.

## 실험 계약

- 실제 VIGS-SLAM 학습이 아닌 scheduler-only 합성 시뮬레이션이다.
- 12,000 optimizer update, 48 scheduler seeds
- static/steady/bursty/accelerating/near-saturation 5개 pool 패턴
- IID/trajectory-correlated/regime-shift/time-modulated 4개 synthetic gradient field
- 비교: IID uniform, production causal shuffle 모사, exp69 active/archive
  (D=0,1,2), raw least-count, ME-QARR, ME-BDS (C=2,3,4)
- 공정성 목표:

  \[
  q_i(T)=\sum_{t=a_i}^{T}\frac1{N_t},
  \qquad e_i(T)=n_i(T)-q_i(T).
  \]

## 결과

| Scheduler | quota RMSE ↓ | worst max \(|n-q|\) ↓ | final gradient RMSE ↓ | 256-step mixing RMSE ↓ |
|---|---:|---:|---:|---:|
| IID uniform | 3.764 | 31.333 | 0.771% | 5.144% |
| production causal shuffle | 0.609 | 3.509 | 3.174% | 9.239% |
| exp69 active/archive, (D=1) | 3.473 | 46.125 | 4.841% | 11.314% |
| raw least-count | 7.427 | 43.667 | 30.505% | 58.168% |
| **ME-QARR, (C=1)** | **0.306** | **0.875** | **0.324%** | 5.831% |
| **ME-BDS, (C=2)** | 0.392 | 1.875 | 0.330% | 5.300% |

- 50개 평가 case의 평균 rank는 ME-QARR 2.56으로 1위, ME-BDS (C=2) 2.96으로
  2위였다.
- ME-QARR는 임의 growing pool에서 \(\max_i|n_i-q_i|<1\)을 보장하며, 고정 pool에서는
  모든 (N!)개 순열에 균등한 exact random reshuffling이다.
- ME-BDS는 다음 선택 뒤 tag-span이 (C) 이내인 모든 feasible view에서 균등 추출한다.
  따라서 deterministic discrepancy cap 아래 one-step conditional Shannon entropy가
  최대다.
- (C=2)는 ME-QARR의 burst 직후 short-window mixing 약화를 줄여 IID uniform과 거의
  같은 평균 mixing을 보이면서 최악 exposure 오차를 2회 미만으로 제한했다.
- near-saturation에서 모든 view를 두 번 보는 것은 계산량상 불가능했다:
  6,031 view × 2 = 12,062 > 12,000 update. Scheduler는 부족한 compute를 만들 수 없고,
  age-adjusted quota에 맞게 배분할 수 있을 뿐이다.

## 판정

**분석 단계 채택.** 논문용 기본 설계는 ME-BDS((C=2)), 강한 이론적 특수형과 ablation은
ME-QARR((C=1))로 둔다. Global maturity gate와 raw lifetime count는 제거 후보로 본다.

단, 이 판정은 scheduler exposure와 synthetic gradient에만 해당한다. 실제 3DGS
PSNR/geometry/floater 개선은 주장하지 않으며, production VIGS-SLAM 코드는 아직 수정하지
않았다. 다음 검증은 동일 admitted set, optimizer update 수, Gaussian budget을 고정한
current v7 / ME-QARR / ME-BDS((C=2))의 세 장면 이상 A/B다.

## 산출물

- [전체 수식·결과 보고서](../../research/view_scheduler_long_horizon_sim_report.md)
- [재현 시뮬레이터](../../research/view_scheduler_long_horizon_sim.py)
- [원자료 및 그림](../../research/view_scheduler_long_horizon_outputs/)

