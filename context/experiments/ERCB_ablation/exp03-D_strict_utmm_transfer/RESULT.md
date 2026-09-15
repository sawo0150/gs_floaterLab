# exp03-D — strict VIGS ERCB UTMM ego-centric transfer

날짜: 2026-09-15
상태: **완료 — compute-matched pair에서 ERCB -0.3306dB, 전이 실패**

## 질문

`exp03-B`의 causal fixed-arrival strict 1.5x 계약을 숫자 변경 없이 UTMM
`ego-centric-1`에 전이했을 때 ERCB의 저예산 이득이 관측되는가?

## 고정 계약

- unified B1, causal fixed-arrival stride5/offset2/max1
- RR vs relative-floor ERCB K8/rho.5/gamma=log3
- online tracking/native topology, KF RGBD+normal, dense appearance+opacity
- fixed 1.5x sensor budget, fixed held-out mapping 제외, zero-tail
- 장면별 phase/topology cutoff와 background polish 없음

seed 0 pair를 gate로 사용한다. 양수일 때만 반복 seed를 검토하며 숫자 튜닝은 하지 않는다.

## 결과

고정 evaluator 308장의 held-out 결과다.

| Selector | fixed PSNR | fixed SSIM | fixed LPIPS | Adam | KF/dense update | late-cohort mean | topology |
|---|---:|---:|---:|---:|---:|---:|---:|
| RR | 18.8776 | 0.66224 | 0.42858 | 2447 | 903 / 1544 | 10.89 | 6 |
| relative-floor ERCB | 18.5470 | 0.64918 | 0.45125 | 2438 | 887 / 1551 | 13.95 | 6 |
| ERCB - RR | **-0.3306** | -0.01306 | +0.02267 | -9 | -16 / +7 | +3.05 | 0 |

두 arm의 membership은 KF 42장+dense 76장으로 동일하고 Adam은 9회(0.37%) 차이,
topology event도 6회로 같다. ERCB는 late-cohort service를 높였지만 PSNR/SSIM/LPIPS가
모두 악화했다. 두 run 모두 deadline/EOS 뒤 update 0이다.

## 판정

**전이 실패.** 이 pair는 `exp03-B`보다 compute/topology가 잘 맞아, 단순 처리량 차이로
패배를 설명하기 어렵다. Coverage/count fairness가 마지막 view의 starvation은 줄이지만
이미 충분히 서비스된 장면에서는 더 높은 학습 잔여량을 가진 view에서 update를 빼앗을 수
있다는 증거다. K나 rho를 장면별로 튜닝하지 않는다. 다음 구현 축은 ERCB를 무조건
production selector로 교체하는 것이 아니라, measured service scarcity가 있을 때만
coverage term을 활성화하고 residual/learning-progress utility와 결합하는 것이다.

원본 artifact는
`results/ERCB_ablation/exp03-D_strict_utmm_transfer/utmm/ego-centric-1/1p5x/`에 보존한다.
