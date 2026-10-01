# ERVS vs RR at budgets 15/25 on four B scenes (2026-10-01)

Status: **EVIDENCE — complete, 16 cells (12 new runs + 4 reused pilot runs)**, seed 0. Not a final claim.

[PREREG](PREREG.md) (sha in `PREREG.sha256`, committed `cd40e9d` before any run). Broader design: [PLAN](PLAN.md)
(Parts B/C deferred). Runner `benchmarks/online_gs/campaigns/gain_attribution/run_b_ablation_v2.py` (official B
worker/recipe/environment + `--selector rr` only). Raw: `results/campaigns/gain_attribution/b_ablation_v2/v1/`.
All new runs passed the execution audit and the twice-run held-out evaluation.

## Results

Whole-cohort held-out PSNR (dB); `*` = |Δ| above that scene's seed noise reference
(aria1253 .021, rot .152, table_06 .048, square-1 .019).

| Scene | Budget | ERVS | RR | ERVS−RR | Recent-third Δ | KF-pool CV ERVS/RR | Dense CV ERVS/RR |
|---|---:|---:|---:|---:|---:|---:|---:|
| aria1253rot | 15 | 23.812 | 23.685 | +0.127 | +0.281 | 0.603/0.678 | 0.855/0.880 |
| aria1253rot | 25 | 24.532 | 24.596 | −0.064 | −0.009 | 0.600/0.677 | 0.822/0.897 |
| table_06 | 15 | 23.787 | 23.342 | **+0.445*** | +0.162 | 0.575/0.669 | 0.867/0.886 |
| table_06 | 25 | 24.426 | 24.159 | **+0.267*** | +0.124 | 0.595/0.660 | 0.832/0.896 |
| aria1253 | 15 | 23.452 | 23.312 | **+0.140*** | −0.030 | 0.644/0.688 | 0.857/0.861 |
| aria1253 | 25 | 24.516 | 24.930 | **−0.414*** | +0.049 | 0.626/0.696 | 0.826/0.878 |
| square-1 | 15 | 20.765 | 20.980 | **−0.215*** | −0.123 | 0.672/0.740 | 0.832/0.842 |
| square-1 | 25 | 21.370 | 21.417 | **−0.048*** | −0.111 | 0.647/0.733 | 0.841/0.847 |

Pilot budget-40 (seed 0) for reference: rot −0.278, table_06 +0.220.

## Reading against the PREREG

- **Mechanism moved in 8/8 cells:** ERVS lowers the keyframe-pool service CV (and slightly the dense CV) in every cell.
- **C2 quality rule not met.** Whole-cohort ERVS−RR positive above noise: budget 15 → 2/4 (table_06, aria1253),
  budget 25 → 1/4 (table_06). Recent-third positive: 2/4 at both budgets. Required ≥3/4.
- The only scene with a consistent ERVS gain is RPNG table_06 (+0.45/+0.27/+0.22 at 15/25/40). square-1 favours RR
  at both budgets; aria1253 flips sign between 15 and 25; rot is within noise except at 40 (RR).
- Balancing the service counts more evenly does not translate into a consistent held-out gain in B. Consistent with
  prior work: 3dgs-custom ERCB gains came mostly from keyframe emphasis, which B's 3:3:6 quota already provides, and
  the earlier VIGS transfer (exp03-E…H) also averaged ≈0.

## Implications

- The paper should not claim a general ERVS quality or convergence gain on the B system from current evidence.
  Defensible statements: ERVS balances service counts (mechanism, 8/8) at no quality cost on average; its quality
  effect is scene-dependent.
- Options: (a) keep ERVS as the default sampler and describe it as a balancing mechanism, with RR reported as an
  equivalent-quality ablation; (b) look for a scene property predicting the RPNG-type gain (pool size, revisits)
  and preregister it before testing; (c) drop ERVS as a headline contribution and centre C1 dense RGB supervision.
- Multi-seed runs would mainly sharpen the per-scene picture; they are unlikely to turn 2/4 into a general claim.
