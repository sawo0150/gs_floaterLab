# Preregistration — ERVS per pool: keyframe pool vs dense pool (2026-10-02, before any run)

## Question

B applies one sampler to both the keyframe pool and the dense pool. ERVS measurably balances the keyframe pool but
not the dense pool, and the joint ERVS−RR effect changes sign across scenes. Do the two pools carry opposite
effects that cancel? A 2×2 factorial separates them.

## Arms (window on = B quotas 3:3:6; seed 0; budgets 15 and 25; four B scenes)

| Arm | Keyframe pool | Dense pool | Source |
|---|---|---|---|
| EE | ERVS | ERVS | B, reused from [b_ablation_v2](../b_ablation_v2/README.md) |
| RR | RR | RR | B-RR, reused from b_ablation_v2 |
| ER | ERVS | RR | new: `--selector rr`, `B_RR_ROLES=dense` |
| RE | RR | ERVS | new: `--selector rr`, `B_RR_ROLES=keyframe` |

New arms use the runtime patch `benchmarks/online_gs/campaigns/gain_attribution/per_pool_selector.py`: it copies
the locked `UnifiedTrainingSet.reserve` (sha256 `93be917d…`) and restricts the RR branch to the listed roles; the
other role keeps the unchanged Gibbs (ERVS) branch. Draw counts per (method, role) are logged per run and must show
only the intended method in each role (execution gate). 16 new runs.

## Effects (per scene and budget, whole-cohort held-out PSNR; recent-third reported alongside)

- Keyframe-pool ERVS effect: ½[(EE − RE) + (ER − RR)]
- Dense-pool ERVS effect: ½[(EE − ER) + (RE − RR)]
- Interaction: (EE − ER) − (RE − RR)

## Noise references

B seed-0/1 spread (colin): aria1253 .021, rot .152, table_06 .048, square-1 .019 dB.

## Reading rules (fixed now)

- A pool effect is a **signal** at a budget if it has the same sign in ≥3/4 scenes and exceeds the scene's noise
  reference in those scenes.
- **Cancellation hypothesis** is supported if the two pool effects are signals of opposite sign at the same budget.
- If neither pool effect is a signal, the sampler effect is small in both pools; no further sampler variants follow.
- Mechanism: keyframe-pool and dense service-count CV per arm. Single seed; no parameter changes afterwards.

## Outputs

- Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_ervs_per_pool.py`
- Raw: `results/campaigns/gain_attribution/ervs_per_pool/v1/pool/<scene>/render<budget>/<arm>/`
- Card: this folder's `README.md`
