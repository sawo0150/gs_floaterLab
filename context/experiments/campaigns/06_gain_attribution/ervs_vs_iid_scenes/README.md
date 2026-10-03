# ERVS K16 vs uniform with replacement, 19 scenes × 3 seeds (2026-10-03)

Status: **EVIDENCE — complete** (90 new runs + 4 pinned scenes from ervs_vs_iid_seeds), budget 25, B recipe.
[PREREG](PREREG.md) (`6bb897c`, Amendment 1: legacy IMU fill for fast-straight). Page:
https://claude.ai/artifact/BXDDcKZe9cFqpNRyNLQ3tt. Raw `results/campaigns/gain_attribution/ervs_vs_iid_scenes/v1/`.
Paused twice for the τ and training-signal studies; interrupted runs archived as `failed_attempts/paused_for_*`.

## Results (Δ = ERVS − uniform, seed means per scene; 95% scene-bootstrap CI)

| Set | ΔPSNR | Δmin-bin | Δworst-Q1 | five-bin Δ | dense CV ERVS / uniform |
|---|---|---|---|---|---|
| 15 new scenes | +0.037 [−0.02, +0.10], 8/15 | −0.107 [−0.26, +0.03], 7/15 | −0.118 [−0.25, +0.01], 5/15 | −0.26/+0.05/+0.19/+0.24/−0.03 | 0.74 / 0.91 |
| all 19 scenes | +0.045 [−0.01, +0.10], 11/19 | −0.080 [−0.20, +0.03], 9/19 | −0.107 [−0.21, −0.00], 7/19 | −0.25/+0.04/+0.22/+0.22/−0.01 | 0.74 / 0.91 |

Reading: ERVS K16 evens dense service counts in every scene and shifts quality from the earliest fifth to the middle of
the stream, but the mean gain is small and not resolved (CI includes 0), and the worst-region metrics are slightly
worse. Three small UTMM scenes (slow-straight-1, fast-straight, slow-straight-2: ≤14 final KFs) are included.

## Amendment 2 result — uniform K16 group (19 scenes × 3 seeds, complete 2026-10-03)

Effect decomposition (seed means per scene; mean [95% scene-bootstrap CI], scenes positive):

| Comparison | ΔPSNR | Δmin-bin | Δworst-Q1 |
|---|---|---|---|
| ERVS − uniform_iid (total) | +0.045 [−0.01, +0.10], 11/19 | −0.080 [−0.21, +0.04], 9/19 | −0.107 [−0.22, −0.00], 7/19 |
| uniform_k16 − uniform_iid (K=16 group structure) | **+0.106 [+0.04, +0.18], 14/19** | −0.094 [−0.23, +0.03], 6/19 | −0.064 [−0.16, +0.03], 8/19 |
| ERVS − uniform_k16 (count-balancing term) | **−0.061 [−0.14, +0.00], 6/19** | +0.014 [−0.11, +0.12], 10/19 | −0.042 [−0.12, +0.03], 9/19 |

On the 15 new scenes the balancing term is −0.078 [−0.18, −0.01] (4/15). Reading: the mean-PSNR gain over sampling
with replacement comes entirely from the without-replacement K=16 group; the ERVS count term itself lowers mean PSNR
slightly and does not lift the worst regions.
