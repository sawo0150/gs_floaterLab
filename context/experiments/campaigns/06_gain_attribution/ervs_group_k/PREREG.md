# Preregistration — ERVS group size K on B (2026-10-02, before any run)

## Question

The revised method (§3.2) draws K distinct views per group from probabilities computed at the group start. In B the
group is one selection batch (K_keyframe = 3, K_dense = 6) and is truncated by the remaining packet credit. With a
persistent per-pool group queue, which K gives the best ERVS before ERVS is compared with uniform sampling?

## Arms (B worker/recipe/environment; ERVS τ = 4 per_view; κ = 16; quotas 3:3:6; seed 0)

| Arm | Group | Implementation |
|---|---|---|
| K_batch (current B) | per batch: keyframe 3, dense 6 | reused (b_ablation_v2, pilot) |
| K16 / K32 / K64 | persistent per-pool queue, same K for keyframe and dense pools | `group_k_patch.py`, `B_GROUP_K` |

Gate per run: `group_k.json` reports groups > 0 for both pools.

Tuning scenes only: aria1253rot (rot), UTMM square-1. Budgets 15 and 25. 12 new runs. aria1253 and RPNG table_06 are
held out for the later ERVS-vs-uniform comparison.

## Metrics

Mean held-out PSNR (selection), SSIM, LPIPS, min-bin PSNR (lowest of five time bins), worst-Q1, service-count CV
per pool, mean group size and skips.

## Selection rule (fixed now)

Pick the K with the highest mean PSNR averaged over the 4 tuning cells (2 scenes × 2 budgets), including K_batch.
If several are within 0.05 dB of the best, pick the smallest K among them. The chosen K is then fixed for the held-out
comparison; no further K or τ changes.
