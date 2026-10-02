# Preregistration — ERVS (K=16) vs uniform sampling on held-out scenes (2026-10-02, before any run)

ERVS group size K = 16 was selected on rot and square-1 ([ervs_group_k](../ervs_group_k/README.md)). This compares it
with the revised method's uniform baseline on the scenes not used for tuning.

## Arms (B worker/recipe/environment; κ = 16; quotas 3:3:6; window unchanged; seed 0)

| Arm | β | K | Implementation |
|---|---|---|---|
| ervs_k16 | ERVS (τ = 4 per_view) | 16, persistent per-pool queue | `group_k_patch.py`, `B_GROUP_K=16` |
| uniform_k16 | 0 (`--tau 1e12`) | 16, same queue | `group_k_patch.py`, `B_GROUP_K=16`, `--tau 1e12` |
| uniform_iid | 0 (`--tau 1e12`) | 1, with replacement | `sampling_mode_patch.py`, `B_WITH_REPLACEMENT=1`, `--tau 1e12` |

Scenes aria1253, RPNG table_06 (held out from K tuning). Budgets 15 and 25. 12 new runs.
Gates: group queue used in both pools (K16 arms); recorded tau ≥ 1e11 (uniform arms); repeated in-batch draws > 0
(uniform_iid).

## Metrics

Mean held-out PSNR, SSIM, LPIPS; min-bin PSNR (lowest of five time-bin means); worst-Q1 (mean of the lowest ⌈n/4⌉
views); service-count CV per pool; mean service count by admission-time quintile.

## Reading (fixed now)

- β effect = ervs_k16 − uniform_k16; K effect = uniform_k16 − uniform_iid.
- Per cell, a difference is resolved if it exceeds the scene noise reference (aria1253 0.021, table_06 0.048 dB).
- All four metrics are reported for every cell whatever their sign. With 2 scenes × 2 budgets, a consistent effect means
  the same sign and resolved in 4/4 cells; 3/4 is reported as a tendency. Single seed. No parameter changes afterwards.
