# synchronous_unbounded 결과

표는 vanilla keyframe을 제외한 `idx % 5 == 0` standalone held-out 평균이다. 논문 multi-method shared split이나 matched-runtime custom 비교가 아니다.

논문 열은 Table 18/19의 final color refinement 전 참고값이며 평가 split이 달라 엄밀한 재현 오차가 아니다.

| family | scene | status | frames | held-out | local PSNR | paper PSNR | local-paper | SSIM | paper SSIM | LPIPS | paper LPIPS | union PSNR | GS | wall(s) | source |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| utmm | ego-centric-1 | complete | 1535 | 299 | 17.3271 | 20.05 | -2.7229 | 0.58184 | 0.711 | 0.37793 | 0.394 | 17.4885 | 108459 | 144.95 | reused_exp81_82 |
| utmm | ego-centric-2 | complete | 1298 | 244 | 19.2300 | 20.39 | -1.1600 | 0.65318 | 0.716 | 0.32112 | 0.382 | 19.2574 | 106963 | 143.49 | reused_exp81_82 |
| utmm | ego-drive | complete | 1399 | 264 | 20.2834 | 21.54 | -1.2566 | 0.66105 | 0.696 | 0.38431 | 0.399 | 20.3739 | 127811 | 214.98 | benchmark_vanila |
| utmm | fast-straight | complete | 332 | 61 | 17.3971 | 21.98 | -4.5829 | 0.66517 | 0.695 | 0.46425 | 0.458 | 18.0531 | 40813 | 67.98 | reused_exp81_82 |
| utmm | slow-straight-1 | complete | 393 | 74 | 18.9565 | 20.66 | -1.7035 | 0.60222 | 0.669 | 0.50313 | 0.482 | 19.1492 | 33199 | 52.53 | reused_exp81_82 |
| utmm | slow-straight-2 | complete | 597 | 120 | 19.1036 | 21.92 | -2.8164 | 0.67820 | 0.695 | 0.46914 | 0.484 | 19.2329 | 36603 | 76.72 | reused_exp81_82 |
| utmm | square-1 | complete | 1614 | 311 | 20.6906 | 19.98 | 0.7106 | 0.69844 | 0.644 | 0.35249 | 0.470 | 20.7198 | 164868 | 183.05 | reused_exp81_82 |
| utmm | square-2 | complete | 1219 | 229 | 20.7113 | 20.42 | 0.2913 | 0.69233 | 0.668 | 0.36869 | 0.460 | 20.8636 | 137148 | 161.69 | benchmark_vanila |
| rpng | table_01 | complete | 2506 | 463 | 24.2268 | 23.41 | 0.8168 | 0.80567 | 0.750 | 0.18928 | 0.289 | 24.2550 | 207887 | 544.31 | benchmark_vanila |
| rpng | table_02 | complete | 2914 | 524 | 21.7037 | 20.84 | 0.8637 | 0.72397 | 0.654 | 0.25458 | 0.338 | 21.6630 | 282727 | 750.00 | benchmark_vanila |
| rpng | table_03 | complete | 7006 | 1307 | 21.6769 | 20.71 | 0.9669 | 0.71032 | 0.639 | 0.27183 | 0.353 | 21.6574 | 351542 | 1287.41 | benchmark_vanila |
| rpng | table_04 | complete | 6068 | 1134 | 20.7960 | 21.97 | -1.1740 | 0.70380 | 0.742 | 0.21057 | 0.247 | 20.8343 | 313542 | 1089.56 | benchmark_vanila |
| rpng | table_05 | complete | 6164 | 1166 | 20.8956 | 21.44 | -0.5444 | 0.64817 | 0.684 | 0.30095 | 0.345 | 20.9048 | 231759 | 1165.50 | benchmark_vanila |
| rpng | table_06 | complete | 2767 | 510 | 23.1418 | 23.47 | -0.3282 | 0.76840 | 0.775 | 0.24834 | 0.304 | 23.1999 | 173747 | 582.22 | benchmark_vanila |
| rpng | table_07 | complete | 4784 | 909 | 25.1673 | 24.81 | 0.3573 | 0.83816 | 0.821 | 0.18091 | 0.252 | 25.1968 | 190748 | 533.55 | benchmark_vanila |
| rpng | table_08 | complete | 8484 | 1583 | 22.1574 | 21.05 | 1.1074 | 0.76364 | 0.720 | 0.27462 | 0.383 | 22.1632 | 411981 | 1667.12 | benchmark_vanila |
| aria | aria1253 | complete | 1303 | 237 | 22.1306 | — | — | 0.73847 | — | 0.45171 | — | 22.1739 | 199656 | 253.25 | reused_exp81_82 |
| aria | aria301_305 | complete | 2688 | 501 | 23.3254 | — | — | 0.80099 | — | 0.48014 | — | 23.4245 | 235090 | 362.47 | reused_exp81_82 |

완료: **18/18**
