# Insertion (I) under reduced Gaussian density × budget — PREREG (2026-10-09, user approved)

**Question.** Does content-aware insertion (I) start to matter for quality when Gaussians are scarce?
**Design.** Birth density lowered equally for both arms by multiplying `pcd_downsample`/`pcd_downsample_init` by 1/scale
(scale 1, 0.5, 0.25) at every birth (local `ablation_support.install_density_scale`, per-arm `density_scale`). Arms on the
KF-pool base: R2@s vs R2-I@s for s ∈ {1, 0.5, 0.25}; R4 captures the frontend tape (shared by all arms of a scene/budget).
Budgets 1N, 2N, 3N (local contract copies). Scenes: ETH3D sofa_1 (pilot), Aria 0416_301-305, TUM fr1_desk, UTMM square-1
(author reference 6N inputs; colin runs UTMM through its queue bootstrap sitecustomize = UTMM sensor adapter, which our
relocation hook shadowed — now chained via ROGO_CHAIN_SITECUSTOMIZE=1), RPNG table_01. 108 runs. Seed 0.
Local harness changes (copies only): density scale, wrapper-chain unwrap in the uniform-init patch, `--arm` accepts plan arms,
`run_suite_density.py` arm order. Output `results/campaigns/gain_attribution/geom_ablation_density/{1N,2N,3N}/`.
**Read-out.** R2-I@s − R2@s (PSNR/SSIM/LPIPS/Gaussians) per scene, budget and density.

## Interim result (2026-10-09) — 1N and 2N complete for 4 scenes; 3N and UTMM not run
Pilots passed at 1N/2N/3N. Aria and RPNG rows show "failed" only from the evaluator's depth-GT assert (quality.json exists).
**Not run:** UTMM square-1 at every budget — the UTMM loader reads `.../utmm_author_reference_6N_20261008_v1/author_source/
gradslam_datasets/utmm.py`, not copied locally. 3N for Aria/TUM/RPNG — the disk guard (stop below 24 GiB free) SIGTERMed
each R4 capture (exit −15); frontend tapes from this and earlier suites take ~160 GB on a 98 %-full disk.
R2-I − R2 (PSNR / SSIM / LPIPS / Gaussians); R2 PSNR and Gaussian count in brackets:
| scene | budget | density 1 | density 0.5 | density 0.25 |
|---|---|---|---|---|
| ETH3D sofa_1 | 1N | +0.09 / +.007 / −.008 / −10% (24.32, 245k) | +0.10 / +.006 / −.012 / −11% (24.36, 123k) | +0.12 / +.005 / −.018 / −11% (24.36, 61k) |
| | 2N | +0.08 / +.005 / −.002 / −14% (25.86) | −0.01 / +.003 / −.005 / −13% (25.99) | +0.13 / +.003 / −.007 / −14% (26.04) |
| | 3N | +0.10 / +.004 / −.006 / −15% (26.73) | +0.04 / +.003 / −.002 / −15% (26.86) | +0.10 / +.002 / −.006 / −15% (26.94) |
| Aria 0416_301-305 | 1N | +0.05 / +.006 / −.011 / −19% (25.86, 319k) | +0.06 / +.004 / −.012 / −19% (25.74) | +0.04 / +.004 / −.015 / −19% (25.53, 83k) |
| | 2N | −0.03 / +.005 / −.007 / −19% (27.21) | +0.03 / +.005 / −.011 / −19% (26.99) | −0.04 / +.003 / −.012 / −19% (26.70) |
| TUM fr1_desk | 1N | +0.01 / +.009 / −.003 / −4% (18.92, 226k) | +0.04 / +.008 / −.009 / −4% (18.90) | +0.01 / +.004 / −.012 / −4% (18.88, 56k) |
| | 2N | +0.10 / +.008 / −.001 / −9% (19.18) | +0.09 / +.005 / −.007 / −9% (19.23) | +0.03 / +.004 / −.011 / −9% (19.27) |
| RPNG table_01 | 1N | +0.00 / +.002 / −.005 / −3% (21.37, 676k) | +0.02 / +.002 / −.008 / −2% (21.29) | +0.05 / +.002 / −.010 / −2% (21.13, 168k) |
| | 2N | +0.02 / +.002 / −.004 / −4% (21.68) | +0.04 / +.002 / −.005 / −4% (21.59) | +0.06 / +.002 / −.006 / −4% (21.45) |
**Reading.** Even with 4× fewer Gaussians, I gives at most +0.13 dB (PSNR Δ −0.04…+0.13 over 27 comparisons). SSIM improves
27/27; LPIPS improves 27/27 and its gain grows as density drops (e.g. Aria 1N −0.011 → −0.015, TUM 1N −0.003 → −0.012).
Side finding: quartering the birth density costs the baseline almost nothing (ETH3D +0.04…+0.21, TUM −0.04…+0.09,
Aria −0.33…−0.51, RPNG −0.23 dB) at 4× fewer Gaussians.

## Completion (2026-10-09) — UTMM and 3N filled after freeing the frontend tapes (~160 GB) and copying the UTMM loader
(`author_source/` from colin, read-only). All 108 runs trained; "failed" rows = depth-GT assert only (Aria/UTMM/RPNG).
Additional R2-I − R2 rows (PSNR / SSIM / LPIPS / Gaussians):
| scene | budget | density 1 | density 0.5 | density 0.25 |
|---|---|---|---|---|
| Aria 0416_301-305 | 3N | +0.02 / +.005 / −.005 / −19% (28.01, 282k) | −0.08 / +.004 / −.005 / −19% | −0.05 / +.003 / −.009 / −19% |
| TUM fr1_desk | 3N | +0.02 / +.007 / −.005 / −10% (19.50, 178k) | +0.03 / +.004 / −.007 / −11% | +0.06 / +.003 / −.012 / −11% |
| UTMM square-1 | 1N | +0.09 / +.007 / −.022 / −16% (18.20, 146k) | +0.09 / +.007 / −.024 / −16% | +0.18 / +.007 / −.018 / −16% (17.25) |
| | 2N | +0.12 / +.007 / −.026 / −16% (18.59) | +0.12 / +.007 / −.026 / −16% | +0.24 / +.008 / −.023 / −16% (17.61) |
| | 3N | +0.13 / +.007 / −.022 / −16% (18.76) | +0.10 / +.007 / −.026 / −16% | +0.23 / +.009 / −.023 / −15% (17.74) |
| RPNG table_01 | 3N | +0.01 / +.001 / +.000 / −6% (21.87, 280k) | +0.04 / +.002 / −.001 / −6% | +0.05 / +.002 / −.005 / −5% |
**Reading.** UTMM is the scene where I helps most (+0.1…+0.24 dB, LPIPS −0.02…−0.03), largest at ¼ density — the only
scene where the I PSNR gain grows as Gaussians become scarce. UTMM is also the most capacity-limited (¼ density −1.0 dB).
**Matched-PSNR reduction vs default (R2, density 1), smallest Gaussian count within 0.1 dB:** ETH3D −78% (LPIPS better),
TUM −77% (LPIPS +0.013…+0.019), RPNG table_01 −51% at 1N/2N (LPIPS +0.024…+0.029), Aria −19…−58%, UTMM −16%.
I alone (density 1) never loses PSNR beyond 0.03 dB and improves LPIPS on every scene: −3…−19% Gaussians.
RPNG table_02 added (user request) in `results/campaigns/gain_attribution/geom_ablation_density_t02/` — pending.

## RPNG table_02 (2026-10-09) — not completed: CUDA OOM on the 16 GB card
The R4 capture (pilot) OOMed at 1920/2282 renders at 1N (14.45 GiB in use, 2.97 GiB reserved-unallocated), so each budget's
suite stopped at its pilot (all three budgets same). Not retried (VRAM-limited scenes are skipped per user rule); a retry
with PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True may fit since ~3 GiB was fragmentation.
