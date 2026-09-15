# ERCB benchmark-A — historical exp03 low-budget all-scene panel

상태: **13 / 16 scene paired 평가 완료** (동일 source를 만들 수 없는 3개 scene은 unavailable).

기존 RPNG table_01의 약 +1dB 결과를 만든 scheduler-isolation 설정을 장면별 재튜닝 없이 확장했다. 이 결과는 strict end-to-end VIGS가 아니라 fixed final VIGS pose/init을 쓰는 진단 실험이다.

## 고정 계약

- update budget: keyframe-arrival event당 15회, seed 0
- RR vs interval relative-floor ERCB (`K=8`, `rho=.5`, `gamma=log(3)`)
- resolution 4, RGB-only, fixed topology, llffhold-8, optimizer zero-tail
- historical exp03 schedule builder를 그대로 사용했다. 마지막 tracking keyframe 뒤 RGB가 그 마지막 event에 함께 admission되는 tail 의미론까지 재현하므로, 이 패널은 인과적 streaming 증거가 아니다.

## Scene results

| family | scene | status | events | train/test | updates | RR PSNR | ERCB PSNR | delta | zero-service RR/ERCB |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| rpng | table_01 | paired_pass | 244 | 2192/314 | 3646 | 22.0061 | 23.2121 | 1.2060 | 269/501 |
| rpng | table_02 | paired_pass | 330 | 2549/365 | 4936 | 19.3381 | 19.8949 | 0.5568 | 328/463 |
| rpng | table_03 | paired_pass | 506 | 6130/876 | 7576 | 20.8299 | 21.0941 | 0.2642 | 1532/1523 |
| rpng | table_04 | paired_pass | 413 | 5309/759 | 6181 | 20.3172 | 21.4399 | 1.1227 | 190/1246 |
| rpng | table_05 | paired_pass | 332 | 5393/771 | 4966 | 20.8555 | 23.4244 | 2.5689 | 427/1808 |
| rpng | table_06 | paired_pass | 224 | 2421/346 | 3346 | 23.1252 | 23.2414 | 0.1162 | 616/612 |
| rpng | table_07 | unavailable: VIGS PGBA failed; no full pose trajectory/keyframe export | — | — | — | — | — | — | — |
| rpng | table_08 | unavailable: VIGS OOM; no full pose trajectory/keyframe export | — | — | — | — | — | — | — |
| utmm | ego-centric-1 | paired_pass | 56 | 1343/192 | 826 | 18.1185 | 18.4009 | 0.2824 | 517/560 |
| utmm | ego-centric-2 | paired_pass | 65 | 1135/163 | 961 | 17.0513 | 17.6789 | 0.6276 | 174/417 |
| utmm | ego-drive | paired_pass | 87 | 1224/175 | 1291 | 17.4330 | 17.7442 | 0.3112 | 230/412 |
| utmm | fast-straight | paired_pass | 18 | 290/42 | 256 | 15.9438 | 16.3460 | 0.4022 | 37/119 |
| utmm | slow-straight-1 | unavailable: VIGS mapping initialization failed; no full pose/init export | — | — | — | — | — | — | — |
| utmm | slow-straight-2 | paired_pass | 16 | 522/75 | 226 | 16.1500 | 16.0634 | -0.0866 | 296/320 |
| utmm | square-1 | paired_pass | 80 | 1412/202 | 1186 | 16.5784 | 16.8027 | 0.2243 | 398/567 |
| utmm | square-2 | paired_pass | 73 | 1066/153 | 1081 | 16.2862 | 16.3720 | 0.0858 | 337/352 |

## Family averages

| family | scenes | RR mean | ERCB mean | mean delta | median delta | ERCB wins |
|---|---:|---:|---:|---:|---:|---:|
| utmm | 7 | 16.7945 | 17.0583 | 0.2638 | 0.2824 | 6/7 |
| rpng | 6 | 21.0787 | 22.0511 | 0.9725 | 0.8397 | 6/6 |
| all | 13 | 18.7718 | 19.3627 | 0.5909 | 0.3112 | 12/13 |

## Existing exp03 anchor rerun

| scene | previous delta | benchmark-A delta | difference | sign |
|---|---:|---:|---:|---|
| utmm/square-1 | 0.3131 | 0.2243 | -0.0888 | same positive |
| rpng/table_01 | 1.1867 | 1.2060 | 0.0193 | same positive |

두 anchor의 event15 schedule SHA-256은 기존 exp03 입력과 일치한다. 절대 PSNR의 작은 재실행 차이는 남지만 ERCB delta의 양수 부호는 둘 다 재현됐다.

## 판정

유효 13개 scene 중 ERCB가 12/13에서 이겼고, scene-unweighted 평균 delta는 +0.5909dB다. 따라서 기존 table_01의 저예산 이득은 이 고정 replay 패널에서 한 장면 특이값이 아니며, optimizer service가 부족할 때 interval-level 재배분이 수렴을 앞당긴다는 신호는 넓게 관측됐다.

그러나 이것은 **seed0 한 번의 broad transfer**다. 또한 ERCB의 zero-service view 수가 RR보다 많은 scene이 11/13개라, 결과를 view-level fairness 개선으로 해석하면 안 된다. 특히 table_05는 +2.5689dB지만 zero-service가 427→1,808로 늘었다. 이 구현은 제한된 update를 일부 interval에 집중시키는 방식이다.

fixed final pose/init, fixed topology, RGB-only, historical tail admission을 쓰므로 strict streaming이나 현재 unified VIGS의 selector 우위 근거는 아니다. 다음 확증 단계는 숫자 재튜닝 없이 seed1/2를 같은 13-scene panel에 반복해 paired mean과 분산을 확인하는 것이다.

Machine-readable: [`evidence/summary.json`](evidence/summary.json), [`evidence/summary.csv`](evidence/summary.csv), [`evidence/manifest.json`](evidence/manifest.json).
Raw outputs: `results/ERCB_ablation/benchmark-A_5070ti_exp03_low_budget/`.
