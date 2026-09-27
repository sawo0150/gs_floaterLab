# Dense slot → KF RGB-only 대조군 결과 (2026-09-26)

세 장면 모두 KF RGB-only가 기존 KF loss보다 좋아졌지만, dense RGB-only에는 미치지 못했다. 따라서 기존 dense on/off 차이를 추가 관측 하나로만 설명할 수 없으며, 그렇다고 loss 구성만 바꾸면 dense 이득이 사라지는 것도 아니다.

동일40 renders/KF, seed0, nominal3:3:6, 영상별Adam, 누적ERVS, immediate admission, blurOFF, densify/prune/phase gateOFF, scale projectionON. 앞의 window3/KF3은 그대로 두고 마지막6자리만 바꿨다. KF 두 조건의 전체 선택 UID/order/batches/LR/counts는 완전히 일치했고 실제 loss dispatch도 검증했다.

## Held-out PSNR (dB)

| 장면 | KF native loss | KF RGB-only | Dense RGB-only | KF RGB-only − native | Dense − KF RGB-only |
|---|---:|---:|---:|---:|---:|
| aria aria1253 | 24.7299 | 25.0578 | 25.5921 | +0.3279 | +0.5343 |
| rpng table_06 | 24.8112 | 25.0035 | 25.1179 | +0.1923 | +0.1144 |
| utmm square-1 | 21.4156 | 21.7631 | 22.1052 | +0.3474 | +0.3421 |

장면을 같은 가중치로 평균하면 KF loss recipe 교체 +0.2892dB, dense 관측 경로 사용 +0.3303dB, 두 끝점의 차이 +0.6195dB다. 이는 이 세 조건 사이의 관측된 차이이며, 두 원인이 독립·가산적으로 작용한다는 추정이나 일반화된 기여도 비율은 아니다.

## 실행 시간과 실제 학습량

시간은 setup/held-out evaluation을 제외한 harness mapping_seconds다. Dense 조건에는 dense pose 준비·시각 보정·학습 입력 준비 비용이 포함된다. 실제 tracking 동시 수행이나 동일 wall-clock 비교가 아니다.

| 장면 | KF native (s) | KF RGB-only (s) | Dense RGB-only (s) | 공통 renders = Adam steps | 공통 최종 GS |
|---|---:|---:|---:|---:|---:|
| aria | 24.66 | 24.50 | 54.54 | 4760 | 192623 |
| rpng | 89.26 | 88.77 | 144.35 | 9080 | 357071 |
| utmm | 31.15 | 30.15 | 56.11 | 3600 | 141545 |

Dense 쪽의 추가 품질 이득에는 상당한 입력/pose 처리 비용이 있다. 같은 렌더링 예산에서 더 좋은 결과이지, 같은 시간에도 같은 이득이 난다는 검증은 아니다. KF RGB-only는 KF native와 실행 시간이 비슷했다. 기본 dense recipe는 유지하고 두 대조군은 명시적인 실험 옵션으로 남겼다.

## 실제 slot 배정

초기 pool 부족 시 중복 없는 sampling을 유지하느라 역할별 렌더링 수가 nominal 비율에서 조금 달라진다. KF 두 대조군은 서로 완전히 같고 dense arm과는 작은 차이가 있다.

| 장면 | Dense arm window / KF / dense | KF control window / KF / auxiliary | Dense pool / 실제 사용 distinct dense |
|---|---|---|---|
| aria | 1190 / 1190 / 2380 | 1201 / 1199 / 2360 | 924 / 747 |
| rpng | 2270 / 2241 / 4569 | 2271 / 2267 / 4542 | 1810 / 1437 |
| utmm | 900 / 900 / 1800 | 922 / 880 / 1798 | 1133 / 813 |

## 해석과 한계

- KF RGB-only와 KF native 비교는 이미지/pose/order/LR/Adam을 맞춘 **loss recipe 교체** 효과다. Native는 0.95×masked RGB L1 + inverse-depth + normal, dense RGB-only는 0.8×L1 + 0.2×(1−SSIM)이다. 따라서 depth나 normal 제거 중 어느 항이 원인인지, SSIM/마스크/가중치 영향인지는 여기서 분리되지 않는다. Carve는 OFF다.
- Dense와 KF RGB-only 비교에서는 RGB loss 함수가 같다. 결과는 추가 관측을 쓰는 경로의 이득을 지지하지만, 서로 다른 입력·pose·pool·count 분포와 위 초기 slot 차이가 포함되므로 픽셀 다양성 하나만의 효과로 단정하지 않는다.
- Held-out PSNR 평가이며 geometry/floater 개선을 뜻하지 않는다. 단일 seed의 세 개발 장면이다. 저장 지도 평가2회는 evaluator 일관성 검증이며 독립 학습 반복이 아니다.
- Frozen causal tracker events/poses를 사용했다. 미래/held-out 학습0, prefix별 renders 일치, 마지막 입력 뒤 optimizer0을 검증했지만 strict 1.5× wall-clock live나 tracking 동시 실행 검증은 아니다.
- 현재 `membership=immediate`, κ64는 비활성이다. 이 결과를 κ 기반 View Set Growth 이득으로 인용하지 않는다. `tau=1`, per-view 정책으로 각 pool의 entropy weight=1/N, window까지 포함한 누적 count를 사용한다. 장면별 튜닝 없음.

## 검증 / 재현

CPU 27 tests PASS. GPU9/9 실행·독립audit·각 저장 지도 평가2회 PASS. KF controls selected UID/order/batch/LR/count exact match; baseline dense service ledger는 이전 기준과 exact match. 모든 source hash가 panel 종료까지 일치했다. 각 장면 Gaussian 수와 전체 렌더링/Adam 수도 세 arm 모두 같다.

- [사전 계획 및 실행별 기록](README.md)
- [구현과 loss/entropy 해석](IMPLEMENTATION.md)
- [전체 결과 JSON](/home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/comparison.json)
- [Runner](/home/intern/gs_floaterLab/benchmarks/online_gs/campaigns/gain_attribution/run_kf_rgb_control_panel.py)
- [새 CPU tests](/home/intern/gs_floaterLab/benchmarks/online_gs/campaigns/gain_attribution/test_kf_rgb_control.py)

재현 명령(새 output 경로 필요):
```bash
/home/colin/miniconda3/envs/vigs-slam-5090/bin/python benchmarks/online_gs/campaigns/gain_attribution/run_kf_rgb_control_panel.py --output results/campaigns/gain_attribution/kf_rgb_control/gpu40_repeat
```
