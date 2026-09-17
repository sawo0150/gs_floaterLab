# ERCB benchmark-A — historical exp03 budget sweep

상태: **39/39 valid scene-budget three-arm 비교 완료**. 원 VIGS source가 없는 3개 scene은 각 budget에서 unavailable이다.

기존 RPNG table_01의 약 +1dB 결과를 만든 scheduler-isolation 설정을 장면별 재튜닝 없이 저·중·고예산으로 확장했다. strict end-to-end VIGS가 아니라 fixed final VIGS pose/init을 쓰는 진단 실험이다.

## 고정 계약

- update budget: keyframe-arrival event당 15/30/60회(low/mid/high), seed 0
- full-pool RR vs recent-10-keyframe-interval window RR vs interval relative-floor ERCB (`K=8`, `rho=.5`, `gamma=log(3)`)
- resolution 4, RGB-only, fixed topology, llffhold-8, optimizer zero-tail
- historical exp03 schedule builder를 그대로 사용했다. 마지막 tracking keyframe 뒤 RGB가 그 마지막 event에 함께 admission되는 tail 의미론까지 재현하므로 인과적 streaming 증거가 아니다.

## Low budget — 15 updates/event

| family | scene | status | events | train/test | updates | full RR | window10 RR | ERCB | window−full | ERCB−full | ERCB−window |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rpng | table_01 | three_arm_pass | 244 | 2192/314 | 3646 | 22.0061 | 20.1206 | 23.2121 | -1.8855 | 1.2060 | 3.0914 |
| rpng | table_02 | three_arm_pass | 330 | 2549/365 | 4936 | 19.3381 | 16.9111 | 19.8949 | -2.4270 | 0.5568 | 2.9838 |
| rpng | table_03 | three_arm_pass | 506 | 6130/876 | 7576 | 20.8299 | 17.6224 | 21.0941 | -3.2076 | 0.2642 | 3.4717 |
| rpng | table_04 | three_arm_pass | 413 | 5309/759 | 6181 | 20.3172 | 19.6579 | 21.4399 | -0.6593 | 1.1227 | 1.7821 |
| rpng | table_05 | three_arm_pass | 332 | 5393/771 | 4966 | 20.8555 | 19.6839 | 23.4244 | -1.1716 | 2.5689 | 3.7405 |
| rpng | table_06 | three_arm_pass | 224 | 2421/346 | 3346 | 23.1252 | 20.3334 | 23.2414 | -2.7918 | 0.1162 | 2.9080 |
| rpng | table_07 | unavailable: VIGS PGBA failed; no full pose trajectory/keyframe export | — | — | — | — | — | — | — | — | — |
| rpng | table_08 | unavailable: VIGS OOM; no full pose trajectory/keyframe export | — | — | — | — | — | — | — | — | — |
| utmm | ego-centric-1 | three_arm_pass | 56 | 1343/192 | 826 | 18.1185 | 16.5451 | 18.4009 | -1.5735 | 0.2824 | 1.8558 |
| utmm | ego-centric-2 | three_arm_pass | 65 | 1135/163 | 961 | 17.0513 | 16.8245 | 17.6789 | -0.2268 | 0.6276 | 0.8544 |
| utmm | ego-drive | three_arm_pass | 87 | 1224/175 | 1291 | 17.4330 | 16.7064 | 17.7442 | -0.7266 | 0.3112 | 1.0378 |
| utmm | fast-straight | three_arm_pass | 18 | 290/42 | 256 | 15.9438 | 16.0540 | 16.3460 | 0.1102 | 0.4022 | 0.2919 |
| utmm | slow-straight-1 | unavailable: VIGS mapping initialization failed; no full pose/init export | — | — | — | — | — | — | — | — | — |
| utmm | slow-straight-2 | three_arm_pass | 16 | 522/75 | 226 | 16.1500 | 16.0856 | 16.0634 | -0.0644 | -0.0866 | -0.0222 |
| utmm | square-1 | three_arm_pass | 80 | 1412/202 | 1186 | 16.5784 | 15.5652 | 16.8027 | -1.0132 | 0.2243 | 1.2374 |
| utmm | square-2 | three_arm_pass | 73 | 1066/153 | 1081 | 16.2862 | 14.8762 | 16.3720 | -1.4101 | 0.0858 | 1.4958 |

## Mid budget — 30 updates/event

| family | scene | status | events | train/test | updates | full RR | window10 RR | ERCB | window−full | ERCB−full | ERCB−window |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rpng | table_01 | three_arm_pass | 244 | 2192/314 | 7291 | 23.7342 | 20.2151 | 23.7209 | -3.5191 | -0.0133 | 3.5058 |
| rpng | table_02 | three_arm_pass | 330 | 2549/365 | 9871 | 20.3977 | 16.8070 | 20.3789 | -3.5906 | -0.0188 | 3.5719 |
| rpng | table_03 | three_arm_pass | 506 | 6130/876 | 15151 | 21.3713 | 17.4140 | 21.3572 | -3.9573 | -0.0141 | 3.9431 |
| rpng | table_04 | three_arm_pass | 413 | 5309/759 | 12361 | 21.8259 | 19.5478 | 21.8497 | -2.2781 | 0.0238 | 2.3019 |
| rpng | table_05 | three_arm_pass | 332 | 5393/771 | 9931 | 21.4743 | 19.7234 | 24.0077 | -1.7509 | 2.5334 | 4.2843 |
| rpng | table_06 | three_arm_pass | 224 | 2421/346 | 6691 | 24.1981 | 20.4655 | 23.9333 | -3.7326 | -0.2648 | 3.4678 |
| rpng | table_07 | unavailable: VIGS PGBA failed; no full pose trajectory/keyframe export | — | — | — | — | — | — | — | — | — |
| rpng | table_08 | unavailable: VIGS OOM; no full pose trajectory/keyframe export | — | — | — | — | — | — | — | — | — |
| utmm | ego-centric-1 | three_arm_pass | 56 | 1343/192 | 1651 | 19.3753 | 16.8924 | 19.3790 | -2.4829 | 0.0037 | 2.4866 |
| utmm | ego-centric-2 | three_arm_pass | 65 | 1135/163 | 1921 | 18.4909 | 17.0340 | 18.4255 | -1.4570 | -0.0655 | 1.3915 |
| utmm | ego-drive | three_arm_pass | 87 | 1224/175 | 2581 | 18.2355 | 17.1327 | 18.4405 | -1.1028 | 0.2050 | 1.3078 |
| utmm | fast-straight | three_arm_pass | 18 | 290/42 | 511 | 17.8993 | 17.6746 | 17.9629 | -0.2247 | 0.0637 | 0.2883 |
| utmm | slow-straight-1 | unavailable: VIGS mapping initialization failed; no full pose/init export | — | — | — | — | — | — | — | — | — |
| utmm | slow-straight-2 | three_arm_pass | 16 | 522/75 | 451 | 17.8439 | 17.7310 | 17.8333 | -0.1130 | -0.0106 | 0.1023 |
| utmm | square-1 | three_arm_pass | 80 | 1412/202 | 2371 | 17.5637 | 15.9520 | 17.7830 | -1.6117 | 0.2193 | 1.8310 |
| utmm | square-2 | three_arm_pass | 73 | 1066/153 | 2161 | 16.8289 | 15.2657 | 17.1353 | -1.5632 | 0.3064 | 1.8697 |

## High budget — 60 updates/event

| family | scene | status | events | train/test | updates | full RR | window10 RR | ERCB | window−full | ERCB−full | ERCB−window |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rpng | table_01 | three_arm_pass | 244 | 2192/314 | 14581 | 24.0383 | 20.1301 | 23.8420 | -3.9082 | -0.1963 | 3.7118 |
| rpng | table_02 | three_arm_pass | 330 | 2549/365 | 19741 | 20.5467 | 16.6143 | 20.1768 | -3.9323 | -0.3699 | 3.5624 |
| rpng | table_03 | three_arm_pass | 506 | 6130/876 | 30301 | 21.4638 | 17.3634 | 21.4489 | -4.1004 | -0.0149 | 4.0854 |
| rpng | table_04 | three_arm_pass | 413 | 5309/759 | 24721 | 21.8240 | 19.4996 | 22.0928 | -2.3244 | 0.2689 | 2.5933 |
| rpng | table_05 | three_arm_pass | 332 | 5393/771 | 19861 | 24.4944 | 19.4749 | 24.2970 | -5.0195 | -0.1974 | 4.8221 |
| rpng | table_06 | three_arm_pass | 224 | 2421/346 | 13381 | 24.4194 | 20.7171 | 24.6019 | -3.7023 | 0.1825 | 3.8848 |
| rpng | table_07 | unavailable: VIGS PGBA failed; no full pose trajectory/keyframe export | — | — | — | — | — | — | — | — | — |
| rpng | table_08 | unavailable: VIGS OOM; no full pose trajectory/keyframe export | — | — | — | — | — | — | — | — | — |
| utmm | ego-centric-1 | three_arm_pass | 56 | 1343/192 | 3301 | 20.3711 | 16.8965 | 20.4455 | -3.4746 | 0.0744 | 3.5490 |
| utmm | ego-centric-2 | three_arm_pass | 65 | 1135/163 | 3841 | 19.2947 | 17.2244 | 19.1667 | -2.0703 | -0.1279 | 1.9424 |
| utmm | ego-drive | three_arm_pass | 87 | 1224/175 | 5161 | 19.1073 | 17.3276 | 19.1432 | -1.7797 | 0.0359 | 1.8156 |
| utmm | fast-straight | three_arm_pass | 18 | 290/42 | 1021 | 18.9990 | 18.3554 | 18.8141 | -0.6436 | -0.1849 | 0.4587 |
| utmm | slow-straight-1 | unavailable: VIGS mapping initialization failed; no full pose/init export | — | — | — | — | — | — | — | — | — |
| utmm | slow-straight-2 | three_arm_pass | 16 | 522/75 | 901 | 18.7558 | 18.6383 | 18.8393 | -0.1175 | 0.0835 | 0.2009 |
| utmm | square-1 | three_arm_pass | 80 | 1412/202 | 4741 | 18.8235 | 16.3898 | 18.7537 | -2.4337 | -0.0698 | 2.3640 |
| utmm | square-2 | three_arm_pass | 73 | 1066/153 | 4321 | 18.1121 | 15.3885 | 18.0069 | -2.7236 | -0.1053 | 2.6184 |

## Budget/family averages

| budget | family | scenes | full RR | window10 RR | ERCB | window−full mean/median | window wins | ERCB−full mean/median | ERCB wins | ERCB−window |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 (low) | utmm | 7 | 16.7945 | 16.0939 | 17.0583 | -0.7006/-0.7266 | 1/7 | 0.2638/0.2824 | 6/7 | 0.9644 |
| 15 (low) | rpng | 6 | 21.0787 | 19.0549 | 22.0511 | -2.0238/-2.1562 | 0/6 | 0.9725/0.8397 | 6/6 | 2.9962 |
| 15 (low) | all | 13 | 18.7718 | 17.4605 | 19.3627 | -1.3113/-1.1716 | 1/13 | 0.5909/0.3112 | 12/13 | 1.9022 |
| 30 (mid) | utmm | 7 | 18.0339 | 16.8118 | 18.1371 | -1.2222/-1.4570 | 0/7 | 0.1031/0.0637 | 5/7 | 1.3253 |
| 30 (mid) | rpng | 6 | 22.1669 | 19.0288 | 22.5413 | -3.1381/-3.5549 | 0/6 | 0.3744/-0.0137 | 2/6 | 3.5125 |
| 30 (mid) | all | 13 | 19.9415 | 17.8350 | 20.1698 | -2.1064/-1.7509 | 0/13 | 0.2283/0.0037 | 7/13 | 2.3348 |
| 60 (high) | utmm | 7 | 19.0662 | 17.1744 | 19.0242 | -1.8919/-2.0703 | 0/7 | -0.0420/-0.0698 | 3/7 | 1.8498 |
| 60 (high) | rpng | 6 | 22.7978 | 18.9666 | 22.7432 | -3.8312/-3.9202 | 0/6 | -0.0545/-0.1056 | 2/6 | 3.7767 |
| 60 (high) | all | 13 | 20.7885 | 18.0015 | 20.7407 | -2.7869/-2.7236 | 0/13 | -0.0478/-0.0698 | 5/13 | 2.7391 |

## Per-scene budget interaction

| family | scene | window−full @15/@30/@60 | ERCB−full @15/@30/@60 |
|---|---|---:|---:|
| rpng | table_01 | -1.8855/-3.5191/-3.9082 | 1.2060/-0.0133/-0.1963 |
| rpng | table_02 | -2.4270/-3.5906/-3.9323 | 0.5568/-0.0188/-0.3699 |
| rpng | table_03 | -3.2076/-3.9573/-4.1004 | 0.2642/-0.0141/-0.0149 |
| rpng | table_04 | -0.6593/-2.2781/-2.3244 | 1.1227/0.0238/0.2689 |
| rpng | table_05 | -1.1716/-1.7509/-5.0195 | 2.5689/2.5334/-0.1974 |
| rpng | table_06 | -2.7918/-3.7326/-3.7023 | 0.1162/-0.2648/0.1825 |
| utmm | ego-centric-1 | -1.5735/-2.4829/-3.4746 | 0.2824/0.0037/0.0744 |
| utmm | ego-centric-2 | -0.2268/-1.4570/-2.0703 | 0.6276/-0.0655/-0.1279 |
| utmm | ego-drive | -0.7266/-1.1028/-1.7797 | 0.3112/0.2050/0.0359 |
| utmm | fast-straight | 0.1102/-0.2247/-0.6436 | 0.4022/0.0637/-0.1849 |
| utmm | slow-straight-2 | -0.0644/-0.1130/-0.1175 | -0.0866/-0.0106/0.0835 |
| utmm | square-1 | -1.0132/-1.6117/-2.4337 | 0.2243/0.2193/-0.0698 |
| utmm | square-2 | -1.4101/-1.5632/-2.7236 | 0.0858/0.3064/-0.1053 |

## Existing exp03 low-budget anchor rerun

| scene | previous delta | benchmark-A delta | difference | sign |
|---|---:|---:|---:|---|
| utmm/square-1 | 0.3131 | 0.2243 | -0.0888 | same positive |
| rpng/table_01 | 1.1867 | 1.2060 | 0.0193 | same positive |

두 anchor의 event15 schedule SHA-256은 기존 exp03 입력과 일치한다.

## 판정

전체 scene-unweighted ERCB−RR 평균은 15:+0.5909dB > 30:+0.2283dB > 60:-0.0478dB다. 예산이 증가할수록 이득이 단조 감소했다.

15 budget ERCB 12/13 승; 30 budget ERCB 7/13 승; 60 budget ERCB 5/13 승.

15 budget window10−full RR -1.3113dB (1/13 승); 30 budget window10−full RR -2.1064dB (0/13 승); 60 budget window10−full RR -2.7869dB (0/13 승).

Window10의 시간순 frame quartile service 평균은 저예산 [0.2669, 0.2771, 0.2736, 0.1825], 고예산 [0.2801, 0.2785, 0.2721, 0.1693]다. Full RR의 대응 분포는 각각 [0.4174, 0.2885, 0.2006, 0.0935]와 [0.5401, 0.2752, 0.1391, 0.0456]다.

Window10−full RR delta와 keyframe event 수의 Pearson 상관은 15:-0.6398, 30:-0.7207, 60:-0.6659다. 긴 장면일수록 recent-only window 손실이 커지는 방향이다.

따라서 최근 10개 keyframe interval만 유지하는 hard window RR은 기각한다. ERCB의 저예산 이득은 최신 구간 집중만으로 설명되지 않으며, 전체 historical pool을 보존한 상태에서 interval service를 조절하는 것이 핵심이다.

이 패널은 seed0 broad transfer이며 fixed final pose/init, fixed topology, RGB-only, historical tail admission을 쓴다. strict streaming이나 현재 unified VIGS의 selector 우위 근거로 해석하지 않는다.

Machine-readable: [`evidence/summary.json`](evidence/summary.json), [`evidence/summary.csv`](evidence/summary.csv), [`evidence/manifest.json`](evidence/manifest.json).
Raw outputs: `results/ERCB_ablation/benchmark-A_5070ti_exp03_low_budget/` (legacy root label이며 event15/30/60을 모두 포함).
RPNG table_03 event60 ERCB의 최초 중단 산출물은 `_interrupted_20260915T215046`로 보존했으며 집계에서 제외했다. clean rerun만 위 결과에 포함된다.
