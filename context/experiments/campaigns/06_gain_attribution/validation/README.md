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
