# 5070ti_1.5x_strict 결과

Local held-out은 evaluator의 `idx % 5 == 0 + keyframe + last` 중 실제 vanilla keyframe을 제외한 view다.
`physical Adam`은 batch나 render 수가 아니라 완료된 Gaussian optimizer step의 실제 횟수다.

| family | scene | status | processed | drop | held-out PSNR | SSIM | LPIPS | physical Adam | updates late | mutations late | track late(s) | GS |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| aria | aria1253 | map_strict_tracking_late | 599/1303 | 704 | 24.2860 | 0.77428 | 0.42949 | 627 | 0 | 0 | 0.493 | 222568 |
| aria | aria1253rot | failed_incomplete | —/— | — | — | — | — | — | — | — | — | — |
| aria | aria301_12F | map_strict_tracking_late | 414/2201 | 1787 | 19.1974 | 0.71122 | 0.57982 | 1064 | 0 | 0 | 0.006 | 675009 |
| aria | aria301_305 | map_strict_tracking_late | 1904/2688 | 784 | 22.1741 | 0.77883 | 0.53072 | 1378 | 0 | 0 | 0.129 | 237403 |
| utmm | ego-centric-1 | map_strict_tracking_late | 1125/1535 | 410 | 16.9769 | 0.57333 | 0.46410 | 446 | 0 | 0 | 0.005 | 103224 |
| utmm | ego-centric-2 | map_strict_tracking_late | 632/1298 | 666 | 19.5966 | 0.65777 | 0.42504 | 608 | 0 | 0 | 0.224 | 83984 |
| utmm | ego-drive | map_strict_tracking_late | 625/1399 | 774 | 19.6320 | 0.62780 | 0.43627 | 703 | 0 | 0 | 0.006 | 117355 |
| utmm | fast-straight | map_strict_tracking_late | 153/332 | 179 | 16.6031 | 0.54923 | 0.59620 | 114 | 0 | 0 | 0.184 | 27517 |
| utmm | slow-straight-1 | map_strict_tracking_late | 299/393 | 94 | 18.9604 | 0.60173 | 0.51733 | 151 | 0 | 0 | 0.005 | 33095 |
| utmm | slow-straight-2 | map_strict_tracking_late | 402/597 | 195 | 18.0110 | 0.64906 | 0.52048 | 232 | 0 | 0 | 0.232 | 33044 |
| utmm | square-1 | map_strict_tracking_late | 1040/1614 | 574 | 18.3141 | 0.60600 | 0.46433 | 796 | 0 | 0 | 0.959 | 130061 |
| utmm | square-2 | map_strict_tracking_late | 675/1219 | 544 | 17.6157 | 0.57568 | 0.51484 | 711 | 0 | 0 | 0.080 | 116295 |
| rpng | table_01 | map_strict_tracking_late | 354/2506 | 2152 | 22.1438 | 0.69878 | 0.33193 | 953 | 0 | 0 | 0.007 | 173109 |
| rpng | table_02 | failed_incomplete | —/— | — | — | — | — | — | — | — | — | — |
| rpng | table_03 | map_strict_tracking_late | 1243/7006 | 5763 | 14.9821 | 0.36061 | 0.68458 | 2373 | 0 | 0 | 0.006 | 307927 |
| rpng | table_04 | map_strict_tracking_late | 968/6068 | 5100 | 22.1662 | 0.74156 | 0.22819 | 1824 | 0 | 0 | 0.005 | 234904 |
| rpng | table_05 | map_strict_tracking_late | 1041/6164 | 5123 | 22.1461 | 0.74854 | 0.25104 | 1525 | 0 | 0 | 0.021 | 206285 |
| rpng | table_06 | map_strict_tracking_late | 354/2767 | 2413 | 19.7719 | 0.66713 | 0.35856 | 799 | 0 | 0 | 0.006 | 145321 |
| rpng | table_07 | missing | —/— | — | — | — | — | — | — | — | — | — |
| rpng | table_08 | missing | —/— | — | — | — | — | — | — | — | — | — |

고정 deadline map/zero-tail 완료: **16/20**; end-to-end strict 통과: **0/20**

## Family averages

| family | scenes | PSNR | SSIM | LPIPS | physical Adam |
|---|---:|---:|---:|---:|---:|
| aria | 3 | 21.8858 | 0.75477 | 0.51334 | 1023.0 |
| utmm | 8 | 18.2137 | 0.60508 | 0.49232 | 470.1 |
| rpng | 5 | 20.2420 | 0.64333 | 0.37086 | 1494.8 |
