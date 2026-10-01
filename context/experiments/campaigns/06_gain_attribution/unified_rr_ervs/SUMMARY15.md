# 15 renders/KF: RR / ERVS 및 dense 대조 (2026-09-27)

예산을40→15로 줄이고 나머지 tuned 설정을 유지했다. 총12개(두 sampler×두 RGB source×세 scene)를 새로 실행했다. **Dense 사용 시 ERVS−RR 평균 +0.2443dB**로40회예산의+0.0755dB보다 커졌다. 다만UTMM은−0.2696dB로악화했다. **Dense−KF RGB-only 평균은 ERVS +0.2022dB(3/3개선), RR +0.0640dB(2/3개선)**다.

## 조건

κ16 dense-only growth,τ0=4(pool별4/N),window:KF:auxiliary=3:3:6,영상별Adam,scaleON,blur/Carve/densify/pruneOFF,seed0. 예산만15renders/KF로변경했으며15회용추가튜닝은없다. Source replacement는세번째pool만dense RGB→KF RGB-only로바꿨고동일RGB loss함수사용. KF RGB-only도geometry parameter를freeze하는것은아니다. RR는window사용도KF epoch에반영하는기존online RR규칙이다.

## 전체 held-out PSNR

| Scene | KF RGB-only + RR | KF RGB-only + ERVS | Dense + RR | Dense + ERVS |
|---|---:|---:|---:|---:|
| aria | 22.7171 | 23.0592 | 22.8292 | 23.2723 |
| rpng | 23.8860 | 23.8767 | 23.4701 | 24.0295 |
| utmm | 20.6494 | 20.6352 | 21.1453 | 20.8756 |

## 두 효과를 분리한 비교

| Scene | ERVS−RR (dense 사용) | 같은 차이 @40 | Dense−KF RGB-only (RR) | Dense−KF RGB-only (ERVS) |
|---|---:|---:|---:|---:|
| aria | +0.4431 | +0.0916 | +0.1121 | +0.2131 |
| rpng | +0.5594 | +0.1521 | -0.4159 | +0.1529 |
| utmm | -0.2696 | -0.0171 | +0.4959 | +0.2405 |
| 평균 | +0.2443 | +0.0755 | +0.0640 | +0.2022 |

KF RGB-only에서ERVS−RR는Aria+0.3421/RPNG−0.0094/UTMM−0.0142dB(평균+0.1062). RPNG에서는KF관측만사용하면샘플러차이가작지만dense를사용하면ERVS가유리했다. 이는이번조건에서추가관측과선택정책의효과가연결되어있다는관찰이며일반적메커니즘증명은아니다.

## 시간과 실제 작업량

| Scene | KF RGB RR(s) | KF RGB ERVS(s) | Dense RR(s) | Dense ERVS(s) | renders=Adam | 최종admitted dense |
|---|---:|---:|---:|---:|---:|---:|
| aria | 14.51 | 14.03 | 19.08 | 18.75 | 1785 | 85 |
| rpng | 57.75 | 57.08 | 67.82 | 66.85 | 3405 | 174 |
| utmm | 25.39 | 25.41 | 27.90 | 28.36 | 1350 | 66 |

ERVS에서mapper합계는KF RGB-only 96.52s→dense 113.96s(+18.1%). Dense pose/input 준비 비용이 포함된다. 고정렌더링비교이므로동일wall-clock이득이나tracking동시실시간성을뜻하지않는다.

## 검증과 비교의 한계

- GPU12개실행·개별audit·지도별held-out평가2회통과. CPU36tests. 실행중source변경없음,두panel의공통source hash동일. 미래/held-out학습0,zero-tail,pose/cohort일치검증.
- 모든조건에서scene별총및arrival-prefix render/Adam과KF admission,입력pose,최종Gaussian수동일(192623/357071/141545). Dense admission기록도KF replacement와동일하되KF replacement는dense pose준비0·dense학습0임을확인.
- Dense RR↔ERVS는admission/pool/loss종류/batch/LR일정동일. Aria 폐기초기generation의window↔KF역할5회차이는40회실험과같이기록했으며동일native loss다.
- **Dense↔KF RGB-only는순수이미지내용만분리한실험이아니다.** 후보수/두KF pool중복/초기quota재분배로실제RGB-only횟수와batch/LR위치도일부달라진다. 같은총예산에서현재구조의관측source를대체한시스템비교로해석한다.

| Scene | Dense RGB-only render | KF RGB-only render | Loss종류가다른step수 | Batch/LR위치가다른step수 |
|---|---:|---:|---:|---:|
| aria | 763 | 845 | 122 | 144 |
| rpng | 1504 | 1616 | 168 | 149 |
| utmm | 557 | 644 | 215 | 392 |

위횟수는RR와ERVS에서같다. Loss종류차이는총RGB횟수차이와달리step별순서차이도포함한다.

- 40→15에서κ고정이므로admitted dense도227/465/177→85/174/66으로줄었다. 배치잔여분과초기pool부족으로실제dense렌더비중은42.75/44.17/41.26%다. 이실험은40회와동일training set을쓰는예산ablation이아니라현재성장정책을저예산에서그대로실행한비교다.
- 세개발장면·단일seed·frozen causal tracker. τ4는기존40회실험에서선택한값으로15회최적값을탐색하지않았다. 평가2회는학습반복이아니며통계적유의성·일반화·geometry/floater효과는미검증. 기본preset은바꾸지않았다.

## 산출물

- [15회 RR/ERVS 및40회와비교](/home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu15_v1/budget_comparison.json)
- [2×2 전체검증](/home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/dense_control_gpu15_v1/factorial_comparison.json)
- [RR/ERVS 실행요약](/home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu15_v1/summary.json)
- [KF RGB-only 실행요약](/home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/dense_control_gpu15_v1/summary.json)
- [기존40회 결과](SUMMARY.md)
- [추가대조군사전조건](dense_control/README.md)
