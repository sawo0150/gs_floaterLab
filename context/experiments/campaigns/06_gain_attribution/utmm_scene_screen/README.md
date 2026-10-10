# UTMM scene screen: content-aware insertion vs uniform across birth density — PREREG (2026-10-10, user approved)

**Question.** On which UTMM scenes, and at which birth density, does content-aware insertion (I, R2-I) reach the PSNR of
uniform insertion at default density (R2@1) with far fewer Gaussians? Goal (user): fewer Gaussians and higher PSNR on UTMM,
first per scene, then across all of UTMM.
**Why UTMM.** In `geom_ablation_density` square-1 was the only scene with a PSNR gain from I (+0.09…+0.24 dB) and the most
capacity-limited (¼ density −1.0 dB). Image analysis (`content_concentration.py`, no GPU, 40 frames per scene,
`results/campaigns/gain_attribution/utmm_scene_screen/content_concentration.json`): all 8 UTMM scenes have concentrated
detail (Sobel Gini 0.66–0.71, flat share 55–63 %), ego-centric-1/2 the most; RPNG 0.54–0.59 and ETH3D 0.51 are spread out.
TUM is also concentrated (0.69) but showed no I effect, so concentration alone is not enough.
**Design.** 8 UTMM scenes (author-reference inputs), 2N, KF-pool base. Arms: R4 (tape capture), R2@s and R2-I@s for
s ∈ {0.5, 0.75, 1, 1.5}; pilot replay validation on square-1. 73 runs (~45 s each). Seed 0.
Harness: local copy, `run_suite_utmm.py` (arm order only); env ABLATION_ALLOW_NO_DEPTH=1,
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True. Output `results/campaigns/gain_attribution/utmm_scene_screen/2N/`.
**Read-out.** Per scene: Gaussian count vs PSNR curves for R2 and R2-I; the smallest-Gaussian R2-I arm with PSNR ≥ R2@1;
LPIPS reported alongside.
