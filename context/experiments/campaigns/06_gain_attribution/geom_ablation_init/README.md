# Content-aware insertion (I) on other datasets — PREREG (2026-10-09, user approved: 4 datasets, 6 scenes)

**Why.** In the local TUM10 ablation R1→R1-I was ≈0 on PSNR (+0.01) with −10% Gaussians. Earlier evidence: exp55 (Aria
1253) content-adaptive birth gave −35% Gaussians at equal or slightly better PSNR; exp78-B (RPNG table_01) online-rank birth
alone −0.01 dB. Question: is I's effect dataset-dependent (TUM vs Aria/UTMM/RPNG/ETH3D), on quality and on Gaussian count?
**Setup.** Same geometry-ablation harness snapshot (local copy; colin untouched), seed 0, 6N. Arms per scene: R4 (C geometry,
captures the frontend tape), R1 vs R1-I (KF window base), R2 vs R2-I (KF-pool base; colin's original R2 definition).
Scenes: ETH3D sofa_1 (pilot, with R4 replay validation), Aria 0416_301-1253 and 0416_301-305, UTMM square-1 (author
reference 6N inputs), RPNG table_01 and table_06. 31 runs. Scenes that exceed 16 GB are reported, not retried.
Local harness changes: `ablation_support.PLAN` overridable via ABLATION_PLAN; `run_suite_init.py` (arm order R4, R1, R1-I,
R2, R2-I; trials grouped by dataset). Output `results/campaigns/gain_attribution/geom_ablation_init/v1/`, profile
`rtx5070ti_geom_init.json` (UTMM 6N inputs and raw frames mapped; local UTMM/RPNG frames match colin by count and hash).
**Read-out.** Per scene and mean: R1-I − R1 and R2-I − R2 for PSNR/SSIM/LPIPS/depth MAE and Gaussian count.

## Result (2026-10-09)
Training finished for all arms on 5 scenes. The suite marked Aria/RPNG runs "failed" only because its stage evaluator
asserts TUM-style depth GT (`views_with_depth > 0`); the image-quality evaluation (evaluation/quality.json: PSNR/SSIM/LPIPS,
Gaussians) completed before the assert and is used here (no depth metrics for these scenes). UTMM square-1 is not supported
by this frontend ("IMU sensor convention not verified for utmm") → skipped.
| scene | R1 → R1-I: PSNR / SSIM / LPIPS / Gaussians | R2 → R2-I: PSNR / SSIM / LPIPS / Gaussians |
|---|---|---|
| Aria 0416_301-1253 | +0.12 / +0.009 / −0.006 / −2.8% | +0.12 / +0.008 / −0.013 / −4.9% |
| Aria 0416_301-305 | +0.02 / +0.006 / +0.004 / −17.3% | −0.07 / +0.004 / +0.000 / −18.3% |
| ETH3D sofa_1 | +0.24 / +0.005 / −0.007 / −15.9% | +0.09 / +0.003 / −0.004 / −20.3% |
| RPNG table_01 | +0.02 / +0.004 / +0.014 / −0.8% | +0.02 / +0.001 / +0.004 / −7.9% |
| RPNG table_06 | −0.25 / +0.000 / +0.006 / −1.2% | +0.02 / +0.003 / −0.003 / −9.5% |
| **mean (5)** | **+0.03 / +0.005 / +0.002 / −7.6%** | **+0.04 / +0.004 / −0.003 / −12.2%** |
| TUM10 (geom_ablation_local) | +0.01 / +0.008 / +0.006 / −10% | — |
**Reading.** I behaves the same across datasets: fewer Gaussians on every scene (−1 … −20%), SSIM up on 10/10 comparisons,
PSNR ≈ neutral (+0.03/+0.04 mean; 8/10 positive; table_06 R1 −0.25, Aria 305 R2 −0.07). The TUM result is not a dataset
artefact; it matches exp55 (equal quality, fewer Gaussians). The reduction is largest on Aria 305 and ETH3D (−16…−20%),
smallest on RPNG (−1…−10%). Single seed.
