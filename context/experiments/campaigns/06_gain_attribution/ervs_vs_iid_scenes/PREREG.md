# Preregistration — ERVS K16 vs uniform with replacement on 15 extra scenes (2026-10-03, before any run)

Extends [ervs_vs_iid_seeds](../ervs_vs_iid_seeds/README.md) (four pinned B scenes) to the other scenes with B-equivalent
setups: aria301_305; RPNG table_01–05, 07, 08; UTMM ego-centric-1, ego-centric-2, ego-drive, fast-straight,
slow-straight-1, slow-straight-2, square-2. None was used for K selection.

## Inputs

Setups: cvpr_assets/fixed_work_v1 captures. Checked against the pinned table_06 and square-1 setups: identical exp78b
command flags and frozen tracker archive; native_setup differs only in recorded output and droid.pth paths. Archives
symlinked from the external handoff volume. The runner's preflight keeps all source/extension/rasterizer hash checks and
replaces only the four-scene lookup (dry run passed on all 15).

## Arms (B worker/recipe/environment; κ = 16; quotas 3:3:6)

ervs_k16 (`group_k_patch.py`, K = 16, τ = 4 per_view) vs uniform_iid (`sampling_mode_patch.py`, with replacement,
`--tau 1e12`). Budget 25 renders/KF. Seeds 0, 1, 2. 90 runs; seed 0 for all scenes first.

Smoke: table_01 seed 0 (2 runs). Continue automatically if all gates pass and the ERVS PSNR is within 23–27 dB
(cvpr d3 table_01: 24.41 at 15, 25.75 at 40 renders/KF).

## Metrics and reading

Per scene seed-mean ΔPSNR (ERVS − iid), Δmin-bin PSNR, Δworst-Q1, SSIM, LPIPS; number of scenes with ERVS ahead;
mean over scenes with a scene-level bootstrap 95% CI. Temporal: paired per-view difference and both arms' mean curves,
averaged over seeds and scenes, five-bin means. Reported for the 15 new scenes alone and pooled with the four pinned
scenes at budget 25 (19 scenes). All scenes reported whatever their sign.
