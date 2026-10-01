# Fixed40 measured comparison

Completed maps: 24/24. Mapper seeds 0 and 1 on the same frozen tracker; arithmetic means below.

A = KF RGB+depth; B = KF RGB+depth + dense RGB; C = KF RGB+depth + dense RGB+depth.

All depths: metric L1, weight 0.25. Normal losses off. Causal frozen tracker replay, 40 single-view updates/KF; not a real-time deadline test.

## Held-out appearance

| Scene | Arm | n | PSNR mean [min, max] dB ↑ | SSIM ↑ | LPIPS ↓ | GS count |
|---|---|---:|---:|---:|---:|---:|
| aria1253 | A | 2 | 24.822 [24.818, 24.826] | 0.8074 | 0.3409 | 205624 |
| aria1253 | B | 2 | 25.791 [25.780, 25.801] | 0.8573 | 0.2537 | 199871 |
| aria1253 | C | 2 | 25.725 [25.719, 25.730] | 0.8559 | 0.2559 | 198620 |
| table_06 | A | 2 | 24.763 [24.740, 24.786] | 0.8298 | 0.1659 | 222082 |
| table_06 | B | 2 | 25.000 [24.976, 25.024] | 0.8526 | 0.1407 | 209312 |
| table_06 | C | 2 | 24.908 [24.887, 24.928] | 0.8508 | 0.1436 | 209812 |
| square-1 | A | 2 | 21.106 [21.099, 21.112] | 0.7221 | 0.3233 | 122597 |
| square-1 | B | 2 | 21.868 [21.859, 21.877] | 0.7639 | 0.2751 | 123755 |
| square-1 | C | 2 | 21.652 [21.641, 21.664] | 0.7564 | 0.2838 | 121910 |
| aria1253rot | A | 2 | 24.479 [24.442, 24.515] | 0.8043 | 0.3408 | 212334 |
| aria1253rot | B | 2 | 25.075 [24.999, 25.151] | 0.8538 | 0.2569 | 200442 |
| aria1253rot | C | 2 | 24.975 [24.916, 25.035] | 0.8522 | 0.2585 | 198000 |

## Paired PSNR effects

| Scene | B − A dB | C − B dB | C − A dB |
|---|---:|---:|---:|
| aria1253 | +0.969 | -0.066 | +0.903 |
| table_06 | +0.237 | -0.092 | +0.145 |
| square-1 | +0.762 | -0.216 | +0.547 |
| aria1253rot | +0.597 | -0.100 | +0.497 |

## Common geometry: held-out tracker depth agreement

**Auxiliary, not independent GT.** MAE is in tracker metric coordinates; front/within/behind use ±6.25% bands and alpha ≥0.95. Holes use alpha ≤0.9. Fractions below are percentages.

| Scene | Arm | MAE m ↓ | Front % ↓ | Within % ↑ | Behind % ↓ | Holes % ↓ |
|---|---|---:|---:|---:|---:|---:|
| aria1253 | A | 0.1819 | 23.09 | 63.77 | 13.14 | 3.45 |
| aria1253 | B | 0.1901 | 26.66 | 60.88 | 12.46 | 2.07 |
| aria1253 | C | 0.1782 | 22.28 | 64.73 | 12.99 | 1.95 |
| table_06 | A | 0.1497 | 9.33 | 83.00 | 7.67 | 1.22 |
| table_06 | B | 0.1552 | 9.61 | 81.84 | 8.55 | 1.06 |
| table_06 | C | 0.1494 | 8.95 | 83.03 | 8.02 | 0.98 |
| square-1 | A | 0.5364 | 26.29 | 56.58 | 17.13 | 10.58 |
| square-1 | B | 0.5490 | 29.40 | 54.18 | 16.42 | 10.52 |
| square-1 | C | 0.5316 | 27.64 | 56.27 | 16.09 | 10.75 |
| aria1253rot | A | 0.2062 | 23.09 | 60.21 | 16.70 | 1.67 |
| aria1253rot | B | 0.2147 | 25.69 | 58.32 | 15.99 | 1.40 |
| aria1253rot | C | 0.2050 | 22.52 | 61.18 | 16.30 | 1.37 |

## Independent MPS termination distribution (Aria only)

Evaluation-only semidense MPS with local 30-KF Sim(3). Front/behind mass are normalized accumulated opacity on opaque rays; surface band ±6.25%. Lower front mass alone is insufficient if behind mass grows.

| Scene | Arm | Front mass % ↓ | Surface mass % ↑ | Behind mass % ↓ | Holes % ↓ | Local alignment RMS median m |
|---|---|---:|---:|---:|---:|---:|
| aria1253 | A | 17.40 | 66.25 | 16.35 | 3.41 | 0.0073 |
| aria1253 | B | 18.11 | 67.15 | 14.73 | 2.92 | 0.0073 |
| aria1253 | C | 15.43 | 68.98 | 15.60 | 2.65 | 0.0073 |
| aria1253rot | A | 16.04 | 66.73 | 17.23 | 1.47 | 0.0080 |
| aria1253rot | B | 16.42 | 68.00 | 15.59 | 1.43 | 0.0080 |
| aria1253rot | C | 14.82 | 68.72 | 16.46 | 1.38 | 0.0080 |

## Independent MPS mean-depth agreement

Semidense reference points, same projection/alignment for all arms. These mean-depth classes supplement the termination distribution above.

| Scene | Arm | Median absolute relative error % ↓ | Front % ↓ | Within % ↑ | Behind % ↓ |
|---|---|---:|---:|---:|---:|
| aria1253 | A | 3.41 | 17.22 | 69.43 | 13.35 |
| aria1253 | B | 3.41 | 18.66 | 69.68 | 11.65 |
| aria1253 | C | 2.98 | 14.41 | 73.24 | 12.35 |
| aria1253rot | A | 3.13 | 13.61 | 72.21 | 14.18 |
| aria1253rot | B | 3.09 | 15.20 | 72.77 | 12.04 |
| aria1253rot | C | 2.89 | 12.29 | 74.69 | 13.02 |

## Independent manual empty-space region (aria1253)

Mean Gaussian count at opacity >0.3 and opacity-weighted support in the annotated empty region. Erosion/dilation and registration residual are retained to expose alignment sensitivity.

| Arm | Eroded count ↓ | Nominal count ↓ | Dilated count ↓ | Nominal opacity support ↓ | Alignment p90 m |
|---|---:|---:|---:|---:|---:|
| A | 53.5 | 168.5 | 583.0 | 190.28 | 0.0384 |
| B | 55.5 | 165.5 | 556.5 | 196.49 | 0.0384 |
| C | 46.5 | 146.0 | 511.0 | 174.40 | 0.0384 |

## Budget and depth coverage

| Scene | Arm | Updates | KF updates | Dense updates | Dense target coverage % | Mapping seconds* |
|---|---|---:|---:|---:|---:|---:|
| aria1253 | A | 4760 | 4760 | 0 | — | 17.44 |
| aria1253 | B | 4760 | 2467 | 2293 | — | 27.99 |
| aria1253 | C | 4760 | 2467 | 2293 | 37.36 | 30.49 |
| table_06 | A | 9080 | 9080 | 0 | — | 62.60 |
| table_06 | B | 9080 | 4635 | 4445 | — | 88.74 |
| table_06 | C | 9080 | 4635 | 4445 | 53.38 | 92.12 |
| square-1 | A | 3600 | 3600 | 0 | — | 27.17 |
| square-1 | B | 3600 | 1886 | 1714 | — | 32.90 |
| square-1 | C | 3600 | 1886 | 1714 | 35.65 | 33.94 |
| aria1253rot | A | 6120 | 6120 | 0 | — | 28.93 |
| aria1253rot | B | 6120 | 3114 | 3006 | — | 45.79 |
| aria1253rot | C | 6120 | 3114 | 3006 | 34.29 | 48.06 |

*Replay mapper time excludes tracking and evaluation; descriptive only, not an end-to-end real-time claim.

PLY files are symlinks to preserved raw results. Per-run values and source paths: `comparison.csv` and `comparison.json`.
