# R4 all-scene fixed-work 요약

날짜: 2026-09-15

범위: B-track mapping-only fixed-work; not C-track strict live-time

## 결론

- 계획 18개 중 유효 17개, N/A 1개
- 유효 장면 PSNR 승리: 17/17
- scene-mean PSNR: R4 **22.2592 dB**, vanilla **20.9983 dB**, delta **+1.2609 dB**
- view-weighted PSNR delta: **+1.4903 dB** (10,557 views)
- scene-mean SSIM/LPIPS delta: **+0.04125 / -0.04619**
- prospective all-scene acceptance: **PASS**

## 데이터셋별 집계

| Dataset | 유효 | 승리 | Views | R4 PSNR | Vanilla PSNR | ΔPSNR | View-weighted ΔPSNR | ΔSSIM | ΔLPIPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RPNG | 8 | 8 | 8,148 | 24.0945 | 22.4954 | **+1.5991** | +1.5458 | +0.05940 | -0.06411 |
| UTMM | 7 | 7 | 1,608 | 19.2545 | 18.7135 | **+0.5411** | +0.6151 | +0.01827 | -0.00784 |
| ARIA | 2 | 2 | 801 | 25.4347 | 23.0073 | **+2.4274** | +2.6834 | +0.04907 | -0.10873 |

## Role별 집계

| Role | 유효 | 승리 | Views | R4 PSNR | Vanilla PSNR | ΔPSNR |
|---|---:|---:|---:|---:|---:|---:|
| `confirmation` | 10 | 10 | 7,589 | 21.1465 | 20.1949 | **+0.9516** |
| `development` | 5 | 5 | 1,845 | 23.7008 | 22.3815 | **+1.3193** |
| `previously_exposed_validation` | 1 | 1 | 584 | 23.2957 | 21.1408 | **+2.1548** |
| `transfer` | 1 | 1 | 539 | 25.1420 | 21.9743 | **+3.1677** |

## 장면별 품질

LPIPS는 낮을수록 좋다.

| Dataset | Scene | Role | Views | R4 PSNR | Vanilla PSNR | ΔPSNR | ΔSSIM | ΔLPIPS |
|---|---|---|---:|---:|---:|---:|---:|---:|
| RPNG | `table_01` | `development` | 502 | 25.6243 | 23.9294 | **+1.6949** | +0.05475 | -0.04584 |
| RPNG | `table_02` | `previously_exposed_validation` | 584 | 23.2957 | 21.1408 | **+2.1548** | +0.08760 | -0.06324 |
| RPNG | `table_03` | `confirmation` | 1,402 | 23.5045 | 21.8338 | **+1.6707** | +0.07829 | -0.07934 |
| RPNG | `table_04` | `confirmation` | 1,215 | 22.3651 | 21.2403 | **+1.1248** | +0.04553 | -0.04391 |
| RPNG | `table_05` | `confirmation` | 1,234 | 22.7780 | 21.7007 | **+1.0773** | +0.04207 | -0.05535 |
| RPNG | `table_06` | `development` | 555 | 24.4876 | 22.7171 | **+1.7705** | +0.06661 | -0.08229 |
| RPNG | `table_07` | `confirmation` | 958 | 26.8400 | 25.3018 | **+1.5382** | +0.04531 | -0.05151 |
| RPNG | `table_08` | `confirmation` | 1,698 | 23.8604 | 22.0988 | **+1.7616** | +0.05503 | -0.09139 |
| UTMM | `ego-centric-1` | `confirmation` | 308 | 17.7558 | 17.2178 | **+0.5380** | +0.03669 | -0.00099 |
| UTMM | `ego-centric-2` | `confirmation` | 261 | 19.4944 | 19.2419 | **+0.2525** | +0.01678 | +0.00547 |
| UTMM | `ego-drive` | `development` | 281 | 21.2489 | 20.5567 | **+0.6922** | +0.02820 | -0.03224 |
| UTMM | `fast-straight` | `confirmation` | 68 | 16.3792 | 16.0215 | **+0.3577** | +0.00171 | -0.00266 |
| UTMM | `slow-straight-2` | `confirmation` | 121 | 17.2476 | 17.0858 | **+0.1618** | -0.00645 | +0.01708 |
| UTMM | `square-1` | `confirmation` | 324 | 21.2397 | 20.2063 | **+1.0334** | +0.03504 | -0.02921 |
| UTMM | `square-2` | `development` | 245 | 21.4160 | 20.6642 | **+0.7518** | +0.01591 | -0.01229 |
| ARIA | `aria1253` | `development` | 262 | 25.7274 | 24.0403 | **+1.6872** | +0.04334 | -0.08350 |
| ARIA | `aria301_305` | `transfer` | 539 | 25.1420 | 21.9743 | **+3.1677** | +0.05481 | -0.13396 |
| UTMM | `slow-straight-1` | `confirmation` | 80 | N/A | N/A | N/A | N/A | N/A |

## 장면별 work와 모델 규모

| Dataset | Scene | Renders/arm | Adam R4/vanilla | GS R4/vanilla | Mapping services | Verifier |
|---|---|---:|---:|---:|---:|---:|
| RPNG | `table_01` | 38,302 | 3,030/3,027 | 417,618/182,825 | 279 | 10/10 |
| RPNG | `table_02` | 53,669 | 4,229/4,231 | 592,626/260,887 | 392 | 10/10 |
| RPNG | `table_03` | 85,029 | 6,724/6,706 | 882,294/342,913 | 610 | 10/10 |
| RPNG | `table_04` | 67,793 | 5,359/5,343 | 751,943/301,623 | 491 | 10/10 |
| RPNG | `table_05` | 52,480 | 4,135/4,138 | 463,577/214,557 | 383 | 10/10 |
| RPNG | `table_06` | 34,437 | 2,714/2,719 | 329,246/148,686 | 254 | 10/10 |
| RPNG | `table_07` | 33,422 | 2,691/2,680 | 344,188/172,953 | 246 | 10/10 |
| RPNG | `table_08` | 94,283 | 7,465/7,436 | 923,349/387,014 | 675 | 10/10 |
| UTMM | `ego-centric-1` | 5,676 | 466/465 | 78,522/82,052 | 45 | 10/10 |
| UTMM | `ego-centric-2` | 6,655 | 559/556 | 84,369/108,195 | 54 | 10/10 |
| UTMM | `ego-drive` | 11,226 | 898/900 | 112,330/123,799 | 81 | 10/10 |
| UTMM | `fast-straight` | 1,348 | 172/165 | 21,614/33,799 | 9 | 10/10 |
| UTMM | `slow-straight-2` | 1,888 | 177/171 | 24,369/36,868 | 9 | 10/10 |
| UTMM | `square-1` | 9,345 | 757/763 | 119,867/149,943 | 76 | 10/10 |
| UTMM | `square-2` | 8,277 | 676/679 | 104,870/130,369 | 67 | 10/10 |
| ARIA | `aria1253` | 13,620 | 1,055/1,071 | 177,174/174,647 | 111 | 10/10 |
| ARIA | `aria301_305` | 17,620 | 1,344/1,376 | 214,276/197,476 | 146 | 10/10 |

## Acceptance와 예외

적용한 사전 기준은 `valid-scene arithmetic mean delta PSNR >= +0.5 dB, strict majority positive, and every included pair passes all fairness checks`이다.

- 평균 ΔPSNR ≥ 0.5 dB: **PASS**
- strict majority positive: **PASS**
- 모든 포함 pair fairness valid: **PASS**
- UTMM `slow-straight-1` N/A: tracker-ineligible: 0 metric_rescale events and no IMU metric initialization, so mapping-after-metric-init admits no map for either arm.

원래 X4 gate는 사후 변경하지 않았다. 유효 confirmation 10개 평균은 +0.951601 dB였지만 UTMM confirmation 5개 평균은 +0.468676 dB였고, `slow-straight-1`은 N/A였으므로 원래 gate는 HOLD다.

## 범위와 원본

이 결과는 B-track mapping-only fixed-work 결과다. C-track strict live-time, 27 dB milestone, region-GT/floater 개선을 증명하지 않는다.

- 장면별 정규화 행: [`summary.csv`](summary.csv)
- verifier, source manifest, 실행 경로와 SHA: [`provenance.json`](provenance.json)
- 해석과 프로토콜 상세: [`README.md`](README.md)

이 파일은 `build_summary.py`가 원시 verifier artifact에서 생성한다.

## Gaussian 수와 mapping 시간 감사

아래 시간은 기존 unbounded B-track 로그의 `mapping_wall_seconds`를 집계한 것이다. 각 pair는 physical training render 수가 정확히 같지만, R4와 vanilla의 Adam step 및 gradient scope는 같지 않다. 따라서 `ms/Adam`과 `ms/render`는 CUDA kernel 자체의 순수 시간이 아니라 mapping 전체 wall-time proxy다.

| Dataset | Scenes | Mean final GS R4/vanilla | Mapping wall R4/vanilla (s) | Wall ratio | ms/Adam R4/vanilla | ms/render R4/vanilla | map() calls R4/vanilla |
|---|---:|---:|---:|---:|---:|---:|---:|
| RPNG | 8 | 2.297× | 2327.993/2273.063 | 1.024× | 64.049/62.653 | 5.067/4.948 | 9,750/3,258 |
| UTMM | 7 | 0.793× | 198.094/156.331 | 1.267× | 53.467/42.263 | 4.460/3.520 | 918/313 |
| ARIA | 2 | 1.050× | 90.235/119.908 | 0.753× | 37.614/49.002 | 2.888/3.838 | 711/239 |
| **전체** | **17** | **1.531×** | **2616.323/2549.302** | **1.026×** | **61.632/60.088** | **4.890/4.764** | **11,379/3,810** |

전체적으로 R4의 scene별 최종 Gaussian 비율 평균은 **1.531×**였지만, mapping wall은 **1.026×**, 즉 **+2.6%**에 그쳤다. R4가 빠른 장면은 6/17개, 느린 장면은 11/17개였다.

최종 Gaussian 수만으로 시간 차이를 설명할 수 없다. RPNG는 최종 GS가 2.297×인데 wall은 1.024×였고, UTMM은 GS가 0.793×로 더 적은데 wall은 1.267×였다. Aria는 GS가 1.050×로 비슷하지만 wall은 0.753×였다.

이유는 (1) 최종 GS 수는 실행 중 평균이나 view별 visible/touched splat 수가 아니고, (2) R4의 dense/KF 보조 update는 appearance-only인 반면 vanilla는 native full-gradient update이며, (3) R4는 frontier/dense/KF service를 분리해 전체 `map()` 호출이 11,379회로 vanilla 3,810회의 약 2.99배이고, (4) PGBA pose refresh, C1/ERCB 장부, densify/prune 및 topology overhead도 wall-time에 포함되기 때문이다.

메모리 영향은 명확하다. RPNG `table_01`은 최종 GS 417,618/182,825 (2.284×), peak CUDA allocated 5.10/2.38 GB였지만, mapping wall은 167.288/194.840초로 오히려 R4가 14.1% 빨랐다. 현재 증거에서 Gaussian 증가는 속도보다 메모리 압력에 더 직접적으로 나타난다.

이 감사만으로 C-track에서 tracking과 GPU를 경쟁할 때의 deadline 영향이나 Gaussian 수의 순수 인과 효과를 증명하지 않는다. 후자를 분리하려면 동일 R4 경로에서 Gaussian capacity만 바꾼 profiler pair가 필요하다.

## 장면별 mapping iteration과 admission

여기서 iteration은 양 arm에 공통으로 정의할 수 있는 **완료된 Gaussian Adam step**이다. R4의 `F/D/K`는 각각 native frontier full-gradient Adam, dense appearance-only Adam, 별도 KF appearance-only Adam이며 항상 `R4 total = F + D + K`다. Frontier 한 step은 여러 keyframe view를 render하므로 iteration 수와 physical rendered-view 수는 구분한다.

| Dataset | Scene | Total Adam R4/vanilla | R4 F/D/K Adam | Dense arrived→admitted (rate) | Dense selected unique | KF tracked→admitted→selected unique |
|---|---|---:|---:|---:|---:|---:|
| RPNG | `table_01` | 3,030/3,027 | 2,492/269/269 | 1,728→270 (15.62%) | 267 | 210→210→189 |
| RPNG | `table_02` | 4,229/4,231 | 3,465/382/382 | 1,999→383 (19.16%) | 380 | 289→289→276 |
| RPNG | `table_03` | 6,724/6,706 | 5,524/600/600 | 5,105→601 (11.77%) | 598 | 430→430→353 |
| RPNG | `table_04` | 5,359/5,343 | 4,397/481/481 | 4,467→482 (10.79%) | 480 | 345→345→279 |
| RPNG | `table_05` | 4,135/4,138 | 3,389/373/373 | 4,626→374 (8.08%) | 371 | 273→273→223 |
| RPNG | `table_06` | 2,714/2,719 | 2,226/244/244 | 1,989→245 (12.32%) | 242 | 186→186→166 |
| RPNG | `table_07` | 2,691/2,680 | 2,219/236/236 | 3,624→237 (6.54%) | 234 | 173→173→138 |
| RPNG | `table_08` | 7,465/7,436 | 6,135/665/665 | 6,292→666 (10.58%) | 663 | 462→462→401 |
| UTMM | `ego-centric-1` | 466/465 | 386/40/40 | 1,146→41 (3.58%) | 39 | 43→40→39 |
| UTMM | `ego-centric-2` | 559/556 | 461/49/49 | 979→50 (5.11%) | 48 | 45→45→37 |
| UTMM | `ego-drive` | 898/900 | 746/76/76 | 998→77 (7.72%) | 73 | 67→67→57 |
| UTMM | `fast-straight` | 172/165 | 164/4/4 | 226→5 (2.21%) | 3 | 10→4→3 |
| UTMM | `slow-straight-2` | 177/171 | 169/4/4 | 406→5 (1.23%) | 2 | 14→3→2 |
| UTMM | `square-1` | 757/763 | 615/71/71 | 1,219→72 (5.91%) | 70 | 71→71→70 |
| UTMM | `square-2` | 676/679 | 552/62/62 | 913→63 (6.90%) | 61 | 58→58→47 |
| ARIA | `aria1253` | 1,055/1,071 | 853/101/101 | 932→102 (10.94%) | 100 | 91→91→76 |
| ARIA | `aria301_305` | 1,344/1,376 | 1,072/136/136 | 2,026→137 (6.76%) | 135 | 118→118→93 |
| **전체** | **17 valid** | **42,451/42,426** | **34,865/3,793/3,793** | **38,675→3,810 (9.85%)** | **3,766** | **2,885→2,865→2,449** |

## 장면별 KF:dense 학습 비율

`KF-side`는 native frontier와 별도 KF appearance를 합친 값이다. `Aux K:D`는 별도 KF appearance와 dense appearance만 비교한다. `KF-side:D rendered views`는 실제로 rasterize된 keyframe-origin view와 dense view의 비율이라, multi-view frontier 때문에 Adam 비율보다 훨씬 크다.

| Dataset | Scene | Aux K:D Adam | KF-side:D Adam | KF-side:D rendered views | Dense share of all renders |
|---|---|---:|---:|---:|---:|
| RPNG | `table_01` | 269:269 (1.00:1) | 2,761:269 (10.26:1) | 38,033:269 (141.39:1) | 0.702% |
| RPNG | `table_02` | 382:382 (1.00:1) | 3,847:382 (10.07:1) | 53,287:382 (139.49:1) | 0.712% |
| RPNG | `table_03` | 600:600 (1.00:1) | 6,124:600 (10.21:1) | 84,429:600 (140.72:1) | 0.706% |
| RPNG | `table_04` | 481:481 (1.00:1) | 4,878:481 (10.14:1) | 67,312:481 (139.94:1) | 0.710% |
| RPNG | `table_05` | 373:373 (1.00:1) | 3,762:373 (10.09:1) | 52,107:373 (139.70:1) | 0.711% |
| RPNG | `table_06` | 244:244 (1.00:1) | 2,470:244 (10.12:1) | 34,193:244 (140.14:1) | 0.709% |
| RPNG | `table_07` | 236:236 (1.00:1) | 2,455:236 (10.40:1) | 33,186:236 (140.62:1) | 0.706% |
| RPNG | `table_08` | 665:665 (1.00:1) | 6,800:665 (10.23:1) | 93,618:665 (140.78:1) | 0.705% |
| UTMM | `ego-centric-1` | 40:40 (1.00:1) | 426:40 (10.65:1) | 5,636:40 (140.90:1) | 0.705% |
| UTMM | `ego-centric-2` | 49:49 (1.00:1) | 510:49 (10.41:1) | 6,606:49 (134.82:1) | 0.736% |
| UTMM | `ego-drive` | 76:76 (1.00:1) | 822:76 (10.82:1) | 11,150:76 (146.71:1) | 0.677% |
| UTMM | `fast-straight` | 4:4 (1.00:1) | 168:4 (42.00:1) | 1,344:4 (336.00:1) | 0.297% |
| UTMM | `slow-straight-2` | 4:4 (1.00:1) | 173:4 (43.25:1) | 1,884:4 (471.00:1) | 0.212% |
| UTMM | `square-1` | 71:71 (1.00:1) | 686:71 (9.66:1) | 9,274:71 (130.62:1) | 0.760% |
| UTMM | `square-2` | 62:62 (1.00:1) | 614:62 (9.90:1) | 8,215:62 (132.50:1) | 0.749% |
| ARIA | `aria1253` | 101:101 (1.00:1) | 954:101 (9.45:1) | 13,519:101 (133.85:1) | 0.742% |
| ARIA | `aria301_305` | 136:136 (1.00:1) | 1,208:136 (8.88:1) | 17,484:136 (128.56:1) | 0.772% |
| **전체** | **17 valid** | **3,793:3,793 (1.00:1)** | **38,658:3,793 (10.19:1)** | **531,277:3,793 (140.07:1)** | **0.709%** |

보조 appearance scheduler 자체는 모든 장면에서 KF:Dense가 정확히 1:1이다. 하지만 native frontier를 포함하면 전체 17개에서 KF-side:Dense는 Adam 기준 **10.19:1**, physical render 기준 **140.07:1**이며, dense view는 전체 physical render의 **0.709%**다. 즉 dense가 보조 slot 안에서는 KF와 동등하지만, 전체 native keyframe 학습량과 비교하면 작은 비중이라는 점을 함께 봐야 한다.

UTMM `slow-straight-1`은 tracker metric initialization 실패로 양 arm 모두 map이 없어 위 두 표에서 제외했다.
