# Preregistration — ERVS vs RR at very low budgets (5 and 10 renders/KF) (2026-10-02, before any run)

## Question

Does ERVS beat RR on the paper system (B) when per-view service is very scarce? Earlier B results at 15/25/40
were scene-dependent ([b_ablation_v2](../b_ablation_v2/README.md), pilot); in 3dgs-custom the ERCB-family gain was
largest at the lowest budget. Budgets 5 and 10 extend the budget curve downward.

## Arms (official B worker/recipe/environment, depth on; seed 0)

| Arm | Overrides |
|---|---|
| ervs (B) | `--renders-per-kf {5,10}` |
| rr | `--renders-per-kf {5,10} --selector rr` |

Scenes aria1253, aria1253rot, RPNG table_06, UTMM square-1. 16 new runs. Runs start after the depth-off diagnostic
finishes (GPU idle check before each run).

## Metrics

Whole-cohort held-out PSNR (primary), SSIM, LPIPS; recent-third PSNR; keyframe-pool and dense service CV.

## Noise references

B seed-0/1 spread at budget 40 (colin): aria1253 .021, rot .152, table_06 .048, square-1 .019 dB. Spread may be
larger at very low budgets; this is a known limitation of single-seed reading.

## Reading rules (fixed now)

- At each budget, ERVS−RR is a **signal** if positive in ≥3/4 scenes and above the scene's noise reference in those.
- The budget curve 5/10/15/25(/40) of ERVS−RR is reported per scene, including all signs.
- "ERVS helps under scarce budgets" is supported only if budget 5 or 10 is a positive signal. A positive signal at
  one budget alone is a candidate for multi-seed confirmation, not a final claim. No κ/τ changes afterwards.

## Outputs

- Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_ervs_low_budget.py`
- Raw: `results/campaigns/gain_attribution/ervs_low_budget/v1/low/<scene>/render<budget>/<arm>/`
- Card: this folder's `README.md`
