# Table X — KF-only vs KF+dense supervision (online incremental)

상태: **FINISHED_38_COMPLETE_0_FAILED_OF_38**

## 설정

각 VIGS keyframe interval에 **60 optimizer iteration을 동일하게 배정**한다. 따라서 총
iteration 수는 궤적 길이(=keyframe interval 수)의 결과이지 조절 대상이 아니며, 이는 online
incremental mapper가 실제로 겪는 조건이다. 두 arm은 dataset·초기 point cloud·pose·causal
arrival schedule·selector(`causal_rr`)·seed·해상도·loss·densification 정책·**총 iteration 수**·
llffhold-8 held-out(두 arm 모두 미학습)을 전부 공유하며 **후보 pool만 다르다**.

- `KF-only`: VIGS keyframe만 supervision으로 사용
- `KF+dense`: keyframe 사이에 도착한 frame까지 함께 사용

## 결과 — held-out PSNR (dB)

| scene | keyframe intervals | frames | total iters | KF-only | KF+dense | Δ | GS ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| aria/aria1253 | 123 | 1140 | 7,321 | 27.75 | **27.78** | **+0.03** | 1.12× |
| aria/aria1253rot | 185 | 1310 | 11,041 | 26.56 | **27.55** | **+0.99** | 0.94× |
| aria/aria301_12F | 349 | 1925 | 20,881 | 29.55 | **30.24** | **+0.69** | 0.97× |
| aria/aria301_305 | 169 | 2352 | 10,081 | 30.15 | **31.42** | **+1.27** | 1.09× |
| rpng/table_01 | 242 | 2192 | 14,461 | 23.66 | **23.94** | **+0.28** | 1.02× |
| rpng/table_02 | 333 | 2549 | 19,921 | 21.96 | **22.49** | **+0.53** | 0.86× |
| rpng/table_03 | 512 | 6130 | 30,661 | 22.17 | 21.45 | -0.72 | 1.05× |
| rpng/table_04 | 414 | 5309 | 24,781 | 21.13 | 20.19 | -0.94 | 1.18× |
| rpng/table_05 | 328 | 5393 | 19,621 | 25.86 | 23.78 | -2.08 | 1.01× |
| rpng/table_06 | 227 | 2421 | 13,561 | 26.01 | 25.26 | -0.74 | 0.99× |
| rpng/table_07 | 218 | 4186 | 13,021 | 26.05 | **26.54** | **+0.50** | 1.11× |
| rpng/table_08 | 566 | 7423 | 33,901 | 20.42 | **20.87** | **+0.44** | 1.31× |
| utmm/ego-centric-1 | 56 | 1343 | 3,301 | 21.69 | **22.24** | **+0.55** | 0.84× |
| utmm/ego-centric-2 | 65 | 1135 | 3,841 | 20.41 | **22.13** | **+1.72** | 0.81× |
| utmm/ego-drive | 87 | 1224 | 5,161 | 18.73 | **19.47** | **+0.74** | 1.10× |
| utmm/fast-straight | 18 | 290 | 1,021 | 20.81 | **21.16** | **+0.35** | 0.92× |
| utmm/slow-straight-2 | 16 | 522 | 901 | 19.58 | **20.07** | **+0.48** | 1.00× |
| utmm/square-1 | 80 | 1412 | 4,741 | 20.44 | **21.48** | **+1.05** | 0.93× |
| utmm/square-2 | 73 | 1066 | 4,321 | 20.06 | **21.25** | **+1.19** | 0.91× |
| **평균 (19 scenes)** | | | | | | **+0.33** (15/19) | |

`GS ratio`는 최종 Gaussian 수의 KF+dense / KF-only 비다. 1에 가까우면 품질 차이를 용량
차이로 설명할 수 없다는 뜻이다.

## 해석 제한

- pose와 초기 point cloud는 사전 VIGS run을 고정 replay한 값이다. strict online
  localization 결과가 아니며, 도착 순서(causality)와 zero-tail만 유지된다.
- 단일 seed다. 이 프로젝트의 run-to-run PSNR 분산은 과거 ±0.33dB로 실측된 바 있어,
  그보다 작은 개별 장면 차이는 단독으로 해석하지 않는다.
- held-out은 llffhold-8이라 held-out frame이 중간 frame과 시간적으로 인접하다. 두 arm이
  동일 held-out을 쓰지만 이 인접성은 KF+dense에 유리하게 작용할 수 있다.
