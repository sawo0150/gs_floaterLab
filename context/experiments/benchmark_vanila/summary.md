# Vanilla VIGS-SLAM PSNR 통합표

UTMM/RPNG 16개 장면의 세 기준을 한곳에 모았다. 로컬 두 열은 동일한
`idx % 5 == 0` evaluator 중 해당 실행의 vanilla keyframe을 제외한 held-out
PSNR이고, 논문 열은 VIGS-SLAM supplementary Table 18/19의 **final color
refinement 전** PSNR이다.

| family | scene | paper before refinement | 5070 Ti synchronous/unbounded | 5070 Ti 1.5x-paced streaming | streaming - sync |
|---|---|---:|---:|---:|---:|
| UTMM | ego-centric-1 | 20.05 | 17.3271 | 17.1881 | -0.1390 |
| UTMM | ego-centric-2 | 20.39 | 19.2300 | 19.1994 | -0.0307 |
| UTMM | ego-drive | 21.54 | 20.2834 | 20.2615 | -0.0219 |
| UTMM | fast-straight | 21.98 | 17.3971 | 17.4259 | +0.0288 |
| UTMM | slow-straight-1 | 20.66 | 18.9565 | 18.9612 | +0.0047 |
| UTMM | slow-straight-2 | 21.92 | 19.1036 | 19.1698 | +0.0662 |
| UTMM | square-1 | 19.98 | 20.6906 | 20.1950 | -0.4956 |
| UTMM | square-2 | 20.42 | 20.7113 | 20.6095 | -0.1018 |
| **UTMM 평균** | **8 scenes** | **20.8675** | **19.2125** | **19.1263** | **-0.0862** |
| RPNG | table_01 | 23.41 | 24.2268 | 24.1699 | -0.0569 |
| RPNG | table_02 | 20.84 | 21.7037 | 21.6856 | -0.0181 |
| RPNG | table_03 | 20.71 | 21.6769 | 21.2867 | -0.3902 |
| RPNG | table_04 | 21.97 | 20.7960 | 20.7658 | -0.0302 |
| RPNG | table_05 | 21.44 | 20.8956 | 21.3940 | +0.4984 |
| RPNG | table_06 | 23.47 | 23.1418 | 23.2718 | +0.1300 |
| RPNG | table_07 | 24.81 | 25.1673 | 25.2574 | +0.0901 |
| RPNG | table_08 | 21.05 | 22.1574 | 21.5246 | -0.6328 |
| **RPNG 평균** | **8 scenes** | **22.2125** | **22.4707** | **22.4195** | **-0.0512** |
| **전체 평균** | **16 scenes** | **21.5400** | **20.8416** | **20.7729** | **-0.0687** |

## 해석 범위

- `5070ti_1.5x_streaming`은 1.5x timestamp pacing과 async mapper를 사용하고
  마지막 입력 뒤 이미 제출된 mapping packet을 drain한 **품질 기준선**이다. offline
  BA와 color refinement는 없다.
- 16/16에서 tracking이 literal 1.5x wall-clock deadline보다 늦었다. 따라서 이 열은
  strict real-time 달성을 증명하지 않는다. mapper drain은 평균 1.321초, 최대
  5.456초였다.
- 논문과 로컬은 평가 split과 장비가 다르므로 `paper - local`을 재현 오차로 판정하지
  않는다. custom의 직접 비교 대상은 동일 로컬 held-out 계약의 streaming 열이다.

상세 evidence는 [synchronous 결과](synchronous_unbounded/summary.md),
[streaming 결과](5070ti_1.5x_streaming/summary.md),
[논문 전사](paper_reference/README.md)에 있다.
