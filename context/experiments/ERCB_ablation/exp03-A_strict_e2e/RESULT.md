# exp03-A — strict VIGS end-to-end ERCB budget interaction

날짜: 2026-09-15
상태: **완료 — strict 1.5x에서 work-credit admission과 selector가 결합됨을 확인**

## 질문

Fixed-pose/init replay에서 재현한 ERCB의 저예산 이득이 online tracking, causal
KF+dense admission, native topology가 모두 작동하는 strict VIGS에서도 관측되는가?

## 고정 계약

- single unified KF+dense mapping loop, physical B1
- KF RGBD+normal+full topology, dense RGB appearance+opacity
- causal IMU rotation-bridge pose, cycle work-credit admission `r=4`
- RR와 interval relative-floor ERCB(`K=8`, `rho=.5`, `gamma=log3`)만 비교
- timestamp RGB+IMU only, fixed replay scale, mapping evaluator frame 제외
- background polish/final BA/color refinement/topology freeze/phase cutoff 없음
- sensor deadline 이후 optimizer/topology update 0
- primary: 같은 scene/scale/seed의 fixed held-out `ERCB - RR`

## Stage A

먼저 UTMM `fast-straight`에서 fixed `1.5x` strict pair를 실행했다. 이는 기존
matched-time scale `2.7996x`보다 mapping wall time이 46% 적은 실제 service-starved
조건이다. 그러나 IMU/map initialization이 stream 후반에 끝나 RR/ERCB가 각각
Adam `1/3`회, dense `0/0`회만 수행했다. PSNR `6.93/9.86dB` 차이는 scheduler
선택이 아니라 우연한 2-step service 차이이므로 ERCB 근거에서 제외한다. 두 run 모두
zero-tail은 통과했으며 실패 진단으로 보존한다.

다음은 같은 fixed `1.5x`에서 stream이 더 긴 UTMM `square-1` pair다.

## 결과

`fast-straight/1.5x`는 비교 불능이다. `square-1/1.5x`, seed 0 결과는 다음과 같다.

| Selector | fixed held-out PSNR | Adam | KF update | dense update | dense pool | topology event |
|---|---:|---:|---:|---:|---:|---:|
| RR | 20.3953 | 3817 | 2856 | 961 | 23 | 19 |
| relative-floor ERCB | 20.3085 | 3830 | 2675 | 1155 | 32 | 18 |
| ERCB - RR | **-0.0868** | +13 | -181 | +194 | +9 | -1 |

두 run 모두 sensor deadline과 EOS 뒤 Adam/topology update가 0이어서 zero-tail 계약은
통과했다. 그러나 ERCB 이득은 관측되지 않았고, 이 pair는 selector만의 공정한 비교도
아니다. `work-credit` admission은 완료된 dense service에서 다음 admission credit을
만든다. ERCB가 dense를 더 고른 결과 다음 dense view도 더 많이 열려, 동일 stream인데
최종 dense pool이 RR `23`, ERCB `32`로 달라졌다. topology event 수도 `19/18`로
달라졌다. 즉 selector → service → admission/topology → map이라는 closed loop가 생겼다.

또한 RR의 dense selection count는 median `42`, p10 `12.4`였고 23장 중 required
opportunity 4회 미달은 1장뿐이었다. strict 1.5x라도 이 admission 아래에서는 대부분의
admitted dense view가 이미 충분히 서비스되어, exp03 fixed replay의 저예산 경쟁 조건과
다르다.

## 판정

**ERCB 우위 미관측, selector-isolation에는 부적합.** 추가 seed를 반복해도 admission
혼입을 해결하지 못하므로 이 조건은 확장하지 않는다. 다음 `exp03-B`에서 causal dense
arrival/membership을 RR와 ERCB에 동일하게 고정하고 selector 효과를 분리한다.

## 해석 제한

낮은 예산에서 양수이고 충분한 예산에서 동률인 interaction을 목표로 한다. ERCB의
full-budget terminal PSNR 보편 우월성을 성공 조건으로 두지 않는다.
