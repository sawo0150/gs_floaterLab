# Merged-main D3 validation — 2026-09-30

Four fresh D3 runs and four fresh official-vanilla runs; each saved map evaluated twice.
Original native fixed40 PSNR below is the previous main validation, not a newly run native control.

| Scene | Previous native | Fresh D3 | Fresh vanilla | D3 gain | D3 − previous native |
|---|---:|---:|---:|---:|---:|
| aria1253 | 25.776 | 25.749 | 20.872 | +4.877 | -0.027 |
| table_06 | 25.224 | 25.128 | 22.679 | +2.450 | -0.095 |
| square-1 | 22.285 | 22.094 | 18.872 | +3.222 | -0.191 |
| aria1253rot | 25.018 | 24.985 | 21.830 | +3.155 | -0.033 |

| Scene | Main training renders (each) | D3 extra proxy renders | D3 / vanilla seconds | D3 / vanilla GS |
|---|---:|---:|---:|---:|
| aria1253 | 4760 | 2467 | 37.98 / 25.04 | 194252 / 190502 |
| table_06 | 9080 | 4635 | 100.68 / 78.79 | 224067 / 233981 |
| square-1 | 3600 | 1886 | 36.95 / 34.35 | 122774 / 163120 |
| aria1253rot | 6120 | 3114 | 54.02 / 39.66 | 190326 / 259143 |

Same frozen causal inputs, per-arrival 40 training renders/KF, trajectories and held-out cohorts were checked.
D3 adds proxy renders and an additional backward traversal, so this is not an equal-total-work comparison.
Times are single-run mapping measurements, not concurrent tracking FPS or isolated D3 cost.
D3 and the raster fixes were enabled together; their separate effects are not identified here.
No new independent ground-truth geometry evaluation was performed. Maintenance and density overrides remain untested in this panel.

Main tested: `a2f3f62bab4060e2594b659a1bf7e832fcfe3684`. Raw results: `/home/intern/gs_floaterLab/results/campaigns/gain_attribution/geometry_main_validation/gpu_v1`.
Mean gain over fresh vanilla: **+3.426 dB**. Mean change from prior native: **-0.087 dB**.
