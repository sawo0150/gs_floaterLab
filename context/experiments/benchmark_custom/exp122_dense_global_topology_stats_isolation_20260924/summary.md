# Exp122 — dense global topology-stat isolation

The stats-off arm keeps the exact unified dense RGB render, loss,
Adam step, and transactional normalized-variance selector. Only its
native radii/gradient densification-stat observation is suppressed.

| Arm | PSNR | Delta | SSIM | LPIPS | Renders | Adam | GS | Dense commits | Stats skipped | Regular added/removed/churn |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mass_normalized_control | 25.582787 | +0.000000 | 0.847447 | 0.153699 | 38302 | 3030 | 417947 | 0 | 0 | 31857/80205/112062 |
| unified_stats_on | 25.410318 | -0.172469 | 0.840008 | 0.163926 | 38302 | 3030 | 418972 | 1610 | 0 | 33476/80790/114266 |
| unified_stats_off | 25.424374 | -0.158413 | 0.840737 | 0.163894 | 38302 | 3030 | 417690 | 1610 | 210 | 31773/80371/112144 |

Corrected v2 gate: **PASS**.

## Verification correction

The original v1 verifier incorrectly compared skipped topology
statistics with all 1,610 dense commits. final-v7 accepts native
densification statistics only in `frontier`; the locked ledger has
210 such committed dense views, and
stats-off skipped exactly 210.
No mapping or evaluation output was rerun.

Stats-off recovered only **+0.014056 dB** over stats-on (8.15% of the stats-on gap).
Thus dense topology statistics explain little of the RPNG loss;
the RGB-D historical-KF to RGB-only dense-view replacement remains
the primary isolated cause.
