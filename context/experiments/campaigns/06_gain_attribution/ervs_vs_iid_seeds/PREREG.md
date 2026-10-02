# Preregistration — ERVS K16 vs uniform with replacement, 3 seeds on the four B scenes (2026-10-03, before any run)

User request: compare ERVS (K=16 persistent per-pool group queue) with uniform sampling with replacement (K=1) on the
four pinned B scenes, add seeds 1 and 2, and plot the seed/cell-averaged temporal curves.

## Arms (B worker/recipe/environment; κ = 16; quotas 3:3:6)

| Arm | Implementation |
|---|---|
| ervs_k16 | `group_k_patch.py`, `B_GROUP_K=16` (τ = 4 per_view) |
| uniform_iid | `sampling_mode_patch.py`, `B_WITH_REPLACEMENT=1`, `--tau 1e12` |

Scenes aria1253, table_06, aria1253rot, square-1 (rot and square-1 were used to select K=16; reported separately as well).
Budgets 15 and 25. Seeds 0, 1, 2 (`--seed`, mapping RNG only; tracker archive fixed).

New runs: seeds 1–2 for all 16 cells × 2 arms (32) + square-1 seed-0 uniform_iid at 15/25 (2) = 34.
Reused seed 0: ervs_k16 from ervs_group_k (rot, square-1) and ervs_vs_uniform_k16 (aria1253, table_06);
uniform_iid from ervs_vs_uniform v1 (rot) and ervs_vs_uniform_k16 (aria1253, table_06).

## Metrics and reading

Per cell, seed-mean of: held-out PSNR, min-bin PSNR (five time bins), worst-Q1, SSIM, LPIPS. Difference ERVS − iid with
the seed-to-seed spread. Temporal figure: paired per-view difference ERVS − iid (same held-out views), moving average
20% of views, averaged over 3 seeds × 8 cells; plus five-bin means with per-cell points. Absolute curves averaged as well.
All cells reported whatever their sign.
