# 5070ti vanilla-matched-time 결과

동일 UID는 양쪽 run에서 tracking keyframe이 아닌 frame의 교집합이다.
`physical Adam`은 MAP_ONLINE_SUMMARY의 실제 B1 optimizer 완료 횟수다.

| family | scene | selector | status | scale | budget(s) | common | PSNR | vanilla | delta | SSIM delta | LPIPS delta | physical Adam | KF upd | dense upd | loop(s) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rpng | table_01 | rr | matched_pass | 4.454 | 372.08 | 463 | 23.3318 | 24.1699 | -0.8381 | -0.05825 | 0.09119 | 24138 | 10517 | 13621 | 372.16 |
| rpng | table_01 | ercb_relative_floor | matched_pass | 4.454 | 372.08 | 463 | 23.2495 | 24.1699 | -0.9204 | -0.06259 | 0.09544 | 24639 | 10654 | 13985 | 372.17 |
| rpng | table_01 | rr_workcredit_r4 | missing | 4.454 | 372.08 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_01 | ercb_relative_floor_workcredit_r4 | missing | 4.454 | 372.08 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_01 | rr_workcredit_cycle_r4 | missing | 4.454 | 372.08 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_01 | ercb_relative_floor_workcredit_cycle_r4 | missing | 4.454 | 372.08 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_01 | view_uniform_k128_workcredit_cycle_r4 | missing | 4.454 | 372.08 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_01 | ercb_view_count_b002_k128_workcredit_cycle_r4 | missing | 4.454 | 372.08 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_01 | ercb_view_count_b002_k32_workcredit_cycle_r4 | missing | 4.454 | 372.08 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_01 | ercb_view_count_b002_k8_workcredit_cycle_r4 | missing | 4.454 | 372.08 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_01 | ercb_base_workcredit_cycle_r4 | missing | 4.454 | 372.08 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_01 | ercb_coverage1_workcredit_cycle_r4 | missing | 4.454 | 372.08 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_01 | rr_workcredit_cycle_r2 | missing | 4.454 | 372.08 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_01 | ercb_relative_floor_workcredit_cycle_r2 | missing | 4.454 | 372.08 | — | — | — | — | — | — | — | — | — | — |
| utmm | fast-straight | rr | matched_pass | 2.800 | 30.91 | 61 | 17.6418 | 17.4259 | 0.2158 | 0.01082 | -0.01054 | 611 | 259 | 352 | 30.93 |
| utmm | fast-straight | ercb_relative_floor | matched_pass | 2.800 | 30.91 | 61 | 17.7496 | 17.4259 | 0.3237 | 0.01287 | -0.01416 | 673 | 277 | 396 | 30.94 |
| utmm | fast-straight | rr_workcredit_r4 | matched_pass | 2.800 | 30.91 | 61 | 17.6274 | 17.4259 | 0.2015 | 0.00655 | 0.00545 | 615 | 420 | 195 | 30.93 |
| utmm | fast-straight | ercb_relative_floor_workcredit_r4 | matched_pass | 2.800 | 30.91 | 61 | 17.6349 | 17.4259 | 0.2090 | 0.00402 | 0.00500 | 578 | 381 | 197 | 30.94 |
| utmm | fast-straight | rr_workcredit_cycle_r4 | matched_pass | 2.800 | 30.91 | 61 | 17.6317 | 17.4259 | 0.2058 | 0.00554 | 0.00598 | 612 | 426 | 186 | 30.94 |
| utmm | fast-straight | ercb_relative_floor_workcredit_cycle_r4 | matched_pass | 2.800 | 30.91 | 61 | 17.6508 | 17.4259 | 0.2248 | 0.00770 | -0.00473 | 610 | 405 | 205 | 30.94 |
| utmm | fast-straight | view_uniform_k128_workcredit_cycle_r4 | matched_pass | 2.800 | 30.91 | 61 | 17.8132 | 17.4259 | 0.3873 | 0.00991 | -0.00209 | 624 | 456 | 168 | 30.94 |
| utmm | fast-straight | ercb_view_count_b002_k128_workcredit_cycle_r4 | matched_pass | 2.800 | 30.91 | 61 | 17.8506 | 17.4259 | 0.4247 | 0.01039 | -0.00327 | 621 | 450 | 171 | 30.95 |
| utmm | fast-straight | ercb_view_count_b002_k32_workcredit_cycle_r4 | missing | 2.800 | 30.91 | — | — | — | — | — | — | — | — | — | — |
| utmm | fast-straight | ercb_view_count_b002_k8_workcredit_cycle_r4 | missing | 2.800 | 30.91 | — | — | — | — | — | — | — | — | — | — |
| utmm | fast-straight | ercb_base_workcredit_cycle_r4 | matched_pass | 2.800 | 30.91 | 61 | 17.7321 | 17.4259 | 0.3062 | 0.00785 | -0.00067 | 606 | 425 | 181 | 30.94 |
| utmm | fast-straight | ercb_coverage1_workcredit_cycle_r4 | matched_pass | 2.800 | 30.91 | 61 | 17.8005 | 17.4259 | 0.3745 | 0.00790 | -0.00545 | 620 | 432 | 188 | 30.93 |
| utmm | fast-straight | rr_workcredit_cycle_r2 | matched_pass | 2.800 | 30.91 | 61 | 17.5169 | 17.4259 | 0.0909 | 0.00572 | 0.01422 | 646 | 349 | 297 | 30.94 |
| utmm | fast-straight | ercb_relative_floor_workcredit_cycle_r2 | matched_pass | 2.800 | 30.91 | 61 | 17.5246 | 17.4259 | 0.0987 | 0.00478 | 0.00989 | 634 | 347 | 287 | 30.94 |
| utmm | ego-drive | rr | matched_pass | 3.209 | 149.65 | 264 | 20.5746 | 20.2615 | 0.3131 | 0.01679 | -0.00295 | 12981 | 5207 | 7774 | 149.71 |
| utmm | ego-drive | ercb_relative_floor | matched_pass | 3.209 | 149.65 | 264 | 20.1762 | 20.2615 | -0.0854 | 0.00315 | 0.01525 | 13603 | 5449 | 8154 | 149.71 |
| utmm | ego-drive | rr_workcredit_r4 | missing | 3.209 | 149.65 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-drive | ercb_relative_floor_workcredit_r4 | missing | 3.209 | 149.65 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-drive | rr_workcredit_cycle_r4 | missing | 3.209 | 149.65 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-drive | ercb_relative_floor_workcredit_cycle_r4 | missing | 3.209 | 149.65 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-drive | view_uniform_k128_workcredit_cycle_r4 | missing | 3.209 | 149.65 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-drive | ercb_view_count_b002_k128_workcredit_cycle_r4 | missing | 3.209 | 149.65 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-drive | ercb_view_count_b002_k32_workcredit_cycle_r4 | missing | 3.209 | 149.65 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-drive | ercb_view_count_b002_k8_workcredit_cycle_r4 | missing | 3.209 | 149.65 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-drive | ercb_base_workcredit_cycle_r4 | missing | 3.209 | 149.65 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-drive | ercb_coverage1_workcredit_cycle_r4 | missing | 3.209 | 149.65 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-drive | rr_workcredit_cycle_r2 | missing | 3.209 | 149.65 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-drive | ercb_relative_floor_workcredit_cycle_r2 | missing | 3.209 | 149.65 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-centric-1 | rr | missing | 1.787 | 91.41 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-centric-1 | ercb_relative_floor | missing | 1.787 | 91.41 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-centric-1 | rr_workcredit_r4 | missing | 1.787 | 91.41 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-centric-1 | ercb_relative_floor_workcredit_r4 | missing | 1.787 | 91.41 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-centric-1 | rr_workcredit_cycle_r4 | matched_pass | 1.787 | 91.41 | 297 | 19.7320 | 17.1679 | 2.5641 | 0.10357 | -0.03112 | 4058 | 2849 | 1209 | 91.44 |
| utmm | ego-centric-1 | ercb_relative_floor_workcredit_cycle_r4 | matched_pass | 1.787 | 91.41 | 297 | 19.3168 | 17.1679 | 2.1489 | 0.08874 | -0.00830 | 4198 | 2660 | 1538 | 91.45 |
| utmm | ego-centric-1 | view_uniform_k128_workcredit_cycle_r4 | matched_pass | 1.787 | 91.41 | 297 | 19.1895 | 17.1679 | 2.0216 | 0.08004 | -0.00167 | 3918 | 2928 | 990 | 91.44 |
| utmm | ego-centric-1 | ercb_view_count_b002_k128_workcredit_cycle_r4 | matched_pass | 1.787 | 91.41 | 297 | 19.5074 | 17.1679 | 2.3396 | 0.09588 | -0.02448 | 3894 | 2890 | 1004 | 91.44 |
| utmm | ego-centric-1 | ercb_view_count_b002_k32_workcredit_cycle_r4 | matched_pass | 1.787 | 91.41 | 297 | 18.4489 | 17.1679 | 1.2810 | 0.06902 | 0.01252 | 4069 | 2829 | 1240 | 91.45 |
| utmm | ego-centric-1 | ercb_view_count_b002_k8_workcredit_cycle_r4 | matched_pass | 1.787 | 91.41 | 297 | 18.8705 | 17.1679 | 1.7026 | 0.07924 | 0.00974 | 4023 | 2559 | 1464 | 91.45 |
| utmm | ego-centric-1 | ercb_base_workcredit_cycle_r4 | missing | 1.787 | 91.41 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-centric-1 | ercb_coverage1_workcredit_cycle_r4 | matched_pass | 1.787 | 91.41 | 297 | 19.2421 | 17.1679 | 2.0742 | 0.08777 | -0.01176 | 4002 | 2943 | 1059 | 91.44 |
| utmm | ego-centric-1 | rr_workcredit_cycle_r2 | missing | 1.787 | 91.41 | — | — | — | — | — | — | — | — | — | — |
| utmm | ego-centric-1 | ercb_relative_floor_workcredit_cycle_r2 | missing | 1.787 | 91.41 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_04 | rr | missing | 4.126 | 834.77 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_04 | ercb_relative_floor | missing | 4.126 | 834.77 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_04 | rr_workcredit_r4 | missing | 4.126 | 834.77 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_04 | ercb_relative_floor_workcredit_r4 | missing | 4.126 | 834.77 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_04 | rr_workcredit_cycle_r4 | missing | 4.126 | 834.77 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_04 | ercb_relative_floor_workcredit_cycle_r4 | missing | 4.126 | 834.77 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_04 | view_uniform_k128_workcredit_cycle_r4 | missing | 4.126 | 834.77 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_04 | ercb_view_count_b002_k128_workcredit_cycle_r4 | missing | 4.126 | 834.77 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_04 | ercb_view_count_b002_k32_workcredit_cycle_r4 | missing | 4.126 | 834.77 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_04 | ercb_view_count_b002_k8_workcredit_cycle_r4 | missing | 4.126 | 834.77 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_04 | ercb_base_workcredit_cycle_r4 | missing | 4.126 | 834.77 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_04 | ercb_coverage1_workcredit_cycle_r4 | missing | 4.126 | 834.77 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_04 | rr_workcredit_cycle_r2 | missing | 4.126 | 834.77 | — | — | — | — | — | — | — | — | — | — |
| rpng | table_04 | ercb_relative_floor_workcredit_cycle_r2 | missing | 4.126 | 834.77 | — | — | — | — | — | — | — | — | — | — |
