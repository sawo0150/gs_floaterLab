# Validation of the online fixes — phase 1 result (2026-10-09, 6 scenes, seed 0, ERVS K16)

Final-map held-out PSNR (the first B′ attempt failed on a no_grad bug, rerun with approval; giant = scale > 0.3 & opacity > 0.3):
| scene | A adopted (clamp 0.1) | B clamp off | giant / max scale | B′ cap 0.5 | giant / max scale |
|---|---:|---:|---|---:|---|
| square-1 | 21.98 | 21.92 (−0.06) | 2,707 / 14.1 | 22.02 (+0.04) | 2,434 / 0.60 |
| aria1253 | 24.85 | 25.32 (+0.47) | 395 / 5.7 | 25.38 (+0.53) | 421 / 0.64 |
| aria1253rot | 24.70 | 25.50 (+0.80) | 980 / 10.5 | 25.55 (+0.85) | 984 / 0.60 |
| table_06 | 24.78 | 24.83 (+0.05) | 454 / 3.0 | 24.83 (+0.06) | 434 / 0.55 |
| ego-drive | 20.81 | 20.81 (−0.00) | 3,182 / 12.9 | 20.84 (+0.02) | 2,845 / 0.50 |
| Retail_Street | 26.74 | 27.03 (+0.29) | 4,999 / 9.8 | 27.05 (+0.32) | 4,608 / 0.63 |
| **mean** | 23.98 | 24.24 (+0.26, 4/6) | | **24.28 (+0.30, 6/6)** | |
**Size-setting rule (PREREG):** B′ − B = +0.045 dB (< 0.05) → **cap 0.5** is selected (it is also higher on every
scene and bounds the maximum scale at ~0.6 instead of up to 14). Phase 2 is on hold (user); the free-space gate is paused.

## Phase 2 result — cap 0.5 + selective births 0.5/0.02 (2026-10-09, 6 valid runs)
| scene | A adopted | B′ cap 0.5 | **C cap 0.5 + selective** | C − A | C − B′ | offline |
|---|---:|---:|---:|---:|---:|---:|
| square-1 | 21.98 | 22.02 | 21.99 | +0.02 | −0.03 | 22.72 |
| aria1253 | 24.85 | 25.38 | **25.83** | +0.98 | +0.44 | 26.90 |
| aria1253rot | 24.70 | 25.55 | **25.69** | +0.99 | +0.14 | 26.75 |
| table_06 | 24.78 | 24.83 | 24.77 | −0.00 | −0.06 | 25.20 |
| ego-drive | 20.81 | 20.84 | 20.83 | +0.02 | −0.00 | 22.04 |
| Retail_Street | 26.74 | 27.05 | **27.14** | +0.40 | +0.09 | 28.40 |
| **mean** | 23.98 | 24.28 | **24.38** | **+0.40 (5/6)** | +0.10 (3/6) | 25.33 |
Selective births add +0.10 on average over cap 0.5, all of it on the revisit / long scenes (aria1253 +0.44,
aria1253rot +0.14, Retail_Street +0.09); neutral elsewhere (−0.06…−0.03, within single-seed noise). The combination
closes ~30% of the online−offline gap on average (1.36 → 0.96 dB). Seed 0 only.
