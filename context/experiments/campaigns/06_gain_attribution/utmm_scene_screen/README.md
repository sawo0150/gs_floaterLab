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

## Result (2026-10-10) — 5 of 8 scenes; pilot passed
fast-straight, slow-straight-1, slow-straight-2 produced no map: the frontend kept "Deferring GS mapping until causal online
IMU metric initialization completes" to the end (straight-line motion; 0 renders → QuotaError). Not a harness issue.
ΔPSNR / ΔGaussians vs uniform at density 1 (U1); I = R2-I:
| scene | U1 PSNR, Gaussians | U0.5 | I0.5 | U0.75 | **I0.75** | I1 | U1.5 | I1.5 |
|---|---|---|---|---|---|---|---|---|
| square-1 | 18.60, 139k | −0.33/−49% | −0.22/−57% | −0.09/−24% | **+0.01/−37%** | +0.10/−16% | +0.11/+49% | +0.19/+24% |
| square-2 | 19.10, 125k | −0.27/−49% | −0.02/−54% | −0.09/−25% | **+0.13/−32%** | +0.20/−10% | +0.12/+49% | +0.27/+35% |
| ego-centric-1 | 19.51, 98k | −0.29/−49% | −0.06/−51% | −0.10/−24% | **+0.08/−28%** | +0.17/−4% | +0.12/+49% | +0.27/+42% |
| ego-centric-2 | 19.83, 109k | −0.30/−49% | −0.08/−53% | −0.14/−25% | **+0.10/−30%** | +0.18/−7% | +0.15/+49% | +0.30/+39% |
| ego-drive | 18.23, 137k | −0.10/−48% | −0.01/−55% | −0.03/−24% | **+0.04/−34%** | +0.07/−13% | +0.02/+49% | +0.10/+29% |
| mean (ΔSSIM, ΔLPIPS) | | −0.26/−49% (−.012, +.047) | −0.08/−54% (−.004, +.021) | −0.09/−24% (−.004, +.019) | **+0.07/−32% (+.004, −.008)** | +0.14/−10% (+.009, −.026) | +0.11/+49% (+.005, −.026) | +0.23/+34% (+.014, −.048) |
**Reading.** On every UTMM scene that maps, I at density 0.75 beats uniform at density 1 on PSNR (+0.01…+0.13), SSIM and
LPIPS with 28–37 % fewer Gaussians; at every density I lies above the uniform count–PSNR curve (I1 vs U1.5: +0.04 dB with
−40 % Gaussians on average). The gain is consistent but moderate (≈0.1–0.2 dB at matched count), not "far fewer and much
better". Seed 0 only.
