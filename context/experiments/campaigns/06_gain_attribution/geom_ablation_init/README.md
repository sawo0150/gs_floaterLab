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
