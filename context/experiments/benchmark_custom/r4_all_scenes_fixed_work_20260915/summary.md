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
