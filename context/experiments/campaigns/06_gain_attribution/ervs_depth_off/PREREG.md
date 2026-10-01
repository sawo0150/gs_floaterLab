# Preregistration — does keyframe depth supervision mask the sampler effect? (2026-10-02, before any run)

## Question and rationale

On B (keyframe RGB + metric depth L1 0.25), ERVS vs RR shows no consistent effect in either pool
([ervs_per_pool](../ervs_per_pool/README.md)). In 3dgs-custom, where training was RGB-only, the ERCB family did show
gains. Hypothesis **H**: keyframe depth supervision constrains geometry strongly enough that the order of photometric
service matters little; with the depth term removed, the sampler effect becomes consistent.

This is a **diagnostic** of the B system (B with keyframe depth weight 0). It is not the paper system and its
numbers must not be reported as the system ablation. Initialization still uses tracker depth; only the depth
*supervision* term is removed.

## Arms (B worker/recipe/environment; keyframe depth weight 0; window on, quotas 3:3:6; seed 0)

| Arm | Keyframe pool | Dense pool | Overrides |
|---|---|---|---|
| D0-EE | ERVS | ERVS | — |
| D0-ER | ERVS | RR | `--selector rr`, `B_RR_ROLES=dense` |
| D0-RE | RR | ERVS | `--selector rr`, `B_RR_ROLES=keyframe` |
| D0-RR | RR | RR | `--selector rr` |

All arms run through `per_pool_selector.py` with `B_KF_DEPTH_W=0` (sets the loaded `w_plain` to 0; keyframe loss
becomes 0.95 × masked RGB L1). Execution gates: `geometry_runtime.json` reports `w_plain = 0`; ER/RE draw counts show
only the intended method per pool. Scenes aria1253, aria1253rot, RPNG table_06, UTMM square-1; budgets 15 and 25.
32 new runs.

## Metrics and effects

Whole-cohort held-out PSNR (primary), SSIM, LPIPS, recent-third PSNR; keyframe-pool / dense service CV.
Per scene and budget: joint ERVS effect D0-EE − D0-RR; keyframe-pool effect ½[(EE−RE)+(ER−RR)];
dense-pool effect ½[(EE−ER)+(RE−RR)]; interaction (EE−ER)−(RE−RR). Depth-off cost: D0-EE − B (descriptive).

## Noise references

B seed-0/1 spread (colin): aria1253 .021, rot .152, table_06 .048, square-1 .019 dB (depth-on; used as is).

## Reading rules (fixed now)

- An effect is a **signal** at a budget if it has the same sign in ≥3/4 scenes and exceeds the scene's noise
  reference in those scenes.
- **H supported** if the joint ERVS effect, or either pool effect, is a positive signal at a budget where the
  corresponding depth-on effect (ervs_per_pool / b_ablation_v2) was not a signal.
- **H rejected** if no positive signal appears at either budget.
- A negative signal is reported as such. No weight, κ, τ or quota changes after seeing results. Single seed.

## Outputs

- Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_ervs_depth_off.py`
- Raw: `results/campaigns/gain_attribution/ervs_depth_off/v1/d0/<scene>/render<budget>/<arm>/`
- Card: this folder's `README.md`
