# κ / τ / motion-blur 탐색 결과 (2026-09-26)

이번 탐색의 공통 권장 설정은 **k16_t4_no_blur**다. κ=16, tau=4.0, blur=OFF. 기존 immediate/tau1/blurOFF 대비 세 장면 평균 held-out PSNR +0.1734dB, 세 mapping 시간 합계 26.0% 감소다. 실제 동시 tracking/live 기준이 아니라 같은40 renders/KF 조건이다.

권장값은 [별도 실행 preset](/home/intern/VIGS-SLAM-online-worker-integration/configs/online_mapping_unified_tuned.json)과 [결과 내 복사본](/home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/recommended_config.json)에 저장하고 세 장면의 실제 runtime report와 대조했다. 기존 baseline preset은 유지했다. VIGS의 `online_mapping` options에 이 JSON 내용을 전달하는 방식이다.

## 기존 코드 설정과 비교

기존은 κ 비활성(immediate), tau1, blurOFF이며 바로 앞 KF RGB-only 대조군에서 새로 실행한 dense baseline이다. 탐색 중의 기준은 별도로 fresh immediate/tau1/blurON을 사용했다. 아래는 사용자가 원래 사용하던 blurOFF baseline과의 비교다.

| 장면 | 기존 PSNR | 선택 PSNR | 변화(dB) | 기존 mapping(s) | 선택 mapping(s) | 시간 감소 |
|---|---:|---:|---:|---:|---:|---:|
| aria | 25.5921 | 25.8851 | +0.2930 | 54.54 | 35.11 | 35.6% |
| rpng | 25.1179 | 25.2309 | +0.1130 | 144.35 | 115.36 | 20.1% |
| utmm | 22.1052 | 22.2194 | +0.1142 | 56.11 | 38.28 | 31.8% |

## 전체 탐색 결과

장면별 하락이 fresh blur baseline 대비0.05dB를 넘으면 공통 추천 후보에서 제외했다. 허용 후보 중 최고 평균PSNR과0.02dB 이내이면 가장 빠른 설정을 선택했다. 이 값은 공학적 선택 기준이며 신뢰구간이 아니다.

| 조건 | Aria | RPNG | UTMM | 평균PSNR | 평균 mapping(s) | 품질 guard |
|---|---:|---:|---:|---:|---:|---|
| immediate_t1_blur | 25.6143 | 25.0891 | 22.0991 | 24.2675 | 85.81 | 통과 |
| k4_t1_blur | 25.6848 | 25.1080 | 22.0433 | 24.2787 | 82.84 | 제외 |
| k8_t1_blur | 25.7004 | 24.9750 | 21.9786 | 24.2180 | 71.01 | 제외 |
| k16_t1_blur | 25.8319 | 25.1336 | 22.0702 | 24.3452 | 64.42 | 통과 |
| k16_t0.25_blur | 23.5295 | 24.7345 | 21.8653 | 23.3764 | 63.83 | 제외 |
| k16_t4_blur | 25.8991 | 25.2055 | 22.2340 | 24.4462 | 63.95 | 통과 |
| k16_t4_no_blur | 25.8851 | 25.2309 | 22.2194 | 24.4451 | 62.92 | 통과 |

## 무엇을 알게 됐는가

- κ4/8/16의 효과는 단조롭지 않았다. κ8은 Aria에서 유리했으나 RPNG/UTMM은 하락했다. κ16/tau1은 기준 대비 평균PSNR을 유지·개선하면서 약25%의 mapping 시간을 줄였다. 세 장면 공통값으로 비교했고 장면별 κ는 만들지 않았다.
- tau0.25는 κ16에서 세 장면 모두 악화했다. 특히 Aria는 tau1의25.8319→23.5295dB였다. 해당 두 실행의 admissions, LR positions, render/Adam 수, Gaussian 수가 같음을 별도 확인했다. 더 강하게 선택 횟수를 균등화하는 것이 더 좋은 map을 보장하지 않았다.
- tau4는 κ16에서 tau1보다 세 장면 모두 개선됐다(Aria+0.0673/RPNG+0.0719/UTMM+0.1638dB). KF와 dense 양쪽의 entropy coefficient를 함께 바꾼 비교이므로 어느 pool에서 온 효과인지는 분리하지 않았다.
- κ 제한으로 실제 준비하는 dense pose/image 수가 줄었다. Dense에 쓰는 렌더링 몫은 약50%를 유지한다. Admission 감소와 dense 학습 비중 감소를 혼동하면 안 된다. 큰 시간 이득을 blur 필터 자체의 효과로 돌리지 않는다.

## 최종 blur ON/OFF

같은 κ16/tau4의 비교다. 기존 energy0.8/frequency0.9 gate를 그대로 사용했고 임계값을 장면별로 튜닝하지 않았다.

| 장면 | blurON PSNR | blurOFF PSNR | OFF−ON(dB) | ON mapping(s) | OFF mapping(s) |
|---|---:|---:|---:|---:|---:|
| aria | 25.8991 | 25.8851 | -0.0140 | 35.89 | 35.11 |
| rpng | 25.2055 | 25.2309 | +0.0254 | 116.86 | 115.36 |
| utmm | 22.2340 | 22.2194 | -0.0146 | 39.09 | 38.28 |

## 실제 admission / sampling

κ는 현재 generation에서 완료한 optimizer step 단위의 dense admission credit이다. KF는 제한하지 않는다. 영상별Adam이라 이 실험에서는 step과 training render 수가 같다. tau는 코드의 기본 계수이며 각 pool N으로 나눠서 entropy 가중치로 사용한다. Count는 window 사용까지 포함한 누적 사용 횟수다. 예산40 renders/KF와3:3:6 비율은 유지했다.

| 장면 | 최종 offered/admitted dense | 실제 준비 distinct dense | dense 렌더링 비율 | KF/dense 실제 entropy weight | renders=Adam |
|---|---|---:|---:|---|---:|
| aria | 924/227 | 213 | 48.17% | 0.043956 / 0.017621 | 4760 |
| rpng | 1810/465 | 425 | 48.95% | 0.021505 / 0.008602 | 9080 |
| utmm | 1133/177 | 166 | 47.61% | 0.056338 / 0.022599 | 3600 |

## 검증 / 범위

- 유효GPU21조건과 각 저장 지도 평가2회 PASS. CPU30 tests 및 선택규칙검사 PASS. 모든 조건에서 scene별 total/prefix renders, Adam 수, map GS 수, 평가 cohort와 tracker poses가 동일하다. Future/held-out training0, zero-tail, actual loss route/count, blur rejection, admission credit, source hash를 audit했다.
- v1은 baseline3개 완료 뒤 첫growth run이 runtime의 full-pool-only guard 때문에 학습 전 실패했다. 실패 로그를 보존하고 guard를 paired schedule에만 제한했다. Runtime growth 배선을 회귀 테스트했다. v2는 세 baseline을 재audit/재사용했고 나머지18개를 실행했다. baseline 재사용 시 source 차이와 backend가 정확히 guard 한 줄만 달라졌다는 검사도 보존했다.
- 세 개발 장면 seed0의 coarse staged search다. 모든 κ×tau 조합을 탐색한 global optimum이나 독립 test 일반화는 아니다. 지도 두 번 평가도 독립 학습 반복은 아니다. τ4보다 큰 값 또는 κ16보다 큰 값의 최적성은 확인하지 않았다.
- Frozen causal tracker의 실제 mapper worker를 사용했으며 tracking 동시 실행/strict1.5×wall-clock/live 성능을 입증하지 않는다. Geometry/floater 지표를 평가하지 않았으므로 photometric 결과를 geometry 개선으로 해석하지 않는다.

## 연결

- [사전 계획 / 실행별 ledger](README.md)
- [구현과 정책 단위](IMPLEMENTATION.md)
- [앞선 KF RGB-only 대조군](../kf_rgb_control/SUMMARY.md): loss recipe 교체 평균+0.2892dB, 추가 dense 경로+0.3303dB로 양쪽 효과 확인.
- [전체 수치](/home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/comparison.json)
- [선택 기준 결과](/home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/final_selection.json)
- [실행 코드](/home/intern/gs_floaterLab/benchmarks/online_gs/campaigns/gain_attribution/run_growth_entropy_blur_panel.py)
