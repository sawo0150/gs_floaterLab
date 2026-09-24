# Exp123 — dense replacement geometry-mass isolation

Both unified arms suppress dense-origin native topology statistics.
The candidate alone rescales remaining RGB-D depth/normal terms by
`(D+1)/D`; it adds no render, Adam step, or paper-method component.

| Arm | PSNR | Delta | SSIM | LPIPS | Render | Adam | GS | Dense commits | Geometry steps/mean scale | Churn |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mass_normalized_control | 25.561123 | +0.000000 | 0.847250 | 0.153962 | 38302 | 3030 | 417930 | 0 | 0 / 1.000000 | 111850 |
| unified_stats_off | 25.434710 | -0.126413 | 0.840641 | 0.163971 | 38302 | 3030 | 417848 | 1610 | 0 / 1.000000 | 112137 |
| unified_stats_off_geometry_mass | 25.412915 | -0.148208 | 0.839953 | 0.164555 | 38302 | 3030 | 417785 | 1610 | 1610 / 1.062575 | 112353 |

Recovery: **-0.021795 dB** (**-17.24%** of the stats-off gap).
Predeclared diagnosis: `view_specific_geometry_coverage_dominates`.
Gate: **PASS**.
