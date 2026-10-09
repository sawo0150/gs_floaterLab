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
