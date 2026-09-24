# Exp116 — LPM significant-zone mass prior

The source-derived prior is `q=(active_pixels+256)/(H*W+256)`,
where 256 pixels are exactly one official 16x16 LPM patch.
No learned/tuned multiplier or additional physical work is used.

| Arm | PSNR | Delta | SSIM | LPIPS | Trace rows changed | Renders | Adam | GS | Wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| normalized_control | 21.228466 | +0.000000 | 0.716368 | 0.339916 | 0 | 9345 | 757 | 120088 | 39.779 |
| lpm_mass_normalized | 21.219499 | -0.008967 | 0.716082 | 0.340907 | 3 | 9345 | 757 | 120106 | 40.298 |
| lpm_mass_rr | 21.231555 | +0.003089 | 0.716271 | 0.340798 | 10 | 9345 | 757 | 120113 | 39.772 |

Gate: **PASS**.
