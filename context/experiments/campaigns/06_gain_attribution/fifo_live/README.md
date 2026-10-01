# Actual tracking + bounded FIFO mapping, sensor time 1x/1.5x

2026-09-30 user-authorized final protocol:
- Actual RGB+IMU tracking and mapping run concurrently on RTX5090; no stored tracking packets/poses/depths.
- 1x = sensor-duration budget; 1.5x = 1.5 times that duration (60s -> 90s).
- Four scenes: Aria1253, RPNG table_06, UTMM square-1, Aria1253rot; seed0.
- Official tracker frontend4/2; IMU pose prediction20 for Aria/RPNG,15 for UTMM. Map after IMU metric initialization.
- Ours: merged main + D3/fixed raster/warp, 40 renders/KF unchanged, unified3:3:6, full-history ERVS, kappa16/tau4, birth.8/prune.1/300. No maintenance/density overrides.
- Vanilla: official source with budget/heldout/finite-depth safety adapters; native losses and grouping.
- FIFO capacity2 ordinary pending packets; evict oldest pending only. Reset/rescale/PGBA are protected FIFO barriers, excluded from eviction capacity. Learning pools unchanged.
- Common .5s admission reserve before sensor deadline; close without draining optimization at EOS.
- Warm model/engine load outside stream, all frame processing and map initialization inside stream.
- Final map immutable before evaluation-only trajectory filling from this run's tracker. Evaluate heldout twice.
- Report quality separately from timing: all frames completed does not imply real-time. Report elapsed tracking time, lag, drop counts, completed renders, deadline overruns.
- Earlier frozen FIFO pilot is not live evidence; its D3 queue test passed but vanilla dedicated-stream attempt failed with CUDA error. Official raster uses legacy stream; live vanilla uses its original default stream.

2026-09-30 live FIFO 1.0x aria/ours: PSNR=23.283798996728795, execution=True, tracking=69.41958943894133s / budget=65.09999891300004s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/aria/ours

2026-09-30 live FIFO 1.0x aria/vanilla: PSNR=20.065057652597208, execution=True, tracking=65.5566164997872s / budget=65.09999891300004s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/aria/vanilla

2026-09-30 live FIFO 1.5x aria/ours: PSNR=25.77303850013791, execution=True, tracking=97.67256407812238s / budget=97.64999836950005s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/aria/ours

2026-09-30 live FIFO 1.5x aria/vanilla: PSNR=21.16782244835191, execution=True, tracking=97.67272765398957s / budget=97.64999836950005s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/aria/vanilla

2026-09-30 live FIFO 1.5x rpng/ours: PSNR=24.98133297138386, execution=True, tracking=142.05981872300617s / budget=138.367005944252s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/rpng/ours

2026-09-30 live FIFO 1.5x rpng/vanilla: PSNR=21.142978231756537, execution=True, tracking=169.3865443880204s / budget=138.367005944252s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/rpng/vanilla

2026-09-30 live FIFO 1.5x utmm/ours: PSNR=21.098959104514417, execution=True, tracking=80.88742585689761s / budget=80.71412551403046s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/utmm/ours

2026-09-30 live FIFO 1.5x utmm/vanilla: PSNR=18.58018343536942, execution=True, tracking=80.8669381190557s / budget=80.71412551403046s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/utmm/vanilla

2026-09-30 live FIFO 1.5x rot/ours: PSNR=24.75129418920298, execution=True, tracking=116.03360276599415s / budget=113.99999981249994s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/rot/ours

2026-09-30 live FIFO 1.5x rot/vanilla: PSNR=21.61899426569704, execution=True, tracking=114.02218396705575s / budget=113.99999981249994s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/rot/vanilla

2026-09-30 live FIFO 1.0x rpng/ours: PSNR=24.12675006282222, execution=True, tracking=124.73897861503065s / budget=92.24467062950134s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/rpng/ours

2026-09-30 live FIFO 1.0x rpng/vanilla: PSNR=20.861975919018995, execution=True, tracking=151.89595809811726s / budget=92.24467062950134s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/rpng/vanilla

2026-09-30 live FIFO 1.0x utmm/ours: PSNR=21.17349331761584, execution=True, tracking=54.335821729153395s / budget=53.80941700935364s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/utmm/ours

2026-09-30 live FIFO 1.0x utmm/vanilla: PSNR=18.752133696167558, execution=True, tracking=54.34218886308372s / budget=53.80941700935364s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/utmm/vanilla

2026-09-30 FIFO live 해석 추가: Aria 두 시퀀스는 Tracking config가 동일하지만 RPNG/UTMM은 기존 custom motion threshold/window/radius=3.6/15/1, vanilla=2.4/25/2를 유지했다. 둘 다 frontend 반복은 실제 4/2이나, KF 수와 tracking 비용까지 다른 전체 시스템 비교다. mapper-only 인과 효과 또는 동일 tracking 비용 비교로 주장하지 않는다.

2026-09-30 live FIFO 1.0x rot/ours: PSNR=23.96086298207768, execution=True, tracking=93.42219292395748s / budget=75.99999987499996s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/rot/ours

2026-09-30 live FIFO 1.0x rot/vanilla: PSNR=21.183946256168554, execution=True, tracking=80.33240165095776s / budget=75.99999987499996s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/rot/vanilla

## Final result

2026-09-30 actual-tracking FIFO 완료: 4 scenes × 1x/1.5x × ours/vanilla = 16회, saved-map double eval 32회. 8/8 PSNR 이득 유지(mean +2.920/+3.524dB). Mapper optimizer tail=0이나 tracking 지연으로 전조건 realtime 달성은 아님. RPNG/UTMM tracking 설정 차이를 유지한 end-to-end 비교; mapper-only 인과 주장 금지.

| Scene | Time allowance | Vanilla PSNR | Ours PSNR | Gain | Vanilla / ours tracking sec | Vanilla / ours drops |
|---|---:|---:|---:|---:|---:|---:|
| aria1253 | 1x | 20.065 | 23.284 | +3.219 | 65.56 / 69.42 | 6 / 9 |
| aria1253 | 1.5x | 21.168 | 25.773 | +4.605 | 97.67 / 97.67 | 3 / 3 |
| table_06 | 1x | 20.862 | 24.127 | +3.265 | 151.90 / 124.74 | 3 / 4 |
| table_06 | 1.5x | 21.143 | 24.981 | +3.838 | 169.39 / 142.06 | 4 / 4 |
| square-1 | 1x | 18.752 | 21.173 | +2.421 | 54.34 / 54.34 | 1 / 1 |
| square-1 | 1.5x | 18.580 | 21.099 | +2.519 | 80.87 / 80.89 | 1 / 0 |
| aria1253rot | 1x | 21.184 | 23.961 | +2.777 | 80.33 / 93.42 | 7 / 25 |
| aria1253rot | 1.5x | 21.619 | 24.751 | +3.132 | 114.02 / 116.03 | 2 / 6 |


| Scene | Allowance | Training renders V / O | Extra D3 renders | GS V / O | Input lag p95 V / O (s) |
|---|---:|---:|---:|---:|---:|
| aria1253 | 1x | 4146 / 3291 | 1676 | 247793 / 179897 | 1.888 / 5.293 |
| aria1253 | 1.5x | 4200 / 3640 | 1850 | 185946 / 184678 | 0.714 / 1.310 |
| table_06 | 1x | 4520 / 4680 | 2370 | 199454 / 171277 | 62.279 / 34.678 |
| table_06 | 1.5x | 6559 / 6640 | 3350 | 172413 / 210818 | 42.157 / 10.429 |
| square-1 | 1x | 3160 / 2040 | 1051 | 153413 / 105690 | 3.054 / 1.470 |
| square-1 | 1.5x | 3160 / 2040 | 1051 | 153373 / 105886 | 0.924 / 0.299 |
| aria1253rot | 1x | 5240 / 4560 | 2310 | 227085 / 169880 | 5.595 / 16.874 |
| aria1253rot | 1.5x | 5572 / 5480 | 2770 | 260001 / 189456 | 1.038 / 3.729 |

Main report: `/home/intern/VIGS-SLAM-custom/docs/LIVE_FIFO_COMPARISON.md`.

2026-09-30 FIFO live 검증 코드·결과 main 반영 완료: bb2d6ce48cbf668d3e910a2fa77c6cbe5d412461, origin/main 및 colin-sync/main push 확인. 기본 unbounded worker는 유지하고 max_pending_packets=2를 opt-in으로 제공; CPU 13 tests, 16 actual-tracker runs, 32 saved-map evaluations 통과.
